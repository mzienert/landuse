# La Plata County Land Use Code - Semantic Search Project

This project provides semantic search capabilities for the La Plata County Land Use Code, enabling efficient discovery and analysis of county regulations through natural language queries.

## Project Overview

This repository contains:
- Scraped La Plata County Land Use Code data
- Tools for semantic search implementation
- Local-first development setup optimized for Apple Silicon

## Local Development Setup

### System Requirements
- Apple Silicon (M4 Pro with 24GB RAM)
- Python 3.10+
- Homebrew (recommended for Python installation)

### Initial Setup

1. **Python Environment**
```bash
# The project uses a virtual environment in the 'env' directory
source env/bin/activate  # Activate the existing environment
```

2. **Install MLX (Required for Semantic Search)**
```bash
# Install MLX and related packages
pip install mlx mlx-lm

# Install additional dependencies if needed
pip install chromadb tqdm numpy
```

Note: The environment is already set up with basic dependencies. MLX installation is only required if you plan to work with the semantic search functionality.

## Technology Stack

### Core Components
- **Embedding Framework**: MLX (Apple-optimized)
- **Vector Database**: 
  - Development: Chroma (local)
  - Production: Pinecone (cloud-based)
- **Programming Language**: Python
- **Future UI/Deployment**: Vercel with Next.js

### Model Selection

We prioritize quantized models for efficient use of 24GB RAM. Current recommendations:

| Model | Dimensions | Size (Quantized) | Best For |
|-------|------------|------------------|----------|
| all-MiniLM-L6-v2 (Primary) | 384 | ~20MB (4-bit) | General purpose, county code analysis |
| BAAI/bge-small-en-v1.5 | 384 | ~50MB (4-bit) | Enhanced semantic search |
| paraphrase-MiniLM-L6-v2 | 384 | ~20MB (4-bit) | Variant phrasings |
| nomic-embed-text-v1.5 | 768 | ~100MB (4-bit) | Long-form documents |

### Model Setup

```bash
# Example: Converting and quantizing MiniLM
mlx_lm.convert --hf-path sentence-transformers/all-MiniLM-L6-v2 \
               --mlx-path local_mini_lm \
               --q_bits 4
```

## Implementation Guide

### 1. Data Processing Pipeline

```python
# Basic implementation structure
import json
from mlx_lm import load
import chromadb
from tqdm import tqdm

# Load and parse JSON
with open('data.json', 'r') as f:
    data = json.load(f)
texts = [item['content'] for item in data]

# Load model
model, tokenizer = load("mlx-community/all-MiniLM-L6-v2-4bit")

# Embedding generation
def embed_texts(texts):
    inputs = tokenizer(texts, return_tensors="np", padding=True)
    outputs = model(**inputs)
    return mx.mean(outputs.last_hidden_state, axis=1).array().tolist()

# Batch processing
batch_size = 128
all_embeddings = []
for i in tqdm(range(0, len(texts), batch_size)):
    batch = texts[i:i + batch_size]
    all_embeddings.extend(embed_texts(batch))

# Store in Chroma
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("county_codes")
ids = [str(i) for i in range(len(texts))]
metadatas = [{'text': t} for t in texts]
collection.upsert(ids=ids, embeddings=all_embeddings, metadatas=metadatas)
```

### 2. Hardware Optimization

- MLX automatically utilizes Apple Neural Engine/GPU
- Monitor RAM usage via Activity Monitor
- Debug with: `export MLX_VERBOSE=1`

### 3. Data Organization

```
project_root/
├── models/              # Local model storage
├── data/               # JSON and processed data
├── chroma_db/          # Local vector database
├── scripts/            # Processing scripts
└── notebooks/          # Development notebooks
```

## Performance Considerations

- **Batch Processing**: Default batch size of 128; adjust based on RAM usage
- **Model Quantization**: Use 4-bit quantization for optimal performance
- **Storage**: Monitor Chroma DB size for large datasets
- **Memory Management**: Implement streaming for large JSON files

## Future Scalability

1. **Cloud Migration Path**
   - Transition from Chroma to Pinecone for production
   - Implement serverless functions for API endpoints
   - Deploy web interface on Vercel

2. **Performance Optimization**
   - Fine-tune models for legal/administrative domain
   - Implement caching for frequent queries
   - Optimize batch sizes based on usage patterns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[Add your chosen license]
