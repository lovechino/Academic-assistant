"""Observer regressions: fake ports plus own unprivileged Linux child only."""
from dataclasses import replace
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from scripts import harness_observer as o


CID = "a" * 64
START = "2026-09-08T10:00:00.123456789Z"


def binding():
    return o.Binding("synthetic-observer", CID, 123, START, 1, 1, *("b" * 64,) * 4)


def info():
    return {"Id": CID, "State": {"Running": True, "Pid": 123, "StartedAt": START}}


def status(pid=123):
    return (f"Name:\tignored-name\nTgid:\t{pid}\nUid:\t65532 65532 65532 65532\n"
            "Gid:\t65532 65532 65532 65532\nCapEff:\t0000000000000000\n"
            "NoNewPrivs:\t1\nSeccomp:\t2\n").encode()


class Clock:
    now = 0

    def __call__(self):
        return self.now


class Target:
    pid = 123
    started = 42
    alive = True
    membership = True
    ticks = 42
    namespace_reads = 0

    def assert_alive(self):
        o.require(self.alive, "PROCESS_EXITED")

    def read_start(self):
        return self.ticks

    def belongs_to(self, cid):
        assert cid == CID
        return self.membership

    def read_controls(self):
        return o.controls(status(), self.pid)

    def read_network_namespace(self):
        self.namespace_reads += 1
        return 200


