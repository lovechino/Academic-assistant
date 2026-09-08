"""Exposed synthetic HPC-1 regressions, not OS enforcement or model evaluation."""
from dataclasses import FrozenInstanceError, replace
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "hpc1_validator", Path(__file__).resolve().parents[1] / "harness_patch_validator.py")
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)
P = "docs/notes/example.md"


class PatchValidatorTests(unittest.TestCase):
    def ctx(self, baseline=None, allowed=None, **kwargs):
        return v.make_context(job_id=kwargs.get("job_id", "synthetic-job"),
                              generation=kwargs.get("generation", 1),
                              baseline={} if baseline is None else baseline,
                              allowed={P: "create"} if allowed is None else allowed)

    def payload(self, context=None, content="Kiến thức tiếng Việt.\n"):
        context = context or self.ctx()
        return {"schema_version": 1, "job_id": context.job_id,
                "generation": context.generation,
                "base_manifest_sha256": context.base_manifest_sha256,
                "changes": [{"path": P, "operation": "create",
                             "before_sha256": None, "content_utf8": content}]}

    def raw(self, payload):
        return json.dumps(payload, ensure_ascii=True).encode("utf-8")

    def validate(self, payload, context=None):
        return v.validate_changeset(self.raw(payload), context=context or self.ctx())

    def rejects(self, code, callback):
        with self.assertRaises(v.ValidationError) as result:
            callback()
        self.assertEqual(result.exception.code, code)
        self.assertEqual(str(result.exception), code)

    def test_vietnamese_create_exact_bytes(self):
        content = "Tiếng Việt 😀\r\nnext\n  "
        candidate = self.validate(self.payload(content=content))
        self.assertEqual(candidate.changes[0].content, content.encode("utf-8"))
        self.assertEqual(candidate.summary()["status"], "valid_in_memory_only")

    def test_update_uses_exact_before_and_preserves_newline(self):
        ctx = self.ctx({P: b"old\r\n"}, {P: "update"})
        payload = self.payload(ctx, "new\n")
        payload["changes"][0].update(operation="update", before_sha256=v.sha256(b"old\r\n"))
        self.assertEqual(self.validate(payload, ctx).changes[0].content, b"new\n")
        payload["changes"][0]["before_sha256"] = v.sha256(b"old\n")
        self.rejects("BEFORE_MISMATCH", lambda: self.validate(payload, ctx))

    def test_empty_content_is_syntactically_valid_not_semantic_acceptance(self):
        self.assertEqual(self.validate(self.payload(content="")).changes[0].content, b"")

    def test_exact_envelope_keys(self):
        for key in v.ENVELOPE_KEYS:
            payload = self.payload()
            del payload[key]
            with self.subTest(missing=key):
                self.rejects("ENVELOPE_SCHEMA", lambda: self.validate(payload))
        for key in ("allowed", "approved", "command", "reviewer", "budget"):
            payload = self.payload()
            payload[key] = "untrusted"
            with self.subTest(extra=key):
                self.rejects("ENVELOPE_SCHEMA", lambda: self.validate(payload))

    def test_exact_change_keys(self):
        for key in v.CHANGE_KEYS:
            payload = self.payload()
            del payload["changes"][0][key]
            self.rejects("CHANGE_SCHEMA", lambda: self.validate(payload))
        for key in ("mode", "target", "command", "approved"):
            payload = self.payload()
            payload["changes"][0][key] = "untrusted"
            self.rejects("CHANGE_SCHEMA", lambda: self.validate(payload))

    def test_types_are_not_coerced(self):
        for key, value in (("schema_version", True), ("schema_version", "1"),
                           ("schema_version", 2), ("generation", True),
                           ("generation", "1"), ("job_id", 1)):
            payload = self.payload()
            payload[key] = value
            with self.subTest(key=key, value=value):
                self.rejects("ENVELOPE_SCHEMA", lambda: self.validate(payload))
        for content in (None, True, 1, [], {}):
            self.rejects("TEXT_INVALID", lambda: self.validate(self.payload(content=content)))

    def test_duplicate_json_keys_at_both_levels(self):
        raw = self.raw(self.payload())
        for original, replacement in ((b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1'),
                                      (b'"path":', b'"path": "other", "path":')):
            self.rejects("JSON_DUPLICATE_KEY", lambda: v.validate_changeset(
                raw.replace(original, replacement), context=self.ctx()))

    def test_duplicate_change_rejected_even_same_bytes(self):
        payload = self.payload()
        payload["changes"].append(dict(payload["changes"][0]))
        self.rejects("DUPLICATE_CHANGE", lambda: self.validate(payload))

    def test_wire_types_encoding_and_malformed(self):
        for raw, code in ((bytearray(b"{}"), "REQUEST_TYPE"), ("{}", "REQUEST_TYPE"),
                          (b"", "REQUEST_LIMIT"), (b"\xef\xbb\xbf{}", "JSON_ENCODING"),
                          (b"\xff", "JSON_INVALID"), (b"{", "JSON_INVALID"),
                          (b"}", "JSON_INVALID"), (b"[}", "JSON_INVALID"),
                          (b"{}{}", "JSON_INVALID"), (b"[]", "ENVELOPE_SCHEMA"),
                          (b"null", "ENVELOPE_SCHEMA"), (b"diff --git a b", "JSON_INVALID"),
                          (b"PK\x03\x04", "JSON_INVALID")):
            with self.subTest(raw=repr(raw)):
                self.rejects(code, lambda: v.validate_changeset(raw, context=self.ctx()))

    def test_numbers_float_nonfinite_and_large(self):
        for token in (b"1.0", b"1e0", b"NaN", b"Infinity", b"-Infinity", b"12345678901"):
            self.rejects("JSON_NUMBER", lambda: v.bounded_json(b'{"n":' + token + b'}'))

    def test_depth_limit_before_decoder_and_structure_limit(self):
        self.assertIsInstance(v.bounded_json(b'{"x":' + b'[' * 5 + b'0' + b']' * 5 + b'}'), dict)
        with patch.object(v.json, "loads", side_effect=AssertionError("decoder should not run")):
            self.rejects("JSON_DEPTH", lambda: v.bounded_json(b'[' * 7))
            self.rejects("JSON_STRUCTURE_LIMIT", lambda: v.bounded_json(b'{"x":[' + b'0,' * 4096))

    def test_structural_count_boundary(self):
        raw = b'{"x":[' + b','.join([b'0'] * 4094) + b']}'
        self.assertEqual(len(v.bounded_json(raw)["x"]), 4094)
        self.rejects("JSON_STRUCTURE_LIMIT", lambda: v.bounded_json(raw[:-2] + b',0]}'))

    def test_quoted_structural_characters_and_escapes(self):
        content = '[{,:}]' * 5000 + '\\"\\\\' + '\n'
        self.assertEqual(self.validate(self.payload(content=content)).changes[0].content, content.encode())

    def test_wire_size_boundary(self):
        raw = self.raw(self.payload())
        raw += b' ' * (v.MAX_REQUEST - len(raw))
        self.assertIsInstance(v.validate_changeset(raw, context=self.ctx()), v.ValidatedCandidate)
        self.rejects("REQUEST_LIMIT", lambda: v.validate_changeset(raw + b' ', context=self.ctx()))

    def test_text_surrogate_bom_nul(self):
        for content in ("\ud800", "\udfff", "\ufeffhello", "hello\0world"):
            self.rejects("TEXT_INVALID", lambda: self.validate(self.payload(content=content)))

    def test_file_byte_limit_including_multibyte(self):
        for content in ("a" * v.MAX_FILE, "é" * (v.MAX_FILE // 2)):
            self.assertEqual(len(self.validate(self.payload(content=content)).changes[0].content), v.MAX_FILE)
            self.rejects("CONTENT_LIMIT", lambda: self.validate(self.payload(content=content + "a")))

    def test_decoded_total_boundary(self):
        paths = [f"docs/notes/{i}.md" for i in range(4)]
        ctx = self.ctx(allowed={p: "create" for p in paths})
        payload = self.payload(ctx)
        payload["changes"] = [dict(path=p, operation="create", before_sha256=None,
                                    content_utf8="a" * v.MAX_FILE) for p in paths[:3]]
        self.assertEqual(self.validate(payload, ctx).summary()["content_bytes"], v.MAX_TOTAL)
        payload["changes"].append(dict(path=paths[3], operation="create", before_sha256=None, content_utf8="a"))
        self.rejects("TOTAL_CONTENT_LIMIT", lambda: self.validate(payload, ctx))

    def test_file_count_boundary_and_types(self):
        ctx = self.ctx(allowed={f"docs/notes/{i}.md": "create" for i in range(10)})
        payload = self.payload(ctx)
        payload["changes"] = [dict(path=g.path, operation="create", before_sha256=None, content_utf8="") for g in ctx.allowed]
        self.assertEqual(len(self.validate(payload, ctx).changes), 10)
        for changes in (payload["changes"] + [payload["changes"][0]], [], {}, None, True):
            bad = dict(payload, changes=changes)
            self.rejects("CHANGE_COUNT", lambda: self.validate(bad, ctx))
        payload["changes"] = [None]
        self.rejects("CHANGE_SCHEMA", lambda: self.validate(payload, ctx))

    def test_path_hazards(self):
        for path in ("/docs/notes/a.md", "C:/a.md", "C:a.md", "//server/a.md", "\\\\?\\C:\\a.md",
                     "docs/notes/../a.md", "docs/./notes/a.md", "docs//notes/a.md", "docs\\notes\\a.md",
                     "docs/notes/a.md:stream", "docs/notes/CON.md", "docs/notes/lPt9.foo.md",
                     "docs/notes/a./b.md", "docs/notes/a.md ", "docs/notes/a.md.", "docs/notes/a*.md",
                     "docs/notes/%2e%2e/a.md", "docs/notes/Việt.md", "docs/notes/a\0.md",
                     "docs/notes/a\n.md", "docs/notes/-a.md", "docs/notes/", 1, None):
            with self.subTest(path=repr(path)):
                self.rejects("PATH_INVALID", lambda: v.note_path(path))

    def test_path_length_and_segment_boundaries(self):
        path = "docs/notes/" + "a" * (v.MAX_PATH - len("docs/notes/.md")) + ".md"
        self.assertEqual(v.note_path(path), path)
        self.rejects("PATH_INVALID", lambda: v.note_path(path + "x"))
        path = "docs/notes/" + "a/" * 9 + "a.md"
        self.assertEqual(v.note_path(path), path)
        self.rejects("PATH_INVALID", lambda: v.note_path("docs/notes/a/" + path[len("docs/notes/"):]))

    def test_protected_surfaces_even_if_granted(self):
        for path in ("AGENTS.md", "docs/notes/AGENTS.md", "docs/notes/CLAUDE.md/x.md",
                     "scripts/checker.md", "ai-core/src/a.md", "docs/harness/policy.md",
                     "docs/notes/code.py", "docs/notes/package.json", "Docs/notes/a.md"):
            with self.subTest(path=path):
                self.rejects("PROTECTED_PATH", lambda: self.ctx(allowed={path: "create"}))
        for path in ("docs/notes/.env", "docs/notes/.git/config.md"):
            self.rejects("PATH_INVALID", lambda: self.ctx(allowed={path: "create"}))

    def test_collision_with_baseline_and_directory_case(self):
        pairs = (("docs/notes/a.md", "docs/notes/A.md"),
                 ("docs/notes/Dir/a.md", "docs/notes/dir/b.md"),
                 ("docs/notes/a.md", "docs/notes/a.md/b.md"))
        for a, b in pairs:
            with self.subTest(a=a, b=b):
                self.rejects("PATH_COLLISION", lambda: self.ctx({a: b""}, {b: "create"}))
                self.rejects("PATH_COLLISION", lambda: self.ctx(allowed={a: "create", b: "create"}))

    def test_exact_scope_and_operation(self):
        payload = self.payload()
        payload["changes"][0]["path"] = "docs/notes/ungranted.md"
        self.rejects("OUT_OF_SCOPE", lambda: self.validate(payload))
        payload = self.payload()
        payload["changes"][0]["operation"] = "update"
        self.rejects("OUT_OF_SCOPE", lambda: self.validate(payload))

    def test_unsupported_operations(self):
        for operation in ("delete", "rename", "copy", "binary", "mode", "submodule", "symlink", None, []):
            payload = self.payload()
            payload["changes"][0]["operation"] = operation
            self.rejects("OPERATION_UNSUPPORTED", lambda: self.validate(payload))

    def test_create_and_update_preconditions(self):
        payload = self.payload()
        payload["changes"][0]["before_sha256"] = "0" * 64
        self.rejects("BEFORE_INVALID", lambda: self.validate(payload))
        ctx = self.ctx({P: b"exists"})
        self.rejects("CREATE_EXISTS", lambda: self.validate(self.payload(ctx), ctx))
        ctx = self.ctx(allowed={P: "update"})
        payload = self.payload(ctx)
        payload["changes"][0].update(operation="update", before_sha256="0" * 64)
        self.rejects("UPDATE_MISSING", lambda: self.validate(payload, ctx))
        for value in (None, "A" * 64, "f" * 63, "g" * 64, 1):
            payload["changes"][0]["before_sha256"] = value
            self.rejects("HASH_INVALID", lambda: self.validate(payload, ctx))

    def test_job_generation_base_binding(self):
        for key, value, code in (("job_id", "other-job", "CONTEXT_MISMATCH"),
                                 ("generation", 2, "CONTEXT_MISMATCH"),
                                 ("base_manifest_sha256", "0" * 64, "BASE_MISMATCH"),
                                 ("base_manifest_sha256", "A" * 64, "HASH_INVALID")):
            payload = self.payload()
            payload[key] = value
            self.rejects(code, lambda: self.validate(payload))

    def test_context_validation_and_generation_boundary(self):
        for job in ("", "ab", "x" * 65, "a/b", "a_b", 1):
            self.rejects("CONTEXT_INVALID", lambda: self.ctx(job_id=job))
        for generation in (0, -1, True, "1", v.MAX_GENERATION + 1):
            self.rejects("CONTEXT_INVALID", lambda: self.ctx(generation=generation))
        ctx = self.ctx(generation=v.MAX_GENERATION)
        self.assertEqual(self.validate(self.payload(ctx), ctx).generation, v.MAX_GENERATION)
        self.rejects("CONTEXT_INVALID", lambda: v.context_info({}))

    def test_forged_context_types_and_duplicate_entries(self):
        ctx = self.ctx()
        for forged, code in ((replace(ctx, baseline=[]), "CONTEXT_LIMIT"),
                             (replace(ctx, allowed=()), "CONTEXT_LIMIT"),
                             (replace(ctx, baseline=("bad",)), "CONTEXT_INVALID"),
                             (replace(ctx, baseline=(v.BaseFile(P, bytearray()),)), "CONTEXT_INVALID"),
                             (replace(ctx, baseline=(v.BaseFile(P, b""),) * 2), "CONTEXT_INVALID"),
                             (replace(ctx, allowed=ctx.allowed * 2), "CONTEXT_INVALID"),
                             (replace(ctx, allowed=(v.Grant(P, "delete"),)), "CONTEXT_INVALID")):
            self.rejects(code, lambda: v.context_info(forged))
        self.rejects("CONTEXT_INVALID", lambda: self.ctx(baseline=[]))
        self.rejects("CONTEXT_INVALID", lambda: self.ctx(allowed=[]))

    def test_baseline_caps_and_encoding(self):
        base = {f"docs/notes/{i}.md": b"" for i in range(64)}
        self.assertEqual(len(self.ctx(base).baseline), 64)
        base["docs/notes/extra.md"] = b""
        self.rejects("CONTEXT_LIMIT", lambda: self.ctx(base))
        self.assertEqual(len(self.ctx({P: b"a" * v.MAX_BASE_BYTES}).baseline[0].content), v.MAX_BASE_BYTES)
        self.rejects("CONTEXT_LIMIT", lambda: self.ctx({P: b"a" * (v.MAX_BASE_BYTES + 1)}))
        for raw in (b"\xff", b"\xef\xbb\xbfhi", b"a\0b"):
            self.rejects("TEXT_INVALID", lambda: self.ctx({P: raw}))
        self.rejects("CONTEXT_LIMIT", lambda: self.ctx(allowed={f"docs/notes/{i}.md": "create" for i in range(11)}))

    def test_immutable_copy_and_no_content_in_repr_or_summary(self):
        baseline = {"docs/notes/read.md": b"READ_SECRET"}
        allowed = {P: "create"}
        ctx = self.ctx(baseline, allowed)
        candidate = self.validate(self.payload(ctx, "OUTPUT_SECRET"), ctx)
        baseline.clear()
        allowed.clear()
        self.assertEqual(len(ctx.baseline), 1)
        self.assertEqual(len(ctx.allowed), 1)
        with self.assertRaises(FrozenInstanceError):
            candidate.generation = 2
        with self.assertRaises(FrozenInstanceError):
            candidate.changes[0].content = b"changed"
        with self.assertRaises(FrozenInstanceError):
            ctx.job_id = "changed"
        self.assertNotIn("READ_SECRET", repr(ctx))
        self.assertNotIn("OUTPUT_SECRET", repr(candidate) + repr(candidate.summary()))

    def test_invalid_second_change_returns_only_safe_error(self):
        payload = self.payload(content="PRIVATE_SENTINEL")
        payload["changes"].append(dict(path="docs/notes/PRIVATE_PATH.md", operation="create",
                                        before_sha256=None, content_utf8="PRIVATE_SENTINEL"))
        self.rejects("OUT_OF_SCOPE", lambda: self.validate(payload))

    def test_semantic_digest_is_stable_wire_digest_is_exact(self):
        ctx = self.ctx()
        payload = self.payload(ctx)
        a = self.validate(payload, ctx)
        raw = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True).encode()
        b = v.validate_changeset(raw, context=ctx)
        self.assertEqual(a.candidate_sha256, b.candidate_sha256)
        self.assertNotEqual(a.request_sha256, b.request_sha256)
        self.assertEqual(a, self.validate(payload, ctx))

    def test_manifest_order_readonly_bytes_and_grants_bind_identity(self):
        base = {"docs/notes/b.md": b"b", "docs/notes/a.md": b"a"}
        a = self.ctx(base)
        b = self.ctx(dict(reversed(list(base.items()))))
        self.assertEqual(a.base_manifest_sha256, b.base_manifest_sha256)
        original = self.validate(self.payload(a), a)
        for ctx in (self.ctx({**base, "docs/notes/a.md": b"changed"}),
                    self.ctx(base, {P: "create", "docs/notes/extra.md": "create"}),
                    self.ctx(base, job_id="another-job"), self.ctx(base, generation=2)):
            self.assertNotEqual(original.candidate_sha256, self.validate(self.payload(ctx), ctx).candidate_sha256)

    def test_changes_order_canonical_and_content_digest_changes(self):
        ctx = self.ctx(allowed={P: "create", "docs/notes/a.md": "create"})
        payload = self.payload(ctx)
        payload["changes"].append(dict(payload["changes"][0], path="docs/notes/a.md"))
        a = self.validate(payload, ctx)
        payload["changes"].reverse()
        b = self.validate(payload, ctx)
        self.assertEqual(a.candidate_sha256, b.candidate_sha256)
        self.assertNotEqual(a.request_sha256, b.request_sha256)
        payload["changes"][0]["content_utf8"] += "!"
        self.assertNotEqual(a.candidate_sha256, self.validate(payload, ctx).candidate_sha256)

    def test_source_commands_are_data_no_io_in_validation(self):
        ctx = self.ctx()
        payload = self.raw(self.payload(ctx, "<script>fetch('https://example.invalid')</script>\n"
                                               "import os; os.system('echo UNTRUSTED')\n\x1b[31m"))
        with patch("builtins.open", side_effect=AssertionError("file access")), \
             patch("os.open", side_effect=AssertionError("file access")), \
             patch("subprocess.run", side_effect=AssertionError("process")), \
             patch("socket.socket", side_effect=AssertionError("network")), \
             patch("sqlite3.connect", side_effect=AssertionError("database")):
            candidate = v.validate_changeset(payload, context=ctx)
        self.assertIn(b"UNTRUSTED", candidate.changes[0].content)
        self.assertNotIn("UNTRUSTED", json.dumps(candidate.summary()))

    def test_demo_observations_do_not_claim_application(self):
        good, bad = v.demo()
        self.assertEqual(good["status"], "valid_in_memory_only")
        self.assertEqual(bad, {"status": "rejected", "code": "OUT_OF_SCOPE", "applied": False})


if __name__ == "__main__":
    unittest.main()
