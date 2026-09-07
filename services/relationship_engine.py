"""
Relationship Engine Service
===========================
Discovers, compares, and classifies cross-document fact relationships into:
1. CORROBORATES: Same factual claim affirmed across documents.
2. CONTRADICTS: Direct incompatibility under identical conditions/timeframe.
3. RECONCILES: Divergent values explained by contextual dimensions (time, scope, units).
4. NO_RELATION: Facts are not sufficiently related (not persisted).

Architecture:
- Deterministic rules are evaluated first for speed, consistency, and zero hallucination.
- Google Gemini LLM fallback is used ONLY when relationships are semantically nuanced
  or ambiguous.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Callable, Dict, Any
from dotenv import load_dotenv

from models.schemas import (
    Fact,
    FactRelationship,
    RelationshipType,
    LLMRelationshipEvaluation,
)
from services.normalizer import Normalizer, NormalizedFact, STOPWORDS, GENERIC_ENTITY_TOKENS

logger = logging.getLogger(__name__)

RELATIONSHIP_SYSTEM_INSTRUCTION = """
You are an expert Fact Relationship Reasoning Engine.
Your task is to analyze TWO extracted facts from different documents and classify their relationship.

CRITICAL INSTRUCTION ON METRIC IDENTITY:
Only compare two facts if their subjects represent the EXACT SAME entity or metric.
If Fact A and Fact B describe different metrics or categories (for example, 'Other expenses' vs 'Total expenses',
or 'Revenue' vs 'Operating revenue', or 'EBITDA' vs 'Adjusted EBITDA'), they have NO RELATION.
Never classify facts as RECONCILES merely because time periods differ if their subjects are different metrics!

RELATIONSHIP CLASSES:
1. CORROBORATES:
   Both facts express substantially the same claim, event, or metric (even if worded differently).
   Values are consistent and time/scope are compatible.
2. CONTRADICTS:
   Both facts describe the exact same subject and predicate under identical conditions and timeframe,
   but assert mutually exclusive or genuinely conflicting values.
   IMPORTANT: If differences in time period, measurement unit, or reporting scope explain the values,
   do NOT classify as CONTRADICTS.
3. RECONCILES:
   Both facts describe the EXACT SAME metric or subject, but have differing values explained by:
   - Different time periods (e.g., FY22 vs. FY24)
   - Different geographical or operational scopes (e.g., Standalone vs. Consolidated)
   - Different measurement units (e.g., Crore vs. Million, where scaled amounts explain the context)
   The explanation MUST state why both facts can coexist.
4. NO_RELATION:
   The facts discuss different topics or metrics (e.g. Other expenses != Total expenses).

