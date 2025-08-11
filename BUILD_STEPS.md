# Build Steps - La Plata County Search API

Detailed step-by-step instructions for setting up the complete semantic search system from scratch.

## Prerequisites

- **Hardware**: Apple Silicon Mac (M4 Pro with 24GB RAM recommended)
- **Software**: Python 3.10+, Git
- **Data**: La Plata County Land Use Code JSON file in `la_plata_code/full_code.json`

## Step 1: Install Dependencies

```bash
# Install core ML dependencies
pip install mlx mlx-lm sentence-transformers

# Install vector database and utilities
pip install chromadb tqdm numpy

# Install JSON processing utilities
pip install ijson  # For streaming large JSON files
```

## Step 2: Prepare the Model

**Note**: `mlx-lm` doesn't support BERT-based embedding models. We'll use `sentence-transformers` with MLX optimization instead.

### Option A: Use Sentence Transformers with MLX Backend (Recommended)
```bash
# Test model loading
python -c "
from sentence_transformers import SentenceTransformer
import mlx.core as mx
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Model loaded successfully')
print(f'MLX available: {mx.metal.is_available()}')
"
```

### Option B: Use Alternative MLX-Compatible Model
If you want to use MLX directly, use a supported model:
```bash
# Test with a language model that supports MLX
python -c "
from mlx_lm import load
model, tokenizer = load('mlx-community/Mistral-7B-Instruct-v0.1-4bit')
print('MLX model loaded successfully')
"
```

## Step 3: Create the Embedding Script

Create `apis/search/embeddings/create_legal_embeddings.py`:

```python

```

## Step 4: Run the Embedding Creation

```bash
# Execute the embedding creation script
python apis/search/embeddings/create_legal_embeddings.py
```

Expected output:
```
Loading JSON data from ./la_plata_code/full_code.json...
Loaded 1298 sections
Loading MLX model...
Model loaded successfully
Creating embeddings for 1298 chunks...
Processing batches: 100%|██████████| 41/41 [02:15<00:00,  3.31s/it]
Generated 1298 embeddings
Setting up ChromaDB at ./chroma_db...
ChromaDB collection ready: 0 existing documents
Storing embeddings in ChromaDB...
Storing batches: 100%|██████████| 13/13 [00:05<00:00,  2.31it/s]
Stored 1298 documents in ChromaDB
✅ Vector embeddings created successfully!
📊 Total sections processed: 1298
🗂️  Database location: ./chroma_db
🔍 Ready for semantic search queries
```

## Step 5: Test the Embeddings

Create `test_search.py`:

```python

```

```bash
python test_search.py
```

## Performance Notes

- **Processing Time**: ~2-3 minutes for 1,298 sections on M4 Pro
- **Memory Usage**: Peak ~8GB RAM during embedding generation
- **Storage**: ~50MB for ChromaDB with embeddings
- **Batch Size**: Reduce to 16 if experiencing memory issues

## Troubleshooting

### Memory Issues
```bash
# Reduce batch size in the script
BATCH_SIZE = 16  # or even 8 for lower memory systems
```

### Model Loading Errors
```bash
# Clear MLX cache and reinstall
pip uninstall mlx mlx-lm
pip install mlx mlx-lm
```

### ChromaDB Issues
```bash
# Reset database
rm -rf ./chroma_db
# Re-run the embedding script
```

## Step 6: Start the API Server

Install Flask dependencies and start the server:

```bash
pip install flask flask-cors
```

**Start API Server:**
```bash
./scripts/api.sh start
```

**Verify API is running:**
```bash
./scripts/api.sh status
curl "http://localhost:8000/health"
```

