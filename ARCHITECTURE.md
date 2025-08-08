## Architecture Overview

This document summarizes the current system and the proposed RAG extension that builds on the existing semantic search and data pipeline.

### Current Architecture

- Data Sources
  - La Plata County Land Use Code (`la_plata_code/full_code.json`)
  - Property Assessor MDB (exported to CSV; composed descriptions stored in `assessor_data/property_descriptions.json`)

- Embeddings & Vector Store
  - Model: `intfloat/e5-large-v2` (1024D)
  - Store: ChromaDB (persistent at `./chroma_db`)
  - Collections:
    - `la_plata_county_code` (section text, metadata: `section_id`, `full_text_length`)
    - `la_plata_assessor` (property descriptions, metadata: `account_number`, `text_length`)

- Backend API (Search)
  - Flask app `search_api.py`
  - Endpoints: `/health`, `/collections`, `/search`, `/search/simple`
  - Responsibilities: model loading, embedding queries, vector retrieval, response formatting

- Frontend (Next.js)
  - User-facing pages: landing (`/`), search (`/search`), protected dashboard (`/protected`)
  - Client fetches from `http://localhost:8000` search API
  - NextAuth credentials auth; Postgres via Drizzle (`app/db.ts`)

- Scripts
  - `create_embeddings.py`, `create_assessor_embeddings.py`
  - `scripts/api.sh` for starting/stopping Flask API
  - Scrapers for code and assessor site (Selenium)

### Proposed RAG Extension

- Objectives
  - Grounded Q&A with citations using our corpora
  - Local LLM inference on Apple Silicon via MLX
  - Streaming responses with inline and endnote citations

- Model
  - Primary: Llama3-LegalLM (Hugging Face)
  - Fallback: Llama 3 Instruct or legal LoRA
  - Quantization: 8-bit preferred on 24GB M4 Pro; fall back to 4-bit as needed
  - Context window: 8K–16K tokens

- Topology & Separation of Concerns
  - Keep existing `search_api.py` (retrieval-only)
  - Add a separate `rag_api.py` for end-to-end RAG (retrieve → rerank → pack → generate → verify → cite)

- RAG Pipeline
  1) Query normalization/rewrite (optional)
  2) Retrieve top-K from ChromaDB across selected collection(s)
  3) Heuristic rerank and diversification
  4) Context packing (1,000–1,500 chars per chunk; preserve `section`/`account` and collection in headers)
  5) LLM generation with MLX (streaming)
  6) Lightweight verification (support threshold per sentence)
  7) Response with inline citations and a sources map

- API Endpoints (rag_api)
  - `POST /rag/answer` (JSON): returns answer, citations, sources
  - `POST /rag/answer/stream` (SSE): streams tokens + partial citations
  - `GET /rag/health`, `GET /rag/config`

- Frontend Additions (later phase)
  - Chat UI with streaming, controls (temperature, max tokens), collection selector
  - Sources side panel with previews and highlights

- Storage & Telemetry (later phase)
  - Conversation and feedback tables in Postgres (reuse auth)
  - Logs for retrieval/generation latency, token usage, selected sources

### Reranking Strategy (Initial)

- Rationale: First-stage vector retrieval is recall-oriented; reranking improves precision
- Heuristic approach (no heavy cross-encoders):
  - Boost passages with high short-window cosine similarity to the query
  - Penalize near-duplicate passages (similarity between candidates)
  - Enforce diversity across different sections/accounts
- Future option: evaluate a small local cross-encoder reranker if latency budget allows

### Evaluation Plan

- Gold Q&A set with expected source sections/accounts
- Metrics: retrieval hit@k, citation precision, supported-claims ratio, end-to-end latency, token usage
- CLI harness for batch evaluation

### Safety

- Legal disclaimer (not legal advice)
- Require citations; block unsupported legal conclusions
- Prompt-injection mitigation by fencing document content and ignoring embedded instructions


