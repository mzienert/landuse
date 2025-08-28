#!/bin/bash

# La Plata County LocalStack Management Script
# Manages LocalStack Docker container for local development

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.localstack.yml"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose not found. Please install Docker Compose first."
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "La Plata County LocalStack Management Script"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|health|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start LocalStack container"
    echo "  stop     - Stop LocalStack container"
    echo "  restart  - Restart LocalStack container"
    echo "  status   - Show LocalStack container status"
    echo "  logs     - Show LocalStack container logs"
    echo "  health   - Check LocalStack health and available services"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start     # Start LocalStack"
    echo "  $0 status    # Check if LocalStack is running"
    echo "  $0 logs      # View LocalStack logs"
    echo "  $0 health    # Check LocalStack service health"
}

# Function to start LocalStack
start_localstack() {
    print_info "🐳 Starting LocalStack..."
    
    check_docker_compose
    
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        print_warning "LocalStack is already running"
        return 0
    fi
    
    docker-compose -f "$COMPOSE_FILE" up -d
    
    if [ $? -eq 0 ]; then
        print_info "Waiting for LocalStack to be ready..."
        
        # Wait for LocalStack to be healthy
        for i in {1..30}; do
            if curl -s http://localhost:4566/_localstack/health &> /dev/null; then
                print_success "LocalStack started successfully!"
                print_info "LocalStack is available at: http://localhost:4566"
                return 0
            fi
            sleep 2
            printf "."
        done
        
        echo ""
        print_error "LocalStack failed to start within 60 seconds"
        print_info "Check logs with: $0 logs"
        return 1
    else
        print_error "Failed to start LocalStack"
        return 1
    fi
}

# Function to stop LocalStack
stop_localstack() {
    print_info "🛑 Stopping LocalStack..."
    
    check_docker_compose
    
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        print_warning "LocalStack is not running"
        return 0
    fi
    
    docker-compose -f "$COMPOSE_FILE" down
    
    if [ $? -eq 0 ]; then
        print_success "LocalStack stopped successfully"
    else
        print_error "Failed to stop LocalStack"
        return 1
    fi
}

# Function to restart LocalStack
restart_localstack() {
    print_info "🔄 Restarting LocalStack..."
    
    stop_localstack
    sleep 2
    start_localstack
}

# Function to show LocalStack status
show_status() {
    print_info "📊 LocalStack Status"
    echo ""
    
    check_docker_compose
    
    # Show container status
    print_info "Container Status:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    
    # Check if LocalStack is responding
    if curl -s http://localhost:4566/_localstack/health &> /dev/null; then
        print_success "LocalStack is running and responding"
        print_info "Available at: http://localhost:4566"
        echo ""
        
        # Show quick health summary
        print_info "Key Services Status:"
        curl -s http://localhost:4566/_localstack/health | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    services = data.get('services', {})
    key_services = ['apigateway', 'lambda', 'cloudformation', 'iam', 'logs', 'sts']
    for service in key_services:
        status = services.get(service, 'unknown')
        emoji = '✅' if status == 'available' else '❌' if status == 'disabled' else '⚠️'
        print(f'  {emoji} {service}: {status}')
except:
    print('  ❌ Could not parse health response')
"
    else
        print_error "LocalStack is not responding"
        print_info "Try starting it with: $0 start"
    fi
}

# Function to show LocalStack logs
show_logs() {
    print_info "📜 LocalStack Logs"
    echo ""
    
    check_docker_compose
    
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "landuse-localstack"; then
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=50
    else
        print_warning "LocalStack container not found"
        print_info "Start LocalStack with: $0 start"
    fi
}

# Function to check LocalStack health
check_health() {
    print_info "🏥 LocalStack Health Check"
    echo ""
    
    if ! curl -s http://localhost:4566/_localstack/health &> /dev/null; then
        print_error "LocalStack is not responding"
        print_info "Check if LocalStack is running: $0 status"
        return 1
    fi
    
    print_success "LocalStack is healthy and responding"
    echo ""
    
    # Show detailed service status
    print_info "Detailed Service Status:"
    curl -s http://localhost:4566/_localstack/health | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    services = data.get('services', {})
    
    # Group services by status
    available = []
    disabled = []
    
    for service, status in sorted(services.items()):
        if status == 'available':
            available.append(service)
        else:
            disabled.append(service)
    
    if available:
        print('  ✅ Available Services:')
        for service in available:
            print(f'     • {service}')
        print()
    
    if disabled:
        print('  ❌ Disabled Services:')
        for service in disabled[:10]:  # Show first 10 to avoid clutter
            print(f'     • {service}')
        if len(disabled) > 10:
            print(f'     ... and {len(disabled) - 10} more')
        print()
    
    print(f'  📊 Total: {len(available)} available, {len(disabled)} disabled')
    print(f'  🔖 Version: {data.get(\"version\", \"unknown\")}')
    print(f'  📦 Edition: {data.get(\"edition\", \"unknown\")}')
    
except Exception as e:
    print(f'  ❌ Could not parse health response: {e}')
"
}

# Main script logic
case "${1:-help}" in
    start)
        start_localstack
        ;;
    stop)
        stop_localstack
        ;;
    restart)
        restart_localstack
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    health)
        check_health
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac