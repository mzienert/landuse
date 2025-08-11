# Search API Architecture

## Overview

The La Plata County Search API provides semantic search capabilities across municipal legal documents and property assessment records using vector embeddings and ChromaDB storage.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                      │
│         (RAG API, Frontend, Direct API Calls)               │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP Requests
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Search API (Port 8000)                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Flask API Layer                         │ │
│  │            (apis/search/search_api.py)                  │ │
│  │                                                         │ │
│  │  • /search (full search endpoint)                       │ │
│  │  • /search/simple (simplified results)                  │ │
│  │  • /collections (metadata)                              │ │
│  │  • /health (system status)                              │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Search Processing Pipeline                  │
│                                                             │
│  ┌───────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   Query       │    │   Embedding     │    │   Vector    │ │
│  │ Processing    │───▶│  Generation     │───▶│   Search    │ │
│  │               │    │(SentenceTransf) │    │ (ChromaDB)  │ │
│  └───────────────┘    └─────────────────┘    └─────────────┘ │
│                                │                             │
│                                ▼                             │
│                      ┌─────────────────┐                     │
│                      │    Result       │                     │
│                      │  Formatting     │                     │
│                      └─────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                 Storage and Models                          │
│                                                             │
│  ┌─────────────────────────┐    ┌─────────────────────────┐ │
│  │    ChromaDB Vector      │    │   SentenceTransformers  │ │
│  │    Database             │    │      Model              │ │
│  │                         │    │                         │ │
│  │  • la_plata_county_code │    │  • intfloat/e5-large-v2 │ │
│  │  • la_plata_assessor    │    │  • 1024D embeddings     │ │
│  │  • 47,528+ documents    │    │  • Semantic similarity  │ │
│  └─────────────────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Flask API Layer (`search_api.py`)
- **Role**: HTTP interface for search operations
- **Responsibilities**:
  - Request handling and validation
  - Parameter parsing and sanitization
  - Response formatting and error handling
  - System health monitoring

**Key Features**:
- CORS support for web applications
- Multiple endpoint formats (GET/POST, simple/full)
- Collection-specific search with validation
- Comprehensive error handling

### 2. Query Processing
- **Role**: Transform user queries into searchable format
- **Responsibilities**:
  - Input validation and sanitization
  - Query parameter extraction
  - Collection routing

**Features**:
- Support for both GET and POST requests
- Parameter validation (num_results: 1-50)
- Collection selection and validation
- Query logging for debugging

### 3. Embedding Generation
- **Model**: `intfloat/e5-large-v2` (1024 dimensions)
- **Role**: Convert text queries to vector representations
- **Responsibilities**:
  - Query vectorization using pre-trained model
  - Consistent embedding generation
  - Model lifecycle management

**Technical Details**:
- **Model Type**: SentenceTransformers-based encoder
- **Dimensions**: 1024D vectors optimized for legal text
- **Performance**: Hardware-accelerated (MPS on Apple Silicon)
- **Memory**: ~2GB model footprint

### 4. Vector Search Engine (ChromaDB)
- **Role**: High-performance similarity search
- **Responsibilities**:
  - Vector similarity computation
  - Result ranking by cosine distance
  - Efficient retrieval at scale

**Performance Characteristics**:
- **Index Type**: HNSW (Hierarchical Navigable Small World)
- **Distance Metric**: Cosine similarity
- **Query Speed**: <100ms for typical searches
- **Scalability**: 50K+ documents per collection

### 5. Result Formatting
- **Role**: Structure search results for different use cases
- **Responsibilities**:
  - Collection-specific metadata extraction
  - Distance-to-relevance score conversion
  - Response format standardization

## Data Collections

### Legal Code Collection (`la_plata_county_code`)
- **Documents**: 1,298 legal sections
- **Content**: Municipal code, zoning regulations, building requirements
- **Structure**: Section-based chunking with hierarchical metadata
- **Use Cases**: Legal research, compliance checking, regulation lookup

**Metadata Schema**:
```json
{
  "text": "Full section text content",
  "full_text_length": 2847,
  "section_id": "67-4",
  "collection": "la_plata_county_code"
}
```

### Property Assessment Collection (`la_plata_assessor`)
- **Documents**: 46,230 property records
- **Content**: Property descriptions, ownership data, assessment details
- **Structure**: Account-based records with combined text descriptions
- **Use Cases**: Property research, ownership lookup, assessment analysis

**Metadata Schema**:
```json
{
  "text": "Combined property description",
  "account_number": "R123456",
  "text_length": 156,
  "collection": "la_plata_assessor"
}
```

## API Endpoints

### Health and Metadata Endpoints

#### `GET /health`
**Purpose**: System health and capacity monitoring
```json
{
  "status": "healthy",
  "models_loaded": 1,
  "collections_connected": 2,
  "total_documents": 47528,
  "available_collections": ["la_plata_county_code", "la_plata_assessor"]
}
```

