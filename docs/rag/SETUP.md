# RAG System Setup Guide

## Overview

This guide covers the complete setup process for the La Plata County RAG system, from dependencies to running your first query.

## Prerequisites

- **Python**: 3.8+ with virtual environment support
- **System**: macOS or Linux with sufficient RAM (8GB+ recommended)
- **Storage**: 5GB+ free space for models and vector database

## Installation Steps

### 1. Environment Setup

Create and activate a virtual environment:

```bash
python3 -m venv env
source env/bin/activate
```

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install mlx mlx-lm flask flask-cors requests
```

**Core Dependencies:**
- `mlx` + `mlx-lm`: Apple Silicon optimized ML inference
- `flask` + `flask-cors`: Web API framework with CORS support
- `requests`: HTTP client for Search API integration

### 3. Verify Search API

The RAG service depends on the existing search API for retrieval. Ensure it's running:

```bash
# Start search API (port 8000)
./scripts/api.sh start

# Verify it's working
curl "http://localhost:8000/health"
```

Expected response:
```json
{
  "status": "healthy",
  "collections": ["la_plata_county_code", "la_plata_assessor"]
}
```

### 4. Start RAG API

Launch the RAG service:

```bash
# Start RAG API (port 8001)
./scripts/run_rag.sh start
```

The service will:
- Auto-load the default Qwen thinking model
- Establish connection to search API
- Configure endpoints and health checks

### 5. Verify Installation

Check that both APIs are operational:

```bash
# Combined health check
./scripts/start_both.sh status
```

You should see:
```
✅ Overall Status: Both APIs running
```

## Model Configuration

### Default Model

The system automatically loads `mlx-community/Qwen3-4B-Thinking-2507-8bit`:
- **Type**: Thinking model with explicit reasoning
- **Size**: ~4GB with 8-bit quantization
- **Strengths**: Legal reasoning, citation generation

### Alternative Models

If you need a different model, load it manually:

```bash
# Load Llama fallback model
curl -X POST http://localhost:8001/rag/model/load \
  -H 'Content-Type: application/json' \
  -d '{"model_id":"mlx-community/Llama-3.1-8B-Instruct-4bit"}'
```

### Model Selection Criteria

**For Legal Use (Recommended)**:
```json
{
  "model_id": "mlx-community/Qwen3-4B-Thinking-2507-8bit",
  "benefits": ["explicit reasoning", "citation generation", "legal analysis"]
}
```

**For Performance**:
```json
{
  "model_id": "mlx-community/Llama-3.1-8B-Instruct-4bit", 
  "benefits": ["faster inference", "lower memory", "general purpose"]
}
```

## Configuration Options

### Environment Variables

Set these in your shell or `.env` file:

```bash
# Model selection
export DEFAULT_MODEL_ID="mlx-community/Qwen3-4B-Thinking-2507-8bit"

# API endpoints
export SEARCH_BASE_URL="http://localhost:8000"
export RAG_PORT="8001"

# Performance tuning
export MAX_CHUNK_CHARS="3000"
export DEFAULT_MAX_TOKENS="1200"
```

### Runtime Configuration

Modify settings in `apis/rag/rag_api.py`:

```python
RAG_CONFIG = {
    "service": "RAG API",
    "version": "0.1.0",
    "model": {
        "default": DEFAULT_MODEL_ID,
        "quantization": "8-bit preferred; fallback to 4-bit",
        "context_window": "8K–16K tokens",
    },
    "retrieval": {
        "store": "ChromaDB",
        "collections": ["la_plata_county_code", "la_plata_assessor"],
        "rerank": "heuristic v1 (cosine boost, redundancy penalty, diversity)",
    },
}
```

## First Test

### Health Check

Verify everything is working:

```bash
curl http://localhost:8001/rag/health | jq
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "mlx_available": true,
  "model_id": "mlx-community/Qwen3-4B-Thinking-2507-8bit",
  "streaming": true,
  "endpoints": ["/rag/health", "/rag/config", "/rag/model/load", "/rag/answer", "/rag/answer/stream"]
}
```

### First Query

Test with a simple legal question:

```bash
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What are the requirements for building permits?",
    "collection": "la_plata_county_code",
    "num_results": 5
  }' | jq .answer
```

You should receive a detailed answer with citations like `[1]`, `[2]` referencing the provided sources.

### Streaming Test

Test the real-time streaming endpoint:

```bash
curl -N -X POST http://localhost:8001/rag/answer/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Explain subdivision requirements in La Plata County",
    "collection": "la_plata_county_code",
    "num_results": 5
  }'
```

You should see Server-Sent Events with:
- `start`: Initial metadata
- `token`: Streaming text chunks  
- `end`: Final completion marker

## Troubleshooting

### Common Issues

**Model fails to load**:
```bash
# Check MLX availability
python3 -c "import mlx_lm; print('MLX available')"

# Check disk space
df -h

# Try 4-bit model instead
curl -X POST http://localhost:8001/rag/model/load \
  -H 'Content-Type: application/json' \
  -d '{"model_id":"mlx-community/Llama-3.1-8B-Instruct-4bit"}'
```

**Search API not responding**:
```bash
# Check search API status
./scripts/api.sh status

# Restart if needed
./scripts/api.sh restart
```

**Empty responses or no citations**:
```bash
# Verify search API has data
curl "http://localhost:8000/search/simple?query=building&collection=la_plata_county_code&num_results=3"

# Check for results array
```

**Memory issues**:
- Close other applications
- Use 4-bit quantization models
- Reduce `max_tokens` in requests
- Monitor system memory: `htop` or Activity Monitor

### Performance Optimization

**For better accuracy**:
- Use 8-bit models when possible
- Increase `num_results` in queries
- Lower temperature (0.2-0.3) for deterministic results

**For better speed**:
- Use 4-bit models
- Reduce `max_tokens` to 600-800
- Decrease `num_results` to 3-5
- Enable response caching

### Log Analysis

Check service logs for issues:

```bash
# RAG API logs
./scripts/run_rag.sh logs

# Search API logs  
./scripts/api.sh logs

# Combined status
./scripts/start_both.sh test
```

## Advanced Configuration

### Custom Collections

To use different document collections:

```python
# In your API request
{
  "query": "property assessment procedures", 
  "collection": "la_plata_assessor",  # Switch to assessor data
  "num_results": 8
}
```

### Tuning Parameters

For legal queries requiring high precision:

```python
query_config = {
    "collection": "la_plata_county_code",
    "num_results": 12,
    "max_tokens": 1500,
    "temperature": 0.2,
    "top_p": 0.85
}
```

For general questions requiring speed:

```python
query_config = {
    "collection": "la_plata_county_code", 
    "num_results": 6,
    "max_tokens": 800,
    "temperature": 0.4,
    "top_p": 0.9
}
```

## Next Steps

After successful setup:

1. **Read** [USAGE.md](./USAGE.md) for detailed API documentation
2. **Review** [ARCHITECTURE.md](./ARCHITECTURE.md) to understand system design  
3. **Explore** [TUNING.md](./TUNING.md) for performance optimization
4. **Check** [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues

## Production Considerations

When moving beyond local development:

- **Security**: Enable authentication, input validation, rate limiting
- **Scaling**: Consider cloud deployment (AWS Bedrock, Pinecone)
- **Monitoring**: Add structured logging, metrics collection
- **Backup**: Document and model versioning strategies
- **Testing**: Automated quality assurance pipelines