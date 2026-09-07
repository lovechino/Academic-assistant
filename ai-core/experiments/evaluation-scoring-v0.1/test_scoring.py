import unittest

from scoring import Ratio, false_refusal, gate_rate, hit_groups, ocr_error, packing_loss, retrieval


class ScoringTests(unittest.TestCase):
    def test_and_inside_or_outside(self):
        groups = {"comparison": [{"a", "b"}, {"c"}]}
        self.assertEqual(hit_groups(groups, {"a"}), set())
        self.assertEqual(hit_groups(groups, {"a", "b"}), {"comparison"})
        self.assertEqual(hit_groups(groups, {"c"}), {"comparison"})

    def test_no_vacuous_alternative(self):
        for groups in ({"g": []}, {"g": [set()]}, {"g": [{""}]}, {"": [{"a"}]}):
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                hit_groups(groups, set())

    def test_exact_locator_not_document_match(self):
        self.assertEqual(hit_groups({"g": [{"doc:v1:p2"}]}, {"doc:v2:p2", "doc"}), set())

    def test_macro_differs_from_micro(self):
        result = retrieval({"q1": {"a": [{"a"}]}, "q2": {"b": [{"b"}], "c": [{"c"}], "d": [{"d"}]}}, {"q1": {"a"}})
        self.assertEqual(result["macro"], .5)
        self.assertEqual(result["micro"].value, .25)
        self.assertEqual(result["all_evidence"].value, .5)

    def test_empty_qrels_na(self):
        result = retrieval({"u": {}}, {})
        self.assertIsNone(result["macro"])
        self.assertIsNone(result["micro"].value)
        self.assertEqual(result["na_query_ids"], ["u"])
        self.assertEqual(result["all_evidence"].denominator, 0)

    def test_missing_output_stays_in_denominator(self):
        result = retrieval({"q": {"g": [{"x"}]}}, {})
        self.assertEqual(result["micro"], Ratio(0, 1))

    def test_unexpected_query_rejected(self):
        with self.assertRaises(ValueError):
            retrieval({}, {"invented": set()})

    def test_duplicate_locators_do_not_double_count(self):
        result = retrieval({"q": {"g": [{"a"}, {"a"}]}}, {"q": {"a"}})
        self.assertEqual(result["micro"], Ratio(1, 1))

    def test_sim03_loss(self):
        groups = {"stack": [{"s"}], "queue": [{"q"}]}
        self.assertEqual(packing_loss(groups, {"s", "q"}, {"s"}), Ratio(1, 2))

    def test_loss_not_net_group_count(self):
        groups = {"a": [{"a"}], "b": [{"b"}]}
        self.assertEqual(packing_loss(groups, {"a"}, {"b"}), Ratio(1, 1))

    def test_no_prepack_hits_is_na(self):
        self.assertIsNone(packing_loss({"a": [{"a"}]}, set(), set()).value)

    def test_gap_all_gates_and_timeout(self):
        self.assertEqual(gate_rate([{"claims": True, "citation": True}, {"claims": True, "citation": False}, None]), Ratio(1, 3))

    def test_gate_values_are_strict(self):
        for row in ({}, {"claims": "false"}, {"claims": 1}, {"claims": None}):
            with self.subTest(row=row), self.assertRaises(ValueError):
                gate_rate([row])

    def test_false_refusal_separate_operational_failure(self):
        self.assertEqual(false_refusal(["false_refusal", "operational_error", "appropriate_partial", "missing_output"]), Ratio(1, 4))
        with self.assertRaises(ValueError):
            false_refusal(["no_hit_means_out_of_scope"])

    def test_ratio_rejects_invalid_counts(self):
        for n, d in ((1, 0), (-1, 2), (True, 2), (1.0, 2)):
            with self.subTest(n=n, d=d), self.assertRaises(ValueError):
                Ratio(n, d)

    def test_ocr_nfc_preserves_accents(self):
        self.assertEqual(ocr_error("á", "a\u0301")["edits"], 0)
        self.assertEqual(ocr_error("á", "a")["edits"], 1)

    def test_ocr_insertions_not_clamped(self):
        self.assertEqual(ocr_error("a", "abcd")["value"], 3)

    def test_ocr_empty_reference_and_missing_output(self):
        self.assertIsNone(ocr_error("", "abc")["value"])
        self.assertEqual(ocr_error("", "abc")["edits"], 3)
        self.assertEqual(ocr_error("abc", "")["value"], 1)

    def test_ocr_whitespace_and_symbols(self):
        self.assertEqual(ocr_error("hai  từ", "hai từ", unit="whitespace_token")["value"], 0)
        self.assertEqual(ocr_error("≤", "£")["edits"], 1)
        self.assertEqual(ocr_error("-1", "1")["edits"], 1)


if __name__ == "__main__":
    unittest.main()
