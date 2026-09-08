"""HPC-2 pure single-attempt collector model; NOT a runner/security boundary.

Only a trusted, serialized caller may supply handles, clock or lifecycle events.
No I/O, worker execution, timers, Docker wire framing, approval or durable replay.
"""
from dataclasses import dataclass, field
import hashlib
import re


MAX_PACKET = 4 * 1024 * 1024
MAX_STDOUT = 1024 * 1024
MAX_STDERR = 256 * 1024
DEADLINE_MS = 60_000
MAX_CLOCK = 2**63 - 1
EVENTS = frozenset({"attach", "start_requested", "start", "stdout", "stderr", "stdout_eof",
                    "stderr_eof", "exit", "stopped", "disconnect", "cancel", "tick"})


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def clock_value(value) -> bool:
    return type(value) is int and 0 <= value <= MAX_CLOCK


@dataclass(frozen=True, slots=True)
class Attempt:
    """Caller-assumed pins, not authenticated identity or access grants."""
    job_id: str
    generation: int
    attempt: int
    packet_sha256: str
    context_sha256: str
    release_sha256: str
    profile_sha256: str


@dataclass(frozen=True, slots=True)
class CapturedProposal:
    """One in-memory observation, NOT validated content/receipt/acceptance."""
    binding: Attempt
    proposal: bytes = field(repr=False)
    proposal_sha256: str
    stderr_bytes: int


