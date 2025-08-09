# La Plata County Semantic Search System

A comprehensive semantic search platform for La Plata County data, enabling natural language queries across Land Use Code regulations and Property Assessor records. Built with dual-model architecture, ChromaDB, and Flask API.

## 🚀 Quick Start

**Prerequisites:** Apple Silicon Mac, Python 3.10+, Virtual environment activated

1. **Setup Environment**
   ```bash
   source env/bin/activate
   pip install sentence-transformers chromadb flask flask-cors mdbtools
   ```

2. **Create Vector Embeddings**
   
   **Land Use Code (1,298 sections):**
   ```bash
   python create_embeddings.py
   ```
   
   **Property Assessor Data (46,230 properties):**
   ```bash
   python create_assessor_embeddings.py
   ```
   
   **Note**: Both processes use optimized models and take 2-6 minutes each.

3. **Start Complete API Suite (Search + RAG)**
   ```bash
   ./scripts/start_both.sh start
   ```
   
   This automatically starts:
   - Search API (port 8000) for semantic search
   - RAG API (port 8001) for Q&A with citations
   - Loads the RAG model ready for questions

4. **Test Search and RAG**
   ```bash
   # Test Search API
   curl "http://localhost:8000/search/simple?query=building%20permits&collection=la_plata_county_code&num_results=5"
   
   # Test RAG API with Q&A
   curl -X POST http://localhost:8001/rag/answer \
     -H 'Content-Type: application/json' \
     -d '{"query":"What are subdivision requirements?","collection":"la_plata_county_code","num_results":5}'
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
┌──────────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│    Dual Data Sources │ →  │  Vector Embeddings  │ →  │   Search API     │
│                      │    │     (ChromaDB)      │    │    (Flask)       │
├──────────────────────┤    ├─────────────────────┤    └──────────────────┘
│ Land Use Code        │    │ la_plata_county_code│              │
│ • 1,298 sections     │    │ • e5-large-v2       │    ┌──────────────────┐
│ • Regulations        │    │ • 1024 dimensions   │    │ Multi-Collection │
├──────────────────────┤    ├─────────────────────┤    │ REST API + CORS  │
│ Property Assessor    │    │ la_plata_assessor   │    │ • Collection     │
│ • 46,230 properties  │    │ • e5-large-v2       │    │   Selection      │
│ • Ownership & Values │    │ • 1024 dimensions   │    │ • Unified Model  │
└──────────────────────┘    └─────────────────────┘    └──────────────────┘
```

### Technology Stack

**Core Components:**
- **Unified Embedding Model**: 
  - `intfloat/e5-large-v2` (1024D) for both collections
  - Superior performance for legal text AND structured data
  - 64% improvement in property search relevance over previous model
- **Vector Database**: ChromaDB with multi-collection support
- **API Framework**: Flask with CORS and collection routing
- **Data Processing**: MDB extraction tools + custom property description generation
- **Language**: Python 3.10+

**Data Pipeline:**
1. **Sources**: 
   - Land Use Code JSON (`la_plata_code/full_code.json`)
   - Property Assessor MDB (`LPC-Assessor-Data-Files/AssessorData.mdb`)
2. **Processing**: 
   - Text chunking and cleaning
   - Model-specific embedding generation
   - Multi-collection vector storage
3. **Search**: Collection-aware semantic similarity search
4. **API**: RESTful endpoints with collection selection

### Project Structure
```
landuse/
├── apis/                            # API services
│   ├── search/                      # Search API
│   │   ├── search_api.py           # Multi-collection Flask API
│   │   └── test_search.py          # Search API testing
│   └── rag/                        # RAG API
│       ├── rag_api.py             # Q&A with citations Flask API
│       ├── inference.py           # MLX model management
│       ├── retrieval.py           # Retrieval orchestration
│       └── verify.py              # Citation verification
├── scripts/                         # Management scripts
│   ├── api.sh                      # Search API management
│   ├── run_rag.sh                  # RAG API management
│   └── start_both.sh               # Combined API management
├── data/                           # Source data
│   ├── la_plata_code/             # Land Use Code source data
│   └── LPC-Assessor-Data-Files/   # Property Assessor source data (MDB)
├── chroma_db/                      # Multi-collection vector database
├── create_embeddings.py           # Land Use Code embeddings (1024D)
├── create_assessor_embeddings.py  # Property Assessor embeddings (768D)
├── components/                     # Next.js UI components
│   ├── search-form.tsx            # Collection-aware search form
│   └── search-results.tsx         # Unified results display
├── app/                           # Next.js application
│   ├── search/page.tsx           # Search interface
│   └── page.tsx                  # Landing page
└── BUILD_STEPS.md                 # Detailed setup guide
```

