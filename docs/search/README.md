# Search API Documentation Index

This directory contains comprehensive documentation for the La Plata County Search API - a semantic search service for legal documents and property records.

## 📚 Documentation Structure

### Core Documentation
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture, components, and technical design
- **[SETUP.md](./SETUP.md)** - Installation, configuration, and initial setup
- **[USAGE.md](./USAGE.md)** - API reference, endpoints, and integration examples  
- **[EMBEDDINGS.md](./EMBEDDINGS.md)** - Vector embeddings creation and data management
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Problem diagnosis and resolution

### System Overview
The Search API provides semantic search across:
- **Legal Code Collection**: 1,298+ La Plata County municipal code sections
- **Property Assessment Collection**: 46,230+ property records with ownership data

### Recent Updates
- **Application Factory Pattern**: Environment-based configuration (development/testing/production)
- **Enhanced Testing**: In-memory ChromaDB for isolated test instances
- **Environment Variables**: Full configuration via environment variables
- **Production Logging**: Automatic file logging in production mode

## 🎯 Documentation Usage

### By Role
- **New Users**: Start with SETUP.md → USAGE.md → TROUBLESHOOTING.md
- **Developers**: Begin with ARCHITECTURE.md → USAGE.md → EMBEDDINGS.md  
- **System Admins**: Focus on SETUP.md → TROUBLESHOOTING.md → EMBEDDINGS.md
- **Data Scientists**: Review EMBEDDINGS.md → ARCHITECTURE.md → USAGE.md

### By Task
- **Installation**: SETUP.md
- **API Integration**: USAGE.md
- **Data Management**: EMBEDDINGS.md
- **Performance Issues**: TROUBLESHOOTING.md
- **System Understanding**: ARCHITECTURE.md

## 🚀 Quick Start

### Basic Setup
```bash
# Start search API
./scripts/api.sh start

# Check health  
curl http://localhost:8000/health

# Test search
curl "http://localhost:8000/search/simple?query=building%20permits&num_results=3"
```

### Key Endpoints
- **Health**: `GET /health` - System status and statistics
- **Collections**: `GET /collections` - Available data collections
- **Simple Search**: `GET /search/simple` - Streamlined search (used by RAG API)
- **Full Search**: `GET/POST /search` - Complete search with metadata

## 📊 System Capabilities

### Technical Specifications
- **Embedding Model**: intfloat/e5-large-v2 (1024 dimensions)
- **Vector Database**: ChromaDB with HNSW indexing
- **Response Time**: 100-200ms typical queries
- **Capacity**: 50K+ documents, 20+ concurrent users
- **Collections**: Legal code (1,298 docs) + Property assessments (46,230 docs)

### Search Quality
- **Semantic Understanding**: Natural language queries work well
- **Legal Domain**: Optimized for municipal code and regulations
- **Property Search**: Owner names, addresses, property characteristics
- **Relevance Scoring**: Cosine similarity with 0.0-1.0 relevance scores

## 🔧 Integration Points

### RAG API Integration
The Search API serves as the retrieval backend for the RAG system:
```python
# RAG API calls Search API
response = requests.get("http://localhost:8000/search/simple", params={
    "query": user_query,
    "collection": "la_plata_county_code", 
    "num_results": 6
})
```

### Frontend Integration
Direct API calls for search interfaces:
```javascript
const results = await fetch(`/api/search/simple?query=${query}&num_results=10`);
const data = await results.json();
```

### Standalone Usage
Command-line testing and automation:
```bash
# Legal searches
curl "http://localhost:8000/search/simple?query=subdivision%20requirements&collection=la_plata_county_code"

# Property searches  
curl "http://localhost:8000/search/simple?query=Smith%20property&collection=la_plata_assessor"
```

## 🗂️ Data Collections

### Legal Code (`la_plata_county_code`)
- **Content**: Municipal code sections, zoning regulations, building requirements
- **Structure**: Section-based chunking (e.g., "67-4", "18-35")  
- **Use Cases**: Building permits, zoning research, subdivision regulations
- **Quality**: Complete legal text with section references preserved

### Property Assessment (`la_plata_assessor`)
- **Content**: Property records, ownership data, assessment information
- **Structure**: Account-based records with combined descriptions
- **Use Cases**: Property lookup, ownership research, assessment analysis
- **Quality**: Rich text combining multiple database fields

## 📈 Performance Characteristics

