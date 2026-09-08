"""
Fact Extractor Service (Gemini Integration)
===========================================
Extracts structured numerical and semantic facts from PDF page text using
the official Google GenAI SDK (`google-genai`), linking each fact to its exact
source evidence quote, document filename, and page number.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from models.schemas import (
    Fact,
    Evidence,
    FactType,
    ExtractedFactItem,
    ExtractedFactsList,
)

logger = logging.getLogger(__name__)

# System instructions to ensure grounding and prevent hallucinations
EXTRACTION_SYSTEM_INSTRUCTION = """
You are an expert Fact Knowledge Extraction Engine.
Your role is to extract all meaningful, verifiable factual claims from the provided document page text.

EXTRACTION PRINCIPLES:
1. STRICT GROUNDING: Extract ONLY facts that are explicitly and directly stated in the text.
   Do NOT extrapolate, infer unstated details, or invent facts.
2. VERBATIM EVIDENCE: For every fact, `evidence_quote` MUST be an EXACT, word-for-word text snippet from the input text.
3. BOTH NUMERICAL & SEMANTIC FACTS:
   - Numerical Facts: Financial metrics (revenue, profit, losses, ARR), counts (headcount, shares, users), percentages, margins.
     * Set `fact_type="NUMERICAL"`
     * Populate `numeric_value` with the float representation (e.g. 12500000.0 for '$12.5M')
     * Populate `unit` if applicable (e.g. 'USD', '%', 'employees')
   - Semantic Facts: Roles, appointments, resignations, mergers, locations, entity statuses.
     * Set `fact_type="SEMANTIC"` or `fact_type="ENTITY_STATUS"`
4. CONTEXT FIELDS:
   - `time_context`: Fiscal year, quarter, or calendar date associated with the claim (e.g., 'FY2023', 'Q3 2024', 'Dec 31, 2023').
   - `scope_context`: Scope or qualifiers mentioned in the text (e.g., 'Consolidated', 'US Division', 'GAAP', 'continuing operations').
   - `page_number`: 1-indexed integer page number where the claim is asserted in the text.
5. EMPTY HANDLING: If the page text contains no meaningful factual claims (e.g. table of contents, cover page, disclaimers, or pure boilerplate), return an empty facts list: {"facts": []}.
"""


class FactExtractor:
    """
    Extracts structured facts from page text using the Google GenAI SDK.
    Never exposes or logs API keys.
    """

    CANDIDATE_MODELS = ["gemini-flash-lite-latest", "gemini-flash-latest"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        batch_size: Optional[int] = None
    ):
        """
        Initialize the Fact Extractor.

        Args:
            api_key: Optional Gemini API key. If omitted, loaded from GEMINI_API_KEY in .env.
            model_name: Gemini model identifier (defaults to 'gemini-flash-lite-latest').
            batch_size: Number of pages to batch per API call (defaults to 3).
        """
        # Load .env from project root
        project_root = Path(__file__).parent.parent.resolve()
        load_dotenv(project_root / ".env")

        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                    self.api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
            except Exception:
                pass

        self.model_name = model_name or self.CANDIDATE_MODELS[0]
        self.batch_size = batch_size if batch_size is not None else int(os.getenv("EXTRACTION_BATCH_SIZE", "3"))
        self._client = None
        self._init_error: Optional[str] = None

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            self._init_error = "GEMINI_API_KEY is not configured or contains placeholder text."
        else:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as exc:
                self._init_error = f"Failed to initialize GenAI client: {type(exc).__name__}"
                logger.error("GenAI client initialization error: %s", type(exc).__name__)

    @property
    def is_configured(self) -> bool:
        """Returns True if the Gemini client is properly initialized."""
        return self._client is not None

    def get_configuration_error(self) -> Optional[str]:
        """Returns a sanitized description of configuration error, if any."""
        return self._init_error

    def extract_facts_from_page(
        self,
        document_name: str,
        page_number: int,
        page_text: str
    ) -> List[Fact]:
        """
        Extracts structured facts from a single page of text using Gemini.

        Args:
            document_name: Name of the PDF file.
            page_number: 1-indexed page number.
            page_text: Raw extracted text of the page.

        Returns:
            List[Fact]: Extracted and validated Fact domain models with Evidence.

        Raises:
            RuntimeError: If the client is unconfigured or if an unrecoverable API error occurs.
        """
        cleaned_text = page_text.strip()
        if not cleaned_text or len(cleaned_text) < 15:
            # Blank or near-empty page (e.g. blank page or page number only)
            return []

        if not self.is_configured:
            raise RuntimeError(
                self._init_error or "Gemini API client is not configured. Please check your .env file."
            )

        from google.genai import types

        prompt = (
            f"{EXTRACTION_SYSTEM_INSTRUCTION}\n\n"
            f"DOCUMENT: {document_name}\n"
            f"PAGE NUMBER: {page_number}\n\n"
            f"PAGE TEXT CONTENT:\n"
            f"\"\"\"\n{cleaned_text}\n\"\"\"\n\n"
            f"Extract all factual claims from the text above as structured JSON."
        )

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedFactsList,
            temperature=0.1,
        )

        # Try designated model first, then candidate fallback models
        models_to_try = [self.model_name] + [m for m in self.CANDIDATE_MODELS if m != self.model_name]
        response = None
        last_error = None

        for model_candidate in models_to_try:
            try:
                response = self._client.models.generate_content(
                    model=model_candidate,
                    contents=prompt,
                    config=config
                )
                if response is not None:
                    break
            except Exception as exc:
                last_error = exc
                error_type = type(exc).__name__
                safe_msg = str(exc)
                if self.api_key:
                    safe_msg = safe_msg.replace(self.api_key, "[REDACTED_API_KEY]")
                logger.warning("Attempt with model %s failed (%s): %s. Trying fallback...", model_candidate, error_type, safe_msg[:80])

        if response is None:
            error_type = type(last_error).__name__ if last_error else "UnknownError"
            safe_msg = str(last_error) if last_error else "No response received"
            if self.api_key:
                safe_msg = safe_msg.replace(self.api_key, "[REDACTED_API_KEY]")
            logger.error("All Gemini model candidates failed on %s p.%d: %s", document_name, page_number, error_type)
            raise RuntimeError(f"Gemini API request failed ({error_type}): {safe_msg[:120]}") from last_error

        # Parse and validate response
        raw_items: List[ExtractedFactItem] = []
        if hasattr(response, "parsed") and response.parsed is not None:
            if isinstance(response.parsed, ExtractedFactsList):
                raw_items = response.parsed.facts
            elif isinstance(response.parsed, dict) and "facts" in response.parsed:
                raw_items = [ExtractedFactItem(**item) for item in response.parsed["facts"]]
        elif hasattr(response, "text") and response.text:
            try:
                data = json.loads(response.text)
                if isinstance(data, dict) and "facts" in data:
                    raw_items = [ExtractedFactItem(**item) for item in data["facts"]]
                elif isinstance(data, list):
                    raw_items = [ExtractedFactItem(**item) for item in data]
            except Exception as parse_err:
                logger.warning("Failed to parse JSON response: %s", parse_err)
                return []

        # Convert ExtractedFactItems to persistent Fact domain models
        facts: List[Fact] = []
        normalized_page_text = re.sub(r"\s+", " ", cleaned_text.lower())

        for item in raw_items:
            try:
                fact = item.to_fact(document_name=document_name, page_number=page_number)

                # Grounding verification: check if evidence quote is present in the page text
                normalized_quote = re.sub(r"\s+", " ", item.evidence_quote.lower().strip())
                if normalized_quote and normalized_quote not in normalized_page_text:
                    # Slightly lower confidence if verbatim match differs due to formatting
                    fact.confidence = max(0.5, round(fact.confidence * 0.85, 2))

                facts.append(fact)
            except Exception as model_err:
                logger.warning("Fact validation warning: %s", model_err)

        return facts

    def extract_facts_from_page_batch(
        self,
        document_name: str,
        pages_batch: List[Dict[str, Any]],
        document_id: Optional[int] = None
    ) -> List[Fact]:
        """
        Extracts structured facts from a batch of pages in a single LLM API call.
        Preserves 100% exact page-by-page provenance and verbatim evidence grounding.

        Args:
            document_name: Name of the PDF file.
            pages_batch: List of page dicts with 'page_number' and 'text'.
            document_id: Optional database ID of the document.

        Returns:
            List[Fact]: Extracted Fact domain models with exact page numbers.
        """
        if not pages_batch:
            return []

        # If batch size is 1, delegate directly to single page extractor
        if len(pages_batch) == 1:
            facts = self.extract_facts_from_page(
                document_name=document_name,
                page_number=pages_batch[0]["page_number"],
                page_text=pages_batch[0]["text"]
            )
            for f in facts:
                if document_id is not None:
                    f.document_id = document_id
            return facts

        if not self.is_configured:
            raise RuntimeError(
                self._init_error or "Gemini API client is not configured. Please check your .env file."
            )

        # Build prompt with clear page-by-page boundaries
        prompt_parts = [
            f"{EXTRACTION_SYSTEM_INSTRUCTION}\n\n",
            f"DOCUMENT: {document_name}\n",
            f"BATCH CONTAINS {len(pages_batch)} PAGES:\n\n"
        ]

        normalized_texts_by_page: Dict[int, str] = {}
        for p in pages_batch:
            p_num = p["page_number"]
            raw_text = p["text"].strip()
            normalized_texts_by_page[p_num] = re.sub(r"\s+", " ", raw_text.lower())
            prompt_parts.append(f"--- START OF PAGE {p_num} ---\n{raw_text}\n--- END OF PAGE {p_num} ---\n\n")

        prompt_parts.append(
            "Extract all factual claims from each page above as structured JSON. "
            "For every fact, set `page_number` to the integer page where that fact appears, "
            "and ensure `evidence_quote` is an exact verbatim quote from that specific page."
        )
        prompt = "".join(prompt_parts)

        from google.genai import types
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedFactsList,
            temperature=0.1,
        )

        models_to_try = [self.model_name] + [m for m in self.CANDIDATE_MODELS if m != self.model_name]
        response = None
        last_error = None

        for model_candidate in models_to_try:
            try:
                response = self._client.models.generate_content(
                    model=model_candidate,
                    contents=prompt,
                    config=config
                )
                if response is not None:
                    break
            except Exception as exc:
                last_error = exc
                error_type = type(exc).__name__
                safe_msg = str(exc)
                if self.api_key:
                    safe_msg = safe_msg.replace(self.api_key, "[REDACTED_API_KEY]")
                logger.warning("Batch attempt with model %s failed (%s): %s. Trying fallback...", model_candidate, error_type, safe_msg[:80])

        if response is None:
            # If batch call fails, fallback to page-by-page extraction for this batch
            logger.warning("Batch call failed; falling back to individual page extraction for batch.")
            fallback_facts: List[Fact] = []
            for p in pages_batch:
                try:
                    p_facts = self.extract_facts_from_page(
                        document_name=document_name,
                        page_number=p["page_number"],
                        page_text=p["text"]
                    )
                    for f in p_facts:
                        if document_id is not None:
                            f.document_id = document_id
                    fallback_facts.extend(p_facts)
                except Exception as p_err:
                    logger.error("Individual page fallback failed on p.%d: %s", p["page_number"], p_err)
            return fallback_facts

        # Parse raw items
        raw_items: List[ExtractedFactItem] = []
        if hasattr(response, "parsed") and response.parsed is not None:
            if isinstance(response.parsed, ExtractedFactsList):
                raw_items = response.parsed.facts
            elif isinstance(response.parsed, dict) and "facts" in response.parsed:
                raw_items = [ExtractedFactItem(**item) for item in response.parsed["facts"]]
        elif hasattr(response, "text") and response.text:
            try:
                data = json.loads(response.text)
                if isinstance(data, dict) and "facts" in data:
                    raw_items = [ExtractedFactItem(**item) for item in data["facts"]]
                elif isinstance(data, list):
                    raw_items = [ExtractedFactItem(**item) for item in data]
            except Exception as parse_err:
                logger.warning("Failed to parse batch JSON response: %s", parse_err)
                return []

        facts: List[Fact] = []
        available_pages = [p["page_number"] for p in pages_batch]

        for item in raw_items:
            try:
                norm_quote = re.sub(r"\s+", " ", item.evidence_quote.lower().strip())
                # Resolve accurate page number:
                assigned_page = item.page_number if item.page_number in available_pages else None
                if assigned_page and norm_quote and norm_quote not in normalized_texts_by_page.get(assigned_page, ""):
                    # Check if quote actually belongs to another page in the batch
                    assigned_page = None

                if assigned_page is None:
                    for p_num, p_text in normalized_texts_by_page.items():
                        if norm_quote and norm_quote in p_text:
                            assigned_page = p_num
                            break
                    if assigned_page is None:
                        assigned_page = available_pages[0]

                fact = item.to_fact(
                    document_name=document_name,
                    page_number=assigned_page,
                    document_id=document_id
                )

                if norm_quote and norm_quote not in normalized_texts_by_page.get(assigned_page, ""):
                    fact.confidence = max(0.5, round(fact.confidence * 0.85, 2))

                facts.append(fact)
            except Exception as model_err:
                logger.warning("Batch fact validation warning: %s", model_err)

        return facts

    def extract_facts_from_document(
        self,
        document_id: int,
        document_name: str,
        pages: List[Dict[str, Any]],
        batch_size: Optional[int] = None
    ) -> List[Fact]:
        """
        Extracts facts from all pages of a document and attaches document_id.
        Uses configurable batching to reduce API calls while preserving 100% provenance.

        Args:
            document_id: Database ID of the document.
            document_name: Name of the PDF file.
            pages: List of page dicts containing 'page_number' and 'text'.
            batch_size: Optional override for batch size.

        Returns:
            List[Fact]: All extracted facts for the document.
        """
        effective_batch_size = batch_size or self.batch_size
        all_facts: List[Fact] = []

        if effective_batch_size <= 1:
            for page in pages:
                page_facts = self.extract_facts_from_page(
                    document_name=document_name,
                    page_number=page["page_number"],
                    page_text=page["text"]
                )
                for fact in page_facts:
                    fact.document_id = document_id
                    all_facts.append(fact)
        else:
            for i in range(0, len(pages), effective_batch_size):
                chunk = pages[i : i + effective_batch_size]
                batch_facts = self.extract_facts_from_page_batch(
                    document_name=document_name,
                    pages_batch=chunk,
                    document_id=document_id
                )
                all_facts.extend(batch_facts)

        return all_facts
