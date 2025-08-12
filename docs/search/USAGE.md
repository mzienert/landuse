# Search API Usage Guide

## API Endpoints Overview

The Search API provides semantic search across La Plata County legal documents and property records.

| Endpoint | Method | Purpose | Response Format |
|----------|---------|---------|-----------------|
| `/health` | GET | System health and statistics | JSON status |
| `/collections` | GET | Available collections metadata | JSON collection info |
| `/search` | GET/POST | Full search with metadata | JSON with complete results |
| `/search/simple` | GET | Simplified search (used by RAG) | JSON with streamlined results |

**Base URL**: `http://localhost:8000`

## Health and System Information

### Check API Health

```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "models_loaded": 1,
  "collections_connected": 2,
  "total_documents": 47528,
  "available_collections": ["la_plata_county_code", "la_plata_assessor"]
}
```

### Get Collection Information

```bash
curl http://localhost:8000/collections
```

**Response**:
```json
{
  "collections": {
    "la_plata_county_code": {
      "name": "Land Use Code",
      "description": "La Plata County Land Use Code regulations",
      "model": "intfloat/e5-large-v2",
      "dimensions": 1024,
      "available": true,
      "document_count": 1298
    },
    "la_plata_assessor": {
      "name": "Property Assessor Data",
      "description": "Property assessment and ownership data", 
      "model": "intfloat/e5-large-v2",
      "dimensions": 1024,
      "available": true,
      "document_count": 46230
    }
  },
  "total_collections": 2,
  "available_collections": 2
}
```

## Search Endpoints

### Full Search Endpoint (`/search`)

Provides complete search results with all metadata and relevance information.

#### GET Request Format

```bash
curl "http://localhost:8000/search?query=building%20permits&collection=la_plata_county_code&num_results=5"
```

#### POST Request Format

```bash
curl -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "building permit requirements",
    "collection": "la_plata_county_code", 
    "num_results": 5
  }'
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search query text |
| `collection` | string | `"la_plata_county_code"` | Collection to search |
| `num_results` | integer | 5 | Number of results (1-50) |

#### Response Format

```json
{
  "query": "building permit requirements",
  "collection": "la_plata_county_code",
  "collection_name": "Land Use Code", 
  "num_results": 3,
  "results": [
    {
      "id": "18-35",
      "distance": 0.234,
      "content": "Building permits shall be required for construction, alteration, repair, or demolition of any building or structure...",
      "collection": "la_plata_county_code",
      "collection_name": "Land Use Code",
      "section_id": "18-35",
      "full_text_length": 2847
    }
  ]
}
```

### Simple Search Endpoint (`/search/simple`)

Streamlined endpoint optimized for integration with other services (used by RAG API).

#### Request Format

```bash
curl "http://localhost:8000/search/simple?query=subdivision%20requirements&collection=la_plata_county_code&num_results=3"
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search query text |
| `collection` | string | `"la_plata_county_code"` | Collection to search |
| `num_results` | integer | 5 | Number of results (1-10) |

#### Response Format

```json
{
  "query": "subdivision requirements",
  "collection": "la_plata_county_code", 
  "collection_name": "Land Use Code",
  "results": [
    {
      "text": "Minor subdivisions shall be processed as a minor land use permit pursuant to the procedures set forth in section 66-20...",
      "relevance": "0.892",
      "collection": "la_plata_county_code",
      "section": "67-4"
    },
    {
      "text": "Major subdivisions involve the division of land into four (4) or more lots...",
      "relevance": "0.847", 
      "collection": "la_plata_county_code",
      "section": "67-3"
    }
  ]
}
```

## Collections

### Legal Code Collection (`la_plata_county_code`)

**Content**: Municipal legal code sections, zoning regulations, building requirements

**Use Cases**:
- Building permit requirements
- Zoning restrictions and allowances
- Subdivision regulations
- Land use compliance

