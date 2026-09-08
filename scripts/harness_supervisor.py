"""Linux-only, operator-run synthetic Docker trial. NOT a coding-agent launcher.

No arbitrary packets/commands/paths accepted. Parent owns durable exact-ID receipt,
watchdog and cleanup. Child owns bounded Engine transport, collector and validator.
Same-user host processes/admins remain trusted; never expose this CLI to a worker.
"""
import argparse
from contextlib import contextmanager
import hashlib
import http.client
import json
import multiprocessing
import os
from pathlib import Path
import re
import signal
import socket
import struct
import sys
import time
import uuid

if __package__:
    from . import harness_collector as capture
    from . import harness_patch_validator as validator
    from . import harness_observer as observer
else:
    # Supports python -I without exposing a repository directory as sys.path.
    import importlib.util

    def load_trusted(name, filename):
        spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent / filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    capture = load_trusted("_hpc2_collector", "harness_collector.py")
    validator = load_trusted("_hpc2_validator", "harness_patch_validator.py")
    observer = load_trusted("_hpc2_observer", "harness_observer.py")


IMAGE = "docker.io/library/python@sha256:b1add8a6f2aca6bcfcf0b9c9b522352f7ce0d62a3d556a2f2f32511aa0cca250"
IMAGE_ID = "sha256:9356cb064a7cbecce9a3ccba46e7fd5459d3a3e939db884ef7fbf3f757cc5ec8"
SOCKET = "/var/run/docker.sock"
API = "/v1.46"
MAX_API = 1024 * 1024
SCENARIOS = ("happy", "fake-pass", "overflow", "hang", "cancel", "observe")
DIFF_IDS = [
    "sha256:1d69a5fd31932841d7825ef4780c06f008eea65aaa9f3110fe09d5832ed5c7d8",
    "sha256:52b622427b589c285e2050412206455922433042980dd60692cd1916a3b36216",
    "sha256:abe239c61612f687cb1ff7d384961b0f141a8234a2147ea59d99adebe1362103",
    "sha256:c5a2bd506e3a6934bb02bee775fe8e842e884ff3780597e11b9a8b83cdecc9af",
]
IMAGE_ENV = [
    "PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "LANG=C.UTF-8", "GPG_KEY=A035C8C19219BA821ECEA86B64E628F8D684696D",
    "PYTHON_VERSION=3.11.16",
    "PYTHON_SHA256=91bcdebfdde239a003ae93738a7fce0f9230fee5c4bc2b86f6e6e8c6f98aabe8",
]
# Only this reviewed fixture executes in the worker. No host command from data.
WORKER = """import json,os,sys,time
p=json.loads(sys.stdin.buffer.readline(4194305))
mode=p['scenario']
if mode=='observe': time.sleep(2)
if mode in ('hang','cancel'): time.sleep(120)
elif mode=='overflow':
 for _ in range(129): os.write(1,b'x'*8192)
elif mode=='fake-pass': print('PASS')
else: print(json.dumps(p['proposal'],separators=(',',':')))
"""


class TrialError(Exception):
    """Fixed error codes only; do not export daemon/source/exception text."""


def need(condition, code):
    if not condition:
        raise TrialError(code)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def exact_id(value):
    need(type(value) is str and re.fullmatch("[0-9a-f]{64}", value), "ID_INVALID")
    return value


class UnixHTTP(http.client.HTTPConnection):
    def __init__(self, timeout=3):
        super().__init__("localhost", timeout=timeout)

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(SOCKET)


