"""
Fact Normalizer Service (Placeholder)
====================================
This module will be responsible for normalizing extracted facts across documents
before feeding them to the relationship engine.

Why Normalization Matters:
--------------------------
1. Entity Resolution:
   - "Acme Corp", "Acme Corporation", and "Acme Inc." refer to the same entity.
2. Temporal Normalization:
   - "FY23", "FY 2023", and "Jan 1, 2023 - Dec 31, 2023" map to the same period.
3. Metric & Currency Normalization:
   - "$10.5M", "10,500,000 USD", and "10.5 million dollars" map to value=10500000, unit='USD'.
4. Candidate Pairing:
   - Clusters facts by topic/subject so the LLM relationship engine only compares
     relevant pairs rather than computing an expensive O(N^2) cartesian product.

NOTE: Placeholder implementation for MVP foundation.
"""

from typing import List, Tuple
from models.schemas import Fact


class Normalizer:
    """Normalizes facts and identifies candidate pairs for comparison."""

    @staticmethod
    def normalize_fact(fact: Fact) -> Fact:
        """
        Normalize subject, metric units, and temporal fields of a single fact.

        Args:
            fact: Raw extracted Fact instance.

        Returns:
            Fact: Normalized Fact instance.
        """
        # Placeholder: Return fact as-is until normalization logic is added.
        return fact

    @staticmethod
    def find_candidate_pairs(facts: List[Fact]) -> List[Tuple[Fact, Fact]]:
        """
        Identify pairs of facts across different documents that discuss similar
        entities or topics and are candidates for relationship evaluation.

        Args:
            facts: List of all extracted facts across documents.

        Returns:
            List of (Fact, Fact) candidate pairs from distinct documents.
        """
        candidate_pairs: List[Tuple[Fact, Fact]] = []

        # Placeholder heuristic: pair facts from different documents
        # Future enhancement: use semantic similarity embeddings or topic clustering
        for i, fact_a in enumerate(facts):
            for fact_b in facts[i + 1:]:
                # Only compare facts originating from different documents
                if fact_a.document_name != fact_b.document_name:
                    candidate_pairs.append((fact_a, fact_b))

        return candidate_pairs