#### `GET /collections`
**Purpose**: Collection metadata and statistics
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
    }
  },
  "total_collections": 2,
  "available_collections": 2
}
```

### Search Endpoints

#### `GET/POST /search`
**Purpose**: Comprehensive search with full metadata
- **Parameters**: `query` (required), `collection`, `num_results` (1-50)
- **Response**: Complete result objects with distances, metadata, and content

#### `GET /search/simple`
**Purpose**: Streamlined search for integration (used by RAG API)
- **Parameters**: `query` (required), `collection`, `num_results` (1-10)
- **Response**: Simplified format optimized for downstream processing

**Example Response**:
```json
{
  "query": "building permits",
  "collection": "la_plata_county_code",
  "collection_name": "Land Use Code",
  "results": [
    {
      "text": "Building permits are required for...",
      "relevance": "0.892",
      "collection": "la_plata_county_code",
      "section": "18-35"
    }
  ]
}
```

## Performance Characteristics

### Latency Profile
- **Model Loading**: 2-5 seconds (startup only)
- **Query Embedding**: 20-50ms per query
- **Vector Search**: 30-80ms per collection
- **Result Formatting**: 5-15ms
- **Total Response Time**: 100-200ms typical

### Throughput Capacity
- **Concurrent Requests**: 20-50 simultaneous (depending on hardware)
- **Queries per Second**: 50-100 QPS sustainable
- **Memory Usage**: 3-4GB (model + index + overhead)
- **CPU Usage**: Moderate during embedding, low during search

### Scalability Considerations
- **Document Limit**: 100K+ documents per collection (ChromaDB scales well)
- **Memory Growth**: Linear with document count (~40MB per 10K docs)
- **Query Complexity**: Constant time regardless of document count
- **Horizontal Scaling**: Stateless API supports load balancing

## Storage Architecture

### ChromaDB Configuration
```python
client = chromadb.PersistentClient(path="./chroma_db")
collection.add(
    documents=texts,
    metadatas=metadata,
    ids=document_ids,
    embeddings=vectors  # 1024D float32 vectors
)
```

### Data Organization
- **Directory Structure**: `./chroma_db/[collection_uuid]/`
- **Index Files**: HNSW index, metadata store, document store
- **Persistence**: Automatic persistence with WAL (Write-Ahead Logging)
- **Backup**: Simple directory copy for full backup

### Embedding Storage
- **Format**: Float32 arrays (1024 dimensions × 4 bytes = 4KB per document)
- **Compression**: ChromaDB handles internal optimization
- **Indexing**: HNSW with configurable ef_construction and M parameters
- **Memory Mapping**: Efficient memory usage with mmap

## Integration Architecture

### RAG API Integration
```python
# RAG API calls Search API
def fetch_simple_search(query, collection="la_plata_county_code", num_results=5):
    url = "http://localhost:8000/search/simple"
    params = {"query": query, "collection": collection, "num_results": num_results}
    response = requests.get(url, params=params)
    return response.json()
```

### Frontend Integration
```javascript
// Direct API calls from Next.js
const searchResults = await fetch('/api/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    query: userInput,
    collection: 'la_plata_county_code',
    num_results: 10
  })
});
```

## Quality and Relevance

### Embedding Quality
- **Model**: `intfloat/e5-large-v2` optimized for English text retrieval
- **Training**: Large-scale web text with contrastive learning
- **Legal Domain**: Good performance on legal terminology
- **Multilingual**: English-focused but handles legal Latin phrases

### Search Relevance Factors
1. **Semantic Similarity**: Core vector similarity scoring
2. **Term Coverage**: Query terms present in results
3. **Document Length**: Balanced representation across section sizes
4. **Collection Context**: Domain-specific relevance weighting

### Quality Metrics
```python
relevance_score = 1 / (1 + cosine_distance)  # 0.0-1.0 scale
distance_threshold = 0.8  # Filter very dissimilar results
result_diversity = True   # ChromaDB handles near-duplicate filtering
```

## Security and Privacy

### Data Security
- **Local Processing**: All data remains on local infrastructure
- **No External APIs**: No third-party API calls for sensitive legal data
- **Access Control**: IP-based access control configurable
- **Input Sanitization**: Query validation and sanitization

### Privacy Considerations
- **Query Logging**: Queries logged locally for debugging (configurable)
- **Data Retention**: No permanent query storage
- **Anonymization**: No user identification in logs
- **Compliance**: Suitable for government/legal data handling

## Monitoring and Maintenance

### Health Monitoring
```bash
# Automated health checks
curl http://localhost:8000/health

# Expected healthy response
{
  "status": "healthy",
  "models_loaded": 1,
  "collections_connected": 2,
  "total_documents": 47528
}
```

### Performance Monitoring
- **Response Times**: Track P95/P99 latencies
- **Error Rates**: Monitor 4xx/5xx response rates  
- **Resource Usage**: Memory, CPU, disk I/O
- **Search Quality**: Relevance feedback and user satisfaction

### Maintenance Tasks
- **Index Optimization**: Periodic HNSW index rebuilding
- **Data Updates**: Document addition/removal procedures
- **Model Updates**: Sentence transformer model upgrades
- **Backup Management**: Regular ChromaDB backup procedures

This architecture provides a robust, scalable foundation for semantic search across legal and property data while maintaining high performance and data privacy.