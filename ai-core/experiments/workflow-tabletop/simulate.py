"""Offline synthetic state-machine experiment, not an application or model test.

Read fixtures, print results, never write files or call network/model services.
The stub generates pre-authored claims; it cannot test semantic entailment.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "data/evaluation/simulations/grounded-qa-tabletop-v0.1/fixtures.json"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Simulation:
    def __init__(self, fixtures: dict, scenario: dict, disable: str = ""):
        self.fixtures = fixtures
        self.scenario = scenario
        self.disable = disable
        self.actor_id = scenario["actor"]
        self.actor = deepcopy(fixtures["actors"][self.actor_id])
        self.docs = {doc["id"]: deepcopy(doc) for doc in fixtures["sources"]}
        self.trace: list[dict] = []
        self.exposures: list[dict] = []
        self.violations: list[str] = []
        self.first_failure = None
        self.generator_stub_calls = 0
        self.repairs = 0
        self.cache_hydrations = 0
        self.delivery_claims: list[str] = []
        self.public_text = ""
        self.viewer = "not_emitted"
        self.outcome = "not_finished"
        self.catalog_epoch = 1
        self.revocation_epoch = 1
        self.retrieved: list[dict] = []
        self.packet: list[dict] = []
        self.pre_pack = 0
        self.post_pack = 0
        self.initial_post_pack = 0

    def step(self, stage: str, owner: str, status: str, result: str, **observed):
        self.trace.append({"step": len(self.trace) + 1, "stage": stage,
                           "owner": owner, "status": status, "result": result,
                           "observed": observed})

    def fail(self, tag: str):
        if self.first_failure is None:
            self.first_failure = tag

    def violate(self, tag: str):
        if tag not in self.violations:
            self.violations.append(tag)

    def evidence(self, doc: dict) -> dict:
        return {"doc_id": doc["id"], "revision": doc["revision"],
                "sha256": sha(doc["text"]), "start": 0, "end": len(doc["text"]),
                "text": doc["text"], "group": doc["group"]}

    def allowed(self, evidence: dict) -> bool:
        doc = self.docs[evidence["doc_id"]]
        return (doc["lifecycle"] == "synthetic_eligible"
                and self.actor["scope"] in doc["scopes"])

    def current(self, evidence: dict) -> bool:
        doc = self.docs[evidence["doc_id"]]
        return (evidence["revision"] == doc["revision"]
                and evidence["sha256"] == sha(doc["text"]))

    def observe_exposure(self, stage: str, evidences: list[dict]):
        # Observer evaluates live fixture state even when a simulated guard is disabled.
        for evidence in evidences:
            doc = self.docs[evidence["doc_id"]]
            authorized = (doc["lifecycle"] == "synthetic_eligible"
                          and self.actor["scope"] in doc["scopes"])
            version_valid = (evidence["revision"] == doc["revision"]
                             and evidence["sha256"] == sha(doc["text"]))
            self.exposures.append({"stage": stage, "doc_id": doc["id"],
                                   "actor": self.actor_id, "revision": evidence["revision"],
                                   "live_revision": doc["revision"],
                                   "revocation_epoch": self.revocation_epoch,
                                   "authorized_at_action": authorized,
                                   "version_valid_at_action": version_valid})
            if not authorized:
                self.violate("unauthorized_" + stage)
            if stage == "cache_hydration" and not version_valid:
                self.violate("stale_cache_hydration")

    def covered_groups(self, evidences: list[dict]) -> set[str]:
        covered = set()
        for doc in self.docs.values():
            intervals = []
            for evidence in evidences:
                if evidence["doc_id"] != doc["id"] or not self.current(evidence):
                    continue
                start, end = evidence["start"], evidence["end"]
                if (0 <= start < end <= len(doc["text"])
                        and evidence["text"] == doc["text"][start:end]):
                    intervals.append((start, end))
            cursor = 0
            for start, end in sorted(intervals):
                if start > cursor:
                    break
                cursor = max(cursor, end)
            if cursor == len(doc["text"]):
                covered.add(doc["group"])
        return covered

    def revoke(self, stage: str):
        self.docs["syn-queue"]["lifecycle"] = "revoked"
        self.revocation_epoch += 1
        self.step(stage, "Backend giả lập", "EVENT",
                  "Thu hồi nguồn queue; tăng revocation epoch. Không thể thu hồi nội dung đã hiển thị trước đó.",
                  revocation_epoch=self.revocation_epoch)

    def replace_version(self, stage: str):
        doc = self.docs["syn-queue"]
        doc["revision"] = 2
        doc["text"] += " Đây là bản giả lập v2."
        self.catalog_epoch += 1
        self.step(stage, "Backend giả lập", "EVENT",
                  "Nguồn queue chuyển v2; fixture không giữ bản v1 có thể mở. Cache/index cũ không được tự coi là hiện hành.",
                  catalog_epoch=self.catalog_epoch, old_version_available=False)

    def fingerprint(self, actor_id: str | None = None) -> dict:
        actor_id = actor_id or self.actor_id
        actor = self.fixtures["actors"][actor_id]
        return {"tenant": actor["tenant"], "course": actor["course"],
                "principal": actor_id, "scope": actor["scope"],
                "authz_epoch": actor["authz_epoch"],
                "revocation_epoch": self.revocation_epoch,
                "catalog_epoch": self.catalog_epoch,
                "question_hash": sha(self.fixtures["question"]),
                "policy": "synthetic-policy-1", "pipeline": "stub-1"}

    def cache_check(self):
        fault = self.scenario["fault"]
        if not fault.startswith("cache_"):
            self.step("Cache", "Backend giả lập", "MISS", "Không có cache; đi tiếp retrieval.")
            return
        old_key = self.fingerprint("student-a")
        dependencies = [self.evidence(doc) for doc in self.docs.values()]
        if fault == "cache_revoked":
            self.revoke("Sự kiện trước đọc cache")
        elif fault == "cache_old_version":
            self.replace_version("Sự kiện trước đọc cache")
        current_key = self.fingerprint()
        different = [key for key in old_key if old_key[key] != current_key[key]]
        valid = (not different and all(self.allowed(e) and self.current(e) for e in dependencies))
        if valid or self.disable == "cache":
            self.cache_hydrations += 1
            self.observe_exposure("cache_hydration", dependencies)
            self.step("Cache", "Backend giả lập", "UNSAFE" if not valid else "HIT",
                      "Nạp payload cache vào request. Lượt mutation cố ý bỏ qua validation; observer vẫn kiểm tra quyền/version.",
                      differing_key_fields=different, ttl_expired=False, hydrated=True)
        else:
            tags = {"cache_revoked": "cache_stale_authorization",
                    "cache_other_scope": "cache_scope_mismatch",
                    "cache_old_version": "cache_stale_version"}
            self.fail(tags[fault])
            self.step("Cache", "Backend giả lập", "REJECT",
                      "Cache còn TTL nhưng không hợp lệ; không nạp payload, loại ứng viên khỏi lần đọc và tìm lại theo scope hiện tại.",
                      differing_key_fields=different, ttl_expired=False, hydrated=False,
                      shared_entry_deleted=False)

    def finish(self) -> dict:
        actual = {"outcome": self.outcome, "delivered_claims": len(self.delivery_claims),
                  "generator_stub_calls": self.generator_stub_calls, "repair_attempts": self.repairs,
                  "viewer": self.viewer, "first_failure": self.first_failure}
        comparisons = [{"field": field, "expected": expected, "actual": actual[field],
                        "passed": actual[field] == expected}
                       for field, expected in self.scenario["expected"].items()]
        comparisons.append({"field": "unsafe_observations", "expected": [],
                            "actual": self.violations, "passed": not self.violations})
        self.step("Đối chiếu kỳ vọng", "Observer offline", "PASS" if all(c["passed"] for c in comparisons) else "FAIL",
                  "So sánh trạng thái thực chạy với kỳ vọng fixture và các hành động truy cập quan sát được.",
                  comparisons=comparisons)
        return {"id": self.scenario["id"], "name": self.scenario["name"],
                "disabled_guard": self.disable or None, "actual": actual,
                "conformant_to_fixture": all(c["passed"] for c in comparisons),
                "violations": self.violations, "comparisons": comparisons,
                "group_counts": {"required": 2, "retrieved": self.pre_pack,
                                 "initial_packed": self.initial_post_pack,
                                 "final_packed": self.post_pack},
                "required_claims": 3, "delivered_claim_ids": self.delivery_claims,
                "cache_payload_hydrations": self.cache_hydrations,
                "public_text": self.public_text, "trace": self.trace,
                "access_observations": self.exposures}

    def run(self) -> dict:
        fault = self.scenario["fault"]
        self.step("Request/scope", "Frontend -> Backend giả lập", "ALLOW",
                  "Session fixture xác định actor/course/scope. Không có role tự khai hoặc auth thật.",
                  actor=self.actor_id, scope=self.actor["scope"], question=self.fixtures["question"])
        self.step("Policy", "AI core giả lập", "ALLOW",
                  "Fixture là câu hỏi khái niệm, cho phép giải thích. Không chạy classifier hay kiểm thử graded-work policy.")
        self.cache_check()
        self.retrieved = [self.evidence(doc) for doc in self.docs.values()
                          if self.allowed(self.evidence(doc))]
        self.observe_exposure("retrieval", self.retrieved)
        self.pre_pack = len(self.covered_groups(self.retrieved))
        self.step("Retrieval", "AI core giả lập", "COMPLETE" if self.pre_pack == 2 else "INCOMPLETE",
                  f"Retriever stub trả {self.pre_pack}/2 nhóm evidence trong scope hiện tại; không đo ranking/search thật.",
                  document_ids=[e["doc_id"] for e in self.retrieved], groups=self.pre_pack)
        self.packet = deepcopy(self.retrieved)
        if fault.startswith("packing_"):
            for evidence in self.packet:
                if evidence["doc_id"] == "syn-queue":
                    evidence["end"] //= 2
                    evidence["text"] = evidence["text"][:evidence["end"]]
            self.fail("packing_loss")
        self.initial_post_pack = len(self.covered_groups(self.packet))
        self.step("Packing", "AI core giả lập", "COMPLETE" if self.initial_post_pack == 2 else "INCOMPLETE",
                  f"Context thực chứa {self.initial_post_pack}/2 nhóm đủ span; tên document còn trong packet không bù phần text đã cắt.",
                  span_lengths=[len(e["text"]) for e in self.packet], groups=self.initial_post_pack)
        if fault == "revoke_before_model":
            self.revoke("Sự kiện sau retrieval/packing")
        if self.initial_post_pack < 2 and self.disable != "packing":
            self.repairs += 1
            candidates = [self.evidence(doc) for doc in self.docs.values()
                          if self.allowed(self.evidence(doc))]
            if fault == "packing_unrecoverable":
                # Deterministic no-fit outcome within this fixture's context budget, not a timeout.
                candidates = [e for e in candidates if e["doc_id"] != "syn-queue"]
            self.observe_exposure("context_expansion", candidates)
            self.packet = candidates
            repaired = len(self.covered_groups(self.packet)) == 2
            self.step("Repair context", "AI core giả lập", "RECOVERED" if repaired else "PARTIAL",
                      "Thử lại đúng một lần có lọc quyền: " +
                      ("khôi phục đủ 2/2 nhóm." if repaired else "vẫn chỉ 1/2 nhóm; không bù từ model memory."),
                      attempts=self.repairs, max_attempts=1)
        self.post_pack = len(self.covered_groups(self.packet))
        access_valid = all(self.allowed(e) and self.current(e) for e in self.packet)
        if not access_valid and self.disable != "pre_model":
            self.fail("policy_or_access")
            self.outcome = "access_denied"
            self.public_text = "Quyền hoặc trạng thái tài liệu đã thay đổi. Vui lòng gửi lại yêu cầu."
            self.step("Kiểm tra trước model", "Backend + AI core giả lập", "BLOCK",
                      "Nguồn trong packet không còn hợp lệ; hủy request, không đưa packet vào generator stub.",
                      generator_stub_calls=0, content_emitted=False)
            self.step("Generate/deliver/viewer", "Pipeline giả lập", "SKIP",
                      "Không tạo answer/citation; chỉ trả thông báo chung, không tên nguồn riêng tư.")
            return self.finish()
        self.step("Kiểm tra trước model", "Backend + AI core giả lập", "ALLOW" if access_valid else "UNSAFE",
                  "Kiểm tra quyền và revision hiện tại ngay trước model input; chạy tuần tự, chưa kiểm thử race thật.")
        groups = self.covered_groups(self.packet)
        selected = [claim for claim in self.fixtures["required_claims"]
                    if set(claim["all_of_groups"]) <= groups]
        if self.disable == "packing":
            selected = deepcopy(self.fixtures["required_claims"])
            if len(groups) < 2:
                self.violate("incomplete_packet_presented_as_full")
        self.generator_stub_calls += 1
        self.observe_exposure("model_input", self.packet)
        links = {}
        for claim in selected:
            links[claim["id"]] = [deepcopy(e) for e in self.packet
                                  if e["group"] in claim["all_of_groups"]]
        if fault == "citation_wrong_version":
            for citations in links.values():
                for citation in citations:
                    if citation["doc_id"] == "syn-queue":
                        citation["revision"] = 999
        self.step("Generate stub", "AI core giả lập", "BUFFERED",
                  f"Tạo {len(selected)}/3 claim từ template cố định; câu trả lời đang giữ trong buffer, chưa gửi cho user.",
                  generator_stub_calls=self.generator_stub_calls, actual_llm_calls=0, buffered_claims=[c["id"] for c in selected])
        # Validate citations against the pinned packet, not live permissions (checked at delivery).
        citations_valid = all(
            set(claim["all_of_groups"]) <= {
                citation["group"] for citation in links[claim["id"]]
                if citation in self.packet
            }
            for claim in selected
        )
        if not citations_valid and self.disable != "citation":
            self.fail("citation_support")
            self.outcome = "citation_invalid"
            self.public_text = "Chưa xác minh được trích dẫn cho câu trả lời này. Vui lòng thử lại."
            self.step("Verify citation", "AI core giả lập", "BLOCK",
                      "Revision citation không khớp evidence packet; loại toàn bộ bản nháp, không phát citation sai.",
                      valid=False, content_emitted=False)
            self.step("Delivery/viewer", "Backend giả lập", "SKIP", "Chỉ gửi thông báo lỗi kiểm chứng; không có citation để mở.")
            return self.finish()
        self.step("Verify citation", "AI core giả lập", "ALLOW" if citations_valid else "UNSAFE",
                  "Liên kết claim-citation khớp groups và packet; chỉ kiểm tra cấu trúc fixture, không đo semantic entailment.",
                  valid=citations_valid)
        if fault == "revoke_before_delivery":
            self.revoke("Sự kiện sau generation")
        delivery_valid = all(self.allowed(e) and self.current(e) for e in self.packet)
        if not delivery_valid and self.disable != "delivery":
            self.fail("policy_or_access")
            self.outcome = "access_denied"
            self.public_text = "Quyền hoặc trạng thái tài liệu đã thay đổi. Vui lòng gửi lại yêu cầu."
            self.step("Delivery", "Backend giả lập", "BLOCK",
                      "Chốt quyền/version cuối phát hiện thay đổi; hủy buffer, không gửi answer/citation hoặc ghi response cache.",
                      content_emitted=False, response_cache_written=False)
            self.step("Viewer", "Frontend giả lập", "SKIP", "Không có citation được phát ra để mở.")
            return self.finish()
        self.delivery_claims = [c["id"] for c in selected]
        self.outcome = "full_answer" if len(selected) == 3 else "partial_answer"
        self.public_text = " ".join(c["text"] for c in selected)
        if self.outcome == "partial_answer":
            self.public_text += " Chưa đủ bằng chứng được phép sử dụng để giải thích queue và hoàn tất so sánh."
        self.observe_exposure("delivery", self.packet)
        if not citations_valid:
            self.violate("invalid_citation_emitted")
        self.step("Delivery", "Backend -> Frontend giả lập", "FULL" if len(selected) == 3 else "PARTIAL",
                  f"Gửi {len(selected)}/3 claim và citation đã kiểm tra; " +
                  ("đủ câu hỏi trong fixture." if len(selected) == 3 else "ghi rõ phần thiếu, không tính hoàn thành câu hỏi."),
                  public_text=self.public_text, content_emitted=True, response_cache_written=False)
        if fault == "viewer_old_version":
            self.replace_version("Sự kiện sau delivery")
        elif fault == "viewer_revoked":
            self.revoke("Sự kiện sau delivery")
        self.viewer = "opened"
        unique = {e["doc_id"]: e for values in links.values() for e in values}
        for evidence in unique.values():
            if not self.allowed(evidence) and self.disable != "viewer_auth":
                self.fail("policy_or_access")
                self.viewer = "access_denied"
                self.step("Mở nguồn", "Backend/source viewer giả lập", "BLOCK",
                          "Không thể truy cập nguồn này; không phát title/text/asset mới của nguồn bị chặn.",
                          requested_doc=evidence["doc_id"], source_content_emitted=False)
            elif not self.current(evidence) and self.disable != "viewer_version":
                self.fail("locator_or_viewer")
                self.viewer = "version_unavailable"
                self.step("Mở nguồn", "Backend/source viewer giả lập", "BLOCK",
                          "Bản được trích dẫn không còn khả dụng; không tự mở bản hiện hành hoặc dùng offset cũ.",
                          requested_doc=evidence["doc_id"], requested_revision=evidence["revision"],
                          source_content_emitted=False)
            else:
                shown = evidence
                if not self.current(evidence):
                    shown = self.evidence(self.docs[evidence["doc_id"]])
                    self.violate("silent_viewer_version_substitution")
                self.observe_exposure("viewer", [shown])
                self.step("Mở nguồn", "Backend/source viewer giả lập", "OPEN",
                          "Mở đúng đoạn nguồn giả lập theo revision/hash/span; chưa có UI highlight thật.",
                          doc_id=shown["doc_id"], revision=shown["revision"],
                          start=shown["start"], end=shown["end"], text=shown["text"])
        return self.finish()


def main() -> int:
    fixture_bytes = FIXTURES.read_bytes()
    fixtures = json.loads(fixture_bytes)
    runs = [Simulation(fixtures, scenario).run() for scenario in fixtures["scenarios"]]
    scenarios = {scenario["id"]: scenario for scenario in fixtures["scenarios"]}
    mutations = []
    for mutation in fixtures["mutations"]:
        run = Simulation(fixtures, scenarios[mutation["scenario"]], mutation["disable"]).run()
        detected = mutation["must_detect"] in run["violations"]
        mutations.append({**mutation, "detected": detected, "run": run})
    # Separate small probes of the span arithmetic used to detect packing loss.
    probe = Simulation(fixtures, fixtures["scenarios"][0])
    whole = probe.evidence(probe.docs["syn-stack"])
    left, right = deepcopy(whole), deepcopy(whole)
    midpoint = whole["end"] // 2
    left.update(end=midpoint, text=whole["text"][:midpoint])
    right.update(start=midpoint, text=whole["text"][midpoint:])
    gap = deepcopy(right)
    gap.update(start=midpoint + 1, text=whole["text"][midpoint + 1:])
    wrong_hash, wrong_revision, wrong_text = deepcopy(whole), deepcopy(whole), deepcopy(whole)
    wrong_hash["sha256"] = "invalid"
    wrong_revision["revision"] = 99
    wrong_text["text"] = "fabricated"
    probe_inputs = [
        ("adjacent_split_spans_union", [left, right], 1),
        ("one_character_gap", [left, gap], 0),
        ("wrong_source_hash", [wrong_hash], 0),
        ("wrong_revision", [wrong_revision], 0),
        ("payload_text_does_not_match_span", [wrong_text], 0),
        ("duplicate_span_not_double_counted", [whole, whole], 1),
        ("partial_span_not_complete_evidence", [left], 0),
    ]
    span_probes = [{"id": name, "expected_groups": expected,
                    "actual_groups": len(probe.covered_groups(evidence)),
                    "passed": len(probe.covered_groups(evidence)) == expected}
                   for name, evidence, expected in probe_inputs]
    failures = [run["id"] for run in runs if not run["conformant_to_fixture"]]
    failures += [mutation["id"] for mutation in mutations if not mutation["detected"]]
    failures += [check["id"] for check in span_probes if not check["passed"]]
    result = {
        "simulation_id": fixtures["simulation_id"], "status": "passed" if not failures else "failed",
        "fixtures_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Sequential synthetic policy-state simulation only; no LLM/retriever/RBAC/cache/UI runtime is tested.",
        "counts": {"baseline_scenarios": len(runs),
                   "conformant_baselines": sum(run["conformant_to_fixture"] for run in runs),
                   "baseline_trace_steps": sum(len(run["trace"]) for run in runs),
                   "baseline_access_observations": sum(len(run["access_observations"]) for run in runs),
                   "baseline_unauthorized_observations": sum(not action["authorized_at_action"] for run in runs for action in run["access_observations"]),
                   "mutations": len(mutations), "mutations_detected": sum(m["detected"] for m in mutations),
                   "span_probes": len(span_probes), "span_probes_passed": sum(p["passed"] for p in span_probes),
                   "actual_llm_calls": 0, "network_calls": 0},
        "policy_assumptions": fixtures["policy_assumptions"],
        "baseline_runs": runs, "mutation_runs": mutations, "span_probes": span_probes, "failures": failures,
        "limitations": [
            "Expectations and simulator are authored together; mutation checks do not make an independent audit.",
            "No concurrency, streaming bytes, distributed invalidation, browser cache, real auth or storage purge is simulated.",
            "The fixed stub and synthetic oracle groups cannot validate model faithfulness or automatic missing-claim detection.",
            "Partial answer after one repair is a proposed UX policy, not stakeholder approval or full-answer success.",
            "Viewer failures after delivery do not undo previously authorized disclosure; not all journey outcomes are successful.",
            "No public/raw corpus is promoted to approved serving; no original source or silver labels are modified."
        ]
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