@contextmanager
def wall_limit(seconds):
    """Total Linux API deadline, not just a per-recv inactivity timeout."""
    need(sys.platform == "linux", "LINUX_ONLY")
    def expired(_signum, _frame):
        raise TrialError("API_WALL_DEADLINE")
    need(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), "TIMER_OWNERSHIP")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def api(method, path, data=None, expected=(200,), timeout=3):
    conn = UnixHTTP(timeout)
    try:
        with wall_limit(timeout):
            body = None if data is None else encoded(data)
            conn.request(method, API + path, body=body,
                         headers={"Content-Type": "application/json"})
            response = conn.getresponse()
            raw = response.read(MAX_API + 1)
            need(len(raw) <= MAX_API, "API_BYTES")
            need(response.status in expected, "API_STATUS_" + str(response.status))
            return response.status, json.loads(raw) if raw else None
    finally:
        conn.close()


def configuration():
    return {
        "Image": IMAGE_ID, "User": "65532:65532", "WorkingDir": "/work",
        "Entrypoint": ["/usr/local/bin/python3", "-I", "-B", "-c", WORKER],
        "Cmd": [], "Env": IMAGE_ENV, "Tty": False, "OpenStdin": True,
        "StdinOnce": True, "AttachStdin": True, "AttachStdout": True,
        "AttachStderr": True, "Healthcheck": {"Test": ["NONE"]},
        "HostConfig": {
            "NetworkMode": "none", "ReadonlyRootfs": True,
            "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges=true"],
            "Privileged": False, "PidMode": "", "IpcMode": "private",
            "CgroupnsMode": "private", "Memory": 536870912,
            "MemorySwap": 536870912, "NanoCpus": 500000000,
            "PidsLimit": 32, "ShmSize": 8388608,
            "LogConfig": {"Type": "none", "Config": {}},
            "RestartPolicy": {"Name": "no", "MaximumRetryCount": 0},
            "AutoRemove": False, "Binds": [], "Devices": [],
            "Tmpfs": {"/work": "rw,noexec,nosuid,nodev,size=32m,nr_inodes=1024,mode=0700,uid=65532,gid=65532"},
        },
    }


def check_image(info):
    need(info.get("Id") == IMAGE_ID and info.get("Os") == "linux"
         and info.get("Architecture") == "amd64", "IMAGE_IDENTITY")
    need(info.get("RootFS", {}).get("Layers") == DIFF_IDS, "IMAGE_LAYERS")
    cfg = info.get("Config", {})
    need(cfg.get("Env") == IMAGE_ENV and cfg.get("Cmd") == ["python3"], "IMAGE_CONFIG")
    for key in ("Volumes", "Entrypoint", "Healthcheck", "OnBuild", "ExposedPorts"):
        need(not cfg.get(key), "IMAGE_DEFAULTS")


def check_effective(info, cid):
    need(info.get("Id") == exact_id(cid) and info.get("Image") == IMAGE_ID, "CONTAINER_IDENTITY")
    expected = configuration()
    cfg, host = info.get("Config", {}), info.get("HostConfig", {})
    for key in ("User", "WorkingDir", "Entrypoint", "Env", "Tty", "OpenStdin",
                "StdinOnce", "AttachStdin", "AttachStdout", "AttachStderr", "Healthcheck"):
        need(cfg.get(key) == expected[key], "EFFECTIVE_CONFIG")
    need(not cfg.get("Cmd") and not cfg.get("Volumes") and not cfg.get("ExposedPorts"), "HIDDEN_CONFIG")
    for key, value in expected["HostConfig"].items():
        actual = host.get(key)
        if key in ("Binds", "Devices"):
            need(not actual, "HIDDEN_MOUNT_DEVICE")
        else:
            need(actual == value, "EFFECTIVE_HOST_CONFIG_" + key)
    for key in ("Mounts", "VolumesFrom", "CapAdd", "GroupAdd", "DeviceRequests",
                "PortBindings", "Links", "ExtraHosts", "Dns", "DnsSearch"):
        need(not host.get(key), "HIDDEN_HOST_CONFIG")
    need(not info.get("Mounts"), "UNEXPECTED_MOUNTS")
    need(bool(host.get("MaskedPaths")) and bool(host.get("ReadonlyPaths")), "SYSTEM_PATH_PROTECTION")