## 🔍 API Usage

### Endpoints

**Health Check**
```bash
curl "http://localhost:8000/health"
```

**Simple Search** (Recommended for testing)
```bash
curl "http://localhost:8000/search/simple?query=building%20permits&num_results=10"
```

**Full Search** (Detailed metadata)
```bash
curl "http://localhost:8000/search?query=zoning%20requirements&num_results=5"
```

**POST Search**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "subdivision regulations", "num_results": 3}'
```

### Browser Testing

Open in your browser:
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Search Example**: [http://localhost:8000/search/simple?query=building%20permits&num_results=10](http://localhost:8000/search/simple?query=building%20permits&num_results=10)
- **Zoning Query**: [http://localhost:8000/search/simple?query=zoning%20requirements&num_results=5](http://localhost:8000/search/simple?query=zoning%20requirements&num_results=5)

### Response Formats

**Simple Search Response** (`/search/simple`)
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

**Full Search Response** (`/search`)
```json
{
  "query": "49617 highway 550", 
  "collection": "la_plata_assessor",
  "results": [
    {
      "id": "R017758",
      "account_number": "R017758",
      "distance": 0.224,
      "content": "Property Account: R017758\nOwner: PURGATORY RENTALS LLC\nProperty Address: 32 TIERRA VERDE DR, DURANGO, CO 81301\nParcel Number: 508924313018\nTax District: 1142\nLegal Description: Subdivision: LODGE/VILLA AT PURGA Unit: 19   DESC: LOT 1 AKA UNIT 204 49617 N US HWY 550 #204 DURANGO  81301\nActual Value: $103,150\nBuilding: Built: 1969, Type: CONDOMINIUM, 1 bath, 818 sq ft",
      "text_length": 368,
      "collection": "la_plata_assessor",
      "collection_name": "Property Assessor Data"
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
   # Edit create_embeddings.py and search_api.py
   # Change: SentenceTransformer('intfloat/e5-large-v2')
   # To your preferred model from the table above
   ```

4. **Generate new embeddings**
   ```bash
   python create_embeddings.py
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

### Current Performance Metrics
- **Land Use Dataset**: 1,298 sections of La Plata County Land Use Code
- **Property Dataset**: 46,230 property records from Assessor database  
- **Model**: intfloat/e5-large-v2 (1024 dimensions) - unified across both collections
- **Embedding Generation**: 
  - Land Use Code: ~2 minutes on M4 Pro
  - Property Assessor: ~19 minutes on M4 Pro (46K records)
- **Memory Usage**: ~8GB RAM during processing, ~4GB during API serving
- **Search Speed**: Sub-second query response times for both collections
- **Storage**: ~180MB ChromaDB + embeddings (combined)
- **Quality Improvements**:
  - Land Use Code: 20% better relevance vs BGE-small model
  - Property Assessor: 64% better relevance vs all-mpnet model

## 🔧 Development

**Local Testing**
```bash
python test_search.py              # Console-based search test
curl "http://localhost:8000/..."   # API endpoint testing
```

**Model Information**
- **Model**: `intfloat/e5-large-v2` (current production model)
- **Dimensions**: 1024 (specialized for legal/administrative text)
- **Apple Silicon**: Leverages MPS (Metal Performance Shaders)
- **Performance**: 20% better relevance scores, superior legal context understanding

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

**Recommended Stack:**
- **Vector DB**: Migrate ChromaDB → Pinecone
- **API**: Deploy Flask on cloud platform (AWS/GCP/Azure)
- **Frontend**: Next.js application with Vercel deployment
- **Caching**: Redis for frequent queries
- **Monitoring**: Application performance monitoring

## 📝 Example Queries

### Land Use Code Collection
Try these semantic searches:
- `building permits and zoning requirements`
- `subdivision regulations and approval process`
- `environmental impact assessments`
- `parking requirements for commercial properties`
- `flood damage prevention regulations`
- `oil and gas development restrictions`

### Property Assessor Collection
Try these property searches:
- `Smith family` (search by owner name)
- `49617 highway 550` (search by address)
- `PURGATORY RENTALS LLC` (search by company name)
- `Durango residential property` (search by property type and location)
- `condominium units` (search by building type)

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

## Next Phase: Retrieval-Augmented Generation (RAG)

We will add grounded Q&A on top of the existing semantic search. This section captures goals, architecture, and the planned components. Implementation will be local-first (Apple Silicon) with MLX.

### Goals
- Build RAG that answers questions with citations from our corpora (Land Use Code and Assessor Data)
- Run locally using an LLM optimized for legal text
- Provide streaming answers, inline citation markers, and a sources panel

### Model
- Target: Llama3-LegalLM from Hugging Face
- If unavailable, adapt to a compatible Llama 3 Instruct variant or a legal LoRA fine-tune
- Quantization: 8-bit on M4 Pro 24GB preferred; fall back to 4-bit if needed
- Context window: 8K–16K tokens (we’ll pack contexts accordingly)

### RAG Architecture (proposed)
1) User query → optional rewrite/normalization
2) Retrieval from ChromaDB collections (la_plata_county_code, la_plata_assessor)
3) Heuristic rerank (lightweight) and diversity selection
4) Context packing with per-chunk citations and safety fencing
5) LLM generation (MLX) with streaming tokens
6) Lightweight verification pass (supports-only policy). If insufficient basis, reply accordingly
7) Response: final answer + citations map and source snippets

