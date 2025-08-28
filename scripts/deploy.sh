#!/bin/bash

# La Plata County RAG System - CDK Deployment Script
# Usage: ./deploy.sh <environment> [action]
#   environment: dev, staging, prod
#   action: deploy (default), watch, destroy, diff, synth

set -e  # Exit on any error

# Ensure we're in the infra directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")/infra"
cd "$INFRA_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
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

# Function to show usage
show_usage() {
    echo "Usage: $0 <environment> [action]"
    echo ""
    echo "Environments:"
    echo "  dev      - Deploy to local development (LocalStack)"
    echo "  staging  - Deploy to staging environment"
    echo "  prod     - Deploy to production environment"
    echo ""
    echo "Actions:"
    echo "  deploy   - Deploy the stack (default)"
    echo "  watch    - Start watch mode for rapid development (dev only)"
    echo "  destroy  - Destroy the stack"
    echo "  diff     - Show differences between deployed and local"
    echo "  synth    - Synthesize CloudFormation template"
    echo ""
    echo "Examples:"
    echo "  $0 dev             # Deploy to LocalStack"
    echo "  $0 dev watch       # Start watch mode for rapid development"
    echo "  $0 staging         # Deploy to staging"
    echo "  $0 prod deploy     # Deploy to production"
    echo "  $0 staging destroy # Destroy staging stack"
    echo "  $0 prod diff       # Show prod differences"
}

# Validate arguments
if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    print_error "Invalid number of arguments"
    show_usage
    exit 1
fi

ENVIRONMENT=$1
ACTION=${2:-deploy}

# Validate environment
if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "prod" ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    print_info "Valid environments are: dev, staging, prod"
    show_usage
    exit 1
fi

# Validate action
if [[ "$ACTION" != "deploy" && "$ACTION" != "watch" && "$ACTION" != "destroy" && "$ACTION" != "diff" && "$ACTION" != "synth" ]]; then
    print_error "Invalid action: $ACTION"
    show_usage
    exit 1
fi

# Validate watch action is only for dev
if [ "$ACTION" == "watch" ] && [ "$ENVIRONMENT" != "dev" ]; then
    print_error "Watch mode is only available for dev environment"
    show_usage
    exit 1
fi

# LocalStack setup for dev environment
if [ "$ENVIRONMENT" == "dev" ]; then
    print_info "🐳 Setting up LocalStack for development environment..."
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose not found. Please install Docker Compose first."
        exit 1
    fi
    
    # Start LocalStack if not already running
    COMPOSE_FILE="../docker-compose.localstack.yml"
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        print_info "Starting LocalStack..."
        docker-compose -f "$COMPOSE_FILE" up -d
        
        # Wait for LocalStack to be ready
        print_info "Waiting for LocalStack to be ready..."
        for i in {1..30}; do
            if curl -s http://localhost:4566/_localstack/health &> /dev/null; then
                print_success "LocalStack is ready!"
                break
            fi
            sleep 2
            if [ $i -eq 30 ]; then
                print_error "LocalStack failed to start within 60 seconds"
                exit 1
            fi
        done
    else
        print_success "LocalStack is already running"
    fi
    
    # Set AWS credentials for LocalStack (dummy values) with specialized S3 endpoint
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test
    export AWS_DEFAULT_REGION=us-west-2
    export AWS_ENDPOINT_URL=http://localhost:4566
    export AWS_ENDPOINT_URL_S3=http://s3.localhost.localstack.cloud:4566
    
    print_success "LocalStack environment configured with specialized S3 endpoint"
    echo ""
fi

# Set stack name
STACK_NAME="LanduseStack-$ENVIRONMENT"

print_info "🚀 La Plata County RAG System - CDK $ACTION"
print_info "Environment: $ENVIRONMENT"
print_info "Stack: $STACK_NAME"
echo ""

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    print_error "AWS CDK CLI not found. Please install it first:"
    echo "  npm install -g aws-cdk"
    exit 1
fi

# Check if Python dependencies are installed
if [ ! -d "env" ] && [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    print_warning "No Python virtual environment detected"
    print_info "Make sure you have activated your virtual environment and installed requirements.txt"
fi

# Check AWS credentials (skip for dev/LocalStack)
if [ "$ENVIRONMENT" != "dev" ]; then
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured or invalid"
        print_info "Please configure your AWS credentials using:"
        echo "  aws configure"
        echo "  # or"
        echo "  export AWS_PROFILE=your-profile"
        exit 1
    fi
    
    # Get AWS account info
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region || echo "us-west-2")
    
    print_info "AWS Account: $AWS_ACCOUNT"
    print_info "AWS Region: $AWS_REGION"
