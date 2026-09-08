"""
Fact Knowledge Layer - UI Styles & Design System
================================================
Defines modern, production-grade CSS styling, typography, and card components.
"""

CUSTOM_CSS = """
<style>
/* ==========================================================================
   Import Google Fonts
   ========================================================================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ==========================================================================
   CSS Variables & Color System
   ========================================================================== */
:root {
    --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;

    /* Accent & Brand Colors */
    --brand-primary: #6366f1;
    --brand-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
    --brand-glow: rgba(99, 102, 241, 0.25);

    /* Status Colors */
    --corroborates-color: #10b981;
    --corroborates-bg: rgba(16, 185, 129, 0.12);
    --corroborates-border: rgba(16, 185, 129, 0.35);

    --contradicts-color: #f43f5e;
    --contradicts-bg: rgba(244, 63, 94, 0.12);
    --contradicts-border: rgba(244, 63, 94, 0.35);

    --reconciles-color: #f59e0b;
    --reconciles-bg: rgba(245, 158, 11, 0.12);
    --reconciles-border: rgba(245, 158, 11, 0.35);

    --numerical-color: #0ea5e9;
    --numerical-bg: rgba(14, 165, 233, 0.12);
    --numerical-border: rgba(14, 165, 233, 0.35);

    --semantic-color: #a855f7;
    --semantic-bg: rgba(168, 85, 247, 0.12);
    --semantic-border: rgba(168, 85, 247, 0.35);

    /* Surface & Background Colors */
    --card-bg: rgba(30, 41, 59, 0.70);
    --card-bg-solid: #1e293b;
    --card-border: rgba(255, 255, 255, 0.08);
    --card-hover-border: rgba(99, 102, 241, 0.45);
    --quote-bg: rgba(15, 23, 42, 0.65);
    --quote-border: #6366f1;
}

/* Global Font Override */
html, body, [class*="css"] {
    font-family: var(--font-main) !important;
}

/* Hide default streamlit header decoration bar */
header[data-testid="stHeader"] {
    background: transparent !important;
}

/* ==========================================================================
   Hero Banner Component
   ========================================================================== */
.fkl-hero-banner {
    background: linear-gradient(180deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    position: relative;
    overflow: hidden;
}

.fkl-hero-banner::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--brand-gradient);
}

.fkl-badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.35);
    margin-bottom: 12px;
}

.pulse-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #10b981;
    box-shadow: 0 0 8px #10b981;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1.3); opacity: 1; }
    100% { transform: scale(0.95); opacity: 0.8; }
}

.fkl-hero-title {
    font-size: 2.1rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    margin: 0 0 8px 0;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.fkl-hero-subtitle {
    font-size: 0.95rem;
    color: #94a3b8;
    margin: 0 0 16px 0;
    line-height: 1.5;
    max-width: 820px;
}

.fkl-status-ribbon {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.06);
    color: #cbd5e1;
}

.pill-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
}
.pill-dot.green { background: #10b981; }
.pill-dot.blue { background: #0ea5e9; }
.pill-dot.purple { background: #a855f7; }

/* ==========================================================================
   KPI Metrics Grid
   ========================================================================== */
.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 14px;
    margin-bottom: 24px;
}

.kpi-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 16px 18px;
    transition: all 0.2s ease;
    backdrop-filter: blur(10px);
}

.kpi-card:hover {
    border-color: var(--card-hover-border);
    transform: translateY(-2px);
    box-shadow: 0 8px 20px -4px var(--brand-glow);
}

.kpi-label {
    font-size: 0.78rem;
    font-weight: 500;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.kpi-value {
    font-size: 1.65rem;
    font-weight: 700;
    color: #ffffff;
    font-feature-settings: "tnum";
}

.kpi-subtext {
    font-size: 0.72rem;
    color: #64748b;
    margin-top: 4px;
}

/* ==========================================================================
   Tabs Navigation Styling
   ========================================================================== */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(15, 23, 42, 0.6) !important;
    padding: 6px !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    margin-bottom: 20px !important;
}

.stTabs [data-baseweb="tab"] {
    height: 42px !important;
    border-radius: 8px !important;
    padding: 0 16px !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    color: #94a3b8 !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #ffffff !important;
    background: rgba(255, 255, 255, 0.05) !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35) !important;
}

.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* ==========================================================================
   Fact Card Component
   ========================================================================== */
.fact-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 16px;
    transition: all 0.2s ease;
    backdrop-filter: blur(8px);
}

.fact-card:hover {
    border-color: var(--card-hover-border);
    box-shadow: 0 6px 18px -2px rgba(0, 0, 0, 0.25);
    transform: translateY(-1px);
}

.fact-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    flex-wrap: wrap;
    gap: 8px;
}

.badge-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-tag.numerical {
    background: var(--numerical-bg);
    color: var(--numerical-color);
    border: 1px solid var(--numerical-border);
}

.badge-tag.semantic {
    background: var(--semantic-bg);
    color: var(--semantic-color);
    border: 1px solid var(--semantic-border);
}

.badge-tag.doc {
    background: rgba(255, 255, 255, 0.05);
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.badge-tag.confidence {
    background: rgba(16, 185, 129, 0.10);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.25);
}

.fact-triple {
    font-size: 1.08rem;
    line-height: 1.5;
    margin-bottom: 10px;
    color: #f1f5f9;
}

.fact-subject {
    font-weight: 700;
    color: #ffffff;
}

.fact-predicate {
    font-style: italic;
    color: #a5b4fc;
    margin: 0 4px;
}

.fact-value {
    display: inline-block;
    background: rgba(99, 102, 241, 0.15);
    color: #818cf8;
    font-family: var(--font-mono);
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid rgba(99, 102, 241, 0.3);
}

.fact-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
}

.meta-item {
    font-size: 0.75rem;
    color: #94a3b8;
    background: rgba(255, 255, 255, 0.03);
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.evidence-quote-box {
    background: var(--quote-bg);
    border-left: 3px solid var(--quote-border);
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    font-size: 0.85rem;
    color: #cbd5e1;
    font-style: italic;
    line-height: 1.5;
    position: relative;
}

.evidence-citation {
    display: block;
    font-style: normal;
    font-size: 0.72rem;
    color: #818cf8;
    font-weight: 500;
    margin-top: 6px;
}

/* ==========================================================================
   Relationship Comparison Cards
   ========================================================================== */
.rel-card {
    background: var(--card-bg);
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 20px;
    border: 1px solid var(--card-border);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(10px);
}

.rel-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 28px -6px rgba(0, 0, 0, 0.35);
}

.rel-card.corroborates {
    border-left: 4px solid var(--corroborates-color);
}
.rel-card.corroborates:hover {
    border-color: var(--corroborates-border);
    box-shadow: 0 8px 24px -4px rgba(16, 185, 129, 0.2);
}

.rel-card.contradicts {
    border-left: 4px solid var(--contradicts-color);
}
.rel-card.contradicts:hover {
    border-color: var(--contradicts-border);
    box-shadow: 0 8px 24px -4px rgba(244, 63, 94, 0.2);
}

.rel-card.reconciles {
    border-left: 4px solid var(--reconciles-color);
}
.rel-card.reconciles:hover {
    border-color: var(--reconciles-border);
    box-shadow: 0 8px 24px -4px rgba(245, 158, 11, 0.2);
}

.rel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    flex-wrap: wrap;
    gap: 10px;
}

.rel-type-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.rel-type-badge.corroborates {
    background: var(--corroborates-bg);
    color: var(--corroborates-color);
    border: 1px solid var(--corroborates-border);
}

.rel-type-badge.contradicts {
    background: var(--contradicts-bg);
    color: var(--contradicts-color);
    border: 1px solid var(--contradicts-border);
}

.rel-type-badge.reconciles {
    background: var(--reconciles-bg);
    color: var(--reconciles-color);
    border: 1px solid var(--reconciles-border);
}

.rel-context-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    background: rgba(245, 158, 11, 0.12);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.rel-comparison-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 16px;
}

@media (max-width: 768px) {
    .rel-comparison-grid {
        grid-template-columns: 1fr;
    }
}

.rel-side-fact {
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 14px 16px;
}

.rel-side-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
}

.rel-reasoning-box {
    background: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.85rem;
    line-height: 1.5;
    color: #e2e8f0;
}

.rel-reasoning-title {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #a5b4fc;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ==========================================================================
   Failure Case Study Cards (Assignment Requirement)
   ========================================================================== */
.failure-case-card {
    background: linear-gradient(180deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 24px -4px rgba(239, 68, 68, 0.15);
}

.failure-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
}

.failure-badge {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.35);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.failure-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
}

.comparison-table-mini {
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 0.83rem;
}

.comparison-table-mini th {
    background: rgba(15, 23, 42, 0.8);
    color: #94a3b8;
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.comparison-table-mini td {
    padding: 8px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    color: #e2e8f0;
}

/* ==========================================================================
   Buttons & Inputs Polishing
   ========================================================================== */
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4) !important;
    transition: all 0.2s ease !important;
}

.stButton button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6) !important;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.5);
}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.25);
}
</style>
"""
