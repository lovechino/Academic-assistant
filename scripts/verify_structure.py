"""Read-only scaffold checks. Does not run audit helpers or product code."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    "AGENTS.md", "README.md", ".gitignore", ".gitattributes",
    "ai-core/README.md", "backend/README.md", "frontend/README.md",
    "ai-core/src/academic_ai/domain/README.md",
    "ai-core/src/academic_ai/application/README.md",
    "ai-core/src/academic_ai/ingestion/README.md",
    "ai-core/src/academic_ai/retrieval/README.md",
    "ai-core/src/academic_ai/agents/README.md",
    "ai-core/src/academic_ai/infrastructure/README.md",
    "ai-core/prompts/README.md", "ai-core/evaluation/README.md",
    "ai-core/experiments/README.md", "ai-core/tests/README.md",
    "backend/src/academic_backend/api/README.md",
    "backend/src/academic_backend/application/README.md",
    "backend/src/academic_backend/domain/README.md",
    "backend/src/academic_backend/infrastructure/README.md",
    "backend/src/academic_backend/workers/README.md",
    "backend/migrations/README.md", "backend/tests/README.md",
    "frontend/src/app/README.md", "frontend/src/features/README.md",
    "frontend/src/components/README.md", "frontend/src/lib/README.md",
    "frontend/public/README.md", "frontend/tests/README.md",
    "contracts/README.md", "contracts/ai-core.md", "contracts/http-api.md",
    "infra/README.md", "tests/README.md", "scripts/README.md",
    "docs/README.md", "docs/architecture/04-source-layout.md",
    "data/README.md",
)
HELPERS = (
    "ai-core/experiments/pdf-pilot/profile_local.py",
    "ai-core/experiments/pdf-pilot/audit_layout_order.py",
)
SOURCE_FOLDERS = ("ai-core", "backend", "frontend", "contracts", "infra", "scripts", "tests", "docs")
IGNORED_DIRS = {"node_modules", ".venv", "venv", "__pycache__", ".next", "dist", "build"}


def source_files(extension: str) -> list[Path]:
    return sorted({
        path
        for folder in SOURCE_FOLDERS
        for path in (ROOT / folder).rglob(f"*{extension}")
        if not any(part in IGNORED_DIRS for part in path.relative_to(ROOT).parts)
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-local-data", action="store_true")
    args = parser.parse_args()
    failures: list[str] = []
    skipped: list[str] = []
    checks = 0

    def check(condition: bool, label: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(label)

    for relative in (*REQUIRED_PATHS, *HELPERS):
        check((ROOT / relative).is_file(), f"Missing scaffold file: {relative}")

    python_files = source_files(".py")
    parsed: dict[Path, ast.Module] = {}
    for path in python_files:
        try:
            parsed[path] = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            check(True, str(path))
        except (SyntaxError, UnicodeError) as exc:
            check(False, f"Python syntax: {path.relative_to(ROOT)}: {exc}")

    expected_root = ast.dump(ast.parse("Path(__file__).resolve().parents[3]", mode="eval").body)
    for relative in HELPERS:
        path = ROOT / relative
        tree = parsed.get(path)
        roots = [] if tree is None else [
            node.value for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "ROOT" for target in node.targets)
        ]
        check(len(roots) == 1 and ast.dump(roots[0]) == expected_root,
              f"Helper ROOT assignment changed unexpectedly: {relative}")
        check(path.resolve().parents[3] == ROOT, f"Helper resolves wrong repo root: {relative}")
    check(not (ROOT / "research/pdf-pilot/profile_local.py").exists(), "Old profile helper still exists")
    check(not (ROOT / "research/pdf-pilot/audit_layout_order.py").exists(), "Old layout helper still exists")

    markdown_files = source_files(".md") + [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "data/README.md"]
    for path in markdown_files:
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8-sig")
        # Current source docs use inline links, without nested parentheses in local targets.
        for match in re.finditer(r"\]\(([^)]+)\)", body):
            target = match.group(1).strip().strip("<>")
            if target.startswith("#") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
                continue
            target = unquote(target.split("#", 1)[0])
            resolved = (path.parent / target).resolve()
            label = f"Local link: {path.relative_to(ROOT)} -> {target}"
            if resolved.is_relative_to(ROOT / "data") and not resolved.exists() and not args.require_local_data:
                skipped.append(label)
            else:
                check(resolved.exists(), label)

    manifest_path = ROOT / "data/raw/pdf-pilot/manifest.json"
    verified_sources = 0
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for item in manifest:
                path = (ROOT / item["local_path"]).resolve()
                if not path.is_relative_to(ROOT / "data/raw/pdf-pilot"):
                    check(False, "Manifest points outside the PDF pilot data directory")
                    continue
                if not path.is_file():
                    check(False, f"Missing source: {item['local_path']}")
                    continue
                with path.open("rb") as stream:
                    checksum = hashlib.file_digest(stream, "sha256").hexdigest()
                valid = checksum == item["sha256"]
                check(valid, f"Source hash mismatch: {item['local_path']}")
                verified_sources += int(valid)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            check(False, f"Cannot validate local PDF manifest: {exc}")
    elif args.require_local_data:
        check(False, "Local PDF manifest required but missing")
    else:
        skipped.append("PDF manifest absent: source-only checkout, no corpus hash check")

    print(json.dumps({
        "status": "passed" if not failures else "failed",
        "scope": "source structure, syntax, links and optional source integrity; not runtime or AI quality",
        "checks": checks, "passed": checks - len(failures),
        "python_files_syntax_checked": len(parsed),
        "pdf_source_hashes_verified": verified_sources,
        "skipped": skipped, "failures": failures,
    }, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
