# Search API Troubleshooting Guide

## Quick Diagnosis

### Health Check

Run this command first to identify issues:

```bash
curl -s http://localhost:8000/health | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null || echo "❌ API not responding"
```

Expected output:
```json
{
  "status": "healthy",
  "models_loaded": 1,
  "collections_connected": 2,
  "total_documents": 47528,
  "available_collections": ["la_plata_county_code", "la_plata_assessor"]
}
```

### Service Status

```bash
# Check if service is running
./scripts/api.sh status

# Check logs for errors
./scripts/api.sh logs
```

## Common Issues and Solutions

### 🔥 Critical Issues (Service Down)

#### API Not Responding

**Symptoms**:
- `curl: (7) Failed to connect to localhost port 8000`
- Browser shows connection refused

**Diagnosis**:
```bash
# Check if process is running
./scripts/api.sh status

# Check if port is in use by another process
lsof -i :8000

# Check recent logs
./scripts/api.sh logs | tail -20
```

**Solutions**:
```bash
# Start the service
./scripts/api.sh start

# If port is busy, kill conflicting process
kill [PID from lsof output]

# Restart service
./scripts/api.sh restart
```

#### ChromaDB Connection Errors

**Symptoms**:
- "Collection [collection_name] does not exist" in logs
- API starts but no collections available
- Health check shows 0 documents

**Diagnosis**:
```bash
# Check if ChromaDB directory exists
ls -la chroma_db/

# Check collection contents
python apis/search/debug_db.py
```

**Solutions**:
```bash
# Create embeddings if missing
python apis/search/embeddings/create_legal_embeddings.py

# Check for corrupted database
rm -rf chroma_db/
python apis/search/embeddings/create_legal_embeddings.py

# Verify embedding creation completed
curl http://localhost:8000/collections
```

#### Model Loading Failures

**Symptoms**:
- "Error loading model" in startup logs
- Service fails to initialize
- "models_loaded": 0 in health check

**Diagnosis**:
```bash
# Test model loading manually
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/e5-large-v2')"

# Check available disk space
df -h

# Check internet connectivity for model download
curl -I https://huggingface.co
```

**Solutions**:
```bash
# Clear model cache and reload
rm -rf ~/.cache/torch/sentence_transformers/
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/e5-large-v2')"

# Check dependencies
pip install --upgrade sentence-transformers torch

# Use alternative model if needed (edit search_api.py)
# Change model name to 'all-MiniLM-L6-v2' for smaller footprint
```

### ⚠️ Quality Issues (Service Running, Poor Results)

#### Empty Search Results

**Symptoms**:
- All searches return empty results array
- Health check shows documents, but searches find nothing
- No errors in logs

**Diagnosis**:
```bash
# Test with very simple query
curl "http://localhost:8000/search/simple?query=building&num_results=1"

# Check collection contents directly
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('la_plata_county_code')
print(f'Documents: {collection.count()}')
sample = collection.peek(limit=1)
print(f'Sample document: {sample}')
"

# Test embedding generation
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('intfloat/e5-large-v2')
embedding = model.encode(['test query'])
print(f'Embedding shape: {embedding.shape}')
"
```

**Solutions**:
```bash
# Recreate embeddings with debugging
python apis/search/embeddings/create_legal_embeddings.py

# Check for embedding dimension mismatch
# Verify model produces 1024D embeddings as expected

# Test with known working queries
curl "http://localhost:8000/search/simple?query=section%2067-4&collection=la_plata_county_code"
```

#### Poor Search Relevance

**Symptoms**:
- Search returns unrelated results
- Expected content not appearing in results
- Low relevance scores across the board

**Diagnosis**:
```bash
# Test with specific legal terms
curl "http://localhost:8000/search/simple?query=subdivision&collection=la_plata_county_code&num_results=5"

# Compare with different query styles
curl "http://localhost:8000/search/simple?query=building%20permit&collection=la_plata_county_code&num_results=3"
curl "http://localhost:8000/search/simple?query=permit%20to%20build&collection=la_plata_county_code&num_results=3"

# Check if results include actual content
curl -s "http://localhost:8000/search/simple?query=building&num_results=1" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['results']:
    print('Content preview:', data['results'][0]['text'][:200])
else:
    print('No results returned')
"
```

**Solutions**:
1. **Use more specific queries**: "building permit residential" vs "building"
2. **Try legal terminology**: "subdivision regulations" vs "splitting land"  
3. **Increase num_results**: Search with 10-15 results to see more options
4. **Check collection**: Ensure using correct collection for query type

#### Slow Response Times (>5 seconds)

**Symptoms**:
- Queries take longer than 5 seconds
- Timeout errors from client applications
- High CPU usage during searches

