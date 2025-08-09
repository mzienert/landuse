#!/bin/bash

# La Plata County Combined API Management Script
# Manages both Search API (port 8000) and RAG API (port 8001)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# API Scripts
API_SCRIPT="$SCRIPT_DIR/api.sh"
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

# Function to check if both APIs are running
check_both_status() {
    local search_running=false
    local rag_running=false
    
    # Check search API
    if [ -f "$PROJECT_ROOT/api.pid" ] && ps -p $(cat "$PROJECT_ROOT/api.pid") > /dev/null 2>&1; then
        search_running=true
    fi
    
    # Check RAG API
    if [ -f "$PROJECT_ROOT/rag.pid" ] && ps -p $(cat "$PROJECT_ROOT/rag.pid") > /dev/null 2>&1; then
        rag_running=true
    fi
    
    if $search_running && $rag_running; then
        return 0  # Both running
    else
        return 1  # At least one not running
    fi
}

# Function to start both APIs
start_both() {
    print_status $YELLOW "🚀 Starting La Plata County API Suite..."
    echo ""
    
    # Start Search API first
    print_status $YELLOW "Starting Search API (port 8000)..."
    if ! "$API_SCRIPT" start; then
        print_status $RED "❌ Failed to start Search API"
        return 1
    fi
    
    echo ""
    
    # Wait a moment for search API to fully start
    sleep 3
    
    # Start RAG API
    print_status $YELLOW "Starting RAG API (port 8001)..."
    if ! "$RAG_SCRIPT" start; then
        print_status $RED "❌ Failed to start RAG API"
        print_status $YELLOW "Search API is still running. Use './scripts/api.sh stop' to stop it."
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
    
    # Load model automatically
    print_status $YELLOW "Loading RAG model..."
    local model_id="mlx-community/Llama-3.1-8B-Instruct-4bit"
    local model_response=$(curl -s -X POST "http://localhost:8001/rag/model/load" \
        -H 'Content-Type: application/json' \
        -d "{\"model_id\":\"$model_id\"}" 2>/dev/null)
    
    if [[ $model_response == *'"success":true'* ]] || [[ $model_response == *'"model_loaded":true'* ]]; then
        print_status $GREEN "✅ Model loaded successfully: $model_id"
    else
        print_status $YELLOW "⚠️  Model load may have issues. Check with: curl http://localhost:8001/rag/health"
        echo "   You can manually load a model with:"
        echo "   curl -X POST http://localhost:8001/rag/model/load -H 'Content-Type: application/json' -d '{\"model_id\":\"mlx-community/Llama-3.1-8B-Instruct-4bit\"}'"
    fi
    
    echo ""
    
    # Verify both are running
    if check_both_status; then
        print_status $GREEN "✅ Both APIs started successfully with model loaded!"
        echo ""
        print_status $GREEN "🔍 Search API: http://localhost:8000"
        print_status $GREEN "🤖 RAG API: http://localhost:8001"
        echo ""
        echo "Test commands:"
        echo "  curl \"http://localhost:8000/health\""
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

# Function to stop both APIs
stop_both() {
    print_status $YELLOW "🛑 Stopping La Plata County API Suite..."
    echo ""
    
    # Stop RAG API first
    print_status $YELLOW "Stopping RAG API..."
    "$RAG_SCRIPT" stop
    
    echo ""
    
    # Stop Search API
    print_status $YELLOW "Stopping Search API..."
    "$API_SCRIPT" stop
    
    echo ""
    print_status $GREEN "✅ Both APIs stopped"
}

# Function to restart both APIs
restart_both() {
    print_status $YELLOW "🔄 Restarting La Plata County API Suite..."
    echo ""
    
    stop_both
    sleep 2
    start_both
}

# Function to show status of both APIs
status_both() {
    print_status $YELLOW "📊 La Plata County API Suite Status"
    echo ""
    
    # Search API Status
    print_status $YELLOW "🔍 Search API (port 8000):"
    "$API_SCRIPT" status
    echo ""
    
    # RAG API Status
    print_status $YELLOW "🤖 RAG API (port 8001):"
    "$RAG_SCRIPT" status
    echo ""
    
    # Overall Status
    if check_both_status; then
        print_status $GREEN "✅ Overall Status: Both APIs running"
        echo ""
        echo "Quick tests:"
        echo "  curl \"http://localhost:8000/search/simple?query=building%20permits&num_results=3\""
        echo "  curl \"http://localhost:8001/rag/health\""
    else
        print_status $RED "❌ Overall Status: One or both APIs not running"
        echo ""
        echo "Use './scripts/start_both.sh start' to start both APIs"
    fi
}

# Function to show logs from both APIs
logs_both() {
    print_status $YELLOW "📜 API Logs"
    echo ""
    
    print_status $YELLOW "🔍 Search API Logs:"
    "$API_SCRIPT" logs
    echo ""
    
    print_status $YELLOW "🤖 RAG API Logs:"
    "$RAG_SCRIPT" logs
}

# Function to test both APIs
test_both() {
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
            echo "Load a model with: curl -X POST http://localhost:8001/rag/model/load -H 'Content-Type: application/json' -d '{\"model_id\":\"mlx-community/Llama-3.1-8B-Instruct-4bit\"}'"
        fi
    else
        print_status $RED "❌ RAG API not responding"
    fi
    
    echo ""
    
    # Overall test result
    if check_both_status; then
        print_status $GREEN "✅ Both APIs are operational"
    else
        print_status $RED "❌ One or both APIs have issues"
    fi
}

# Function to show help
show_help() {
    echo "La Plata County API Suite Management Script"
    echo ""
    echo "Manages both Search API (port 8000) and RAG API (port 8001) together"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|test|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start both API servers"
    echo "  stop     - Stop both API servers"
    echo "  restart  - Restart both API servers"
    echo "  status   - Show status of both APIs"
    echo "  logs     - Show logs from both APIs"
    echo "  test     - Test connectivity and functionality of both APIs"
    echo "  help     - Show this help message"
    echo ""
    echo "Individual API management:"
    echo "  ./scripts/api.sh {start|stop|status}     # Search API only"
    echo "  ./scripts/run_rag.sh {start|stop|status} # RAG API only"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start both APIs"
    echo "  $0 status                   # Check if both are running"
    echo "  $0 test                     # Test both APIs"
    echo ""
    echo "Typical workflow:"
    echo "  1. $0 start                 # Start both services"
    echo "  2. $0 test                  # Verify everything works"
    echo "  3. Load RAG model if needed"
    echo "  4. Use APIs for search and Q&A"
}

# Main script logic
case "${1:-help}" in
    start)
        start_both
        ;;
    stop)
        stop_both
        ;;
    restart)
        restart_both
        ;;
    status)
        status_both
        ;;
    logs)
        logs_both
        ;;
    test)
        test_both
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