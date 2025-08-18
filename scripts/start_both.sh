#!/bin/bash

# La Plata County Combined API Management Script
# Manages Search API (port 8000), llama.cpp Service (port 8003), and RAG API (port 8001)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# API Scripts
API_SCRIPT="$SCRIPT_DIR/api.sh"
LLAMA_SCRIPT="$SCRIPT_DIR/llama.sh"
RAG_SCRIPT="$SCRIPT_DIR/run_rag.sh"

cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if all services are running
check_all_status() {
    local search_running=false
    local llama_running=false
    local rag_running=false
    
    # Check search API
    if [ -f "$PROJECT_ROOT/api.pid" ] && ps -p $(cat "$PROJECT_ROOT/api.pid") > /dev/null 2>&1; then
        search_running=true
    fi
    
    # Check llama.cpp service
    if [ -f "$PROJECT_ROOT/llama.pid" ] && ps -p $(cat "$PROJECT_ROOT/llama.pid") > /dev/null 2>&1; then
        llama_running=true
    fi
    
    # Check RAG API
    if [ -f "$PROJECT_ROOT/rag.pid" ] && ps -p $(cat "$PROJECT_ROOT/rag.pid") > /dev/null 2>&1; then
        rag_running=true
    fi
    
    if $search_running && $llama_running && $rag_running; then
        return 0  # All running
    else
        return 1  # At least one not running
    fi
}

# Function to start all services
start_all() {
    local env_type=${RAG_ENV:-local}
    print_status $YELLOW "🚀 Starting La Plata County API Suite (Environment: $env_type)..."
    echo ""
    
    # Start Search API first
    print_status $YELLOW "1/3 Starting Search API (port 8000)..."
    if ! "$API_SCRIPT" start; then
        print_status $RED "❌ Failed to start Search API"
        return 1
    fi
    
    echo ""
    
    # Start llama.cpp inference service
    print_status $YELLOW "2/3 Starting llama.cpp Inference Service (port 8003)..."
    if ! "$LLAMA_SCRIPT" start; then
        print_status $RED "❌ Failed to start llama.cpp service"
        print_status $YELLOW "Search API is still running. Use './scripts/api.sh stop' to stop it."
        return 1
    fi
    
    echo ""
    
    # Wait a moment for services to fully start
    sleep 3
    
    # Start RAG API with environment
    print_status $YELLOW "3/3 Starting RAG API (port 8001) with environment: $env_type..."
    export RAG_ENV="$env_type"
    if ! "$RAG_SCRIPT" start; then
        print_status $RED "❌ Failed to start RAG API"
        print_status $YELLOW "Other services are still running. Use './scripts/start_both.sh stop' to stop all."
        return 1
    fi
    
    echo ""
    
    # Wait for RAG API to be fully ready
    print_status $YELLOW "Waiting for RAG API to be ready..."
    local max_wait=30
    local count=0
    while [ $count -lt $max_wait ]; do
        if curl -s --connect-timeout 2 "http://localhost:8001/rag/health" > /dev/null 2>&1; then
            break
        fi
        sleep 1
        count=$((count + 1))
        printf "."
    done
    echo ""
    
    if [ $count -ge $max_wait ]; then
        print_status $RED "❌ RAG API failed to become ready within ${max_wait} seconds"
        return 1
    fi
    
    # Load default model automatically from config
    print_status $YELLOW "Loading default RAG model from config..."
    local model_response=$(curl -s -X POST "http://localhost:8001/rag/model/load" \
        -H 'Content-Type: application/json' \
        -d '{}' 2>/dev/null)
    
    if [[ $model_response == *'"loaded":true'* ]]; then
        print_status $GREEN "✅ Default model loaded successfully"
    else
        print_status $YELLOW "⚠️  Model load may have issues. Check with: curl http://localhost:8001/rag/health"
        echo "   Response: $model_response"
        echo "   You can manually load a model with:"
        echo "   curl -X POST http://localhost:8001/rag/model/load -H 'Content-Type: application/json' -d '{}'"
    fi
    
    echo ""
    
    # Verify all services are running
    if check_all_status; then
        print_status $GREEN "✅ All services started successfully!"
        echo ""
        print_status $GREEN "🔍 Search API: http://localhost:8000"
        print_status $GREEN "🧠 llama.cpp Service: http://localhost:8003"  
        print_status $GREEN "🤖 RAG API: http://localhost:8001"
        echo ""
        echo "Test commands:"
        echo "  curl \"http://localhost:8000/health\""
        echo "  curl \"http://localhost:8003/health\""
        echo "  curl \"http://localhost:8001/rag/health\""
        echo ""
        echo "RAG test query:"
        echo "  curl -X POST http://localhost:8001/rag/answer -H 'Content-Type: application/json' -d '{\"query\":\"What are subdivision requirements?\",\"collection\":\"la_plata_county_code\",\"num_results\":5}'"
        echo ""
        echo "Management:"
        echo "  ./scripts/start_both.sh status   # Check both APIs"
        echo "  ./scripts/start_both.sh stop     # Stop both APIs"
        return 0
    else
        print_status $RED "❌ One or both APIs failed to start properly"
        return 1
    fi
}

