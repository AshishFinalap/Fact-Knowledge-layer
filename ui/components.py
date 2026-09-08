"""
Fact Knowledge Layer - UI Components
====================================
Reusable HTML/Streamlit components for modern cards, badges, and comparison views.
"""

import html
from typing import Dict, Any, Optional


def escape(val: Any) -> str:
    """Safely escape HTML characters."""
    if val is None:
        return ""
    return html.escape(str(val))


def render_hero_banner(
    gemini_model: str = "gemini-flash-lite-latest",
    is_configured: bool = True
) -> str:
    """Generate HTML for the top Hero Banner with live status indicators."""
    status_class = "green" if is_configured else "purple"
    status_text = f"Gemini Active ({escape(gemini_model)})" if is_configured else "Gemini Disconnected"

    return f"""
    <div class="fkl-hero-banner">
        <div class="fkl-badge-pill">
            <span class="pulse-dot"></span> FACT KNOWLEDGE GRAPH & REASONING ENGINE
        </div>
        <h1 class="fkl-hero-title">Fact Knowledge Layer</h1>
        <p class="fkl-hero-subtitle">
            Enterprise intelligence pipeline for extracting verifiable numerical and semantic facts from financial and corporate PDF disclosures, grounding each claim with exact page citations, and executing cross-filing semantic reconciliation.
        </p>
        <div class="fkl-status-ribbon">
            <div class="status-pill">
                <span class="pill-dot {status_class}"></span> {status_text}
            </div>
            <div class="status-pill">
                <span class="pill-dot blue"></span> PyMuPDF 1.25 Page Provenance
            </div>
            <div class="status-pill">
                <span class="pill-dot green"></span> SQLite Local Persistence
            </div>
            <div class="status-pill">
                <span class="pill-dot purple"></span> Strict Metric Canonicalization & Unit Scaling
            </div>
        </div>
    </div>
    """


