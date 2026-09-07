# Fact Knowledge Layer

> **Superjoin · VIT 2026 Engineering Intern Hiring Assignment**  
> A system to extract meaningful facts from PDFs, link them to exact source evidence (document + page), and discover cross-document relationships (`CORROBORATES`, `CONTRADICTS`, `RECONCILES`).

---

## 🎯 The Challenge & Purpose

Important facts are often scattered across disparate documents—stated in different ways, supported by complementary evidence, or contradicted elsewhere. The **Fact Knowledge Layer** solves this by:
1. Ingesting multiple PDF documents and extracting text on a page-by-page basis.
2. Grounding every piece of data to its exact source (document filename and 1-indexed page number).
3. Providing a structured schema and storage for facts and cross-document relationships.
4. Supplying an intuitive Streamlit interface for uploading, inspecting, and navigating facts.

---

## 🏗️ Architecture & Project Structure

```text
fact-knowledge-layer/
├── app.py                     # Streamlit frontend & UI controller
├── requirements.txt           # Python dependencies
├── .gitignore                 # Version control exclusions
├── README.md                  # Comprehensive project documentation
├── .env.example               # Template for environment variables
│
├── services/                  # Business logic and processing pipelines
│   ├── __init__.py
│   ├── pdf_service.py         # PyMuPDF-based page-by-page text extraction
│   ├── fact_extractor.py      # [LLM Placeholder] Extracts structured facts from text
│   ├── normalizer.py          # [Placeholder] Entity, temporal, & metric normalization
│   └── relationship_engine.py # [LLM Placeholder] Classifies CORROBORATES, CONTRADICTS, RECONCILES
│
├── models/                    # Pydantic schemas for data validation
│   ├── __init__.py
│   └── schemas.py             # DocumentMetadata, DocumentPage, Evidence, Fact, FactRelationship
│
├── database/                  # SQLite storage layer
│   ├── __init__.py
│   └── database.py            # SQLite schema initialization and CRUD methods
│
└── data/                      # Local data directory
    └── .gitkeep
```

---

## 🚀 Setup and Run Instructions

### 1. Prerequisites
- Python 3.10+ installed
- `pip` package manager

### 2. Create and Activate Virtual Environment
```bash
# Navigate to project folder
cd fact-knowledge-layer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (cmd):
.\venv\Scripts\activate.bat
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env   # Windows
# or: cp .env.example .env (Linux/macOS)
```
*(Optional for MVP: The Gemini API key will be used when activating the LLM extraction in Phase 2).*

### 5. Launch the Streamlit Application
```bash
streamlit run app.py
```
The application will open automatically in your browser at `http://localhost:8501`.

---

## 🧩 Module Breakdown & Design Decisions

| Module | Responsibility | Key Technologies |
|---|---|---|
| [`services/pdf_service.py`](services/pdf_service.py) | Ingests PDF files and extracts text cleanly while maintaining page boundaries. | **PyMuPDF (fitz)** for speed and high-fidelity text extraction. |
| [`models/schemas.py`](models/schemas.py) | Defines rigorous data contracts for facts, source evidence, and relationships. | **Pydantic v2** for validation and JSON serialization. |
| [`database/database.py`](database/database.py) | Persistent storage for documents, extracted pages, facts, and relationships. | **SQLite3** with parameterized queries and relational integrity. |
| [`services/fact_extractor.py`](services/fact_extractor.py) | Interfaces with LLM to extract semantic and numerical assertions. | Designed for **Google Gemini API** integration. |
| [`services/normalizer.py`](services/normalizer.py) | Harmonizes entities, currencies, and dates, and identifies candidate pairs. | Modular normalization logic to avoid $O(N^2)$ LLM calls. |
| [`services/relationship_engine.py`](services/relationship_engine.py) | Compares candidate fact pairs across documents using LLM reasoning. | Classifies into `CORROBORATES`, `CONTRADICTS`, `RECONCILES`. |
| [`app.py`](app.py) | Multi-tab UI for document ingestion, page inspection, and provenance tracking. | **Streamlit** for rapid, reactive prototyping. |

---

## 🔍 The Four Target Cases (Assignment Roadmap)

The downstream LLM reasoning engine is designed around the four core cases required by the internship assignment:

1. **CORROBORATES**: Same fact stated across multiple documents (e.g., matching revenue or headcount reported across separate reports).
2. **CONTRADICTS**: Genuine contradiction where documents conflict on the same entity, attribute, and timeframe.
3. **RECONCILES**: Discrepancies that appear contradictory but are resolved by contextual variables:
   - **Time period** (e.g., FY22 vs. FY23 performance)
   - **Scope** (e.g., US division vs. Global entity, GAAP vs. Non-GAAP)
   - **Units** (e.g., USD vs. EUR or millions vs. thousands)
4. **Extraction / Reasoning Failure Analysis**: Handling edge cases (scanned PDFs without OCR, ambiguous semantic references) with fallback mechanisms and uncertainty scoring.

---

## 🔮 Extending to Gemini LLM Integration (Phase 2)

To enable Gemini LLM extraction:
1. Add `google-generativeai` or `google-genai` to `requirements.txt`.
2. Add your `GEMINI_API_KEY` to `.env`.
3. In `services/fact_extractor.py`, implement structured output prompt with `gemini-1.5-pro` or `gemini-1.5-flash` using `response_schema=Fact`.
4. In `services/relationship_engine.py`, prompt Gemini with candidate fact pairs to classify relationship type and produce explanatory reasoning grounded in evidence.