# Function to stop all services
stop_all() {
    print_status $YELLOW "🛑 Stopping La Plata County API Suite..."
    echo ""
    
    # Stop RAG API first
    print_status $YELLOW "Stopping RAG API..."
    "$RAG_SCRIPT" stop
    
    echo ""
    
    # Stop llama.cpp service  
    print_status $YELLOW "Stopping llama.cpp Inference Service..."
    "$LLAMA_SCRIPT" stop
    
    echo ""
    
    # Stop Search API
    print_status $YELLOW "Stopping Search API..."
    "$API_SCRIPT" stop
    
    echo ""
    print_status $GREEN "✅ All services stopped"
}

# Function to restart all services
restart_all() {
    print_status $YELLOW "🔄 Restarting La Plata County API Suite..."
    echo ""
    
    stop_all
    sleep 2
    start_all
}

# Function to show status of all services
status_all() {
    print_status $YELLOW "📊 La Plata County API Suite Status"
    echo ""
    
    # Search API Status
    print_status $YELLOW "🔍 Search API (port 8000):"
    "$API_SCRIPT" status
    echo ""
    
    # llama.cpp Status
    print_status $YELLOW "🧠 llama.cpp Inference Service (port 8003):"
    "$LLAMA_SCRIPT" status
    echo ""
    
    # RAG API Status
    print_status $YELLOW "🤖 RAG API (port 8001):"
    "$RAG_SCRIPT" status
    echo ""
    
    # Overall Status
    if check_all_status; then
        print_status $GREEN "✅ Overall Status: All services running"
        echo ""
        echo "Quick tests:"
        echo "  curl \"http://localhost:8000/search/simple?query=building%20permits&num_results=3\""
        echo "  curl \"http://localhost:8003/health\""
        echo "  curl \"http://localhost:8001/rag/health\""
    else
        print_status $RED "❌ Overall Status: One or more services not running"
        echo ""
        echo "Use './scripts/start_both.sh start' to start all services"
    fi
}

# Function to show logs from all services
logs_all() {
    print_status $YELLOW "📜 Service Logs"
    echo ""
    
    print_status $YELLOW "🔍 Search API Logs:"
    "$API_SCRIPT" logs
    echo ""
    
    print_status $YELLOW "🧠 llama.cpp Service Logs:"
    "$LLAMA_SCRIPT" logs
    echo ""
    
    print_status $YELLOW "🤖 RAG API Logs:"
    "$RAG_SCRIPT" logs
}

