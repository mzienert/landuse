# RAG System Architecture

## Overview

The La Plata County RAG (Retrieval-Augmented Generation) system is a sophisticated multi-component architecture designed to provide accurate, cited answers to legal and municipal questions using local documents.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Application                        │
│                   (Next.js Frontend)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP Requests
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway                               │
│                  (Port 8001)                               │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 RAG API Layer                           │ │
│  │              (rag_api.py)                               │ │
│  │                                                         │ │
│  │  • /rag/answer (non-streaming)                          │ │
│  │  • /rag/answer/stream (Server-Sent Events)              │ │
│  │  • /rag/model/load                                      │ │
│  │  • /rag/health                                          │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Core RAG Pipeline                            │
│                                                             │
│  ┌───────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │     Query     │    │   Enhanced      │    │   Answer    │ │
│  │ Normalization │───▶│   Retrieval     │───▶│ Generation  │ │
│  │ (normalize.py)│    │ (retrieval.py)  │    │(inference.py)│ │
│  └───────────────┘    └─────────────────┘    └─────────────┘ │
│                                │                             │
│                                ▼                             │
│                      ┌─────────────────┐                     │
│                      │   Verification  │                     │
│                      │   (verify.py)   │                     │
│                      └─────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                 External Services                           │
│                                                             │
│  ┌─────────────────────────┐    ┌─────────────────────────┐ │
│  │    Search API           │    │  External Inference     │ │
│  │   (Port 8000)           │    │  Service (Port 8003)    │ │
│  │                         │    │                         │ │
│  │  • ChromaDB Vector      │    │  • llama.cpp Server     │ │
│  │    Store                │    │  • GGUF Models          │ │
│  │  • Embeddings           │    │  • Native Performance   │ │
│  │  • Semantic Search      │    │  • GPU Acceleration     │ │
│  └─────────────────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. RAG API Layer (`rag_api.py`)
- **Role**: Main Flask application providing HTTP endpoints
- **Responsibilities**:
  - Request handling and validation
  - Model lifecycle management (auto-loading on startup)
  - Streaming and non-streaming response coordination
  - Error handling and status reporting

**Key Features**:
- Auto-loads default model (`Qwen3-4B-Thinking-2507-8bit`) on startup
- Supports both streaming (SSE) and non-streaming responses
- Integrated health checks with model status
- Configurable generation parameters (temperature, tokens, etc.)

### 2. Query Normalization (`normalize.py`)
- **Role**: Transform user queries for optimal retrieval
- **Responsibilities**:
  - Legal-specific query pattern matching
  - Verbose question simplification
  - Query variation generation for fallback

**Key Features**:
- 60+ legal transformation patterns
- Handles complex questions like "What are the requirements for..." → "requirements"
- Fallback strategies with multiple query variations
- Transparent logging of normalization decisions

### 3. Enhanced Retrieval (`retrieval.py`)
- **Role**: Sophisticated document retrieval with cross-reference following
- **Responsibilities**:
  - Integration with Search API (port 8000)
  - Legal reference extraction and expansion
  - Reranking and deduplication
  - Context-aware prompt building

**Key Features**:
- **Reference Expansion**: Automatically follows legal cross-references (e.g., "section 67-4")
- **Heuristic Reranking**: Lexical overlap scoring with diversity enforcement
- **Source Management**: Preserves full text for UI while truncating for LLM context
- **Citation Support**: Numbered source tracking for answer citations

### 4. Model Inference (`inference.py` / External Service)
- **Role**: Text generation via external inference service
- **Responsibilities**:
  - HTTP client for external inference API
  - Request/response handling and error management
  - Streaming text generation coordination
  - Service health monitoring

**Key Features**:
- External service integration (llama.cpp server)
- HTTP-based inference with timeout handling
- Supports both streaming and batch generation
- Service discovery and health checking

### 5. Answer Verification (`verify.py`)
- **Role**: Post-generation answer validation and citation support
- **Responsibilities**:
  - Sentence-level support checking using lexical overlap
  - Citation extraction and validation
  - Answer annotation with support flags
  - Auto-citation generation when missing

