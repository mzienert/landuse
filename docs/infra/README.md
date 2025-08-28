# Infrastructure Documentation

This directory contains infrastructure documentation for migrating the complete La Plata County RAG system to AWS.

## 📋 Overview

The complete RAG system consists of three core services being migrated to AWS:

- **Search API** (Port 8000) - Vector search via ChromaDB + SentenceTransformers → **AWS Lambda + Bedrock + Pinecone**
- **RAG API** (Port 8001) - Orchestration, retrieval, and response generation → **AWS Lambda/ECS + Bedrock**
- **Inference Service** (Port 8003) - llama.cpp HTTP server → **AWS Bedrock**

## 🏗️ Migration Strategy: Parallel Development Approach

### Current Local Development (Preserved During Migration)
- **Existing Complete RAG System**: Continue running via `scripts/start_both.sh`
  - Search API (port 8000): Vector search with ChromaDB/SentenceTransformers
  - RAG API (port 8001): Flask orchestration with LangChain abstraction
  - Inference (port 8003): llama.cpp server with GGUF models
- **Frontend**: Next.js (deployed to Vercel)
- **Data**: Migrated to cloud Pinecone (1,298 county code vectors completed)

### LocalStack Integration (New Parallel Path)
- **LocalStack**: Complete AWS service emulation (API Gateway, Lambda, Bedrock simulation)
- **Dual Development**: Run existing RAG system **alongside** LocalStack implementation
- **Gradual Migration**: Move complete RAG functionality piece-by-piece from direct services → LocalStack → AWS
- **Validation Pipeline**: Local RAG → LocalStack RAG → Staging RAG → Production RAG

### Complete System Migration Flow
```
Current Local RAG System (keep running)
         ↓ (gradual component migration)
LocalStack RAG Implementation (parallel)
         ↓ (validate full RAG functionality)
AWS Staging RAG Environment
         ↓ (production readiness)
AWS Production RAG Environment
```

## 💾 Current Infrastructure Status

### AWS CDK Deployment
- ✅ **CDK Infrastructure**: Python-based with multi-environment support (staging/prod)
- ✅ **Basic Search Lambda**: Deployed and responding at staging/prod endpoints
  - **Staging**: `https://0vf263niik.execute-api.us-west-2.amazonaws.com/staging/search`
  - **Production**: `https://zlhcbs2w8e.execute-api.us-west-2.amazonaws.com/prod/search`
- ✅ **Resource Tagging**: Environment and cost tracking configured

### Data Migration Progress
- ✅ **Pinecone Setup**: External vector database configured
- ✅ **County Code Migration**: 1,298 legal code sections migrated to `la-plata-county-code` index
- ⏳ **Assessor Data**: 46,230 property records pending migration

### LocalStack Development Environment
- 🔄 **In Progress**: Docker-compose LocalStack setup for complete RAG system
- ⏳ **CDK LocalStack Deployment**: Configure CDK to deploy complete RAG to LocalStack
- ⏳ **Parallel RAG Testing**: Run existing RAG system + LocalStack RAG side-by-side

## 🚀 Implementation Roadmap

### Phase 1: LocalStack Foundation (Current)
- [ ] **LocalStack Docker Setup** - Configure LocalStack with API Gateway + Lambda + Bedrock services
- [ ] **CDK LocalStack Integration** - Deploy complete RAG Lambda functions to LocalStack
- [ ] **Parallel Development Script** - Modified start script running existing RAG system + LocalStack RAG
- [ ] **Local Testing Framework** - Compare RAG responses between direct system and LocalStack implementation

### Phase 2: Search Service Migration (Starting Point)
- [ ] **Search Lambda Health Check** - Migrate search `/health` endpoint functionality
- [ ] **Bedrock Integration Setup** - Configure LocalStack Bedrock simulation for embeddings
- [ ] **Pinecone Connection** - Connect LocalStack search Lambda to cloud Pinecone
- [ ] **Simple Search Migration** - Move basic search functionality to Lambda
- [ ] **Search Response Alignment** - Ensure LocalStack search responses match existing API

### Phase 3: RAG Orchestration Migration
- [ ] **RAG Lambda Development** - Create RAG orchestration Lambda functions
- [ ] **LangChain Integration** - Migrate LangChain abstraction layer to Lambda
- [ ] **Inter-Lambda Communication** - Configure Lambda-to-Lambda communication (search → RAG)
- [ ] **RAG Response Pipeline** - Complete query → search → generate → response flow
- [ ] **RAG API Compatibility** - Ensure LocalStack RAG API matches existing interface