Expected output:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "database_connected": true,
  "document_count": 1298
}
```

## Step 7: Test the Search API

**Basic search test:**
```bash
curl "http://localhost:8000/search/simple?query=building%20permits&num_results=3"
```

**Expected search response format:**
```json
{
  "query": "building permits",
  "results": [
    {
      "section": "2538",
      "text": "Chapter 2 ADMINISTRATION...",
      "relevance": "0.798"
    }
  ]
}
```

## Troubleshooting

### Build Issues

**Memory problems during embedding generation:**
```bash
# Reduce batch size in apis/search/embeddings/create_legal_embeddings.py
BATCH_SIZE = 16  # Instead of 32
```

**Model loading errors:**
```bash
pip uninstall sentence-transformers
pip install sentence-transformers
```

**ChromaDB issues:**
```bash
rm -rf ./chroma_db
python apis/search/embeddings/create_legal_embeddings.py  # Recreate embeddings
```

### API Issues

**Port already in use:**
```bash
./scripts/api.sh stop
./scripts/api.sh start
```

**Virtual environment not found:**
```bash
# Ensure you're running from project root directory
cd /path/to/landuse
./scripts/api.sh start
```

## Performance Optimization

**For lower memory systems:**
- Reduce `BATCH_SIZE` in `apis/search/embeddings/create_legal_embeddings.py` to 16 or 8
- Monitor Activity Monitor during processing

**For faster processing:**
- Increase `BATCH_SIZE` to 64 if you have sufficient RAM
- Ensure MLX is properly utilizing Apple Silicon

---

# Next Phase: RAG Bring-Up (Local, MLX)

This section outlines the steps we will take to add a Retrieval-Augmented Generation service that uses our existing ChromaDB collections and an MLX-hosted LLM.

## RAG Prerequisites
- Apple Silicon with 24GB RAM (M4 Pro) recommended
- Python venv `env` activated
- Existing ChromaDB at `./chroma_db` with both collections populated
- Hugging Face access for model download (Llama3-LegalLM or fallback)

## RAG Dependencies
```bash
pip install mlx flask flask-cors chromadb sentence-transformers tqdm numpy sse-starlette
```

## Model Sourcing
- Preferred: Llama3-LegalLM (from Hugging Face). If unavailable:
  - Fallback to Llama 3 Instruct variant compatible with MLX OR a legal LoRA fine-tune
- Quantization: Try 8-bit on 24GB; if OOM or slow, fall back to 4-bit
- Context window: aim for 8K–16K tokens; tune prompt/packing accordingly

## Service Topology
- Search API at `apis/search/search_api.py` (retrieval/search service)
- RAG API at `apis/rag/rag_api.py` that:
  - Loads the model via MLX
  - Exposes `/rag/answer` (JSON POST) and `/rag/answer/stream` (SSE) for streamed tokens
  - Orchestrates: retrieve → heuristic rerank → pack → generate → verify → respond with citations

## Retrieval & Packing (Initial Policy)
- Use existing collections: `la_plata_county_code`, `la_plata_assessor`
- Fetch top-K (e.g., 12) candidates per collection depending on selection
- Heuristic rerank: boost high cosine-similarity windows; penalize near-duplicates; ensure cross-source diversity
- Pack 3–6 best chunks (1,000–1,500 chars each, ~150 overlap) with headers and stable IDs for citations

## Prompting & Citations
- System prompt: legal accuracy, cite every material claim, include disclaimer
- User template: question + packed contexts
- Output format: answer with inline numeric citations [1], [2], plus a citations section mapping to `section`/`account` and collection

## Lightweight Verification
- For each answer sentence, verify at least one supporting chunk meets a similarity threshold; otherwise soften or remove unsupported claims

## Running RAG (planned)
```bash
# Start Search API (if not running)
./scripts/api.sh start

# Start RAG API (to be added)
./scripts/run_rag.sh start

# Test
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What are subdivision requirements for minor subdivisions?",
    "collection": "la_plata_county_code",
    "num_results": 6
  }'
```

## Evaluation Harness (planned)
- Provide a CLI to run a small gold set and report retrieval hit@k, citation precision, supported-claims ratio, latency, and token usage

## Troubleshooting RAG
- OOM during model load: switch to lower-bit quantization
- Long latency: reduce max_tokens, temperature; lower K; reduce packed chunk sizes
- Weak citations: increase K, tweak rerank weights, add diversity constraint