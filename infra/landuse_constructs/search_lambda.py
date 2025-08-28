from constructs import Construct
from aws_cdk import (
    Duration,
    Tags,
    aws_lambda as _lambda,
    aws_iam as iam,
)


class SearchLambda(Construct):
    """
    Search Lambda Function Construct
    
    Creates a Lambda function for the La Plata County search service with:
    - Python 3.11 runtime
    - Configurable timeout and memory
    - Environment-specific naming and tagging
    - IAM role with basic execution permissions
    """
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        env_name: str,
        timeout_seconds: int = 30,
        memory_size: int = 512,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create the Lambda function
        self.function = self._create_function(timeout_seconds, memory_size)
        
        # Apply resource-level tags
        self._apply_tags()
    
    def _create_function(self, timeout_seconds: int, memory_size: int) -> _lambda.Function:
        """Create the Lambda function with specified configuration"""
        
        # For LocalStack dev environment, use inline code to avoid S3 asset issues
        if self.env_name == "dev":
            lambda_code = '''
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

def lambda_handler(event, context):
    """Basic Lambda function handler for La Plata County search service."""
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    environment = os.environ.get('ENVIRONMENT', 'unknown')
    
    response_body = {
        "message": "Hello World from La Plata County Search API",
        "environment": environment,
        "status": "online",
        "step": "1 - Basic Lambda Deployment (LocalStack)",
        "timestamp": context.aws_request_id
    }
    
    http_method = event.get('httpMethod', 'UNKNOWN')
    logger.info(f"Handling {http_method} request")
    
    if http_method == 'POST' and event.get('body'):
        try:
            request_body = json.loads(event['body'])
            response_body['received_data'] = request_body
        except json.JSONDecodeError:
            response_body['received_data'] = event['body']
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        },
        'body': json.dumps(response_body, indent=2)
    }
'''
            code = _lambda.Code.from_inline(lambda_code)
        else:
            # For staging/prod, use asset-based deployment
            code = _lambda.Code.from_asset("lambda/search")
        
        function = _lambda.Function(
            self,
            f"Function",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.lambda_handler",
            code=code,
            timeout=Duration.seconds(timeout_seconds),
            memory_size=memory_size,
            environment={
                "ENVIRONMENT": self.env_name,
                "LOG_LEVEL": "INFO"
            },
            function_name=f"landuse-search-{self.env_name}",
            description=f"La Plata County Search Service - {self.env_name}"
        )
        
        return function
    
    def _apply_tags(self) -> None:
        """Apply consistent resource-level tags"""
        Tags.of(self.function).add("Service", "Search")
        Tags.of(self.function).add("Component", "Lambda")
    
    def add_bedrock_permissions(self) -> None:
        """Add Bedrock permissions to the Lambda function (for future use)"""
        bedrock_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeModel",
                "bedrock:GetModelInvocationLoggingConfiguration"
            ],
            resources=["*"]  # Can be restricted to specific models later
        )
        
        self.function.add_to_role_policy(bedrock_policy)
    
    def add_environment_variable(self, key: str, value: str) -> None:
        """Add an environment variable to the Lambda function"""
        self.function.add_environment(key, value)
    
    @property
    def function_arn(self) -> str:
        """Get the Lambda function ARN"""
        return self.function.function_arn
    
    @property
    def function_name(self) -> str:
        """Get the Lambda function name"""
        return self.function.function_name