def read_exact(stream, count, *, eof=False):
    result = bytearray()
    while len(result) < count:
        part = stream.recv(min(8192, count - len(result)))
        if not part and not result and eof:
            return None
        need(bool(part), "STREAM_TRUNCATED")
        result.extend(part)
    return bytes(result)


def frame_header(raw, remaining):
    need(type(raw) is bytes and len(raw) == 8, "FRAME_HEADER")
    channel, pad, size = raw[0], raw[1:4], struct.unpack(">I", raw[4:])[0]
    need(channel in (1, 2) and pad == b"\0\0\0" and size > 0, "FRAME_HEADER")
    need(size <= remaining[channel], "STDOUT_LIMIT" if channel == 1 else "STDERR_LIMIT")
    return channel, size


def attach(cid):
    stream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        stream.settimeout(3)
        stream.connect(SOCKET)
        path = API + "/containers/" + exact_id(cid) + "/attach?stream=1&stdin=1&stdout=1&stderr=1&logs=0"
        stream.sendall(("POST " + path + " HTTP/1.1\r\nHost: localhost\r\n"
                        "Connection: Upgrade\r\nUpgrade: tcp\r\nContent-Length: 0\r\n\r\n").encode("ascii"))
        header = bytearray()
        # One-byte reads only for the bounded header: never discard initial frames.
        while not header.endswith(b"\r\n\r\n"):
            need(len(header) < 8192, "ATTACH_HEADER_LIMIT")
            header.extend(read_exact(stream, 1))
        need(header.startswith(b"HTTP/1.1 101 "), "ATTACH_UPGRADE")
        return stream
    except BaseException:
        stream.close()
        raise


def fixture(job, scenario):
    need(scenario in SCENARIOS, "SCENARIO_INVALID")
    ctx = validator.make_context(job_id=job, generation=1, baseline={},
                                 allowed={"docs/notes/synthetic.md": "create"})
    proposal = {"schema_version": 1, "job_id": job, "generation": 1,
                "base_manifest_sha256": ctx.base_manifest_sha256,
                "changes": [{"path": "docs/notes/synthetic.md", "operation": "create",
                             "before_sha256": None, "content_utf8": "synthetic\n"}]}
    return ctx, encoded({"scenario": scenario, "proposal": proposal}) + b"\n"


def release_hash():
    # Explicit trusted four-module closure, not a worker-selected import path.
    return capture.digest(b"".join(Path(p).read_bytes() for p in
                                  (__file__, capture.__file__, validator.__file__, observer.__file__)))


def trial_pins(job, scenario):
    ctx, packet = fixture(job, scenario)
    return {"generation": 1, "attempt": 1, "image_id": IMAGE_ID,
            "packet_sha256": capture.digest(packet),
            "context_sha256": validator.context_info(ctx)[3],
            "release_sha256": release_hash(),
            "profile_sha256": capture.digest(encoded(configuration()))}


def limits(cpu):
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_FSIZE, (65536, 65536))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))


