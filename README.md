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

3. **Start API Server**
   ```bash
   ./scripts/api.sh start
   ```

4. **Test Both Collections**
   ```bash
   # Land Use Code
   curl "http://localhost:8000/search/simple?query=building%20permits&collection=la_plata_county_code&num_results=5"
   
   # Property Assessor Data
   curl "http://localhost:8000/search/simple?query=Smith%20family&collection=la_plata_assessor&num_results=5"
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
│ • 46,230 properties  │    │ • all-mpnet-base-v2 │    │   Selection      │
│ • Ownership & Values │    │ • 768 dimensions    │    │ • Dual Models    │
└──────────────────────┘    └─────────────────────┘    └──────────────────┘
```

### Technology Stack

**Core Components:**
- **Dual Embedding Models**: 
  - `intfloat/e5-large-v2` (1024D) for legal/regulatory text
  - `all-mpnet-base-v2` (768D) for property/structured data
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
├── la_plata_code/                    # Land Use Code source data
├── LPC-Assessor-Data-Files/          # Property Assessor source data (MDB)
├── chroma_db/                        # Multi-collection vector database
├── scripts/                          # Management scripts
│   └── api.sh                       # API server management
├── create_embeddings.py             # Land Use Code embeddings (1024D)
├── create_assessor_embeddings.py    # Property Assessor embeddings (768D)
├── search_api.py                    # Multi-collection Flask API
├── components/                       # Next.js UI components
│   ├── search-form.tsx              # Collection-aware search form
│   └── search-results.tsx           # Unified results display
├── app/                             # Next.js application
│   ├── search/page.tsx             # Search interface
│   └── page.tsx                    # Landing page
└── BUILD_STEPS.md                   # Detailed setup guide
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

### Response Format
```json
{
  "query": "building permits",
  "results": [
    {
      "section": "2538",
      "text": "Chapter 2 ADMINISTRATION...",
      "relevance": "0.798"
    }
  ]
}
```

## 🛠️ Server Management

**Start/Stop API Server**
```bash
./scripts/api.sh start     # Start in background
./scripts/api.sh status    # Check status + connectivity test
./scripts/api.sh stop      # Stop server
./scripts/api.sh restart   # Restart server
./scripts/api.sh logs      # View recent logs
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

- **Dataset**: 1,298 sections of La Plata County Land Use Code
- **Model**: intfloat/e5-large-v2 (1024 dimensions)
- **Embedding Generation**: ~2 minutes on M4 Pro (Apple Silicon optimized)
- **Memory Usage**: ~8GB RAM during processing, ~3GB during API serving
- **Search Speed**: Sub-second query response times
- **Storage**: ~140MB ChromaDB + embeddings
- **Quality**: 20% higher relevance scores, superior legal text comprehension

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

Try these semantic searches:
- `building permits and zoning requirements`
- `subdivision regulations and approval process`
- `environmental impact assessments`
- `parking requirements for commercial properties`
- `flood damage prevention regulations`
- `oil and gas development restrictions`

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
