# Evaluation scoring v0.1 — offline arithmetic only

Python 3.11+, standard library. No model calls, corpus loading, artifact writes, index or product orchestration. Implements toy calculations under supplied evaluation labels; it does not discover claims, semantic evidence, access rights or source-span coverage. Locators are opaque snapshot-bound strings supplied by a trusted evaluator fixture, not arbitrary document titles.

Specification: [WP-03 scorer draft](../../../docs/evaluation/32-scorer-specification-v0.1.md).

Run: `py -3.11 -B -m unittest discover -s ai-core/experiments/evaluation-scoring-v0.1 -p test_scoring.py -v`.

Tests cover AND/OR, unequal macro/micro, empty qrels, missing predictions, packing loss identities, strict boolean gates, false refusal vs timeout, and OCR edits (NFC with accents preserved). All inputs synthetic in memory; PASS proves arithmetic on these fixtures, not academic accuracy. Full registry/scorers, span matching, judge calibration and runtime integration remain separate work.
