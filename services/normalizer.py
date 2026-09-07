"""
Fact Normalizer Service
=======================
Provides deterministic normalization for extracted facts to enable accurate,
noise-free candidate matching and cross-document relationship reasoning.

Key Principles:
1. Immutability: The original Fact domain model remains completely unchanged.
2. Deterministic Normalization: Canonicalizes subjects, predicates, values,
   currencies, measurement units, and temporal contexts.
3. Intelligent Candidate Matching: Uses inverted keyword indexing and token
   similarity to pair related cross-document facts while eliminating unrelated noise.
"""

import re
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict, Any, Optional
from models.schemas import Fact, FactType

# Standard stopwords that do not convey domain meaning.
# CRITICAL: "total", "other", "net", "gross", "operating" are EXCLUDED from stopwords
# because they are essential metric qualifiers that differentiate distinct financial items.
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it",
    "its", "itself", "let's", "me", "more", "most", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "she", "should", "so", "some", "such",
    "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "were", "weren't", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "won't", "would", "you", "your", "yours",
    "yourself", "yourselves", "also", "per", "etc"
}

GENERIC_ENTITY_TOKENS = {
    "private", "limited", "ltd", "pvt", "corp", "corporation",
    "inc", "incorporated", "llc", "co", "company", "holdings", "holding"
}

# Broad category words that must NEVER be used on their own to match different metrics
BROAD_CATEGORY_KEYWORDS = {
    "expense", "expenses", "revenue", "revenues", "cost", "costs",
    "income", "profit", "profits", "loss", "losses", "asset", "assets",
    "liability", "liabilities", "cash", "debt", "debts", "margin", "margins",
    "expenditure", "expenditures"
}

# Verified exact synonyms and canonical aliases in business/financial reporting
CANONICAL_SUBJECT_ALIASES = {
    "revenue from contracts with customers": "revenue from operations",
    "revenues from contracts with customers": "revenue from operations",
    "revenue from customer contracts": "revenue from operations",
    "revenue from contract with customers": "revenue from operations",
    "sales revenue": "revenue from operations",
    "total revenue from operations": "revenue from operations",
    "net sales": "revenue from operations",
    "pat": "profit after tax",
    "pbt": "profit before tax",
    "ebitda": "ebitda",
    "net profit": "net profit",
    "net income": "net profit",
    "diluted earnings per share": "earnings per share",
    "basic earnings per share": "earnings per share",
    "eps": "earnings per share",
    "headcount": "total employees",
    "number of employees": "total employees",
    "total employee count": "total employees",
    "workforce": "total employees",
    "pin codes covered": "pin codes",
    "postal codes covered": "pin codes",
    "network pin codes": "pin codes",
    "pincodes": "pin codes",
}

# Unit normalizations
UNIT_MAP = {
    "$": "USD",
    "usd": "USD",
    "dollars": "USD",
    "us dollars": "USD",
    "inr": "INR",
    "rs": "INR",
    "rs.": "INR",
    "rupees": "INR",
    "₹": "INR",
    "inr cr": "INR_CRORE",
    "inr crore": "INR_CRORE",
    "crore": "INR_CRORE",
    "cr": "INR_CRORE",
    "₹ cr": "INR_CRORE",
    "₹ crore": "INR_CRORE",
    "inr million": "INR_MILLION",
    "₹ million": "INR_MILLION",
    "million": "INR_MILLION",
    "inr lakh": "INR_LAKH",
    "₹ lakh": "INR_LAKH",
    "lakh": "INR_LAKH",
    "inr billion": "INR_BILLION",
    "₹ billion": "INR_BILLION",
    "%": "PERCENT",
    "percent": "PERCENT",
    "percentage": "PERCENT",
    "employees": "HEADCOUNT",
    "people": "HEADCOUNT",
    "headcount": "HEADCOUNT",
    "team members": "HEADCOUNT",
    "pin codes": "PIN_CODES",
    "pincodes": "PIN_CODES",
    "postal codes": "PIN_CODES",
    "sq ft": "SQ_FT",
    "sq. ft": "SQ_FT",
    "sqft": "SQ_FT",
    "square feet": "SQ_FT",
}

# Predicate classifications
PREDICATE_REPORTING = {
    "is", "was", "are", "were", "amounted to", "amounted", "reported",
    "recorded", "stood at", "reached", "generated", "totaled", "totalled",
    "valued at", "equal to", "has", "had", "accounted for", "comprised",
    "represented", "posted"
}

PREDICATE_DIRECTIONAL_UP = {
    "increased", "grew", "rose", "expanded", "jumped", "surged", "climbed"
}