def child(connection, job, scenario):
    stream = None
    stage = "admission"
    try:
        # Child inherits the parent's hard limit; never try to raise it.
        limits(10)
        ctx, packet = fixture(job, scenario)
        now = lambda: int(time.monotonic() * 1000)
        binding = capture.Attempt(job, 1, 1, capture.digest(packet),
                                  validator.context_info(ctx)[3], release_hash(),
                                  capture.digest(encoded(configuration())))
        col = capture.Collector(binding, packet, now_ms=now())
        event = lambda kind, payload=None: col.event(col.handle, kind, now_ms=now(), payload=payload)
        stage = "image_inspect"
        check_image(api("GET", "/images/" + IMAGE_ID + "/json")[1])
        stage = "create"
        connection.send({"phase": "create_intent"})
        need(connection.poll(3) and connection.recv() == "ack", "PARENT_ACK")
        _, created = api("POST", "/containers/create?name=" + job, configuration(), (201,))
        cid = exact_id(created["Id"])
        # Parent fsyncs this ID before allowing ANY start dispatch.
        connection.send({"phase": "created", "id": cid})
        need(connection.poll(3) and connection.recv() == "ack", "PARENT_ACK")
        need(not created.get("Warnings"), "CREATE_WARNING")
        stage = "effective_inspect"
        check_effective(api("GET", "/containers/" + cid + "/json")[1], cid)
        stage = "attach"
        stream = attach(cid)
        need(event("attach") == "OK", "COLLECTOR_ATTACH")
        need(event("start_requested") == "OK", "COLLECTOR_START_INTENT")
        connection.send({"phase": "start_intent"})
        need(connection.poll(3) and connection.recv() == "ack", "PARENT_ACK")
        stage = "start"
        api("POST", "/containers/" + cid + "/start", expected=(204,))
        need(event("start") == "OK", "COLLECTOR_START")
        connection.send({"phase": "running"})
        stage = "capture"
        stream.sendall(packet)
        # Input is newline-framed. Worker does not need EOF; don't half-close attach.
        remaining = {1: capture.MAX_STDOUT, 2: capture.MAX_STDERR}
        command_end = time.monotonic() + 30
        while True:
            need(time.monotonic() < command_end, "COMMAND_DEADLINE")
            stream.settimeout(min(3, max(.01, command_end - time.monotonic())))
            raw = read_exact(stream, 8, eof=True)
            if raw is None:
                break
            channel, size = frame_header(raw, remaining)
            remaining[channel] -= size
            while size:
                part = read_exact(stream, min(size, 8192))
                size -= len(part)
                need(event("stdout" if channel == 1 else "stderr", part) == "OK", "COLLECTOR_BYTES")
        stage = "termination"
        state = api("GET", "/containers/" + cid + "/json")[1]["State"]
        need(state["Status"] == "exited" and not state["Running"] and not state["OOMKilled"], "EXIT_UNCONFIRMED")
        for kind, payload in (("stdout_eof", None), ("stderr_eof", None),
                              ("exit", state["ExitCode"]), ("stopped", None)):
            need(event(kind, payload) == "OK", "COLLECTOR_TERMINATION")
        sealed = col.take(col.handle, now_ms=now())
        need(sealed is not None, "CAPTURE_INCOMPLETE")
        connection.send({"phase": "validating"})
        stage = "validation"
        candidate = validator.validate_changeset(sealed.proposal, context=ctx)
        connection.send({"phase": "result", "status": "validated_synthetic_only",
                         "candidate_sha256": candidate.candidate_sha256,
                         "packet_sha256": binding.packet_sha256,
                         "proposal_sha256": sealed.proposal_sha256,
                         "context_sha256": binding.context_sha256,
                         "release_sha256": binding.release_sha256,
                         "profile_sha256": binding.profile_sha256,
                         "exit_code": state["ExitCode"], "stderr_bytes": sealed.stderr_bytes})
    except (TrialError, validator.ValidationError) as exc:
        connection.send({"phase": "result", "status": "rejected", "reason": str(exc), "failure_stage": stage})
    except BaseException as exc:
        error_type = next((c.__name__ for c in (OSError, MemoryError, KeyError, ValueError, AttributeError)
                           if isinstance(exc, c)), "Other")
        connection.send({"phase": "result", "status": "rejected", "reason": "TRANSPORT_OR_CHILD_FAILURE",
                         "failure_stage": stage, "error_type": error_type})
    finally:
        if stream is not None:
            stream.close()
        connection.close()


def cleanup(cid):
    """Only caller-recorded newly created ID. Force removal fences future starts.

    Never use names/labels/globs for deletion. Any ambiguous request is non-success;
    no retries, no prune, and no assertion that killing a client killed a container.
    """
    target = "/containers/" + exact_id(cid)
    api("DELETE", target + "?force=1&v=0", expected=(204, 404), timeout=3)
    status, _ = api("GET", target + "/json", expected=(404,), timeout=3)
    return status == 404