**Example Queries**:
```bash
# Building regulations
curl "http://localhost:8000/search/simple?query=building%20permit%20residential&collection=la_plata_county_code"

# Zoning information  
curl "http://localhost:8000/search/simple?query=commercial%20zoning%20requirements&collection=la_plata_county_code"

# Subdivision rules
curl "http://localhost:8000/search/simple?query=minor%20subdivision%20three%20lots&collection=la_plata_county_code"
```

### Property Assessment Collection (`la_plata_assessor`)

**Content**: Property records, ownership data, assessment information

**Use Cases**:
- Property ownership lookup
- Assessment value research
- Property description search
- Owner contact information

**Example Queries**:
```bash
# Property by owner name
curl "http://localhost:8000/search/simple?query=Smith%20family%20property&collection=la_plata_assessor"

# Property by location
curl "http://localhost:8000/search/simple?query=Main%20Street%20residential&collection=la_plata_assessor"

# Property by characteristics
curl "http://localhost:8000/search/simple?query=agricultural%20land%20160%20acres&collection=la_plata_assessor"
```

## Query Best Practices

### Effective Query Patterns

**✅ Good Queries**:
- **Specific terms**: "building permit residential construction"  
- **Legal concepts**: "minor subdivision three lots or fewer"
- **Regulatory areas**: "commercial zoning setback requirements"
- **Property details**: "agricultural land Bayfield area"

**❌ Less Effective**:
- **Too broad**: "building" (too many results)
- **Too vague**: "what can I do" (no specific focus)
- **Single words**: "permit" (lacks context)
- **Non-legal terms**: "help me please" (not domain-specific)

### Query Optimization

#### Legal Code Searches
```bash
# Instead of "Can I build a deck?"
curl "http://localhost:8000/search/simple?query=deck%20building%20permit%20requirements"

# Instead of "What is zoning?"
curl "http://localhost:8000/search/simple?query=residential%20commercial%20zoning%20regulations"

# Instead of "Subdivision rules"
curl "http://localhost:8000/search/simple?query=minor%20major%20subdivision%20procedures"
```

#### Property Assessment Searches
```bash
# Search by owner characteristics
curl "http://localhost:8000/search/simple?query=Johnson%20family%20ranch%20property&collection=la_plata_assessor"

# Search by property features
curl "http://localhost:8000/search/simple?query=irrigation%20ditch%20water%20rights&collection=la_plata_assessor"

# Search by location and size
curl "http://localhost:8000/search/simple?query=Durango%20residential%20subdivision%20lots&collection=la_plata_assessor"
```

### Advanced Query Techniques

#### Multi-term Queries
Use multiple related terms for better coverage:
```bash
curl "http://localhost:8000/search/simple?query=building%20construction%20permit%20residential%20requirements"
```

#### Phrase Queries
Include specific phrases for exact matches:
```bash
curl "http://localhost:8000/search/simple?query=accessory%20dwelling%20unit%20ADU%20regulations"
```

#### Context-Specific Terms
Use domain-specific terminology:
```bash
curl "http://localhost:8000/search/simple?query=setback%20easement%20right%20of%20way%20encroachment"
```

## Response Interpretation

### Relevance Scores

The search API provides relevance scores based on semantic similarity:

- **0.9+**: Highly relevant, very similar content
- **0.8-0.9**: Good relevance, related concepts  
- **0.7-0.8**: Moderate relevance, some connection
- **0.6-0.7**: Low relevance, tangentially related
- **<0.6**: Poor relevance, may not be useful

### Distance vs. Relevance

```python
# API converts cosine distance to relevance score
relevance = 1 / (1 + distance)

# Lower distance = higher relevance
# Distance 0.1 → Relevance 0.909 (very relevant)
# Distance 0.5 → Relevance 0.667 (moderately relevant)  
# Distance 1.0 → Relevance 0.500 (low relevance)
```

### Result Ranking

