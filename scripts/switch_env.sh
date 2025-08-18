#!/bin/bash

# Environment Switching Script for LangChain RAG Migration
# Usage: ./scripts/switch_env.sh [local|staging|production]

set -e

ENV=${1:-local}

if [[ ! "$ENV" =~ ^(local|staging|production)$ ]]; then
    echo "Error: Invalid environment. Use: local, staging, or production"
    exit 1
fi

ENV_FILE=".env.$ENV"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

# Create or update the main .env file
cp "$ENV_FILE" .env

echo "✅ Switched to $ENV environment"
echo "📁 Configuration loaded from $ENV_FILE"

# Show key settings
echo ""
echo "🔧 Key Configuration:"
echo "  DEPLOYMENT_ENV=$(grep DEPLOYMENT_ENV .env | cut -d= -f2)"
echo "  LANGSMITH_TRACING=$(grep LANGSMITH_TRACING .env | cut -d= -f2)"

if [[ "$ENV" == "local" ]]; then
    echo "  LLAMA_CPP_BASE_URL=$(grep LLAMA_CPP_BASE_URL .env | cut -d= -f2)"
else
    echo "  AWS_REGION=$(grep AWS_REGION .env | cut -d= -f2)"
    if [[ "$ENV" == "staging" ]]; then
        echo "  MODEL=$(grep BEDROCK_STAGING_MODEL .env | cut -d= -f2)"
    else
        echo "  MODEL=$(grep BEDROCK_PRODUCTION_MODEL .env | cut -d= -f2)"
    fi
fi

echo ""
echo "🚀 Environment ready! You can now start the RAG API with:"
echo "   source env/bin/activate && python apis/rag/rag_api.py"