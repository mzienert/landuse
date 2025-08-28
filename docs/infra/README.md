# Infrastructure Documentation

This directory contains infrastructure documentation for migrating the complete La Plata County RAG system to AWS.

## 🚀 Quick Start

### Prerequisites

Before setting up the local development environment, ensure you have the following installed:

**Required:**
- **Node.js (v18+)**: [Download here](https://nodejs.org/)
- **Docker & Docker Compose**: [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Python 3.11+**: [Download here](https://www.python.org/downloads/)
- **AWS CDK**: Install globally with `npm install -g aws-cdk`
- **CDK Local**: Install globally with `npm install -g aws-cdk-local`

**Optional but Recommended:**
- **AWS CLI**: [Installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

### Local Setup (First Time)

```bash
# 1. Clone and navigate to project
cd /path/to/landuse

# 2. Install CDK dependencies
npm install -g aws-cdk aws-cdk-local

# 3. Set up Python environment (recommended)
cd infra
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Start LocalStack
./scripts/localstack.sh start

# 5. Initial deployment
./scripts/deploy.sh dev deploy

# 6. Test the deployment (endpoint will be shown in deploy output)
curl "https://YOUR_API_ID.execute-api.localhost.localstack.cloud:4566/dev/search"
```

### Daily Development Workflow

```bash
# Start LocalStack (if not already running)
./scripts/localstack.sh start

# Start rapid development mode
./scripts/deploy.sh dev watch

# Make changes to lambda/search/lambda_function.py
# Changes auto-deploy in ~1-2 seconds
# Test with: curl "https://YOUR_API_ID.execute-api.localhost.localstack.cloud:4566/dev/search"
```

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

## 💡 Available Scripts

### LocalStack Management
```bash
./scripts/localstack.sh start    # Start LocalStack container
./scripts/localstack.sh stop     # Stop LocalStack container  
./scripts/localstack.sh status   # Check LocalStack status
./scripts/localstack.sh health   # Detailed health check
./scripts/localstack.sh logs     # View LocalStack logs
```

### Deployment Commands
```bash
./scripts/deploy.sh dev deploy   # Deploy to LocalStack (one-time)
./scripts/deploy.sh dev watch    # Start watch mode (rapid development)
./scripts/deploy.sh dev destroy  # Destroy LocalStack resources
./scripts/deploy.sh dev diff     # Show differences
./scripts/deploy.sh dev synth    # Generate CloudFormation template

# Staging/Production (when ready)
./scripts/deploy.sh staging deploy
./scripts/deploy.sh prod deploy
```

## 🔧 Development Iteration Cycles

### 🚀 Primary: CDK Watch Mode (Recommended)
```bash
./scripts/deploy.sh dev watch
# - Auto-redeploy on file changes (~1-2 seconds)
# - Uses hotswap for Lambda-only changes  
# - Perfect for rapid development
```

### ⚡ Advanced: Hot Reload (For Algorithm Tuning)
```bash
# Add to docker-compose.localstack.yml for instant changes:
environment:
  - LAMBDA_MOUNT_CODE=1
volumes:
  - "./infra/lambda:/var/lib/localstack/lambda"

# Changes are instant (no deployment cycle)
# Use for intensive algorithm iteration sessions
```

### 🐢 Full Stack: Traditional Deployment  
```bash
./scripts/deploy.sh dev deploy
# - Complete infrastructure deployment (~7-10 seconds)
# - Use for infrastructure changes or final validation
```

## 🔄 Complete Development Workflow
1. **Start Existing RAG System**: `./scripts/start_both.sh` (unchanged)
2. **Start LocalStack**: `./scripts/localstack.sh start` 
3. **Deploy Initial Infrastructure**: `./scripts/deploy.sh dev deploy`
4. **Begin Rapid Development**: `./scripts/deploy.sh dev watch`
5. **RAG Feature Development**: Build in existing system first, then migrate to LocalStack
6. **AWS Testing**: Deploy to staging when LocalStack implementation validates

### RAG Migration Validation
- **Response Parity**: Ensure LocalStack RAG matches direct RAG system responses
- **Performance Baseline**: Measure complete RAG pipeline response times and resource usage
- **Error Handling**: Test failure scenarios across all RAG components
- **Integration Testing**: Verify complete RAG workflow in both environments

This approach ensures zero downtime and provides confidence at each RAG migration step while maintaining the ability to rollback to the complete local RAG system if issues arise.

## 🔧 Troubleshooting

### Common Issues

**LocalStack not starting:**
```bash
# Check Docker is running
docker ps

# Check LocalStack logs
./scripts/localstack.sh logs

# Restart LocalStack
./scripts/localstack.sh restart
```

**CDK deployment fails:**
```bash
# Ensure LocalStack is healthy
./scripts/localstack.sh health

# Check environment variables are set
echo $AWS_ENDPOINT_URL
echo $AWS_ENDPOINT_URL_S3

# Try destroying and redeploying
./scripts/deploy.sh dev destroy
./scripts/deploy.sh dev deploy
```

**API endpoint not responding:**
```bash
# Check LocalStack API Gateway is running
curl -s http://localhost:4566/_localstack/health | python3 -m json.tool

# Verify Lambda function exists
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test aws lambda list-functions --endpoint-url http://localhost:4566 --region us-west-2

# Check CloudFormation stack
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test aws cloudformation describe-stacks --stack-name LanduseStack-dev --endpoint-url http://localhost:4566 --region us-west-2
```

**Python dependencies:**
```bash
# Ensure virtual environment is active
source infra/venv/bin/activate

# Install/update requirements
pip install -r infra/requirements.txt
```

### Key Environment Variables
When working with LocalStack, these environment variables are automatically set by the deploy script:
- `AWS_ACCESS_KEY_ID=test`
- `AWS_SECRET_ACCESS_KEY=test` 
- `AWS_ENDPOINT_URL=http://localhost:4566`
- `AWS_ENDPOINT_URL_S3=http://s3.localhost.localstack.cloud:4566`

### Finding Your API Endpoints

After deployment, the API endpoints are shown in the deploy script output:

```bash
# Deploy and note the endpoint URLs in the output
./scripts/deploy.sh dev deploy

# Example output:
# ✅  LanduseStack-dev
# Outputs:
# LanduseStack-dev.SearchAPIAPIEndpointAACEDA10 = https://YOUR_UNIQUE_ID.execute-api.localhost.localstack.cloud:4566/dev/search
```

**Standard Endpoints:**
- **Search API**: `https://YOUR_API_ID.execute-api.localhost.localstack.cloud:4566/dev/search`
- **API Root**: `https://YOUR_API_ID.execute-api.localhost.localstack.cloud:4566/dev/`
- **LocalStack Health**: `http://localhost:4566/_localstack/health`

**Get Current Endpoints:**
```bash
# Query deployed stack for current endpoints
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test aws cloudformation describe-stacks \
  --stack-name LanduseStack-dev \
  --endpoint-url http://localhost:4566 \
  --region us-west-2 \
  --query 'Stacks[0].Outputs'
```

## 📁 Project Structure

```
landuse/
├── infra/                          # Infrastructure as Code (CDK)
│   ├── app.py                      # CDK app entry point
│   ├── cdk.json                    # CDK configuration (watch settings)
│   ├── requirements.txt            # Python dependencies  
│   ├── lambda/                     # Lambda function source code
│   │   └── search/
│   │       └── lambda_function.py  # Search Lambda implementation
│   ├── landuse_constructs/         # Reusable CDK constructs
│   │   ├── search_lambda.py        # Lambda construct
│   │   └── search_api_gateway.py   # API Gateway construct
│   └── stacks/                     # CDK stack definitions
│       └── landuse_stack.py        # Main application stack
├── scripts/                        # Automation scripts
│   ├── deploy.sh                   # Deployment script (dev/staging/prod)
│   └── localstack.sh              # LocalStack management
├── docker-compose.localstack.yml   # LocalStack container config
└── docs/
    └── infra/
        └── README.md               # This file
```

### Key Files to Modify During Development

**Lambda Function Logic:**
- `infra/lambda/search/lambda_function.py` - Main search functionality

**Infrastructure Configuration:**  
- `infra/landuse_constructs/search_lambda.py` - Lambda configuration
- `infra/landuse_constructs/search_api_gateway.py` - API Gateway setup
- `infra/stacks/landuse_stack.py` - Overall stack composition

**Environment Configuration:**
- `infra/app.py` - Environment-specific settings
- `docker-compose.localstack.yml` - LocalStack container settings