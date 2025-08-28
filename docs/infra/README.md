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
- **LocalStack**: AWS service emulation (API Gateway, Lambda) + existing llama.cpp inference
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
- ✅ **Docker-compose LocalStack Setup**: Complete LocalStack environment configured
- ✅ **CDK LocalStack Deployment**: Deploy script supports `dev` environment with LocalStack
- ✅ **LocalStack Management**: Standalone script for container management (`scripts/localstack.sh`)
- ⏳ **Parallel RAG Testing**: Ready for independent service testing alongside LocalStack

## 🚀 Implementation Roadmap

### Phase 1: LocalStack Foundation ✅ **COMPLETED**
- [x] **LocalStack Docker Setup** - LocalStack configured with API Gateway, Lambda, CloudFormation, IAM, STS services
- [x] **CDK LocalStack Integration** - Deploy script supports `./scripts/deploy.sh dev` for LocalStack deployment
- [x] **LocalStack Management** - Independent LocalStack management via `./scripts/localstack.sh`

### Phase 2: Search Service Migration ✅ **COMPLETED**
- ✅ **LocalStack Version Update**: Upgraded to LocalStack 4.7.0 with improved CDK compatibility
- ✅ **CDK Bootstrap Success**: Successfully bootstrapped CDK with LocalStack 4.7.0 using proper endpoint configuration
- ✅ **Binary Asset Issue Resolved**: Inline Lambda code deployment bypasses S3 binary zip file parsing errors
- ✅ **S3 Endpoint Configuration Fixed**: Using specialized S3 endpoint `http://s3.localhost.localstack.cloud:4566` resolves JSON-as-XML parsing
- ✅ **Complete CDK Deployment Success**: Lambda function and API Gateway successfully deployed and tested on LocalStack
- ✅ **Working API Endpoints**: Both GET and POST requests work correctly
  - **Search API Endpoint**: `https://ewti59m6iv.execute-api.localhost.localstack.cloud:4566/dev/search`
  - **Health Check**: ✅ Responds with proper JSON and processes request bodies
- [ ] **Search Lambda Health Check** - Migrate search `/health` endpoint functionality
- [ ] **Embedding Generation Setup** - Configure embedding generation for LocalStack (initially via existing service)
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
- [ ] **Bedrock LLM Integration** - Replace llama.cpp with AWS Bedrock models (production only)
- [ ] **Model Configuration** - Configure Bedrock models to match local llama.cpp behavior
- [ ] **Inference Abstraction** - Create abstraction layer for llama.cpp → Bedrock transition
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
│ llama.cpp  :8003│    │ llama.cpp :8003 │
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
- Phase 2: Search Service Migration - Ready to begin with LocalStack foundation complete
- Local testing framework development for comparing responses

### 🎉 LocalStack CDK Integration Success

The LocalStack CDK compatibility issue has been **fully resolved**! Key breakthrough discoveries:

#### The Solution
1. **Updated LocalStack**: Upgraded from 3.0 to 4.7.0 with improved CDK support
2. **Specialized S3 Endpoint**: Using `AWS_ENDPOINT_URL_S3=http://s3.localhost.localstack.cloud:4566` instead of `localhost:4566`
3. **Inline Lambda Code**: For dev environment, Lambda code is embedded inline instead of S3 asset uploads
4. **Proper CDK Bootstrap**: LocalStack 4.7.0 requires both `AWS_ENDPOINT_URL` and `AWS_ENDPOINT_URL_S3` to be specified

#### Working Commands
```bash
# Deploy to LocalStack (now works perfectly!)
./scripts/deploy.sh dev deploy

# Test deployed API
curl -s "https://ewti59m6iv.execute-api.localhost.localstack.cloud:4566/dev/search"
```

### ⏳ Next Steps
1. ✅ **LocalStack Foundation Complete** - Ready for search service migration
2. Begin migrating actual search functionality from local services to LocalStack Lambda
3. Connect LocalStack Lambda to cloud Pinecone for vector search
4. Implement embedding generation integration

## 💡 Development Workflow

### Daily Development

#### Quick Setup
1. **Start LocalStack**: `./scripts/localstack.sh start`
2. **Initial Deploy**: `./scripts/deploy.sh dev deploy`

#### Development Iteration Cycles

**🚀 Fast Development (Recommended): CDK Watch Mode**
```bash
# Auto-redeploy on file changes (~1-2 seconds per change)
./scripts/deploy.sh dev watch

# Make changes to lambda/search/lambda_function.py
# Changes auto-deploy with hotswap in ~1-2 seconds
# Test: curl "https://ewti59m6iv.execute-api.localhost.localstack.cloud:4566/dev/search"
```

**⚡ Ultra-Fast Development: Hot Reload (For Algorithm Tuning)**
```bash
# Add to docker-compose.localstack.yml for instant code changes
environment:
  - LAMBDA_MOUNT_CODE=1
volumes:
  - "./infra/lambda:/var/lib/localstack/lambda"

# Changes to lambda files are instant (no deployment needed)
# Note: LocalStack-specific, may have inconsistencies with real AWS
```

**🐢 Full Deployment: Traditional CDK**
```bash
# For infrastructure changes or final validation (~7-10 seconds)
./scripts/deploy.sh dev deploy
```

#### Complete Development Workflow
1. **Start Existing RAG System**: `./scripts/start_both.sh` (unchanged)
2. **Start LocalStack**: `./scripts/localstack.sh start` 
3. **Begin Watch Mode**: Use CDK watch for rapid Lambda development
4. **RAG Feature Development**: Build in existing RAG system first, then migrate to LocalStack
5. **Algorithm Tuning**: Switch to hot reload for intensive iteration sessions
6. **AWS Testing**: Deploy to staging when LocalStack implementation validates

### RAG Migration Validation
- **Response Parity**: Ensure LocalStack RAG matches direct RAG system responses
- **Performance Baseline**: Measure complete RAG pipeline response times and resource usage
- **Error Handling**: Test failure scenarios across all RAG components
- **Integration Testing**: Verify complete RAG workflow in both environments

This approach ensures zero downtime and provides confidence at each RAG migration step while maintaining the ability to rollback to the complete local RAG system if issues arise.