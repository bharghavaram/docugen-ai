> **📅 Project Period:** Dec 2024 – Feb 2025 &nbsp;|&nbsp; **Status:** Completed &nbsp;|&nbsp; **Author:** [Bharghava Ram Vemuri](https://github.com/bharghavaram)

# 📄 DocuGen AI – Intelligent Document Generation & Summarisation Platform

> **End-to-end GenAI platform using Claude and Mistral to ingest unstructured data and generate tailored business documents with 88% accuracy.**

## Overview

DocuGen AI transforms unstructured source documents into professional, structured outputs using LlamaIndex for document processing, ChromaDB for semantic retrieval, and Claude/Mistral for generation. Includes a Streamlit UI for non-technical users.

**Key Metrics:**
- 📄 300+ files processed at 88% accuracy
- ⚡ 55% reduction in report generation time
- 🔍 ChromaDB semantic retrieval with ReAct query routing
- 🎨 Streamlit UI for easy document management

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM Framework | LlamaIndex |
| LLMs | Anthropic Claude 3.5 Sonnet, Mistral Large |
| Vector Store | ChromaDB (persistent) |
| API | FastAPI |
| UI | Streamlit |
| Document Processing | PyPDF, python-docx |

## Document Generation Pipeline

```
Source Documents (PDF/TXT/DOCX/MD)
        │
        ▼
  LlamaIndex Document Loader
        │
        ▼
  Sentence Splitter (512 chunks / 64 overlap)
        │
        ▼
  ChromaDB Vector Storage (persistent)
        │
        ▼
  ReAct Query Engine ──── User Request
        │
        ▼
  Tree Summarise Synthesizer
        │
        ▼
  Claude / Mistral Generation
        │
        ▼
  Structured Document Output
```

## Quick Start

```bash
git clone https://github.com/bharghavram/docugen-ai.git
cd docugen-ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your Anthropic and Mistral API keys

# Start FastAPI server
uvicorn main:app --reload

# Start Streamlit UI (separate terminal)
streamlit run pages/app.py
```

- API Docs: `http://localhost:8000/docs`
- Streamlit UI: `http://localhost:8501`

## Document Types

| Template | Description |
|----------|-------------|
| `executive_summary` | 500-word summary with key findings |
| `technical_report` | Full 7-section technical report |
| `business_proposal` | ROI-focused proposal with timeline |
| `meeting_notes` | Action items and decisions |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload source documents |
| `POST` | `/api/v1/documents/generate` | Generate a document |
| `POST` | `/api/v1/documents/summarise` | Summarise text |
| `GET` | `/api/v1/documents/templates` | List templates |
| `GET` | `/api/v1/documents/stats` | Index statistics |

### Example: Generate Executive Summary

```bash
curl -X POST "http://localhost:8000/api/v1/documents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Generate a Q3 2024 performance summary focusing on revenue growth and market expansion",
    "doc_type": "executive_summary",
    "llm_provider": "claude"
  }'
```

### Example: Quick Summarise

```bash
curl -X POST "http://localhost:8000/api/v1/documents/summarise" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your long text here...", "style": "executive"}'
```

## Docker

```bash
docker build -t docugen-ai .
docker run -p 8000:8000 -p 8501:8501 --env-file .env docugen-ai
```

## Tests

```bash
pytest tests/ -v
```

---

*Built by Bharghava Ram Vemuri | Dec 2024 – Feb 2025*