**Diagnosis**:
```bash
# Time a simple request
time curl -s "http://localhost:8000/search/simple?query=building&num_results=5" > /dev/null

# Check system resources during search
htop &
curl "http://localhost:8000/search/simple?query=complex%20building%20permit%20requirements&num_results=10"

# Test with fewer results
time curl -s "http://localhost:8000/search/simple?query=building&num_results=1" > /dev/null
```

**Solutions**:
```bash
# Reduce result count for faster responses
curl "http://localhost:8000/search/simple?query=permits&num_results=3"

# Close memory-intensive applications
# Check available memory: free -h (Linux) or Activity Monitor (macOS)

# Restart service to clear memory leaks
./scripts/api.sh restart

# Use shorter, more specific queries
# "permit" instead of "what are the requirements for building permits"
```

### 🔧 Configuration Issues

#### Wrong Collection Results

**Symptoms**:
- Searching legal collection returns property data
- Property searches return legal code sections
- Collection parameter being ignored

**Diagnosis**:
```bash
# Test explicit collection specification  
curl "http://localhost:8000/search/simple?query=building&collection=la_plata_county_code&num_results=2"
curl "http://localhost:8000/search/simple?query=building&collection=la_plata_assessor&num_results=2"

# Check available collections
curl http://localhost:8000/collections | python3 -c "
import sys, json
data = json.load(sys.stdin)
for name, info in data['collections'].items():
    print(f'{name}: {info[\"document_count\"]} documents, available: {info[\"available\"]}')
"
```

**Solutions**:
```bash
# Always specify collection explicitly
curl "http://localhost:8000/search/simple?query=Smith%20property&collection=la_plata_assessor"

# Verify collection parameter in requests
# For legal queries: collection=la_plata_county_code  
# For property queries: collection=la_plata_assessor
```

#### Memory Issues During Operation

**Symptoms**:
- Service crashes after running for hours
- Gradual performance degradation
- "Out of memory" errors in logs

**Diagnosis**:
```bash
# Monitor memory usage over time
top -p $(pgrep -f search_api.py)

# Check for memory leaks
./scripts/api.sh restart
# Monitor memory right after restart vs after many queries

# Check system memory
free -h  # Linux
vm_stat  # macOS
```

**Solutions**:
```bash
# Restart service periodically (automated)
echo "0 */6 * * * /path/to/scripts/api.sh restart" | crontab -

# Reduce concurrent load
# Implement request queuing in frontend if needed

# Clear model cache if very high memory usage
rm -rf ~/.cache/torch/sentence_transformers/
./scripts/api.sh restart
```

## Error Code Reference

### HTTP Status Codes

| Code | Meaning | Common Causes | Solutions |
|------|---------|---------------|-----------|
| 200 | OK | Successful request | Normal operation |
| 400 | Bad Request | Missing query parameter, invalid collection | Check request format |
| 404 | Not Found | Invalid endpoint | Check URL path |
| 500 | Internal Server Error | Model/DB errors, system issues | Check logs, restart service |
| 503 | Service Unavailable | Service overloaded | Restart service, reduce load |

### Specific Error Messages

#### "Query parameter is required"
```json
{"error": "Query parameter is required"}
```

**Solution**: Include query in request:
```bash
curl "http://localhost:8000/search/simple?query=your%20search%20here"
```

#### "Invalid collection"
```json
{"error": "Invalid collection. Available: ['la_plata_county_code', 'la_plata_assessor']"}
```

**Solution**: Use valid collection name:
```bash
curl "http://localhost:8000/search/simple?query=building&collection=la_plata_county_code"
```

#### "Collection 'collection_name' not available"
```json
{"error": "Collection 'la_plata_county_code' not available"}
```

**Solution**: Create embeddings:
```bash
python apis/search/embeddings/create_legal_embeddings.py
./scripts/api.sh restart
```

## Debugging Workflow

### Step 1: Verify Service Status

```bash
# Check if API is running
curl -s http://localhost:8000/health || echo "API not responding"

# Check process status
./scripts/api.sh status

# Review recent logs
./scripts/api.sh logs | tail -10
```

### Step 2: Test Basic Functionality

```bash
# Test simplest possible request
curl "http://localhost:8000/search/simple?query=test&num_results=1"

# Test with known good query
curl "http://localhost:8000/search/simple?query=building&collection=la_plata_county_code&num_results=1"

# Check collection health
curl http://localhost:8000/collections
```

### Step 3: Isolate the Problem

```bash
# Test embedding generation manually
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('intfloat/e5-large-v2')
result = model.encode(['building permit'])
print(f'Success: embedding shape {result.shape}')
"

# Test ChromaDB access manually
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collections = client.list_collections()
print(f'Collections: {[c.name for c in collections]}')
"

# Test search components separately
python apis/search/debug_db.py
```