Results are automatically ranked by semantic similarity:
1. **Most relevant** content appears first
2. **Diverse results** avoid near-duplicates
3. **Complete sections** preserved (no truncation in simple search)
4. **Metadata preserved** for downstream processing

## Integration Examples

### RAG API Integration

The RAG API uses the simple search endpoint:

```python
# RAG API calls Search API
import requests

def fetch_simple_search(query, collection="la_plata_county_code", num_results=5):
    url = "http://localhost:8000/search/simple"
    params = {
        "query": query,
        "collection": collection, 
        "num_results": num_results
    }
    response = requests.get(url, params=params)
    return response.json()

# Usage in RAG pipeline
search_results = fetch_simple_search("building permit requirements", num_results=8)
for result in search_results['results']:
    print(f"Section {result['section']}: {result['text'][:100]}...")
```

### Frontend Integration

JavaScript client for web applications:

```javascript
// Simple search from frontend
async function searchDocuments(query, collection = 'la_plata_county_code') {
  const response = await fetch(`/api/search/simple?query=${encodeURIComponent(query)}&collection=${collection}&num_results=10`);
  const data = await response.json();
  return data.results;
}

// Usage
const results = await searchDocuments('zoning requirements commercial');
results.forEach(result => {
  console.log(`${result.section}: ${result.relevance} - ${result.text.substring(0, 150)}...`);
});
```

### Python Client Library

```python
import requests
from typing import List, Dict, Optional

class LaPlataSearchClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def health_check(self) -> Dict:
        """Check API health and get system info"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_collections(self) -> Dict:
        """Get available collections and metadata"""  
        response = requests.get(f"{self.base_url}/collections")
        response.raise_for_status()
        return response.json()
    
    def search_simple(self, query: str, collection: str = "la_plata_county_code", 
                     num_results: int = 5) -> List[Dict]:
        """Simple search optimized for processing"""
        params = {
            "query": query,
            "collection": collection,
            "num_results": num_results
        }
        response = requests.get(f"{self.base_url}/search/simple", params=params)
        response.raise_for_status()
        return response.json()["results"]
    
    def search_full(self, query: str, collection: str = "la_plata_county_code",
                   num_results: int = 5) -> Dict:
        """Full search with complete metadata"""
        data = {
            "query": query, 
            "collection": collection,
            "num_results": num_results
        }
        response = requests.post(f"{self.base_url}/search", json=data)
        response.raise_for_status()
        return response.json()

# Usage example
client = LaPlataSearchClient()

# Check if API is running
health = client.health_check()
print(f"API Status: {health['status']}, Documents: {health['total_documents']}")

# Search for building permits
results = client.search_simple("building permit requirements", num_results=5)
for result in results:
    print(f"Section {result['section']}: Relevance {result['relevance']}")
    print(f"Content: {result['text'][:200]}...\n")
```

## Testing and Development

### Application Factory Pattern

The Search API uses Flask's application factory pattern for better testability and configuration management:

```python
from apis.search.app_factory import create_app

# Create test instance (in-memory database)
test_app = create_app('testing')

# Test with Flask test client
with test_app.test_client() as client:
    response = client.get('/health')
    assert response.status_code == 200

# Create development instance
dev_app = create_app('development')

# Create production instance
prod_app = create_app('production')
```

### Testing Configuration

Testing mode provides isolated configuration with in-memory ChromaDB:

```python
# Testing mode - uses in-memory database
test_app = create_app('testing')
assert test_app.config['TESTING'] == True
assert test_app.config['CHROMA_DB_PATH'] == ':memory:'

# Search engine initializes but doesn't auto-load collections
search_engine = test_app.config['SEARCH_ENGINE']
```

### Integration Testing Examples

```python
import unittest
from apis.search.app_factory import create_app

class TestSearchAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('status', data)

    def test_collections_endpoint(self):
        response = self.client.get('/collections')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('collections', data)

    def test_simple_search_no_collections(self):
        # In testing mode, collections aren't auto-loaded
        response = self.client.get('/search/simple?query=test')
        # Should handle gracefully when no collections available
        self.assertIn(response.status_code, [200, 503])
```

