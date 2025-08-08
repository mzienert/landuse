## RAG System Guide

This document describes the Retrieval-Augmented Generation (RAG) service that runs alongside the existing search API. It covers setup, starting/stopping, model loading, testing (streaming and non-streaming), and future enhancements.

### Overview

- Service: `rag_api.py` (Flask, port 8001)
- Script: `scripts/run_rag.sh` (start/stop/status/logs)
- Components:
  - `rag/inference.py`: MLX model manager for loading and generating
  - `rag/retrieval.py`: Calls existing search service to fetch top-K context, builds prompt with SOURCES
  - `rag_api.py`: Endpoints to load model and answer questions (streaming/non-streaming)
- Dependencies: MLX, MLX-LM, Flask, Flask-CORS, Requests (for retrieval calls)

Notes:
- The RAG service depends on the existing search API at `http://localhost:8000` for retrieval.
- The current implementation retrieves top-K passages and includes them in the prompt. Reranking and verification come later.

---

## Setup

Activate your virtual environment and install required packages:

```bash
source env/bin/activate
pip install mlx mlx-lm flask flask-cors requests
```

Ensure the search API is running (for retrieval):

```bash
./scripts/api.sh start
```

---

## Start/Stop RAG API

```bash
# Start RAG API (port 8001)
./scripts/run_rag.sh start

# Check status
./scripts/run_rag.sh status

# Tail logs
./scripts/run_rag.sh logs

# Stop RAG API
./scripts/run_rag.sh stop
```

Health check:

```bash
curl http://localhost:8001/rag/health | jq
```

Expected fields include: `model_loaded`, `mlx_available`, `model_id`, and endpoints.

---

## Load a Model (on demand)

Use a compatible MLX model. Example tested locally:

```bash
curl -X POST http://localhost:8001/rag/model/load \
  -H 'Content-Type: application/json' \
  -d '{"model_id":"mlx-community/Llama-3.1-8B-Instruct-4bit"}' | jq
```

Health should now report `model_loaded: true` and the `model_id`.

If you plan to use a legal fine-tune (e.g., Llama3-LegalLM) and an MLX variant is available, supply that `model_id` instead. Otherwise, use a compatible Llama 3 Instruct variant as fallback.

---

## Test Non-Streaming Answer

```bash
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{
    "query":"Summarize subdivision requirements in La Plata County",
    "collection":"la_plata_county_code",
    "num_results":5
  }' | jq
```

Response includes the `answer` and `sources` metadata. The answer is grounded on retrieved SOURCES included in the prompt.

---

## Test Streaming Answer (SSE)

```bash
curl -N -X POST http://localhost:8001/rag/answer/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "query":"Summarize subdivision requirements in La Plata County",
    "collection":"la_plata_county_code",
    "num_results":5
  }'
```

Stream events:
- `start`: indicates whether a model is loaded
- `token`: token/text chunks
- `error`: error details if generation fails
- `end`: end-of-stream marker, with final metadata fields

Note: Depending on MLX-LM version, generation may return full text. The service emulates streaming by chunking the text into word-like pieces.

---

## Heuristic Reranker (v1)

The RAG service applies a lightweight reranker to first-stage retrieval results before building the prompt.

- What it does
  - Scores each candidate by lexical overlap with the query (Jaccard over simple tokens)
  - Blends in the retrieval service's relevance when available
  - Enforces diversity: skips near-duplicates using a similarity threshold

- Defaults and knobs
  - `top_k`: up to 6 final chunks are selected (bounded by `num_results` in your request)
  - `diversity_threshold`: 0.8 Jaccard; higher = more aggressive de-duplication
  - `max_chunk_chars`: 1200 characters per chunk fed to the model

- How to test selection size
  - Ask for more initial results, e.g. `num_results: 8`; the reranker will reduce to ≤6 diverse passages
  ```bash
  curl -N -X POST http://localhost:8001/rag/answer/stream \
    -H 'Content-Type: application/json' \
    -d '{
      "query":"Summarize subdivision requirements in La Plata County",
      "collection":"la_plata_county_code",
      "num_results":8
    }'
  ```

- Limitations (by design for v1)
  - Uses simple lexical signals (fast, fully local)
  - May miss semantically relevant content with low lexical overlap
  - Future: evaluate adding a small cross-encoder or better semantic rerank

