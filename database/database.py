"""
SQLite Database Layer
=====================
Provides persistence for:
- Uploaded document records
- Page-by-page extracted text
- Extracted facts and evidence grounding (future LLM integration)
- Cross-document fact relationships (CORROBORATES, CONTRADICTS, RECONCILES)
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Any, Optional
from models.schemas import Fact, FactRelationship, RelationshipType, FactType


class Database:
    """Manages SQLite database connections and CRUD operations."""

    def __init__(self, db_path: str = "data/fact_knowledge.db"):
        self.db_path = db_path
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_db()

    @contextmanager
    def _get_connection(self):
        """Create a connection with row factory enabled and ensure proper closure."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initialize database tables if they do not already exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Documents Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL UNIQUE,
                    total_pages INTEGER NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    file_path TEXT
                )
            """)

            # Document Pages Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    char_count INTEGER NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    UNIQUE(document_id, page_number)
                )
            """)

            # Facts Table (ready for LLM extraction)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    document_name TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object_value TEXT NOT NULL,
                    fact_type TEXT NOT NULL,
                    numeric_value REAL,
                    unit TEXT,
                    time_period TEXT,
                    context TEXT,
                    evidence_quote TEXT NOT NULL,
                    evidence_context TEXT,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)

            # Relationships Table (ready for relationship classification engine)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact_a_id INTEGER NOT NULL,
                    fact_b_id INTEGER NOT NULL,
                    relationship_type TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    reconciliation_context TEXT,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    FOREIGN KEY (fact_a_id) REFERENCES facts(id) ON DELETE CASCADE,
                    FOREIGN KEY (fact_b_id) REFERENCES facts(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    # --------------------------------------------------------------------------
    # Document and Page Operations
    # --------------------------------------------------------------------------

    def save_document(self, filename: str, total_pages: int, file_path: str = "") -> int:
        """
        Insert or update a document record and return its ID.
        """
        uploaded_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documents (filename, total_pages, uploaded_at, file_path)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(filename) DO UPDATE SET
                    total_pages = excluded.total_pages,
                    uploaded_at = excluded.uploaded_at,
                    file_path = excluded.file_path
            """, (filename, total_pages, uploaded_at, file_path))
            conn.commit()
            cursor.execute("SELECT id FROM documents WHERE filename = ?", (filename,))
            row = cursor.fetchone()
            return row["id"] if row else -1

    def save_pages(self, document_id: int, pages: List[Dict[str, Any]]) -> None:
        """
        Save page-by-page text for a document.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for page in pages:
                cursor.execute("""
                    INSERT INTO pages (document_id, page_number, text, char_count)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(document_id, page_number) DO UPDATE SET
                        text = excluded.text,
                        char_count = excluded.char_count
                """, (
                    document_id,
                    page["page_number"],
                    page["text"],
                    page.get("char_count", len(page["text"]))
                ))
            conn.commit()

    def get_documents(self) -> List[Dict[str, Any]]:
        """Retrieve all documents ordered by upload date descending."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_document_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific document by its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_pages_for_document(self, document_id: int) -> List[Dict[str, Any]]:
        """Retrieve all pages for a given document ordered by page number."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM pages WHERE document_id = ? ORDER BY page_number ASC",
                (document_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_page_text(self, document_id: int, page_number: int) -> Optional[str]:
        """Retrieve text for a specific page."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT text FROM pages WHERE document_id = ? AND page_number = ?",
                (document_id, page_number)
            )
            row = cursor.fetchone()
            return row["text"] if row else None

    # --------------------------------------------------------------------------
    # Facts Operations (Ready for LLM Fact Extractor)
    # --------------------------------------------------------------------------

    def save_fact(self, fact: Fact) -> int:
        """
        Store an extracted fact with its evidence grounding.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO facts (
                    document_id, document_name, page_number,
                    subject, predicate, object_value, fact_type,
                    numeric_value, unit, time_period, context,
                    evidence_quote, evidence_context, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fact.document_id,
                fact.document_name,
                fact.page_number,
                fact.subject,
                fact.predicate,
                fact.object_value,
                fact.fact_type.value if hasattr(fact.fact_type, 'value') else str(fact.fact_type),
                fact.numeric_value,
                fact.unit,
                fact.time_period,
                fact.context,
                fact.evidence.quote,
                fact.evidence.context_snippet,
                fact.confidence
            ))
            conn.commit()
            return cursor.lastrowid

    def get_facts(self, document_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve facts, optionally filtered by document_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if document_id is not None:
                cursor.execute("SELECT * FROM facts WHERE document_id = ? ORDER BY page_number ASC", (document_id,))
            else:
                cursor.execute("SELECT * FROM facts ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

    # --------------------------------------------------------------------------
    # Relationships Operations (Ready for Relationship Engine)
    # --------------------------------------------------------------------------

    def save_relationship(self, rel: FactRelationship) -> int:
        """Store a cross-document relationship between two facts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO relationships (
                    fact_a_id, fact_b_id, relationship_type,
                    reasoning, reconciliation_context, confidence
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rel.fact_a_id,
                rel.fact_b_id,
                rel.relationship_type.value if hasattr(rel.relationship_type, 'value') else str(rel.relationship_type),
                rel.reasoning,
                rel.reconciliation_context,
                rel.confidence
            ))
            conn.commit()
            return cursor.lastrowid

    def get_relationships(self) -> List[Dict[str, Any]]:
        """Retrieve all recorded relationships between facts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM relationships ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

    # --------------------------------------------------------------------------
    # Utility Operations
    # --------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, int]:
        """Return counts of stored entities for UI display."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS count FROM documents")
            doc_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) AS count FROM pages")
            page_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) AS count FROM facts")
            fact_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) AS count FROM relationships")
            rel_count = cursor.fetchone()["count"]

            return {
                "documents": doc_count,
                "pages": page_count,
                "facts": fact_count,
                "relationships": rel_count,
            }

    def clear_all(self) -> None:
        """Clear all stored data from tables (useful for reset)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM relationships")
            cursor.execute("DELETE FROM facts")
            cursor.execute("DELETE FROM pages")
            cursor.execute("DELETE FROM documents")
            conn.commit()