### Phase 4: Inference Service Migration
- [ ] **Bedrock LLM Integration** - Replace llama.cpp with AWS Bedrock models
- [ ] **Model Configuration** - Configure Bedrock models to match local llama.cpp behavior
- [ ] **Inference Lambda Development** - Create inference abstraction Lambda if needed
- [ ] **Response Format Compatibility** - Ensure Bedrock responses match llama.cpp format

### Phase 5: Complete RAG System Integration
- [ ] **End-to-End RAG Pipeline** - Complete LocalStack RAG system functionality
- [ ] **Performance Testing** - Compare LocalStack RAG vs direct RAG system performance
- [ ] **Error Handling** - Comprehensive error handling across all RAG components
- [ ] **Integration Testing** - Full RAG workflow testing in LocalStack

### Phase 6: AWS Staging Validation
- [ ] **Complete RAG Staging Deployment** - Deploy full RAG system to AWS staging
- [ ] **End-to-End RAG Testing** - Complete user journey testing on staging RAG
- [ ] **Performance Benchmarking** - AWS RAG performance vs local RAG system
- [ ] **Cost Analysis** - Actual AWS RAG costs vs projections

### Phase 7: Production RAG Migration
- [ ] **Production RAG Deployment** - Deploy complete tested RAG system to production
- [ ] **Traffic Gradual Migration** - Gradual shift from local to AWS RAG system
- [ ] **Monitoring & Alerts** - CloudWatch monitoring for complete RAG pipeline
- [ ] **Rollback Planning** - Ability to rollback to local RAG system if needed

## 🔧 Development Environment Architecture

### Current Parallel Setup (During Migration)
```
┌─────────────────────────────────────────┐
│              Frontend (Vercel)          │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
    ▼                           ▼
┌─────────────────┐    ┌─────────────────┐
│ Existing Local  │    │   LocalStack    │
│   RAG System    │    │   RAG System    │
├─────────────────┤    ├─────────────────┤
│ Search API :8000│    │ Search Lambda   │
│ RAG API    :8001│    │ RAG Lambda      │
│ llama.cpp  :8003│    │ Bedrock (mock)  │
└─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│ ChromaDB Local  │    │ Pinecone Cloud  │
│ (legacy)        │    │ (shared)        │
└─────────────────┘    └─────────────────┘
```

### Target AWS Production RAG Architecture
```
Frontend (Vercel) → API Gateway → RAG Lambda Functions → Bedrock + Pinecone
                                       ├─ Search Lambda
                                       ├─ RAG Orchestration Lambda  
                                       └─ Bedrock LLM Integration
```

## 📋 Current Progress Tracking

### ✅ Completed
- AWS CDK infrastructure setup with staging/prod environments
- Basic search Lambda function deployment and API Gateway integration
- ChromaDB to Pinecone migration script and county code data migration
- Multi-environment configuration and resource tagging

### 🔄 In Progress
- LocalStack development environment setup for complete RAG system
- Infrastructure documentation revision and complete RAG migration strategy planning

### ⏳ Next Steps
1. Complete LocalStack docker-compose configuration for full RAG services
2. Configure CDK to deploy complete RAG system to LocalStack endpoint
3. Create parallel development startup script for both RAG systems
4. Begin incremental RAG component migration starting with search health endpoints

## 💡 Development Workflow

### Daily Development
1. **Start Both RAG Systems**: `./scripts/start_local_with_localstack.sh` (planned)
2. **RAG Feature Development**: Build in existing RAG system first
3. **Migration Testing**: Migrate RAG feature to LocalStack implementation
4. **Validation**: Compare RAG responses between both environments
5. **AWS Testing**: Deploy to staging when LocalStack RAG validates

### RAG Migration Validation
- **Response Parity**: Ensure LocalStack RAG matches direct RAG system responses
- **Performance Baseline**: Measure complete RAG pipeline response times and resource usage
- **Error Handling**: Test failure scenarios across all RAG components
- **Integration Testing**: Verify complete RAG workflow in both environments

This approach ensures zero downtime and provides confidence at each RAG migration step while maintaining the ability to rollback to the complete local RAG system if issues arise.