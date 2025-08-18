#!/bin/bash

# Convenient wrapper for starting services with environment switching
# Usage: ./scripts/start_with_env.sh [local|staging|production] [start|stop|restart|status]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ENV=${1:-local}
COMMAND=${2:-start}

if [[ ! "$ENV" =~ ^(local|staging|production)$ ]]; then
    echo "Error: Invalid environment. Use: local, staging, or production"
    echo ""
    echo "Usage: $0 [local|staging|production] [start|stop|restart|status]"
    echo ""
    echo "Examples:"
    echo "  $0 local start      # Start with local environment (default)"
    echo "  $0 staging start    # Start with staging environment"
    echo "  $0 production start # Start with production environment"
    echo "  $0 local stop       # Stop services"
    echo "  $0 staging status   # Check status"
    exit 1
fi

cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔧 Setting up $ENV environment...${NC}"

# Switch environment
if ! ./scripts/switch_env.sh "$ENV"; then
    echo "Failed to switch environment"
    exit 1
fi

echo ""
echo -e "${YELLOW}🚀 Running command: $COMMAND${NC}"

# Export environment for the start scripts
export RAG_ENV="$ENV"

# Run the command
case "$COMMAND" in
    start|stop|restart|status|logs|test)
        ./scripts/start_both.sh "$COMMAND"
        ;;
    rag-only)
        ./scripts/run_rag.sh start
        ;;
    help|--help|-h)
        echo "Environment-aware service management"
        echo ""
        echo "Usage: $0 [environment] [command]"
        echo ""
        echo "Environments: local, staging, production"
        echo "Commands: start, stop, restart, status, logs, test, rag-only"
        echo ""
        echo "Examples:"
        echo "  $0 local start       # Start all services locally"
        echo "  $0 staging start     # Start all services with staging config"
        echo "  $0 production rag-only # Start only RAG API in production mode"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Valid commands: start, stop, restart, status, logs, test, rag-only"
        exit 1
        ;;
esac