def observe_process(cid, *, job, pins):
    """Delegate fixed-field observation using original admission pins, never output IDs.

    This is still unprivileged/in-process. No privileged service is activated here.
    PID handles/cgroup/current Docker identity reduce stale-PID confusion; they do
    not turn this observation into an atomic or full egress-security measurement.
    """
    session = None
    try:
        inspect = lambda: api("GET", "/containers/" + exact_id(cid) + "/json")[1]
        info = inspect()
        state = info.get("State", {})
        binding = observer.Binding(job, cid, state.get("Pid"), state.get("StartedAt"),
                                   pins["generation"], pins["attempt"], pins["packet_sha256"],
                                   pins["context_sha256"], pins["release_sha256"], pins["profile_sha256"])
        observer.check_binding(binding)
        need(info.get("Id") == cid and state.get("Running") is True, "OBSERVER_IDENTITY")
        # API calls have their own total timers; Session checks elapsed across them.
        with observer.ProcTarget(binding.pid) as target:
            host_net = observer.namespace_number(os.readlink("/proc/self/ns/net"))
            session = observer.Session(binding, target, inspect, host_net)
            measured = session.observe(session.handle)
            expected = {"uid": [65532] * 4, "gid": [65532] * 4,
                        "effective_capabilities": 0, "no_new_privileges": 1, "seccomp_mode": 2}
            if measured["process_controls"] != expected or measured["network_namespace_differs"] is not True:
                return {"status": "blocked", "reason": "HOST_OBSERVER_CONTROL_MISMATCH"}
            return measured
    except observer.ObserverError as exc:
        return {"status": "blocked", "reason": str(exc),
                "failure_stage": session.phase if session is not None else "target_admission",
                "authority": "NOT_security_acceptance"}
    except PermissionError:
        return {"status": "blocked", "reason": "HOST_OBSERVER_PERMISSION_DENIED"}
    except OSError:
        return {"status": "blocked", "reason": "HOST_OBSERVER_UNAVAILABLE"}


