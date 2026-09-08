"""HPC-1: pure, bounded synthetic-note changeset validation. NOT an applier.

No filesystem/Git/database/network access or execution of proposed content.
Caller context is assumed, NOT authenticated; valid does not mean approved/secure.
"""
from dataclasses import dataclass, field
import hashlib
import json
import re


PROFILE = "hpc1_synthetic_notes_v1"
MAX_REQUEST = 1024 * 1024
MAX_FILE = 256 * 1024
MAX_TOTAL = 768 * 1024
MAX_FILES = 10
MAX_BASE_FILES = 64
MAX_BASE_BYTES = 4 * 1024 * 1024
MAX_DEPTH = 6
MAX_STRUCTURE = 4096
MAX_PATH = 180
MAX_SEGMENTS = 12
MAX_GENERATION = 2**31 - 1
ENVELOPE_KEYS = {"schema_version", "job_id", "generation", "base_manifest_sha256", "changes"}
CHANGE_KEYS = {"path", "operation", "before_sha256", "content_utf8"}
RESERVED = {"con", "prn", "aux", "nul", *[f"com{i}" for i in range(1, 10)], *[f"lpt{i}" for i in range(1, 10)]}
INSTRUCTION_FILES = {"agents.md", "claude.md", "gemini.md", "skill.md", "copilot-instructions.md"}


