# RAG System Usage Guide

## API Endpoints Overview

The RAG system provides several HTTP endpoints for different use cases:

| Endpoint | Method | Purpose | Response Type |
|----------|---------|---------|---------------|
| `/rag/health` | GET | System status and model info | JSON |
| `/rag/config` | GET | Configuration details | JSON |
| `/rag/model/load` | POST | Load/switch models | JSON |
| `/rag/answer` | POST | Get complete answer with citations | JSON |
| `/rag/answer/stream` | POST | Stream answer in real-time | Server-Sent Events |

## Health and Configuration

### Check System Status

```bash
curl http://localhost:8001/rag/health | jq
```

Response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "mlx_available": true, 
  "model_id": "mlx-community/Qwen3-4B-Thinking-2507-8bit",
  "streaming": true,
  "endpoints": [
    "/rag/health",
    "/rag/config", 
    "/rag/model/load",
    "/rag/answer",
    "/rag/answer/stream"
  ]
}
```

### View Configuration

```bash
curl http://localhost:8001/rag/config | jq
```

Response includes model settings, retrieval configuration, and version information.

## Model Management

### Load a Model

```bash
curl -X POST http://localhost:8001/rag/model/load \
  -H 'Content-Type: application/json' \
  -d '{
    "model_id": "mlx-community/Qwen3-4B-Thinking-2507-8bit"
  }' | jq
```

Successful response:
```json
{
  "loaded": true,
  "model_id": "mlx-community/Qwen3-4B-Thinking-2507-8bit",
  "max_context": 8192,
  "quantization": "8bit"
}
```

### Supported Models

**Recommended for Legal Queries**:
- `mlx-community/Qwen3-4B-Thinking-2507-8bit` - Explicit reasoning, best citations
- `mlx-community/Llama-3.1-8B-Instruct-4bit` - Reliable fallback, faster inference

**Model Selection Guidelines**:
- **8-bit models**: Higher accuracy, more memory usage (~8-12GB)
- **4-bit models**: Faster inference, less memory (~4-6GB)  
- **Thinking models**: Show reasoning process, better for complex legal questions

## Non-Streaming Answers

### Basic Query

```bash
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What are the requirements for a minor subdivision?",
    "collection": "la_plata_county_code",
    "num_results": 5
  }' | jq
```

### Complete Request Example

```bash
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Building permit requirements for residential construction",
    "collection": "la_plata_county_code",
    "num_results": 8,
    "max_tokens": 1200,
    "temperature": 0.2,
    "top_p": 0.9
  }' | jq
```

### Response Structure

```json
{
  "query": "What are the requirements for a minor subdivision?",
  "collection": "la_plata_county_code", 
  "num_results": 5,
  "answer": "Based on the provided sources, minor subdivisions in La Plata County are defined as land divisions that result in three (3) or fewer lots [1]. The key requirements include:\n\n**Application Process:**\n- Must follow minor land use permit procedures outlined in section 66-20 [2]\n- Subject to general land use permit approval criteria in section 66-16 [2]\n\n**Approval Requirements:** \n- Must meet all applicable approval criteria [2]\n- Final approval must be recorded with the county clerk within three (3) years [2]\n\n**Applicability:**\nMinor subdivisions apply when dividing land into 3 or fewer lots, while divisions into 4 or more lots require major subdivision procedures [1].",
  "citations": [
    {
      "marker": 1,
      "id": "3042",
      "collection": "la_plata_county_code"
    },
    {
      "marker": 2, 
      "id": "3200",
      "collection": "la_plata_county_code"
    }
  ],
  "sources": [
    {
      "index": 1,
      "id": "3042",
      "collection": "la_plata_county_code", 
      "preview": "Section 67-4. Minor subdivisions. (a) Applicability. This section applies to land divisions that result in the creation of three (3) or fewer lots...",
      "chunk": "Section 67-4. Minor subdivisions. (a) Applicability. This section applies to land divisions that result in the creation of three (3) or fewer lots. Land divisions that result in the creation of four (4) or more lots shall comply with the major subdivision requirements of section 67-3. (b) Procedures. Minor subdivisions shall be processed as a minor land use permit pursuant to the procedures set forth in section 66-20. (c) Approval criteria. Minor subdivisions shall be subject to the approval criteria for land use permits set forth in section 66-16. (d) Effect of approval. Approval of a minor subdivision shall be recorded with the La Plata County clerk within three (3) years of the date of approval, or the approval shall be deemed to have expired."
    }
  ],
  "verification": {
    "total_sentences": 8,
    "supported_sentences": 7,
    "unsupported_sentences": 1,
    "support_ratio": 0.875,
    "avg_support_score": 0.34
  }
}
```

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | User question |
| `collection` | string | `"la_plata_county_code"` | Document collection to search |
| `num_results` | integer | 5 | Number of sources to retrieve (1-15) |
| `max_tokens` | integer | 1200 | Maximum response length |
| `temperature` | float | 0.2 | Creativity vs consistency (0.1-1.0) |
| `top_p` | float | 0.9 | Nucleus sampling parameter |

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Generated response with citations |
| `citations` | array | Citation markers found in answer |
| `sources` | array | Source documents with full text |
| `verification` | object | Answer support analysis |

## Testing and Development

### Application Factory Pattern

The RAG API uses Flask's application factory pattern for better testability and configuration management:

```python
from apis.rag.app_factory import create_app

