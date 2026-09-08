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

# Essential financial metric qualifiers that differentiate line items.
# CRITICAL: These must NEVER be stripped, ignored, or conflated.
FINANCIAL_QUALIFIERS = {
    "total", "other", "net", "gross", "operating", "adjusted", "basic", "diluted", "non-operating"
}

# Sets of qualifiers that are strictly mutually exclusive in financial reporting.
# If Fact A and Fact B contain qualifiers from opposing sides of these sets,
# they MUST be rejected immediately as NO_RELATION.
MUTUALLY_EXCLUSIVE_QUALIFIERS = [
    {"total", "other"},
    {"net", "gross"},
    {"operating", "net"},
    {"operating", "other"},
    {"operating", "non-operating"},
    {"basic", "diluted"},
]

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
    "operating revenue": "revenue from operations",
    "operating revenues": "revenue from operations",
    "revenue from operation": "revenue from operations",
    "sales revenue": "revenue from operations",
    "total revenue from operations": "revenue from operations",
    "net sales": "revenue from operations",
    "pat": "profit after tax",
    "pbt": "profit before tax",
    "ebitda": "ebitda",
    "net profit": "net profit",
    "net income": "net profit",
    "gross profit": "gross profit",
    "gross margin": "gross profit",
    "operating profit": "operating profit",
    "operating income": "operating profit",
    "ebit": "operating profit",
    "other expense": "other expenses",
    "total expense": "total expenses",
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
    def extract_qualifiers(cls, text: Optional[str]) -> Set[str]:
        """Extract active financial qualifiers (e.g. 'total', 'other', 'net', 'gross', 'operating', 'adjusted')."""
        if not text:
            return set()
        clean = cls.clean_text(text)
        tokens = set(clean.split())
        return tokens.intersection(FINANCIAL_QUALIFIERS)

    @classmethod
    def are_qualifiers_compatible(cls, subj_a: Optional[str], subj_b: Optional[str]) -> bool:
        """
        Enforce strict financial qualifier compatibility.
        - 'Other expenses' != 'Total expenses'
        - 'Net revenue' != 'Gross revenue'
        - 'Operating profit' != 'Net profit'
        - 'Basic EPS' != 'Diluted EPS'
        If two subjects contain mutually exclusive qualifiers, or if one contains 'other'
        while the other does not (e.g. 'Other expenses' vs 'Total expenses' / 'Expenses'),
        reject immediately as False.
        """
        quals_a = cls.extract_qualifiers(subj_a)
        quals_b = cls.extract_qualifiers(subj_b)

        # 1. Check mutually exclusive qualifier pairs
        combined = quals_a.union(quals_b)
        for conflict_set in MUTUALLY_EXCLUSIVE_QUALIFIERS:
            if conflict_set.issubset(combined):
                # Ensure the conflict isn't internal to a single term (e.g., if one term had both)
                has_a = bool(quals_a.intersection(conflict_set))
                has_b = bool(quals_b.intersection(conflict_set))
                if has_a and has_b and quals_a.intersection(conflict_set) != quals_b.intersection(conflict_set):
                    return False

        # 2. Asymmetric 'other' check: 'other expenses' is a specific sub-item, never equivalent to general or total items
        if ("other" in quals_a and "other" not in quals_b) or ("other" in quals_b and "other" not in quals_a):
            clean_a = cls.clean_text(subj_a)
            clean_b = cls.clean_text(subj_b)
            if any(kw in clean_a or kw in clean_b for kw in BROAD_CATEGORY_KEYWORDS):
                return False

        # 3. Asymmetric 'total' check when paired with non-total specific qualifiers
        if ("total" in quals_a and "total" not in quals_b) or ("total" in quals_b and "total" not in quals_a):
            non_total_quals = {"operating", "net", "other", "gross"}
            if quals_a.intersection(non_total_quals) or quals_b.intersection(non_total_quals):
                if quals_a != quals_b:
                    return False

        return True

    @classmethod
    def compute_metric_similarity(cls, subj_a: Optional[str], subj_b: Optional[str]) -> float:
        """
        Lightweight local semantic similarity between two metric subjects.
        - Returns 0.0 immediately if financial qualifiers conflict.
        - Evaluates token Jaccard similarity, sequence ratio, and canonical alias equivalence.
        - Pure standard library: does NOT require external cloud infrastructure or heavy vector stores.
        """
        if not subj_a or not subj_b:
            return 0.0

        # Strict qualifier barrier: if qualifiers conflict, similarity is 0.0
        if not cls.are_qualifiers_compatible(subj_a, subj_b):
            return 0.0

        canon_a = cls.canonicalize_subject(subj_a)
        canon_b = cls.canonicalize_subject(subj_b)

        if canon_a == canon_b:
            return 1.0

        toks_a = cls.extract_tokens(canon_a)
        toks_b = cls.extract_tokens(canon_b)

        if not toks_a or not toks_b:
            return 0.0

        # Disjoint broad category rejection (e.g. employee count vs revenue, or expense vs profit)
        cats_a = toks_a.intersection(BROAD_CATEGORY_KEYWORDS)
        cats_b = toks_b.intersection(BROAD_CATEGORY_KEYWORDS)
        if cats_a and cats_b and cats_a != cats_b:
            return 0.0
        if bool(cats_a) != bool(cats_b) and not toks_a.intersection(toks_b):
            return 0.0

        # Jaccard Token Overlap
        intersection = toks_a.intersection(toks_b)
        union = toks_a.union(toks_b)
        jaccard = len(intersection) / len(union) if union else 0.0

        # Difflib sequence similarity on canonical strings
        import difflib
        seq_ratio = difflib.SequenceMatcher(None, canon_a, canon_b).ratio()

        return round(0.6 * jaccard + 0.4 * seq_ratio, 3)

    @classmethod
    def are_subjects_compatible(cls, subj_a: Optional[str], subj_b: Optional[str]) -> bool:
        """
        Strict subject matching check.
        Returns True IF AND ONLY IF canonical subjects represent the exact same entity or metric.
        - Enforces qualifier compatibility (e.g. Other expenses != Total expenses).
        - Checks canonical alias equivalence (e.g. 'Revenue from operations' == 'Operating revenue').
        - Evaluates semantic similarity with identical root category.
        - Explicitly rejects matching based on broad category keywords alone.
        """
        if not subj_a or not subj_b:
            return False

        # 1. HARD QUALIFIER BARRIER FIRST
        if not cls.are_qualifiers_compatible(subj_a, subj_b):
            return False

        canon_a = cls.canonicalize_subject(subj_a)
        canon_b = cls.canonicalize_subject(subj_b)

        if not canon_a or not canon_b:
            return False

        # 2. Identical canonical subject or exact alias match
        if canon_a == canon_b:
            return True

        # 3. Disjoint category rejection
        toks_a = cls.extract_tokens(canon_a)
        toks_b = cls.extract_tokens(canon_b)
        cats_a = toks_a.intersection(BROAD_CATEGORY_KEYWORDS)
        cats_b = toks_b.intersection(BROAD_CATEGORY_KEYWORDS)
        if cats_a and cats_b and cats_a != cats_b:
            return False
        if bool(cats_a) != bool(cats_b) and not toks_a.intersection(toks_b):
            return False

        # 4. Semantic similarity threshold with compatible heads
        sim = cls.compute_metric_similarity(subj_a, subj_b)
        if sim >= 0.82:
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
        max_candidates: int = 250,
        top_k_per_fact: int = 5,
        prefer_cross_document: bool = True
    ) -> List[Tuple[NormalizedFact, NormalizedFact]]:
        """
        Identify high-confidence candidate fact pairs for comparison.

        CANDIDATE GENERATION PIPELINE:
        All Facts
           ↓
        Metric Canonicalization
           ↓
        Strict Metric Compatibility Filter (Hard Financial Qualifier Barrier)
           ↓
        Semantic Similarity (Lightweight & Local)
           ↓
        Top-K Relevant Candidates
           ↓
        Relationship Engine

        Guarantees:
        - Never compares every fact against every other fact (no brute force).
        - Distinct financial qualifiers ('Other expenses' vs 'Total expenses') are rejected upfront.
        - Cross-document boundary is respected when prefer_cross_document is True.
        - Predicates must be compatible.
        """
        if len(facts) < 2:
            return []

        # 1. Normalize all facts
        normalized_facts = [cls.normalize_fact(f) for f in facts]

        # 2. Metric Canonicalization: Group facts into canonical metric buckets
        subject_to_facts: Dict[str, List[NormalizedFact]] = {}
        for n_fact in normalized_facts:
            subj = n_fact.canonical_subject
            if not subj or len(subj) < 2:
                continue
            subject_to_facts.setdefault(subj, []).append(n_fact)

        # 3. Strict Metric Compatibility: Find compatible bucket clusters via inverted token index
        all_canonical_keys = list(subject_to_facts.keys())
        compatible_key_pairs: Set[Tuple[str, str]] = set()

        # Each canonical bucket is self-compatible
        for key in all_canonical_keys:
            compatible_key_pairs.add((key, key))

        # Index keys by meaningful tokens to avoid quadratic all-pairs comparisons
        token_to_keys: Dict[str, List[str]] = {}
        for key in all_canonical_keys:
            toks = cls.extract_tokens(key)
            for t in toks:
                token_to_keys.setdefault(t, []).append(key)

        evaluated_pairs: Set[Tuple[str, str]] = set()
        for token, keys_with_token in token_to_keys.items():
            if len(keys_with_token) > 1:
                for i in range(len(keys_with_token)):
                    k_a = keys_with_token[i]
                    for j in range(i + 1, len(keys_with_token)):
                        k_b = keys_with_token[j]
                        pair_id = (min(k_a, k_b), max(k_a, k_b))
                        if pair_id in evaluated_pairs:
                            continue
                        evaluated_pairs.add(pair_id)

                        if cls.are_subjects_compatible(k_a, k_b):
                            compatible_key_pairs.add((k_a, k_b))
                            compatible_key_pairs.add((k_b, k_a))

        # 4. Semantic Similarity & Candidate Pair Generation
        # Map fact_id -> list of candidate tuples (score, NormalizedFact, NormalizedFact)
        fact_candidates: Dict[int, List[Tuple[float, NormalizedFact, NormalizedFact]]] = {}
        seen_pairs: Set[Tuple[int, int]] = set()

        for (key_a, key_b) in compatible_key_pairs:
            group_a = subject_to_facts[key_a]
            group_b = subject_to_facts[key_b]

            is_same_group = (key_a == key_b)

            for i in range(len(group_a)):
                fa = group_a[i]
                start_j = (i + 1) if is_same_group else 0

                for j in range(start_j, len(group_b)):
                    fb = group_b[j]

                    if fa.fact_id == fb.fact_id:
                        continue

                    # Cross-document boundary enforcement
                    if prefer_cross_document and fa.document_name == fb.document_name:
                        continue

                    # Filter incompatible predicates upfront
                    if not cls.are_predicates_compatible(fa.norm_predicate, fb.norm_predicate, subj_canonical=fa.canonical_subject):
                        continue

                    # Filter incompatible units upfront (e.g. INR vs USD, or INR vs PERCENT)
                    if fa.base_unit and fb.base_unit and fa.base_unit != fb.base_unit:
                        continue

                    pair_key = (min(fa.fact_id, fb.fact_id), max(fa.fact_id, fb.fact_id))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    # Compute similarity score
                    sim_score = cls.compute_metric_similarity(fa.norm_subject, fb.norm_subject)

                    # Boost score if values are equivalent
                    if fa.base_numeric_value is not None and fb.base_numeric_value is not None:
                        if cls.are_numeric_values_equivalent(fa.numeric_value, fa.norm_unit, fb.numeric_value, fb.norm_unit):
                            sim_score += 0.3

                    fact_candidates.setdefault(fa.fact_id, []).append((sim_score, fa, fb))
                    fact_candidates.setdefault(fb.fact_id, []).append((sim_score, fb, fa))

        # 5. Top-K Relevant Candidates Selection
        scored_pairs: Dict[Tuple[int, int], Tuple[float, NormalizedFact, NormalizedFact]] = {}

        for fid, candidates in fact_candidates.items():
            # Sort candidates by similarity score descending
            candidates.sort(key=lambda x: x[0], reverse=True)
            for score, fa, fb in candidates[:top_k_per_fact]:
                pair_key = (min(fa.fact_id, fb.fact_id), max(fa.fact_id, fb.fact_id))
                if pair_key not in scored_pairs or score > scored_pairs[pair_key][0]:
                    scored_pairs[pair_key] = (score, fa, fb)

        # Sort all selected candidate pairs by score descending and truncate to max_candidates
        sorted_candidates = sorted(scored_pairs.values(), key=lambda x: x[0], reverse=True)
        return [(fa, fb) for _, fa, fb in sorted_candidates[:max_candidates]]
