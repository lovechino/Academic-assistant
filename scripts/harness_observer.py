"""Bounded observer building block; no daemon, privilege grant or public PID API.

Only trusted controller code may construct a target/session. In-process handles
are NOT authenticated IPC. Never install this mutable repo module with capabilities.
Linux I/O reads fixed proc fields through held descriptors; no Docker/network/shell.
"""
from dataclasses import asdict, dataclass
import os
import re
import select
import sys
import time


MAX_PROC = 65536
MAX_SESSION_MS = 2000


class ObserverError(Exception):
    """Only fixed error codes are exposed."""


def require(condition, code):
    if not condition:
        raise ObserverError(code)


def clock_ms():
    return time.monotonic_ns() // 1_000_000


def start_ticks(raw, pid):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_PROC, "STAT_BYTES")
    end = raw.rfind(b")")
    require(raw.startswith((str(pid) + " (").encode()) and end > 0, "STAT_IDENTITY")
    fields = raw[end + 1:].split()
    require(len(fields) >= 20 and re.fullmatch(rb"[0-9]{1,20}", fields[19]), "STAT_SCHEMA")
    return int(fields[19])


def controls(raw, pid):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_PROC, "STATUS_BYTES")
    keys = {b"Tgid", b"Uid", b"Gid", b"CapEff", b"NoNewPrivs", b"Seccomp"}
    found = {}
    for line in raw.splitlines():
        key, _, value = line.partition(b":")
        if key in keys:
            require(key not in found, "STATUS_DUPLICATE")
            found[key] = value.split()
    require(found.keys() == keys, "STATUS_MISSING")
    for key, count in ((b"Tgid", 1), (b"Uid", 4), (b"Gid", 4),
                       (b"NoNewPrivs", 1), (b"Seccomp", 1)):
        require(len(found[key]) == count and all(re.fullmatch(rb"[0-9]{1,10}", x)
                                                for x in found[key]), "STATUS_SCHEMA")
    require(int(found[b"Tgid"][0]) == pid, "STATUS_IDENTITY")
    uid, gid = [int(x) for x in found[b"Uid"]], [int(x) for x in found[b"Gid"]]
    require(all(x <= 2**32 - 1 for x in uid + gid), "STATUS_SCHEMA")
    cap = found[b"CapEff"]
    require(len(cap) == 1 and re.fullmatch(rb"[0-9a-fA-F]{16}", cap[0]), "STATUS_SCHEMA")
    nnp, seccomp = int(found[b"NoNewPrivs"][0]), int(found[b"Seccomp"][0])
    require(nnp in (0, 1) and seccomp in (0, 1, 2), "STATUS_SCHEMA")
    return {"uid": uid, "gid": gid, "effective_capabilities": int(cap[0], 16),
            "no_new_privileges": nnp, "seccomp_mode": seccomp}


def cgroup_matches(raw, container_id):
    require(type(raw) is bytes and len(raw) <= MAX_PROC, "CGROUP_BYTES")
    require(type(container_id) is str and re.fullmatch(r"[0-9a-f]{64}", container_id), "BINDING_INVALID")
    components = {container_id.encode(), ("docker-" + container_id + ".scope").encode()}
    for line in raw.splitlines():
        parts = line.split(b":", 2)
        require(len(parts) == 3 and parts[2].startswith(b"/"), "CGROUP_SCHEMA")
        if components.intersection(parts[2].split(b"/")):
            return True
    return False


def namespace_number(link):
    require(type(link) is str and re.fullmatch(r"net:\[[0-9]{1,20}\]", link), "NAMESPACE_SCHEMA")
    return int(link[5:-1])


class ProcTarget:
    """Held pidfd + proc directory. Caller supplies an already authorized PID.

    Holding proc descriptors does not prevent PID reuse, but operations on the old
    proc descriptor do not retarget a new process. pidfd detects the old exit.
    No method for environ, cmdline, mem, root, cwd, fd enumeration or namespace entry.
    """
    def __init__(self, pid):
        require(sys.platform == "linux" and hasattr(os, "pidfd_open"), "PIDFD_UNSUPPORTED")
        require(type(pid) is int and 1 < pid <= 2**31 - 1, "PID_INVALID")
        self.pid, self._pidfd, self._proc = pid, None, None
        try:
            self._pidfd = os.pidfd_open(pid, 0)
            self._proc = os.open("/proc/" + str(pid), os.O_RDONLY | os.O_DIRECTORY
                                 | os.O_CLOEXEC | os.O_NOFOLLOW)
            self.assert_alive()
            self.started = self.read_start()
            self.assert_alive()
        except BaseException:
            self.close()
            raise

    def _read_fixed(self, name):
        require(name in ("status", "stat", "cgroup") and self._proc is not None, "FIELD_NOT_ALLOWED")
        fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=self._proc)
        try:
            raw = bytearray()
            while len(raw) <= MAX_PROC:
                chunk = os.read(fd, min(4096, MAX_PROC + 1 - len(raw)))
                if not chunk:
                    break
                raw.extend(chunk)
            require(len(raw) <= MAX_PROC, "PROC_BYTES")
            return bytes(raw)
        finally:
            os.close(fd)

    def assert_alive(self):
        require(self._pidfd is not None, "PROCESS_CLOSED")
        poller = select.poll()
        poller.register(self._pidfd, select.POLLIN)
        require(not poller.poll(0), "PROCESS_EXITED")

    def read_start(self):
        return start_ticks(self._read_fixed("stat"), self.pid)

    def read_controls(self):
        return controls(self._read_fixed("status"), self.pid)

    def belongs_to(self, container_id):
        return cgroup_matches(self._read_fixed("cgroup"), container_id)

    def read_network_namespace(self):
        require(self._proc is not None, "PROCESS_CLOSED")
        # Only traverse this directory: O_RDONLY would unnecessarily require
        # directory-list/read DAC permission for a different UID's ns directory.
        fd = os.open("ns", os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                     dir_fd=self._proc)
        try:
            return namespace_number(os.readlink("net", dir_fd=fd))
        finally:
            os.close(fd)

    def close(self):
        for key in ("_proc", "_pidfd"):
            fd = getattr(self, key, None)
            if fd is not None:
                os.close(fd)
                setattr(self, key, None)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