# Create test instance
test_app = create_app('testing')

# Test with Flask test client
with test_app.test_client() as client:
    response = client.post('/rag/answer', 
                          json={'query': 'test question'})
    assert response.status_code == 200

# Create development instance
dev_app = create_app('development')

# Create production instance
prod_app = create_app('production')
```

### Testing Configuration

Testing mode provides isolated configuration without model auto-loading:

```python
# Testing mode - no models auto-load
test_app = create_app('testing')
assert test_app.config['TESTING'] == True
assert test_app.config['DEBUG'] == True

# Models need to be loaded manually in tests
with test_app.app_context():
    rag_engine = test_app.config['RAG_ENGINE']
    # Optionally load model for testing
    if rag_engine.model_mgr:
        rag_engine.model_mgr.load('test-model-id')
```

### Integration Testing Examples

```python
import unittest
from apis.rag.app_factory import create_app

class TestRAGAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_health_endpoint(self):
        response = self.client.get('/rag/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('status', data)

    def test_answer_endpoint_without_model(self):
        response = self.client.post('/rag/answer', 
                                   json={'query': 'test'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('answer', data)
        # Should return stub response when no model loaded
        self.assertIn('stub', data['answer'])
```

### Environment-based Testing

```bash
# Run tests in testing mode
export FLASK_ENV=testing
python -m unittest discover tests/

# Test with custom configuration
export DEFAULT_MODEL_ID=test-model
export MAX_TOKENS=500
python test_rag_api.py

# Integration test with real models (development mode)
export FLASK_ENV=development
python test_full_integration.py
```

## Streaming Answers

### Basic Streaming Query

```bash
curl -N -X POST http://localhost:8001/rag/answer/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Explain zoning requirements for commercial development",
    "collection": "la_plata_county_code",
    "num_results": 6
  }'
```

### Stream Events

The streaming endpoint returns Server-Sent Events:

**Start Event**:
```
data: {"event":"start","model_loaded":true,"collection":"la_plata_county_code"}
```

**Token Events** (continuous):
```
data: {"event":"token","text":"Based"}
data: {"event":"token","text":" on"}  
data: {"event":"token","text":" the"}
data: {"event":"token","text":" provided"}
data: {"event":"token","text":" sources"}
```

**End Event**:
```
data: {"event":"end","answer":null,"citations":[],"sources":[]}
```

### Streaming vs Non-Streaming

| Feature | Streaming | Non-Streaming |
|---------|-----------|---------------|
| **Response Time** | Immediate start | Wait for completion |
| **User Experience** | Real-time feedback | All-at-once result |
| **Citations** | Not included | Full citation analysis |
| **Verification** | Not included | Answer support checking |
| **Use Case** | Interactive chat | API integration |

## Collections

### Available Collections

| Collection | Content | Use Cases |
|------------|---------|-----------|
| `la_plata_county_code` | Municipal legal code | Building permits, zoning, subdivisions |
| `la_plata_assessor` | Property assessment data | Property values, tax assessment |

### Collection-Specific Examples

**Legal Code Queries**:
```bash
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What are setback requirements for residential buildings?",
    "collection": "la_plata_county_code",
    "num_results": 6
  }'
```

**Property Assessment Queries**:
```bash
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "How are property values determined for taxation?", 
    "collection": "la_plata_assessor",
    "num_results": 8
  }'
