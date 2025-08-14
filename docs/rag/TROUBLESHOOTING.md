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

#### Response Inconsistency (Different Results for Same Query)

**Symptoms**:
- Identical queries produce vastly different answers on each run
- Same semantic search results but varying LLM outputs
- Response quality fluctuates unpredictably
- Cannot reproduce specific answers

**Example**:
```bash
# Running this query multiple times produces different responses each time
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query": "What are minor subdivision requirements?"}'

# Response 1: "Minor subdivision procedures apply to divisions of 3 or fewer lots..."
# Response 2: "According to La Plata County Code, minor subdivisions require..."  
# Response 3: "The requirements for minor subdivisions include..."
```

**Root Cause**: Non-deterministic model generation due to:
- Random sampling with temperature > 0
- No fixed seed causing different KV cache behavior in llama.cpp
- Model inference variations between runs

**Diagnosis**:
```bash
# Test consistency by running same query multiple times
for i in {1..3}; do
  echo "=== Run $i ==="
  curl -s -X POST http://localhost:8001/rag/answer \
    -H 'Content-Type: application/json' \
    -d '{"query": "What are minor subdivision requirements?"}' | jq -r '.answer' | head -n 3
  echo
done
```

**Solution - Hybrid Deterministic Approach**:

The solution combines multiple techniques for consistent responses while maintaining quality:

1. **Fixed Seed**: Set deterministic seed in `inference.py:89`
2. **Temperature Capping**: Limit randomness via `inference.py:85`  
3. **Structured Prompts**: Enhanced prompt engineering in `retrieval.py:53`

**Implementation Details**:

```python
# In apis/rag/inference.py (lines 85-89)
"temperature": min(temperature, 0.1),  # Cap at 0.1 for consistency
"repeat_penalty": 1.3,                 # Prevent repetition
"repeat_last_n": 128,                  # Consider more tokens for repetition
"seed": 42,                            # Fixed seed for reproducible results
```

```python
# In apis/rag/retrieval.py (lines 53-54)
"Structure your response clearly with the key information first, followed by supporting details. "
"Include citation markers [n] in your response to reference the sources you use. "
```

**Configuration Parameters**:
- `seed: 42` - Fixed seed for reproducible generation
- `temperature: ≤ 0.1` - Minimal randomness while preserving quality
- `repeat_penalty: 1.3` - Prevent repetitive text generation
- Enhanced prompt structure for consistent formatting

**Testing Consistency**:
```bash
# Verify the fix works by running identical queries
query='{"query": "What are minor subdivision requirements?", "collection": "la_plata_county_code", "num_results": 4}'

echo "=== Test 1 ==="
curl -s -X POST http://localhost:8001/rag/answer -H 'Content-Type: application/json' -d "$query" | jq -r '.answer'

echo -e "\n=== Test 2 ==="  
curl -s -X POST http://localhost:8001/rag/answer -H 'Content-Type: application/json' -d "$query" | jq -r '.answer'

echo -e "\n=== Test 3 ==="
curl -s -X POST http://localhost:8001/rag/answer -H 'Content-Type: application/json' -d "$query" | jq -r '.answer'

# All three responses should be identical
```

**Performance Impact**:
- Minimal impact on response quality (maintains detail and accuracy)
- Slight reduction in creative variation (intentional for legal use cases)
- Same response times (~4-5 seconds)
- Deterministic behavior across all identical queries

**When to Adjust**:
- **Increase seed variation**: For A/B testing different response styles
- **Raise temperature cap**: If responses become too rigid (unlikely for legal content)
- **Modify prompt structure**: To adjust response formatting consistency

**Reverting to Non-Deterministic Behavior** (if needed):
```python
# In apis/rag/inference.py, remove/modify these lines:
"temperature": temperature,  # Remove min() cap
# "seed": 42,                # Comment out fixed seed
```

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
- System memory usage >85-90% when model loads
- Models stall during inference despite working in CLI

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

# Compare CLI vs API memory usage
mlx_lm.generate --model mlx-community/Qwen3-4B-Instruct-2507-4bit --prompt "test" &
# vs
curl -X POST http://localhost:8001/rag/model/load -d '{"model_id":"mlx-community/Qwen3-4B-Instruct-2507-4bit"}' &
```

**Root Cause**: Python MLX bindings have significantly higher memory overhead than direct CLI usage
- CLI: ~3-4GB for 4B models
- Python API: 8-12GB+ for same models due to:
  - Python interpreter overhead
  - Flask application memory
  - MLX Python wrapper overhead  
  - ChromaDB + embeddings
  - Memory fragmentation from persistent service

**Solutions**:
1. **Use 4-bit models**: Require ~4-6GB instead of 8-12GB
2. **Close other applications**: Free up system memory  
3. **Reduce context size**: Lower `num_results` and `max_tokens`
4. **Restart services**: Clear memory leaks
5. **⚠️ RECOMMENDED: Migrate to external inference service** (see Migration Blueprint below)

```bash
# Switch to memory-efficient model (temporary fix)
curl -X POST http://localhost:8001/rag/model/load \
  -H 'Content-Type: application/json' \
  -d '{"model_id":"mlx-community/Llama-3.1-8B-Instruct-4bit"}'

