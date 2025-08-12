# Search API Setup Guide

## Overview

This guide covers the complete setup process for the La Plata County Search API, from installation to creating your first embeddings and performing searches.

## Prerequisites

- **Python**: 3.8+ with virtual environment support
- **System**: macOS or Linux with sufficient RAM (4GB+ recommended for embeddings)
- **Storage**: 2GB+ free space for models and vector database
- **Tools**: `mdb-tools` for processing Access databases (optional, for assessor data)

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
pip install flask flask-cors chromadb sentence-transformers numpy tqdm
```

**Core Dependencies:**
- `flask` + `flask-cors`: Web API framework with CORS support
- `chromadb`: Vector database for embedding storage
- `sentence-transformers`: Embedding model infrastructure
- `numpy` + `tqdm`: Numerical computing and progress tracking

### 3. Verify Installation

Test that key packages are working:

```bash
python3 -c "import chromadb, sentence_transformers; print('✅ Dependencies installed')"
```

## Data Preparation

### Legal Code Embeddings

The legal code data should already be scraped and processed. If you need to create embeddings:

```bash
# Create legal code embeddings (requires la_plata_code/full_code.json)
cd /Users/matthewzienert/Documents/landuse
python apis/search/embeddings/create_legal_embeddings.py
```

**Expected Output**:
```
🚀 Starting embedding generation with ULTRA-aggressive memory management
📦 Micro-batch size: 1 (single item processing)
Loading JSON data from ../../../la_plata_code/full_code.json...
Loaded 1298 sections
Loading sentence transformer model...
Model loaded successfully: intfloat/e5-large-v2 (1024 dimensions)
Creating embeddings for 1298 chunks...
```

This process takes 5-15 minutes depending on your system.

### Property Assessment Embeddings (Optional)

If you have access to the assessor database:

```bash
# Create assessor embeddings (requires LPC-Assessor-Data-Files/AssessorData.mdb)
python apis/search/embeddings/create_assessor_embeddings.py
```

**Note**: This requires the Access database file and `mdb-tools` for export.

## Service Configuration

### Application Factory Pattern

The Search API uses environment-based configuration with three modes:

#### Environment Variables

```bash
# Core settings (with defaults)
export FLASK_ENV=development           # development|testing|production
export SECRET_KEY=your-secret-key      # Required for production
export PORT=8000                       # API port
export HOST=0.0.0.0                   # Bind address

# Search Engine settings
export EMBEDDING_MODEL=intfloat/e5-large-v2  # Embedding model
export CHROMA_DB_PATH=./chroma_db      # Vector database path
export DEFAULT_SEARCH_LIMIT=10         # Default result limit
export MAX_SEARCH_LIMIT=50            # Maximum result limit
```

#### Configuration Modes

**Development Mode (default)**:
```bash
export FLASK_ENV=development
# Debug enabled, uses file-based ChromaDB
```

**Testing Mode**:
```bash
export FLASK_ENV=testing
# In-memory ChromaDB, isolated configuration
```

**Production Mode**:
```bash
export FLASK_ENV=production
export SECRET_KEY=your-production-secret
# File logging enabled, debug disabled
```

### Default Configuration

The search API is pre-configured with these collections:

```python
AVAILABLE_COLLECTIONS = {
    'la_plata_county_code': {
        'name': 'Land Use Code',
        'model': 'intfloat/e5-large-v2',
        'dimensions': 1024,
        'description': 'La Plata County Land Use Code regulations'
    },
    'la_plata_assessor': {
        'name': 'Property Assessor Data', 
        'model': 'intfloat/e5-large-v2',
        'dimensions': 1024,
        'description': 'Property assessment and ownership data'
    }
}
```

### Environment Variables (Optional)

Set these for custom configuration:

```bash
# Service configuration
export SEARCH_PORT="8000"
export CHROMA_DB_PATH="./chroma_db"
export SEARCH_LOG_LEVEL="INFO"

# Model configuration
export EMBEDDING_MODEL="intfloat/e5-large-v2"
export MAX_RESULTS_LIMIT="50"
```

## Start Search API

### Using Management Script (Recommended)

```bash
# Start with default (development) configuration
./scripts/api.sh start

# Or with specific environment
export FLASK_ENV=production
./scripts/api.sh start
```

**Expected Output**:
```
Starting La Plata County Search API...
✅ API started successfully!
   PID: 12345
   Port: 8000
   URL: http://localhost:8000
   Logs: /path/to/api.log
```

### Direct Python Execution

```bash
# Run directly from project root
cd /Users/matthewzienert/Documents/landuse
python -m apis.search.search_api

# Or with specific environment
export FLASK_ENV=testing
python -m apis.search.search_api