class ObserverTests(unittest.TestCase):
    def session(self, inspector=info):
        self.target, self.clock = Target(), Clock()
        return o.Session(binding(), self.target, inspector, 100, clock=self.clock)

    def test_valid_projection_is_partial_not_security_acceptance(self):
        session = self.session()
        result = session.observe(session.handle)
        self.assertEqual(result["status"], "partial_observation_only")
        self.assertFalse(result["atomic_snapshot"])
        self.assertTrue(result["network_namespace_differs"])
        self.assertEqual(result["binding"]["container_id"], CID)
        self.assertNotIn("ignored-name", str(result))

    def test_wrong_handle_no_io_or_poisoning(self):
        session = self.session()
        with patch.object(self.target, "read_controls") as read, self.assertRaisesRegex(o.ObserverError, "STALE_SESSION"):
            session.observe(object())
        read.assert_not_called()
        self.assertEqual(session.state, "ready")
        session.observe(session.handle)

    def test_replay_rejected(self):
        session = self.session()
        session.observe(session.handle)
        with self.assertRaisesRegex(o.ObserverError, "SESSION_UNAVAILABLE"):
            session.observe(session.handle)

    def test_cancel_before_measurement_no_reads(self):
        session = self.session()
        session.cancel(session.handle)
        with patch.object(self.target, "read_controls") as read, self.assertRaises(o.ObserverError):
            session.observe(session.handle)
        read.assert_not_called()

    def test_cancel_during_read_discards_and_stops_remaining_reads(self):
        session = self.session()
        def cancelled():
            session.cancel(session.handle)
            return o.controls(status(), 123)
        with patch.object(self.target, "read_controls", side_effect=cancelled):
            with self.assertRaisesRegex(o.ObserverError, "SESSION_REVOKED"):
                session.observe(session.handle)
        self.assertEqual(self.target.namespace_reads, 0)

    def test_deadline_inclusive_boundary(self):
        session = self.session()
        self.clock.now = 2000
        with self.assertRaisesRegex(o.ObserverError, "OBSERVATION_DEADLINE"):
            session.observe(session.handle)

    def test_deadline_during_last_inspect(self):
        calls = []
        def inspect():
            calls.append(1)
            if len(calls) == 2:
                self.clock.now = 2000
            return info()
        session = self.session(inspect)
        with self.assertRaisesRegex(o.ObserverError, "OBSERVATION_DEADLINE"):
            session.observe(session.handle)
        self.assertEqual(len(calls), 2)

    def test_clock_reversal(self):
        session = self.session()
        self.clock.now = -1
        with self.assertRaisesRegex(o.ObserverError, "CLOCK_INVALID"):
            session.observe(session.handle)

    def test_changed_container_pid_start_or_running(self):
        for key, value in (("Pid", 456), ("StartedAt", "2026-09-08T10:01:00Z"), ("Running", False)):
            changed = info()
            changed["State"][key] = value
            with self.subTest(key=key):
                session = self.session(lambda: changed)
                with self.assertRaisesRegex(o.ObserverError, "CONTAINER_CHANGED"):
                    session.observe(session.handle)

    def test_changed_container_id(self):
        changed = info()
        changed["Id"] = "c" * 64
        session = self.session(lambda: changed)
        with self.assertRaisesRegex(o.ObserverError, "CONTAINER_CHANGED"):
            session.observe(session.handle)

    def test_change_on_second_inspect_discards_measurement(self):
        records = [info(), {"Id": CID, "State": {"Running": False}}]
        session = self.session(lambda: records.pop(0))
        with self.assertRaisesRegex(o.ObserverError, "CONTAINER_CHANGED"):
            session.observe(session.handle)
        self.assertEqual(self.target.namespace_reads, 1)
        self.assertEqual(session.state, "failed")

    def test_exited_target(self):
        session = self.session()
        self.target.alive = False
        with self.assertRaisesRegex(o.ObserverError, "PROCESS_EXITED"):
            session.observe(session.handle)

    def test_recycled_pid_start_ticks_changed(self):
        session = self.session()
        self.target.ticks += 1
        with self.assertRaisesRegex(o.ObserverError, "PROCESS_CHANGED"):
            session.observe(session.handle)

    def test_cgroup_mismatch_no_namespace_read(self):
        session = self.session()
        self.target.membership = False
        with self.assertRaisesRegex(o.ObserverError, "CGROUP_MISMATCH"):
            session.observe(session.handle)
        self.assertEqual(self.target.namespace_reads, 0)

    def test_permission_denial_has_no_partial_success_payload(self):
        session = self.session()
        with patch.object(self.target, "read_network_namespace", side_effect=PermissionError("untrusted details")):
            with self.assertRaisesRegex(o.ObserverError, "^HOST_OBSERVER_PERMISSION_DENIED$"):
                session.observe(session.handle)
        self.assertEqual(session.state, "failed")

    def test_missing_process_is_not_access_denial_pass(self):
        session = self.session()
        with patch.object(self.target, "read_controls", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(o.ObserverError, "HOST_OBSERVER_UNAVAILABLE"):
                session.observe(session.handle)

    def test_binding_closed_schema_and_types(self):
        for key, value in (("pid", True), ("generation", True), ("attempt", 0), ("container_id", "name"),
                           ("started_at", "../../other"), ("profile_sha256", "z" * 64)):
            with self.subTest(key=key), self.assertRaisesRegex(o.ObserverError, "BINDING_INVALID"):
                o.check_binding(replace(binding(), **{key: value}))
        with self.assertRaises(o.ObserverError):
            o.check_binding({"approved": True})

    def test_status_projection_whitelist(self):
        fields = o.controls(status() + b"Secret:\tSYNTHETIC\n", 123)
        self.assertEqual(set(fields), {"uid", "gid", "effective_capabilities", "no_new_privileges", "seccomp_mode"})
        self.assertNotIn("SYNTHETIC", str(fields))

    def test_status_missing_duplicate_and_malformed(self):
        for raw in (status().replace(b"Seccomp:\t2\n", b""), status() + b"Uid:\t0 0 0 0\n",
                    status().replace(b"65532", b"-1"), status().replace(b"Tgid:\t123", b"Tgid:\t456")):
            with self.subTest(raw=raw), self.assertRaises(o.ObserverError):
                o.controls(raw, 123)

    def test_stat_name_parentheses_and_newline_not_authority(self):
        raw = b"123 (fake )\n(name) S " + b"0 " * 18 + b"42 0 0\n"
        self.assertEqual(o.start_ticks(raw, 123), 42)
        with self.assertRaises(o.ObserverError):
            o.start_ticks(raw, 456)

    def test_proc_bounds(self):
        for parser in (o.controls, o.start_ticks):
            with self.assertRaises(o.ObserverError):
                parser(b"x" * (o.MAX_PROC + 1), 123)

    def test_cgroup_exact_components_not_substring(self):
        for path in ("/docker/" + CID, "/system.slice/docker-" + CID + ".scope"):
            self.assertTrue(o.cgroup_matches(("0::" + path + "\n").encode(), CID))
        for path in ("/docker/x" + CID, "/docker/" + CID + "x", "/other"):
            self.assertFalse(o.cgroup_matches(("0::" + path + "\n").encode(), CID))

    def test_namespace_format_only(self):
        self.assertEqual(o.namespace_number("net:[4026531840]"), 4026531840)
        for value in ("/proc/1/root", "net:[-1]", "pid:[123]", "net:[123]\n"):
            with self.assertRaises(o.ObserverError):
                o.namespace_number(value)

    @unittest.skipUnless(sys.platform == "linux", "Linux pidfd/proc test; Windows NOT RUN")
    def test_own_child_handle_exit_and_descriptor_close(self):
        child = subprocess.Popen([sys.executable, "-I", "-B", "-c", "import time; time.sleep(10)"],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        target = None
        try:
            target = o.ProcTarget(child.pid)
            self.assertEqual(target.read_start(), target.started)
            self.assertEqual(target.read_controls()["uid"][0], os.getuid())
            self.assertEqual(target.read_network_namespace(), o.namespace_number(os.readlink("/proc/self/ns/net")))
            with self.assertRaisesRegex(o.ObserverError, "FIELD_NOT_ALLOWED"):
                target._read_fixed("environ")
            child.terminate()
            child.wait(timeout=3)
            with self.assertRaisesRegex(o.ObserverError, "PROCESS_EXITED"):
                target.assert_alive()
            target.close()
            with self.assertRaisesRegex(o.ObserverError, "PROCESS_CLOSED"):
                target.assert_alive()
        finally:
            if target is not None:
                target.close()
            if child.poll() is None:
                child.kill()
            child.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