# Or switch to GGUF/llama.cpp approach (permanent solution)
# See Migration Blueprint section below
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

## Model Testing and Performance Analysis

### Model Performance Comparison

During system optimization, extensive testing revealed significant differences between models and inference methods:

#### Tested Models and Results

| Model | Quantization | Memory Usage (CLI) | Memory Usage (Python API) | Performance | Notes |
|-------|--------------|-------------------|---------------------------|-------------|-------|
| Qwen3-4B-Thinking-2507-8bit | 8-bit | ~3-4GB | 8-12GB+ | Good reasoning, citations | Thinking chains visible |
| Qwen3-4B-Instruct-2507-4bit | 4-bit | ~3-4GB | 8-12GB+ | Fast, good quality | Best balance |
| Qwen3-4B-Instruct-2507-6bit | 6-bit | ~4-5GB | 10-14GB+ | Higher quality | More memory usage |
| Qwen2.5-3B-Instruct-4bit | 4-bit | ~2-3GB | 6-10GB+ | Decent performance | Smaller model |
| Meta-Llama-3.1-8B-Instruct-4bit | 4-bit | ~4-5GB | 10-16GB+ | Good general use | Larger context |

#### Key Findings

1. **Memory Overhead**: Python MLX bindings use 2-3x more memory than CLI
2. **Model Stalls**: Models that work fine via CLI stall when loaded through Python API
3. **Memory Pressure**: System becomes unresponsive at 80-90% memory usage (24GB M4 Pro)
4. **Performance Degradation**: Inference speed significantly slower through Python bindings

### Root Cause Analysis

The memory and performance issues stem from architectural limitations of the current MLX Python bindings approach:

**Python MLX Overhead Sources**:
- Python interpreter memory overhead
- Flask application persistence in memory
- MLX Python wrapper inefficiencies compared to direct CLI usage
- ChromaDB + embeddings loaded simultaneously
- Memory fragmentation from long-running service
- Multiple Python objects and garbage collection overhead

**CLI vs API Memory Usage**:
```bash
# CLI usage (efficient)
mlx_lm.generate --model mlx-community/Qwen3-4B-Instruct-2507-4bit --prompt "test"
# Memory: ~3-4GB

# Python API usage (inefficient) 
curl -X POST http://localhost:8001/rag/model/load -d '{"model_id":"mlx-community/Qwen3-4B-Instruct-2507-4bit"}'
# Memory: 8-12GB+
```

## Migration Blueprint: MLX Python → llama.cpp Server

### Why Migrate?

1. **Immediate Benefits**:
   - Reduced memory usage (closer to CLI performance)
   - Better process isolation and stability
   - Cleaner service architecture
   - Independent scaling of inference vs RAG logic

2. **Strategic Benefits**:
   - Foundation for AWS Bedrock migration
   - External service pattern matches cloud deployment
   - Easier model management and swapping
   - Better monitoring and observability

### Migration Plan

#### Phase 1: Setup llama.cpp Server

1. **Install llama.cpp**:
```bash
# Clone and build llama.cpp
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make LLAMA_METAL=1  # For Apple Silicon GPU acceleration

# Or use pre-built binaries
brew install llama.cpp
```

2. **Download GGUF Models**:
```bash
# Example with Qwen3-4B model
curl -L "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q4_K_M.gguf" \
  -o models/Qwen3-4B-Instruct-2507-Q4_K_M.gguf
```

3. **Start llama.cpp Server**:
```bash
# Start server with API endpoint
./llama-server \
  --model models/Qwen3-4B-Instruct-2507-Q4_K_M.gguf \
  --port 8003 \
  --host 0.0.0.0 \
  --n-gpu-layers 32 \
  --ctx-size 8192 \
  --threads 8
```

#### Phase 2: Update RAG System

1. **Create External Inference Client** (`apis/rag/inference_client.py`):
```python
import requests
import json
from typing import Iterator, Optional

class LlamaCppClient:
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        
    def generate(self, prompt: str, max_tokens: int = 1200, 
                temperature: float = 0.2, stream: bool = False) -> str | Iterator[str]:
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
            "stop": ["</s>", "<|im_end|>"]
        }
        
        if stream:
            return self._stream_generate(payload)
        else:
            return self._sync_generate(payload)
    
    def _sync_generate(self, payload: dict) -> str:
        response = requests.post(f"{self.base_url}/completion", 
                               json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["content"]
    
    def _stream_generate(self, payload: dict) -> Iterator[str]:
        response = requests.post(f"{self.base_url}/completion", 
                               json=payload, stream=True, timeout=120)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line and line.startswith(b"data: "):
                data = json.loads(line[6:])
                if "content" in data:
                    yield data["content"]
```