else
    # LocalStack dev environment
    AWS_ACCOUNT="000000000000"  # Default LocalStack account ID
    AWS_REGION="us-west-2"
    
    print_info "LocalStack Account: $AWS_ACCOUNT"
    print_info "LocalStack Region: $AWS_REGION"
fi
echo ""

# Acknowledge CDK notices to reduce noise
cdk acknowledge 34892 2>/dev/null || true

# Configure CDK for LocalStack if dev environment
if [ "$ENVIRONMENT" == "dev" ]; then
    export CDK_CLI_OPTIONS="--no-lookups"
    CDK_ENDPOINT_ARGS="--context @aws-cdk/core:target-partitions=[aws,aws-cn] --context @aws-cdk/aws-apigateway:usagePlanKeyOrderInsensitiveId=true"
    
    # Set up LocalStack environment variables for CDK
    export AWS_ENDPOINT_URL=http://localhost:4566
    export LOCALSTACK_HOSTNAME=localhost
    
    print_info "CDK configured for LocalStack deployment"
    echo ""
fi

# Execute the requested action
case $ACTION in
    synth)
        print_info "Synthesizing CloudFormation template..."
        cdk synth --context env=$ENVIRONMENT
        print_success "Synthesis completed"
        ;;
    
    diff)
        print_info "Showing differences..."
        cdk diff --context env=$ENVIRONMENT
        ;;
    
    deploy)
        print_info "Starting deployment..."
        print_warning "This will deploy AWS resources and may incur charges"
        
        # Ask for confirmation in production
        if [ "$ENVIRONMENT" == "prod" ]; then
            echo ""
            read -p "⚠️  You are deploying to PRODUCTION. Are you sure? (yes/no): " confirm
            if [ "$confirm" != "yes" ]; then
                print_info "Deployment cancelled"
                exit 0
            fi
        fi
        
        # Bootstrap if needed (this doesn't need context)
        print_info "Checking CDK bootstrap..."
        if [ "$ENVIRONMENT" == "dev" ]; then
            cdklocal bootstrap --context env=$ENVIRONMENT 2>/dev/null || true
        else
            cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION 2>/dev/null || true
        fi
        
        # Deploy
        print_info "Deploying stack..."
        if [ "$ENVIRONMENT" == "dev" ]; then
            cdklocal deploy --context env=$ENVIRONMENT --require-approval never
        else
            cdk deploy --context env=$ENVIRONMENT --require-approval never
        fi
        
        print_success "Deployment completed!"
        print_info "Getting stack outputs..."
        aws cloudformation describe-stacks \
            --stack-name $STACK_NAME \
            --query 'Stacks[0].Outputs' \
            --output table 2>/dev/null || print_warning "Could not retrieve stack outputs"
        ;;
    
    watch)
        print_info "🚀 Starting watch mode for rapid Lambda development..."
        print_info "This will auto-redeploy your Lambda function on file changes (~1-2 seconds)"
        print_info "Make changes to: lambda/search/lambda_function.py"
        print_info "Test endpoint will be shown in deployment output"
        echo ""
        print_warning "Press Ctrl+C to stop watch mode"
        echo ""
        
        # Initial bootstrap if needed
        print_info "Checking CDK bootstrap..."
        cdklocal bootstrap --context env=$ENVIRONMENT 2>/dev/null || true
        
        # Start watch mode (LocalStack only for now)
        print_info "Starting watch mode..."
        cdklocal deploy --context env=$ENVIRONMENT --hotswap --watch
        ;;
    
    destroy)
        print_error "⚠️  DESTRUCTIVE ACTION: This will delete all resources in $STACK_NAME"
        echo ""
        
        # Show what will be destroyed
        print_info "Resources that will be destroyed:"
        aws cloudformation list-stack-resources \
            --stack-name $STACK_NAME \
            --query 'StackResourceSummaries[].{Type:ResourceType,LogicalId:LogicalResourceId,Status:ResourceStatus}' \
            --output table 2>/dev/null || print_warning "Stack not found or no resources"
        
        echo ""
        read -p "Are you sure you want to destroy the $ENVIRONMENT environment? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            print_info "Destruction cancelled"
            exit 0
        fi
        
        print_info "Destroying stack..."
        cdk destroy --context env=$ENVIRONMENT --force
        print_success "Stack destroyed"
        ;;
esac

print_success "Operation completed successfully!"