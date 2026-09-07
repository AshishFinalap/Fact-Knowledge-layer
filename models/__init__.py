"""
Models Package
==============
Defines the Pydantic data schemas representing documents, extracted facts,
source evidence grounding, and cross-document relationships.
"""

from models.schemas import (
    DocumentMetadata,
    DocumentPage,
    Evidence,
    Fact,
    ExtractedFactItem,
    ExtractedFactsList,
    FactRelationship,
    LLMRelationshipEvaluation,
    FactType,
    RelationshipType,
)

__all__ = [
    "DocumentMetadata",
    "DocumentPage",
    "Evidence",
    "Fact",
    "ExtractedFactItem",
    "ExtractedFactsList",
    "FactRelationship",
    "LLMRelationshipEvaluation",
    "FactType",
    "RelationshipType",
]