2. **Update inference.py**:
```python
# Replace MLX imports and ModelManager class with:
from .inference_client import LlamaCppClient

class ExternalModelManager:
    def __init__(self):
        self.client = LlamaCppClient()
        self.model_loaded = True  # External service manages loading
        
    def generate_text(self, prompt: str, max_tokens: int = 1200, 
                     temperature: float = 0.2) -> str:
        return self.client.generate(prompt, max_tokens, temperature)
        
    def stream_text(self, prompt: str, max_tokens: int = 1200, 
                   temperature: float = 0.2) -> Iterator[str]:
        return self.client.generate(prompt, max_tokens, temperature, stream=True)
```

3. **Update Health Checks**:
```python
# In rag_api.py health endpoint
def check_inference_service():
    try:
        response = requests.get("http://localhost:8003/health", timeout=5)
        return response.status_code == 200
    except:
        return False
```

#### Phase 3: Service Management

1. **Create llama.cpp Service Script** (`scripts/run_llama.sh`):
```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MODEL_PATH="$PROJECT_ROOT/models/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
PID_FILE="$PROJECT_ROOT/llama.pid"
LOG_FILE="$PROJECT_ROOT/llama.log"

start_service() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "llama.cpp server already running (PID: $(cat "$PID_FILE"))"
        return 0
    fi
    
    echo "Starting llama.cpp server..."
    nohup ./llama-server \
        --model "$MODEL_PATH" \
        --port 8003 \
        --host 0.0.0.0 \
        --n-gpu-layers 32 \
        --ctx-size 8192 \
        --threads 8 \
        > "$LOG_FILE" 2>&1 &
    
    echo $! > "$PID_FILE"
    echo "llama.cpp server started (PID: $!)"
}
```

2. **Update start_both.sh**:
```bash
# Add llama.cpp server startup
case "$1" in
    start)
        ./scripts/run_llama.sh start
        ./scripts/api.sh start
        ./scripts/run_rag.sh start
        ;;
    stop)
        ./scripts/run_rag.sh stop
        ./scripts/api.sh stop  
        ./scripts/run_llama.sh stop
        ;;
esac
```

#### Phase 4: Configuration Updates

1. **Update config.py**:
```python
# Add inference service settings
INFERENCE_SERVICE_URL = os.environ.get('INFERENCE_SERVICE_URL', 'http://localhost:8003')
INFERENCE_SERVICE_TIMEOUT = int(os.environ.get('INFERENCE_SERVICE_TIMEOUT', '120'))

# Remove MLX-specific settings
# DEFAULT_MODEL_ID now refers to GGUF model file name
DEFAULT_MODEL_ID = os.environ.get('DEFAULT_MODEL_ID', 'Qwen3-4B-Instruct-2507-Q4_K_M.gguf')
```

2. **Update model loading endpoint**:
```python
# /rag/model/load now restarts llama.cpp server with new model
@app.route("/rag/model/load", methods=["POST"])
def load_model():
    data = request.get_json()
    model_file = data.get("model_file")
    
    # Restart llama.cpp server with new model
    subprocess.run(["./scripts/run_llama.sh", "stop"])
    subprocess.run(["./scripts/run_llama.sh", "start", model_file])
    
    return jsonify({"status": "success", "model_file": model_file})
```

### Migration Benefits

1. **Memory Efficiency**: 
   - Expected reduction from 8-12GB to 4-6GB
   - Better memory isolation between services
   - Reduced Python overhead

2. **Performance**:
   - Faster inference closer to CLI performance
   - Better GPU utilization with native Metal acceleration
   - Reduced context switching overhead

3. **Architecture**:
   - Clean separation of concerns
   - External service pattern ready for cloud migration
   - Independent service scaling and monitoring
   - Easier model management and swapping

4. **Cloud Migration Foundation**:
   - HTTP API pattern matches AWS Bedrock
   - Service boundary established for easy substitution
   - Configuration externalized for environment-specific endpoints

### Testing the Migration

1. **Benchmark Memory Usage**:
```bash
# Before migration (current system)
curl -X POST http://localhost:8001/rag/model/load -d '{"model_id":"mlx-community/Qwen3-4B-Instruct-2507-4bit"}'
# Monitor memory with Activity Monitor / htop

# After migration (llama.cpp)
./scripts/run_llama.sh start Qwen3-4B-Instruct-2507-Q4_K_M.gguf
# Compare memory usage
```

2. **Performance Comparison**:
```bash
# Test response times for identical queries
time curl -X POST http://localhost:8001/rag/answer -d '{"query":"building permits"}'
```

3. **Quality Verification**:
```bash
# Compare response quality between MLX and llama.cpp
# Use same model (Qwen3-4B-Instruct) in both formats
```

This migration blueprint provides a clear path to resolve the immediate memory issues while establishing the foundation for future cloud migration to AWS Bedrock.

---

This comprehensive troubleshooting guide should help identify and resolve most issues with the RAG system. For persistent problems not covered here, check the logs and consider the system architecture documentation for deeper diagnosis.