### Components to Add
- LLM inference (MLX) service
  - Load Llama3-LegalLM (or fallback) with tokenizer, 8-bit quantization when possible
  - Generation controls: temperature, top_p, max_tokens; streaming endpoint
- Retrieval orchestration
  - Multi-collection retrieval with current embeddings
  - Packing policy (1,000–1,500 chars per chunk, ~150 overlap); deduplication; cross-source diversity
  - Citations preserved: section/account IDs and collection names
- Reranking (initial approach)
  - Start with a heuristic rerank that boosts passages with higher short-window similarity to the query, penalizes near-duplicates, and ensures source diversity. This avoids heavy cross-encoders and runs fast locally
  - Later, evaluate a small local reranker; see “Rerankers 101” below
- Prompting
  - System prompt emphasizes legal accuracy, citations, and non-speculation
  - Template: user question + packed contexts with source headers; output requires citations [1], [2], etc.
- Verification (lightweight)
  - For each sentence/claim, ensure at least one retrieved chunk is sufficiently similar (embedding cosine threshold). If not supported, soften or remove the claim
- API layer
  - Keep `search_api.py` separate (retrieval service)
  - Add a separate `rag_api.py` for generation endpoints: `/rag/answer` and `/rag/answer/stream` (SSE)
- UI (next phase after API)
  - Chat interface with streaming, adjustable parameters, and source panel
- Sessioning and feedback (optional after MVP)
  - Store conversations, used sources, and thumbs up/down for evaluation
- Caching
  - Retrieval cache keyed by normalized query + corpus version; generation cache keyed by prompt+sources hash

### API Topology Decision
- Separation of concerns: retain `search_api.py` for search-only; implement RAG in a distinct `rag_api.py` service

### Rerankers 101 (What/Why/How)
- What: A reranker reorders retrieved passages to put the most useful at the top before sending to the LLM
- Why: First-stage vector retrieval is recall-oriented; reranking improves precision and reduces wasted context window
- Spectrum:
  - Heuristic: cosine-sim boosts, redundancy penalties, source diversity—cheap and fast
  - Cross-encoder: small transformer that takes (query, passage) together and scores relevance—higher quality but slower
- Our plan: Start with a heuristic reranker to keep latency low and work fully offline; re-evaluate cross-encoders later

### Evaluation (planned)
- Gold questions with expected sources; metrics for hit@k, citation precision, supported-claims ratio, latency
- Simple CLI harness to run batch evals

### Safety & Compliance (planned)
- Explicit disclaimer: not legal advice
- Require citations for all claims; block unsupported conclusions
- Prompt-injection mitigation: fence context and ignore instructions from documents
