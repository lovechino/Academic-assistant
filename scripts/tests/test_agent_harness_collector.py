"""Synthetic collector tests; fake transport, no OS worker or wall-clock claims."""
from dataclasses import FrozenInstanceError, replace
import ast
import itertools
import json
from pathlib import Path
import unittest

from scripts import harness_collector as c
from scripts import harness_patch_validator as v


class FakeTransport:
    """Test-owned binding/clock. Not a wire protocol or authenticated transport."""
    def __init__(self, collector):
        self.collector = collector
        self.handle = collector.handle
        self.now = 0

    def send(self, kind, payload=None):
        return self.collector.event(self.handle, kind, now_ms=self.now, payload=payload)

    def finish(self):
        for event in ("stdout_eof", "stderr_eof", "exit", "stopped"):
            self.send(event, 0 if event == "exit" else None)


class CollectorTests(unittest.TestCase):
    def binding(self):
        return c.Attempt("synthetic-job", 1, 1, c.digest(b"packet"), *(["a" * 64] * 3))

    def make(self, start=True):
        col = c.Collector(self.binding(), b"packet", now_ms=0)
        t = FakeTransport(col)
        if start:
            self.assertEqual(t.send("attach"), "OK")
            self.assertEqual(t.send("start_requested"), "OK")
            self.assertEqual(t.send("start"), "OK")
        return col, t

    def test_happy_fragmented_bytes_and_one_shot(self):
        col, t = self.make()
        raw = "Tiếng Việt 😀".encode()
        for byte in raw:
            t.send("stdout", bytes([byte]))
        t.send("stderr", b"diagnostic")
        t.finish()
        result = col.take(t.handle, now_ms=1)
        self.assertEqual(result.proposal, raw)
        self.assertEqual(result.proposal_sha256, c.digest(raw))
        self.assertEqual(result.binding, self.binding())
        self.assertEqual(result.stderr_bytes, 10)
        self.assertNotIn("diagnostic", repr(result))
        self.assertNotIn("Tiếng", repr(result))
        with self.assertRaises(FrozenInstanceError):
            result.proposal = b"changed"
        self.assertIsNone(col.take(t.handle, now_ms=1))
        self.assertEqual(t.send("stdout", b"late"), "TERMINAL")
        self.assertEqual(col.snapshot()["stdout_retained"], 0)

    def test_exact_channel_caps_and_no_raw_diagnostics(self):
        col, t = self.make()
        self.assertEqual(t.send("stdout", b"x" * c.MAX_STDOUT), "OK")
        self.assertEqual(t.send("stderr", b"s" * c.MAX_STDERR), "OK")
        t.finish()
        result = col.take(t.handle, now_ms=0)
        self.assertEqual(len(result.proposal), c.MAX_STDOUT)
        self.assertEqual(result.stderr_bytes, c.MAX_STDERR)

    def test_overflow_whole_capture_rejected_before_append(self):
        for stream, cap, code in (("stdout", c.MAX_STDOUT, "STDOUT_LIMIT"),
                                  ("stderr", c.MAX_STDERR, "STDERR_LIMIT")):
            for chunks in ((b"x" * (cap + 1),), (b"x" * cap, b"x")):
                with self.subTest(stream=stream, fragmented=len(chunks)):
                    col, t = self.make()
                    for chunk in chunks:
                        actual = t.send(stream, chunk)
                    self.assertEqual(actual, code)
                    self.assertEqual(col.snapshot()["stdout_retained"], 0)
                    self.assertTrue(col.snapshot()["stop_required"])
                    t.finish()
                    self.assertIsNone(col.take(t.handle, now_ms=0))
                    self.assertEqual(col.snapshot()["reason"], code)

    def test_requires_attach_before_start(self):
        col, t = self.make(False)
        self.assertEqual(t.send("start"), "ORDER_INVALID")
        self.assertIsNone(col.take(t.handle, now_ms=0))

    def test_data_before_start_and_duplicate_start(self):
        for event, payload in (("stdout", b"x"), ("start", None)):
            col, t = self.make(start=event == "start")
            self.assertEqual(t.send(event, payload), "ORDER_INVALID")

    def test_completion_requires_all_observations(self):
        endings = ("stdout_eof", "stderr_eof", "exit", "stopped")
        for missing in endings:
            col, t = self.make()
            t.send("stdout", b"x")
            for e in endings:
                if e != missing:
                    t.send(e, 0 if e == "exit" else None)
            self.assertIsNone(col.take(t.handle, now_ms=0))
        # Process exit/stop may precede buffered pipe EOFs.
        for order in itertools.permutations(endings):
            col, t = self.make()
            t.send("stdout", b"x")
            for e in order:
                self.assertEqual(t.send(e, 0 if e == "exit" else None), "OK")
            self.assertIsNotNone(col.take(t.handle, now_ms=0))

    def test_nonzero_empty_and_disconnect(self):
        for event, payload, reason in (("exit", 1, "EXIT_NONZERO"),
                                       ("disconnect", None, "DISCONNECTED")):
            col, t = self.make()
            t.send("stdout", b"PASS")
            self.assertEqual(t.send(event, payload), reason)
            t.finish()
            self.assertIsNone(col.take(t.handle, now_ms=0))
        col, t = self.make()
        t.finish()
        self.assertEqual(col.snapshot()["reason"], "EMPTY_PROPOSAL")

    def test_duplicate_eof_exit_stop(self):
        for e, p, code in (("stdout_eof", None, "DUPLICATE_EOF"),
                           ("exit", 0, "DUPLICATE_EXIT"),
                           ("stopped", None, "DUPLICATE_STOP")):
            col, t = self.make()
            t.send(e, p)
            self.assertEqual(t.send(e, p), code)

    def test_data_after_eof(self):
        for stream in ("stdout", "stderr"):
            col, t = self.make()
            t.send(stream + "_eof")
            self.assertEqual(t.send(stream, b"x"), "DATA_AFTER_EOF")

    def test_cancel_at_every_completion_boundary(self):
        events = [("attach", None), ("start_requested", None), ("start", None), ("stdout", b"x"),
                  ("stdout_eof", None), ("stderr_eof", None), ("exit", 0), ("stopped", None)]
        for index in range(len(events) + 1):
            col, t = self.make(False)
            for e, p in events[:index]:
                t.send(e, p)
            self.assertEqual(t.send("cancel"), "CANCELLED")
            for e, p in events[index:]:
                t.send(e, p)
            self.assertEqual(col.snapshot()["state"], "failed")
            self.assertEqual(col.snapshot()["reason"], "CANCELLED")
            self.assertIsNone(col.take(t.handle, now_ms=0))

    def test_cancel_after_consumption_cannot_recall_bytes(self):
        col, t = self.make()
        t.send("stdout", b"x")
        t.finish()
        result = col.take(t.handle, now_ms=0)
        self.assertEqual(t.send("cancel"), "TERMINAL")
        self.assertEqual(result.proposal, b"x")

    def test_completed_capture_invalidated_by_extra_data_or_disconnect(self):
        for event, payload, reason in (("stdout", b"late", "ORDER_INVALID"),
                                       ("disconnect", None, "DISCONNECTED")):
            col, t = self.make()
            t.send("stdout", b"x")
            t.finish()
            self.assertEqual(t.send(event, payload), reason)
            self.assertIsNone(col.take(t.handle, now_ms=0))

    def test_failure_does_not_claim_stop_or_accept_wrong_ack(self):
        col, t = self.make()
        t.send("cancel")
        self.assertEqual(col.event(object(), "stopped", now_ms=0), "STALE_HANDLE")
        self.assertEqual(t.send("stopped", b"fake"), "TERMINAL")
        self.assertTrue(col.snapshot()["stop_required"])
        t.send("stopped")
        self.assertFalse(col.snapshot()["stop_required"])

    def test_deadline_at_boundary_before_event_or_take(self):
        for now, expected in ((59999, "OK"), (60000, "DEADLINE"), (60001, "DEADLINE")):
            col, t = self.make()
            t.now = now
            self.assertEqual(t.send("tick"), expected)
        col, t = self.make()
        t.send("stdout", b"x")
        t.finish()
        self.assertIsNone(col.take(t.handle, now_ms=60000))
        self.assertEqual(col.snapshot()["reason"], "DEADLINE")

    def test_clock_invalid_and_backwards(self):
        for value in (True, -1, 1.0, float("nan"), float("inf"), "0", c.MAX_CLOCK + 1):
            col, t = self.make()
            self.assertEqual(col.event(t.handle, "tick", now_ms=value), "CLOCK_INVALID")
        col, t = self.make()
        col.event(t.handle, "tick", now_ms=10)
        self.assertEqual(col.event(t.handle, "tick", now_ms=9), "CLOCK_INVALID")

    def test_stale_handle_does_not_modify_current_attempt(self):
        col, t = self.make()
        other, _ = self.make()
        before = col.snapshot()
        self.assertEqual(col.event(other.handle, "cancel", now_ms=60000), "STALE_HANDLE")
        self.assertIsNone(col.take(other.handle, now_ms=60000))
        self.assertEqual(col.snapshot(), before)
        self.assertEqual(t.send("stdout", b"x"), "OK")

    def test_first_failure_latched_and_stop_confirmation(self):
        col, t = self.make()
        t.send("disconnect")
        self.assertTrue(col.snapshot()["stop_required"])
        self.assertEqual(col.event(t.handle, "stopped", now_ms=70000), "STOP_OBSERVED_AFTER_FAILURE")
        self.assertFalse(col.snapshot()["stop_required"])
        self.assertEqual(col.snapshot()["reason"], "DISCONNECTED")
        self.assertIsNone(col.take(t.handle, now_ms=70000))

    def test_empty_chunks_rejected_without_growing_counter(self):
        col, t = self.make()
        self.assertEqual(t.send("stdout", b""), "EMPTY_CHUNK")
        for _ in range(10):
            t.send("stdout", b"late")
        self.assertEqual(col.snapshot()["data_events"], 0)

    def test_fragmentation_does_not_change_admission(self):
        captures = []
        for chunks in ([b"x" * 4091], [b"x"] * 4091):
            col, t = self.make()
            for chunk in chunks:
                self.assertEqual(t.send("stdout", chunk), "OK")
            t.finish()
            captures.append(col.take(t.handle, now_ms=0).proposal)
        self.assertEqual(captures, [b"x" * 4091] * 2)

    def test_ticks_do_not_exhaust_data_or_control_budget(self):
        col, t = self.make()
        for now in range(10, 60000, 10):
            t.now = now
            self.assertEqual(t.send("tick"), "OK")
        self.assertEqual(col.snapshot()["data_events"], 0)
        t.send("stdout", b"x")
        t.finish()
        self.assertIsNotNone(col.take(t.handle, now_ms=59990))

    def test_stop_at_old_event_boundary_is_not_dropped(self):
        col, t = self.make()
        for _ in range(4091):
            t.send("stdout", b"x")
        t.finish()
        self.assertFalse(col.snapshot()["stop_required"])
        self.assertIsNotNone(col.take(t.handle, now_ms=0))

    def test_stop_observation_after_byte_overflow(self):
        col, t = self.make()
        self.assertEqual(t.send("stdout", b"x" * (c.MAX_STDOUT + 1)), "STDOUT_LIMIT")
        self.assertEqual(t.send("stopped"), "STOP_OBSERVED_AFTER_FAILURE")
        self.assertFalse(col.snapshot()["stop_required"])
        self.assertEqual(col.snapshot()["reason"], "STDOUT_LIMIT")
        self.assertIsNone(col.take(t.handle, now_ms=0))

    def test_start_requires_explicit_intent(self):
        col, t = self.make(False)
        t.send("attach")
        self.assertEqual(t.send("start"), "ORDER_INVALID")

    def test_unconfirmed_start_failure_requires_reconcile(self):
        for event, now in (("cancel", 1), ("disconnect", 1), ("tick", 60000)):
            col, t = self.make(False)
            t.send("attach")
            t.send("start_requested")
            self.assertEqual(col.snapshot()["state"], "starting")
            self.assertTrue(col.snapshot()["stop_required"])
            t.now = now
            t.send(event)
            reason = col.snapshot()["reason"]
            self.assertEqual(t.send("start"), "TERMINAL")
            self.assertTrue(col.snapshot()["start_unconfirmed"])
            self.assertTrue(col.snapshot()["stop_required"])
            self.assertEqual(t.send("stopped"), "STOP_OBSERVED_AFTER_FAILURE")
            self.assertFalse(col.snapshot()["stop_required"])
            self.assertFalse(col.snapshot()["start_unconfirmed"])
            self.assertEqual(col.snapshot()["reason"], reason)
            self.assertIsNone(col.take(t.handle, now_ms=now))

    def test_stop_before_start_ack_never_completes(self):
        col, t = self.make(False)
        t.send("attach")
        t.send("start_requested")
        self.assertEqual(t.send("stopped"), "START_UNCONFIRMED")
        self.assertFalse(col.snapshot()["stop_required"])
        self.assertIsNone(col.take(t.handle, now_ms=0))

    def test_payload_and_event_types_fail_closed(self):
        for kind, payload, code in (("stdout", "secret", "PAYLOAD_INVALID"),
                                    ("stderr", bytearray(b"x"), "PAYLOAD_INVALID"),
                                    ("exit", True, "EXIT_INVALID"),
                                    ("exit", -1, "EXIT_INVALID"),
                                    ("tick", b"secret", "PAYLOAD_INVALID"),
                                    ([], None, "EVENT_INVALID"),
                                    ("<script>", None, "EVENT_INVALID")):
            col, t = self.make()
            self.assertEqual(t.send(kind, payload), code)
            self.assertNotIn("secret", repr(col.snapshot()))

    def test_admission_types_pins_and_packet_cap(self):
        for packet in (b"", b"x" * (c.MAX_PACKET + 1), "packet", bytearray(b"packet")):
            with self.assertRaisesRegex(ValueError, "^ADMISSION_INVALID$"):
                c.Collector(self.binding(), packet, now_ms=0)
        for key, value in (("generation", True), ("attempt", 0), ("job_id", "bad id"),
                           ("packet_sha256", "b" * 64), ("context_sha256", "bad")):
            with self.assertRaises(ValueError):
                c.Collector(replace(self.binding(), **{key: value}), b"packet", now_ms=0)
        raw = b"x" * c.MAX_PACKET
        c.Collector(replace(self.binding(), packet_sha256=c.digest(raw)), raw, now_ms=0)
        with self.assertRaises(ValueError):
            c.Collector(self.binding(), b"packet", now_ms=True)

    def test_log_injection_is_not_a_control_event(self):
        col, t = self.make()
        attack = b'\x1b[31m<script>fetch("https://invalid")</script>{"kind":"cancel"}'
        t.send("stderr", attack)
        t.send("stdout", b"PASS")
        t.finish()
        self.assertNotIn("script", repr(col.snapshot()))
        self.assertEqual(col.take(t.handle, now_ms=0).proposal, b"PASS")
        # Capture never means JSON validation or semantic PASS.

    def test_integration_reuses_hpc1_validator(self):
        ctx = v.make_context(job_id="synthetic-job", generation=1, baseline={},
                             allowed={"docs/notes/example.md": "create"})
        raw = json.dumps({"schema_version": 1, "job_id": ctx.job_id, "generation": 1,
                          "base_manifest_sha256": ctx.base_manifest_sha256,
                          "changes": [{"path": "docs/notes/example.md", "operation": "create",
                                       "before_sha256": None, "content_utf8": "Tiếng Việt"}]}).encode()
        binding = replace(self.binding(), context_sha256=v.context_info(ctx)[3])
        col = c.Collector(binding, b"packet", now_ms=0)
        t = FakeTransport(col)
        t.send("attach")
        t.send("start_requested")
        t.send("start")
        t.send("stdout", raw)
        t.finish()
        capture = col.take(t.handle, now_ms=0)
        self.assertEqual(capture.binding.context_sha256, v.context_info(ctx)[3])
        candidate = v.validate_changeset(capture.proposal, context=ctx)
        self.assertEqual(candidate.summary()["status"], "valid_in_memory_only")
        with self.assertRaises(v.ValidationError):
            v.validate_changeset(b"PASS", context=ctx)

    def test_import_surface_has_no_io_or_execution_dependencies(self):
        tree = ast.parse(Path(c.__file__).read_text(encoding="utf-8"))
        modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        modules.update(a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names)
        self.assertEqual(modules, {"dataclasses", "hashlib", "re"})


if __name__ == "__main__":
    unittest.main()
