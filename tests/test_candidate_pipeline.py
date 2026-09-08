"""
Unit Tests for Candidate Filtering, Semantic Similarity, and Relationship Engine
================================================================================
Verifies:
1. Strict financial qualifier preservation ('total', 'other', 'net', 'gross', 'operating').
2. Mutually exclusive qualifier rejection ('Other expenses' != 'Total expenses').
3. Semantic equivalence for valid synonyms ('Revenue from operations' == 'Operating revenue').
4. Candidate generation pipeline efficiency and pruning.
5. Rejection of false reconciliations caused merely by differing time periods.
"""

import unittest
import time
from models.schemas import Fact, Evidence, RelationshipType, ExtractedFactItem
from services.normalizer import Normalizer
from services.relationship_engine import RelationshipEngine


class TestStrictCandidateFiltering(unittest.TestCase):
    """Test suite for strict candidate filtering and qualifier compatibility."""

    def setUp(self):
        self.engine = RelationshipEngine()

    def test_pass_identical_revenue(self):
        """PASS: 'Revenue' vs 'Revenue' must be recognized as compatible."""
        subj_a = "Revenue"
        subj_b = "Revenue"
        self.assertTrue(
            Normalizer.are_subjects_compatible(subj_a, subj_b),
            "Identical metrics must be compatible."
        )

        fa = Fact(
            id=1, document_id=1, document_name="doc_a.pdf", page_number=1,
            subject="Revenue", predicate="was", object_value="1000",
            unit="INR_CRORE", time_period="FY24",
            evidence=Evidence(document_name="doc_a.pdf", page_number=1, quote="Revenue was 1000 Cr in FY24.")
        )
        fb = Fact(
            id=2, document_id=2, document_name="doc_b.pdf", page_number=5,
            subject="Revenue", predicate="reported", object_value="1000",
            unit="INR_CRORE", time_period="FY24",
            evidence=Evidence(document_name="doc_b.pdf", page_number=5, quote="Reported revenue of 1000 Cr in FY24.")
        )
        rel = self.engine.compare_facts(fa, fb)
        self.assertIsNotNone(rel, "Identical revenue facts must produce a relationship.")
        self.assertEqual(rel.relationship_type, RelationshipType.CORROBORATES)

    def test_pass_revenue_from_operations_synonym(self):
        """PASS: 'Revenue from operations' vs recognized synonyms ('Operating revenue', 'Revenue from contracts with customers')."""
        subj_a = "Revenue from operations"
        subj_b = "Operating revenue"
        subj_c = "Revenue from contracts with customers"

        self.assertTrue(
            Normalizer.are_subjects_compatible(subj_a, subj_b),
            "'Revenue from operations' and 'Operating revenue' must be recognized as equivalent metrics."
        )
        self.assertTrue(
            Normalizer.are_subjects_compatible(subj_a, subj_c),
            "'Revenue from operations' and 'Revenue from contracts with customers' must be recognized as equivalent metrics."
        )

        fa = Fact(
            id=10, document_id=1, document_name="doc_a.pdf", page_number=2,
            subject="Revenue from operations", predicate="was", object_value="8,825",
            unit="₹ Cr", time_period="FY24",
            evidence=Evidence(document_name="doc_a.pdf", page_number=2, quote="Revenue from operations was 8,825 Cr.")
        )
        fb = Fact(
            id=11, document_id=2, document_name="doc_b.pdf", page_number=4,
            subject="Operating revenue", predicate="stood at", object_value="8,825",
            unit="₹ Cr", time_period="FY24",
            evidence=Evidence(document_name="doc_b.pdf", page_number=4, quote="Operating revenue stood at 8,825 Cr.")
        )
        rel = self.engine.compare_facts(fa, fb)
        self.assertIsNotNone(rel, "Equivalent revenue metrics must produce a relationship.")
        self.assertEqual(rel.relationship_type, RelationshipType.CORROBORATES)

    def test_reject_other_expenses_vs_total_expenses(self):
        """REJECT: 'Other expenses' vs 'Total expenses' must be rejected as NO_RELATION."""
        subj_a = "Other expenses"
        subj_b = "Total expenses"

        # 1. Qualifier compatibility must fail
        self.assertFalse(
            Normalizer.are_qualifiers_compatible(subj_a, subj_b),
            "Qualifiers 'other' and 'total' must be mutually exclusive."
        )
        # 2. Subject compatibility must fail
        self.assertFalse(
            Normalizer.are_subjects_compatible(subj_a, subj_b),
            "'Other expenses' and 'Total expenses' are distinct metrics and must not be compatible."
        )
        # 3. Semantic similarity must be zero due to qualifier conflict
        self.assertEqual(
            Normalizer.compute_metric_similarity(subj_a, subj_b),
            0.0,
            "Conflicting qualifiers must override similarity to 0.0."
        )

        # 4. Engine must NOT establish any relationship, even with different time periods!
        fa = Fact(
            id=101, document_id=1, document_name="prospectus_2022.pdf", page_number=240,
            subject="Other expenses", predicate="was", object_value="1,963.74",
            unit="₹ million", time_period="Year ended March 31, 2019",
            evidence=Evidence(document_name="prospectus_2022.pdf", page_number=240, quote="Other expenses was 1,963.74 million.")
        )
        fb = Fact(
            id=102, document_id=2, document_name="earnings_q4_fy24.pdf", page_number=12,
            subject="Total expenses", predicate="was", object_value="8,825",
            unit="₹ Cr", time_period="FY24",
            evidence=Evidence(document_name="earnings_q4_fy24.pdf", page_number=12, quote="Total expenses was 8,825 Cr.")
        )
        rel = self.engine.compare_facts(fa, fb)
        self.assertIsNone(
            rel,
            "CRITICAL: 'Other expenses' (FY19) and 'Total expenses' (FY24) must NEVER produce a RECONCILES relationship!"
        )

    def test_reject_net_profit_vs_gross_profit(self):
        """REJECT: 'Net profit' vs 'Gross profit' must be rejected as NO_RELATION."""
        subj_a = "Net profit"
        subj_b = "Gross profit"

        self.assertFalse(
            Normalizer.are_qualifiers_compatible(subj_a, subj_b),
            "'net' and 'gross' qualifiers must be mutually exclusive."
        )
        self.assertFalse(
            Normalizer.are_subjects_compatible(subj_a, subj_b),
            "'Net profit' and 'Gross profit' must not be compatible."
        )

        fa = Fact(
            id=201, document_id=1, document_name="doc_a.pdf", page_number=10,
            subject="Net profit", predicate="was", object_value="500",
            unit="INR_CRORE", time_period="FY24",
            evidence=Evidence(document_name="doc_a.pdf", page_number=10, quote="Net profit was 500 Cr.")
        )
        fb = Fact(
            id=202, document_id=2, document_name="doc_b.pdf", page_number=15,
            subject="Gross profit", predicate="was", object_value="1500",
            unit="INR_CRORE", time_period="FY24",
            evidence=Evidence(document_name="doc_b.pdf", page_number=15, quote="Gross profit was 1500 Cr.")
        )
        rel = self.engine.compare_facts(fa, fb)
        self.assertIsNone(rel, "Net profit and Gross profit must have NO_RELATION.")

    def test_reject_employee_count_vs_revenue(self):
        """REJECT: 'Employee count' vs 'Revenue' must be rejected as NO_RELATION."""
        subj_a = "Employee count"
        subj_b = "Revenue"

        self.assertFalse(
            Normalizer.are_subjects_compatible(subj_a, subj_b),
            "'Employee count' and 'Revenue' must not be compatible."
        )

        fa = Fact(
            id=301, document_id=1, document_name="doc_a.pdf", page_number=5,
            subject="Employee count", predicate="stood at", object_value="25,000",
            unit="employees", time_period="FY24",
            evidence=Evidence(document_name="doc_a.pdf", page_number=5, quote="Employee count stood at 25,000.")
        )
        fb = Fact(
            id=302, document_id=2, document_name="doc_b.pdf", page_number=8,
            subject="Revenue", predicate="stood at", object_value="8,825",
            unit="₹ Cr", time_period="FY24",
            evidence=Evidence(document_name="doc_b.pdf", page_number=8, quote="Revenue stood at 8,825 Cr.")
        )
        rel = self.engine.compare_facts(fa, fb)
        self.assertIsNone(rel, "Employee count and Revenue must have NO_RELATION.")

    def test_reject_operating_profit_vs_net_profit(self):
        """REJECT: 'Operating profit' vs 'Net profit' must be rejected."""
        self.assertFalse(Normalizer.are_qualifiers_compatible("Operating profit", "Net profit"))
        self.assertFalse(Normalizer.are_subjects_compatible("Operating profit", "Net profit"))

    def test_unit_scaling_equivalence(self):
        """PASS: 100 Crore INR == 1,000 Million INR (Unit Scaling within 1.5% tolerance)."""
        equiv = Normalizer.are_numeric_values_equivalent(
            val_a=100.0, unit_a="₹ Cr",
            val_b=1000.0, unit_b="₹ million"
        )
        self.assertTrue(equiv, "100 Cr and 1,000 Million INR must be equivalent.")

        fa = Fact(
            id=401, document_id=1, document_name="doc_a.pdf", page_number=1,
            subject="Total income", predicate="was", object_value="100",
            unit="₹ Cr", time_period="FY24",
            evidence=Evidence(document_name="doc_a.pdf", page_number=1, quote="Total income was 100 Cr.")
        )
        fb = Fact(
            id=402, document_id=2, document_name="doc_b.pdf", page_number=3,
            subject="Total income", predicate="was", object_value="1000",
            unit="₹ million", time_period="FY24",
            evidence=Evidence(document_name="doc_b.pdf", page_number=3, quote="Total income was 1000 million.")
        )
        rel = self.engine.compare_facts(fa, fb)
        self.assertIsNotNone(rel)
        self.assertEqual(rel.relationship_type, RelationshipType.CORROBORATES)

    def test_candidate_generation_prunes_brute_force(self):
        """Verify candidate generation uses canonical buckets and avoids brute force."""
        # Create 100 facts across 10 distinct metrics (5 facts per metric in doc A, 5 in doc B)
        facts = []
        metrics = [
            "Revenue from operations", "Operating expenses", "Other expenses",
            "Total expenses", "Net profit", "Gross profit", "EBITDA",
            "Total assets", "Total liabilities", "Headcount"
        ]
        fid = 1
        for doc_name in ["Doc_A.pdf", "Doc_B.pdf"]:
            for metric in metrics:
                for idx in range(3):
                    facts.append(Fact(
                        id=fid,
                        document_id=1 if doc_name == "Doc_A.pdf" else 2,
                        document_name=doc_name,
                        page_number=1,
                        subject=metric,
                        predicate="was",
                        object_value=str(100 * idx),
                        unit="INR_CRORE",
                        time_period="FY24",
                        evidence=Evidence(document_name=doc_name, page_number=1, quote=f"{metric} quote")
                    ))
                    fid += 1

        total_facts = len(facts)
        total_possible_pairs = (total_facts * (total_facts - 1)) // 2  # 60 * 59 // 2 = 1770

        t0 = time.time()
        candidates = Normalizer.find_candidate_pairs(facts, max_candidates=100, prefer_cross_document=True)
        elapsed = time.time() - t0

        self.assertLess(elapsed, 0.5, "Candidate generation must complete in under 500ms.")
        self.assertLess(len(candidates), total_possible_pairs, "Candidates must be pruned significantly.")

        # Ensure that no candidate pair crosses "Other expenses" and "Total expenses"
        for fa, fb in candidates:
            quals_a = Normalizer.extract_qualifiers(fa.norm_subject)
            quals_b = Normalizer.extract_qualifiers(fb.norm_subject)
            if "other" in quals_a:
                self.assertNotIn("total", quals_b, f"Candidate pair crossed 'other' and 'total': {fa.norm_subject} vs {fb.norm_subject}")
            if "total" in quals_a:
                self.assertNotIn("other", quals_b, f"Candidate pair crossed 'total' and 'other': {fa.norm_subject} vs {fb.norm_subject}")

    def test_batch_provenance_preservation(self):
        """Verify ExtractedFactItem preserves exact page_number in to_fact."""
        item = ExtractedFactItem(
            subject="Revenue",
            predicate="was",
            value="100 Cr",
            fact_type="NUMERICAL",
            unit="INR_CRORE",
            time_context="FY24",
            evidence_quote="Revenue was 100 Cr.",
            page_number=4
        )
        # When to_fact is called with default fallback page 1, the explicit item.page_number 4 must be preserved
        fact = item.to_fact(document_name="test.pdf", page_number=1, document_id=99)
        self.assertEqual(fact.page_number, 4)
        self.assertEqual(fact.evidence.page_number, 4)
        self.assertEqual(fact.document_id, 99)


if __name__ == "__main__":
    unittest.main()