---

## Citations and Sources

Non-stream responses include:
- `answer`: final text; the model is instructed to include citations like `[1]`, `[2]` that refer to SOURCES.
- `citations`: array of `{ marker, id, collection }` extracted from the answer.
- `sources`: the subset of retrieved sources actually referenced in `answer` (each includes `index`, `id`, `collection`, `preview`, and `chunk`).

Behavior:
- The prompt enforces citation usage for material claims.
- If the model omits markers, a best-effort auto-citation fallback analyzes overlap and inserts minimal citations (and will attach at least `[1]` if any sources exist).
- Streaming endpoint does not include final citations (no buffering). Use the non-stream endpoint when you need structured `citations`/`sources` in the response.

Example (non-stream):
```bash
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{
    "query":"Summarize subdivision requirements in La Plata County",
    "collection":"la_plata_county_code",
    "num_results":6
  }' | jq '{answer, citations, sources}'
```

---

## Lightweight Verification (v1)

Non-stream responses include a verification report based on lexical support checks:

- What it does
  - Splits the answer into sentences and checks each against retrieved source chunks using token-level Jaccard overlap.
  - Appends a citation marker [n] to supported sentences when missing; flags unsupported ones with “(insufficient support)”.
  - Returns `verification` with counts and per-sentence details.

- Where to see it
  - Non-stream endpoint returns `verification` and the annotated `answer`.
  - Streaming endpoint does not include verification (no buffering).

Example (non-stream):
```bash
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{
    "query":"Summarize subdivision requirements in La Plata County",
    "collection":"la_plata_county_code",
    "num_results":6
  }' | jq '{answer, citations, sources, verification}'
```

---

## Request Fields

- `query` (string, required): user question
- `collection` (string): `la_plata_county_code` or `la_plata_assessor` (defaults to code)
- `num_results` (int): retrieval K (1–10)
- Optional generation controls (currently may be ignored by some MLX-LM versions):
  - `max_tokens` (int)
  - `temperature` (float)
  - `top_p` (float)

---

## Troubleshooting

- Model not loaded: Load a model via `/rag/model/load`.
- Retrieval errors: Ensure the search API (`./scripts/api.sh start`) is running on port 8000.
- MLX argument issues: The service uses a minimal call; version differences are handled by fallbacks and streaming emulation.
- Performance: If generation is slow or OOMs, try a smaller model/quantization (e.g., 4-bit). Close other memory-intensive apps.

### No citations returned
- Ensure the search API is running and returning results (citations only appear when sources exist):
  ```bash
  ./scripts/api.sh status
  curl "http://localhost:8000/search/simple?query=Subdivision%20requirements&collection=la_plata_county_code&num_results=5" | jq
  ```
- If `results` is empty, build embeddings or fix data. If retrieval works but `citations` is still empty, use non-stream endpoint and confirm `sources` is non-empty; auto-citation will then attach minimal markers.

---

## Current Limitations (to be addressed in later steps)

- No reranking: passages are taken as-is from first-stage retrieval
- No strict citation enforcement or post-answer verification
- Streaming is best-effort and can be word-level depending on backend

---

## Future Enhancements (Notes)

- UI comparison mode: When a UI is available, display the baseline (previous step) answer side-by-side with the augmented (RAG) answer for comparison.
- Heuristic reranker: Reorder candidates via short-window cosine boosts, redundancy penalties, and source diversity.
- Strict citation policy: Enforce that claims are supported by SOURCES; add inline markers [1], [2] and a sources section.
- Lightweight verification: Post-generate support check; remove or soften unsupported statements.
- Configurable parameters: Expose K, chunk sizes, and generation controls in the UI.
- Sessioning and feedback: Store conversations and thumbs up/down; learn from feedback.
- Caching: Retrieval and prompt+sources generation caches.
- Evaluation harness: Gold Q&A set with metrics (hit@k, citation precision, supported-claims ratio, latency, token usage).
- Observability: Structured logs and dashboards for latency and usage.
- Retrieval quality:
  - Filter out “Reserved” sections during retrieval to reduce noise before reranking.
  - Add a small post-processor to clean incomplete/dangling citation tokens (e.g., a trailing "[4").