PREDICATE_DIRECTIONAL_DOWN = {
    "decreased", "dropped", "fell", "declined", "contracted", "slumped", "shrank"
}

PREDICATE_EVENT = {
    "appointed", "named", "designated", "elected", "resigned", "stepped down",
    "retired", "vacated", "acquired", "bought", "purchased", "founded", "incorporated",
    "partnered", "launched"
}

# Predicate synonym clusters
PREDICATE_SYNONYMS = {
    "reported": "reported",
    "recorded": "reported",
    "achieved": "reported",
    "generated": "reported",
    "stood at": "reported",
    "reached": "reported",
    "amounted to": "reported",
    "was": "is",
    "are": "is",
    "were": "is",
    "grew": "increased",
    "rose": "increased",
    "expanded": "increased",
    "dropped": "decreased",
    "fell": "decreased",
    "declined": "decreased",
    "named": "appointed",
    "designated": "appointed",
    "elected": "appointed",
    "stepped down": "resigned",
    "retired": "resigned",
    "vacated": "resigned",
    "bought": "acquired",
    "purchased": "acquired",
}


@dataclass
class NormalizedFact:
    """
    Comparison representation of a Fact.
    Leaves the original Fact untouched while exposing clean comparison properties.
    """
    fact_id: int
    document_id: Optional[int]
    document_name: str
    page_number: int
    original_fact: Fact

    # Canonical comparison strings
    norm_subject: str
    canonical_subject: str
    subject_tokens: Set[str]
    norm_predicate: str
    predicate_class: str
    predicate_tokens: Set[str]
    norm_value_str: str
    numeric_value: Optional[float]
    base_numeric_value: Optional[float]
    norm_unit: Optional[str]
    base_unit: Optional[str]
    norm_time: Optional[str]
    norm_scope: Optional[str]
    fact_type: str