# Or production mode
export FLASK_ENV=production
export SECRET_KEY=your-secret
python -m apis.search.search_api
```

**Expected Output**:
```
INFO:__main__:Starting Flask server in development mode...
INFO:__main__:Connecting to ChromaDB...
INFO:__main__:Loading model: intfloat/e5-large-v2
INFO:__main__:Model loaded: intfloat/e5-large-v2 (1024 dimensions)
INFO:__main__:Connected to collection 'la_plata_county_code': 1298 documents
INFO:__main__:Search system initialized successfully
INFO:__main__:Starting Flask server...
 * Running on http://127.0.0.1:8000
```

## Verification and Testing

### Health Check

Verify the API is running:

```bash
curl http://localhost:8000/health | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
```

**Expected Response**:
```json
{
  "status": "healthy",
  "models_loaded": 1,
  "collections_connected": 1,
  "total_documents": 1298,
  "available_collections": ["la_plata_county_code"]
}
```

### Collection Information

Check available collections:

```bash
curl http://localhost:8000/collections | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
```

### First Search Test

Test with a simple legal query:

```bash
curl "http://localhost:8000/search/simple?query=building%20permits&collection=la_plata_county_code&num_results=3" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
```

**Expected Response**:
```json
{
  "query": "building permits",
  "collection": "la_plata_county_code",
  "collection_name": "Land Use Code",
  "results": [
    {
      "text": "Building permits are required for construction...",
      "relevance": "0.892",
      "collection": "la_plata_county_code", 
      "section": "18-35"
    }
  ]
}
```

### Full Search Test

Test the complete search endpoint:

```bash
curl -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "subdivision requirements",
    "collection": "la_plata_county_code",
    "num_results": 5
  }' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
```

## Integration with RAG API

If you're running the RAG API, it should automatically connect to the search API:

```bash
# Start both APIs together
./scripts/start_both.sh start

# Test integration
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query": "What are building permit requirements?"}'
```

The RAG API will use the search API for document retrieval.

## Service Management

### Status Checking

```bash
# Check if running
./scripts/api.sh status

# View logs
./scripts/api.sh logs

# Restart if needed
./scripts/api.sh restart
```

### Stop Service

```bash
# Stop search API
./scripts/api.sh stop

# Or stop both APIs
./scripts/start_both.sh stop
```

## Troubleshooting Common Issues

### ChromaDB Not Found

**Error**: `Collection [collection_name] does not exist`

**Solution**: Create embeddings first:
```bash
python apis/search/embeddings/create_legal_embeddings.py
```

### Model Loading Errors

**Error**: `sentence_transformers` import issues

**Solution**: Reinstall with specific versions:
```bash
pip install sentence-transformers==2.2.2 torch torchvision
```

### Memory Issues During Embedding Creation

**Error**: Out of memory during embedding generation

**Solution**: The scripts use micro-batch processing, but you can:
```bash
# Close other applications
# Monitor memory usage: htop or Activity Monitor
# Reduce batch size in embedding script if needed
```

### Port Already in Use

**Error**: `Address already in use` on port 8000

**Solution**:
```bash
# Find process using port
lsof -i :8000

# Kill process if needed
kill [PID]

# Or use different port
export SEARCH_PORT=8001
```

### Empty Search Results

**Issue**: Searches return empty results

**Debug Steps**:
```bash
# Check collection health
curl http://localhost:8000/collections

# Test with simple terms
curl "http://localhost:8000/search/simple?query=building&num_results=1"

# Check ChromaDB directly
python apis/search/debug_db.py
```

## Performance Optimization

### For Better Search Quality

```python
# Use more specific queries
"building permit requirements residential"  # Better than "building"
"subdivision three lots or fewer"           # Better than "subdivision"
```

### For Better Performance

```bash
# Increase num_results limit for better coverage
curl "http://localhost:8000/search/simple?query=zoning&num_results=10"

# Use POST for complex queries to avoid URL encoding issues
curl -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "complex query with special chars & symbols"}'
```

## Data Management

### Adding New Documents

To add new legal sections:

1. Update `la_plata_code/full_code.json`
2. Regenerate embeddings:
   ```bash
   python apis/search/embeddings/create_legal_embeddings.py
   ```
3. Restart search API

### Backing Up Data

```bash
# Backup vector database
cp -r chroma_db chroma_db_backup_$(date +%Y%m%d)

# Backup raw data
cp -r la_plata_code la_plata_code_backup_$(date +%Y%m%d)
```

## Next Steps

After successful setup:

1. **Read** [USAGE.md](./USAGE.md) for detailed API documentation
2. **Review** [ARCHITECTURE.md](./ARCHITECTURE.md) for system understanding
3. **Check** [TUNING.md](./TUNING.md) for performance optimization
4. **Reference** [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for issues

## Production Considerations

For production deployment:

- **Security**: Enable authentication, input validation, rate limiting
- **Scaling**: Consider load balancing, model caching strategies
- **Monitoring**: Add structured logging, health check automation
- **Backup**: Implement automated backup procedures
- **Updates**: Plan for model updates and data refresh procedures

The search API provides a solid foundation for semantic search across legal documents and can be extended for additional data sources and use cases.