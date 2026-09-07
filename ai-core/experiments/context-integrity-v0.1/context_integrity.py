"""Bounded offline fixes for representation and dependency packing.

Stdlib only. No datasets, models, network, index writes or product authorization.
Historical serializers/runners remain unchanged; this profile reuses the R0 event
serializer, not the lossy legacy text projection used by R2-R4.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
PROFILE = "context-integrity-v0.1"


@lru_cache(maxsize=1)
def source_helpers():
    modules = []
    for name, relative in (
        ("integrity_source_tree", "html-structure/build_representation.py"),
        ("integrity_source_events", "source-serialization/serialize_source.py"),
    ):
        spec = importlib.util.spec_from_file_location(name, ROOT / "ai-core/experiments" / relative)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules.append(module)
    return tuple(modules)


def project_source(source: str, source_id: str) -> dict:
    """Project one complete explicit HTML root in the supported text subset.

    Preserves the source tape, source hash and R0 alignment. Does not interpret
    browser layout. Attributes, images, MathML and implicit/malformed structures
    fail closed in this profile; no claim that this is a general HTML/PDF parser.
    Output is inert text, never HTML for a browser or a system instruction.
    """
    if not source_id or not source.strip():
        raise ValueError("nonempty_source_and_identity_required")
    tree_module, serializer = source_helpers()
    tree = tree_module.SourceTree(source, serializer.digest(source)).finish()
    roots = [node for node in tree.nodes if node["parent"] is None]
    reasons = []
    if len(roots) != 1 or roots[0]["source_span"] != [0, len(source)]:
        reasons.append("requires_one_complete_explicit_root")
    if tree.issues:
        reasons.append("source_tree_has_issues")
    for node in tree.nodes:
        if node["attributes"]:
            reasons.append("attributes_require_layout_or_span_review")
        if node["tag"] in {"img", "math", "svg"}:
            reasons.append("required_modality_unsupported")
    base = {"profile": PROFILE, "source_id": source_id,
            "source_sha256": serializer.digest(source), "source_text": source,
            "serving_authorized": False, "answerability": "not_assessed"}
    if reasons:
        return dict(base, status="blocked", reasons=sorted(set(reasons)),
                    structured_text="", alignment=[])
    root = roots[0]
    rep = {"source": {"document_id": source_id}, "nodes": tree.nodes,
           "source_tokens": tree.tokens, "text_runs": tree.runs, "tables": [], "images": []}
    ref = {"document_id": source_id, "node_id": root["id"], "tag": root["tag"],
           "raw_html_span": root["source_span"], "raw_fragment_sha256": serializer.digest(source)}
    unit = serializer.serialize_unit(source, rep, ref)
    if unit["status"] != "serialized":
        return dict(base, status="blocked", reasons=unit["blocking_reasons"],
                    structured_text="", alignment=[])
    return dict(base, status="supported_subset_serialized", reasons=[],
                structured_text=unit["review_projection"]["text"],
                alignment=unit["review_projection"]["alignment"], events=unit["events"])


@dataclass(frozen=True)
class Unit:
    id: str
    text: str
    scope: str
    version: str
    order: int
    required: tuple[str, ...] = ()
    dependencies_assessed: bool = False
    eligible: bool = True  # Offline input availability, NEVER a PDP decision.


def model_projection(ids: list[str], units: dict[str, Unit], question: str) -> dict:
    """Explicit allowlist; internal IDs/scope/version are kept out of model text."""
    return {"question": question, "evidence": [
        {"item_id": f"e{index}", "content": units[unit_id].text,
         "format": "structured_source_markup", "trust": "untrusted_content"}
        for index, unit_id in enumerate(ids, 1)
    ]}


def serialize_payload(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def pack_required(ranking: list[str], units: dict[str, Unit], *, budget: int,
                  measure: Callable[[str], int], accounting_profile: str,
                  question: str = "", max_hops: int = 8, max_units: int = 64,
                  optional: dict[str, tuple[str, ...]] | None = None) -> dict:
    """Atomic required closures, then optional closures, on preselected mock units.

    Each closure is same-scope/same-version in this diagnostic. Cross-version
    conflicts, PDP enforcement and automatic dependency discovery are NOT tested.
    The caller supplies a measurement of the full serialized model projection;
    this is an input budget AFTER reserving model output and other overhead.
    """
    if budget < 0 or max_hops < 0 or max_units < 1 or not accounting_profile:
        raise ValueError("invalid_budget_or_profile")
    if any(key != unit.id for key, unit in units.items()):
        raise ValueError("unit_identity_mismatch")
    retained, accepted, trace = [], [], []

    def cost(ids):
        value = measure(serialize_payload(model_projection(ids, units, question)))
        if type(value) is not int or value < 0:
            raise ValueError("measurement_must_be_nonnegative_integer")
        return value

    if cost([]) > budget:
        raise ValueError("base_model_input_exceeds_budget")

    def closure(root_id):
        if root_id not in units:
            raise ValueError("missing_unit")
        root, visiting, completed = units[root_id], set(), set()

        def visit(unit_id, depth):
            if depth > max_hops:
                raise ValueError("dependency_hop_limit")
            if unit_id in visiting:
                raise ValueError("dependency_cycle")
            if unit_id in completed:
                return
            unit = units.get(unit_id)
            if unit is None or not unit.eligible or not unit.text.strip():
                raise ValueError("dependency_unavailable")
            if (unit.scope, unit.version) != (root.scope, root.version):
                raise ValueError("dependency_scope_or_version_mismatch")
            if not unit.dependencies_assessed:
                raise ValueError("dependencies_not_assessed")
            if len(completed) + len(visiting) >= max_units:
                raise ValueError("dependency_unit_limit")
            visiting.add(unit_id)
            for child in unit.required:
                visit(child, depth + 1)
            visiting.remove(unit_id)
            completed.add(unit_id)

        visit(root_id, 0)
        return completed

    def proposed_order(extra):
        # Preserve source order inside each source scope/version; retain group
        # first-appearance order across independently ranked source documents.
        merged = list(dict.fromkeys(retained + sorted(extra, key=lambda key: (units[key].order, key))))
        groups = {}
        for key in merged:
            groups.setdefault((units[key].scope, units[key].version), []).append(key)
        return [key for group in groups.values()
                for key in sorted(group, key=lambda key: (units[key].order, key))]

    def attempt(root_id, kind, parent=None):
        nonlocal retained
        try:
            extra = closure(root_id)
            if parent is not None and ((units[root_id].scope, units[root_id].version) !=
                                       (units[parent].scope, units[parent].version)):
                raise ValueError("optional_scope_or_version_mismatch")
            proposed = proposed_order(extra)
            if len(proposed) > max_units:
                raise ValueError("packet_unit_limit")
            if cost(proposed) > budget:
                raise ValueError("required_bundle_over_budget")
        except ValueError as exc:
            trace.append({"anchor": root_id, "kind": kind, "decision": "omitted",
                          "reason": str(exc), "parent": parent})
            return False
        retained = proposed
        trace.append({"anchor": root_id, "kind": kind, "decision": "retained", "parent": parent})
        return True

    for root_id in dict.fromkeys(ranking):
        if attempt(root_id, "required_bundle"):
            accepted.append(root_id)
    # No expansion for an omitted ranking root; optional context cannot evict
    # any accepted required closure, and is itself checked for dependencies.
    for root_id in accepted:
        for candidate in (optional or {}).get(root_id, ()):
            attempt(candidate, "optional_bundle", root_id)

    missing = {key: sorted(set(units[key].required) - set(retained)) for key in retained}
    if any(missing.values()):
        raise AssertionError("post_pack_required_closure_broken")
    payload = model_projection(retained, units, question)
    serialized = serialize_payload(payload)
    return {"profile": PROFILE, "model_input": payload,
            "model_input_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            "internal_item_map": {f"e{i}": key for i, key in enumerate(retained, 1)},
            "retained_ids": retained, "accepted_anchors": accepted, "trace": trace,
            "accounting_profile": accounting_profile, "input_usage": cost(retained),
            "input_budget": budget, "post_pack_required_missing": missing,
            "retained_anchor_closure_rate": 1.0 if accepted else None,
            "anchor_retention_rate": len(accepted) / len(set(ranking)) if ranking else None,
            "answerability": "not_assessed", "serving_authorized": False}
