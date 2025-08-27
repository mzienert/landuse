# Infrastructure Documentation

This directory contains infrastructure documentation for deploying the La Plata County RAG application to AWS.

## 📋 Overview

The RAG application consists of three core services that need to be deployed:

- **Search API** (Port 8000) - Vector search via ChromaDB + SentenceTransformers
- **RAG API** (Port 8001) - Orchestration, retrieval, and response generation
- **Inference Service** (Port 8003) - llama.cpp HTTP server or AWS Bedrock

*Note: Services are located in the `services/` directory (renamed from `apis/` for clarity)*

## 🏗️ Current Architecture

### Local Development
- **LocalStack**: Local AWS service emulation (API Gateway, Lambda, Bedrock)
- **Search API**: Lambda functions (same as production) via LocalStack
- **RAG API**: Flask app with LangChain abstraction layer  
- **Inference**: llama.cpp server with GGUF models
- **Frontend**: Next.js (already deployed to Vercel)
- **Vector DB**: Pinecone Local (in-memory emulator) for development

### Service Dependencies
```
Frontend (Vercel) → RAG API → Search API (Lambda via API Gateway) → Bedrock + Pinecone
                            → Inference Service
                            
Local Development:
Frontend → RAG API → LocalStack (API Gateway + Lambda) → Pinecone Local
```

## 💾 Critical Components

### Data Storage
- **Vector Database**: Pinecone (free tier, up to 100K vectors) - external SaaS, not AWS-hosted
- **Embedding Model**: intfloat/e5-large-v2 (~2GB)
- **LLM Models**: GGUF format models (~2-4GB each)
- **Note**: ChromaDB being replaced with Pinecone for cost control ($0 vs $50/month minimum)

### Resource Requirements
- **Memory**: 8-12GB per service instance
- **Storage**: ~4GB for models (vector database now external via Pinecone)
- **Compute**: GPU-optimized for inference service
- **Network**: External API calls to Pinecone (consider latency/reliability)

### Collections
- `la_plata_county_code`: 1,298 legal code sections
- `la_plata_assessor`: 46,230 property records

## 🚀 Deployment Readiness

The application is already architected for cloud deployment:

- **Service Boundaries**: HTTP APIs between components
- **Configuration**: Environment variable driven
- **Cloud Integration**: Built-in AWS Bedrock support
- **Application Factory**: Environment-specific configs (dev/staging/prod)

## 📁 Documentation Structure

*This directory will contain deployment guides, configuration examples, and infrastructure-as-code templates as they are developed.*

## 🔄 Migration Strategy

The system supports multiple deployment approaches:

1. **Containerized Services**: ECS/EKS with model storage (vector DB external via Pinecone)
2. **Managed Services**: AWS Bedrock + Lambda (vector DB external via Pinecone)
3. **Hybrid Approach**: Mix of managed and self-hosted components + external Pinecone

Each approach leverages the existing service architecture and configuration system.

## 🏗️ AWS Technology Stack

### Infrastructure as Code
- **AWS CDK for Python** - Infrastructure definition and deployment automation ✅
  - Multi-environment support (dev/staging/prod)
  - Stack-level tagging (Project, Environment) + resource-level tagging for granular cost analysis
- **Resource Tagging Strategy** - Proactive tagging for fine-grained cost analysis and insights ✅

### API Management
- **API Gateway** - Service routing and external API exposure (stub for now, routes TBD)

### Compute Services
- **AWS Lambda** - Search service compute (query embedding via Bedrock + Pinecone search)

### AI/ML Services
- **AWS Bedrock** - Query embedding generation and LLM inference service integration

## 📋 AWS Infrastructure Planning Todo

### Phase 1: Foundation
- [x] **Setup AWS CDK for Python project structure** - Initialize CDK app with proper organization
- [x] **Define resource tagging strategy** - Establish consistent tagging for cost tracking and resource management
- [ ] **Setup LocalStack for local development** - Configure local AWS service emulation for dev/prod parity
- [ ] **Define environment configuration strategy** - Dev/staging/prod configs in AWS
- [ ] **Plan monitoring and logging approach** - Observability setup

### Phase 2: Service Migration
- [ ] **Design solution for RAG API deployment** - How to containerize and deploy the orchestration service
- [ ] **Design solution for Search API deployment** - Lambda-based service (Bedrock embedding + Pinecone search)
- [ ] **Plan service-to-service communication setup** - API Gateway routing between services

### Phase 3: Data Migration
- [ ] **Plan ChromaDB → Pinecone migration strategy** - Migrate 47K+ vectors to Pinecone free tier (100K limit)
- [ ] **Configure Bedrock embedding models** - Setup embedding generation for both migration and runtime queries
- [ ] **Update Search API for Lambda + Pinecone integration** - Replace SentenceTransformers + ChromaDB with Bedrock + Pinecone
- [ ] **Setup Pinecone Local for development** - Configure in-memory emulator for local development environment

## 🔧 Service Organization Notes

*These organizational improvements are not blockers for AWS deployment but important for long-term maintainability and testing.*

### Current Service Structure Analysis

**RAG Service** (`services/rag/`):
- ✅ **Well-organized**: `handlers/`, `inference/`, `providers/` modules
- ❓ **Root-level utilities**: `retrieval.py`, `normalize.py`, `verify.py` could move to `lib/` or `utils/`
- ❓ **Routing**: `routes.py` at root could consolidate into `handlers/`

**Search Service** (`services/search/`):
- ✅ **Well-organized**: `handlers/`, `embeddings/` modules  
- ❓ **Engine separation**: `search_engine.py` could move to `lib/engines/`
- ❓ **Routing**: `routes.py` at root could consolidate into `handlers/`

### Future Service Organization Tasks (Post-AWS):
- [ ] Move utility modules (`retrieval.py`, `normalize.py`, `verify.py`) to `lib/` or `utils/`
- [ ] Consolidate routing - move root `routes.py` into `handlers/`
- [ ] Create shared `lib/engines/` for `search_engine.py`
- [ ] Standardize module structure between services
- [ ] Enhance test coverage with cleaner module boundaries