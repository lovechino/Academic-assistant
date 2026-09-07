"""Bounded evaluator arithmetic, not product runtime or semantic adjudication."""
from __future__ import annotations

from dataclasses import dataclass
import unicodedata


@dataclass(frozen=True)
class Ratio:
    numerator: int
    denominator: int

    def __post_init__(self):
        if (type(self.numerator) is not int or type(self.denominator) is not int
                or not 0 <= self.numerator <= self.denominator):
            raise ValueError("Expected integer hit counts within denominator")

    @property
    def value(self):
        return self.numerator / self.denominator if self.denominator else None

    @property
    def status(self):
        return "measured" if self.denominator else "not_applicable"


def strings(values):
    if not isinstance(values, (set, frozenset)) or any(
            not isinstance(x, str) or not x.strip() for x in values):
        raise ValueError("Expected a set of nonempty opaque locator IDs")


def hit_groups(groups, observed):
    """groups: group ID -> list of alternative sets of required locators."""
    strings(observed)
    if not isinstance(groups, dict):
        raise ValueError("Expected group mapping")
    hits = set()
    for gid, alternatives in groups.items():
        if not isinstance(gid, str) or not gid.strip() or not isinstance(alternatives, list) or not alternatives:
            raise ValueError("Group requires identity and nonempty alternatives")
        for alternative in alternatives:
            strings(alternative)
            if not alternative:
                raise ValueError("Empty evidence alternative cannot pass vacuously")
        if any(a <= observed for a in alternatives):
            hits.add(gid)
    return hits


def retrieval(expected, observed):
    """All queries preselected; absent observations mean missing system output.

    Evaluator telemetry corruption must invalidate the run before this function.
    Empty qrels remain explicitly N/A, not excluded after prediction.
    """
    if not isinstance(expected, dict) or not isinstance(observed, dict) or set(observed) - set(expected):
        raise ValueError("Unexpected query universe")
    rows = {}
    for qid, groups in expected.items():
        if not isinstance(qid, str) or not qid.strip():
            raise ValueError("Invalid query ID")
        hits = hit_groups(groups, observed.get(qid, set()))
        rows[qid] = Ratio(len(hits), len(groups))
    eligible = [r for r in rows.values() if r.denominator]
    return {
        "queries": rows,
        "macro": sum(r.value for r in eligible) / len(eligible) if eligible else None,
        "micro": Ratio(sum(r.numerator for r in eligible), sum(r.denominator for r in eligible)),
        "all_evidence": Ratio(sum(r.numerator == r.denominator for r in eligible), len(eligible)),
        "na_query_ids": [qid for qid, r in rows.items() if not r.denominator],
    }


def packing_loss(groups, before, after):
    pre, post = hit_groups(groups, before), hit_groups(groups, after)
    return Ratio(len(pre - post), len(pre))


def gate_rate(decisions):
    """Conjunction of externally adjudicated applicable gates. None = timeout.

    Pending labels must not be encoded as None: resolve eligibility beforehand.
    This function does not itself validate the rubric or grant approval.
    """
    passes = 0
    for row in decisions:
        if row is None:
            continue
        if not isinstance(row, dict) or not row or any(type(v) is not bool for v in row.values()):
            raise ValueError("Need nonempty strict boolean gate decisions")
        passes += all(row.values())
    return Ratio(passes, len(decisions))


def false_refusal(outcomes):
    """One externally labelled outcome per eligible benign/Q case."""
    allowed = {"appropriate_answer", "appropriate_partial", "appropriate_clarify",
               "false_refusal", "operational_error", "missing_output", "other_failure"}
    if any(x not in allowed for x in outcomes):
        raise ValueError("Unknown disposition; no automatic semantic labelling")
    return Ratio(outcomes.count("false_refusal"), len(outcomes))


def edit_distance(reference, hypothesis):
    previous = list(range(len(hypothesis) + 1))
    for i, left in enumerate(reference, 1):
        current = [i]
        for j, right in enumerate(hypothesis, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j - 1] + (left != right)))
        previous = current
    return previous[-1]


def ocr_error(reference, hypothesis, *, unit="character"):
    if not isinstance(reference, str) or not isinstance(hypothesis, str) or unit not in {"character", "whitespace_token"}:
        raise ValueError("Invalid transcription/unit")
    reference, hypothesis = (unicodedata.normalize("NFC", s) for s in (reference, hypothesis))
    if unit == "whitespace_token":
        reference, hypothesis = reference.split(), hypothesis.split()
    edits = edit_distance(reference, hypothesis)
    return {"edits": edits, "reference_units": len(reference),
            "value": edits / len(reference) if reference else None,
            "status": "measured" if reference else "not_applicable"}
