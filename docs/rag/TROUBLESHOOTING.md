# RAG System Troubleshooting Guide

## Quick Diagnosis

### System Health Check

Run this command first to identify issues:

```bash
./scripts/start_both.sh test
```

Expected output:
```
✅ Search API responding
✅ Search functionality working  
✅ RAG API responding
✅ RAG model loaded and ready
✅ Both APIs are operational
```

### Individual Service Status

```bash
# Check RAG API specifically
curl http://localhost:8001/rag/health | jq

# Check Search API
curl http://localhost:8000/health | jq

# Check model status
curl http://localhost:8001/rag/health | jq '.model_loaded'
```

## Common Issues and Solutions

### 🔥 Critical Issues (Service Down)

#### RAG API Not Responding

**Symptoms**:
- `curl: (7) Failed to connect to localhost port 8001`
- Browser shows connection refused

**Diagnosis**:
```bash
# Check if service is running
./scripts/run_rag.sh status

# Check logs for errors
./scripts/run_rag.sh logs
```

**Solutions**:
```bash
# Restart RAG service
./scripts/run_rag.sh restart

# Start from scratch if needed
./scripts/run_rag.sh stop
./scripts/run_rag.sh start

# Check port availability
lsof -i :8001
```

#### Search API Not Available

**Symptoms**:
- RAG responses but no sources/citations
- Error: "Connection refused to search API"

**Diagnosis**:
```bash
./scripts/api.sh status
curl http://localhost:8000/health
```

**Solutions**:
```bash
# Start search API
./scripts/api.sh start

# Restart if running but not responding
./scripts/api.sh restart

# Check both services together
./scripts/start_both.sh start
```

#### Model Loading Failures

**Symptoms**:
- `"model_loaded": false` in health check
- Error: "Model not loaded" in responses

**Diagnosis**:
```bash
# Check model status
curl http://localhost:8001/rag/health | jq '.model_loaded,.model_id'

# Check MLX availability
python3 -c "import mlx_lm; print('MLX available')"

# Check available disk space
df -h
```

**Solutions**:
```bash
# Try loading default model
curl -X POST http://localhost:8001/rag/model/load \
  -H 'Content-Type: application/json' \
  -d '{"model_id":"mlx-community/Qwen3-4B-Thinking-2507-8bit"}'

# Try fallback model if memory constrained
curl -X POST http://localhost:8001/rag/model/load \
  -H 'Content-Type: application/json' \
  -d '{"model_id":"mlx-community/Llama-3.1-8B-Instruct-4bit"}'

# Check system memory
htop  # or Activity Monitor on macOS
```

### ⚠️ Quality Issues (Service Running, Poor Results)

#### No Citations or Empty Responses

**Symptoms**:
- Responses like "[stub] Model not loaded"
- Empty `citations` and `sources` arrays
- Answers without `[1]`, `[2]` markers

**Diagnosis**:
```bash
# Test search API directly
curl "http://localhost:8000/search/simple?query=building&collection=la_plata_county_code&num_results=5" | jq '.results | length'

# Check model status  
curl http://localhost:8001/rag/health | jq '.model_loaded'

# Test with known working query
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"minor subdivision requirements","num_results":5}' | jq '.sources | length'
```

**Solutions**:
1. **Model Issue**: Load model if `model_loaded` is false
2. **Search Issue**: Restart search API if no results
3. **Data Issue**: Check if ChromaDB has embeddings
4. **Query Issue**: Try simpler, more specific queries

#### Truncated or Incomplete Answers

**Symptoms**:
- Responses cut off mid-sentence
- Missing context or incomplete reasoning
- Sources show "Less than ten thousa..." (truncated)

**Diagnosis**:
```bash
# Check if it's a token limit issue
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"building permits","max_tokens":1500}' | jq '.answer | length'

# Compare with shorter token limit
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"building permits","max_tokens":500}' | jq '.answer | length'
```

**Solutions**:
```bash
# Increase token limit for complex queries
{
  "query": "subdivision requirements",
  "max_tokens": 1500,     # Up from default 1200
  "num_results": 6
}

# For thinking models, use higher limits
{
  "max_tokens": 1800,     # Thinking models need more tokens
  "temperature": 0.2      # Lower temperature for focused responses
}
```

#### Irrelevant or Generic Responses

**Symptoms**:
- Answers don't address specific question
- Generic legal advice not specific to La Plata County
- No section references or specific citations

**Diagnosis**:
```bash
# Test query normalization
python3 -c "
import sys; sys.path.append('apis/rag')
from normalize import debug_normalization
print(debug_normalization('What are the requirements for building permits?'))
"

# Check what sources are retrieved
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"building permits"}' | jq '.sources[].preview'
```