```

## Query Patterns and Best Practices

### Effective Query Patterns

**✅ Good Queries**:
- "Requirements for building permits"
- "Minor subdivision procedures" 
- "Zoning restrictions for commercial use"
- "Property tax assessment methods"

**❌ Less Effective**:
- "Tell me everything about building"
- "What can I do?" (too broad)
- "Is this legal?" (without context)
- Single word queries

### Query Normalization

The system automatically transforms verbose questions:

| Original Query | Normalized | Result |
|----------------|------------|--------|
| "What are the requirements for a minor subdivision in La Plata County?" | "minor subdivision requirements" | ✅ Finds section 67-4 |
| "How do I apply for a building permit?" | "building permit application process" | ✅ Finds permit procedures |
| "Can I build a deck without a permit?" | "building a deck without a permit regulations" | ✅ Finds deck exemptions |

### Advanced Query Techniques

**Use Specific Legal Terms**:
```json
{
  "query": "section 67-4 minor subdivision requirements",
  "collection": "la_plata_county_code"
}
```

**Combine Multiple Concepts**:
```json
{
  "query": "commercial zoning setback requirements",
  "collection": "la_plata_county_code"
}
```

**Property-Specific Searches**:
```json
{
  "query": "agricultural land assessment valuation",
  "collection": "la_plata_assessor"
}
```

## Response Quality and Citations

### Citation System

The system provides numbered citations like `[1]`, `[2]` that reference the sources array:

- **Citation Extraction**: Automatically detects citation markers in generated text
- **Source Mapping**: Each citation maps to specific source documents
- **Validation**: Ensures citations only reference provided sources
- **Auto-Generation**: Adds citations when model omits them but content is supported

### Answer Verification

Each response includes verification analysis:

```json
{
  "verification": {
    "total_sentences": 12,
    "supported_sentences": 10, 
    "unsupported_sentences": 2,
    "support_ratio": 0.833,
    "avg_support_score": 0.42,
    "details": [
      {
        "sentence": "Minor subdivisions require permits [1]",
        "support_score": 0.78,
        "best_source": 1,
        "status": "supported"
      }
    ]
  }
}
```

### Quality Indicators

**High Quality Response**:
- Support ratio > 0.8
- Multiple diverse sources cited
- Specific section references
- Clear legal language

**Lower Quality Response**:
- Support ratio < 0.6
- Few or missing citations
- Generic statements
- Vague references

## Error Handling

### Common Errors

**Model Not Loaded**:
```json
{
  "error": "Model not loaded. Load via POST /rag/model/load"
}
```
**Solution**: Load a model first

**Search API Unavailable**:
```json
{
  "error": "Connection refused to search API"
}
```
**Solution**: Start search API with `./scripts/api.sh start`

**Invalid Parameters**:
```json
{
  "error": "query is required"
}
```
**Solution**: Check request format and required fields

### Graceful Degradation

When retrieval fails, the system falls back to direct model responses:
- No sources or citations provided
- Answer marked as unsupported
- User informed of limited information

## Performance Considerations

### Response Time Factors

- **Query Complexity**: Simple queries (2-4s), complex queries (8-15s)
- **Model Size**: 4-bit models faster than 8-bit models
- **Number of Sources**: More sources = longer retrieval time
- **Reference Expansion**: Legal cross-references add 200-500ms

### Optimization Tips

**For Speed**:
- Use 4-bit models
- Reduce `num_results` to 4-6
- Lower `max_tokens` to 600-800
- Use specific, focused queries

**For Accuracy**:
- Use 8-bit models when possible
- Increase `num_results` to 8-12
- Set `temperature` to 0.2 or lower
- Include legal section numbers in queries

## Integration Examples

### Frontend Integration

**JavaScript Streaming Client**:
```javascript
const eventSource = new EventSource('/rag/answer/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: userQuestion,
    collection: 'la_plata_county_code',
    num_results: 6
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.event === 'token') {
    appendToAnswer(data.text);
  }
};
```

**React Integration**:
```jsx
const useRAGQuery = (query) => {
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  
  const submitQuery = async () => {
    const response = await fetch('/rag/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, num_results: 6 })
    });
    
    const result = await response.json();
    setAnswer(result.answer);
    setSources(result.sources);
  };
  
  return { answer, sources, submitQuery };
};
```

### API Wrapper

**Python Client**:
```python
import requests

class RAGClient:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
    
    def query(self, question, collection="la_plata_county_code", num_results=6):
        response = requests.post(f"{self.base_url}/rag/answer", 
            json={
                "query": question,
                "collection": collection,
                "num_results": num_results
            }
        )
        return response.json()
    
    def stream_query(self, question, collection="la_plata_county_code"):
        response = requests.post(f"{self.base_url}/rag/answer/stream",
            json={"query": question, "collection": collection},
            stream=True
        )
        for line in response.iter_lines():
            if line.startswith(b'data: '):
                yield json.loads(line[6:])

# Usage
client = RAGClient()
result = client.query("What are building permit requirements?")
print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])}")
```