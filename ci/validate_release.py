#!/usr/bin/env python3
"""Validate and reproducibly package the public Skill repository.

The validator deliberately uses only the Python standard library.  It treats the
repository root as the Skill root and keeps the release surface locked to the
versioned manifest below and in ``ci/release-files.txt``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


SKILL_NAME = "comprehensive-engineering-cybernetics"
DISPLAY_TITLE = "最全面工程控制论 Skill：面向工程与 AI 领域科研"
MANIFEST_PATH = "ci/release-files.txt"
LICENSE_SHA256 = "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"
MAX_FILE_BYTES = 1_000_000
MAX_RELEASE_BYTES = 5_000_000
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ZIP_MODE = 0o100644
SEMVER_TAG = re.compile(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")

REQUIRED_RELEASE_FILES = (
    ".gitattributes",
    ".github/ISSUE_TEMPLATE/bug-report.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/feature-request.yml",
    ".github/workflows/quality-gate.yml",
    ".gitignore",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "SKILL.md",
    "THIRD_PARTY_NOTICES.md",
    "agents/openai.yaml",
    "ci/release-files.txt",
    "ci/validate_release.py",
    "evaluations/README.md",
    "evaluations/ai-research/RESULT.md",
    "evaluations/ai-research/RUBRIC.md",
    "evaluations/ai-research/RUN_PROMPT.md",
    "evaluations/ai-research/TASK.md",
    "evaluations/ai-research/evaluate.py",
    "evaluations/ai-research/result.json",
    "evaluations/ai-research/submission.json",
    "evaluations/project-delivery/RESULT.md",
    "evaluations/project-delivery/RUBRIC.md",
    "evaluations/project-delivery/RUN_PROMPT.md",
    "evaluations/project-delivery/TASK.md",
    "evaluations/project-delivery/acceptance_test.py",
    "evaluations/project-delivery/counter_merge.py",
    "evaluations/project-delivery/result.json",
    "evaluations/resource-synthesis/REPORT.md",
    "evaluations/resource-synthesis/RESULT.md",
    "evaluations/resource-synthesis/RUBRIC.md",
    "evaluations/resource-synthesis/RUN_PROMPT.md",
    "evaluations/resource-synthesis/TASK.md",
    "evaluations/resource-synthesis/evaluate.py",
    "evaluations/resource-synthesis/plan.json",
    "evaluations/resource-synthesis/result.json",
    "evaluations/run_all.py",
    "references/ai-research.md",
    "references/foundations.md",
    "references/project-delivery.md",
    "references/resource-synthesis.md",
)

FORBIDDEN_SUFFIXES = {
    ".7z",
    ".doc",
    ".docx",
    ".key",
    ".p12",
    ".pdf",
    ".pem",
    ".rar",
    ".tar",
    ".tgz",
    ".zip",
}

EVALUATION_FORBIDDEN_PARTS = {
    ".run",
    "private",
    "evidence",
    "workspaces",
    "__pycache__",
}

MARKDOWN_LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
WINDOWS_ABSOLUTE = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/](?![\\/])[^\s<>\"']+)")
_BACKSLASH = chr(92)
UNC_ABSOLUTE = re.compile(
    r"(?<![A-Za-z0-9])"
    + re.escape(_BACKSLASH * 2)
    + r"[A-Za-z0-9._-]+"
    + re.escape(_BACKSLASH)
    + r"[A-Za-z0-9$._-]+"
)
POSIX_PRIVATE = re.compile(
    r"(?<![A-Za-z0-9:/])/(?:Users|home|private|tmp|var/folders)/[^\s<>\"')\]]+"
)

SECRET_RULES = (
    ("github-token", re.compile(r"\bgh(?:p|o|u|s|r)_[A-Za-z0-9]{20,}\b")),
    ("github-fine-grained-token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("openai-api-key", re.compile(r"\bsk-(?:(?:proj|svcacct)-)?[A-Za-z0-9_-]{20,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("npm-token", re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "private-key",
        re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----"),
    ),
    (
        "embedded-url-credential",
        re.compile(r"https?://[^\s/:@]+:[^\s/@]+@[^\s/]+", re.IGNORECASE),
    ),
    (
        "generic-credential",
        re.compile(
            r"\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\b"
            r"\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{16,}",
            re.IGNORECASE,
        ),
    ),
)

_PLACEHOLDER_WORDS = (
    "TO" + "DO",
    "FIX" + "ME",
    "T" + "BD",
    "CHANGE" + "ME",
    "REPLACE" + "_ME",
    "OWN" + "ER",
    "YOUR" + "_GITHUB_USERNAME",
    "REPOSITORY" + "_HTTPS_URL",
)
PLACEHOLDER = re.compile(
    r"(?<![A-Za-z0-9_])(?:"
    + "|".join(map(re.escape, _PLACEHOLDER_WORDS[:-3]))
    + r")(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
PUBLICATION_PLACEHOLDER = re.compile(
    r"(?<![A-Za-z0-9_])(?:"
    + "|".join(map(re.escape, _PLACEHOLDER_WORDS[-3:]))
    + r")(?![A-Za-z0-9_])"
)
EXAMPLE_DOMAIN = re.compile(r"(?<![A-Za-z0-9-])example\.com(?![A-Za-z0-9-])", re.IGNORECASE)


@dataclass(frozen=True, order=True)
class Finding:
    category: str
    path: str
    line: int
    message: str

    def render(self) -> str:
        location = self.path if self.line <= 0 else f"{self.path}:{self.line}"
        return f"[{self.category}] {location}: {self.message}"


def add(
    findings: list[Finding],
    category: str,
    path: str,
    message: str,
    line: int = 0,
) -> None:
    findings.append(Finding(category, path, line, message))


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def strict_utf8(path: Path, relative: str, findings: list[Finding]) -> tuple[bytes, str] | None:
    try:
        data = path.read_bytes()
    except OSError:
        add(findings, "read-error", relative, "file could not be read")
        return None

    if data.startswith(b"\xef\xbb\xbf"):
        add(findings, "encoding", relative, "UTF-8 BOM is not allowed")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        add(findings, "encoding", relative, "file is not strict UTF-8")
        return None
    if "\x00" in text:
        add(findings, "encoding", relative, "NUL bytes are not allowed")
    if "\r" in text:
        add(findings, "line-ending", relative, "use LF line endings")
    if data and not data.endswith(b"\n"):
        add(findings, "line-ending", relative, "text file must end with LF")
    return data, text


def validate_file_policy(relative: str, size: int, findings: list[Finding]) -> None:
    if size > MAX_FILE_BYTES:
        add(findings, "size", relative, "file exceeds the per-file release limit")
    if Path(relative).suffix.lower() in FORBIDDEN_SUFFIXES:
        add(findings, "file-type", relative, "archive or private-source file type is not allowed")
    pure = PurePosixPath(relative)
    if relative.startswith("evaluations/") and any(part in EVALUATION_FORBIDDEN_PARTS for part in pure.parts):
        add(findings, "evaluation-artifact", relative, "raw or private evaluation directories are not publishable")
    name = pure.name.lower()
    if relative.startswith("evaluations/") and (
        name.endswith(".pyc")
        or name.startswith("heldout-seed.")
        or "seed-reveal" in name
    ):
        add(findings, "evaluation-artifact", relative, "raw caches and held-out seed material are not publishable")


def validate_json_document(relative: str, text: str, findings: list[Finding]) -> object | None:
    def no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise ValueError(f"non-finite JSON constant: {value}")

    try:
        return json.loads(text, object_pairs_hook=no_duplicates, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as error:
        add(findings, "json", relative, f"strict JSON parse failed: {error}")
        return None


def validate_python_source(relative: str, text: str, findings: list[Finding]) -> None:
    try:
        compile(text, relative, "exec")
    except (SyntaxError, ValueError, TypeError) as error:
        add(findings, "python", relative, f"source does not compile: {error}")


def validate_project_artifacts(repo: Path, documents: dict[str, object], findings: list[Finding]) -> None:
    relative = "evaluations/project-delivery/result.json"
    result = documents.get(relative)
    if not isinstance(result, dict):
        return
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, dict):
        add(findings, "evaluation-integrity", relative, "artifact records are missing")
        return
    for name in ("acceptance_test.py", "counter_merge.py", "RUN_PROMPT.md"):
        record = artifacts.get(name)
        path = repo / "evaluations" / "project-delivery" / name
        if not isinstance(record, dict) or not path.is_file():
            add(findings, "evaluation-integrity", relative, f"artifact record is missing for {name}")
            continue
        data = path.read_bytes()
        if record.get("bytes") != len(data) or record.get("sha256") != hashlib.sha256(data).hexdigest():
            add(findings, "evaluation-integrity", relative, f"artifact record does not match {name}")


def validate_ai_skill_binding(repo: Path, documents: dict[str, object], findings: list[Finding]) -> None:
    relative = "evaluations/ai-research/result.json"
    result = documents.get(relative)
    if not isinstance(result, dict):
        return
    binding = result.get("closed_loop_fix")
    if not isinstance(binding, dict):
        add(findings, "evaluation-integrity", relative, "revised Skill hash binding is missing")
        return
    expected = {
        "SKILL.md": binding.get("current_skill_sha256"),
        "references/ai-research.md": binding.get("current_ai_research_reference_sha256"),
    }
    for name, recorded in expected.items():
        path = repo / PurePosixPath(name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if recorded != actual:
            add(findings, "evaluation-integrity", relative, f"revised Skill binding does not match {name}")


def is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    checker = getattr(path, "is_junction", None)
    return bool(checker and checker())


def repository_files(repo: Path, findings: list[Finding]) -> set[str]:
    files: set[str] = set()
    folded: dict[str, str] = {}

    for current, directory_names, file_names in os.walk(repo, topdown=True, followlinks=False):
        current_path = Path(current)
        relative_dir = current_path.relative_to(repo)
        if relative_dir == Path(".") and ".git" in directory_names:
            directory_names.remove(".git")

        for directory_name in list(directory_names):
            candidate = current_path / directory_name
            if is_link_like(candidate):
                rel = candidate.relative_to(repo).as_posix()
                add(findings, "symlink", rel, "linked directories are not allowed")
                directory_names.remove(directory_name)

        for file_name in file_names:
            candidate = current_path / file_name
            rel = candidate.relative_to(repo).as_posix()
            if is_link_like(candidate):
                add(findings, "symlink", rel, "linked files are not allowed")
                continue
            key = rel.casefold()
            previous = folded.get(key)
            if previous is not None and previous != rel:
                add(findings, "case-collision", rel, f"path collides with {previous}")
            else:
                folded[key] = rel
            files.add(rel)
    return files


def valid_manifest_entry(entry: str) -> bool:
    if not entry or entry != entry.strip() or "\\" in entry:
        return False
    pure = PurePosixPath(entry)
    return not pure.is_absolute() and pure.as_posix() == entry and all(part not in ("", ".", "..") for part in pure.parts)


def read_manifest(repo: Path, findings: list[Finding]) -> list[str]:
    manifest = repo / MANIFEST_PATH
    parsed = strict_utf8(manifest, MANIFEST_PATH, findings) if manifest.is_file() else None
    if parsed is None:
        if not manifest.is_file():
            add(findings, "manifest", MANIFEST_PATH, "release manifest is missing")
        return []
    _, text = parsed
    entries = text.splitlines()
    for number, entry in enumerate(entries, 1):
        if not valid_manifest_entry(entry):
            add(findings, "manifest", MANIFEST_PATH, "invalid release path", number)
    if len(entries) != len(set(entries)):
        add(findings, "manifest", MANIFEST_PATH, "duplicate release paths are not allowed")
    if entries != sorted(entries):
        add(findings, "manifest", MANIFEST_PATH, "release paths must be sorted")
    if tuple(entries) != REQUIRED_RELEASE_FILES:
        add(findings, "manifest", MANIFEST_PATH, "manifest differs from the locked release surface")
    return entries


def parse_scalar(raw: str) -> str | None:
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, str) else None
    if re.fullmatch(r"[A-Za-z0-9$][A-Za-z0-9$ ._:/-]*", raw):
        return raw
    return None


def validate_skill_frontmatter(text: str, findings: list[Finding]) -> None:
    path = "SKILL.md"
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        add(findings, "frontmatter", path, "opening delimiter is missing", 1)
        return
    try:
        closing = lines.index("---", 1)
    except ValueError:
        add(findings, "frontmatter", path, "closing delimiter is missing")
        return
    if closing > 20:
        add(findings, "frontmatter", path, "frontmatter is unexpectedly long")
        return

    values: dict[str, str] = {}
    for index, line in enumerate(lines[1:closing], 2):
        match = re.fullmatch(r"([a-z][a-z0-9_-]*):[ ]+(.+)", line)
        if not match:
            add(findings, "frontmatter", path, "unsupported YAML form", index)
            continue
        key, raw = match.groups()
        if key in values:
            add(findings, "frontmatter", path, "duplicate key", index)
            continue
        value = parse_scalar(raw)
        if value is None:
            add(findings, "frontmatter", path, "scalar must use the constrained form", index)
            continue
        if key == "description" and not raw.startswith('"'):
            add(findings, "frontmatter", path, "description must be a double-quoted string", index)
        values[key] = value

    if set(values) != {"name", "description"}:
        add(findings, "frontmatter", path, "only name and description are allowed")
    if values.get("name") != SKILL_NAME:
        add(findings, "frontmatter", path, "Skill name does not match the release name")
    description = values.get("description", "")
    if description != description.strip() or not 20 <= len(description) <= 1_024:
        add(findings, "frontmatter", path, "description length is outside the accepted range")
    if "<" in description or ">" in description:
        add(findings, "frontmatter", path, "description must not contain angle brackets")
    if not any(line.strip() for line in lines[closing + 1 :]):
        add(findings, "frontmatter", path, "Skill body is empty")


def validate_openai_yaml(text: str, findings: list[Finding]) -> None:
    path = "agents/openai.yaml"
    lines = text.splitlines()
    if not lines or lines[0] != "interface:":
        add(findings, "agent-metadata", path, "expected a single interface mapping", 1)
        return
    values: dict[str, str] = {}
    for number, line in enumerate(lines[1:], 2):
        if not line:
            continue
        match = re.fullmatch(r"  ([a-z][a-z0-9_]*):[ ]+(.+)", line)
        if not match:
            add(findings, "agent-metadata", path, "unsupported YAML form", number)
            continue
        key, raw = match.groups()
        if key in values:
            add(findings, "agent-metadata", path, "duplicate key", number)
            continue
        value = parse_scalar(raw)
        if value is None or not raw.startswith('"'):
            add(findings, "agent-metadata", path, "values must be double-quoted strings", number)
            continue
        values[key] = value

    required = {"display_name", "short_description", "default_prompt"}
    if set(values) != required:
        add(findings, "agent-metadata", path, "interface keys do not match the required schema")
    if values.get("display_name") != DISPLAY_TITLE:
        add(findings, "agent-metadata", path, "display title does not match the public title")
    short_description = values.get("short_description", "")
    if short_description != short_description.strip() or not 25 <= len(short_description) <= 64:
        add(findings, "agent-metadata", path, "short description length is outside the accepted range")
    prompt = values.get("default_prompt", "")
    if not 10 <= len(prompt) <= 1_000 or f"${SKILL_NAME}" not in prompt:
        add(findings, "agent-metadata", path, "default prompt must invoke the released Skill")


def validate_links(repo: Path, relative: str, text: str, findings: list[Finding]) -> None:
    source = repo / PurePosixPath(relative)
    for match in MARKDOWN_LINK.finditer(text):
        raw = match.group(1).strip()
        if raw.startswith("<") and ">" in raw:
            target = raw[1 : raw.index(">")]
        else:
            target = raw.split(maxsplit=1)[0]
        if not target or target.startswith("#"):
            continue
        split = urlsplit(target)
        if split.scheme:
            if split.scheme.lower() not in {"http", "https", "mailto"}:
                add(findings, "link", relative, "unsupported link scheme", line_number(text, match.start()))
            continue
        if split.netloc or split.path.startswith("/") or "\\" in split.path:
            add(findings, "link", relative, "relative link escapes the portable release", line_number(text, match.start()))
            continue
        decoded = unquote(split.path)
        if not decoded:
            continue
        target_path = (source.parent / PurePosixPath(decoded)).resolve()
        try:
            target_path.relative_to(repo)
        except ValueError:
            add(findings, "link", relative, "relative link leaves the repository", line_number(text, match.start()))
            continue
        if not target_path.is_file() or is_link_like(target_path):
            add(findings, "link", relative, "relative link target is not a regular repository file", line_number(text, match.start()))


def validate_sensitive_content(relative: str, text: str, findings: list[Finding]) -> None:
    for label, pattern in SECRET_RULES:
        for match in pattern.finditer(text):
            add(findings, "secret", relative, f"possible {label} material", line_number(text, match.start()))
    for pattern in (WINDOWS_ABSOLUTE, UNC_ABSOLUTE, POSIX_PRIVATE):
        for match in pattern.finditer(text):
            add(findings, "private-path", relative, "possible private absolute path", line_number(text, match.start()))
    if relative != "LICENSE":
        for pattern in (PLACEHOLDER, PUBLICATION_PLACEHOLDER, EXAMPLE_DOMAIN):
            for match in pattern.finditer(text):
                add(findings, "placeholder", relative, "unfinished publication placeholder", line_number(text, match.start()))


def validate_workflow(text: str, findings: list[Finding]) -> None:
    required_fragments = (
        "pull_request:",
        "push:",
        "- main",
        "tags:",
        '- "v*.*.*"',
        "workflow_dispatch:",
        "permissions:\n  contents: read",
        "concurrency:",
        "runs-on: ubuntu-24.04",
        "timeout-minutes: 5",
        'PYTHONUTF8: "1"',
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "persist-credentials: false",
        "python3 -X utf8 -I -B ci/validate_release.py --self-test",
        "python3 -X utf8 -I -B ci/validate_release.py",
        "python3 -X utf8 -I -B evaluations/run_all.py",
        "Validate, build, and revalidate deterministic archive",
        "--archive",
    )
    for fragment in required_fragments:
        if fragment not in text:
            add(findings, "workflow", ".github/workflows/quality-gate.yml", "required quality-gate setting is missing")
    forbidden_fragments = ("pull_request_target:", "persist-credentials: true")
    for fragment in forbidden_fragments:
        if fragment in text:
            add(findings, "workflow", ".github/workflows/quality-gate.yml", "unsafe workflow setting is present")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("uses:") and not re.fullmatch(r"uses: [A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}(?: +#.*)?", stripped):
            add(findings, "workflow", ".github/workflows/quality-gate.yml", "actions must be pinned to a full commit SHA")
        if re.search(r"(?:^|[{: ,])write(?:-all)?(?:$|[}, #])", stripped):
            add(findings, "workflow", ".github/workflows/quality-gate.yml", "write permissions are not allowed")


def validate_release_tag(ref_type: str, ref_name: str, findings: list[Finding]) -> None:
    if ref_type == "tag" and not SEMVER_TAG.fullmatch(ref_name):
        add(findings, "release-tag", "GITHUB_REF_NAME", "release tags must use the exact vMAJOR.MINOR.PATCH form")


def validate_license(data: bytes, findings: list[Finding]) -> None:
    digest = hashlib.sha256(data).hexdigest()
    if digest != LICENSE_SHA256:
        add(findings, "license", "LICENSE", "Apache-2.0 license text is missing or modified")


def validate_release(repo: Path) -> tuple[list[Finding], list[str], int]:
    repo = repo.resolve()
    findings: list[Finding] = []
    if not repo.is_dir():
        add(findings, "repository", ".", "repository root is not a directory")
        return findings, [], 0

    validate_release_tag(os.environ.get("GITHUB_REF_TYPE", ""), os.environ.get("GITHUB_REF_NAME", ""), findings)

    entries = read_manifest(repo, findings)
    actual = repository_files(repo, findings)
    expected = set(entries)
    for relative in sorted(actual - expected):
        add(findings, "unexpected-file", relative, "file is outside the release allowlist")
    for relative in sorted(expected - actual):
        add(findings, "missing-file", relative, "allowlisted release file is missing")

    texts: dict[str, str] = {}
    blobs: dict[str, bytes] = {}
    documents: dict[str, object] = {}
    total = 0
    for relative in entries:
        path = repo / PurePosixPath(relative)
        if relative not in actual or not path.is_file():
            continue
        size = path.stat().st_size
        total += size
        validate_file_policy(relative, size, findings)
        parsed = strict_utf8(path, relative, findings)
        if parsed is None:
            continue
        data, text = parsed
        blobs[relative] = data
        texts[relative] = text
        validate_sensitive_content(relative, text, findings)
        if relative.endswith(".md"):
            validate_links(repo, relative, text, findings)
        if relative.endswith(".json"):
            document = validate_json_document(relative, text, findings)
            if document is not None:
                documents[relative] = document
        if relative.endswith(".py"):
            validate_python_source(relative, text, findings)

    if total > MAX_RELEASE_BYTES:
        add(findings, "size", ".", "release exceeds the total size limit")
    if "SKILL.md" in texts:
        validate_skill_frontmatter(texts["SKILL.md"], findings)
    if "agents/openai.yaml" in texts:
        validate_openai_yaml(texts["agents/openai.yaml"], findings)
    if ".github/workflows/quality-gate.yml" in texts:
        validate_workflow(texts[".github/workflows/quality-gate.yml"], findings)
    if "LICENSE" in blobs:
        validate_license(blobs["LICENSE"], findings)
    validate_project_artifacts(repo, documents, findings)
    validate_ai_skill_binding(repo, documents, findings)

    return sorted(set(findings)), entries, total


def write_zip(repo: Path, entries: list[str], destination: Path) -> None:
    prefix = f"{SKILL_NAME}/"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
        archive.comment = b""
        for relative in sorted(entries):
            info = zipfile.ZipInfo(prefix + relative, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = ZIP_MODE << 16
            info.extra = b""
            info.comment = b""
            archive.writestr(info, (repo / PurePosixPath(relative)).read_bytes())


def verify_zip(repo: Path, entries: list[str], archive_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    prefix = f"{SKILL_NAME}/"
    expected_names = [prefix + relative for relative in sorted(entries)]
    with zipfile.ZipFile(archive_path, "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if names != expected_names or len(names) != len(set(names)):
            add(findings, "archive", archive_path.name, "archive member list differs from the release manifest")
            return findings
        for info, relative in zip(infos, sorted(entries)):
            if (
                info.date_time != ZIP_TIMESTAMP
                or info.compress_type != zipfile.ZIP_STORED
                or info.create_system != 3
                or (info.external_attr >> 16) != ZIP_MODE
                or info.extra
                or info.comment
            ):
                add(findings, "archive", archive_path.name, "archive metadata is not deterministic")
            if archive.read(info) != (repo / PurePosixPath(relative)).read_bytes():
                add(findings, "archive", archive_path.name, "archive content differs from the validated source")

        with tempfile.TemporaryDirectory(prefix="skill-archive-check-") as temporary:
            extracted_root = Path(temporary) / SKILL_NAME
            for info, relative in zip(infos, sorted(entries)):
                destination = extracted_root / PurePosixPath(relative)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(info))
            nested_findings, _, _ = validate_release(extracted_root)
            if nested_findings:
                add(findings, "archive", archive_path.name, "extracted archive failed release revalidation")
    return findings


def build_archive(repo: Path, entries: list[str], destination: Path) -> tuple[str, list[Finding]]:
    repo = repo.resolve()
    destination = destination.resolve()
    try:
        destination.relative_to(repo)
    except ValueError:
        pass
    else:
        return "", [Finding("archive", destination.name, 0, "archive destination must be outside the repository")]
    if destination.exists():
        return "", [Finding("archive", destination.name, 0, "refusing to overwrite an existing archive destination")]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="skill-archive-build-") as temporary:
        first = Path(temporary) / "first.zip"
        second = Path(temporary) / "second.zip"
        write_zip(repo, entries, first)
        write_zip(repo, entries, second)
        first_bytes = first.read_bytes()
        if first_bytes != second.read_bytes():
            return "", [Finding("archive", destination.name, 0, "repeated archive builds are not byte-identical")]
        findings = verify_zip(repo, entries, first)
        if findings:
            return "", findings
        try:
            with destination.open("xb") as output:
                output.write(first_bytes)
        except FileExistsError:
            return "", [Finding("archive", destination.name, 0, "refusing to overwrite an existing archive destination")]
    return hashlib.sha256(first_bytes).hexdigest(), []


def run_self_test() -> int:
    assertions = 0

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(f"SELF-TEST FAIL: {message}")

    findings: list[Finding] = []
    secret = "gh" + "p_" + ("A" * 32)
    validate_sensitive_content("sample.md", secret, findings)
    require(any(item.category == "secret" for item in findings), "GitHub token was not detected")
    assertions += 1

    findings = []
    private_path = "C:" + "\\" + "Users" + "\\" + "person" + "\\" + "notes.txt"
    validate_sensitive_content("sample.md", private_path, findings)
    require(any(item.category == "private-path" for item in findings), "private path was not detected")
    assertions += 1

    findings = []
    placeholder = "OWN" + "ER"
    validate_sensitive_content("sample.md", placeholder, findings)
    require(any(item.category == "placeholder" for item in findings), "publication placeholder was not detected")
    assertions += 1

    findings = []
    validate_sensitive_content("sample.md", "ordinary public documentation", findings)
    require(not findings, "ordinary documentation caused a sensitive-content finding")
    assertions += 1

    findings = []
    validate_file_policy("private-source.pdf", 1, findings)
    require(any(item.category == "file-type" for item in findings), "forbidden PDF was not detected")
    assertions += 1

    findings = []
    validate_json_document("result.json", '{"a": 1, "a": 2, "b": NaN}\n', findings)
    require(any(item.category == "json" for item in findings), "non-strict JSON was accepted")
    assertions += 1

    findings = []
    validate_python_source("evaluate.py", "def broken(:\n", findings)
    require(any(item.category == "python" for item in findings), "invalid Python source was accepted")
    assertions += 1

    findings = []
    validate_workflow("permissions: {contents: write}\npersist-credentials: true\n", findings)
    require(any(item.message == "write permissions are not allowed" for item in findings), "inline write permission was accepted")
    require(any(item.message == "unsafe workflow setting is present" for item in findings), "persisted checkout credentials were accepted")
    assertions += 1

    findings = []
    validate_release_tag("tag", "v1.2.3", findings)
    require(not findings, "valid semantic-version tag was rejected")
    validate_release_tag("tag", "v1.2.3.4", findings)
    require(any(item.category == "release-tag" for item in findings), "overlong semantic-version tag was accepted")
    findings = []
    validate_release_tag("tag", "v1١.2.3", findings)
    require(any(item.category == "release-tag" for item in findings), "Unicode digits were accepted in a release tag")
    assertions += 1

    with tempfile.TemporaryDirectory(prefix="skill-validator-test-") as temporary:
        root = Path(temporary).resolve()
        docs = root / "docs"
        docs.mkdir()
        (docs / "target.md").write_text("target\n", encoding="utf-8", newline="\n")
        findings = []
        validate_links(root, "docs/source.md", "[ok](target.md)\n", findings)
        require(not findings, "valid relative link was rejected")
        assertions += 1
        validate_links(root, "docs/source.md", "[escape](../../outside.md)\n", findings)
        require(any(item.category == "link" for item in findings), "escaping relative link was accepted")
        assertions += 1

        findings = []
        (docs / "directory-target").mkdir()
        validate_links(root, "docs/source.md", "[directory](directory-target)\n", findings)
        require(any(item.category == "link" for item in findings), "directory link target was accepted")
        assertions += 1

        invalid_utf8 = root / "invalid.txt"
        invalid_utf8.write_bytes(b"\xff\xfe")
        findings = []
        require(strict_utf8(invalid_utf8, "invalid.txt", findings) is None, "invalid UTF-8 decoded successfully")
        require(any(item.category == "encoding" for item in findings), "invalid UTF-8 produced no encoding finding")
        assertions += 1

        try:
            linked = root / "linked.txt"
            linked.symlink_to(docs / "target.md")
        except OSError:
            pass
        else:
            findings = []
            repository_files(root, findings)
            require(any(item.category == "symlink" for item in findings), "supported symlink was not detected")
            assertions += 1

        payload = root / "payload"
        payload.mkdir()
        (payload / "a.txt").write_bytes(b"alpha\n")
        (payload / "b.txt").write_bytes(b"beta\n")
        first = root / "a.zip"
        second = root / "b.zip"
        write_zip(payload, ["a.txt", "b.txt"], first)
        write_zip(payload, ["a.txt", "b.txt"], second)
        require(first.read_bytes() == second.read_bytes(), "deterministic ZIP builds differ")
        assertions += 1

        protected = payload / "protected.md"
        protected.write_bytes(b"keep\n")
        _, archive_findings = build_archive(payload, ["a.txt"], protected)
        require(any(item.category == "archive" for item in archive_findings), "in-repository archive destination was accepted")
        require(protected.read_bytes() == b"keep\n", "in-repository file was overwritten by archive build")
        assertions += 1

    findings = []
    valid_skill = f'---\nname: {SKILL_NAME}\ndescription: "A sufficiently detailed description for this validation test."\n---\n\n# Body\n'
    validate_skill_frontmatter(valid_skill, findings)
    require(not findings, "valid Skill frontmatter was rejected")
    assertions += 1

    findings = []
    valid_agent = (
        "interface:\n"
        f'  display_name: "{DISPLAY_TITLE}"\n'
        '  short_description: "A valid compact public description"\n'
        f'  default_prompt: "Use ${SKILL_NAME} for this task."\n'
    )
    validate_openai_yaml(valid_agent, findings)
    require(not findings, "valid agent metadata was rejected")
    assertions += 1

    findings = []
    validate_openai_yaml("interface:\n  display_name: [invalid]\n", findings)
    require(any(item.category == "agent-metadata" for item in findings), "malformed agent metadata was accepted")
    assertions += 1

    print(f"SELF-TEST PASS ({assertions} assertions)")
    return 0


def print_findings(findings: list[Finding]) -> None:
    for finding in findings:
        print(finding.render(), file=sys.stderr)
    print(f"VALIDATION FAIL ({len(findings)} finding(s))", file=sys.stderr)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run built-in validator tests")
    parser.add_argument("--repo", type=Path, help="repository root")
    parser.add_argument("--skill", type=Path, help="Skill root; must equal the repository root")
    parser.add_argument("--archive", type=Path, help="write a deterministic ZIP after validation")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        result = run_self_test()
        if not (args.repo or args.skill or args.archive):
            return result
    if args.repo is None or args.skill is None:
        print("--repo and --skill are required unless only --self-test is used", file=sys.stderr)
        return 2

    repo = args.repo.resolve()
    skill = (repo / args.skill).resolve() if not args.skill.is_absolute() else args.skill.resolve()
    if skill != repo:
        print("VALIDATION FAIL: repository root must equal Skill root", file=sys.stderr)
        return 2

    findings, entries, total = validate_release(repo)
    if findings:
        print_findings(findings)
        return 1
    print(f"VALIDATION PASS ({len(entries)} files, {total} bytes)")

    if args.archive is not None:
        digest, archive_findings = build_archive(repo, entries, args.archive)
        if archive_findings:
            print_findings(archive_findings)
            return 1
        print(f"ARCHIVE PASS ({args.archive.name}, sha256={digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