class ValidationError(ValueError):
    """Static code only; never include untrusted content, filenames or JSON errors."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValidationError(code)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def object_digest(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii"))


def note_path(value: str) -> str:
    require(type(value) is str and 0 < len(value) <= MAX_PATH, "PATH_INVALID")
    parts = value.split("/")
    require(len(parts) <= MAX_SEGMENTS, "PATH_INVALID")
    for part in parts:
        require(bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", part)) and not part.endswith("."), "PATH_INVALID")
        require(part.split(".", 1)[0].lower() not in RESERVED, "PATH_INVALID")
        require(part.lower() not in INSTRUCTION_FILES, "PROTECTED_PATH")
    require(len(parts) >= 3 and parts[:2] == ["docs", "notes"] and parts[-1].endswith(".md"), "PROTECTED_PATH")
    return value


def check_tree(paths) -> None:
    """Reject file/directory and component-case aliases, including baseline paths."""
    paths = set(paths)
    file_keys = {p.casefold() for p in paths}
    prefixes = {}
    for path in sorted(paths):
        parts = path.split("/")
        for count in range(1, len(parts) + 1):
            prefix = "/".join(parts[:count])
            key = prefix.casefold()
            require(key not in prefixes or prefixes[key] == prefix, "PATH_COLLISION")
            require(count == len(parts) or key not in file_keys, "PATH_COLLISION")
            prefixes[key] = prefix


def utf8_bytes(value: str, limit: int) -> bytes:
    require(type(value) is str, "TEXT_INVALID")
    require(len(value) <= limit, "CONTENT_LIMIT")
    require(not value.startswith("\ufeff") and "\0" not in value, "TEXT_INVALID")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError:
        raise ValidationError("TEXT_INVALID") from None
    require(len(encoded) <= limit, "CONTENT_LIMIT")
    return encoded


@dataclass(frozen=True, slots=True)
class BaseFile:
    path: str
    content: bytes = field(repr=False)


@dataclass(frozen=True, slots=True)
class Grant:
    path: str
    operation: str


@dataclass(frozen=True, slots=True)
class ValidationContext:
    job_id: str
    generation: int
    baseline: tuple[BaseFile, ...] = field(repr=False)
    allowed: tuple[Grant, ...] = field(repr=False)

    @property
    def base_manifest_sha256(self) -> str:
        return context_info(self)[2]


def context_info(context: ValidationContext) -> tuple:
    require(type(context) is ValidationContext, "CONTEXT_INVALID")
    require(type(context.job_id) is str and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{2,63}", context.job_id)), "CONTEXT_INVALID")
    require(type(context.generation) is int and 1 <= context.generation <= MAX_GENERATION, "CONTEXT_INVALID")
    require(type(context.baseline) is tuple and len(context.baseline) <= MAX_BASE_FILES, "CONTEXT_LIMIT")
    require(type(context.allowed) is tuple and 1 <= len(context.allowed) <= MAX_FILES, "CONTEXT_LIMIT")
    baseline, allowed, total = {}, {}, 0
    for item in context.baseline:
        require(type(item) is BaseFile, "CONTEXT_INVALID")
        path = note_path(item.path)
        require(path not in baseline and type(item.content) is bytes, "CONTEXT_INVALID")
        total += len(item.content)
        require(total <= MAX_BASE_BYTES, "CONTEXT_LIMIT")
        try:
            decoded = item.content.decode("utf-8", errors="strict")
        except UnicodeError:
            raise ValidationError("TEXT_INVALID") from None
        utf8_bytes(decoded, MAX_BASE_BYTES)
        baseline[path] = item.content
    for item in context.allowed:
        require(type(item) is Grant, "CONTEXT_INVALID")
        path = note_path(item.path)
        require(path not in allowed and type(item.operation) is str and item.operation in {"create", "update"}, "CONTEXT_INVALID")
        allowed[path] = item.operation
    check_tree([*baseline, *allowed])
    manifest = object_digest({"profile": PROFILE, "files": [
        [path, "regular_utf8", sha256(data)] for path, data in sorted(baseline.items())
    ]})
    binding = object_digest({"profile": PROFILE, "job_id": context.job_id,
                             "generation": context.generation, "base_manifest_sha256": manifest,
                             "allowed": sorted(allowed.items())})
    return baseline, allowed, manifest, binding


def make_context(*, job_id: str, generation: int, baseline: dict[str, bytes], allowed: dict[str, str]) -> ValidationContext:
    """Copy caller-supplied synthetic data; never discover/read a real directory."""
    require(type(baseline) is dict and type(allowed) is dict, "CONTEXT_INVALID")
    require(len(baseline) <= MAX_BASE_FILES and 1 <= len(allowed) <= MAX_FILES, "CONTEXT_LIMIT")
    context = ValidationContext(job_id, generation,
                                tuple(BaseFile(p, b) for p, b in baseline.items()),
                                tuple(Grant(p, op) for p, op in allowed.items()))
    context_info(context)
    return context


def bounded_json(raw: bytes) -> dict:
    require(type(raw) is bytes, "REQUEST_TYPE")
    require(0 < len(raw) <= MAX_REQUEST, "REQUEST_LIMIT")
    require(not raw.startswith(b"\xef\xbb\xbf"), "JSON_ENCODING")
    # Bound nesting/structural allocation BEFORE calling json.loads. Quotes/escapes
    # are scanned, but full grammar validation belongs to the standard decoder.
    depth = structure = 0
    quoted = escaped = False
    for char in raw:
        if quoted:
            if escaped:
                escaped = False
            elif char == 92:
                escaped = True
            elif char == 34:
                quoted = False
        elif char == 34:
            quoted = True
        elif char in (123, 91):
            depth += 1
            structure += 1
            require(depth <= MAX_DEPTH, "JSON_DEPTH")
        elif char in (125, 93):
            depth -= 1
            require(depth >= 0, "JSON_INVALID")
        elif char in (44, 58):
            structure += 1
        require(structure <= MAX_STRUCTURE, "JSON_STRUCTURE_LIMIT")

    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, "JSON_DUPLICATE_KEY")
            value[key] = item
        return value

    def integer(value):
        require(len(value) <= 10, "JSON_NUMBER")
        return int(value)

    def reject_number(_):
        raise ValidationError("JSON_NUMBER")

    try:
        result = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=unique,
                            parse_int=integer, parse_float=reject_number, parse_constant=reject_number)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValidationError("JSON_INVALID") from None
    require(type(result) is dict, "ENVELOPE_SCHEMA")
    return result


@dataclass(frozen=True, slots=True)
class Change:
    path: str
    operation: str
    before_sha256: str | None
    content: bytes = field(repr=False)


@dataclass(frozen=True, slots=True)
class ValidatedCandidate:
    """Diagnostic changeset identity; NOT a sealed tree, receipt, grant or approval."""
    job_id: str
    generation: int
    base_manifest_sha256: str
    context_sha256: str
    request_sha256: str
    candidate_sha256: str
    changes: tuple[Change, ...] = field(repr=False)

    def summary(self) -> dict:
        return {"status": "valid_in_memory_only", "profile": PROFILE,
                "files": len(self.changes), "content_bytes": sum(len(c.content) for c in self.changes),
                "candidate_sha256": self.candidate_sha256,
                "authority": "NOT_approval_or_filesystem_enforcement"}


def valid_hash(value) -> bool:
    return type(value) is str and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def validate_changeset(raw: bytes, *, context: ValidationContext) -> ValidatedCandidate:
    payload = bounded_json(raw)
    require(set(payload) == ENVELOPE_KEYS, "ENVELOPE_SCHEMA")
    require(type(payload["schema_version"]) is int and payload["schema_version"] == 1, "ENVELOPE_SCHEMA")
    require(type(payload["job_id"]) is str and type(payload["generation"]) is int, "ENVELOPE_SCHEMA")
    require(valid_hash(payload["base_manifest_sha256"]), "HASH_INVALID")
    baseline, allowed, manifest, binding = context_info(context)
    require(payload["job_id"] == context.job_id and payload["generation"] == context.generation, "CONTEXT_MISMATCH")
    require(payload["base_manifest_sha256"] == manifest, "BASE_MISMATCH")
    items = payload["changes"]
    require(type(items) is list and 1 <= len(items) <= MAX_FILES, "CHANGE_COUNT")
    changes, paths, total = [], set(), 0
    for item in items:
        require(type(item) is dict and set(item) == CHANGE_KEYS, "CHANGE_SCHEMA")
        path = note_path(item["path"])
        require(path not in paths, "DUPLICATE_CHANGE")
        paths.add(path)
        operation = item["operation"]
        require(type(operation) is str and operation in {"create", "update"}, "OPERATION_UNSUPPORTED")
        require(allowed.get(path) == operation, "OUT_OF_SCOPE")
        before = item["before_sha256"]
        if operation == "create":
            require(before is None, "BEFORE_INVALID")
            require(path not in baseline, "CREATE_EXISTS")
        else:
            require(valid_hash(before), "HASH_INVALID")
            require(path in baseline, "UPDATE_MISSING")
            require(before == sha256(baseline[path]), "BEFORE_MISMATCH")
        content = utf8_bytes(item["content_utf8"], MAX_FILE)
        total += len(content)
        require(total <= MAX_TOTAL, "TOTAL_CONTENT_LIMIT")
        changes.append(Change(path, operation, before, content))
    check_tree([*baseline, *paths])
    ordered = tuple(sorted(changes, key=lambda change: change.path))
    digest = object_digest({"context_sha256": binding, "changes": [
        [c.path, c.operation, c.before_sha256, sha256(c.content)] for c in ordered
    ]})
    return ValidatedCandidate(context.job_id, context.generation, manifest, binding,
                              sha256(raw), digest, ordered)


def demo() -> list[dict]:
    """Built-in synthetic observations only; no file/CLI payload inputs."""
    context = make_context(job_id="synthetic-demo", generation=1, baseline={},
                           allowed={"docs/notes/example.md": "create"})
    payload = {"schema_version": 1, "job_id": context.job_id, "generation": 1,
               "base_manifest_sha256": context.base_manifest_sha256,
               "changes": [{"path": "docs/notes/example.md", "operation": "create",
                            "before_sha256": None, "content_utf8": "Ví dụ synthetic, chưa áp dụng.\n"}]}
    good = validate_changeset(json.dumps(payload, ensure_ascii=False).encode("utf-8"), context=context)
    payload["changes"][0]["path"] = "docs/notes/not-granted.md"
    try:
        validate_changeset(json.dumps(payload).encode("utf-8"), context=context)
    except ValidationError as exc:
        return [good.summary(), {"status": "rejected", "code": exc.code, "applied": False}]
    raise AssertionError("Synthetic out-of-scope demonstration was not rejected")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", required=True, help="Built-in synthetic validation only")
    parser.parse_args()
    print(json.dumps(demo(), ensure_ascii=True, indent=2))