def private_store():
    import fcntl
    root = Path("/tmp") / ("academic-hpc2-" + str(os.getuid()))
    try:
        root.mkdir(mode=0o700)
    except FileExistsError:
        pass
    st = root.lstat()
    import stat
    need(stat.S_ISDIR(st.st_mode) and st.st_uid == os.getuid()
         and st.st_mode & 0o077 == 0, "STORE_PERMISSIONS")
    fd = os.open(root / "lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        need(not list(root.glob("*.pending")), "INTERRUPTED_RECEIPT_WRITE")
        receipts = list(root.glob("*.json"))
        need(len(receipts) < 32, "RECEIPT_QUOTA")
        for path in receipts:
            need(not path.is_symlink() and path.stat().st_size <= 65536, "RECEIPT_INVALID")
            need(json.loads(path.read_bytes()).get("cleanup") == "confirmed_absent", "UNRESOLVED_ATTEMPT")
        return root, fd
    except BaseException:
        os.close(fd)
        raise


def save(path, record):
    raw = encoded(record)
    need(len(raw) <= 65536, "RECEIPT_BYTES")
    temp = path.with_suffix(".pending")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def supervise(scenario):
    need(sys.platform == "linux", "LINUX_ONLY")
    need(scenario in SCENARIOS, "SCENARIO_INVALID")
    limits(10)
    root, lock = private_store()
    job = "academic-hpc2-" + uuid.uuid4().hex
    receipt = root / (job + ".json")
    record = {"job": job, "scenario": scenario, "cleanup": "not_started",
              "status": "incomplete", "authority": "NOT_acceptance_or_agent_enforcement"}
    record.update(trial_pins(job, scenario))
    context = multiprocessing.get_context("fork")
    parent, child_end = context.Pipe()
    process = context.Process(target=child, args=(child_end, job, scenario))
    began = time.monotonic()
    work_end = began + 45  # leaves teardown inside 60s overall profile
    cid, created_intent, start_at = None, False, None
    try:
        save(receipt, record)
        process.start()
        child_end.close()
        while process.is_alive() or parent.poll():
            elapsed = time.monotonic() - began
            if time.monotonic() >= work_end:
                record.update(status="rejected", reason="WATCHDOG_DEADLINE")
                break
            if scenario == "cancel" and start_at is not None and time.monotonic() - start_at >= .5:
                record.update(status="rejected", reason="OPERATOR_SYNTHETIC_CANCEL")
                break
            if scenario == "hang" and start_at is not None and time.monotonic() - start_at >= 1:
                record.update(status="rejected", reason="SYNTHETIC_COMMAND_DEADLINE")
                break
            if not parent.poll(.05):
                continue
            try:
                message = parent.recv()
            except EOFError:
                break
            phase = message.get("phase")
            if phase == "create_intent":
                created_intent = True
                record["cleanup"] = "create_unknown"
            elif phase == "created":
                cid = exact_id(message["id"])
                record.update(container_id=cid, cleanup="required")
            elif phase == "start_intent":
                record["start"] = "unconfirmed"
            elif phase == "running":
                start_at = time.monotonic()
                record["start"] = "acknowledged"
                if scenario == "observe":
                    record["observer"] = observe_process(cid, job=job, pins=record)
            elif phase == "validating":
                work_end = min(work_end, time.monotonic() + 10)
            elif phase == "result":
                if message.get("status") == "validated_synthetic_only":
                    for key in ("packet_sha256", "context_sha256", "release_sha256", "profile_sha256"):
                        need(message.get(key) == record[key], "RESULT_BINDING_MISMATCH")
                record.update(message)
            else:
                raise TrialError("CHILD_PROTOCOL")
            save(receipt, record)
            if phase in ("create_intent", "created", "start_intent"):
                parent.send("ack")
        process.join(.2)
        if process.exitcode not in (None, 0):
            record.update(status="rejected", reason="CHILD_EXIT")
    except BaseException:
        record.update(status="rejected", reason="SUPERVISOR_INTERRUPTED_OR_FAILED")
    finally:
        if process.is_alive():
            process.kill()
            process.join(1)
        # Client is quiescent first. Even an in-flight daemon start must meet a
        # deleted exact ID; ambiguity remains non-success, never restart/retry.
        try:
            if cid is not None:
                cleanup(cid)
                record["cleanup"] = "confirmed_absent"
            elif not created_intent:
                record["cleanup"] = "confirmed_absent"
            else:
                record["cleanup"] = "create_unknown_operator_reconcile"
        except BaseException:
            record["cleanup"] = "unknown_operator_reconcile"
        if record["cleanup"] != "confirmed_absent" or process.is_alive():
            record.update(status="blocked", reason="CLEANUP_UNCONFIRMED")
        elif record["status"] == "incomplete":
            record.update(status="rejected", reason="MISSING_RESULT")
        if record.get("observer", {}).get("status") == "blocked":
            record.update(status="blocked", reason="HOST_OBSERVER_NOT_READY")
        record["elapsed_seconds"] = round(time.monotonic() - began, 3)
        if record["elapsed_seconds"] >= 60:
            record.update(status="blocked", reason="OVERALL_DEADLINE_EXCEEDED")
        save(receipt, record)
        parent.close()
        os.close(lock)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=SCENARIOS)
    args = parser.parse_args()
    try:
        result = supervise(args.scenario)
    except TrialError as exc:
        result = {"status": "blocked", "reason": str(exc)}
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result.get("status") == "validated_synthetic_only" else 2


if __name__ == "__main__":
    raise SystemExit(main())
