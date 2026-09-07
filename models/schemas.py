"""
Data Schemas for Fact Knowledge Layer
======================================
Defines Pydantic models for:
- Document and page metadata
- Exact source evidence grounding
- Structured facts (numerical and semantic)
- Cross-document relationship classifications (CORROBORATES, CONTRADICTS, RECONCILES)
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class FactType(str, Enum):
    """Classification of the nature of an extracted fact."""
    NUMERICAL = "NUMERICAL"       # e.g., Financial figures, counts, percentages, metrics
    SEMANTIC = "SEMANTIC"         # e.g., Statements, descriptions, qualitative assertions
    TEMPORAL = "TEMPORAL"         # e.g., Dates, tenure, effective periods, milestones
    ENTITY_STATUS = "ENTITY_STATUS" # e.g., Active director, resigned, incorporated


class RelationshipType(str, Enum):
    """
    Cross-document relationship types defined for the assignment:
    - CORROBORATES: Same fact expressed differently across documents.
    - CONTRADICTS: Same subject/predicate/context but with conflicting values.
    - RECONCILES: Facts appear contradictory but can be explained by context (e.g. time period, scope, units).
    """
    CORROBORATES = "CORROBORATES"
    CONTRADICTS = "CONTRADICTS"
    RECONCILES = "RECONCILES"


class Evidence(BaseModel):
    """
    Source grounding for an extracted fact.
    Every fact must trace back to its exact evidence in the source document.
    """
    document_name: str = Field(..., description="Name of the source PDF document.")
    page_number: int = Field(..., description="1-indexed page number where the fact appears.")
    quote: str = Field(..., description="Exact verbatim text snippet from the document page supporting this fact.")
    context_snippet: Optional[str] = Field(
        default=None,
        description="Surrounding paragraph or sentence providing contextual scope."
    )


class Fact(BaseModel):
    """
    Structured representation of an extracted fact.
    Can represent numerical, semantic, or entity-state information with full provenance.
    """
    id: Optional[int] = Field(default=None, description="Unique identifier for the fact in storage.")
    document_id: Optional[int] = Field(default=None, description="Foreign key to the source document.")
    document_name: str = Field(..., description="Name of the source document.")
    page_number: int = Field(..., description="Source page number.")
    
    # Core semantic triple representation
    subject: str = Field(..., description="Entity or topic the fact is about (e.g., 'Acme Corp Revenue', 'John Doe').")
    predicate: str = Field(..., description="Attribute or relationship (e.g., 'reported annual revenue of', 'held position of').")
    object_value: str = Field(..., description="Raw or formatted value (e.g., '$10.5 million', 'Director').")
    
    # Optional normalized attributes
    fact_type: FactType = Field(default=FactType.SEMANTIC, description="Type of fact (numerical, semantic, etc.).")
    numeric_value: Optional[float] = Field(default=None, description="Normalized numeric value if applicable.")
    unit: Optional[str] = Field(default=None, description="Unit of measurement (e.g., 'USD', '%', 'employees').")
    time_period: Optional[str] = Field(default=None, description="Applicable timeframe (e.g., 'FY2023', 'Q1 2024').")
    context: Optional[str] = Field(default=None, description="Qualifying context, scope, or accounting standard.")
    
    # Grounding & confidence
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score.")
    evidence: Evidence = Field(..., description="Exact source grounding supporting this fact.")


class FactRelationship(BaseModel):
    """
    Comparison relationship identified between two facts across documents.
    """
    id: Optional[int] = Field(default=None, description="Unique identifier for the relationship record.")
    fact_a_id: int = Field(..., description="ID of the first fact being compared.")
    fact_b_id: int = Field(..., description="ID of the second fact being compared.")
    relationship_type: RelationshipType = Field(
        ...,
        description="Classification: CORROBORATES, CONTRADICTS, or RECONCILES."
    )
    reasoning: str = Field(
        ...,
        description="System's reasoning explaining why the relationship holds based on evidence."
    )
    reconciliation_context: Optional[str] = Field(
        default=None,
        description="For RECONCILES: The specific dimension (e.g., time period, scope, units) that reconciles them."
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the relationship assessment.")


class DocumentMetadata(BaseModel):
    """Metadata for an uploaded document."""
    id: Optional[int] = None
    filename: str
    total_pages: int
    uploaded_at: Optional[str] = None
    file_path: Optional[str] = None


class DocumentPage(BaseModel):
    """Extracted text and metadata for a single page of a document."""
    id: Optional[int] = None
    document_id: int
    page_number: int
    text: str
    char_count: int