**Key Features**:
- Jaccard similarity-based support verification
- Per-sentence annotation with support levels
- Automatic citation insertion for supported claims
- Verification reporting with detailed metrics

## Data Flow

### Standard Query Flow
1. **Input**: User submits query via `/rag/answer` or `/rag/answer/stream`
2. **Normalization**: Query processed through legal-specific patterns
3. **Retrieval**: Enhanced search with reference expansion
   - Initial vector search via Search API
   - Extract legal references from results
   - Follow cross-references for additional context
   - Rerank and deduplicate results
4. **Generation**: External inference service generates answer with source citations
5. **Verification**: Post-process answer for citation support
6. **Output**: Structured response with answer, citations, sources, and verification

### Enhanced Retrieval Process
```
User Query: "What are the requirements for minor subdivisions?"
    ↓
Normalization: "minor subdivision requirements"
    ↓ 
Variations: ["minor subdivision requirements", "section 67-4", "subdivision three lots or fewer"]
    ↓
Initial Search: Retrieve top-K results for each variation
    ↓
Reference Extraction: Find patterns like "section 67-4", "Chapter 66"
    ↓
Follow References: Search for extracted references
    ↓
Combine & Rerank: Merge results, apply heuristic scoring, remove duplicates
    ↓
Context Building: Create numbered SOURCES list for LLM prompt
```

## Storage Architecture

### Vector Database (ChromaDB)
- **Collections**: 
  - `la_plata_county_code`: Legal municipal code sections
  - `la_plata_assessor`: Property assessment data
- **Embeddings**: Sentence transformers model for semantic search
- **Indexing**: Optimized for legal text retrieval patterns

### Document Processing
- **Legal Code**: Scraped from official La Plata County website
- **Chunking Strategy**: Section-based segmentation preserving legal structure
- **Metadata**: Section numbers, chapter references, document hierarchy

## Inference Architecture

### External Inference Service (llama.cpp)
- **Service**: Standalone HTTP server on port 8003
- **Protocol**: HTTP REST API with streaming support
- **Model Format**: GGUF format for optimal performance
- **GPU Acceleration**: Native Metal support for Apple Silicon

### Supported Models
- **Primary**: Qwen3-4B-Instruct-2507-Q4_K_M.gguf (4-bit quantization)
- **Alternative**: Qwen3-4B-Thinking-2507-Q4_K_M.gguf (thinking model)
- **Fallback**: Llama-3.1-8B-Instruct-Q4_K_M.gguf (larger context)
- **Memory Efficient**: Any 4-bit quantized GGUF model

### Service Management
- **Lifecycle**: Independent service startup/shutdown
- **Model Loading**: Runtime model switching via service restart
- **Health Monitoring**: HTTP health checks and service status
- **Resource Isolation**: Separate process for better memory management

## Quality Assurance

### Multi-Layer Validation
1. **Query Validation**: Input sanitization and parameter validation
2. **Retrieval Quality**: Relevance scoring and diversity enforcement  
3. **Generation Quality**: Legal-specific prompting and citation requirements
4. **Post-Generation**: Answer verification and support checking

### Citation System
- **Extraction**: Automatic detection of `[1]`, `[2]` citation markers
- **Validation**: Ensure citations reference actual provided sources
- **Auto-Generation**: Fallback citation insertion when model omits them
- **Source Tracking**: Maintain bidirectional mapping between citations and sources

### Performance Monitoring
- **Response Times**: API endpoint latency tracking
- **Model Health**: Memory usage, inference speed, error rates
- **Quality Metrics**: Citation accuracy, answer support levels
- **Retrieval Effectiveness**: Hit rates, diversity scores

## Deployment Architecture

### Current State (Local Development)
- **RAG API**: Flask dev server, port 8001
- **Search API**: Flask dev server, port 8000  
- **Inference Service**: llama.cpp server, port 8003
- **Vector DB**: Local ChromaDB instance

### Migration Path to Cloud
- **Phase 1**: External inference service (llama.cpp) - **CURRENT APPROACH**
- **Phase 2**: Cloud search (Pinecone) + local inference (llama.cpp)
- **Phase 3**: Full cloud - Pinecone + AWS Bedrock
- **Benefits**: Memory efficiency, independent scaling, cloud-ready architecture