### Response Times
- **Simple Queries**: 50-100ms (e.g., "building")
- **Complex Queries**: 100-200ms (e.g., "residential building permit requirements")
- **Cold Start**: 200-500ms (first query after restart)
- **Large Result Sets**: +50ms per 10 additional results

### Resource Usage
- **Memory**: 3-4GB (model + indices + overhead)
- **CPU**: Moderate during search, high during embedding creation
- **Storage**: 250MB vector database + 1.3GB model weights
- **Network**: Minimal (local processing)

## 🛡️ Security and Privacy

### Data Handling
- **Local Processing**: All data remains on local infrastructure
- **No External Calls**: No third-party APIs for sensitive legal data
- **Query Logging**: Local logs only, configurable retention
- **Access Control**: IP-based restrictions configurable

### Privacy Considerations
- **Government Data**: Suitable for municipal/legal document handling
- **No User Tracking**: No persistent user identification  
- **Audit Trail**: All queries logged for debugging (optional)
- **Data Retention**: No permanent storage of user queries

## 🔍 Common Use Cases

### Legal Research
```bash
# Find building permit requirements
curl "http://localhost:8000/search/simple?query=building%20permit%20residential%20requirements"

# Research subdivision regulations  
curl "http://localhost:8000/search/simple?query=minor%20subdivision%20three%20lots"

# Zoning information
curl "http://localhost:8000/search/simple?query=commercial%20zoning%20setback%20requirements"
```

### Property Research
```bash
# Find properties by owner
curl "http://localhost:8000/search/simple?query=Johnson%20family%20ranch&collection=la_plata_assessor"

# Search by location
curl "http://localhost:8000/search/simple?query=Main%20Street%20downtown&collection=la_plata_assessor"

# Find by property characteristics
curl "http://localhost:8000/search/simple?query=agricultural%20land%20irrigation&collection=la_plata_assessor"
```

### API Development
```python
import requests

class SearchClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def search(self, query, collection="la_plata_county_code", num_results=5):
        response = requests.get(f"{self.base_url}/search/simple", params={
            "query": query,
            "collection": collection,
            "num_results": num_results
        })
        return response.json()["results"]
    
    def health_check(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Usage
client = SearchClient()
results = client.search("building permits", num_results=5)
```

## 🔄 Maintenance

### Regular Tasks
- **Health Monitoring**: Automated health checks via cron
- **Log Rotation**: Prevent log file growth
- **Performance Monitoring**: Track response times and resource usage
- **Data Updates**: Refresh embeddings when source data changes

### Troubleshooting
- **Service Issues**: Check logs, restart service, verify dependencies
- **Search Quality**: Test with known queries, check embedding quality
- **Performance**: Monitor memory/CPU usage, optimize queries
- **Data Problems**: Regenerate embeddings, verify source data integrity

## 📞 Support and Development

### Getting Help
- **Documentation**: Use the appropriate guide for your needs
- **Troubleshooting**: Follow systematic debugging workflow
- **Health Checks**: Run automated diagnostics first
- **Logs**: Check service logs for detailed error information

### Contributing
- **Bug Reports**: Include system status, logs, reproduction steps
- **Performance Issues**: Provide timing data and system specifications
- **Feature Requests**: Consider integration with existing architecture
- **Documentation**: Improvements always welcome

### Development Status
- **Current Version**: 2.0 (Production Ready)
- **Recent Updates**: Application factory pattern implementation for better testability
- **Stability**: High reliability with automated error recovery
- **Performance**: Optimized for local deployment
- **Scalability**: Cloud migration strategies documented

### Application Factory Pattern Benefits
The Search API now uses Flask's application factory pattern, providing:
- **Environment-based Configuration**: Separate settings for development, testing, and production
- **Enhanced Testability**: Easy creation of test instances with in-memory ChromaDB
- **Better Deployment**: Environment variable driven configuration for production
- **Maintainable Growth**: Structured foundation for adding middleware, logging, and security features

**Factory Usage Examples**:
```python
# Development instance (file-based ChromaDB)
dev_app = create_app('development')

# Testing instance (in-memory ChromaDB)
test_app = create_app('testing')

# Production instance (with logging)
prod_app = create_app('production')

# Environment-driven (uses FLASK_ENV)
app = create_app()  # Respects environment variables
```

This comprehensive documentation system provides everything needed to understand, deploy, use, and maintain the La Plata County Search API for semantic search across legal and property data.