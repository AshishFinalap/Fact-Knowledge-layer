"""
Fact Knowledge Layer - Streamlit UI
====================================
A clean MVP user interface for:
1. Ingesting multiple PDF documents.
2. Extracting text page-by-page using PyMuPDF.
3. Grounding extracted text in an SQLite database with page provenance.
4. Extracting structured numerical and semantic facts using Google Gemini (`google-genai`).
5. Linking every fact to its exact verbatim source quote, document name, and page number.
6. Inspecting extracted facts and previewing cross-document relationships.
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
from services.normalizer import Normalizer
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

# Initialize Database & Services
db_path = os.getenv("DATABASE_PATH", "data/fact_knowledge.db")
db = Database(db_path=db_path)
fact_extractor = FactExtractor()
relationship_engine = RelationshipEngine()


def render_sidebar():
    """Renders the sidebar with statistics, configuration status, and controls."""
    st.sidebar.title("📚 Fact Knowledge Layer")
    st.sidebar.caption("VIT 2026 · Engineering Intern Hiring Assignment")
    st.sidebar.divider()

    # Gemini API Status (Never displays or prints secret keys)
    st.sidebar.subheader("🤖 LLM Engine Status")
    if fact_extractor.is_configured:
        st.sidebar.success("✅ Gemini API Connected")
        st.sidebar.caption(f"Model: `{fact_extractor.model_name}`")
    else:
        st.sidebar.error("⚠️ Gemini API Not Configured")
        err_msg = fact_extractor.get_configuration_error()
        if err_msg:
            st.sidebar.caption(err_msg)

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
    """Handles PDF file uploading, text extraction, and optional LLM fact extraction."""
    st.header("📄 Ingest & Extract PDFs")
    st.write(
        "Upload one or more PDF documents. The system uses **PyMuPDF** to extract text "
        "page-by-page, and uses **Google Gemini** to extract structured facts grounded in exact source quotes."
    )

    uploaded_files = st.file_uploader(
        "Choose PDF files to process",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload multiple documents (e.g. the 3 starter PDFs)."
    )

    # Option to toggle Gemini fact extraction during ingestion
    extract_facts_toggle = st.checkbox(
        "⚡ Extract structured facts using Gemini LLM during ingestion",
        value=fact_extractor.is_configured,
        help="Calls Gemini to extract facts for each page and save them to SQLite.",
        disabled=not fact_extractor.is_configured
    )
    if not fact_extractor.is_configured:
        st.caption("ℹ️ Fact extraction is disabled because `GEMINI_API_KEY` is not configured in `.env`.")

    if uploaded_files:
        if st.button("🚀 Process & Ingest Documents", type="primary"):
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            total_files = len(uploaded_files)
            total_extracted_facts = 0

            for idx, uploaded_file in enumerate(uploaded_files):
                filename = uploaded_file.name
                status_text.text(f"Extracting text from: {filename} (File {idx + 1}/{total_files})...")

                try:
                    # 1. Page-by-page extraction via PyMuPDF
                    extraction_result = PDFService.extract_text_page_by_page(
                        uploaded_file,
                        filename=filename
                    )

                    # 2. Store document metadata in SQLite
                    doc_id = db.save_document(
                        filename=extraction_result["filename"],
                        total_pages=extraction_result["total_pages"],
                        file_path=""
                    )

                    # 3. Store individual pages in SQLite
                    db.save_pages(doc_id, extraction_result["pages"])

                    # 4. Optional: Extract facts via Gemini LLM
                    if extract_facts_toggle and fact_extractor.is_configured:
                        doc_pages = extraction_result["pages"]
                        for p_idx, page_item in enumerate(doc_pages):
                            p_num = page_item["page_number"]
                            status_text.text(
                                f"Extracting facts with Gemini: {filename} (Page {p_num}/{len(doc_pages)})..."
                            )
                            try:
                                page_facts = fact_extractor.extract_facts_from_page(
                                    document_name=filename,
                                    page_number=p_num,
                                    page_text=page_item["text"]
                                )
                                for fact in page_facts:
                                    fact.document_id = doc_id
                                    db.save_fact(fact)
                                    total_extracted_facts += 1
                            except Exception as fact_err:
                                st.warning(f"Note on {filename} (Page {p_num}): {fact_err}")

                except Exception as err:
                    st.error(f"Error processing {filename}: {err}")

                progress_bar.progress((idx + 1) / total_files)

            status_text.empty()
            progress_bar.empty()

            if extract_facts_toggle:
                st.success(
                    f"Successfully processed {total_files} document(s) and extracted {total_extracted_facts} structured fact(s)!"
                )
            else:
                st.success(f"Successfully processed and stored {total_files} document(s) page-by-page!")
            st.rerun()

    st.divider()

    # On-demand extraction for existing documents
    documents = db.get_documents()
    if documents and fact_extractor.is_configured:
        with st.expander("⚡ Run / Re-run Fact Extraction on Stored Documents", expanded=False):
            st.write("Extract facts for documents that are already uploaded in SQLite:")
            selected_doc_for_extract = st.selectbox(
                "Choose document to extract facts from:",
                [d["filename"] for d in documents],
                key="doc_ondemand_select"
            )
            if st.button("Extract Facts for Selected Document"):
                target_doc = next(d for d in documents if d["filename"] == selected_doc_for_extract)
                pages = db.get_pages_for_document(target_doc["id"])
                new_facts_count = 0
                ext_prog = st.progress(0.0)
                ext_status = st.empty()

                for i, page in enumerate(pages):
                    ext_status.text(f"Extracting facts for page {page['page_number']}/{len(pages)}...")
                    try:
                        extracted = fact_extractor.extract_facts_from_page(
                            document_name=target_doc["filename"],
                            page_number=page["page_number"],
                            page_text=page["text"]
                        )
                        for f in extracted:
                            f.document_id = target_doc["id"]
                            db.save_fact(f)
                            new_facts_count += 1
                    except Exception as e:
                        st.warning(f"Page {page['page_number']} issue: {e}")
                    ext_prog.progress((i + 1) / len(pages))

                ext_status.empty()
                ext_prog.empty()
                st.success(f"Extracted {new_facts_count} new facts for '{target_doc['filename']}'!")
                st.rerun()

    # Document & Page Viewer
    st.subheader("📑 Inspect Extracted Page Text")
    if not documents:
        st.info("No documents uploaded yet. Upload PDFs above to begin.")
        return

    doc_options = {doc["filename"]: doc["id"] for doc in documents}
    selected_doc_name = st.selectbox("Select document to inspect:", list(doc_options.keys()))
    selected_doc_id = doc_options[selected_doc_name]

    pages = db.get_pages_for_document(selected_doc_id)
    st.write(f"Total Pages: **{len(pages)}**")

    # Search inside document pages
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
    """Displays extracted structured facts, source evidence grounding, and filters."""
    st.header("🧠 Extracted Facts & Grounded Evidence")
    st.write(
        "Every fact extracted by Gemini is linked to its **exact source evidence**, "
        "including document filename, page number, and verbatim text quote."
    )

    facts = db.get_facts()

    if not facts:
        st.info(
            "No facts extracted yet. Upload PDFs in the 'Ingest & Extract' tab with "
            "'Extract structured facts' enabled, or run on-demand extraction for stored documents."
        )
        # Display Pydantic Schema Preview
        with st.expander("🔍 View Structured Fact Schema (Pydantic Model)", expanded=True):
            st.code("""
