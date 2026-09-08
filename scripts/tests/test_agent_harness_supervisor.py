"""Pure/fake adapter regressions; discovery never contacts Docker."""
import copy
import io
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from scripts import harness_supervisor as s


class FakeStream:
    def __init__(self, data, fragment=3):
        self.data = io.BytesIO(data)
        self.fragment = fragment

    def recv(self, size):
        return self.data.read(min(size, self.fragment))


def effective():
    cfg = s.configuration()
    host = cfg.pop("HostConfig")
    host.update(MaskedPaths=["/proc/kcore"], ReadonlyPaths=["/proc/sys"])
    return {"Id": "a" * 64, "Image": s.IMAGE_ID, "Config": cfg,
            "HostConfig": host, "Mounts": []}


def fake_hang(connection, job, scenario):
    connection.send({"phase": "create_intent"})
    connection.recv()
    connection.send({"phase": "created", "id": "a" * 64})
    connection.recv()
    connection.send({"phase": "start_intent"})
    connection.recv()
    connection.send({"phase": "running"})
    time.sleep(10)


class SupervisorTests(unittest.TestCase):
    def test_fixture_reuses_original_validator(self):
        ctx, packet = s.fixture("synthetic-test", "happy")
        candidate = s.validator.validate_changeset(s.encoded(json.loads(packet)["proposal"]), context=ctx)
        self.assertEqual(candidate.changes[0].content, b"synthetic\n")

    def test_failure_receipts_have_admission_pins_without_worker_result(self):
        pins = s.trial_pins("synthetic-test", "overflow")
        self.assertEqual(pins["image_id"], s.IMAGE_ID)
        self.assertEqual(pins["attempt"], 1)
        for key in ("packet_sha256", "context_sha256", "release_sha256", "profile_sha256"):
            self.assertRegex(pins[key], r"^[0-9a-f]{64}$")

    def test_no_arbitrary_scenario(self):
        with self.assertRaises(s.TrialError):
            s.fixture("synthetic-test", "shell")

    def test_fixed_grant_rejects_worker_target(self):
        ctx, packet = s.fixture("synthetic-test", "happy")
        proposal = json.loads(packet)["proposal"]
        proposal["changes"][0]["path"] = "docs/notes/another.md"
        with self.assertRaises(s.validator.ValidationError):
            s.validator.validate_changeset(s.encoded(proposal), context=ctx)

    def test_fake_pass_is_not_validation(self):
        ctx, _ = s.fixture("synthetic-test", "happy")
        with self.assertRaises(s.validator.ValidationError):
            s.validator.validate_changeset(b"PASS", context=ctx)

    def test_id_only_not_name_label_or_path(self):
        for value in ("owned-name", "a" * 63, "A" * 64, "a" * 64 + "/start", None):
            with self.subTest(value=value), self.assertRaises(s.TrialError):
                s.exact_id(value)

    def test_effective_positive(self):
        s.check_effective(effective(), "a" * 64)

    def test_effective_config_changes_fail(self):
        for key, value in (("User", "0"), ("Tty", True), ("Env", ["TOKEN=synthetic"]),
                           ("Entrypoint", ["sh"]), ("Cmd", ["injected"]),
                           ("Volumes", {"/data": {}})):
            record = effective()
            record["Config"][key] = value
            with self.subTest(key=key), self.assertRaises(s.TrialError):
                s.check_effective(record, "a" * 64)

    def test_effective_host_changes_fail(self):
        for key, value in (("NetworkMode", "host"), ("Privileged", True),
                           ("Memory", 0), ("PidsLimit", -1), ("CapAdd", ["SYS_ADMIN"]),
                           ("Binds", ["/tmp:/host"]), ("SecurityOpt", ["seccomp=unconfined"]),
                           ("DeviceRequests", [{"Driver": "nvidia"}])):
            record = effective()
            record["HostConfig"][key] = value
            with self.subTest(key=key), self.assertRaises(s.TrialError):
                s.check_effective(record, "a" * 64)

    def test_mount_and_system_path_checks(self):
        for variant in ("mount", "masked"):
            record = effective()
            if variant == "mount":
                record["Mounts"] = [{"Type": "bind"}]
            else:
                record["HostConfig"]["MaskedPaths"] = []
            with self.assertRaises(s.TrialError):
                s.check_effective(record, "a" * 64)

    def test_frame_fragmentation_and_eof(self):
        self.assertEqual(s.read_exact(FakeStream(b"12345678", 1), 8), b"12345678")
        self.assertIsNone(s.read_exact(FakeStream(b""), 8, eof=True))

    def test_truncated_frame_never_eof_success(self):
        with self.assertRaises(s.TrialError):
            s.read_exact(FakeStream(b"123"), 8, eof=True)

    def test_frame_caps_checked_before_payload_read(self):
        with self.assertRaisesRegex(s.TrialError, "STDOUT_LIMIT"):
            s.frame_header(b"\x01\0\0\0" + struct.pack(">I", 2**32 - 1), {1: 1024, 2: 256})

    def test_frame_header_channels_padding_and_zero(self):
        for raw in (b"", b"\x03\0\0\0\0\0\0\x01", b"\x01\x01\0\0\0\0\0\x01",
                    b"\x01\0\0\0\0\0\0\0"):
            with self.subTest(raw=raw), self.assertRaises(s.TrialError):
                s.frame_header(raw, {1: 1024, 2: 256})

    def test_exact_limit_frame(self):
        self.assertEqual(s.frame_header(b"\x02\0\0\0\0\0\x01\0", {1: 1024, 2: 256}), (2, 256))

    def test_cleanup_only_exact_id_and_verify_absence(self):
        with patch.object(s, "api", side_effect=[(204, None), (404, {})]) as api:
            self.assertTrue(s.cleanup("a" * 64))
            self.assertEqual(api.call_count, 2)
            self.assertIn("force=1&v=0", api.call_args_list[0].args[1])
            self.assertEqual(api.call_args_list[1].kwargs["expected"], (404,))

    def test_cleanup_ambiguity_not_success_or_retry(self):
        with patch.object(s, "api", side_effect=TimeoutError) as api:
            with self.assertRaises(TimeoutError):
                s.cleanup("a" * 64)
            self.assertEqual(api.call_count, 1)

    def test_cleanup_rejects_name_before_io(self):
        with patch.object(s, "api") as api, self.assertRaises(s.TrialError):
            s.cleanup("owned-name")
        api.assert_not_called()

    def test_observer_permission_denial_is_not_worker_security_pass(self):
        info = {"Id": "a" * 64, "State": {"Running": True, "Pid": 123,
                                          "StartedAt": "2026-09-08T00:00:00Z"}}
        with patch.object(s, "api", return_value=(200, info)), \
                patch.object(s.observer, "ProcTarget", side_effect=PermissionError):
            result = s.observe_process("a" * 64, job="synthetic-test", pins=s.trial_pins("synthetic-test", "observe"))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "HOST_OBSERVER_PERMISSION_DENIED")

    def test_observer_bad_identity_rejected_before_proc_open(self):
        info = {"Id": "c" * 64, "State": {"Running": True, "Pid": 123,
                                          "StartedAt": "2026-09-08T00:00:00Z"}}
        with patch.object(s, "api", return_value=(200, info)), \
                patch.object(s.observer, "ProcTarget") as target, self.assertRaisesRegex(s.TrialError, "OBSERVER_IDENTITY"):
            s.observe_process("a" * 64, job="synthetic-test", pins=s.trial_pins("synthetic-test", "observe"))
        target.assert_not_called()

    def test_observer_measured_control_mismatch_blocks(self):
        info = {"Id": "a" * 64, "State": {"Running": True, "Pid": 123,
                                          "StartedAt": "2026-09-08T00:00:00Z"}}
        with patch.object(s, "api", return_value=(200, info)), \
                patch.object(s.observer, "ProcTarget"), patch.object(s.observer, "Session") as session, \
                patch.object(s.os, "readlink", return_value="net:[123]"):
            session.return_value.observe.return_value = {"process_controls": {"uid": [0]*4},
                                                        "network_namespace_differs": True}
            result = s.observe_process("a" * 64, job="synthetic-test", pins=s.trial_pins("synthetic-test", "observe"))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "HOST_OBSERVER_CONTROL_MISMATCH")

    def test_image_pins_and_inherited_defaults(self):
        image = {"Id": s.IMAGE_ID, "Os": "linux", "Architecture": "amd64",
                 "RootFS": {"Layers": s.DIFF_IDS},
                 "Config": {"Env": s.IMAGE_ENV, "Cmd": ["python3"]}}
        s.check_image(image)
        for key in ("Volumes", "OnBuild", "Entrypoint", "Healthcheck", "ExposedPorts"):
            bad = copy.deepcopy(image)
            bad["Config"][key] = ["injected"]
            with self.subTest(key=key), self.assertRaises(s.TrialError):
                s.check_image(bad)

    def test_isolated_bootstrap_no_repository_sys_path(self):
        completed = subprocess.run([sys.executable, "-I", "-B", str(Path(s.__file__).resolve()), "--help"],
                                   capture_output=True, timeout=5)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    @unittest.skipUnless(sys.platform == "linux", "Linux signal deadline; Windows NOT RUN")
    def test_total_deadline_interrupts_blocking_call(self):
        began = time.monotonic()
        with self.assertRaisesRegex(s.TrialError, "API_WALL_DEADLINE"):
            with s.wall_limit(.05):
                time.sleep(2)
        self.assertLess(time.monotonic() - began, .5)

    @unittest.skipUnless(sys.platform == "linux", "Linux inherited limits; Windows NOT RUN")
    def test_inherited_hard_limit_does_not_raise(self):
        code = "from scripts.harness_supervisor import limits; import os; limits(10); p=os.fork(); limits(10); os._exit(0) if p==0 else None; print(os.waitpid(p,0)[1])"
        completed = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, timeout=5)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), b"0")

    @unittest.skipUnless(sys.platform == "linux", "Linux process/fsync test; Windows NOT RUN")
    def test_real_parent_deadline_kills_fake_child_and_cleans_exact_id(self):
        with tempfile.TemporaryDirectory() as directory:
            fd = os.open(Path(directory) / "lock", os.O_CREAT | os.O_RDWR, 0o600)
            with patch.object(s, "limits"), patch.object(s, "private_store", return_value=(Path(directory), fd)), \
                    patch.object(s, "child", fake_hang), patch.object(s, "cleanup", return_value=True) as cleanup:
                result = s.supervise("hang")
            self.assertEqual(result["reason"], "SYNTHETIC_COMMAND_DEADLINE")
            self.assertEqual(result["cleanup"], "confirmed_absent")
            self.assertLess(result["elapsed_seconds"], 5)
            cleanup.assert_called_once_with("a" * 64)

    @unittest.skipUnless(sys.platform == "linux", "Linux process/fsync test; Windows NOT RUN")
    def test_cancel_fences_late_result_and_cleanup_failure_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            fd = os.open(Path(directory) / "lock", os.O_CREAT | os.O_RDWR, 0o600)
            with patch.object(s, "limits"), patch.object(s, "private_store", return_value=(Path(directory), fd)), \
                    patch.object(s, "child", fake_hang), patch.object(s, "cleanup", side_effect=TimeoutError):
                result = s.supervise("cancel")
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "CLEANUP_UNCONFIRMED")
            self.assertNotIn("candidate_sha256", result)


if __name__ == "__main__":
    unittest.main()
