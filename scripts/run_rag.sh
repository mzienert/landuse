#!/bin/bash

# RAG API management script (separate from search_api)

API_PORT=8001
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_ROOT/rag.pid"
LOG_FILE="$PROJECT_ROOT/rag.log"

cd "$PROJECT_ROOT"

is_running() {
  if [ -f "$PID_FILE" ]; then
    local pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
      return 0
    else
      rm -f "$PID_FILE"
      return 1
    fi
  else
    return 1
  fi
}

start_api() {
  if is_running; then
    echo "RAG API already running (PID: $(cat $PID_FILE))"
    return 0
  fi

  if [ ! -d "env" ]; then
    echo "Error: Virtual environment 'env' not found"
    echo "Please run: python3 -m venv env && source env/bin/activate && pip install -r requirements.txt (or required deps)"
    return 1
  fi

  source env/bin/activate

  echo "Starting RAG API on port $API_PORT..."
  nohup python -m apis.rag.rag_api > "$LOG_FILE" 2>&1 &
  local pid=$!
  echo "$pid" > "$PID_FILE"
  sleep 2

  if is_running; then
    echo "✅ RAG API started (PID: $pid)"
    echo "URL: http://localhost:$API_PORT"
    echo "Logs: $LOG_FILE"
  else
    echo "❌ Failed to start RAG API"
    echo "Check logs: $LOG_FILE"
  fi
}

stop_api() {
  if is_running; then
    local pid=$(cat "$PID_FILE")
    echo "Stopping RAG API (PID: $pid)..."
    kill "$pid"
    sleep 1
    if ps -p "$pid" > /dev/null 2>&1; then
      echo "Force killing RAG API..."
      kill -9 "$pid"
    fi
    rm -f "$PID_FILE"
    echo "✅ RAG API stopped"
  else
    echo "RAG API is not running"
  fi
}

restart_api() {
  stop_api
  sleep 1
  start_api
}

status_api() {
  if is_running; then
    local pid=$(cat "$PID_FILE")
    echo "✅ RAG API running (PID: $pid)"
    echo "URL: http://localhost:$API_PORT"
    if command -v curl > /dev/null; then
      if curl -s --connect-timeout 3 "http://localhost:$API_PORT/rag/health" > /dev/null; then
        echo "Health: Responding ✅"
      else
        echo "Health: Not responding ❌"
      fi
    fi
  else
    echo "❌ RAG API not running"
  fi
}

logs_api() {
  if [ -f "$LOG_FILE" ]; then
    echo "=== RAG API Logs (last 50 lines) ==="
    tail -50 "$LOG_FILE"
  else
    echo "No log file at $LOG_FILE"
  fi
}

case "${1:-help}" in
  start) start_api ;;
  stop) stop_api ;;
  restart) restart_api ;;
  status) status_api ;;
  logs) logs_api ;;
  help|--help|-h)
    echo "RAG API management"
    echo "Usage: $0 {start|stop|restart|status|logs|help}"
    ;;
  *)
    echo "Unknown command: $1" ;;
esac