class Collector:
    """No reset/retry API. One object per attempt; multi-job admission is absent.

    Deadline checks run on calls only. The caller must own scheduling, cancellation,
    lifecycle observations and memory allocated before event() in a future adapter.
    """

    def __init__(self, binding: Attempt, packet: bytes, *, now_ms: int):
        valid = (type(binding) is Attempt and type(packet) is bytes
                 and 0 < len(packet) <= MAX_PACKET and clock_value(now_ms)
                 and now_ms <= MAX_CLOCK - DEADLINE_MS)
        if valid:
            valid = (type(binding.job_id) is str and
                     re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{2,63}", binding.job_id)
                     and all(type(n) is int and 1 <= n <= 2**31 - 1
                             for n in (binding.generation, binding.attempt))
                     and all(type(h) is str and re.fullmatch(r"[0-9a-f]{64}", h)
                             for h in (binding.packet_sha256, binding.context_sha256,
                                       binding.release_sha256, binding.profile_sha256))
                     and binding.packet_sha256 == digest(packet))
        if not valid:
            raise ValueError("ADMISSION_INVALID")
        self._binding = binding
        self._handle = object()
        self._last_ms = now_ms
        self._deadline = now_ms + DEADLINE_MS
        self._state = "admitted"
        self._reason = None
        self._stdout = bytearray()
        self._stderr_bytes = 0
        self._events = 0
        self._started = False
        self._start_requested = False
        self._stopped = False
        self._eofs = set()
        self._exit = None

    @property
    def handle(self):
        """In-process routing identity, to be kept outside worker data."""
        return self._handle

    def snapshot(self) -> dict:
        """Fixed vocabulary/counts only; no worker log or exception payload."""
        return {"state": self._state, "reason": self._reason,
                "stdout_retained": len(self._stdout), "stderr_bytes": self._stderr_bytes,
                "data_events": self._events,
                "start_unconfirmed": self._start_requested and not self._started and not self._stopped,
                "stop_required": self._start_requested and not self._stopped,
                "authority": "synthetic_only_NOT_enforcement_or_approval"}

    def _fail(self, code: str) -> str:
        if self._state not in {"failed", "consumed"}:
            self._reason = code
            self._state = "failed"
            self._stdout.clear()
        return code

    def _check_call(self, handle, now_ms):
        if handle is not self._handle:
            return "STALE_HANDLE"
        if self._state == "consumed":
            return "TERMINAL"
        if not clock_value(now_ms) or now_ms < self._last_ms:
            return self._fail("CLOCK_INVALID")
        self._last_ms = now_ms
        if self._state == "failed":
            return "TERMINAL"
        if now_ms >= self._deadline:
            return self._fail("DEADLINE")
        return None

    def event(self, handle, kind: str, *, now_ms: int, payload=None) -> str:
        """Fake adapter feeds bytes; all non-byte events are trusted observations.

        Worker output is NEVER decoded into events. Wrong handles do not poison
        this attempt. Valid-handle protocol errors invalidate the whole capture.
        """
        blocked = self._check_call(handle, now_ms)
        # Allow a trusted stop acknowledgment after failure/deadline, but never
        # change the outcome or restore discarded bytes. No real cleanup here.
        if blocked:
            if (blocked in {"TERMINAL", "DEADLINE"} and self._state == "failed"
                    and handle is self._handle and type(kind) is str
                    and kind == "stopped" and payload is None
                    and clock_value(now_ms) and now_ms >= self._last_ms and self._start_requested):
                self._stopped = True
                return "STOP_OBSERVED_AFTER_FAILURE"
            return blocked
        if type(kind) is not str or kind not in EVENTS:
            return self._fail("EVENT_INVALID")
        if kind in {"stdout", "stderr"}:
            if type(payload) is not bytes:
                return self._fail("PAYLOAD_INVALID")
            if not payload:
                return self._fail("EMPTY_CHUNK")
        elif kind == "exit":
            if type(payload) is not int or not 0 <= payload <= 255:
                return self._fail("EXIT_INVALID")
        elif payload is not None:
            return self._fail("PAYLOAD_INVALID")
        if kind == "cancel":
            return self._fail("CANCELLED")
        if kind == "disconnect":
            return self._fail("DISCONNECTED")
        if kind == "tick":
            return "OK"
        if kind == "attach" and self._state == "admitted":
            self._state = "attached"
            return "OK"
        if kind == "start_requested" and self._state == "attached":
            # Trusted caller records intent BEFORE dispatching an external start.
            self._state = "starting"
            self._start_requested = True
            return "OK"
        if kind == "start" and self._state == "starting":
            self._state = "running"
            self._started = True
            return "OK"
        if kind == "stopped" and self._state == "starting":
            self._stopped = True
            return self._fail("START_UNCONFIRMED")
        if self._state != "running":
            return self._fail("ORDER_INVALID")
        if kind in {"stdout", "stderr"}:
            if kind in self._eofs:
                return self._fail("DATA_AFTER_EOF")
            if kind == "stdout":
                if len(payload) > MAX_STDOUT - len(self._stdout):
                    return self._fail("STDOUT_LIMIT")
                self._stdout.extend(payload)
            else:
                if len(payload) > MAX_STDERR - self._stderr_bytes:
                    return self._fail("STDERR_LIMIT")
                # Raw diagnostics never retained or rendered by this slice.
                self._stderr_bytes += len(payload)
            # Nonempty accepted chunks consume at least one byte each, so this
            # count is bounded by MAX_STDOUT + MAX_STDERR, independent of ticks.
            self._events += 1
        elif kind in {"stdout_eof", "stderr_eof"}:
            stream = kind.removesuffix("_eof")
            if stream in self._eofs:
                return self._fail("DUPLICATE_EOF")
            self._eofs.add(stream)
        elif kind == "exit":
            if self._exit is not None:
                return self._fail("DUPLICATE_EXIT")
            self._exit = payload
            if payload != 0:
                return self._fail("EXIT_NONZERO")
        elif kind == "stopped":
            if self._stopped:
                return self._fail("DUPLICATE_STOP")
            self._stopped = True
        else:
            return self._fail("ORDER_INVALID")
        if self._eofs == {"stdout", "stderr"} and self._exit == 0 and self._stopped:
            if not self._stdout:
                return self._fail("EMPTY_PROPOSAL")
            self._state = "complete"
        return "OK"

    def take(self, handle, *, now_ms: int) -> CapturedProposal | None:
        """Consume once, before deadline. Further validation is a separate step.

        Cancel after take cannot recall returned bytes; HPC-3 currentness/acceptance
        remains absent. Caller must never interpret this as authority to apply.
        """
        if self._check_call(handle, now_ms) or self._state != "complete":
            return None
        raw = bytes(self._stdout)
        result = CapturedProposal(self._binding, raw, digest(raw), self._stderr_bytes)
        self._stdout.clear()
        self._state = "consumed"
        return result
