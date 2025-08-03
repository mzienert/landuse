# La Plata County Land Use Code - Semantic Search API

A semantic search system for the La Plata County Land Use Code, enabling natural language queries over county regulations. Built with sentence transformers, ChromaDB, and Flask API.

## 🚀 Quick Start

**Prerequisites:** Apple Silicon Mac, Python 3.10+, Virtual environment activated

1. **Setup Environment**
   ```bash
   source env/bin/activate
   pip install sentence-transformers chromadb flask flask-cors
   ```

2. **Create Vector Embeddings** (First time only)
   ```bash
   python create_embeddings.py
   ```

3. **Start API Server**
   ```bash
   ./scripts/api.sh start
   ```

4. **Test the API**
   ```bash
   curl "http://localhost:8000/search/simple?query=building%20permits&num_results=10"
   ```

📖 **Detailed setup instructions:** See [BUILD_STEPS.md](BUILD_STEPS.md)

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Source Data    │ →  │ Vector Embeddings │ →  │   Search API    │
│ (JSON files)    │    │   (ChromaDB)      │    │   (Flask)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
    ┌─────────┐              ┌──────────┐           ┌─────────────┐
    │ 1,298   │              │ all-Mini │           │ REST API    │
    │sections │              │ LM-L6-v2 │           │ + CORS      │
    └─────────┘              └──────────┘           └─────────────┘
```

### Technology Stack

**Core Components:**
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions, optimized for Apple Silicon)
- **Vector Database**: ChromaDB (local development) / Pinecone (production)
- **API Framework**: Flask with CORS support
- **Language**: Python 3.10+

**Data Pipeline:**
1. **Source**: La Plata County Land Use Code (`la_plata_code/full_code.json`)
2. **Processing**: Text chunking, embedding generation, vector storage
3. **Search**: Semantic similarity search with configurable result counts
4. **API**: RESTful endpoints with JSON responses

### Project Structure
```
landuse/
├── la_plata_code/           # Source data (JSON, TXT files)
├── chroma_db/               # Vector database storage
├── scripts/                 # Management scripts
│   └── api.sh              # API server management
├── create_embeddings.py     # Embedding generation script
├── search_api.py           # Flask API server
├── test_search.py          # Local testing utilities
└── BUILD_STEPS.md          # Detailed setup guide
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

## 📊 Performance

- **Dataset**: 1,298 sections of La Plata County Land Use Code
- **Embedding Generation**: ~2-3 minutes on M4 Pro (Apple Silicon optimized)
- **Memory Usage**: ~8GB RAM during processing, ~2GB during API serving
- **Search Speed**: Sub-second query response times
- **Storage**: ~50MB ChromaDB + embeddings

## 🔧 Development

**Local Testing**
```bash
python test_search.py              # Console-based search test
curl "http://localhost:8000/..."   # API endpoint testing
```

**Model Information**
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384 (optimized for legal/administrative text)
- **Apple Silicon**: Leverages MPS (Metal Performance Shaders)
- **Quantization**: Automatic optimization for Apple Neural Engine

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

## 📄 License

[Add your chosen license]