class Normalizer:
    """Normalizes facts and identifies high-confidence candidate pairs for comparison."""

    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        """Lowercase, strip punctuation, and collapse whitespace."""
        if not text:
            return ""
        # Replace non-alphanumeric (except standard period and hyphens in numbers)
        cleaned = re.sub(r"[^\w\s\.\-%]", " ", str(text).lower())
        # Collapse multiple spaces
        return re.sub(r"\s+", " ", cleaned).strip()

    @staticmethod
    def extract_tokens(text: str) -> Set[str]:
        """Extract meaningful, non-stopword tokens of length >= 2."""
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        words = cleaned.split()
        return {w for w in words if len(w) >= 2 and w not in STOPWORDS and not w.isdigit()}

    @classmethod
    def canonicalize_subject(cls, subject: Optional[str]) -> str:
        """
        Produce a strict canonical representation of a subject or entity.
        - Strips punctuation and extraneous whitespace.
        - Strips corporate legal suffixes (e.g. 'Delhivery Limited' -> 'delhivery').
        - Maps known exact aliases (e.g. 'revenue from contracts with customers' -> 'revenue from operations').
        - PRESERVES all line-item qualifiers ('total', 'other', 'operating', 'adjusted', 'gross', 'net').
        """
        if not subject:
            return ""

        cleaned = cls.clean_text(subject)

        # Strip corporate legal entity suffixes at word boundaries
        cleaned = re.sub(
            r"\b(pvt\.?|private|ltd\.?|limited|corp\.?|corporation|inc\.?|incorporated|llc|co\.?|company)\b",
            " ",
            cleaned
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Check canonical aliases
        if cleaned in CANONICAL_SUBJECT_ALIASES:
            return CANONICAL_SUBJECT_ALIASES[cleaned]

        return cleaned

    @classmethod
    def are_subjects_compatible(cls, subj_a: Optional[str], subj_b: Optional[str]) -> bool:
        """
        Strict subject matching check.
        Returns True IF AND ONLY IF canonical subjects represent the exact same entity or metric.
        Explicitly rejects matching based on broad category keywords alone.
        """
        canon_a = cls.canonicalize_subject(subj_a)
        canon_b = cls.canonicalize_subject(subj_b)

        if not canon_a or not canon_b:
            return False

        # Identical canonical subject or exact alias match
        if canon_a == canon_b:
            return True

        return False

    @staticmethod
    def clean_unit(unit_str: Optional[str]) -> Optional[str]:
        """Normalize unit strings to standard representations."""
        if not unit_str:
            return None
        raw = unit_str.lower().strip()
        # Replace unicode rupee symbol and alternate abbreviations
        raw = raw.replace("₹", "inr ").replace("rs.", "inr ").replace("rs ", "inr ").strip()
        raw = re.sub(r"\s+", " ", raw)
        return UNIT_MAP.get(raw, UNIT_MAP.get(unit_str.lower().strip(), unit_str.upper()))

    @classmethod
    def parse_numeric_value(cls, value_str: Optional[str], unit_str: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
        """
        Parses numeric magnitude and unit from string representations.
        Detects currency, multipliers, and unit markers.
        """
        if not value_str:
            return None, cls.clean_unit(unit_str)

        raw = str(value_str).lower().replace(",", "").strip()
        detected_unit = cls.clean_unit(unit_str)

        # Check in-value unit indicators
        if "$" in raw or "usd" in raw or "dollar" in raw:
            detected_unit = detected_unit or "USD"
        elif "₹" in raw or "rs" in raw or "inr" in raw or "rupee" in raw:
            if "cr" in raw or "crore" in raw:
                detected_unit = "INR_CRORE"
            elif "lakh" in raw:
                detected_unit = "INR_LAKH"
            elif "million" in raw:
                detected_unit = "INR_MILLION"
            else:
                detected_unit = detected_unit or "INR"
        elif "%" in raw or "percent" in raw:
            detected_unit = "PERCENT"
        elif "pin code" in raw or "pincode" in raw:
            detected_unit = "PIN_CODES"
        elif "employee" in raw or "headcount" in raw or "people" in raw:
            detected_unit = "HEADCOUNT"

        # Multipliers
        multiplier = 1.0
        if "billion" in raw or re.search(r"\b\d+(\.\d+)?b\b", raw):
            multiplier = 1_000_000_000.0
            if detected_unit in ("USD", "INR"):
                detected_unit = f"{detected_unit}_BILLION"
        elif "million" in raw or re.search(r"\b\d+(\.\d+)?m\b", raw):
            multiplier = 1_000_000.0
            if detected_unit in ("USD", "INR"):
                detected_unit = f"{detected_unit}_MILLION"
        elif "crore" in raw or re.search(r"\b\d+(\.\d+)?cr\b", raw):
            multiplier = 10_000_000.0
            detected_unit = "INR_CRORE"
        elif "lakh" in raw:
            multiplier = 100_000.0
            detected_unit = "INR_LAKH"

        # Extract number
        match = re.search(r"[-+]?\d*\.?\d+", raw)
        if match:
            try:
                base_val = float(match.group())
                # If unit string already conveys the unit multiplier (e.g. unit="₹ million" and value="1,963.74"),
                # we keep base_val as 1963.74 and unit as INR_MILLION.
                # Only apply in-string word multiplier if unit was not already explicitly tagged.
                if multiplier != 1.0 and unit_str and any(m in unit_str.lower() for m in ["million", "crore", "cr", "lakh", "billion"]):
                    return base_val, detected_unit
                return base_val * multiplier, detected_unit
            except ValueError:
                pass

        return None, detected_unit

    @classmethod
    def convert_to_base_numeric(
        cls,
        value: Optional[float],
        unit: Optional[str]
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Converts numerical values to a standardized base scale and unit for accurate comparison.
        - Indian Currency: ₹1 Cr = 10,000,000 INR = 10 Million INR. ₹1 Lakh = 100,000 INR.
        - Standardizes all INR values to base INR.
        - Standardizes USD values to base USD.
        """
        if value is None:
            return None, None

        if not unit:
            return value, None

        unit_clean = cls.clean_unit(unit) or unit.upper()

        # INR Currency Family
        if unit_clean in ("INR_CRORE", "CRORE", "CR"):
            return value * 10_000_000.0, "INR"
        elif unit_clean in ("INR_LAKH", "LAKH"):
            return value * 100_000.0, "INR"
        elif unit_clean in ("INR_MILLION", "MILLION"):
            return value * 1_000_000.0, "INR"
        elif unit_clean in ("INR_BILLION", "BILLION"):
            return value * 1_000_000_000.0, "INR"
        elif unit_clean in ("INR", "RUPEES", "RS"):
            return value * 1.0, "INR"

        # USD Currency Family
        elif unit_clean in ("USD_BILLION",):
            return value * 1_000_000_000.0, "USD"
        elif unit_clean in ("USD_MILLION",):
            return value * 1_000_000.0, "USD"
        elif unit_clean in ("USD", "DOLLARS"):
            return value * 1.0, "USD"

        # Other measurement families
        elif unit_clean in ("PERCENT", "%"):
            return value, "PERCENT"
        elif unit_clean in ("HEADCOUNT", "EMPLOYEES"):
            return value, "HEADCOUNT"
        elif unit_clean in ("PIN_CODES", "PINCODES"):
            return value, "PIN_CODES"
        elif unit_clean in ("SQ_FT", "SQFT"):
            return value, "SQ_FT"

        return value, unit_clean

    @classmethod
    def are_numeric_values_equivalent(
        cls,
        val_a: Optional[float],
        unit_a: Optional[str],
        val_b: Optional[float],
        unit_b: Optional[str],
        tolerance: float = 0.015
    ) -> bool:
        """
        Checks if two numerical values are equivalent after unit normalization.
        Tolerance defaults to 1.5% to allow for rounding in audited filings.
        """
        if val_a is None or val_b is None:
            return False

        base_val_a, base_unit_a = cls.convert_to_base_numeric(val_a, unit_a)
        base_val_b, base_unit_b = cls.convert_to_base_numeric(val_b, unit_b)

        # Incompatible units (e.g. INR vs USD, or INR vs PERCENT) cannot be equivalent
        if base_unit_a and base_unit_b and base_unit_a != base_unit_b:
            return False

        if abs(base_val_a) < 1e-6 and abs(base_val_b) < 1e-6:
            return True

        max_val = max(abs(base_val_a), abs(base_val_b))
        if max_val == 0.0:
            return True

        return (abs(base_val_a - base_val_b) / max_val) <= tolerance

    @staticmethod
    def get_predicate_class(norm_predicate: str) -> str:
        """Categorize predicate into REPORTING, DIRECTIONAL_UP, DIRECTIONAL_DOWN, EVENT, or ATTRIBUTE."""
        clean = norm_predicate.strip().lower()
        words = set(clean.split())
        if clean in PREDICATE_REPORTING or words.intersection(PREDICATE_REPORTING):
            return "REPORTING"
        if clean in PREDICATE_DIRECTIONAL_UP or words.intersection(PREDICATE_DIRECTIONAL_UP):
            return "DIRECTIONAL_UP"
        if clean in PREDICATE_DIRECTIONAL_DOWN or words.intersection(PREDICATE_DIRECTIONAL_DOWN):
            return "DIRECTIONAL_DOWN"
        if clean in PREDICATE_EVENT or words.intersection(PREDICATE_EVENT):
            return "EVENT"
        return "ATTRIBUTE"

    @classmethod
    def are_predicates_compatible(cls, pred_a: str, pred_b: str, subj_canonical: str = "") -> bool:
        """
        Check if two predicates are semantically compatible.
        - Reporting predicates ('was', 'reported', 'amounted to') are mutually compatible
          when comparing specific metrics (e.g. Revenue, EBITDA, Expenses).
        - If the subject is a broad company entity (e.g. 'Delhivery', 'Company'), generic reporting
          verbs alone do not guarantee they discuss the same metric.
        - Attribute predicates ('scrip code', 'corporate identity number') must match in attribute meaning.
        """
        clean_a = cls.clean_text(pred_a)
        clean_b = cls.clean_text(pred_b)

        if clean_a == clean_b:
            return True

        class_a = cls.get_predicate_class(clean_a)
        class_b = cls.get_predicate_class(clean_b)

        # Both are generic reporting verbs ("was", "reported", "amounted to")
        if class_a == "REPORTING" and class_b == "REPORTING":
            if subj_canonical in ("delhivery", "company", "group", "the company", "corporation"):
                return False
            return True

        # Both are directional in the same direction
        if class_a == class_b and class_a in ("DIRECTIONAL_UP", "DIRECTIONAL_DOWN", "EVENT"):
            return True

        # Both are attribute descriptions (e.g., "headquarters", "registered office")
        if class_a == "ATTRIBUTE" and class_b == "ATTRIBUTE":
            toks_a = cls.extract_tokens(clean_a)
            toks_b = cls.extract_tokens(clean_b)
            if toks_a and toks_a == toks_b:
                return True
            return False

        return False

    @staticmethod
    def normalize_time(time_str: Optional[str]) -> Optional[str]:
        """
        Standardizes fiscal years and dates.
        Examples:
          'FY 2023', 'FY23', 'Financial Year 2023' -> 'FY2023'
          'Year ended March 31, 2019' -> 'FY2019'
          'Q4 FY24' -> 'Q4_FY2024'
          '2022' -> '2022'
        """
        if not time_str:
            return None

        raw = time_str.lower().strip()

        # Match Q[1-4] FY[0-9]+
        q_match = re.search(r"\b(q[1-4])\s*(?:of\s*)?(?:fy|fiscal\s*(?:year)?)?\s*('?20)?(\d{2})\b", raw)
        if q_match:
            quarter = q_match.group(1).upper()
            year_suffix = q_match.group(3)
            full_year = f"20{year_suffix}" if len(year_suffix) == 2 else year_suffix
            return f"{quarter}_FY{full_year}"

        # Match FY[0-9]+
        fy_match = re.search(r"\b(?:fy|fiscal\s*(?:year)?)\s*('?20)?(\d{2,4})\b", raw)
        if fy_match:
            year = fy_match.group(2)
            full_year = f"20{year}" if len(year) == 2 else year
            return f"FY{full_year}"

        # Match 4-digit calendar year or 'year ended march 31, 2019'
        m_year = re.search(r"\b(19\d{2}|20\d{2})\b", raw)
        if m_year:
            if "year ended" in raw or "march 31" in raw:
                return f"FY{m_year.group(1)}"
            return m_year.group(1)

        return Normalizer.clean_text(time_str)

    @classmethod
    def normalize_fact(cls, fact: Fact) -> NormalizedFact:
        """
        Produce a normalized comparison view of a Fact without mutating the original.
        """
        clean_subj = cls.clean_text(fact.subject)
        canonical_subj = cls.canonicalize_subject(fact.subject)
        clean_pred = cls.clean_text(fact.predicate)
        clean_val = cls.clean_text(fact.object_value)

        # Map predicate synonyms
        pred_words = clean_pred.split()
        canonical_pred = " ".join(PREDICATE_SYNONYMS.get(w, w) for w in pred_words)
        pred_class = cls.get_predicate_class(canonical_pred)

        parsed_num, parsed_unit = cls.parse_numeric_value(fact.object_value, fact.unit)
        if fact.numeric_value is not None:
            parsed_num = fact.numeric_value

        base_val, base_unit = cls.convert_to_base_numeric(parsed_num, parsed_unit)

        norm_time = cls.normalize_time(fact.time_period)
        norm_scope = cls.clean_text(fact.context) if fact.context else None

        fact_type_str = fact.fact_type.value if hasattr(fact.fact_type, "value") else str(fact.fact_type)

        return NormalizedFact(
            fact_id=fact.id or 0,
            document_id=fact.document_id,
            document_name=fact.document_name,
            page_number=fact.page_number,
            original_fact=fact,
            norm_subject=clean_subj,
            canonical_subject=canonical_subj,
            subject_tokens=cls.extract_tokens(clean_subj),
            norm_predicate=canonical_pred,
            predicate_class=pred_class,
            predicate_tokens=cls.extract_tokens(canonical_pred),
            norm_value_str=clean_val,
            numeric_value=parsed_num,
            base_numeric_value=base_val,
            norm_unit=parsed_unit,
            base_unit=base_unit,
            norm_time=norm_time,
            norm_scope=norm_scope,
            fact_type=fact_type_str,
        )

    @classmethod
    def find_candidate_pairs(
        cls,
        facts: List[Fact],
        max_candidates: int = 150,
        prefer_cross_document: bool = True
    ) -> List[Tuple[NormalizedFact, NormalizedFact]]:
        """
        Identify high-confidence candidate fact pairs for comparison.

        STRICT SUBJECT MATCHING:
        - Groups facts strictly by canonical subject or verified alias.
        - Never pairs facts based on broad category words (e.g. 'expense', 'cost', 'revenue') alone.
        - Filters out incompatible predicates upfront.
        """
        if len(facts) < 2:
            return []

        # 1. Normalize all facts
        normalized_facts = [cls.normalize_fact(f) for f in facts]

        # 2. Group facts strictly by canonical subject
        subject_to_facts: Dict[str, List[NormalizedFact]] = {}
        for n_fact in normalized_facts:
            subj = n_fact.canonical_subject
            if not subj or len(subj) < 2:
                continue
            subject_to_facts.setdefault(subj, []).append(n_fact)

        # 3. Form candidate pairs within matching canonical subject groups
        candidate_pairs: List[Tuple[NormalizedFact, NormalizedFact]] = []
        seen_pairs = set()

        for subj, group in subject_to_facts.items():
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    fa = group[i]
                    fb = group[j]

                    # Enforce document boundary if prefer_cross_document is requested
                    if prefer_cross_document and fa.document_name == fb.document_name:
                        continue

                    # Filter incompatible predicates upfront
                    if not cls.are_predicates_compatible(fa.norm_predicate, fb.norm_predicate, subj_canonical=subj):
                        continue

                    # Prevent duplicate pairs
                    pair_key = (min(fa.fact_id, fb.fact_id), max(fa.fact_id, fb.fact_id))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    candidate_pairs.append((fa, fb))
                    if len(candidate_pairs) >= max_candidates:
                        return candidate_pairs

        return candidate_pairs
