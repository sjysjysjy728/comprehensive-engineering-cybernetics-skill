from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any


EVALUATIONS = (
    (
        "ai-ideation",
        "evaluate.py",
        ("--check", "result.json"),
    ),
    (
        "project-delivery",
        "acceptance_test.py",
        ("counter_merge.py",),
    ),
    (
        "resource-synthesis",
        "evaluate.py",
        ("--check", "result.json"),
    ),
    (
        "ai-research",
        "evaluate.py",
        ("--check", "result.json"),
    ),
)


def run_evaluation(root: Path, evaluation_id: str, script_name: str, arguments: tuple[str, ...]) -> dict[str, Any]:
    directory = root / evaluation_id
    script = directory / script_name
    display_command = ["python", "-I", "-B", f"{evaluation_id}/{script_name}", *arguments]
    command = [sys.executable, "-I", "-B", str(script), *arguments]
    try:
        completed = subprocess.run(
            command,
            cwd=directory,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        return {
            "id": evaluation_id,
            "status": "ERROR",
            "returncode": None,
            "command": display_command,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "id": evaluation_id,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "command": display_command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    root = Path(__file__).resolve().parent
    results = [
        run_evaluation(root, evaluation_id, script_name, arguments)
        for evaluation_id, script_name, arguments in EVALUATIONS
    ]
    passed = all(result["returncode"] == 0 for result in results)
    summary = {
        "schema_version": "1.0",
        "status": "PASS" if passed else "FAIL",
        "passed": sum(result["returncode"] == 0 for result in results),
        "failed": sum(result["returncode"] != 0 for result in results),
        "evaluations": results,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
