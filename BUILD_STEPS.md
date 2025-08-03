# La Plata County Land Use Code - Vector Embeddings Setup

Step-by-step guide to create vector embeddings from the La Plata County Land Use Code JSON data.

## Prerequisites

- Apple Silicon Mac (M4 Pro with 24GB RAM recommended)
- Python 3.10+
- Virtual environment activated: `source env/bin/activate`

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

Create `create_embeddings.py`:

```python

```

## Step 4: Run the Embedding Creation

```bash
# Execute the embedding creation script
python create_embeddings.py
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

## Step 6: HTTP API Setup

Create a simple HTTP API to serve the search functionality:

### Install Flask
```bash
pip install flask flask-cors
```

### Start the API Server

**Option A: Using the management script (Recommended)**
```bash
# Start the API in background
./api.sh start

# Check status
./api.sh status

# View logs
./api.sh logs

# Stop the API
./api.sh stop

# Restart the API
./api.sh restart
```

**Option B: Direct Python execution**
```bash
python search_api.py
```

The server will start at `http://localhost:8000`

### API Endpoints

**Health Check:**
```bash
curl "http://localhost:8000/health"
```

**Simple Search:**
```bash
curl "http://localhost:8000/search/simple?query=building%20permits&num_results=3"
```

**Full Search (GET):**
```bash
curl "http://localhost:8000/search?query=zoning%20requirements&num_results=5"
```

**Full Search (POST):**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "subdivision regulations", "num_results": 3}'
```

### Example Response
```json
{
  "query": "building permits",
  "results": [
    {
      "relevance": "-0.202",
      "section": "77",
      "text": "Chapter 2 ADMINISTRATION..."
    }
  ]
}
```

## Next Steps

After successful API setup:
1. Build web interface for querying
2. Add query result ranking and filtering
3. Consider fine-tuning models for legal domain
4. Deploy to production environment