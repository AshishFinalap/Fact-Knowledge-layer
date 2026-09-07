"""
Fact Knowledge Layer - Streamlit UI
====================================
A clean MVP user interface for:
1. Ingesting multiple PDF documents.
2. Extracting text page-by-page using PyMuPDF.
3. Grounding extracted text in an SQLite database with page provenance.
4. Previewing architecture for downstream LLM Fact Extraction and Cross-Document
   Relationship Reasoning (CORROBORATES, CONTRADICTS, RECONCILES).
"""

import os
import sys
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Ensure local project modules can be imported
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from database.database import Database
from services.pdf_service import PDFService
from services.fact_extractor import FactExtractor
from services.relationship_engine import RelationshipEngine

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Fact Knowledge Layer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
db_path = os.getenv("DATABASE_PATH", "data/fact_knowledge.db")
db = Database(db_path=db_path)


def render_sidebar():
    """Renders the sidebar with statistics, configuration, and controls."""
    st.sidebar.title("📚 Fact Knowledge Layer")
    st.sidebar.caption("VIT 2026 · Engineering Intern Hiring Assignment")
    st.sidebar.divider()

    # Gemini API Key Status (Preparation for LLM integration)
    st.sidebar.subheader("🔑 LLM Configuration")
    env_key = os.getenv("GEMINI_API_KEY", "")
    has_env_key = bool(env_key and env_key != "your_gemini_api_key_here")

    api_key_input = st.sidebar.text_input(
        "Gemini API Key",
        value=env_key if has_env_key else "",
        type="password",
        help="Will be used when LLM extraction is activated."
    )
    if api_key_input:
        st.sidebar.success("API Key detected (ready for Phase 2).")
    else:
        st.sidebar.info("Optional for MVP: PDF extraction works offline.")

    st.sidebar.divider()

    # Database Statistics
    st.sidebar.subheader("📊 Knowledge Layer Stats")
    stats = db.get_stats()
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Documents", stats["documents"])
    col2.metric("Total Pages", stats["pages"])
    col3, col4 = st.sidebar.columns(2)
    col3.metric("Facts", stats["facts"])
    col4.metric("Relationships", stats["relationships"])

    st.sidebar.divider()

    # Reset Action
    if st.sidebar.button("🗑️ Clear Database", help="Deletes all stored documents, pages, and facts"):
        db.clear_all()
        st.sidebar.warning("Database cleared.")
        st.rerun()