**Solutions**:
1. **Use specific legal terms**: "section 67-4" instead of "subdivision rules"
2. **Increase source count**: `"num_results": 10` for broader context
3. **Lower temperature**: `"temperature": 0.2` for more focused responses
4. **Check collection**: Ensure using `"la_plata_county_code"` for legal queries

### 🐌 Performance Issues (Slow Responses)

#### Slow Response Times (>15 seconds)

**Symptoms**:
- Queries take longer than 15 seconds
- Timeout errors in browser/client
- High CPU usage during generation

**Diagnosis**:
```bash
# Time a request
time curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"building permits","num_results":5}'

# Check system resources
htop  # Monitor CPU and memory during query

# Test with minimal parameters  
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"permits","num_results":3,"max_tokens":400}'
```

**Solutions**:
```bash
# Use performance-optimized settings
{
  "query": "building permits",
  "num_results": 5,        # Down from 10+
  "max_tokens": 800,       # Down from 1200+
  "temperature": 0.4       # Slightly higher for faster sampling
}

# Switch to 4-bit model for speed
curl -X POST http://localhost:8001/rag/model/load \
  -H 'Content-Type: application/json' \
  -d '{"model_id":"mlx-community/Llama-3.1-8B-Instruct-4bit"}'

# Close other memory-intensive applications
```

#### Memory Issues (OOM Crashes)

**Symptoms**:
- Service crashes with memory errors
- System becomes unresponsive
- "Killed" in logs

**Diagnosis**:
```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS

# Monitor memory during loading
curl -X POST http://localhost:8001/rag/model/load \
  -H 'Content-Type: application/json' \
  -d '{"model_id":"mlx-community/Qwen3-4B-Thinking-2507-8bit"}' &
htop
```

**Solutions**:
1. **Use 4-bit models**: Require ~4-6GB instead of 8-12GB
2. **Close other applications**: Free up system memory
3. **Reduce context size**: Lower `num_results` and `max_tokens`
4. **Restart services**: Clear memory leaks

```bash
# Switch to memory-efficient model
curl -X POST http://localhost:8001/rag/model/load \
  -H 'Content-Type: application/json' \
  -d '{"model_id":"mlx-community/Llama-3.1-8B-Instruct-4bit"}'
```

## Error Code Reference

### HTTP Status Codes

| Code | Meaning | Common Causes | Solutions |
|------|---------|---------------|-----------|
| 400 | Bad Request | Missing `query` parameter | Include required fields |
| 500 | Internal Server Error | Model not loaded, MLX error | Load model, check logs |
| 502 | Bad Gateway | Search API down | Start search API |
| 503 | Service Unavailable | RAG API overloaded | Restart service, reduce load |

### Specific Error Messages

#### "Model not loaded"
```json
{"error": "Model not loaded. Load via POST /rag/model/load with {\"model_id\": \"...\"}"}
```

**Solution**:
```bash
curl -X POST http://localhost:8001/rag/model/load \
  -H 'Content-Type: application/json' \
  -d '{"model_id":"mlx-community/Qwen3-4B-Thinking-2507-8bit"}'
```

#### "query is required"
```json  
{"error": "query is required"}
```

**Solution**: Include `query` field in JSON body:
```bash
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query": "your question here"}'
```

#### "Connection refused"
```json
{"error": "Connection refused to search API"}
```

**Solution**: Start search API:
```bash
./scripts/api.sh start
```

#### MLX Import Error
```
ImportError: No module named 'mlx_lm'
```

**Solution**: Install MLX dependencies:
```bash
pip install mlx mlx-lm
```

## Debugging Workflow

### Step 1: Identify Issue Category

```bash
# Quick health check
curl http://localhost:8001/rag/health

# If RAG API responds, check search API
curl http://localhost:8000/health  

# If both respond, test end-to-end
curl -X POST http://localhost:8001/rag/answer \
  -d '{"query":"test","num_results":3}' | jq '.sources | length'
```

### Step 2: Check Logs

```bash
# RAG API logs (Flask output)
./scripts/run_rag.sh logs

# Search API logs  
./scripts/api.sh logs

# System logs (if services crash)
dmesg | tail -20  # Linux
console | grep rag  # macOS
```

### Step 3: Test Components Individually

```bash
# Test query normalization
python3 -c "
import sys; sys.path.append('apis/rag')  
from normalize import normalize_legal_query
print(normalize_legal_query('What are building permit requirements?'))
"

# Test search API directly
curl "http://localhost:8000/search/simple?query=permits&num_results=3"

# Test model loading
curl -X POST http://localhost:8001/rag/model/load \
  -d '{"model_id":"mlx-community/Llama-3.1-8B-Instruct-4bit"}'
```