def render_kpi_card(label: str, value: Any, subtext: str = "", icon: str = "") -> str:
    """Generate HTML for an individual KPI metric card."""
    icon_html = f"<span>{icon}</span> " if icon else ""
    sub_html = f"<div class='kpi-subtext'>{escape(subtext)}</div>" if subtext else ""
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{icon_html}{escape(label)}</div>
        <div class="kpi-value">{escape(value)}</div>
        {sub_html}
    </div>
    """


def render_fact_card_html(fact: Dict[str, Any]) -> str:
    """Render a modern structured fact card with provenance and exact evidence grounding."""
    f_id = fact.get("id", 0)
    doc_name = escape(fact.get("document_name", "Unknown Document"))
    page_num = fact.get("page_number", 1)
    f_type = fact.get("fact_type", "SEMANTIC")
    subj = escape(fact.get("subject", ""))
    pred = escape(fact.get("predicate", ""))
    val = escape(fact.get("object_value", ""))
    conf = int(fact.get("confidence", 1.0) * 100)
    quote = escape(fact.get("evidence_quote", "No evidence quote recorded."))

    type_class = "numerical" if f_type == "NUMERICAL" else "semantic"

    meta_badges = []
    if fact.get("unit"):
        meta_badges.append(f"<span class='meta-item'>📏 Unit: <b>{escape(fact['unit'])}</b></span>")
    if fact.get("time_period"):
        meta_badges.append(f"<span class='meta-item'>⏱️ Time: <b>{escape(fact['time_period'])}</b></span>")
    if fact.get("context"):
        meta_badges.append(f"<span class='meta-item'>🌐 Scope: <b>{escape(fact['context'])}</b></span>")

    meta_html = "".join(meta_badges)

    return f"""
    <div class="fact-card">
        <div class="fact-header">
            <div style="display:flex; align-items:center; gap:8px;">
                <span class="badge-tag {type_class}">{f_type}</span>
                <span class="badge-tag doc">📄 {doc_name} · Page {page_num}</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                <span class="badge-tag confidence">🎯 {conf}% Confidence</span>
                <span style="font-size:0.75rem; color:#64748b; font-family:var(--font-mono);">#Fact-{f_id}</span>
            </div>
        </div>

        <div class="fact-triple">
            <span class="fact-subject">{subj}</span>
            <span class="fact-predicate">{pred}</span>
            <span class="fact-value">{val}</span>
        </div>

        <div class="fact-meta-row">
            {meta_html}
        </div>

        <div class="evidence-quote-box">
            ❝ {quote} ❞
            <span class="evidence-citation">📍 Verbatim Grounding Quote · {doc_name}, Page {page_num}</span>
        </div>
    </div>
    """


def render_relationship_card_html(rel: Dict[str, Any]) -> str:
    """Render a side-by-side comparison relationship card with deep reasoning."""
    rel_type = rel.get("relationship_type", "RECONCILES")
    conf = int(rel.get("confidence", 1.0) * 100)
    recon_ctx = rel.get("reconciliation_context")
    reasoning = escape(rel.get("reasoning", ""))

    if rel_type == "CORROBORATES":
        card_class = "corroborates"
        type_icon = "🟢"
        type_title = "CORROBORATES"
        type_desc = "Factual agreement confirmed across documents"
    elif rel_type == "CONTRADICTS":
        card_class = "contradicts"
        type_icon = "🔴"
        type_title = "CONTRADICTS"
        type_desc = "Direct conflict under identical timeframe & scope"
    else:
        card_class = "reconciles"
        type_icon = "🟠"
        type_title = "RECONCILES"
        type_desc = "Divergence explained by context (Time, Scope, or Units)"

    ctx_badge_html = ""
    if recon_ctx:
        ctx_badge_html = f"<div class='rel-context-badge'>🔍 {escape(recon_ctx)}</div>"

    # Fact A attributes
    meta_a = []
    if rel.get("fact_a_unit"):
        meta_a.append(f"<span class='meta-item'>Unit: <b>{escape(rel['fact_a_unit'])}</b></span>")
    if rel.get("fact_a_time"):
        meta_a.append(f"<span class='meta-item'>Time: <b>{escape(rel['fact_a_time'])}</b></span>")
    if rel.get("fact_a_context"):
        meta_a.append(f"<span class='meta-item'>Scope: <b>{escape(rel['fact_a_context'])}</b></span>")
    meta_a_html = "".join(meta_a)

    # Fact B attributes
    meta_b = []
    if rel.get("fact_b_unit"):
        meta_b.append(f"<span class='meta-item'>Unit: <b>{escape(rel['fact_b_unit'])}</b></span>")
    if rel.get("fact_b_time"):
        meta_b.append(f"<span class='meta-item'>Time: <b>{escape(rel['fact_b_time'])}</b></span>")
    if rel.get("fact_b_context"):
        meta_b.append(f"<span class='meta-item'>Scope: <b>{escape(rel['fact_b_context'])}</b></span>")
    meta_b_html = "".join(meta_b)

    return f"""
    <div class="rel-card {card_class}">
        <div class="rel-header">
            <div style="display:flex; align-items:center; gap:10px;">
                <span class="rel-type-badge {card_class}">
                    {type_icon} {type_title}
                </span>
                <span style="font-size:0.8rem; color:#94a3b8;">{type_desc}</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                {ctx_badge_html}
                <span class="badge-tag confidence">🎯 {conf}% Confidence</span>
                <span style="font-size:0.75rem; color:#64748b; font-family:var(--font-mono);">#Rel-{rel.get('id', '')}</span>
            </div>
        </div>

        <div class="rel-comparison-grid">
            <!-- FACT A -->
            <div class="rel-side-fact">
                <div class="rel-side-title">
                    <span>📄 Fact A (#{rel['fact_a_id']})</span>
                    <span style="color:#6366f1;">{escape(rel['fact_a_document'])} · p.{rel['fact_a_page']}</span>
                </div>
                <div style="margin: 8px 0; font-size: 0.95rem;">
                    <b>{escape(rel['fact_a_subject'])}</b> <i>{escape(rel['fact_a_predicate'])}</i>
                    <span class="fact-value" style="font-size:0.85rem; padding: 1px 6px;">{escape(rel['fact_a_value'])}</span>
                </div>
                <div class="fact-meta-row" style="margin-bottom:8px;">
                    {meta_a_html}
                </div>
                <div class="evidence-quote-box" style="font-size:0.78rem; padding:6px 10px;">
                    ❝ {escape(rel['fact_a_evidence'])} ❞
                </div>
            </div>

            <!-- FACT B -->
            <div class="rel-side-fact">
                <div class="rel-side-title">
                    <span>📄 Fact B (#{rel['fact_b_id']})</span>
                    <span style="color:#8b5cf6;">{escape(rel['fact_b_document'])} · p.{rel['fact_b_page']}</span>
                </div>
                <div style="margin: 8px 0; font-size: 0.95rem;">
                    <b>{escape(rel['fact_b_subject'])}</b> <i>{escape(rel['fact_b_predicate'])}</i>
                    <span class="fact-value" style="font-size:0.85rem; padding: 1px 6px;">{escape(rel['fact_b_value'])}</span>
                </div>
                <div class="fact-meta-row" style="margin-bottom:8px;">
                    {meta_b_html}
                </div>
                <div class="evidence-quote-box" style="font-size:0.78rem; padding:6px 10px;">
                    ❝ {escape(rel['fact_b_evidence'])} ❞
                </div>
            </div>
        </div>

        <div class="rel-reasoning-box">
            <div class="rel-reasoning-title">
                💡 System Knowledge & Provenance Reasoning
            </div>
            {reasoning}
        </div>
    </div>
    """


def render_failure_case_study_html() -> str:
    """
    Renders an in-depth assignment case study explaining extraction & reasoning failure modes,
    root-cause mechanics, and the architectural fix.
    """
    return """
    <div class="failure-case-card">
        <div class="failure-header">
            <span class="failure-badge">Assignment Requirement</span>
            <h3 class="failure-title">Case Study: The Over-Generalization & False Reconciliation Failure</h3>
        </div>

        <p style="color:#cbd5e1; font-size:0.9rem; line-height:1.6; margin-bottom:14px;">
            A critical failure mode in multi-document LLM knowledge architectures is <b>conflating distinct financial line items</b>
            due to broad lexical token overlap (e.g. sharing words like <i>"expenses"</i>, <i>"revenue"</i>, or <i>"ebitda"</i>),
            and falsely classifying them as <b>RECONCILES</b> simply because their fiscal periods differ.
        </p>

        <table class="comparison-table-mini">
            <thead>
                <tr>
                    <th>Dimension</th>
                    <th>Fact A (Prospectus 2022)</th>
                    <th>Fact B (Q4 FY24 Earnings)</th>
                    <th>Naive LLM Result (Failure)</th>
                    <th>Fact Knowledge Layer Result (Correct)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><b>Subject Metric</b></td>
                    <td><span style="color:#f87171; font-weight:600;">Other expenses</span></td>
                    <td><span style="color:#60a5fa; font-weight:600;">Total expenses</span></td>
                    <td rowspan="4" style="background:rgba(239,68,68,0.1); color:#fca5a5; vertical-align:middle; border-left:1px solid rgba(239,68,68,0.3);">
                        ❌ <b>FALSE RECONCILES</b><br>
                        <i>"Reconciled because FY19 differs from FY24"</i><br>
                        <small style="color:#f87171;">(Completely invalid: comparing sub-expense with total expenses!)</small>
                    </td>
                    <td rowspan="4" style="background:rgba(16,185,129,0.1); color:#86efac; vertical-align:middle; border-left:1px solid rgba(16,185,129,0.3);">
                        ✅ <b>NO_RELATION (Rejected)</b><br>
                        <i>"Canonical subjects are distinct financial metrics"</i><br>
                        <small style="color:#34d399;">(Zero false reconciliation hallucination)</small>
                    </td>
                </tr>
                <tr>
                    <td><b>Reported Value</b></td>
                    <td>1,963.74</td>
                    <td>8,825.00</td>
                </tr>
                <tr>
                    <td><b>Measurement Unit</b></td>
                    <td>₹ million (INR_MILLION)</td>
                    <td>₹ Cr (INR_CRORE)</td>
                </tr>
                <tr>
                    <td><b>Time Context</b></td>
                    <td>Year ended March 31, 2019</td>
                    <td>FY24</td>
                </tr>
            </tbody>
        </table>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin-top:16px;">
            <div style="background:rgba(15,23,42,0.6); padding:14px; border-radius:10px; border:1px solid rgba(255,255,255,0.06);">
                <div style="font-size:0.78rem; font-weight:700; color:#f87171; text-transform:uppercase; margin-bottom:6px;">
                    🚨 Root Cause of Failure
                </div>
                <ul style="font-size:0.82rem; color:#94a3b8; margin:0; padding-left:18px; line-height:1.5;">
                    <li><b>Stopword Contamination:</b> Naive NLP strippers remove <i>"other"</i> and <i>"total"</i> as common stopwords, collapsing both into the generic token <code>"expenses"</code>.</li>
                    <li><b>Loose Token Overlap:</b> Inverted indexing treats any single shared accounting keyword as grounds for cross-document pairing.</li>
                    <li><b>False Temporal Excuse:</b> LLMs observe different timeframes and invent a narrative that the metric "grew over time", ignoring metric identity.</li>
                </ul>
            </div>

            <div style="background:rgba(15,23,42,0.6); padding:14px; border-radius:10px; border:1px solid rgba(255,255,255,0.06);">
                <div style="font-size:0.78rem; font-weight:700; color:#34d399; text-transform:uppercase; margin-bottom:6px;">
                    🛡️ Architectural Defense Implemented
                </div>
                <ul style="font-size:0.82rem; color:#94a3b8; margin:0; padding-left:18px; line-height:1.5;">
                    <li><b>Qualifier Preservation:</b> <code>"total"</code>, <code>"other"</code>, <code>"operating"</code>, <code>"adjusted"</code>, <code>"gross"</code>, and <code>"net"</code> are strictly retained as critical metric qualifiers.</li>
                    <li><b>Strict Canonical Subject Equality:</b> Facts are compared if and only if <code>canonical_subject_A == canonical_subject_B</code>.</li>
                    <li><b>Unit Scaling Layer:</b> Automatic scale alignment (₹1 Cr = 10 M = 100 Lakh) ensures genuine figures can only corroborate or reconcile when subjects match.</li>
                </ul>
            </div>
        </div>
    </div>
    """
