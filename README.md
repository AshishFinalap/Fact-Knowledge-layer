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

https://drive.google.com/drive/folders/1oh58N44cLgBm01Bj3nJiglRnpqwjFTeB?usp=sharing

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

# Fact Knowledge Layer

> **Superjoin · VIT 2026 Engineering Intern Hiring Assignment**
>
> A system to extract meaningful facts from PDFs, link them to exact source evidence (document + page), and discover cross-document relationships (CORROBORATES, CONTRADICTS, RECONCILES).

---

## Overview

**Full Video Explanation:** [Google Drive](https://drive.google.com/drive/folders/1oh58N44cLgBm01Bj3nJiglRnpqwjFTeB?usp=sharing)

**Live Deployment:** [Fact Knowledge Layer Application](https://fact-knowledge-layer-k3aduymuhfkcpnpjevsmyq.streamlit.app/)

---

## Challenge and Purpose

Important facts are often scattered across disparate documents—stated in different ways, supported by complementary evidence, or contradicted elsewhere. The Fact Knowledge Layer solves this challenge by:

1. Ingesting multiple PDF documents and extracting text on a page-by-page basis
2. Grounding every piece of data to its exact source (document filename and 1-indexed page number)
3. Providing structured schemas and storage for facts and cross-document relationships
4. Supplying an intuitive Streamlit interface for uploading, inspecting, and navigating facts

---

## Architecture and Project Structure

```
fact-knowledge-layer/
├── app.py                     # Streamlit frontend and UI controller
├── requirements.txt           # Python dependencies
├── .gitignore                 # Version control exclusions
├── README.md                  # Comprehensive project documentation
├── .env.example               # Template for environment variables
│
├── services/                  # Business logic and processing pipelines
│   ├── __init__.py
│   ├── pdf_service.py         # PyMuPDF-based page-by-page text extraction
│   ├── fact_extractor.py      # LLM placeholder: extracts structured facts from text
│   ├── normalizer.py          # Entity, temporal, and metric normalization
│   └── relationship_engine.py # LLM placeholder: classifies CORROBORATES, CONTRADICTS, RECONCILES
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

## Setup and Installation

### Prerequisites

- Python 3.10 or later
- pip package manager
- Gemini API key (optional for MVP)

### Step 1: Create and Activate Virtual Environment

```bash
# Navigate to project folder
cd fact-knowledge-layer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
.\venv\Scripts\activate.bat

# On Linux/macOS:
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

Optional: Add your Gemini API key to the `.env` file for LLM-powered extraction features.

### Step 4: Launch the Application

```bash
streamlit run app.py
```

The application will automatically open in your browser at `http://localhost:8501`.

---

## Approach and Methodology

The application uses a page-preserving ingestion pipeline. PyMuPDF extracts each PDF page independently, and SQLite stores document metadata, page text, extracted facts, evidence quotes, and relationships. Pydantic models define the contracts between layers.

Fact extraction is optional during upload and uses Google Gemini structured output when `GEMINI_API_KEY` is configured. Every returned fact retains the document name, 1-indexed page number, and verbatim evidence quote. The extractor lowers confidence when a quote does not exactly match normalized page text, rather than silently accepting ungrounded output.

Relationship discovery first uses deterministic normalization for subject, predicate, numeric units, time periods, and scope. It then classifies compatible facts as CORROBORATES, CONTRADICTS, or RECONCILES; Gemini is reserved for ambiguous cases. This keeps common comparisons fast and explainable while supporting nuanced language.

**Trade-off:** Simplicity versus scale. Streamlit and SQLite make the MVP easy to run locally, but a production version would require background jobs, larger-scale storage, authentication, and stronger document/OCR processing.

---

## Core Components

### Module Breakdown and Design Decisions

| Module | Responsibility | Technologies |
|--------|---|---|
| `services/pdf_service.py` | Ingests PDF files and extracts text while maintaining page boundaries | PyMuPDF (fitz) for speed and high-fidelity text extraction |
| `models/schemas.py` | Defines rigorous data contracts for facts, source evidence, and relationships | Pydantic v2 for validation and JSON serialization |
| `database/database.py` | Persistent storage for documents, extracted pages, facts, and relationships | SQLite3 with parameterized queries and relational integrity |
| `services/fact_extractor.py` | Interfaces with LLM to extract semantic and numerical assertions | Google Gemini API integration |
| `services/normalizer.py` | Harmonizes entities, currencies, and dates; identifies candidate pairs | Modular normalization logic to avoid O(N²) LLM calls |
| `services/relationship_engine.py` | Compares candidate fact pairs across documents using LLM reasoning | Classifies into CORROBORATES, CONTRADICTS, RECONCILES |
| `app.py` | Multi-tab UI for document ingestion, page inspection, and provenance tracking | Streamlit for rapid, reactive prototyping |

---

## PDF Ingestion

**Technology:** PyMuPDF

**File:** `services/pdf_service.py`

PDFs are processed page-by-page rather than treating the entire document as one large text block. For each page, the system preserves:

- Document filename
- Page number
- Extracted text
- Character count
- Word count

This ensures that every downstream fact can be traced back to its original document and page.

---

## LLM Fact Extraction

**Technology:** Google Gemini + google-genai SDK

**File:** `services/fact_extractor.py`

Gemini converts unstructured page text into structured facts. Each extracted fact can contain:

- Subject
- Predicate
- Object value
- Unit
- Time period
- Context
- Fact type
- Confidence score
- Evidence quote

### Example

**Input:**
```
Revenue from operations increased to ₹8,825 crore in FY24.
```

**Structured Output:**
```
Subject: Revenue from operations
Predicate: increased to
Value: 8,825
Unit: ₹ crore
Time: FY24
Type: NUMERICAL
```

The system preserves the exact source quote: *"Revenue from operations increased to ₹8,825 crore in FY24."*

---

## Grounded Evidence

A key design goal is ensuring extracted facts remain connected to their source. Every fact maintains relationships with:

- Document
- Page
- Evidence Quote

The UI allows users to inspect:

- Extracted fact
- Document name
- Page number
- Evidence quote
- Confidence score

This provides transparent and auditable extraction.

---

## Fact Types

The system supports both numerical and semantic information.

### Numerical Facts

Examples:
- Revenue = ₹8,825 Cr
- Employees = 25,000
- Growth = 18%
- Expenses = ₹2,257 Cr

### Semantic Facts

Examples:
- Company → headquartered in → Gurugram
- Director → resigned from → Board
- Company → operates in → India

This allows the knowledge layer to handle information beyond financial numbers.

---

## Normalization Engine

**File:** `services/normalizer.py`

Facts extracted from different documents may use different representations. The normalization layer makes comparison possible while avoiding overly broad matching.

### Metric Canonicalization

Different expressions may represent the same underlying metric. Examples:

- Revenue from operations
- Operating revenue
- Revenue from contracts with customers

Important qualifiers such as total, net, gross, operating, and adjusted are preserved to avoid incorrectly treating different metrics as identical.

### Unit Normalization

Financial values can be expressed using different scales:

- ₹1 Crore = ₹10 Million = ₹10,000,000

The system normalizes compatible units before comparing numerical values, preventing false differences caused only by unit representation.

### Time Normalization

The system tracks reporting periods such as:

- FY23, FY24
- Q4 FY23, Q4 FY24
- Year ended March 31, 2024

This is important because two different values may both be correct when they refer to different reporting periods.

### Context and Scope

The system also considers reporting context, including:

- Consolidated
- Standalone
- Segment
- Region

before deciding whether two facts contradict each other.

---

## Candidate Generation and Optimization

A naive approach would compare every fact with every other fact, resulting in O(N²) comparisons. Instead, the system first narrows the search space using:

- Metric canonicalization
- Predicate compatibility
- Time information
- Context and scope
- Semantic similarity
- Cross-document filtering

Only promising fact pairs proceed to relationship reasoning, reducing unnecessary comparisons and LLM calls.

---

## Relationship Engine

**File:** `services/relationship_engine.py`

The relationship engine identifies three primary relationship types required by the assignment.

### CORROBORATES

Two documents support the same underlying fact, even when expressed differently.

**Example:**
- Document A: Revenue from operations = X
- Document B: Operating revenue = X

The system considers metric compatibility, normalized values, timeframe, context and scope, and predicate compatibility. If the underlying claim is sufficiently compatible, the relationship is classified as CORROBORATES. The UI displays both facts and their evidence.

### CONTRADICTS

Two documents report conflicting information for the same underlying fact under the same relevant context.

**Example:**
- Document A: Cash = ₹500 Cr (Date: March 31, 2024)
- Document B: Cash = ₹475 Cr (Date: March 31, 2024)

**Output:** CONTRADICTS

Both source evidences are preserved so the user can inspect the disagreement.

### RECONCILES

Two values may initially appear contradictory but can be explained by contextual differences:

- Different financial years
- Different quarters
- Consolidated vs. Standalone
- Different reporting scopes
- Different units
- Different regions

**Example:**
- Revenue FY23 = X
- Revenue FY24 = Y

The values differ, but the facts are not contradictory because the reporting periods differ.

**Output:** RECONCILES

The system provides the reasoning behind the reconciliation.

---

## Database

**Technology:** SQLite

**File:** `database/database.py`

The system stores:

- Documents
- Pages
- Facts
- Relationships

Conceptually:

```
Documents
   │
   └── Pages
          │
          └── Facts
                 │
                 ├── Evidence
                 │
                 └── Relationships
```

SQLite was selected because it provides simple persistent relational storage without requiring an external database for the prototype.

---

## User Interface

**Technology:** Streamlit

**File:** `app.py`

The application provides several workflows:

### Ingest and Pipeline

Users can:
- Upload PDFs
- Process documents
- Extract page-level text
- Trigger fact extraction
- Store results

### Extracted Facts and Grounding

Users can:
- Browse extracted facts
- Search facts
- Filter by document
- Filter by fact type
- View confidence scores
- Inspect evidence quotes
- Inspect page numbers

### Cross-Document Reasoning

Users can:
- Compare facts across documents
- Discover relationships
- View classifications
- Inspect reasoning
- Inspect source evidence

### Failure Analysis and Edge Cases

The application documents and demonstrates difficult cases such as:

- Ambiguous semantic references
- Similar but different metrics
- Missing text
- Scanned/image-only PDFs
- Uncertain relationships

The goal is to make failure behavior visible rather than hiding uncertainty.

### Database and Provenance Explorer

Users can inspect the stored relational data:

- Documents
- Pages
- Facts
- Relationships

This provides an additional audit and debugging view.

---

## Required Demonstration Cases

The assignment requires the following four cases to be demonstrated:

### Case 1: CORROBORATES

Same underlying fact appears across documents, potentially using different wording.

**Flow:**
- Different wording → Metric normalization → Compatible context and value → CORROBORATES

### Case 2: CONTRADICTS

Same underlying fact and relevant timeframe/scope but incompatible values.

**Conditions:**
- Same metric
- Same context
- Same timeframe
- Conflicting values → CONTRADICTS

### Case 3: RECONCILES

Values differ, but the difference can be explained by context.

**Conditions:**
- Same underlying metric
- Different time, scope, or unit → RECONCILES

### Case 4: Failure and Edge Case Analysis

Examples include:

- Scanned PDFs
- Ambiguous wording
- Similar metrics
- Different units
- Different reporting periods
- Uncertain semantic match

The system handles these using validation, conservative candidate matching, confidence scoring, and documented limitations.

---

## Generalization

The system is designed to work beyond the starter documents. It does not depend on:

- Hard-coded facts
- Fixed document filenames
- Manually entered financial values
- Document-specific comparison rules

New PDFs can be uploaded through the UI and processed through the same pipeline.

---

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| User Interface | Streamlit |
| PDF Processing | PyMuPDF |
| Large Language Model | Google Gemini |
| Gemini SDK | google-genai |
| Data Validation | Pydantic |
| Database | SQLite |
| Environment Configuration | python-dotenv |
| Deployment | Streamlit Community Cloud |
| Version Control | Git and GitHub |

---

## AI Tools and Implementation

### Google Gemini

Gemini is used for:

- Structured fact extraction
- Semantic understanding
- Ambiguous relationship reasoning
- Generating explanations for complex cases

The application uses the official Google Gemini Python SDK.

### AI-Assisted Development

AI coding assistants were used during development for:

- Code scaffolding
- Debugging
- Refactoring
- Test development
- UI development
- Architecture exploration

AI-generated code was reviewed, tested, and integrated into the final implementation.

---

## Engineering Decisions and Trade-offs

### Why PyMuPDF?

PyMuPDF provides fast local PDF text extraction while preserving page boundaries. Page-level processing is important because provenance is a core requirement of the system.

### Why Gemini?

Gemini provides strong language understanding and structured output capabilities for extracting semantic and numerical information from unstructured documents.

### Why Pydantic?

Pydantic provides explicit schemas and validation between the extraction and storage layers. This reduces the risk of malformed LLM output entering the database.

### Why SQLite?

SQLite keeps the prototype simple and easy to run. It requires no external database server, minimal configuration, and simple persistence with relational integrity. For a production system, PostgreSQL or another scalable database would be more appropriate.

### Why Deterministic Normalization?

LLMs are powerful at language understanding but can incorrectly compare similar-looking metrics. Deterministic normalization provides explicit guardrails for metrics, units, predicates, dates, and scopes before relationship reasoning.

### Why Hybrid Reasoning?

Sending every possible fact pair to an LLM would increase latency, API usage, cost, and unpredictability. The hybrid approach provides:

```
Normalization → Candidate Filtering → Deterministic Reasoning → LLM for Ambiguous Cases
```

This provides a more practical architecture.

---

## Limitations

1. **Scanned PDFs:** Image-only PDFs may not contain machine-readable text. OCR support would be required for full scanned-document coverage.

2. **LLM Dependency:** Gemini-powered extraction and ambiguous reasoning require API access and available quota.

3. **Processing Time:** Large documents can require significant LLM processing. Batch processing and candidate pruning reduce unnecessary work, but asynchronous background processing would further improve scalability.

4. **SQLite Scalability:** SQLite is suitable for this prototype but is not designed for large-scale concurrent production workloads.

5. **Conservative Matching:** The system intentionally favors avoiding false-positive relationships over aggressively matching every potentially related fact. Some semantically related facts may not be linked.

6. **Duplicate Documents:** Uploading the same PDF multiple times may currently create separate document records.

7. **Complex PDF Layouts:** Highly complex layouts, tables, charts, or image-heavy documents may require additional specialized extraction or OCR.

---

## Deployment

The application is deployed using Streamlit Community Cloud.

**Live Application:** [Fact Knowledge Layer](https://fact-knowledge-layer-k3aduymuhfkcpnpjevsmyq.streamlit.app/)

The deployed application uses the GitHub repository with `app.py` as the Streamlit entry point. The Gemini API key is configured through Streamlit Secrets and is not stored in the repository.

---

## Extending Gemini Integration

To enable Gemini LLM extraction:

1. Add `google-generativeai` or `google-genai` to `requirements.txt`
2. Add your `GEMINI_API_KEY` to `.env`
3. In `services/fact_extractor.py`, implement structured output prompt with `gemini-1.5-pro` or `gemini-1.5-flash` using `response_schema=Fact`
4. In `services/relationship_engine.py`, prompt Gemini with candidate fact pairs to classify relationship type and produce explanatory reasoning grounded in evidence

---

## Video Demonstration

Full video explanation and demonstration: [Google Drive](https://drive.google.com/drive/folders/1oh58N44cLgBm01Bj3nJiglRnpqwjFTeB?usp=sharing)

The demonstration covers:

- PDF upload and processing
- Page-level extraction
- Fact extraction
- Evidence grounding
- Cross-document reasoning
- CORROBORATES demonstration
- CONTRADICTS demonstration
- RECONCILES demonstration
- Failure and edge-case analysis
- Database and provenance inspection

---

## Future Enhancements

A production-oriented version could add:

- OCR support for scanned PDFs
- Asynchronous background processing
- Job queues and progress tracking
- PostgreSQL database
- Cloud object storage
- Vector database for large-scale semantic retrieval
- Duplicate document detection
- User authentication
- Automated evaluation datasets
- Precision and recall metrics
- Human review workflow for low-confidence facts
- Incremental knowledge updates
- Improved table extraction
- Better handling of complex PDF layouts
- Multi-user support

---

## Security and Credentials

API credentials are intentionally excluded from the repository. The project uses:

- `.env` for local configuration
- `.gitignore` to exclude sensitive and generated files:
  - `.env`
  - `*.db`
  - `*.sqlite`
  - Uploaded PDFs

For deployment, the Gemini API key is stored using Streamlit's Secrets configuration and is never committed to version control.

---

## Additional Notes

- The system is designed to accept new PDFs through the UI
- Starter documents are not hard-coded into the reasoning engine
- Every extracted fact maintains source provenance
- Evidence quotes are retained with facts
- Page numbers are preserved during ingestion
- Deterministic normalization is used before expensive reasoning
- Ambiguous cases can be passed to Gemini for semantic reasoning
- The system exposes uncertainty rather than silently hiding it
- The application remains useful for PDF ingestion and inspection even when LLM functionality is unavailable
- The architecture prioritizes explainability and auditability over unnecessary complexity

---

## Support and Attribution

This project was developed as part of the Superjoin VIT 2026 Engineering Intern Hiring Assignment.

For questions or issues, please refer to the project repository or contact the development team.
