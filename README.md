# Fact Knowledge Layer

> **Superjoin · VIT 2026 Engineering Intern Hiring Assignment**  
> A system to extract meaningful facts from PDFs, link them to exact source evidence (document + page), and discover cross-document relationships (`CORROBORATES`, `CONTRADICTS`, `RECONCILES`).

---
FULL VIDEO EXPLANATION-
https://drive.google.com/drive/folders/1oh58N44cLgBm01Bj3nJiglRnpqwjFTeB?usp=sharing

Deploy Link-
https://fact-knowledge-layer-k3aduymuhfkcpnpjevsmyq.streamlit.app/

<img width="1910" height="910" alt="image" src="https://github.com/user-attachments/assets/bdb48b9e-66d6-4158-aead-ac65e72e03d2" />

## 🎯 The Challenge & Purpose

Important facts are often scattered across disparate documents—stated in different ways, supported by complementary evidence, or contradicted elsewhere. The **Fact Knowledge Layer** solves this by:

1. Ingesting multiple PDF documents and extracting text on a page-by-page basis.
2. Grounding every piece of data to its exact source (document filename and 1-indexed page number).
3. Providing a structured schema and storage for facts and cross-document relationships.
4. Supplying an intuitive Streamlit interface for uploading, inspecting, and navigating facts.

---

## 🏗️ Architecture & Project Structure
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/88b56e1f-0055-4436-a5f2-12f70577a477" />

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

## Setup and Run Instructions

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

_(Optional for MVP: The Gemini API key will be used when activating the LLM extraction in Phase 2)._

### 5. Launch the Streamlit Application

```bash
streamlit run app.py
```

The application will open automatically in your browser at `http://localhost:8501`.

---

## Approach

The application uses a page-preserving ingestion pipeline. PyMuPDF extracts each PDF page independently, and SQLite stores document metadata, page text, extracted facts, evidence quotes, and relationships. Pydantic models define the contracts between these layers.

Fact extraction is optional during upload and uses Google Gemini structured output when `GEMINI_API_KEY` is configured. Every returned fact retains the document name, 1-indexed page number, and verbatim evidence quote. The extractor lowers confidence when a quote does not exactly match normalized page text, rather than silently accepting ungrounded output.

Relationship discovery first uses deterministic normalization for subject, predicate, numeric units, time periods, and scope. It then classifies compatible facts as `CORROBORATES`, `CONTRADICTS`, or `RECONCILES`; Gemini is reserved for ambiguous cases. This keeps common comparisons fast and explainable while still supporting nuanced language.

The main trade-off is simplicity versus scale: Streamlit and SQLite make the MVP easy to run locally, but a production version would need background jobs, larger-scale storage, authentication, and stronger document/OCR processing.

### AI Tools Used

- Google Gemini via the official `google-genai` SDK for structured fact extraction and ambiguous relationship reasoning.
- Streamlit for the interactive application surface.
- PyMuPDF for local PDF text extraction and page-level provenance.
- Pydantic for schema validation and structured model output.

### Module Breakdown & Design Decisions

| Module                                                               | Responsibility                                                                 | Key Technologies                                                 |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| [`services/pdf_service.py`](services/pdf_service.py)                 | Ingests PDF files and extracts text cleanly while maintaining page boundaries. | **PyMuPDF (fitz)** for speed and high-fidelity text extraction.  |
| [`models/schemas.py`](models/schemas.py)                             | Defines rigorous data contracts for facts, source evidence, and relationships. | **Pydantic v2** for validation and JSON serialization.           |
| [`database/database.py`](database/database.py)                       | Persistent storage for documents, extracted pages, facts, and relationships.   | **SQLite3** with parameterized queries and relational integrity. |
| [`services/fact_extractor.py`](services/fact_extractor.py)           | Interfaces with LLM to extract semantic and numerical assertions.              | Designed for **Google Gemini API** integration.                  |
| [`services/normalizer.py`](services/normalizer.py)                   | Harmonizes entities, currencies, and dates, and identifies candidate pairs.    | Modular normalization logic to avoid $O(N^2)$ LLM calls.         |
| [`services/relationship_engine.py`](services/relationship_engine.py) | Compares candidate fact pairs across documents using LLM reasoning.            | Classifies into `CORROBORATES`, `CONTRADICTS`, `RECONCILES`.     |
| [`app.py`](app.py)                                                   | Multi-tab UI for document ingestion, page inspection, and provenance tracking. | **Streamlit** for rapid, reactive prototyping.                   |

---

## Four Required Cases

The downstream LLM reasoning engine is designed around the four core cases required by the internship assignment:

1. **CORROBORATES**: Same fact stated across multiple documents (e.g., matching revenue or headcount reported across separate reports).
2. **CONTRADICTS**: Genuine contradiction where documents conflict on the same entity, attribute, and timeframe.
3. **RECONCILES**: Discrepancies that appear contradictory but are resolved by contextual variables:
   - **Time period** (e.g., FY22 vs. FY23 performance)
   - **Scope** (e.g., US division vs. Global entity, GAAP vs. Non-GAAP)
   - **Units** (e.g., USD vs. EUR or millions vs. thousands)
4. **Extraction / Reasoning Failure Analysis**: Handling edge cases (scanned PDFs without OCR, ambiguous semantic references) with fallback mechanisms and uncertainty scoring.

---

## Video Demo

Add a hosted recording of the complete workflow here:

**[Watch the PDF processing demo](https://youtu.be/REPLACE_WITH_DEMO_VIDEO_ID)**

The recording should be three minutes or less and show PDF upload, page-level extraction and provenance, fact extraction, and the `CORROBORATES`, `CONTRADICTS`, and `RECONCILES` relationship cases, including a failure/edge case.

## Limitations and Next Steps

- Scanned/image-only PDFs require OCR; PyMuPDF currently reports those pages as having no extracted text.
- Gemini extraction and ambiguous relationship reasoning require a configured API key and network access.
- SQLite is local and single-user; it is not yet suitable for concurrent production workloads.
- Candidate matching is intentionally conservative, so semantically related facts may be skipped.
- Duplicate uploads are currently stored as new document records.

Next steps would be OCR support, background processing with job status, persistent object storage, a production database, authentication, duplicate detection, evaluation fixtures for the four relationship classes, and a review workflow for low-confidence facts.

## Additional Notes

- The API key is read from `.env` and is never displayed or logged.
- Generated SQLite files and uploaded PDFs are excluded from git by `.gitignore`.
- The application remains useful without Gemini: users can ingest PDFs, inspect page text, and explore the database while LLM features are disabled.

## Extending Gemini Integration

To enable Gemini LLM extraction:

1. Add `google-generativeai` or `google-genai` to `requirements.txt`.
2. Add your `GEMINI_API_KEY` to `.env`.
3. In `services/fact_extractor.py`, implement structured output prompt with `gemini-1.5-pro` or `gemini-1.5-flash` using `response_schema=Fact`.
4. In `services/relationship_engine.py`, prompt Gemini with candidate fact pairs to classify relationship type and produce explanatory reasoning grounded in evidence.
