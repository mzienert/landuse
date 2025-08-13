#!/bin/bash

# llama.cpp Inference Service Management Script

LLAMA_PORT=8003
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_ROOT/llama.pid"
LOG_FILE="$PROJECT_ROOT/llama.log"

# Default model settings
DEFAULT_MODEL="Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m"
MODEL_ID="${LLAMA_MODEL_ID:-$DEFAULT_MODEL}"

cd "$PROJECT_ROOT"

# Function to check if llama.cpp server is running
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

# Function to check if llama-server is installed
check_llama_cpp() {
    if ! command -v llama-server > /dev/null; then
        echo "Error: llama-server not found"
        echo "Install with: brew install llama.cpp"
        return 1
    fi
    return 0
}

# Function to start the llama.cpp server
start_llama() {
    if is_running; then
        echo "llama.cpp server is already running (PID: $(cat $PID_FILE))"
        echo "Use './llama.sh status' to check or './llama.sh stop' to stop"
        return 1
    fi
    
    if ! check_llama_cpp; then
        return 1
    fi
    
    echo "Starting llama.cpp inference server..."
    echo "Model: $MODEL_ID"
    echo "Port: $LLAMA_PORT"
    
    # Start llama-server in background
    nohup llama-server \
        -hf "$MODEL_ID" \
        --host 0.0.0.0 \
        --port "$LLAMA_PORT" \
        --ctx-size 4096 \
        --threads 8 \
        > "$LOG_FILE" 2>&1 &
    
    local pid=$!
    
    # Save PID
    echo "$pid" > "$PID_FILE"
    
    echo "Starting up... (this may take a few moments for model download/loading)"
    
    # Wait for server to be ready (up to 60 seconds)
    local count=0
    local ready=false
    while [ $count -lt 60 ]; do
        if curl -s --connect-timeout 2 "http://localhost:$LLAMA_PORT/health" > /dev/null 2>&1; then
            ready=true
            break
        fi
        sleep 2
        count=$((count + 2))
        echo -n "."
    done
    echo ""
    
    if [ "$ready" = true ] && is_running; then
        echo "✅ llama.cpp server started successfully!"
        echo "   PID: $pid"
        echo "   Port: $LLAMA_PORT"
        echo "   URL: http://localhost:$LLAMA_PORT"
        echo "   Model: $MODEL_ID"
        echo "   Logs: $LOG_FILE"
        echo ""
        echo "Test with: curl \"http://localhost:$LLAMA_PORT/health\""
        return 0
    else
        echo "❌ Failed to start llama.cpp server"
        echo "Check logs: cat $LOG_FILE"
        if [ -f "$PID_FILE" ]; then
            local pid=$(cat "$PID_FILE")
            kill "$pid" 2>/dev/null
            rm -f "$PID_FILE"
        fi
        return 1
    fi
}

# Function to stop the llama.cpp server
stop_llama() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "Stopping llama.cpp server (PID: $pid)..."
        kill "$pid"
        
        # Wait for process to stop
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Force killing llama.cpp server..."
            kill -9 "$pid"
        fi
        
        rm -f "$PID_FILE"
        echo "✅ llama.cpp server stopped"
    else
        echo "llama.cpp server is not running"
    fi
}

# Function to restart the llama.cpp server
restart_llama() {
    echo "Restarting llama.cpp server..."
    stop_llama
    sleep 2
    start_llama
}

# Function to show llama.cpp server status
status_llama() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "✅ llama.cpp server is running"
        echo "   PID: $pid"
        echo "   Port: $LLAMA_PORT"
        echo "   URL: http://localhost:$LLAMA_PORT"
        echo "   Model: $MODEL_ID"
        
        # Test if server is responding
        if command -v curl > /dev/null; then
            echo "   Testing connectivity..."
            if curl -s --connect-timeout 3 "http://localhost:$LLAMA_PORT/health" > /dev/null; then
                echo "   Status: Responding ✅"
                
                # Test completion endpoint
                echo "   Testing completion..."
                local test_response=$(curl -s --connect-timeout 5 -X POST "http://localhost:$LLAMA_PORT/completion" \
                    -H "Content-Type: application/json" \
                    -d '{"prompt":"Hello", "n_predict":5}' 2>/dev/null)
                
                if [ $? -eq 0 ] && [ -n "$test_response" ]; then
                    echo "   Completion: Working ✅"
                else
                    echo "   Completion: Not responding ❌"
                fi
            else
                echo "   Status: Not responding ❌"
            fi
        fi
    else
        echo "❌ llama.cpp server is not running"
    fi
}

# Function to show logs
logs_llama() {
    if [ -f "$LOG_FILE" ]; then
        echo "=== llama.cpp Server Logs (last 50 lines) ==="
        tail -50 "$LOG_FILE"
    else
        echo "No log file found at $LOG_FILE"
    fi
}

# Function to change model
load_model() {
    local new_model="$1"
    if [ -z "$new_model" ]; then
        echo "Error: Model ID required"
        echo "Example: $0 load Qwen/Qwen2.5-7B-Instruct-GGUF:q4_k_m"
        return 1
    fi
    
    echo "Loading model: $new_model"
    export LLAMA_MODEL_ID="$new_model"
    
    if is_running; then
        echo "Restarting server with new model..."
        restart_llama
    else
        echo "Starting server with model..."
        start_llama
    fi
}

# Function to show help
show_help() {
    echo "llama.cpp Inference Service Management Script"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|load|help}"
    echo ""
    echo "Commands:"
    echo "  start            - Start the llama.cpp server"
    echo "  stop             - Stop the llama.cpp server"
    echo "  restart          - Restart the llama.cpp server"
    echo "  status           - Show server status and test connectivity"
    echo "  logs             - Show recent server logs"
    echo "  load <model-id>  - Load a different model (restarts server)"
    echo "  help             - Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  LLAMA_MODEL_ID   - Override default model"
    echo ""
    echo "Default Model: $DEFAULT_MODEL"
    echo "Current Model: $MODEL_ID"
    echo ""
    echo "Examples:"
    echo "  $0 start                                    # Start server"
    echo "  $0 status                                   # Check status"
    echo "  $0 load Qwen/Qwen2.5-7B-Instruct-GGUF:q4_k_m  # Load different model"
    echo "  curl \"http://localhost:8003/health\"         # Test server"
}

# Main script logic
case "${1:-help}" in
    start)
        start_llama
        ;;
    stop)
        stop_llama
        ;;
    restart)
        restart_llama
        ;;
    status)
        status_llama
        ;;
    logs)
        logs_llama
        ;;
    load)
        load_model "$2"
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