### Environment-based Testing

```bash
# Run tests in testing mode (in-memory ChromaDB)
export FLASK_ENV=testing
python -m unittest discover tests/

# Test with custom configuration
export CHROMA_DB_PATH=/tmp/test_chroma
export DEFAULT_SEARCH_LIMIT=3
python test_search_api.py

# Integration test with real collections (development mode)
export FLASK_ENV=development
python test_full_integration.py
```

### Mock Testing for ChromaDB

```python
import unittest.mock
from apis.search.app_factory import create_app

class TestSearchAPIMocked(unittest.TestCase):
    @unittest.mock.patch('apis.search.search_engine.chromadb.Client')
    def test_search_with_mock_db(self, mock_client):
        # Mock ChromaDB responses
        mock_collection = unittest.mock.Mock()
        mock_collection.query.return_value = {
            'documents': [['test document']],
            'distances': [[0.5]],
            'ids': [['test_id']]
        }
        mock_client.return_value.get_collection.return_value = mock_collection
        
        app = create_app('testing')
        with app.test_client() as client:
            response = client.get('/search/simple?query=test')
            # Should work with mocked data
```

## Error Handling

### Common Error Responses

#### Missing Query Parameter
```json
{
  "error": "Query parameter is required"
}
```

#### Invalid Collection
```json
{
  "error": "Invalid collection. Available: ['la_plata_county_code', 'la_plata_assessor']"
}
```

#### Service Unavailable
```json
{
  "error": "Collection 'la_plata_county_code' not available"
}
```

### Error Handling Best Practices

```python
import requests
from requests.exceptions import RequestException

def safe_search(query, collection="la_plata_county_code", num_results=5):
    try:
        response = requests.get(
            "http://localhost:8000/search/simple",
            params={"query": query, "collection": collection, "num_results": num_results},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if 'error' in data:
            print(f"Search API error: {data['error']}")
            return []
            
        return data.get('results', [])
        
    except RequestException as e:
        print(f"Request failed: {e}")
        return []
    except ValueError as e:
        print(f"JSON decode error: {e}")
        return []

# Usage with error handling
results = safe_search("building permits", num_results=3)
if results:
    print(f"Found {len(results)} results")
else:
    print("No results or error occurred")
```

## Performance Considerations

### Response Time Optimization

- **Simple queries** (1-3 words): ~100ms
- **Complex queries** (5+ words): ~150ms  
- **Large result sets** (20+ results): ~200ms
- **Collection switching**: No additional overhead

### Request Optimization

```bash
# Use simple endpoint for integration
curl "http://localhost:8000/search/simple?query=permits&num_results=5"

# Use POST for complex queries to avoid URL encoding
curl -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "complex query with special characters & symbols"}'

# Limit results for faster responses
curl "http://localhost:8000/search/simple?query=zoning&num_results=3"
```

### Caching Strategies

The API is stateless and suitable for caching:

```python
# Simple in-memory cache
import time
from typing import Dict, Tuple

class SearchCache:
    def __init__(self, ttl_seconds: int = 300):  # 5-minute TTL
        self.cache: Dict[str, Tuple[Dict, float]] = {}
        self.ttl = ttl_seconds
    
    def get(self, query: str, collection: str) -> Optional[Dict]:
        key = f"{collection}:{query}"
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            else:
                del self.cache[key]
        return None
    
    def set(self, query: str, collection: str, result: Dict):
        key = f"{collection}:{query}"
        self.cache[key] = (result, time.time())

# Usage
cache = SearchCache()
cached_result = cache.get("building permits", "la_plata_county_code")
if not cached_result:
    cached_result = client.search_simple("building permits")
    cache.set("building permits", "la_plata_county_code", cached_result)
```

This comprehensive usage guide provides everything needed to effectively use the La Plata County Search API for semantic search across legal and property data.