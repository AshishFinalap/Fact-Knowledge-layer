"""
Fact Knowledge Layer - Enterprise Intelligence & Semantic Reasoning
====================================================================
Production-grade user interface for:
1. Multi-document PDF ingestion with page-level spatial provenance (PyMuPDF).
2. Verifiable fact extraction with structured Gemini LLM schemas.
3. Exact verbatim quote evidence linking and document citations.
4. Deterministic metric canonicalization and financial unit scaling (1 Cr = 10 M).
5. Cross-document relationship reasoning (CORROBORATES, CONTRADICTS, RECONCILES).
6. Failure mode analysis and interactive edge-case verification.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Ensure local project root is discoverable
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from database.database import Database
from services.pdf_service import PDFService
from services.fact_extractor import FactExtractor
from services.normalizer import Normalizer
from services.relationship_engine import RelationshipEngine
from models.schemas import Fact, Evidence, FactType, RelationshipType
from ui.styles import CUSTOM_CSS
from ui.components import (
    render_hero_banner,
    render_kpi_card,
    render_fact_card_html,
    render_relationship_card_html,
    render_failure_case_study_html
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Fact Knowledge Layer | Enterprise Semantic Graph",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom modern CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Database & Services
db_path = os.getenv("DATABASE_PATH", "data/fact_knowledge.db")
db = Database(db_path=db_path)
fact_extractor = FactExtractor()
relationship_engine = RelationshipEngine()


def render_sidebar():
    """Renders the high-tech sidebar with statistics, configuration status, and controls."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 10px 0 16px 0;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #818cf8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px;">
                    ENTERPRISE AI LAYER
                </div>
                <h2 style="margin: 0; font-size: 1.45rem; font-weight: 800; color: #ffffff;">
                    🧠 Fact Knowledge
                </h2>
                <div style="font-size: 0.8rem; color: #94a3b8;">
                    Cross-Document Verifiable Reasoning
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        # Engine Status
        st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #cbd5e1; text-transform: uppercase; margin-bottom: 8px;'>🤖 Extraction Engine</div>", unsafe_allow_html=True)
        if fact_extractor.is_configured:
            st.markdown(
                f"""
                <div style="background: rgba(16, 185, 129, 0.10); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 10px 12px; margin-bottom: 12px;">
                    <div style="display:flex; align-items:center; gap:8px; font-weight:600; font-size:0.85rem; color:#10b981;">
                        <span class="pulse-dot"></span> Gemini API Connected
                    </div>
                    <div style="font-size:0.75rem; color:#94a3b8; margin-top:4px; font-family:var(--font-mono);">
                        Model: {fact_extractor.model_name}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="background: rgba(239, 68, 68, 0.10); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 10px 12px; margin-bottom: 12px;">
                    <div style="display:flex; align-items:center; gap:8px; font-weight:600; font-size:0.85rem; color:#f87171;">
                        ⚠️ Gemini API Offline
                    </div>
                    <div style="font-size:0.75rem; color:#94a3b8; margin-top:4px;">
                        Configure <code>GEMINI_API_KEY</code> in <code>.env</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Normalizer / Reasoner Status
        st.markdown(
            """
            <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 8px; padding: 10px 12px; margin-bottom: 16px;">
                <div style="font-size:0.75rem; font-weight:600; color:#a5b4fc; text-transform:uppercase;">
                    ⚖️ Strict Reasoning Engine
                </div>
                <div style="font-size:0.78rem; color:#cbd5e1; margin-top:4px;">
                    Strict Metric Equality & Unit Scaling Active (1 Cr = 10 M = 100 L)
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        # Knowledge Stats
        st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #cbd5e1; text-transform: uppercase; margin-bottom: 10px;'>📊 Knowledge Base Stats</div>", unsafe_allow_html=True)
        stats = db.get_stats()
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Documents", stats["documents"])
            st.metric("Facts", stats["facts"])
        with c2:
            st.metric("Pages", stats["pages"])
            st.metric("Relations", stats["relationships"])

        st.divider()

        # Database Controls
        st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #cbd5e1; text-transform: uppercase; margin-bottom: 8px;'>⚙️ Quick Actions</div>", unsafe_allow_html=True)
        if st.button("🗑️ Reset All Stored Data", use_container_width=True, help="Deletes all stored documents, pages, facts, and relationships"):
            db.clear_all()
            st.toast("Database cleared successfully.", icon="🧹")
            st.rerun()

        st.markdown(
            """
            <div style="margin-top: 24px; font-size: 0.72rem; color: #64748b; line-height: 1.4;">
                Superjoin VIT 2026 Engineering Assignment<br>
                Modular Fact Knowledge Layer MVP
            </div>
            """,
            unsafe_allow_html=True
        )


def render_kpi_ribbon():
    """Renders the top summary KPI metric cards."""
    stats = db.get_stats()
    facts = db.get_facts()
    detailed_rels = db.get_detailed_relationships()

    num_facts = sum(1 for f in facts if f.get("fact_type") == "NUMERICAL")
    sem_facts = len(facts) - num_facts

    corrob_count = sum(1 for r in detailed_rels if r["relationship_type"] == "CORROBORATES")
    contra_count = sum(1 for r in detailed_rels if r["relationship_type"] == "CONTRADICTS")
    reconc_count = sum(1 for r in detailed_rels if r["relationship_type"] == "RECONCILES")

    html_ribbon = f"""
    <div class="kpi-container">
        {render_kpi_card("Indexed Documents", stats["documents"], f"{stats['pages']} total pages processed", "📄")}
        {render_kpi_card("Extracted Facts", stats["facts"], f"{num_facts} numerical · {sem_facts} semantic", "🧠")}
        {render_kpi_card("Corroborations", corrob_count, "Cross-document verified agreement", "🟢")}
        {render_kpi_card("Contradictions", contra_count, "Conflicting values under same scope", "🔴")}
        {render_kpi_card("Reconciliations", reconc_count, "Explained by time, scope, or units", "🟠")}
    </div>
    """
    st.markdown(html_ribbon, unsafe_allow_html=True)


def render_upload_tab():
    """Tab 1: PDF Ingestion, PyMuPDF page-by-page extraction, and Gemini fact structuring."""
    st.markdown("### 📄 Document Ingestion & Extraction Pipeline")
    st.markdown(
        "Upload corporate filings, prospectuses, or earnings releases. "
        "The pipeline performs **exact page-by-page text extraction via PyMuPDF**, "
        "grounds each page with verifiable page indexes, and extracts structured facts with Gemini."
    )

    # Visual Pipeline Stepper
    st.markdown(
        """
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px 18px; margin-bottom: 20px;">
            <div style="font-size: 0.75rem; font-weight: 700; color: #818cf8; text-transform: uppercase; margin-bottom: 8px;">
                Pipeline Architecture Flow
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; font-size: 0.8rem; color: #cbd5e1;">
                <div><b>1. Ingest PDF</b> (Streamlit Uploader)</div>
                <div style="color: #6366f1;">➔</div>
                <div><b>2. PyMuPDF Parsing</b> (Page Text & Provenance)</div>
                <div style="color: #6366f1;">➔</div>
                <div><b>3. SQLite Storage</b> (Pages & Documents)</div>
                <div style="color: #6366f1;">➔</div>
                <div><b>4. Gemini Extraction</b> (Typed Facts & Quotes)</div>
                <div style="color: #6366f1;">➔</div>
                <div><b>5. Reasoning Engine</b> (Cross-Doc Graph)</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_up1, col_up2 = st.columns([3, 2])

    with col_up1:
        uploaded_files = st.file_uploader(
            "Upload Disclosures / Reports (PDF format):",
            type=["pdf"],
            accept_multiple_files=True,
            help="Select one or multiple PDF filings (e.g. IPO Prospectus, Annual Report, Earnings Presentation)."
        )

        extract_facts_toggle = st.checkbox(
            "⚡ Extract structured facts using Gemini LLM during ingestion",
            value=fact_extractor.is_configured,
            help="Invokes Gemini to extract facts for each page and link verbatim quotes.",
            disabled=not fact_extractor.is_configured
        )

        if not fact_extractor.is_configured:
            st.info("ℹ️ Gemini LLM is offline. Page text will be extracted via PyMuPDF and stored in SQLite.")

        if uploaded_files:
            if st.button("🚀 Ingest & Process Documents", type="primary", use_container_width=True):
                progress_bar = st.progress(0.0)
                status_box = st.empty()

                total_files = len(uploaded_files)
                total_new_facts = 0

                for idx, uploaded_file in enumerate(uploaded_files):
                    filename = uploaded_file.name
                    status_box.markdown(f"**Step 1/2: Extracting text from `{filename}` (File {idx + 1}/{total_files})...**")

                    try:
                        # 1. PyMuPDF Page-by-page Extraction
                        extraction_result = PDFService.extract_text_page_by_page(
                            uploaded_file,
                            filename=filename
                        )

                        # 2. Store Document Metadata
                        doc_id = db.save_document(
                            filename=extraction_result["filename"],
                            total_pages=extraction_result["total_pages"],
                            file_path=""
                        )

                        # 3. Store Pages in SQLite
                        db.save_pages(doc_id, extraction_result["pages"])

                        # 4. Gemini Structured Fact Extraction (Configurable Batching)
                        if extract_facts_toggle and fact_extractor.is_configured:
                            doc_pages = extraction_result["pages"]
                            batch_size = max(1, fact_extractor.batch_size)
                            for chunk_start in range(0, len(doc_pages), batch_size):
                                chunk = doc_pages[chunk_start : chunk_start + batch_size]
                                p_label = f"Page {chunk[0]['page_number']}" if len(chunk) == 1 else f"Pages {chunk[0]['page_number']}–{chunk[-1]['page_number']}"
                                status_box.markdown(
                                    f"**Step 2/2: Extracting facts via Gemini for `{filename}` ({p_label} of {len(doc_pages)})...**"
                                )
                                try:
                                    batch_facts = fact_extractor.extract_facts_from_page_batch(
                                        document_name=filename,
                                        pages_batch=chunk,
                                        document_id=doc_id
                                    )
                                    for fact in batch_facts:
                                        db.save_fact(fact)
                                        total_new_facts += 1
                                except Exception as p_err:
                                    st.caption(f"Note on {filename} ({p_label}): {p_err}")

                    except Exception as err:
                        st.error(f"Error processing {filename}: {err}")

                    progress_bar.progress((idx + 1) / total_files)

                status_box.empty()
                progress_bar.empty()

                if extract_facts_toggle:
                    st.success(f"✅ Successfully ingested {total_files} document(s) and extracted {total_new_facts} structured facts!")
                else:
                    st.success(f"✅ Successfully ingested and indexed {total_files} document(s) page-by-page!")
                st.rerun()

    with col_up2:
        st.markdown("#### ⚡ On-Demand Extraction")
        documents = db.get_documents()
        if documents and fact_extractor.is_configured:
            st.write("Run Gemini extraction for documents already stored in SQLite:")
            selected_doc_for_extract = st.selectbox(
                "Select stored document:",
                [d["filename"] for d in documents],
                key="doc_ondemand_select"
            )
            if st.button("Extract Facts for Selected Document", use_container_width=True):
                target_doc = next(d for d in documents if d["filename"] == selected_doc_for_extract)
                pages = db.get_pages_for_document(target_doc["id"])
                new_facts_count = 0
                ext_prog = st.progress(0.0)
                ext_status = st.empty()

                batch_size = max(1, fact_extractor.batch_size)
                for i in range(0, len(pages), batch_size):
                    chunk = pages[i : i + batch_size]
                    p_label = f"page {chunk[0]['page_number']}" if len(chunk) == 1 else f"pages {chunk[0]['page_number']}–{chunk[-1]['page_number']}"
                    ext_status.text(f"Extracting facts for {p_label} of {len(pages)}...")
                    try:
                        extracted = fact_extractor.extract_facts_from_page_batch(
                            document_name=target_doc["filename"],
                            pages_batch=chunk,
                            document_id=target_doc["id"]
                        )
                        for f in extracted:
                            db.save_fact(f)
                            new_facts_count += 1
                    except Exception as e:
                        st.caption(f"Pages {p_label} issue: {e}")
                    ext_prog.progress(min(1.0, (i + len(chunk)) / len(pages)))

                ext_status.empty()
                ext_prog.empty()
                st.success(f"Extracted {new_facts_count} new facts for '{target_doc['filename']}'!")
                st.rerun()
        elif not documents:
            st.info("No documents stored yet. Upload PDFs using the panel on the left.")

    st.divider()

    # Document & Page Text Inspector
    st.markdown("### 📑 Verified Page Text Inspector")
    if not documents:
        st.caption("Upload documents to inspect page-by-page text extractions.")
        return

    doc_options = {doc["filename"]: doc["id"] for doc in documents}
    s_col1, s_col2 = st.columns([2, 3])
    with s_col1:
        selected_doc_name = st.selectbox("Document to inspect:", list(doc_options.keys()), key="inspect_doc_select")
        selected_doc_id = doc_options[selected_doc_name]
        pages = db.get_pages_for_document(selected_doc_id)
        st.caption(f"Indexed Pages: **{len(pages)}**")

    with s_col2:
        search_query = st.text_input("🔍 Search within pages:", "", placeholder="e.g. revenue, ebitda, promoter, pin codes")

    for page in pages:
        page_num = page["page_number"]
        page_text = page["text"]
        char_count = page["char_count"]

        if search_query and search_query.lower() not in page_text.lower():
            continue

        with st.expander(f"📍 Page {page_num} ({char_count:,} characters)", expanded=(page_num == 1 and not search_query)):
            if not page_text:
                st.warning("⚠️ No text detected on this page (page may be image-only).")
            else:
                st.text_area(
                    label=f"Text content of Page {page_num}",
                    value=page_text,
                    height=180,
                    key=f"page_text_{selected_doc_id}_{page_num}",
                    disabled=True
                )


def render_facts_tab():
    """Tab 2: Extracted Facts & Exact Grounding Evidence."""
    st.markdown("### 🧠 Extracted Facts & Grounded Evidence")
    st.markdown(
        "Every fact is represented as a structured semantic claim `(Subject, Predicate, Value)` "
        "and is **rigorously linked to its exact verbatim source evidence**, including document name, page number, and text quote."
    )

    facts = db.get_facts()
    if not facts:
        st.info("No facts extracted yet. Upload PDFs in the Ingest tab with fact extraction enabled.")
        return

    # Filter Controls Bar
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 3, 2])

    docs = db.get_documents()
    doc_filter_options = ["All Documents"] + [d["filename"] for d in docs]
    with f_col1:
        selected_doc = st.selectbox("Filter Document:", doc_filter_options, key="fact_filter_doc")

    with f_col2:
        type_options = ["All Types", "NUMERICAL", "SEMANTIC", "ENTITY_STATUS", "TEMPORAL"]
        selected_type = st.selectbox("Filter Fact Type:", type_options, key="fact_filter_type")

    with f_col3:
        search_kw = st.text_input("🔍 Search facts:", "", placeholder="Filter by subject, predicate, or value...", key="fact_search_input")

    with f_col4:
        display_mode = st.radio("View Mode:", ["Cards", "Table"], horizontal=True, key="fact_display_mode")

    # Filter Application
    filtered = []
    for f in facts:
        if selected_doc != "All Documents" and f.get("document_name") != selected_doc:
            continue
        if selected_type != "All Types" and f.get("fact_type") != selected_type:
            continue
        if search_kw:
            q = search_kw.lower()
            text_corpus = f"{f.get('subject', '')} {f.get('predicate', '')} {f.get('object_value', '')} {f.get('evidence_quote', '')}".lower()
            if q not in text_corpus:
                continue
        filtered.append(f)

    st.markdown(f"<div style='font-size: 0.85rem; color: #94a3b8; margin: 12px 0;'>Showing <b>{len(filtered)}</b> of <b>{len(facts)}</b> facts:</div>", unsafe_allow_html=True)

    if display_mode == "Table":
        df_data = []
        for f in filtered:
            df_data.append({
                "ID": f["id"],
                "Document": f["document_name"],
                "Page": f["page_number"],
                "Type": f["fact_type"],
                "Subject": f["subject"],
                "Predicate": f["predicate"],
                "Value": f["object_value"],
                "Unit": f.get("unit") or "-",
                "Time Context": f.get("time_period") or "-",
                "Scope": f.get("context") or "-",
                "Evidence Quote": f["evidence_quote"]
            })
        st.dataframe(df_data, use_container_width=True)
    else:
        # Render clean cards with pagination
        page_size = 25
        total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
        if total_pages > 1:
            p_col1, p_col2 = st.columns([1, 4])
            with p_col1:
                fact_page = st.number_input("Page:", min_value=1, max_value=total_pages, value=1, step=1, key="fact_page_num")
            with p_col2:
                st.markdown(f"<div style='padding-top:8px; font-size:0.82rem; color:#94a3b8;'>Showing items {(fact_page - 1) * page_size + 1}–{min(fact_page * page_size, len(filtered))} of {len(filtered)} facts</div>", unsafe_allow_html=True)
            start_idx = (fact_page - 1) * page_size
            page_items = filtered[start_idx : start_idx + page_size]
        else:
            page_items = filtered

        for fact in page_items:
            st.markdown(render_fact_card_html(fact), unsafe_allow_html=True)


def render_relationships_tab():
    """Tab 3: Cross-Document Fact Relationship Discovery & Reasoning."""
    st.markdown("### ⚖️ Cross-Document Fact Reasoning & Relationships")
    st.markdown(
        "Automatically identifies, compares, and explains relationships across documents using "
        "**strict canonical metric matching**, **predicate polarity checks**, and **financial unit scaling**."
    )

    # Relationship Category Definitions Card
    st.markdown(
        """
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-bottom: 20px;">
            <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 10px; padding: 14px 16px;">
                <div style="font-weight: 700; color: #10b981; font-size: 0.9rem; margin-bottom: 4px;">🟢 1. CORROBORATES</div>
                <div style="font-size: 0.78rem; color: #cbd5e1; line-height: 1.4;">
                    Identical metric and timeframe asserted across documents with consistent values (accounting for unit scaling).
                </div>
            </div>
            <div style="background: rgba(244, 63, 94, 0.08); border: 1px solid rgba(244, 63, 94, 0.25); border-radius: 10px; padding: 14px 16px;">
                <div style="font-weight: 700; color: #f43f5e; font-size: 0.9rem; margin-bottom: 4px;">🔴 2. CONTRADICTS</div>
                <div style="font-size: 0.78rem; color: #cbd5e1; line-height: 1.4;">
                    Direct conflict where both documents describe the exact same metric and timeframe, but assert mutually exclusive values.
                </div>
            </div>
            <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 10px; padding: 14px 16px;">
                <div style="font-weight: 700; color: #f59e0b; font-size: 0.9rem; margin-bottom: 4px;">🟠 3. RECONCILES</div>
                <div style="font-size: 0.78rem; color: #cbd5e1; line-height: 1.4;">
                    Same metric with divergent values explained by context dimensions: <b>time period difference</b> or <b>reporting scope</b>.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Action Toolbar
    all_facts = db.get_fact_models()
    docs = db.get_documents()

    btn_col1, btn_col2 = st.columns([3, 1])
    with btn_col1:
        cross_doc_only = st.checkbox(
            "Compare across different documents only (Recommended)",
            value=True,
            help="When checked, compares facts originating from different PDF files."
        )
        if st.button("🔍 Run Cross-Document Relationship Analysis", type="primary", use_container_width=True):
            prog = st.progress(0.0)
            status_text = st.empty()

            status_text.text(f"Indexing {len(all_facts)} facts for strict canonical metric pairs...")
            candidate_pairs = Normalizer.find_candidate_pairs(
                all_facts,
                max_candidates=250,
                prefer_cross_document=cross_doc_only
            )

            if not candidate_pairs:
                prog.empty()
                status_text.empty()
                st.warning("No candidate pairs met the strict canonical metric threshold.")
            else:
                status_text.text(f"Evaluating {len(candidate_pairs)} candidate pairs...")

                def update_p(curr, total):
                    prog.progress(curr / total)
                    status_text.text(f"Evaluating pair {curr}/{total}...")

                confirmed = relationship_engine.evaluate_relationships(
                    candidate_pairs,
                    progress_callback=update_p
                )

                # Persist discovered relationships
                saved = 0
                for r in confirmed:
                    db.save_relationship(r)
                    saved += 1

                prog.empty()
                status_text.empty()
                st.success(f"✅ Analysis complete! Recorded {saved} cross-document relationships.")
                st.rerun()

    with btn_col2:
        if st.button("🗑️ Clear Relationships", use_container_width=True):
            db.clear_relationships()
            st.toast("Relationships cleared.", icon="🧹")
            st.rerun()

    st.divider()

    # Display Recorded Relationships
    detailed_rels = db.get_detailed_relationships()
    if not detailed_rels:
        st.markdown(
            """
            <div style="text-align: center; padding: 32px 16px; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px dashed rgba(255, 255, 255, 0.1);">
                <div style="font-size: 1.8rem; margin-bottom: 8px;">⚖️</div>
                <div style="font-size: 1.05rem; font-weight: 600; color: #ffffff;">No Relationships Recorded Yet</div>
                <div style="font-size: 0.85rem; color: #94a3b8; max-width: 460px; margin: 6px auto;">
                    Click <b>'Run Cross-Document Relationship Analysis'</b> above to discover corroborations, contradictions, and reconciliations across stored PDF documents.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Filter & View Controls Bar
    rf_col1, rf_col2, rf_col3 = st.columns([2, 2, 1])
    with rf_col1:
        rel_type_filter = st.selectbox(
            "Filter by Relationship Type:",
            ["All", "CORROBORATES", "CONTRADICTS", "RECONCILES"],
            key="rel_filter_type"
        )
    with rf_col2:
        rel_search = st.text_input("🔍 Search (metric, value, reasoning):", "", key="rel_search_kw")
    with rf_col3:
        rel_view_mode = st.radio("View Mode:", ["Cards", "Table"], horizontal=True, key="rel_view_mode")

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

    st.markdown(f"<div style='font-size: 0.85rem; color: #94a3b8; margin: 12px 0;'>Found <b>{len(filtered_rels)}</b> matching relationships (out of {len(detailed_rels)} recorded):</div>", unsafe_allow_html=True)

    if not filtered_rels:
        st.info("No relationships match the selected filter criteria.")
    elif rel_view_mode == "Table":
        df_rels = []
        for r in filtered_rels:
            doc_a = r.get("fact_a_document") or r.get("doc_a_name", "Document A")
            page_a = r.get("fact_a_page", 1)
            doc_b = r.get("fact_b_document") or r.get("doc_b_name", "Document B")
            page_b = r.get("fact_b_page", 1)
            df_rels.append({
                "ID": r.get("id"),
                "Type": r.get("relationship_type"),
                "Metric A": f"{r.get('fact_a_subject', '')} ({r.get('fact_a_value', '')} {r.get('fact_a_unit') or ''})".strip(),
                "Source A": f"{doc_a} (p. {page_a})",
                "Metric B": f"{r.get('fact_b_subject', '')} ({r.get('fact_b_value', '')} {r.get('fact_b_unit') or ''})".strip(),
                "Source B": f"{doc_b} (p. {page_b})",
                "Reasoning & Context": r.get("reasoning", "")
            })
        st.dataframe(df_rels, use_container_width=True)
    else:
        # Render Side-by-Side Comparison Cards with pagination
        page_size = 15
        total_pages = max(1, (len(filtered_rels) + page_size - 1) // page_size)
        if total_pages > 1:
            p_col1, p_col2 = st.columns([1, 4])
            with p_col1:
                rel_page = st.number_input("Relationship Page:", min_value=1, max_value=total_pages, value=1, step=1, key="rel_page_num")
            with p_col2:
                st.markdown(f"<div style='padding-top:8px; font-size:0.82rem; color:#94a3b8;'>Showing items {(rel_page - 1) * page_size + 1}–{min(rel_page * page_size, len(filtered_rels))} of {len(filtered_rels)} relationships</div>", unsafe_allow_html=True)
            start_idx = (rel_page - 1) * page_size
            page_rels = filtered_rels[start_idx : start_idx + page_size]
        else:
            page_rels = filtered_rels

        for rel in page_rels:
            st.markdown(render_relationship_card_html(rel), unsafe_allow_html=True)


def render_failure_analysis_tab():
    """Tab 4: Extraction/Reasoning Failure Mode & Interactive Audit (Assignment Requirement)."""
    st.markdown("### ⚠️ Extraction & Reasoning Failure Analysis")
    st.markdown(
        "A key requirement of the assignment is to **identify and explain a genuine extraction or reasoning failure mode**, "
        "document its root cause, and implement architectural defenses to mitigate it."
    )

    # In-depth Case Study Card
    st.markdown(render_failure_case_study_html(), unsafe_allow_html=True)

    st.markdown("---")

    # Interactive Live Sandbox
    st.markdown("#### 🧪 Interactive Reasoning Sandbox")
    st.markdown("Test candidate pairs live to see how the strict matching layer rejects false matches and resolves reconciliations:")

    sandbox_col1, sandbox_col2 = st.columns(2)

    with sandbox_col1:
        st.markdown("##### Fact A (Input)")
        subj_a = st.text_input("Subject A:", "Other expenses", key="sb_subj_a")
        pred_a = st.text_input("Predicate A:", "was", key="sb_pred_a")
        val_a = st.text_input("Value A:", "1,963.74", key="sb_val_a")
        unit_a = st.text_input("Unit A:", "₹ million", key="sb_unit_a")
        time_a = st.text_input("Time Context A:", "Year ended March 31, 2019", key="sb_time_a")

    with sandbox_col2:
        st.markdown("##### Fact B (Input)")
        subj_b = st.text_input("Subject B:", "Total expenses", key="sb_subj_b")
        pred_b = st.text_input("Predicate B:", "was", key="sb_pred_b")
        val_b = st.text_input("Value B:", "8,825", key="sb_val_b")
        unit_b = st.text_input("Unit B:", "₹ Cr", key="sb_unit_b")
        time_b = st.text_input("Time Context B:", "FY24", key="sb_time_b")

    if st.button("⚡ Test Relationship Engine Live", type="primary"):
        test_fa = Fact(
            id=9991, document_id=1, document_name="Sandbox_A.pdf", page_number=1,
            subject=subj_a, predicate=pred_a, object_value=val_a,
            unit=unit_a, time_period=time_a,
            evidence=Evidence(document_name="Sandbox_A.pdf", page_number=1, quote="Evidence for Fact A")
        )
        test_fb = Fact(
            id=9992, document_id=2, document_name="Sandbox_B.pdf", page_number=1,
            subject=subj_b, predicate=pred_b, object_value=val_b,
            unit=unit_b, time_period=time_b,
            evidence=Evidence(document_name="Sandbox_B.pdf", page_number=1, quote="Evidence for Fact B")
        )

        canon_a = Normalizer.canonicalize_subject(subj_a)
        canon_b = Normalizer.canonicalize_subject(subj_b)
        compat = Normalizer.are_subjects_compatible(canon_a, canon_b)

        result_rel = relationship_engine.compare_facts(test_fa, test_fb)

        st.markdown("##### Engine Evaluation Result:")
        r_col1, r_col2 = st.columns([1, 2])
        with r_col1:
            if result_rel is None:
                st.error("🚫 Classification: NO_RELATION")
            elif result_rel.relationship_type == RelationshipType.CORROBORATES:
                st.success("🟢 Classification: CORROBORATES")
            elif result_rel.relationship_type == RelationshipType.CONTRADICTS:
                st.error("🔴 Classification: CONTRADICTS")
            else:
                st.warning("🟠 Classification: RECONCILES")

        with r_col2:
            st.markdown(f"- Canonical Subject A: `'{canon_a}'`")
            st.markdown(f"- Canonical Subject B: `'{canon_b}'`")
            st.markdown(f"- Metric Identity Compatible: `{compat}`")
            if result_rel:
                st.markdown(f"- Reasoning: {result_rel.reasoning}")
                if result_rel.reconciliation_context:
                    st.markdown(f"- Context: `{result_rel.reconciliation_context}`")
            else:
                st.markdown("- **Engine Verdict**: Rejected upfront because canonical subjects are distinct metrics. Zero false reconciliation hallucinated!")


def render_database_tab():
    """Tab 5: Local SQLite Database & Provenance Explorer."""
    st.markdown("### 🗄️ Database & Provenance Explorer")
    st.markdown("Inspect raw relational records directly from the local SQLite database.")

    tab_docs, tab_pages, tab_facts, tab_rels = st.tabs([
        "📄 Documents Table",
        "📍 Pages Table",
        "🧠 Facts Table",
        "⚖️ Relationships Table"
    ])

    with tab_docs:
        docs = db.get_documents()
        if docs:
            df_docs = pd.DataFrame(docs)
            st.dataframe(df_docs, use_container_width=True)
            st.download_button(
                "📥 Download Documents CSV",
                df_docs.to_csv(index=False).encode("utf-8"),
                "documents.csv",
                "text/csv"
            )
        else:
            st.info("No documents recorded.")

    with tab_pages:
        docs = db.get_documents()
        if docs:
            selected_doc = st.selectbox("Filter pages for document:", [d["filename"] for d in docs], key="db_pages_select")
            doc_id = next(d["id"] for d in docs if d["filename"] == selected_doc)
            pages = db.get_pages_for_document(doc_id)
            df_pages = pd.DataFrame(pages)
            st.dataframe(df_pages, use_container_width=True)
        else:
            st.info("No pages recorded.")

    with tab_facts:
        facts = db.get_facts()
        if facts:
            df_facts = pd.DataFrame(facts)
            st.dataframe(df_facts, use_container_width=True)
            st.download_button(
                "📥 Download Facts CSV",
                df_facts.to_csv(index=False).encode("utf-8"),
                "facts.csv",
                "text/csv"
            )
        else:
            st.info("No facts recorded.")

    with tab_rels:
        rels = db.get_detailed_relationships()
        if rels:
            df_rels = pd.DataFrame(rels)
            st.dataframe(df_rels, use_container_width=True)
            st.download_button(
                "📥 Download Relationships CSV",
                df_rels.to_csv(index=False).encode("utf-8"),
                "relationships.csv",
                "text/csv"
            )
        else:
            st.info("No relationships recorded.")


def main():
    """Main application entry point."""
    render_sidebar()

    # Hero Banner
    banner_html = render_hero_banner(
        gemini_model=fact_extractor.model_name,
        is_configured=fact_extractor.is_configured
    )
    st.markdown(banner_html, unsafe_allow_html=True)

    # Top KPI Ribbon
    render_kpi_ribbon()

    # Top-Level Navigation Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Ingest & Pipeline",
        "🧠 Extracted Facts & Grounding",
        "⚖️ Cross-Document Reasoning",
        "⚠️ Failure Analysis & Edge Cases",
        "🗄️ Database & Provenance"
    ])

    with tab1:
        render_upload_tab()
    with tab2:
        render_facts_tab()
    with tab3:
        render_relationships_tab()
    with tab4:
        render_failure_analysis_tab()
    with tab5:
        render_database_tab()


if __name__ == "__main__":
    main()
