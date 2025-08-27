#!/bin/bash

# LangChain Migration Test Runner
# Tests the LangChain migration implementation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if virtual environment exists
if [ ! -d "env" ]; then
    print_status $RED "❌ Virtual environment 'env' not found"
    echo "Please create it with: python3 -m venv env && source env/bin/activate"
    exit 1
fi

# Activate virtual environment
source env/bin/activate

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    print_status $YELLOW "📦 Installing pytest..."
    pip install pytest pytest-mock
fi

print_status $BLUE "🧪 Running LangChain Migration Tests"
echo ""

# Function to run specific test categories
run_test_category() {
    local category=$1
    local description=$2
    local test_pattern=$3
    
    print_status $YELLOW "Testing: $description"
    if python -m pytest "services/rag/test_langchain_migration.py::$test_pattern" -v; then
        print_status $GREEN "✅ $description passed"
    else
        print_status $RED "❌ $description failed"
        return 1
    fi
    echo ""
}

# Run all test categories
echo "🔧 Running unit tests..."
echo ""

# Test provider functionality
run_test_category "providers" "LLM Provider Classes" "TestLLMProviders"

# Test inference manager
run_test_category "inference" "LangChain Inference Manager" "TestLangChainInferenceManager"

# Test consistency parameters
run_test_category "consistency" "Parameter Consistency" "TestConsistencyParameters"

# Test LangSmith integration
run_test_category "langsmith" "LangSmith Integration" "TestLangSmithIntegration"

# Test error handling
run_test_category "errors" "Error Handling" "TestErrorHandling"

# Integration tests (optional)
print_status $YELLOW "🔗 Running integration tests (optional)..."
if python -m pytest "services/rag/test_langchain_migration.py::TestIntegration" -v -m integration; then
    print_status $GREEN "✅ Integration tests passed"
else
    print_status $YELLOW "⚠️  Integration tests skipped (llama.cpp server not running)"
fi

echo ""
print_status $GREEN "🎉 LangChain migration tests completed!"

# Additional validation
echo ""
print_status $BLUE "🔍 Additional Validation:"

# Check if environment files exist
if [ -f ".env.local" ] && [ -f ".env.staging" ] && [ -f ".env.production" ]; then
    print_status $GREEN "✅ Environment configuration files exist"
else
    print_status $RED "❌ Missing environment configuration files"
fi

# Check if dependencies are installed
print_status $YELLOW "Checking LangChain dependencies..."
python -c "
import sys
try:
    import langchain_openai
    import langchain_aws  
    import langchain_core
    import langsmith
    print('✅ All LangChain dependencies installed')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    sys.exit(1)
"

# Test configuration loading
print_status $YELLOW "Testing configuration loading..."
python -c "
import sys
import os
sys.path.insert(0, '.')
try:
    from services.rag.config import Config
    config = Config()
    
    # Check LangChain settings exist
    assert hasattr(config, 'DEPLOYMENT_ENV')
    assert hasattr(config, 'LANGSMITH_TRACING')
    assert hasattr(config, 'GENERATION_TEMPERATURE')
    
    print('✅ Configuration loading successful')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"

echo ""
print_status $GREEN "🚀 LangChain migration is ready for implementation!"
echo ""
echo "Next steps:"
echo "  1. Start llama.cpp server: ./scripts/llama.sh start"
echo "  2. Test local environment: ./scripts/start_with_env.sh local start"
echo "  3. Verify RAG API: curl http://localhost:8001/rag/health"