# Function to test all services
test_all() {
    print_status $YELLOW "🧪 Testing La Plata County API Suite..."
    echo ""
    
    # Test Search API
    print_status $YELLOW "Testing Search API..."
    if curl -s --connect-timeout 5 "http://localhost:8000/health" > /dev/null; then
        print_status $GREEN "✅ Search API responding"
        
        # Test a simple search
        echo "Testing search functionality..."
        local search_result=$(curl -s --connect-timeout 5 "http://localhost:8000/search/simple?query=building&num_results=1")
        if [[ $search_result == *"results"* ]]; then
            print_status $GREEN "✅ Search functionality working"
        else
            print_status $YELLOW "⚠️  Search API responding but search may have issues"
        fi
    else
        print_status $RED "❌ Search API not responding"
    fi
    
    echo ""
    
    # Test llama.cpp service
    print_status $YELLOW "Testing llama.cpp Inference Service..."
    if curl -s --connect-timeout 5 "http://localhost:8003/health" > /dev/null; then
        print_status $GREEN "✅ llama.cpp service responding"
        
        # Test completion functionality
        echo "Testing completion functionality..."
        local completion_result=$(curl -s --connect-timeout 10 -X POST "http://localhost:8003/completion" \
            -H "Content-Type: application/json" \
            -d '{"prompt":"Hello", "n_predict":5}')
        if [[ $completion_result == *"content"* ]]; then
            print_status $GREEN "✅ llama.cpp completion working"
        else
            print_status $YELLOW "⚠️  llama.cpp responding but completion may have issues"
        fi
    else
        print_status $RED "❌ llama.cpp service not responding"
    fi
    
    echo ""
    
    # Test RAG API
    print_status $YELLOW "Testing RAG API..."
    if curl -s --connect-timeout 5 "http://localhost:8001/rag/health" > /dev/null; then
        print_status $GREEN "✅ RAG API responding"
        
        # Check if model is loaded
        local health_result=$(curl -s --connect-timeout 5 "http://localhost:8001/rag/health")
        if [[ $health_result == *'"model_loaded":true'* ]]; then
            print_status $GREEN "✅ RAG model loaded and ready"
        else
            print_status $YELLOW "⚠️  RAG API responding but no model loaded"
            echo "Load a model with: curl -X POST http://localhost:8001/rag/model/load -H 'Content-Type: application/json' -d '{}'"
        fi
    else
        print_status $RED "❌ RAG API not responding"
    fi
    
    echo ""
    
    # Overall test result
    if check_all_status; then
        print_status $GREEN "✅ All services are operational"
    else
        print_status $RED "❌ One or more services have issues"
    fi
}

# Function to show help
show_help() {
    echo "La Plata County API Suite Management Script"
    echo ""
    echo "Manages Search API (port 8000), llama.cpp Service (port 8003), and RAG API (port 8001) together"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|test|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start all services (Search API → llama.cpp → RAG API)"
    echo "  stop     - Stop all services"
    echo "  restart  - Restart all services"
    echo "  status   - Show status of all services"
    echo "  logs     - Show logs from all services"
    echo "  test     - Test connectivity and functionality of all services"
    echo "  help     - Show this help message"
    echo ""
    echo "Individual service management:"
    echo "  ./scripts/api.sh {start|stop|status}     # Search API only"
    echo "  ./scripts/llama.sh {start|stop|status}   # llama.cpp service only"
    echo "  ./scripts/run_rag.sh {start|stop|status} # RAG API only"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start all services (local environment)"
    echo "  RAG_ENV=staging $0 start    # Start with staging environment"
    echo "  $0 status                   # Check if all are running"
    echo "  $0 test                     # Test all services"
    echo ""
    echo "Typical workflow:"
    echo "  1. $0 start                 # Start all services"
    echo "  2. $0 test                  # Verify everything works"
    echo "  3. Use APIs for search and Q&A"
}

# Main script logic
case "${1:-help}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        status_all
        ;;
    logs)
        logs_all
        ;;
    test)
        test_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac