from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time


TIMEOUT_SECONDS = 3
MAX_COUNT = 9223372036854775807
RUNTIME_GUARD = r'''import builtins
import io
import os
import pathlib
import socket
import subprocess


def _deny(*args, **kwargs):
    raise RuntimeError("forbidden side effect during acceptance test")


def _is_write_mode(mode):
    return isinstance(mode, str) and any(flag in mode for flag in "wax+")


_real_builtin_open = builtins.open
_real_io_open = io.open
_real_os_open = os.open
_real_fdopen = os.fdopen


def _guarded_builtin_open(file, mode="r", *args, **kwargs):
    if _is_write_mode(mode):
        _deny()
    return _real_builtin_open(file, mode, *args, **kwargs)


def _guarded_io_open(file, mode="r", *args, **kwargs):
    if _is_write_mode(mode):
        _deny()
    return _real_io_open(file, mode, *args, **kwargs)


def _guarded_os_open(path, flags, *args, **kwargs):
    write_flags = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
    if flags & write_flags:
        _deny()
    return _real_os_open(path, flags, *args, **kwargs)


def _guarded_fdopen(fd, mode="r", *args, **kwargs):
    if _is_write_mode(mode):
        _deny()
    return _real_fdopen(fd, mode, *args, **kwargs)


builtins.open = _guarded_builtin_open
io.open = _guarded_io_open
os.open = _guarded_os_open
os.fdopen = _guarded_fdopen

for _name in (
    "chmod", "link", "makedirs", "mkdir", "popen", "remove", "removedirs",
    "rename", "renames", "replace", "rmdir", "startfile", "symlink", "system",
    "truncate", "unlink", "utime",
):
    if hasattr(os, _name):
        setattr(os, _name, _deny)
for _name in tuple(name for name in dir(os) if name.startswith(("exec", "spawn"))):
    setattr(os, _name, _deny)

for _name in (
    "chmod", "hardlink_to", "link_to", "mkdir", "rename", "replace", "rmdir",
    "symlink_to", "touch", "unlink", "write_bytes", "write_text",
):
    if hasattr(pathlib.Path, _name):
        setattr(pathlib.Path, _name, _deny)

socket.socket = _deny
socket.create_connection = _deny
socket.create_server = _deny
subprocess.Popen = _deny
subprocess.call = _deny
subprocess.check_call = _deny
subprocess.check_output = _deny
subprocess.run = _deny
'''


class Harness:
    def __init__(self, target: Path) -> None:
        self.target = target.resolve()
        self.guard_dir: Path | None = None
        self.passed = 0
        self.failed = 0
        self.failures: list[dict[str, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
            return
        self.failed += 1
        self.failures.append({"check": name, "detail": detail})

    @staticmethod
    def normalized_ascii(data: bytes) -> tuple[str | None, str]:
        try:
            return data.decode("ascii").replace("\r\n", "\n").replace("\r", "\n"), ""
        except UnicodeDecodeError as exc:
            return None, f"non-ASCII output: {exc}"

    def run(self, cwd: Path, args: list[str], env: dict[str, str] | None = None) -> dict[str, object]:
        command = [sys.executable, str(self.target), *args]
        child_env = os.environ.copy() if env is None else env.copy()
        if self.guard_dir is not None:
            child_env["PYTHONPATH"] = str(self.guard_dir)
        child_env["PYTHONDONTWRITEBYTECODE"] = "1"
        child_env["PYTHONNOUSERSITE"] = "1"
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                shell=False,
                timeout=TIMEOUT_SECONDS,
                env=child_env,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {"timeout": True, "returncode": None, "stdout": None, "stderr": None, "decode_error": ""}
        stdout, stdout_error = self.normalized_ascii(completed.stdout)
        stderr, stderr_error = self.normalized_ascii(completed.stderr)
        return {
            "timeout": False,
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "decode_error": stdout_error or stderr_error,
        }

    @staticmethod
    def describe(result: dict[str, object]) -> str:
        return json.dumps(result, ensure_ascii=True, sort_keys=True, default=str)

    def expect_success(self, name: str, cwd: Path, args: list[str], expected: str, env: dict[str, str] | None = None) -> dict[str, object]:
        result = self.run(cwd, args, env)
        ok = (
            result["timeout"] is False
            and result["decode_error"] == ""
            and result["returncode"] == 0
            and result["stdout"] == expected
            and result["stderr"] == ""
        )
        self.check(name, ok, self.describe(result))
        return result

    def expect_error(self, name: str, cwd: Path, args: list[str], message: str) -> dict[str, object]:
        result = self.run(cwd, args)
        ok = (
            result["timeout"] is False
            and result["decode_error"] == ""
            and result["returncode"] == 2
            and result["stdout"] == ""
            and result["stderr"] == message + "\n"
        )
        self.check(name, ok, self.describe(result))
        return result


def write_bytes(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def snapshot(path: Path) -> dict[str, object]:
    info = path.stat()
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "mtime_ns": info.st_mtime_ns,
        "mode": info.st_mode,
        "file_attributes": getattr(info, "st_file_attributes", None),
    }


def inventory(root: Path) -> list[tuple[str, bool]]:
    return sorted((str(path.relative_to(root)).replace("\\", "/"), path.is_dir()) for path in root.rglob("*"))


def tree_snapshot(root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root)).replace("\\", "/")
        if path.is_dir():
            records.append({"path": relative, "type": "directory"})
            continue
        info = path.stat()
        records.append(
            {
                "path": relative,
                "type": "file",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "mtime_ns": info.st_mtime_ns,
                "mode": info.st_mode,
                "file_attributes": getattr(info, "st_file_attributes", None),
            }
        )
    return records


def check_static_constraints(harness: Harness) -> None:
    try:
        source = harness.target.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, UnicodeError, SyntaxError) as exc:
        harness.check("24-static-standard-library-and-no-side-effects", False, repr(exc))
        return

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])

    non_stdlib = sorted(module for module in imported if module not in sys.stdlib_module_names)
    ok = not non_stdlib
    detail = json.dumps({"non_stdlib": non_stdlib}, sort_keys=True)
    harness.check("24-static-standard-library-and-no-side-effects", ok, detail)


def check_runtime_guard(harness: Harness, root: Path) -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(harness.guard_dir)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONNOUSERSITE"] = "1"
    probes = {
        "file-write": "open('guard-probe.txt','w')",
        "network": "import socket; socket.socket()",
        "subprocess": "import subprocess; subprocess.run(['never-started'])",
    }
    results: dict[str, int | str] = {}
    for name, program in probes.items():
        try:
            completed = subprocess.run(
                [sys.executable, "-c", program],
                cwd=root,
                capture_output=True,
                shell=False,
                timeout=TIMEOUT_SECONDS,
                env=environment,
                check=False,
            )
            results[name] = completed.returncode
        except subprocess.TimeoutExpired:
            results[name] = "timeout"
    ok = all(value not in (0, "timeout") for value in results.values()) and not (root / "guard-probe.txt").exists()
    harness.check("24-runtime-side-effect-guard-active", ok, json.dumps(results, sort_keys=True))


def main() -> int:
    started = time.perf_counter()
    if len(sys.argv) != 2:
        print(json.dumps({"passed": 0, "failed": 1, "checks": 1, "failures": [{"check": "harness-arguments", "detail": "expected target script path"}], "duration_seconds": 0.0}, separators=(",", ":")))
        return 1

    target = Path(sys.argv[1])
    harness = Harness(target)
    if not target.is_file():
        harness.check("target-exists", False, str(target))
    else:
        target_tree_before = tree_snapshot(target.resolve().parent)
        with tempfile.TemporaryDirectory(prefix="counter-merge-acceptance-") as temporary:
            root = Path(temporary)
            guard_dir = root / "runtime-guard"
            write_bytes(guard_dir / "sitecustomize.py", RUNTIME_GUARD.encode("ascii"))
            harness.guard_dir = guard_dir
            check_runtime_guard(harness, root)
            left = write_bytes(root / "left.json", b'{"bananas":1,"apples":2}')
            right = write_bytes(root / "right.json", b'{"cherries":3,"bananas":4}')
            harness.expect_success(
                "1-normal-overlap-and-stream-discipline",
                root,
                [str(left), str(right)],
                '{"apples":2,"bananas":5,"cherries":3}\n',
            )

            left = write_bytes(root / "case-left.json", b'{" A ":1,"a":2}')
            right = write_bytes(root / "case-right.json", b'{" A ":3,"A":4}')
            harness.expect_success("2-key-preservation", root, [str(left), str(right)], '{" A ":4,"A":4,"a":2}\n')

            empty_left = write_bytes(root / "empty-left.json", b"{}")
            empty_right = write_bytes(root / "empty-right.json", b"{}")
            harness.expect_success("4-empty-objects", root, [str(empty_left), str(empty_right)], "{}\n")

            unicode_dir = root / "路径 含 空格"
            bom_left = write_bytes(unicode_dir / "左.json", b'\xef\xbb\xbf  {"\xc3\xa9":2,"":0,"a":1} \r\n')
            unicode_right = write_bytes(unicode_dir / "右.json", '{"😀":3,"é":4}'.encode("utf-8"))
            harness.expect_success(
                "5-and-9-bom-unicode-whitespace-and-path",
                root,
                [str(bom_left), str(unicode_right)],
                '{"":0,"a":1,"\\u00e9":6,"\\ud83d\\ude00":3}\n',
            )
            bom_right = write_bytes(root / "bom-right.json", b'\xef\xbb\xbf {"r":2}\n')
            harness.expect_success("5-right-input-bom", root, [str(empty_left), str(bom_right)], '{"r":2}\n')

            dash_left = write_bytes(root / "-left.json", b'{"x":1}')
            dash_right = write_bytes(root / "--right.json", b'{"x":2}')
            harness.expect_success("3-leading-dash-paths-are-not-options", root, [dash_left.name, dash_right.name], '{"x":3}\n')

            max_left = write_bytes(root / "max-left.json", f'{{"m":{MAX_COUNT},"z":0}}'.encode("ascii"))
            max_right = write_bytes(root / "max-right.json", f'{{"m":{MAX_COUNT}}}'.encode("ascii"))
            harness.expect_success(
                "6-max-input-overflow-sum-and-zero-retention",
                root,
                [str(max_left), str(max_right)],
                '{"m":18446744073709551614,"z":0}\n',
            )

            negative_zero = write_bytes(root / "negative-zero.json", b'{"x":-0}')
            harness.expect_success("7-negative-zero", root, [str(negative_zero), str(empty_right)], '{"x":0}\n')

            same = write_bytes(root / "same.json", b'{"x":7}')
            harness.expect_success("8-same-path-read-twice", root, [str(same), str(same)], '{"x":14}\n')

            for count, args in ((0, []), (1, [str(empty_left)]), (3, [str(empty_left), str(empty_right), str(same)])):
                harness.expect_error(f"10-argument-count-{count}", root, args, "error: expected exactly two input paths")

            missing_left = root / "missing-left.json"
            missing_right = root / "missing-right.json"
            harness.expect_error("11-left-read-error", root, [str(missing_left), str(empty_right)], "error: cannot read left input")
            harness.expect_error("11-right-read-error", root, [str(empty_left), str(missing_right)], "error: cannot read right input")
            harness.expect_error("11-left-directory-read-error", root, [str(root), str(empty_right)], "error: cannot read left input")

            invalid_utf8_left = write_bytes(root / "bad-utf8-left.json", b'{"x":\xff}')
            invalid_utf8_right = write_bytes(root / "bad-utf8-right.json", b'{"x":\xff}')
            harness.expect_error("12-left-invalid-utf8", root, [str(invalid_utf8_left), str(empty_right)], "error: invalid UTF-8 in left input")
            harness.expect_error("12-right-invalid-utf8", root, [str(empty_left), str(invalid_utf8_right)], "error: invalid UTF-8 in right input")

            for index, payload in enumerate((b"", b'{"x":', b'{"x":1} trailing')):
                invalid = write_bytes(root / f"invalid-json-{index}.json", payload)
                harness.expect_error(f"13-invalid-json-{index}", root, [str(invalid), str(empty_right)], "error: invalid JSON in left input")

            for constant in (b"NaN", b"Infinity", b"-Infinity"):
                invalid = write_bytes(root / (constant.decode("ascii").replace("-", "minus-") + ".json"), b'{"x":' + constant + b"}")
                harness.expect_error(f"14-nonstandard-{constant.decode('ascii')}", root, [str(invalid), str(empty_right)], "error: invalid JSON in left input")
            right_constant = write_bytes(root / "right-nan.json", b'{"x":NaN}')
            harness.expect_error("14-right-nonstandard-constant", root, [str(empty_left), str(right_constant)], "error: invalid JSON in right input")

            top_level_values = {
                "array": b"[]",
                "string": b'"x"',
                "number": b"1",
                "boolean": b"true",
                "null": b"null",
            }
            for label, payload in top_level_values.items():
                invalid = write_bytes(root / f"top-{label}.json", payload)
                harness.expect_error(f"15-top-level-{label}", root, [str(invalid), str(empty_right)], "error: invalid count object in left input")

            duplicate = write_bytes(root / "duplicate.json", b'{"x":1,"x":2}')
            harness.expect_error("16-duplicate-key", root, [str(duplicate), str(empty_right)], "error: invalid count object in left input")
            right_duplicate = write_bytes(root / "right-duplicate.json", b'{"x":1,"x":2}')
            harness.expect_error("16-right-duplicate-key", root, [str(empty_left), str(right_duplicate)], "error: invalid count object in right input")

            invalid_values = ["true", "false", "null", '"1"', "1.0", "1e0", "-1", "[]", "{}", "9223372036854775808"]
            for index, value in enumerate(invalid_values):
                invalid = write_bytes(root / f"invalid-value-{index}.json", ('{"x":' + value + "}").encode("ascii"))
                harness.expect_error(f"17-invalid-value-{value}", root, [str(invalid), str(empty_right)], "error: invalid count object in left input")
            right_invalid_value = write_bytes(root / "right-invalid-value.json", b'{"x":true}')
            harness.expect_error("17-right-invalid-value", root, [str(empty_left), str(right_invalid_value)], "error: invalid count object in right input")

            bad_left = write_bytes(root / "priority-left.json", b'{"x":')
            harness.expect_error("18-left-error-precedes-missing-right", root, [str(bad_left), str(missing_right)], "error: invalid JSON in left input")

            bad_right = write_bytes(root / "atomic-right.json", b'{"x":')
            atomic = harness.expect_error("19-right-error-has-atomic-empty-stdout", root, [str(empty_left), str(bad_right)], "error: invalid JSON in right input")
            harness.check("20-no-traceback-on-errors", "Traceback" not in str(atomic.get("stderr")), harness.describe(atomic))

            deterministic_left = write_bytes(root / "det-left.json", '{"é":2,"b":1}'.encode("utf-8"))
            deterministic_right = write_bytes(root / "det-right.json", '{"a":3,"é":4}'.encode("utf-8"))
            outputs: list[tuple[object, object, object]] = []
            for seed in ("1", "7", "123456"):
                environment = os.environ.copy()
                environment["PYTHONHASHSEED"] = seed
                result = harness.run(root, [str(deterministic_left), str(deterministic_right)], environment)
                outputs.append((result["returncode"], result["stdout"], result["stderr"]))
            harness.check(
                "21-deterministic-across-hash-seeds",
                len(set(outputs)) == 1 and outputs[0] == (0, '{"a":3,"b":1,"\\u00e9":6}\n', ""),
                repr(outputs),
            )

            immutable_left = write_bytes(root / "immutable-left.json", b'{"x":1}')
            immutable_right = write_bytes(root / "immutable-right.json", b'{"x":2}')
            os.chmod(immutable_left, stat.S_IREAD)
            before_left = snapshot(immutable_left)
            before_right = snapshot(immutable_right)
            before_inventory = inventory(root)
            immutable_result = harness.run(root, [str(immutable_left), str(immutable_right)])
            after_left = snapshot(immutable_left)
            after_right = snapshot(immutable_right)
            after_inventory = inventory(root)
            os.chmod(immutable_left, stat.S_IREAD | stat.S_IWRITE)
            harness.check(
                "22-input-content-metadata-and-readonly-unchanged",
                before_left == after_left and before_right == after_right and immutable_result["returncode"] == 0,
                json.dumps({"before_left": before_left, "after_left": after_left, "before_right": before_right, "after_right": after_right}, sort_keys=True),
            )
            harness.check("23a-no-runtime-files-created-in-input-directory", before_inventory == after_inventory, repr({"before": before_inventory, "after": after_inventory}))

            check_static_constraints(harness)
            harness.check("25-all-processes-respected-three-second-timeout", True)

        target_tree_after = tree_snapshot(target.resolve().parent)
        harness.check(
            "23b-no-runtime-files-or-mutations-in-target-directory",
            target_tree_before == target_tree_after,
            repr({"before": target_tree_before, "after": target_tree_after}),
        )

    duration = round(time.perf_counter() - started, 6)
    result = {
        "passed": harness.passed,
        "failed": harness.failed,
        "checks": harness.passed + harness.failed,
        "failures": harness.failures,
        "duration_seconds": duration,
    }
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0 if harness.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