### Step 4: Check Dependencies

```bash
# Verify Python packages
pip list | grep -E "(flask|chromadb|sentence|torch)"

# Test imports
python3 -c "import flask, chromadb, sentence_transformers; print('All imports OK')"

# Check system resources  
df -h  # Disk space
free -h  # Memory (Linux)
vm_stat  # Memory (macOS)
```

## Data Issues and Recovery

### Corrupted ChromaDB

**Symptoms**:
- Service starts but crashes on first search
- "Database corruption" errors in logs
- Collections show 0 documents despite embeddings

**Recovery**:
```bash
# Backup existing database
mv chroma_db chroma_db_corrupted_$(date +%Y%m%d)

# Recreate embeddings
python apis/search/embeddings/create_legal_embeddings.py

# If you have assessor data:
python apis/search/embeddings/create_assessor_embeddings.py

# Restart service
./scripts/api.sh restart

# Verify recovery
curl http://localhost:8000/health
```

### Missing or Incomplete Embeddings

**Symptoms**:
- Some collections missing from health check
- Lower than expected document counts
- Searches work for some content but not others

**Diagnosis**:
```bash
# Check what collections exist
curl http://localhost:8000/collections

# Check raw data sources
ls -la la_plata_code/full_code.json
ls -la LPC-Assessor-Data-Files/AssessorData.mdb

# Check embedding logs for errors
grep -i error logs/embedding_*.log
```

**Recovery**:
```bash
# Recreate specific collection
python apis/search/embeddings/create_legal_embeddings.py

# For assessor data (if available)
python apis/search/embeddings/create_assessor_embeddings.py

# Verify completion
curl http://localhost:8000/collections | python3 -c "
import sys, json
data = json.load(sys.stdin)
for name, info in data['collections'].items():
    print(f'{name}: {info[\"document_count\"]} docs')
"
```

## Performance Debugging

### Profiling Search Performance

Add timing instrumentation:

```python
# Temporary debugging in search_api.py
import time

def perform_search(query, collection_name='la_plata_county_code', num_results=5):
    start_time = time.time()
    
    # ... existing code ...
    
    embedding_time = time.time()
    query_embedding = model.encode([query]).tolist()[0]
    
    search_start = time.time()  
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=num_results
    )
    search_end = time.time()
    
    # Log timing
    logger.info(f"Search timing - Embedding: {embedding_time-start_time:.3f}s, Search: {search_end-search_start:.3f}s")
    
    # ... rest of function ...
```

### Memory Usage Analysis

```bash
# Monitor memory during operation
watch -n 1 'ps aux | grep search_api.py | grep -v grep'

# Check for memory leaks over time
./scripts/api.sh restart
# Run searches and monitor memory growth

# Profile memory usage
python3 -m memory_profiler apis/search/search_api.py
```

## Prevention and Monitoring

### Automated Health Monitoring

```bash
#!/bin/bash
# health_check.sh - Run via cron every 5 minutes

API_URL="http://localhost:8000/health"
LOG_FILE="/tmp/search_api_monitor.log"

check_health() {
    curl -s --connect-timeout 5 --max-time 10 "$API_URL" | grep -q "healthy"
}

if ! check_health; then
    echo "$(date): Search API unhealthy, restarting" >> "$LOG_FILE"
    /path/to/scripts/api.sh restart
    sleep 30
    if check_health; then
        echo "$(date): Search API recovered" >> "$LOG_FILE"  
    else
        echo "$(date): Search API restart failed" >> "$LOG_FILE"
    fi
fi
```

### Log Rotation

```bash
# Add to /etc/logrotate.d/search-api
/path/to/landuse/api.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 644 user user
    postrotate
        /path/to/scripts/api.sh restart > /dev/null
    endscript
}
```

### Performance Testing

```bash
#!/bin/bash
# performance_test.sh - Test API performance

echo "Testing Search API performance..."

# Test response times
for query in "building" "permit" "subdivision" "zoning" "property"; do
    echo -n "Query '$query': "
    time_result=$(curl -s -w "%{time_total}" -o /dev/null "http://localhost:8000/search/simple?query=$query&num_results=5")
    echo "${time_result}s"
done

# Test concurrent requests  
echo "Testing concurrent requests..."
for i in {1..10}; do
    curl -s "http://localhost:8000/search/simple?query=test$i&num_results=3" > /dev/null &
done
wait
echo "Concurrent test completed"
```

This comprehensive troubleshooting guide should help identify and resolve most issues with the Search API while providing preventive monitoring strategies.