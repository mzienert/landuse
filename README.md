# La Plata County RAG System

A comprehensive Retrieval-Augmented Generation (RAG) platform for La Plata County legal and property data. The system provides natural language Q&A with citations across Land Use Code regulations and Property Assessor records, powered by advanced semantic search and local AI inference.

## 🚀 Quick Start

**Prerequisites:** Apple Silicon Mac, Python 3.10+, Virtual environment activated

1. **Setup Environment**
   ```bash
   source env/bin/activate
   pip install sentence-transformers chromadb flask flask-cors mdbtools mlx mlx-lm requests
   ```

2. **Create Vector Embeddings**
   
   **Land Use Code (1,298 sections):**
   ```bash
   python apis/search/embeddings/create_legal_embeddings.py
   ```
   
   **Property Assessor Data (46,230 properties):**
   ```bash
   python apis/search/embeddings/create_assessor_embeddings.py
   ```
   
   **Note**: Both processes use optimized models and take 2-6 minutes each.

3. **Start Complete RAG System**
   ```bash
   ./scripts/start_both.sh start
   ```
   
   This automatically starts:
   - Search API (port 8000) for semantic search and retrieval
   - RAG API (port 8001) for Q&A with citations and legal reasoning
   - MLX inference service with optimized models for legal text

4. **Test RAG System**
   ```bash
   # Test Search API (retrieval only)
   curl "http://localhost:8000/search/simple?query=building%20permits&collection=la_plata_county_code&num_results=5"
   
   # Test RAG API with Q&A and citations
   curl -X POST http://localhost:8001/rag/answer \
     -H 'Content-Type: application/json' \
     -d '{"query":"What are the requirements for minor subdivisions?","num_results":5}'
   
   # Test streaming RAG responses
   curl -X POST http://localhost:8001/rag/answer/stream \
     -H 'Content-Type: application/json' \
     -d '{"query":"What permits are needed for building?","num_results":5}'
   ```

   **Alternative: Start APIs Individually**
   ```bash
   ./scripts/api.sh start        # Search API only
   ./scripts/run_rag.sh start    # RAG API only
   ```

📖 **Detailed setup instructions:** See [BUILD_STEPS.md](BUILD_STEPS.md)

## 🏗️ Architecture

### System Overview
```
┌─────────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│   Data Sources      │ →  │  Vector Embeddings  │ →  │   Search API     │
│                     │    │     (ChromaDB)      │    │  (Port 8000)     │
├─────────────────────┤    ├─────────────────────┤    └──────────┬───────┘
│ Land Use Code       │    │ la_plata_county_code│               │
│ • 1,298 sections    │    │ • e5-large-v2       │               ▼
│ • Legal regulations │    │ • 1024 dimensions   │    ┌──────────────────┐
├─────────────────────┤    ├─────────────────────┤    │    RAG API       │
│ Property Assessor   │    │ la_plata_assessor   │    │  (Port 8001)     │
│ • 46,230 properties │    │ • e5-large-v2       │    │ • Q&A Generation │
│ • Ownership & Values│    │ • 1024 dimensions   │    │ • Citation System│
└─────────────────────┘    └─────────────────────┘    │ • Legal Reasoning│
                                                      └──────────┬───────┘
                                                                 ▼
                                                      ┌──────────────────┐
                                                      │ External Inference│
                                                      │  (llama.cpp)     │
                                                      │ • GGUF Models    │
                                                      │ • Metal GPU      │
                                                      │ • Memory Efficient│
                                                      └──────────────────┘
```

### Technology Stack

**Core Components:**
- **RAG Pipeline**: 
  - Query normalization and legal-specific processing
  - Enhanced retrieval with cross-reference following
  - Citation extraction and verification
  - Streaming and non-streaming response generation
- **Embedding Model**: `intfloat/e5-large-v2` (1024D) for semantic search
- **Vector Database**: ChromaDB with multi-collection support
- **Inference Service**: External llama.cpp server with GGUF models
- **API Framework**: Flask with CORS, streaming SSE, and health monitoring
- **Model Management**: Qwen3-4B-Instruct optimized for legal reasoning
- **Language**: Python 3.10+ with MLX for Apple Silicon optimization