@dataclass(frozen=True, slots=True)
class Binding:
    job_id: str
    container_id: str
    pid: int
    started_at: str
    generation: int
    attempt: int
    packet_sha256: str
    context_sha256: str
    release_sha256: str
    profile_sha256: str


def check_binding(binding):
    require(type(binding) is Binding, "BINDING_INVALID")
    require(type(binding.job_id) is str and re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9-]{2,63}", binding.job_id), "BINDING_INVALID")
    require(type(binding.pid) is int and 1 < binding.pid <= 2**31 - 1, "BINDING_INVALID")
    require(all(type(x) is int and 1 <= x <= 2**31 - 1 for x in
                (binding.generation, binding.attempt)), "BINDING_INVALID")
    require(type(binding.started_at) is str and re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?Z", binding.started_at), "BINDING_INVALID")
    require(all(type(x) is str and re.fullmatch(r"[0-9a-f]{64}", x) for x in
                (binding.container_id, binding.packet_sha256, binding.context_sha256,
                 binding.release_sha256, binding.profile_sha256)), "BINDING_INVALID")


class Session:
    """Trusted serialized caller only; one attempt, one observation, no IPC authority.

    inspector is a trusted exact-ID read port. Targets/inspectors are injectable in
    tests; accepting arbitrary ports from a worker would defeat this boundary.
    Caller owns descriptor close and independent hard wall deadline.
    """
    def __init__(self, binding, target, inspector, host_network_namespace, *, clock=clock_ms):
        check_binding(binding)
        require(target.pid == binding.pid, "PROCESS_MISMATCH")
        require(type(host_network_namespace) is int and host_network_namespace > 0, "NAMESPACE_SCHEMA")
        self.binding, self.target, self.inspector = binding, target, inspector
        self.host_net, self.clock = host_network_namespace, clock
        self.handle = object()
        self.state = "ready"
        self.phase = "admitted"
        self.initial = clock()
        require(type(self.initial) is int and self.initial >= 0, "CLOCK_INVALID")
        self.last = self.initial

    def _guard(self):
        now = self.clock()
        require(type(now) is int and now >= self.last, "CLOCK_INVALID")
        self.last = now
        require(now - self.initial < MAX_SESSION_MS, "OBSERVATION_DEADLINE")
        require(self.state == "measuring", "SESSION_REVOKED")

    def _current(self):
        self._guard()
        self.phase = "container_identity"
        info = self.inspector()
        self._guard()
        state = info.get("State", {})
        require(info.get("Id") == self.binding.container_id
                and state.get("Running") is True
                and type(state.get("Pid")) is int and state["Pid"] == self.binding.pid
                and state.get("StartedAt") == self.binding.started_at, "CONTAINER_CHANGED")
        self.phase = "process_identity"
        self.target.assert_alive()
        require(self.target.read_start() == self.target.started, "PROCESS_CHANGED")
        self._guard()
        self.phase = "cgroup_identity"
        require(self.target.belongs_to(self.binding.container_id), "CGROUP_MISMATCH")
        self._guard()

    def cancel(self, handle):
        require(handle is self.handle, "STALE_SESSION")
        self.state = "cancelled"

    def observe(self, handle):
        require(handle is self.handle, "STALE_SESSION")
        require(self.state == "ready", "SESSION_UNAVAILABLE")
        self.state = "measuring"
        try:
            self._current()
            self.phase = "controls"
            observed = self.target.read_controls()
            self._guard()
            self.phase = "network_namespace"
            namespace = self.target.read_network_namespace()
            self._guard()
            self._current()
            self._guard()
            self.state = "consumed"
            return {"status": "partial_observation_only", "binding": asdict(self.binding),
                    "process_start_ticks": self.target.started, "process_controls": observed,
                    "network_namespace_differs": namespace != self.host_net,
                    "atomic_snapshot": False, "authority": "NOT_access_or_egress_acceptance"}
        except PermissionError:
            self.state = "failed"
            raise ObserverError("HOST_OBSERVER_PERMISSION_DENIED") from None
        except OSError:
            self.state = "failed"
            raise ObserverError("HOST_OBSERVER_UNAVAILABLE") from None
        except BaseException:
            self.state = "failed"
            raise


if __name__ == "__main__":
    raise SystemExit("LIBRARY_ONLY_NO_PRIVILEGED_SERVICE")
