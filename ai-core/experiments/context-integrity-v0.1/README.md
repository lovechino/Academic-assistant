# Context integrity repair experiment v0.1

Offline repair for review findings F-01/F-02, 2026-09-06. Reuses the R0 source event serializer; historical R2/R3/R4 algorithms, configs and result artifacts are preserved for reproducibility. Do not route new model-input work through R2's `normalize_legacy()` or treat R4 resolver-only coverage as final packet coverage.

Run from repository root with Python 3.11+:

```powershell
py -3.11 -B -m unittest discover -s ai-core/experiments/context-integrity-v0.1 -p "test_*.py" -v
```

The tests use synthetic strings/units in memory, print results, and do not read pilot datasets, write results, invoke historical audit `main()` functions, install packages, call models/network or create an index.

## Supported repair

- Single explicit HTML root with no attributes: R0 typed tape, escaped structure, source hash and alignment survive projection. Sub/sup, case, negation, operators, code line breaks and simple table cells/blanks remain distinct. Structure markers are not citable source text.
- Unknown layout/attributes, images, MathML, spanning tables and malformed/implicit roots block the entire unit in this small profile. This is not a replacement PDF/OCR/parser or production HTML sanitizer.
- Required dependency closures are packed atomically before optional context, with hop/unit/budget limits and a post-pack closure assertion. Omitting an anchor cannot produce standalone optional expansion.
- Internal item map remains outside the allowlisted model projection; its exact serialized input hash and cost are recorded. IDs in text remain untrusted source text.

## Limits and measurement

`Unit.eligible`, scope and version are preselected offline fixture attributes, not authenticated identity or policy enforcement. Dependencies are supplied explicitly in synthetic fixtures to test packing; automatic dependency detection and semantic truth are not tested. Unknown dependency assessment blocks the unit. This profile limits a closure to one source scope/version; authorized cross-version conflict hydration remains a future contract test.

Tests measure full serialized input in codepoints (`synthetic-codepoint-NOT-token`), and the legacy counterexample uses whitespace counts. Neither is a generator tokenizer or a BGE-M3 benchmark. Callers of a later experiment must supply the actual tokenizer/accounting profile, reserve model output/history/tools/images and measure the complete payload. No 512/2048 budget or new retrieval winner is selected here.

Every result retains `answerability=not_assessed` and `serving_authorized=false`. Full closure is a structural prerequisite, not semantic completeness. All-omitted packets have null closure rate and zero anchor retention, not a success score.

Review findings, contract cases and measurement corrections: [repair registry](../../../docs/evaluation/29-review-regression-and-metric-clarifications-v0.1.md).