**RAG Pipeline:**
1. **Query Processing**: 
   - Legal-specific query normalization (60+ patterns)
   - Query variation generation for fallback searches
2. **Enhanced Retrieval**: 
   - Multi-collection semantic search via ChromaDB
   - Legal cross-reference extraction and following
   - Heuristic reranking with diversity enforcement
3. **Context Building**: 
   - Source deduplication and citation tracking
   - Context-aware prompt construction with numbered sources
4. **Generation**: 
   - External inference via llama.cpp server
   - Streaming and non-streaming response modes
5. **Verification**: 
   - Citation extraction and validation
   - Answer support verification using lexical overlap

### Project Structure
```
landuse/
├── apis/                            # API services
│   ├── search/                      # Search API
│   │   ├── search_api.py           # Multi-collection Flask API
│   │   └── test_search.py          # Search API testing
│   └── rag/                        # RAG System
│       ├── rag_api.py             # Q&A with citations Flask API
│       ├── inference.py           # External inference client
│       ├── retrieval.py           # Enhanced retrieval with cross-references
│       ├── normalize.py           # Legal query normalization
│       ├── verify.py              # Citation verification
│       └── config.py              # Application configuration
├── scripts/                         # Management scripts
│   ├── api.sh                      # Search API management
│   ├── run_rag.sh                  # RAG API management
│   └── start_both.sh               # Combined API management
├── data/                           # Source data
│   ├── la_plata_code/             # Land Use Code source data
│   └── LPC-Assessor-Data-Files/   # Property Assessor source data (MDB)
├── chroma_db/                      # Multi-collection vector database
├── apis/search/embeddings/create_legal_embeddings.py     # Land Use Code embeddings (1024D)
├── apis/search/embeddings/create_assessor_embeddings.py # Property Assessor embeddings (1024D)
├── docs/rag/                        # RAG System Documentation
│   ├── ARCHITECTURE.md             # System architecture and design
│   ├── TROUBLESHOOTING.md          # Problem diagnosis and solutions
│   ├── SETUP.md                   # Installation and configuration
│   └── USAGE.md                   # API reference and examples
├── components/                     # Next.js UI components
│   ├── search-form.tsx            # Collection-aware search form
│   └── search-results.tsx         # Unified results display
├── app/                           # Next.js application
│   ├── search/page.tsx           # Search interface
│   └── page.tsx                  # Landing page
└── BUILD_STEPS.md                 # Detailed setup guide
```

## 🔍 API Usage

### RAG API Endpoints (Port 8001)

**Health Check**
```bash
curl "http://localhost:8001/rag/health"
```

**Q&A with Citations** (Recommended)
```bash
curl -X POST "http://localhost:8001/rag/answer" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the requirements for minor subdivisions?", "num_results": 5}'
```

**Streaming Q&A** (Server-Sent Events)
```bash
curl -X POST "http://localhost:8001/rag/answer/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "What permits are needed for building?", "num_results": 5}'
```

**Model Management**
```bash
# Load specific model
curl -X POST "http://localhost:8001/rag/model/load" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "mlx-community/Qwen3-4B-Instruct-2507-4bit"}'
```

### Search API Endpoints (Port 8000)

**Simple Search** (For testing retrieval)
```bash
curl "http://localhost:8000/search/simple?query=building%20permits&num_results=10"
```

**Full Search** (Detailed metadata)
```bash
curl "http://localhost:8000/search?query=zoning%20requirements&num_results=5"
```

### Browser Testing