## Integration Points

### Search API Dependency
- **Protocol**: HTTP REST at `localhost:8000`
- **Endpoints**: `/search/simple` for vector similarity search
- **Data Format**: JSON with results, metadata, and relevance scores
- **Decoupling**: Clean API boundary enables independent scaling

### Inference Service Dependency
- **Protocol**: HTTP REST at `localhost:8003`
- **Endpoints**: `/completion` for text generation, `/health` for status
- **Data Format**: JSON with prompt, streaming options, and generation parameters
- **Decoupling**: External service enables memory optimization and cloud migration

### Frontend Integration
- **Streaming**: Server-Sent Events for real-time response display
- **Non-Streaming**: Traditional REST for complete responses with citations
- **Error Handling**: Graceful degradation with informative error messages

## Configuration Management

### Environment Variables
- `DEFAULT_MODEL_ID`: GGUF model filename for inference service
- `INFERENCE_SERVICE_URL`: Inference service endpoint (default: http://localhost:8003)
- `SEARCH_BASE_URL`: Search API endpoint override
- `MAX_CHUNK_CHARS`: Context truncation limit
- `RETRIEVAL_TIMEOUT`: Search API timeout configuration
- `INFERENCE_SERVICE_TIMEOUT`: Inference service timeout (default: 120s)

### Runtime Parameters
- Generation: temperature, max_tokens, top_p
- Retrieval: num_results, collection selection
- Verification: support thresholds, citation requirements

## Performance Characteristics

### Latency Profile
- **Query Normalization**: <10ms
- **Enhanced Retrieval**: 200-500ms (depends on reference expansion)
- **Model Generation**: 2-8 seconds (varies by response length)
- **Verification**: 50-100ms
- **Total Response Time**: 3-10 seconds typical

### Resource Usage
- **Memory**: 4-6GB for external inference service (vs 8-12GB with MLX Python)
- **CPU**: Moderate during retrieval, inference delegated to external service
- **Storage**: ~500MB for vector database, ~2-4GB for GGUF models
- **Network**: Local HTTP calls between services, minimal external traffic

## Security Considerations

### Input Validation
- Query sanitization to prevent injection attacks
- Parameter bounds checking and type validation
- Rate limiting and request size limits

### Data Privacy
- All processing occurs locally (current deployment)
- No external API calls for sensitive legal queries
- Document access control via collection boundaries

### Inference Service Security
- Local inference service execution (no external APIs)
- Service-to-service authentication (localhost only)
- Process isolation between RAG API and inference service
- Inference request isolation and timeout protection

## Monitoring and Observability

### Health Checks
- Inference service availability and response times  
- Search API connectivity and response times
- Database connection and query performance
- Service-to-service communication health

### Logging
- Request/response logging with sanitization
- Performance metrics for each pipeline stage
- Error tracking with context and stack traces

### Metrics
- Answer quality scores (citation accuracy, support levels)
- System performance (latency, throughput, resource usage)
- User interaction patterns (query types, success rates)

## Architecture Benefits

### Memory Optimization
The external inference service architecture provides significant memory improvements:
- **Reduced Memory Usage**: 4-6GB vs 8-12GB with MLX Python bindings
- **Process Isolation**: Better memory management and garbage collection
- **Service Independence**: RAG logic and inference can scale independently

### Cloud Migration Foundation  
This architecture establishes patterns for seamless cloud migration:
- **Service Boundaries**: HTTP API pattern matches AWS Bedrock integration
- **External Dependencies**: Already designed for remote service calls
- **Configuration Externalization**: Environment-based service endpoint management

### Performance and Reliability
- **Native Performance**: llama.cpp provides optimized inference closer to CLI performance
- **Fault Isolation**: Service failures don't crash the entire RAG system
- **Independent Scaling**: Services can be scaled based on specific resource needs

This architecture provides a robust, scalable foundation for legal document RAG while maintaining high accuracy, performance, and reliability. The external inference service approach resolves immediate memory constraints while establishing the foundation for future cloud migration.