def render_upload_tab():
    """Handles PDF file uploading and page-by-page text extraction."""
    st.header("📄 Ingest & Extract PDFs")
    st.write(
        "Upload one or more PDF documents. The system uses **PyMuPDF** to extract text "
        "page-by-page and records document metadata and page text in SQLite."
    )

    uploaded_files = st.file_uploader(
        "Choose PDF files to process",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload multiple documents (e.g. the 3 starter PDFs)."
    )

    if uploaded_files:
        if st.button("🚀 Process & Extract Text", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            total_files = len(uploaded_files)
            for idx, uploaded_file in enumerate(uploaded_files):
                filename = uploaded_file.name
                status_text.text(f"Extracting text from: {filename} ({idx + 1}/{total_files})...")

                try:
                    # 1. Page-by-page extraction via PyMuPDF
                    extraction_result = PDFService.extract_text_page_by_page(
                        uploaded_file,
                        filename=filename
                    )

                    # 2. Store document in SQLite
                    doc_id = db.save_document(
                        filename=extraction_result["filename"],
                        total_pages=extraction_result["total_pages"],
                        file_path=""
                    )

                    # 3. Store individual pages in SQLite
                    db.save_pages(doc_id, extraction_result["pages"])

                except Exception as err:
                    st.error(f"Error processing {filename}: {err}")

                progress_bar.progress((idx + 1) / total_files)

            status_text.empty()
            progress_bar.empty()
            st.success(f"Successfully processed and stored {total_files} document(s)!")
            st.rerun()

    st.divider()

    # Document & Page Viewer
    st.subheader("📑 Inspect Extracted Page Text")
    documents = db.get_documents()

    if not documents:
        st.info("No documents uploaded yet. Upload PDFs above to begin.")
        return

    doc_options = {doc["filename"]: doc["id"] for doc in documents}
    selected_doc_name = st.selectbox("Select document to inspect:", list(doc_options.keys()))
    selected_doc_id = doc_options[selected_doc_name]

    pages = db.get_pages_for_document(selected_doc_id)
    st.write(f"Total Pages: **{len(pages)}**")

    # Optional text search inside document pages
    search_query = st.text_input("🔍 Search within this document's pages:", "")

    for page in pages:
        page_num = page["page_number"]
        page_text = page["text"]
        char_count = page["char_count"]

        if search_query and search_query.lower() not in page_text.lower():
            continue

        with st.expander(f"Page {page_num} ({char_count:,} characters)", expanded=(page_num == 1)):
            if not page_text:
                st.warning("⚠️ No text detected on this page (page might be scanned or image-based).")
            else:
                st.text_area(
                    label=f"Content of Page {page_num}",
                    value=page_text,
                    height=200,
                    key=f"page_text_{selected_doc_id}_{page_num}",
                    disabled=True
                )


def render_facts_tab():
    """Displays facts schema, provenance information, and placeholder for LLM extraction."""
    st.header("🧠 Fact Extraction (LLM Pipeline)")
    st.write(
        "Every fact extracted by the system is linked to its **exact source evidence**, "
        "including document filename, page number, and verbatim quote."
    )

    st.info(
        "💡 **Phase 1 Architecture Status**: LLM fact extraction is intentionally stubbed. "
        "The models and database are fully prepared to receive Gemini API outputs."
    )

    # Display Pydantic Schema Preview
    with st.expander("🔍 View Structured Fact Schema (Pydantic Model)", expanded=False):
        st.code("""
class Fact(BaseModel):
    subject: str               # e.g., 'Total Annual Revenue', 'Jane Doe'
    predicate: str             # e.g., 'reported as', 'holds office of'
    object_value: str          # e.g., '$12.5M', 'Chief Technology Officer'
    fact_type: FactType        # NUMERICAL | SEMANTIC | TEMPORAL | ENTITY_STATUS
    numeric_value: Optional[float]
    unit: Optional[str]        # e.g., 'USD', '%', 'employees'
    time_period: Optional[str] # e.g., 'FY2023', 'Q2 2024'
    context: Optional[str]     # Scope, qualifiers, or accounting basis
    confidence: float
    evidence: Evidence         # Exact source document, page, and verbatim quote
        """, language="python")

    # Show currently stored facts (if any)
    facts = db.get_facts()
    if not facts:
        st.write("---")
        st.subheader("Current Extracted Facts: 0")
        st.caption("Facts will appear here once the Gemini LLM extraction pipeline is executed.")
    else:
        st.dataframe(facts, use_container_width=True)


def render_relationships_tab():
    """Explains and previews the cross-document fact relationship engine."""
    st.header("⚖️ Cross-Document Fact Relationships")
    st.write(
        "The system discovers, compares, and explains relationships between facts across "
        "different documents, categorizing them into three primary relationship types:"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("#### 1. CORROBORATES")
        st.write(
            "The same fact is asserted across multiple documents, even if expressed with different phrasing."
        )
        st.caption("*Example: 'Headcount reached 500' vs '500 active employees on payroll'.*")

    with col2:
        st.error("#### 2. CONTRADICTS")
        st.write(
            "Genuine conflict between facts sharing the same subject, predicate, and temporal/scope context."
        )
        st.caption("*Example: 'Operating profit was $10M' vs 'Operating profit was $2M' for the same period.*")

    with col3:
        st.warning("#### 3. RECONCILES")
        st.write(
            "Facts appear contradictory at first glance, but are reconciled by examining contextual dimensions (time period, scope, units)."
        )
        st.caption("*Example: Differing revenue numbers explained by FY22 vs FY23 periods.*")

    st.divider()
    relationships = db.get_relationships()
    if not relationships:
        st.subheader("Discovered Relationships: 0")
        st.caption("Relationships will be populated here when the Relationship Engine runs.")
    else:
        st.dataframe(relationships, use_container_width=True)


def render_database_tab():
    """Direct explorer for raw SQLite tables."""
    st.header("🗄️ Database Explorer")
    st.write("Inspect records directly from the local SQLite database.")

    tab_docs, tab_pages = st.tabs(["Documents Table", "Pages Table"])

    with tab_docs:
        docs = db.get_documents()
        if docs:
            st.dataframe(docs, use_container_width=True)
        else:
            st.info("No documents in database.")

    with tab_pages:
        docs = db.get_documents()
        if docs:
            selected_doc = st.selectbox(
                "Filter pages by document:",
                [d["filename"] for d in docs],
                key="db_page_filter"
            )
            doc_id = next(d["id"] for d in docs if d["filename"] == selected_doc)
            pages = db.get_pages_for_document(doc_id)
            st.dataframe(pages, use_container_width=True)
        else:
            st.info("No pages in database.")


def main():
    """Main application entry point."""
    render_sidebar()

    st.title("Fact Knowledge Layer")
    st.markdown(
        "A modular system for extracting, grounding, and reasoning over facts across multiple PDF documents."
    )

    # Top-level navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Ingest & Extract",
        "🧠 Extracted Facts",
        "⚖️ Fact Relationships",
        "🗄️ Database Explorer"
    ])

    with tab1:
        render_upload_tab()
    with tab2:
        render_facts_tab()
    with tab3:
        render_relationships_tab()
    with tab4:
        render_database_tab()


if __name__ == "__main__":
    main()