### Step 4: Isolate Variables

```bash
# Minimal request (eliminate parameter issues)
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"permits"}'

# Known working query
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"minor subdivision requirements"}'

# Test different models
curl -X POST http://localhost:8001/rag/model/load \
  -d '{"model_id":"mlx-community/Llama-3.1-8B-Instruct-4bit"}'
```

## Environment-Specific Issues

### macOS Specific

#### Apple Silicon Compatibility
- Ensure using MLX (not CUDA/CPU versions)
- Check if running under Rosetta: `arch` should show `arm64`
- Install native Python: avoid x86_64 versions

#### Memory Pressure
- macOS aggressively manages memory
- Monitor with Activity Monitor > Memory tab
- Look for "Memory Pressure" indicator

### Python Environment Issues

#### Virtual Environment Problems
```bash
# Check if in virtual environment
echo $VIRTUAL_ENV

# Recreate if corrupted
deactivate
rm -rf env
python3 -m venv env
source env/bin/activate
pip install mlx mlx-lm flask flask-cors requests
```

#### Package Version Conflicts
```bash
# Check installed versions
pip list | grep -E "(mlx|flask|requests)"

# Upgrade if needed
pip install --upgrade mlx mlx-lm
```

## Advanced Debugging

### Enable Debug Logging

Add to `apis/rag/rag_api.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
```

### Request/Response Inspection

```bash
# Verbose curl output
curl -v -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"test"}'

# Save response for analysis
curl -X POST http://localhost:8001/rag/answer \
  -d '{"query":"building permits"}' > response.json

# Analyze response structure
jq keys response.json
jq '.sources | length' response.json
jq '.answer | length' response.json
```

### Performance Profiling

```python
# Add timing to rag_api.py
import time

@app.route("/rag/answer", methods=["POST"])
def rag_answer():
    start_time = time.time()
    
    # ... existing code ...
    
    retrieval_time = time.time()
    # ... retrieval code ...
    
    generation_time = time.time() 
    # ... generation code ...
    
    end_time = time.time()
    
    print(f"Retrieval: {retrieval_time - start_time:.2f}s")
    print(f"Generation: {generation_time - retrieval_time:.2f}s") 
    print(f"Total: {end_time - start_time:.2f}s")
```

## Recovery Procedures

### Complete Service Reset

```bash
# Stop everything
./scripts/start_both.sh stop

# Clear any stuck processes
pkill -f "rag_api.py"
pkill -f "search_api.py"

# Restart fresh
./scripts/start_both.sh start

# Verify functionality
./scripts/start_both.sh test
```

### Database Reset (if ChromaDB corrupted)

```bash
# Backup current database
cp -r chroma_db chroma_db_backup

# Regenerate embeddings (this takes time)
python apis/search/embeddings/create_legal_embeddings.py

# Test with fresh database
curl "http://localhost:8000/search/simple?query=test&num_results=3"
```

### Model Cache Clearing

```bash
# Clear MLX model cache (if models corrupted)
rm -rf ~/.cache/mlx

# Force reload model
curl -X POST http://localhost:8001/rag/model/load \
  -d '{"model_id":"mlx-community/Qwen3-4B-Thinking-2507-8bit"}'
```

## Prevention and Monitoring

### Health Monitoring Script

```bash
#!/bin/bash
# health_monitor.sh - Run every 5 minutes via cron

check_health() {
    curl -s http://localhost:8001/rag/health | jq -r '.status' 2>/dev/null
}

if [ "$(check_health)" != "healthy" ]; then
    echo "$(date): RAG API unhealthy, restarting" >> /tmp/rag_monitor.log
    ./scripts/run_rag.sh restart
fi
```

### Automated Testing

```bash
#!/bin/bash
# test_rag.sh - Automated functionality test

test_query() {
    local query="$1"
    local expected_sources="$2"
    
    local actual=$(curl -s -X POST http://localhost:8001/rag/answer \
        -H 'Content-Type: application/json' \
        -d "{\"query\":\"$query\",\"num_results\":5}" | \
        jq '.sources | length')
    
    if [ "$actual" -ge "$expected_sources" ]; then
        echo "✅ Query '$query': $actual sources"
        return 0
    else
        echo "❌ Query '$query': only $actual sources (expected $expected_sources+)"
        return 1
    fi
}

# Run tests
test_query "building permits" 3
test_query "minor subdivision requirements" 2  
test_query "property assessment" 2

echo "Testing complete"
```

This comprehensive troubleshooting guide should help identify and resolve most issues with the RAG system. For persistent problems not covered here, check the logs and consider the system architecture documentation for deeper diagnosis.