RULES:
- Base reasoning ONLY on the facts and evidence quotes provided.
- Do NOT invent facts or extrapolate unstated context.
- Output valid JSON conforming strictly to the requested schema.
"""


class RelationshipEngine:
    """Classifies cross-document relationships using deterministic rules and Gemini LLM fallback."""

    CANDIDATE_MODELS = ["gemini-flash-lite-latest", "gemini-flash-latest"]

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize the Relationship Engine."""
        project_root = Path(__file__).parent.parent.resolve()
        load_dotenv(project_root / ".env")

        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = model_name or self.CANDIDATE_MODELS[0]
        self._client = None

        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as exc:
                logger.warning("Gemini client initialization error in RelationshipEngine: %s", type(exc).__name__)

    @property
    def is_llm_available(self) -> bool:
        """Returns True if the Gemini fallback client is ready."""
        return self._client is not None

    def _are_values_equivalent(self, na: NormalizedFact, nb: NormalizedFact) -> bool:
        """Determines if two normalized facts assert equivalent values, accounting for unit scaling."""
        # 1. Numeric equivalence with base conversion (e.g. ₹100 Cr == ₹1,000 Million)
        if na.numeric_value is not None and nb.numeric_value is not None:
            return Normalizer.are_numeric_values_equivalent(
                na.numeric_value, na.norm_unit,
                nb.numeric_value, nb.norm_unit
            )

        # 2. String value equivalence
        if na.norm_value_str and nb.norm_value_str:
            if na.norm_value_str == nb.norm_value_str:
                return True
            # Check containment for string descriptions (e.g. "resigned" and "resigned as director")
            if (len(na.norm_value_str) >= 4 and na.norm_value_str in nb.norm_value_str) or \
               (len(nb.norm_value_str) >= 4 and nb.norm_value_str in na.norm_value_str):
                return True

        return False

    def _evaluate_deterministic(
        self,
        na: NormalizedFact,
        nb: NormalizedFact
    ) -> Optional[Tuple[RelationshipType, float, str, Optional[str]]]:
        """
        Evaluate relationship deterministically.
        Returns: (relationship_type, confidence, reasoning, reconciliation_context) or None if ambiguous.
        """
        # ----------------------------------------------------------------------
        # STEP 1: STRICT SUBJECT MATCHING FIRST
        # Only compare facts if normalized subjects represent the exact same metric/entity.
        # Reject immediately if subjects differ (e.g. Other expenses != Total expenses).
        # ----------------------------------------------------------------------
        if not Normalizer.are_subjects_compatible(na.canonical_subject, nb.canonical_subject):
            return None

        # ----------------------------------------------------------------------
        # STEP 2: PREDICATE COMPATIBILITY
        # Static reporting predicates must not match directional changes without reconciliation.
        # ----------------------------------------------------------------------
        if not Normalizer.are_predicates_compatible(na.norm_predicate, nb.norm_predicate, subj_canonical=na.canonical_subject):
            return None

        # ----------------------------------------------------------------------
        # STEP 3: VALUE & UNIT NORMALIZATION
        # ----------------------------------------------------------------------
        _, base_u_a = Normalizer.convert_to_base_numeric(na.numeric_value, na.norm_unit)
        _, base_u_b = Normalizer.convert_to_base_numeric(nb.numeric_value, nb.norm_unit)

        # Incompatible units cannot be compared (e.g. INR vs USD, or INR vs PERCENT)
        if base_u_a and base_u_b and base_u_a != base_u_b:
            return None

        values_match = self._are_values_equivalent(na, nb)

        # Temporal and scope context
        time_differs = bool(
            na.norm_time and nb.norm_time and na.norm_time != nb.norm_time
        )
        same_time = bool(
            (na.norm_time and nb.norm_time and na.norm_time == nb.norm_time)
            or (not na.norm_time and not nb.norm_time)
        )
        scope_differs = bool(
            na.norm_scope and nb.norm_scope and na.norm_scope != nb.norm_scope
        )

        # ----------------------------------------------------------------------
        # RULE 1: CORROBORATES
        # Same metric, compatible predicates, equivalent values, compatible timeframe
        # ----------------------------------------------------------------------
        if values_match and not time_differs and not scope_differs:
            time_str = f" ({na.norm_time})" if na.norm_time else ""
            reasoning = (
                f"Both documents corroborate the same factual claim regarding '{na.original_fact.subject}'{time_str}: "
                f"Fact A ({na.document_name}, p.{na.page_number}) asserts '{na.original_fact.object_value}' and "
                f"Fact B ({nb.document_name}, p.{nb.page_number}) asserts '{nb.original_fact.object_value}'."
            )
            return (RelationshipType.CORROBORATES, 0.95, reasoning, None)

        # ----------------------------------------------------------------------
        # RULE 2: CONTRADICTS
        # Same metric, compatible predicates, conflicting values, same time, no reconciling scope
        # ----------------------------------------------------------------------
        if not values_match and same_time and not scope_differs:
            time_str = f" for {na.norm_time}" if na.norm_time else ""
            reasoning = (
                f"Direct contradiction regarding '{na.original_fact.subject}'{time_str}: "
                f"Fact A ({na.document_name}, p.{na.page_number}) asserts '{na.original_fact.object_value}' while "
                f"Fact B ({nb.document_name}, p.{nb.page_number}) asserts conflicting value '{nb.original_fact.object_value}' under identical conditions."
            )
            return (RelationshipType.CONTRADICTS, 0.90, reasoning, None)

        # ----------------------------------------------------------------------
        # RULE 3: RECONCILES
        # Same metric, compatible predicates, differing values explained by time or scope.
        # (CRITICAL: Never classifies as RECONCILES if subjects are different metrics!)
        # ----------------------------------------------------------------------
        if not values_match:
            # Reconciled by Time
            if time_differs:
                time_a = na.original_fact.time_period or na.norm_time
                time_b = nb.original_fact.time_period or nb.norm_time
                reasoning = (
                    f"The values for '{na.original_fact.subject}' differ because they reflect different time periods: "
                    f"'{na.original_fact.object_value}' in {time_a} ({na.document_name}) versus "
                    f"'{nb.original_fact.object_value}' in {time_b} ({nb.document_name}). "
                    f"Both facts coexist consistently as the metric changed over time."
                )
                recon_ctx = f"Time period difference: {time_a} vs {time_b}"
                return (RelationshipType.RECONCILES, 0.92, reasoning, recon_ctx)

            # Reconciled by Scope
            if scope_differs:
                scope_a = na.original_fact.context or na.norm_scope
                scope_b = nb.original_fact.context or nb.norm_scope
                reasoning = (
                    f"Values for '{na.original_fact.subject}' differ due to distinct operational or reporting scopes: "
                    f"'{na.original_fact.object_value}' ({scope_a}) in Fact A versus "
                    f"'{nb.original_fact.object_value}' ({scope_b}) in Fact B. Both facts can be valid within their respective scopes."
                )
                recon_ctx = f"Scope difference: {scope_a} vs {scope_b}"
                return (RelationshipType.RECONCILES, 0.88, reasoning, recon_ctx)

        # Ambiguous -> defer to Gemini fallback (only if same canonical subject)
        return None

    def _evaluate_llm_fallback(
        self,
        na: NormalizedFact,
        nb: NormalizedFact
    ) -> Optional[Tuple[RelationshipType, float, str, Optional[str]]]:
        """Query Gemini to resolve genuinely ambiguous candidate pairs."""
        if not self.is_llm_available:
            return None

        from google.genai import types

        prompt = (
            f"{RELATIONSHIP_SYSTEM_INSTRUCTION}\n\n"
            f"FACT A:\n"
            f"- Document: {na.document_name} (Page {na.page_number})\n"
            f"- Subject: {na.original_fact.subject}\n"
            f"- Predicate: {na.original_fact.predicate}\n"
            f"- Value: {na.original_fact.object_value}\n"
            f"- Unit: {na.original_fact.unit or 'N/A'}\n"
            f"- Time Context: {na.original_fact.time_period or 'N/A'}\n"
            f"- Scope Context: {na.original_fact.context or 'N/A'}\n"
            f"- Evidence Quote: \"{na.original_fact.evidence.quote}\"\n\n"
            f"FACT B:\n"
            f"- Document: {nb.document_name} (Page {nb.page_number})\n"
            f"- Subject: {nb.original_fact.subject}\n"
            f"- Predicate: {nb.original_fact.predicate}\n"
            f"- Value: {nb.original_fact.object_value}\n"
            f"- Unit: {nb.original_fact.unit or 'N/A'}\n"
            f"- Time Context: {nb.original_fact.time_period or 'N/A'}\n"
            f"- Scope Context: {nb.original_fact.context or 'N/A'}\n"
            f"- Evidence Quote: \"{nb.original_fact.evidence.quote}\"\n\n"
            f"Classify the relationship between Fact A and Fact B as structured JSON."
        )

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=LLMRelationshipEvaluation,
            temperature=0.1,
        )

        for model_name in self.CANDIDATE_MODELS:
            try:
                response = self._client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                if response is not None:
                    eval_obj: Optional[LLMRelationshipEvaluation] = None
                    if hasattr(response, "parsed") and isinstance(response.parsed, LLMRelationshipEvaluation):
                        eval_obj = response.parsed
                    elif hasattr(response, "text") and response.text:
                        data = json.loads(response.text)
                        eval_obj = LLMRelationshipEvaluation(**data)

                    if eval_obj:
                        if eval_obj.relationship_type == RelationshipType.NO_RELATION:
                            return None
                        return (
                            eval_obj.relationship_type,
                            eval_obj.confidence,
                            eval_obj.explanation,
                            eval_obj.reconciliation_context
                        )
            except Exception as err:
                safe_err = str(err)
                if "429" in safe_err or "RESOURCE_EXHAUSTED" in safe_err:
                    self._rate_limited = True
                    logger.warning("Gemini rate limit reached; switching to deterministic engine.")
                if self.api_key:
                    safe_err = safe_err.replace(self.api_key, "[REDACTED]")
                logger.warning("LLM relationship fallback attempt with %s failed: %s", model_name, safe_err[:80])

        return None

    def compare_facts(self, fact_a: Fact, fact_b: Fact) -> Optional[FactRelationship]:
        """
        Compares two facts and classifies their relationship.
        Applies deterministic normalization and strict rules first, falling back to Gemini
        ONLY when candidate facts share the exact canonical subject and are genuinely ambiguous.
        """
        na = Normalizer.normalize_fact(fact_a)
        nb = Normalizer.normalize_fact(fact_b)

        # STEP 1: STRICT SUBJECT REJECTION FIRST
        # If subjects represent different metrics/entities (e.g. Other expenses vs Total expenses),
        # immediately reject without establishing any relationship.
        if not Normalizer.are_subjects_compatible(na.canonical_subject, nb.canonical_subject):
            return None

        # 1. Deterministic evaluation (fast, high-confidence, zero cost)
        det_result = self._evaluate_deterministic(na, nb)
        if det_result is not None:
            rel_type, conf, reasoning, recon_ctx = det_result
            return FactRelationship(
                fact_a_id=fact_a.id or 0,
                fact_b_id=fact_b.id or 0,
                relationship_type=rel_type,
                reasoning=reasoning,
                reconciliation_context=recon_ctx,
                confidence=conf
            )

        # 2. LLM fallback: Only for identical canonical subjects when deterministic rules are inconclusive
        if not getattr(self, "_rate_limited", False) and self.is_llm_available:
            llm_result = self._evaluate_llm_fallback(na, nb)
            if llm_result is not None:
                rel_type, conf, reasoning, recon_ctx = llm_result
                return FactRelationship(
                    fact_a_id=fact_a.id or 0,
                    fact_b_id=fact_b.id or 0,
                    relationship_type=rel_type,
                    reasoning=reasoning,
                    reconciliation_context=recon_ctx,
                    confidence=conf
                )

        return None

    def evaluate_relationships(
        self,
        candidate_pairs: List[Tuple[NormalizedFact, NormalizedFact]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[FactRelationship]:
        """
        Evaluates candidate fact pairs and returns all confirmed relationships.
        Filters out NO_RELATION pairs and ensures uniqueness.
        """
        confirmed_relationships: List[FactRelationship] = []
        seen_pairs = set()

        total = len(candidate_pairs)
        for idx, (na, nb) in enumerate(candidate_pairs):
            if progress_callback:
                progress_callback(idx + 1, total)

            pair_key = (min(na.fact_id, nb.fact_id), max(na.fact_id, nb.fact_id))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            rel = self.compare_facts(na.original_fact, nb.original_fact)
            if rel is not None and rel.relationship_type != RelationshipType.NO_RELATION:
                confirmed_relationships.append(rel)

        return confirmed_relationships
