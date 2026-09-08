"""Read-only, Git-visible PRE-PRODUCT placement check; not an import/bug detector.

No product code imports, auto-fix, runtime allowance or approval flag. Python 3.11+.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import stat
import subprocess


ROOT = Path(__file__).resolve().parents[1]
# One marker inventory, also consumed by verify_structure.py.
SCAFFOLD_FILES = (
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
    "infra/README.md", "tests/README.md",
)
# Existing design-only research selection manifest, not a runtime config allowance.
REFERENCE_FILES = {"ai-core/evaluation/profiles/technical-pilot-v0.1.json"}
ROOT_FILES = {"AGENTS.md", "README.md", ".gitignore", ".gitattributes", "LICENSE", "NOTICE"}
RESEARCH_ROOTS = {"docs", "contracts", "data", "scripts"}
COMPONENT_ROOTS = {"ai-core", "backend", "frontend", "infra", "tests"}


def canonical(name: str) -> bool:
    return (isinstance(name, str) and bool(name)
            and not any(c in name for c in "\\:*?[]")
            and not any(ord(c) < 32 for c in name)
            and not PurePosixPath(name).is_absolute()
            and all(part not in {"", ".", ".."} for part in name.split("/")))


def check_paths(names: list[str]) -> dict:
    """Classify names only; caller supplies existing regular Git-visible files."""
    failures = []
    paths = set()
    folded = {}
    for name in sorted(set(names)):
        if not canonical(name):
            failures.append(f"Non-canonical source path: {name!r}")
            continue
        if name.casefold() in folded:
            failures.append(f"Case-colliding paths: {folded[name.casefold()]} / {name}")
        folded[name.casefold()] = name
        paths.add(name)
        parts = PurePosixPath(name).parts
        if name in ROOT_FILES or name in SCAFFOLD_FILES or name in REFERENCE_FILES:
            continue
        if len(parts) > 1 and parts[0] in RESEARCH_ROOTS:
            continue
        if name.startswith("ai-core/experiments/"):
            continue
        if parts[0] in COMPONENT_ROOTS:
            failures.append(f"Pre-product scaffold only; unregistered component file: {name}")
        else:
            failures.append(f"Unregistered source root/file: {name}")
    for name in SCAFFOLD_FILES:
        if name not in paths:
            failures.append(f"Missing source marker: {name}")
    return {
        "status": "failed" if failures else "passed",
        "profile": "pre_product_scaffold_v1",
        "scope": "Git-visible paths and markers only; NOT semantic duplication, imports, runtime safety or GO",
        "files_observed": len(paths),
        "required_markers": len(SCAFFOLD_FILES),
        "failures": failures,
    }


def check_layout(root: Path) -> dict:
    """Do not execute file contents or follow Git-visible symlink/reparse paths."""
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        capture_output=True, check=False, timeout=30,
    )
    if result.returncode:
        raise ValueError("Cannot inventory Git-visible source paths")
    paths, failures = [], []
    for name in sorted(set(result.stdout.decode("utf-8").split("\0")) - {""}):
        if not canonical(name):
            failures.append(f"Non-canonical source path: {name!r}")
            continue
        path = root
        missing, linked = False, False
        for part in PurePosixPath(name).parts:
            path = path / part
            try:
                info = path.lstat()
            except FileNotFoundError:
                missing = True
                break
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                linked = True
                break
        if linked:
            failures.append(f"Linked/reparse source path unsupported: {name}")
        elif not missing:
            if not stat.S_ISREG(info.st_mode):
                failures.append(f"Non-regular Git-visible source file: {name}")
            else:
                paths.append(name)
    report = check_paths(paths)
    report["failures"].extend(failures)
    report["status"] = "failed" if report["failures"] else "passed"
    return report


def main() -> int:
    try:
        report = check_layout(ROOT)
    except (OSError, ValueError, subprocess.SubprocessError):
        report = {"status": "failed", "failures": ["Cannot inspect source layout; no success claim"]}
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return int(report["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