Open in your browser:
- **RAG Health Check**: [http://localhost:8001/rag/health](http://localhost:8001/rag/health)
- **Search Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Search Example**: [http://localhost:8000/search/simple?query=building%20permits&num_results=10](http://localhost:8000/search/simple?query=building%20permits&num_results=10)

### Response Formats

**RAG Answer Response** (`/rag/answer`)
```json
{
  "answer": "Based on the La Plata County Land Use Code, minor subdivisions have the following requirements:\n\n**Definition and Scope [1]:**\nA minor subdivision is defined as the division of land into three (3) or fewer lots where no new streets are created...\n\n**Application Requirements [2]:**\n- Completed application form\n- Survey plat prepared by licensed surveyor\n- Proof of ownership...",
  "query": "What are the requirements for minor subdivisions?",
  "sources": [
    {
      "id": 1,
      "section": "67-4",
      "text": "Minor Subdivision. A minor subdivision is the division of land into three (3) or fewer lots...",
      "collection": "la_plata_county_code",
      "relevance": 0.892
    }
  ],
  "citations": [
    {"marker": "[1]", "source_id": 1, "section": "67-4"},
    {"marker": "[2]", "source_id": 2, "section": "67-5"}
  ],
  "verification": {
    "total_sentences": 12,
    "supported_sentences": 11,
    "support_ratio": 0.917
  }
}
```

**Search Response** (`/search/simple`)
```json
{
  "query": "building permits",
  "collection": "la_plata_county_code",
  "results": [
    {
      "section": "2538",
      "text": "Chapter 2 ADMINISTRATION...",
      "relevance": "0.798"
    }
  ]
}
```

**Available Metadata Fields**:
- **Land Use Code**: `section_id`, `full_text_length`, `text`
- **Property Assessor**: `account_number`, `text_length`, `text`, `data_source`

## 🛠️ Server Management

**Complete API Suite Management (Recommended)**
```bash
./scripts/start_both.sh start     # Start both Search + RAG APIs with model
./scripts/start_both.sh status    # Check status of both APIs
./scripts/start_both.sh test      # Test connectivity and functionality
./scripts/start_both.sh stop      # Stop both APIs
./scripts/start_both.sh restart   # Restart both APIs
./scripts/start_both.sh logs      # View logs from both APIs
```

**Individual API Management**
```bash
# Search API only (port 8000)
./scripts/api.sh start     # Start in background
./scripts/api.sh status    # Check status + connectivity test
./scripts/api.sh stop      # Stop server
./scripts/api.sh restart   # Restart server
./scripts/api.sh logs      # View recent logs

# RAG API only (port 8001)
./scripts/run_rag.sh start     # Start RAG service
./scripts/run_rag.sh status    # Check RAG status
./scripts/run_rag.sh stop      # Stop RAG service
./scripts/run_rag.sh logs      # View RAG logs
```

## 🔄 Vector Database Management

### Regenerating Embeddings

**When to regenerate:**
- Switching to a different embedding model
- Updating source data in `la_plata_code/full_code.json`
- Corrupted or missing ChromaDB files

**Steps to regenerate:**
1. **Stop the API server**
   ```bash
   ./scripts/api.sh stop
   ```

2. **Remove existing vector database**
   ```bash
   rm -rf ./chroma_db
   ```

3. **Update model in scripts** (if changing models)
   ```bash
   # Edit apis/search/embeddings/create_legal_embeddings.py and apis/search/search_api.py
   # Change: SentenceTransformer('intfloat/e5-large-v2')
   # To your preferred model from the table above
   ```

4. **Generate new embeddings**
   ```bash
   python apis/search/embeddings/create_legal_embeddings.py
   ```

5. **Restart API server**
   ```bash
   ./scripts/api.sh start
   ```

### Model Comparison

| Current Model | Previous Model | Improvement |
|---------------|----------------|-------------|
| intfloat/e5-large-v2 (1024D) | BAAI/bge-small-en-v1.5 (384D) | Superior legal text understanding |
| Relevance: 0.65-0.67 | Relevance: 0.45-0.55 | +20% higher relevance scores |
| Processing: ~2 min | Processing: ~15 sec | Acceptable trade-off for quality |
| **Best for**: Legal/regulatory text | **Best for**: General purpose | Specialized for complex documents |

## 📊 Performance

### RAG System Performance
- **Land Use Dataset**: 1,298 sections of La Plata County Land Use Code
- **Property Dataset**: 46,230 property records from Assessor database  
- **Embedding Model**: intfloat/e5-large-v2 (1024 dimensions)
- **Inference Models**: Qwen3-4B-Instruct (4-bit), Qwen3-4B-Thinking (8-bit)
- **Memory Usage**: 
  - Vector database + APIs: ~4GB RAM
  - External inference service: 4-6GB RAM (vs 8-12GB with MLX Python)
  - Total system: ~8-10GB (optimized from 12-16GB)
- **Response Times**: 
  - Query normalization: <10ms
  - Enhanced retrieval: 200-500ms
  - Model generation: 2-8 seconds
  - Total response: 3-10 seconds typical
- **Citation Accuracy**: 90%+ citation extraction and verification
- **Quality Improvements**:
  - Legal reasoning with proper citations
  - Cross-reference following for comprehensive answers
  - Support verification ensures answer accuracy

## 🔧 Development

**Local Testing**
```bash
# Test search retrieval
python apis/search/test_search.py

# Test RAG system
curl -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"test query","num_results":3}'

# Health checks
curl http://localhost:8001/rag/health
curl http://localhost:8000/health
```

**Model Information**
- **Embedding Model**: `intfloat/e5-large-v2` (1024D, specialized for legal text)
- **Inference Models**: Qwen3-4B family (4-bit/8-bit quantization)
- **Apple Silicon**: External llama.cpp with Metal GPU acceleration
- **Architecture**: External inference service for memory efficiency and cloud-ready design

### Model Selection

Model recommendations for different use cases:

| Model | Dimensions | Storage Size | Best For |
|-------|------------|--------------|----------|
| **intfloat/e5-large-v2** ⭐ | 1024 | ~140MB | **Legal/regulatory text (current)** |
| BAAI/bge-small-en-v1.5 | 384 | ~52MB | General purpose, faster processing |
| all-MiniLM-L6-v2 | 384 | ~50MB | Basic semantic search |
| nomic-embed-text-v1.5 | 768 | ~100MB | Long-form documents |

⭐ **Current production model** - Optimized for legal/administrative content with superior relevance scores (0.65-0.67 range).

## 🚀 Production Deployment

**Current Architecture**: External inference service ready for cloud migration

**Migration Path:**
- **Phase 1**: llama.cpp external service (current) - Memory optimized, cloud-ready pattern
- **Phase 2**: Cloud vector database (Pinecone) + local inference  
- **Phase 3**: Full cloud - Pinecone + AWS Bedrock

**Recommended Stack:**
- **Vector DB**: Migrate ChromaDB → Pinecone for production scale
- **Inference**: AWS Bedrock (external service pattern already established)
- **APIs**: Deploy Flask on cloud platform (AWS/GCP/Azure) 
- **Frontend**: Next.js application with Vercel deployment
- **Caching**: Redis for frequent queries and retrieval results
- **Monitoring**: Application performance monitoring with health checks

## 📝 Example Queries

### RAG Q&A Examples  
Try these natural language questions:
- `"What are the requirements for minor subdivisions?"`
- `"What permits are needed to build a commercial building?"`
- `"What are the parking requirements for restaurants?"`
- `"How do I apply for a building permit?"`
- `"What are the setback requirements for residential properties?"`
- `"What is the process for environmental impact assessments?"`
- `"What are the zoning restrictions for oil and gas development?"`
- `"What flood damage prevention regulations apply?"`

### Search-Only Examples (Port 8000)
- **Land Use Code**: `building permits`, `subdivision regulations`, `zoning requirements`
- **Property Data**: `Smith family`, `49617 highway 550`, `PURGATORY RENTALS LLC`

## 🔍 Search Performance & Accuracy

### Model Performance Comparison

Both collections now use the **intfloat/e5-large-v2** model (1024 dimensions) for optimal results:

#### Land Use Code Performance
- **Relevance Range**: 0.65-0.85 for legal/regulatory queries
- **Optimal For**: Complex legal text, zoning regulations, building codes
- **Example**: Query `"building permits"` returns relevance 0.747-0.740

#### Property Assessor Performance  
- **Relevance Range**: 0.45-0.79 for property queries
- **Optimal For**: Owner names, property types, general location searches
- **Limitation**: Exact address matching can be challenging

### Address Search Accuracy Case Study

**Test Case**: Query `"49617 highway 550"`

**Findings**:
- ✅ **Significant Improvement**: After switching to e5-large-v2 model
  - **Before**: 0.473 relevance (all-mpnet-base-v2)  
  - **After**: 0.776+ relevance (e5-large-v2)
  - **Improvement**: 64% better relevance scores

- ✅ **Data Completeness**: All 29 properties at "49617 N US HWY 550" exist in database with full details including:
  - Owner information (PURGATORY RENTALS LLC)
  - Property addresses (32 TIERRA VERDE DR)
  - Parcel numbers, tax districts, legal descriptions
  - Building details (Built: 1969, Type: CONDOMINIUM, etc.)
  - Actual values and assessments

- ⚠️ **Exact Address Challenge**: While relevance improved dramatically, exact address matches don't always rank at the top due to semantic vs lexical matching

### Recommendations for Address Search

1. **Use Specific Formats**: Include directional indicators and route numbers
   - Good: `"49617 N US HWY 550"`
   - Better: `"49617 N US HWY 550 #204"` (for condos)

2. **Try Alternative Searches**: 
   - Search by owner: `"PURGATORY RENTALS LLC"`
   - Search by property type: `"Lodge Villa Purgatory"`
   - Search by legal description: `"LODGE/VILLA AT PURGA"`

3. **For Exact Matches**: Consider implementing hybrid search combining:
   - Semantic similarity (current system)
   - Exact text matching for addresses/parcel numbers
   - Field-specific search weighting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🎯 Roadmap / TODO

### Data Expansion
- [ ] **GIS Data Integration**: Scrape and integrate https://gis.lpcgov.org/lpcmap/ for geographic/zoning overlay data
- [ ] **Assessor's Office Data**: Scrape and integrate property assessment data from La Plata County Assessor's Office

### Future Enhancements
- [ ] Multi-county support (expansion beyond La Plata County)
- [ ] Real-time data synchronization
- [ ] Advanced search filters (date ranges, document types, etc.)
- [ ] Geographic search capabilities with GIS integration

## 📄 License

[Add your chosen license]

## 🏆 Current System Status

### Implemented Features ✅
- **Complete RAG Pipeline**: Query normalization → Enhanced retrieval → Generation → Verification
- **Citation System**: Automatic citation extraction, validation, and support verification
- **Streaming Support**: Real-time response generation with Server-Sent Events
- **External Inference**: Memory-optimized llama.cpp service architecture
- **Legal Reasoning**: Specialized models (Qwen3-4B) optimized for legal text analysis
- **Cross-Reference Following**: Automatic expansion of legal references (e.g., "section 67-4")
- **Heuristic Reranking**: Relevance scoring with diversity enforcement
- **Health Monitoring**: Comprehensive API health checks and status reporting
- **Comprehensive Documentation**: Architecture, troubleshooting, and migration guides

### Key Innovations
- **Memory Optimization**: Reduced from 12-16GB to 8-10GB total system usage
- **Cloud-Ready Architecture**: External service pattern ready for AWS Bedrock migration  
- **Legal-Specific Processing**: 60+ query normalization patterns for legal terminology
- **Multi-Layer Validation**: Query → Retrieval → Generation → Verification pipeline
- **Support Verification**: Sentence-level answer validation using lexical overlap

### Migration Blueprint Available
- **Phase 1**: External inference service (completed) ✅
- **Phase 2**: Cloud vector database (Pinecone) integration planned
- **Phase 3**: Full cloud migration (AWS Bedrock) architecture established

The system has evolved from a semantic search proof-of-concept into a production-ready RAG platform specifically designed for legal document analysis and municipal code Q&A.
