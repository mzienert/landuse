#!/bin/bash

# La Plata County Search API Startup Script

API_PORT=8000
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_ROOT/api.pid"
LOG_FILE="$PROJECT_ROOT/api.log"

cd "$PROJECT_ROOT"

# Function to check if API is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Running
        else
            rm -f "$PID_FILE"  # Clean up stale PID file
            return 1  # Not running
        fi
    else
        return 1  # Not running
    fi
}

# Function to start the API
start_api() {
    if is_running; then
        echo "API is already running (PID: $(cat $PID_FILE))"
        echo "Use './start_api.sh status' to check or './start_api.sh stop' to stop"
        return 1
    fi
    
    echo "Starting La Plata County Search API..."
    
    # Check if virtual environment exists
    if [ ! -d "env" ]; then
        echo "Error: Virtual environment 'env' not found"
        echo "Please run: python3 -m venv env && source env/bin/activate && pip install -r requirements.txt"
        return 1
    fi
    
    # Check if ChromaDB exists
    if [ ! -d "chroma_db" ]; then
        echo "Error: ChromaDB not found at ./chroma_db"
        echo "Please run: python create_embeddings.py"
        return 1
    fi
    
    # Activate virtual environment and start server
    source env/bin/activate
    
    # Start server in background
    nohup python apis/search/search_api.py > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment to check if it started successfully
    sleep 2
    
    if is_running; then
        echo "✅ API started successfully!"
        echo "   PID: $pid"
        echo "   Port: $API_PORT"
        echo "   URL: http://localhost:$API_PORT"
        echo "   Logs: $LOG_FILE"
        echo ""
        echo "Test with: curl \"http://localhost:$API_PORT/health\""
        return 0
    else
        echo "❌ Failed to start API"
        echo "Check logs: cat $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop the API
stop_api() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "Stopping API (PID: $pid)..."
        kill "$pid"
        
        # Wait for process to stop
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Force killing API process..."
            kill -9 "$pid"
        fi
        
        rm -f "$PID_FILE"
        echo "✅ API stopped"
    else
        echo "API is not running"
    fi
}

# Function to restart the API
restart_api() {
    echo "Restarting API..."
    stop_api
    sleep 1
    start_api
}

# Function to show API status
status_api() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "✅ API is running"
        echo "   PID: $pid"
        echo "   Port: $API_PORT"
        echo "   URL: http://localhost:$API_PORT"
        
        # Test if API is responding
        if command -v curl > /dev/null; then
            echo "   Testing connectivity..."
            if curl -s --connect-timeout 3 "http://localhost:$API_PORT/health" > /dev/null; then
                echo "   Status: Responding ✅"
            else
                echo "   Status: Not responding ❌"
            fi
        fi
    else
        echo "❌ API is not running"
    fi
}

# Function to show logs
logs_api() {
    if [ -f "$LOG_FILE" ]; then
        echo "=== API Logs (last 50 lines) ==="
        tail -50 "$LOG_FILE"
    else
        echo "No log file found at $LOG_FILE"
    fi
}

# Function to show help
show_help() {
    echo "La Plata County Search API Management Script"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the API server"
    echo "  stop     - Stop the API server"
    echo "  restart  - Restart the API server"
    echo "  status   - Show API status and test connectivity"
    echo "  logs     - Show recent API logs"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                              # Start the API"
    echo "  $0 status                             # Check if running"
    echo "  curl \"http://localhost:8000/health\"   # Test API"
}

# Main script logic
case "${1:-help}" in
    start)
        start_api
        ;;
    stop)
        stop_api
        ;;
    restart)
        restart_api
        ;;
    status)
        status_api
        ;;
    logs)
        logs_api
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