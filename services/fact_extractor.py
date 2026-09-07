"""
Fact Extractor Service (LLM Placeholder)
========================================
This module will be responsible for calling an LLM (such as Google Gemini)
to extract structured numerical and semantic facts from raw page text.

Integration Architecture:
-------------------------
1. Input: Cleaned page text + document metadata (document name, page number).
2. Prompt Strategy:
   - Instruct Gemini to identify core assertions (subject, predicate, object).
   - Demand exact verbatim quotes for the `evidence` block.
   - Extract numerical facts with normalized values and units (e.g., USD, %, FTE).
   - Extract semantic facts (entity statuses, milestones, governance changes).
3. Output: Validated Pydantic `Fact` instances linking back to `Evidence`.

NOTE: LLM integration is deliberately not implemented yet per assignment specification.
The placeholder functions below define the interface for future integration.
"""

from typing import List, Dict, Any, Optional
from models.schemas import Fact, Evidence, FactType


class FactExtractor:
    """Placeholder service for extracting facts using Gemini LLM."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the fact extractor.
        
        Args:
            api_key: Google Gemini API key. When integrating, this will configure
                     the `google.generativeai` or `google-genai` SDK.
        """
        self.api_key = api_key

    def extract_facts_from_page(
        self,
        document_name: str,
        page_number: int,
        page_text: str
    ) -> List[Fact]:
        """
        Extract facts from a single page of text using an LLM.

        Future LLM Implementation Steps:
        --------------------------------
        1. Format a structured prompt containing:
           - Page text and document context.
           - JSON schema requirement matching `models.schemas.Fact`.
           - Constraint: Every fact MUST contain an exact quote present in `page_text`.
        2. Send request to Gemini (e.g. `gemini-1.5-pro` or `gemini-1.5-flash`).
        3. Parse and validate JSON response with Pydantic `Fact` model.
        4. Return the list of extracted Fact objects.

        Args:
            document_name: Name of the PDF file.
            page_number: 1-indexed page number.
            page_text: Extracted text of the page.

        Returns:
            List[Fact]: Extracted facts (currently empty placeholder).
        """
        # Placeholder: No LLM calls executed at this stage.
        # Future Gemini integration will populate this list dynamically.
        return []

    def extract_facts_from_document(
        self,
        document_id: int,
        document_name: str,
        pages: List[Dict[str, Any]]
    ) -> List[Fact]:
        """
        Extract facts across all pages of a document.

        Args:
            document_id: Database ID of the document.
            document_name: Name of the PDF file.
            pages: List of page dictionaries with 'page_number' and 'text'.

        Returns:
            List[Fact]: All extracted facts for the document.
        """
        all_facts: List[Fact] = []
        for page in pages:
            facts = self.extract_facts_from_page(
                document_name=document_name,
                page_number=page["page_number"],
                page_text=page["text"]
            )
            for fact in facts:
                fact.document_id = document_id
                all_facts.append(fact)
        return all_facts