class Fact(BaseModel):
    subject: str               # e.g., 'TechCorp', 'Jane Doe'
    predicate: str             # e.g., 'achieved operating income', 'resigned from'
    object_value: str          # e.g., '$45.2 million', 'Chief Technology Officer'
    fact_type: FactType        # NUMERICAL | SEMANTIC | TEMPORAL | ENTITY_STATUS
    numeric_value: Optional[float]
    unit: Optional[str]        # e.g., 'USD', '%', 'employees'
    time_period: Optional[str] # e.g., 'FY2023', 'Q4 2023'
    context: Optional[str]     # Scope or qualifiers (e.g., 'Consolidated', 'US Division')
    confidence: float          # Confidence score (0.0 - 1.0)
    evidence: Evidence         # Exact document name, page number, and verbatim quote
            """, language="python")
        return

    # Metrics Row
    num_facts = sum(1 for f in facts if f.get("fact_type") == "NUMERICAL")
    sem_facts = sum(1 for f in facts if f.get("fact_type") in ("SEMANTIC", "ENTITY_STATUS", "TEMPORAL"))
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Extracted Facts", len(facts))
    m2.metric("Numerical Facts", num_facts)
    m3.metric("Semantic & Status Facts", sem_facts)

    st.divider()

    # Filter Controls
    f_col1, f_col2, f_col3 = st.columns([2, 2, 3])

    docs = db.get_documents()
    doc_filter_options = ["All Documents"] + [d["filename"] for d in docs]
    with f_col1:
        selected_doc_filter = st.selectbox("Filter by Document:", doc_filter_options)

    with f_col2:
        type_filter_options = ["All Types", "NUMERICAL", "SEMANTIC", "ENTITY_STATUS", "TEMPORAL"]
        selected_type_filter = st.selectbox("Filter by Fact Type:", type_filter_options)

    with f_col3:
        search_filter = st.text_input("🔍 Search facts (subject, predicate, value, evidence):", "")

    # Apply Filters
    filtered_facts = []
    for f in facts:
        if selected_doc_filter != "All Documents" and f.get("document_name") != selected_doc_filter:
            continue
        if selected_type_filter != "All Types" and f.get("fact_type") != selected_type_filter:
            continue
        if search_filter:
            q = search_filter.lower()
            searchable = f"{f.get('subject', '')} {f.get('predicate', '')} {f.get('object_value', '')} {f.get('evidence_quote', '')}".lower()
            if q not in searchable:
                continue
        filtered_facts.append(f)

    st.write(f"Showing **{len(filtered_facts)}** of **{len(facts)}** facts:")

    view_mode = st.radio("Display Mode:", ["Card View (Detailed Grounding)", "Table View (Bulk)"], horizontal=True)

    if view_mode == "Table View (Bulk)":
        display_rows = []
        for f in filtered_facts:
            display_rows.append({
                "ID": f["id"],
                "Document": f["document_name"],
                "Page": f["page_number"],
                "Type": f["fact_type"],
                "Subject": f["subject"],
                "Predicate": f["predicate"],
                "Value": f["object_value"],
                "Unit": f.get("unit") or "-",
                "Time Context": f.get("time_period") or "-",
                "Scope Context": f.get("context") or "-",
                "Confidence": f.get("confidence", 1.0),
                "Evidence Quote": f["evidence_quote"],
            })
        st.dataframe(display_rows, width="stretch")
    else:
        # Card View with detailed grounding
        for f in filtered_facts:
            f_type = f.get("fact_type", "SEMANTIC")
            type_color = "blue" if f_type == "NUMERICAL" else "green"

            with st.container(border=True):
                # Header row: Badges
                b_col1, b_col2, b_col3, b_col4 = st.columns([2, 3, 2, 2])
                b_col1.markdown(f"**Fact #{f['id']}** `[{f_type}]`")
                b_col2.markdown(f"📄 **{f['document_name']}**")
                b_col3.markdown(f"📍 **Page {f['page_number']}**")
                conf = f.get("confidence", 1.0)
                b_col4.markdown(f"🎯 **Confidence: {int(conf * 100)}%**")

                # Triple Representation
                st.markdown(
                    f"### **{f['subject']}** *{f['predicate']}* `{f['object_value']}`"
                )

                # Context & Metadata row
                tags = []
                if f.get("unit"):
                    tags.append(f"**Unit**: {f['unit']}")
                if f.get("time_period"):
                    tags.append(f"**Time Context**: {f['time_period']}")
                if f.get("context"):
                    tags.append(f"**Scope Context**: {f['context']}")

                if tags:
                    st.caption(" | ".join(tags))

                # Exact Grounding Quote
                st.markdown(
                    f"> ❝ *{f['evidence_quote']}* ❞"
                )


def render_relationships_tab():
    """Explains and inspects cross-document fact relationships (CORROBORATES, CONTRADICTS, RECONCILES)."""
    st.header("⚖️ Cross-Document Fact Relationships")
    st.write(
        "Discovers, compares, and explains relationships between facts across different documents, "
        "using deterministic normalizers and Gemini reasoning for ambiguous cases."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("#### 1. CORROBORATES")
        st.caption("Same fact confirmed across documents, even if expressed with different wording.")

    with col2:
        st.error("#### 2. CONTRADICTS")
        st.caption("Direct conflict under identical subject, predicate, timeframe, and scope.")

    with col3:
        st.warning("#### 3. RECONCILES")
        st.caption("Differences resolved by context: time periods, reporting scopes, or measurement units.")

    st.divider()

    # Trigger Relationship Analysis Across Documents
    all_facts = db.get_fact_models()
    docs = db.get_documents()

    if len(docs) < 2:
        st.info("ℹ️ Upload and extract at least two different documents to discover cross-document relationships.")
    btn_col1, btn_col2 = st.columns([3, 1])
    with btn_col1:
        cross_doc_only = st.checkbox(
            "Compare across different documents only (Recommended)",
            value=True,
            help="When checked, pairs facts originating from different PDF files. When unchecked, also compares sections across different pages of documents."
        )
        if st.button("🔍 Analyze Relationships Across Documents", type="primary"):
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            status_text.text(f"Scanning {len(all_facts)} facts for candidate pairs...")
            candidate_pairs = Normalizer.find_candidate_pairs(
                all_facts,
                max_candidates=150,
                prefer_cross_document=cross_doc_only
            )

            if not candidate_pairs:
                status_text.empty()
                progress_bar.empty()
                st.warning(
                    f"Analyzed {len(all_facts)} facts across {len(docs)} documents. "
                    "No candidate pairs met the topical relevance threshold. "
                    "(Ensure uploaded documents discuss common entities or industry topics)."
                )
            else:
                status_text.text(f"Evaluating {len(candidate_pairs)} candidate pair(s)...")

                def update_progress(curr, total):
                    progress_bar.progress(curr / total)
                    status_text.text(f"Evaluating pair {curr}/{total}...")

                confirmed_relationships = relationship_engine.evaluate_relationships(
                    candidate_pairs,
                    progress_callback=update_progress
                )

                saved_count = 0
                for rel in confirmed_relationships:
                    db.save_relationship(rel)
                    saved_count += 1

                status_text.empty()
                progress_bar.empty()
                st.success(
                    f"Analysis complete! Discovered {saved_count} cross-document relationship(s) from {len(candidate_pairs)} candidate pair(s)."
                )
                st.rerun()

        with btn_col2:
            if st.button("🗑️ Clear Relationships"):
                db.clear_relationships()
                st.warning("Relationships cleared.")
                st.rerun()

    # Display Recorded Relationships
    detailed_rels = db.get_detailed_relationships()

    if not detailed_rels:
        st.subheader("Discovered Relationships: 0")
        st.caption("Click 'Analyze Relationships Across Documents' above to run cross-document comparison.")
        return

    # Metrics Summary
    total_rel_count = len(detailed_rels)
    corroborate_count = sum(1 for r in detailed_rels if r["relationship_type"] == "CORROBORATES")
    contradict_count = sum(1 for r in detailed_rels if r["relationship_type"] == "CONTRADICTS")
    reconcile_count = sum(1 for r in detailed_rels if r["relationship_type"] == "RECONCILES")

    rm1, rm2, rm3, rm4 = st.columns(4)
    rm1.metric("Total Relationships", total_rel_count)
    rm2.metric("Corroborates", corroborate_count)
    rm3.metric("Contradicts", contradict_count)
    rm4.metric("Reconciles", reconcile_count)

    st.divider()

    # Filter Controls
    rf_col1, rf_col2 = st.columns([2, 3])
    with rf_col1:
        rel_type_filter = st.selectbox(
            "Filter by Relationship Type:",
            ["All", "CORROBORATES", "CONTRADICTS", "RECONCILES"]
        )
    with rf_col2:
        rel_search = st.text_input("🔍 Search relationships (subject, value, reasoning):", "")

    # Apply Filters
    filtered_rels = []
    for r in detailed_rels:
        if rel_type_filter != "All" and r["relationship_type"] != rel_type_filter:
            continue
        if rel_search:
            q = rel_search.lower()
            text_corpus = f"{r['fact_a_subject']} {r['fact_b_subject']} {r['fact_a_value']} {r['fact_b_value']} {r['reasoning']}".lower()
            if q not in text_corpus:
                continue
        filtered_rels.append(r)

    st.write(f"Showing **{len(filtered_rels)}** of **{len(detailed_rels)}** relationships:")

    # Render Side-by-Side Comparison Cards
    for rel in filtered_rels:
        rel_type = rel["relationship_type"]

        # Color-coded badge
        if rel_type == "CORROBORATES":
            type_badge = "🟢 **CORROBORATES**"
        elif rel_type == "CONTRADICTS":
            type_badge = "🔴 **CONTRADICTS**"
        else:
            type_badge = "🟠 **RECONCILES**"

        with st.container(border=True):
            # Header Row
            hdr_col1, hdr_col2, hdr_col3 = st.columns([3, 2, 3])
            hdr_col1.markdown(f"### {type_badge}")
            conf_pct = int(rel.get("confidence", 1.0) * 100)
            hdr_col2.markdown(f"🎯 **Confidence: {conf_pct}%**")
            if rel.get("reconciliation_context"):
                hdr_col3.info(f"Context: {rel['reconciliation_context']}")

            st.divider()

            # Side-by-Side Comparison Columns
            fact_col_a, fact_col_b = st.columns(2)

            # Fact A
            with fact_col_a:
                st.markdown(f"#### 📄 Fact A (ID #{rel['fact_a_id']})")
                st.caption(f"**Document**: `{rel['fact_a_document']}` | **Page**: {rel['fact_a_page']}")
                st.markdown(f"**Subject:** {rel['fact_a_subject']}")
                st.markdown(f"**Predicate:** *{rel['fact_a_predicate']}*")
                st.markdown(f"**Value:** `{rel['fact_a_value']}`")

                tags_a = []
                if rel.get("fact_a_unit"):
                    tags_a.append(f"Unit: {rel['fact_a_unit']}")
                if rel.get("fact_a_time"):
                    tags_a.append(f"Time: {rel['fact_a_time']}")
                if rel.get("fact_a_context"):
                    tags_a.append(f"Scope: {rel['fact_a_context']}")
                if tags_a:
                    st.caption(" | ".join(tags_a))

                st.markdown(f"> ❝ *{rel['fact_a_evidence']}* ❞")

            # Fact B
            with fact_col_b:
                st.markdown(f"#### 📄 Fact B (ID #{rel['fact_b_id']})")
                st.caption(f"**Document**: `{rel['fact_b_document']}` | **Page**: {rel['fact_b_page']}")
                st.markdown(f"**Subject:** {rel['fact_b_subject']}")
                st.markdown(f"**Predicate:** *{rel['fact_b_predicate']}*")
                st.markdown(f"**Value:** `{rel['fact_b_value']}`")

                tags_b = []
                if rel.get("fact_b_unit"):
                    tags_b.append(f"Unit: {rel['fact_b_unit']}")
                if rel.get("fact_b_time"):
                    tags_b.append(f"Time: {rel['fact_b_time']}")
                if rel.get("fact_b_context"):
                    tags_b.append(f"Scope: {rel['fact_b_context']}")
                if tags_b:
                    st.caption(" | ".join(tags_b))

                st.markdown(f"> ❝ *{rel['fact_b_evidence']}* ❞")

            st.divider()

            # Reasoning Explanation
            st.markdown(f"💡 **Reasoning:** {rel['reasoning']}")


def render_database_tab():
    """Direct explorer for raw SQLite tables."""
    st.header("🗄️ Database Explorer")
    st.write("Inspect records directly from the local SQLite database.")

    tab_docs, tab_pages, tab_facts = st.tabs(["Documents Table", "Pages Table", "Facts Table"])

    with tab_docs:
        docs = db.get_documents()
        if docs:
            st.dataframe(docs, width="stretch")
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
            st.dataframe(pages, width="stretch")
        else:
            st.info("No pages in database.")

    with tab_facts:
        facts = db.get_facts()
        if facts:
            st.dataframe(facts, width="stretch")
        else:
            st.info("No facts in database.")


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
