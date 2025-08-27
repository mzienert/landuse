from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Tags,
    aws_bedrock as bedrock,
)

# Import our custom constructs
from landuse_constructs.search_lambda import SearchLambda
from landuse_constructs.search_api_gateway import SearchApiGateway


class LanduseStack(Stack):
    """
    Main CDK stack for La Plata County RAG System
    
    This stack orchestrates the core search infrastructure using custom constructs:
    - SearchLambda: Lambda function for search processing
    - SearchApiGateway: API Gateway with search endpoints
    - AWS Bedrock: LLM inference (configured separately)
    - Proactive resource tagging for cost analysis
    """
    
    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Apply consistent resource tagging strategy
        self._apply_resource_tags()
        
        # Create Search Lambda function using custom construct
        self.search_lambda_construct = SearchLambda(
            self,
            "SearchLambda",
            env_name=env_name
        )
        
        # Create API Gateway using custom construct
        self.api_gateway_construct = SearchApiGateway(
            self,
            "SearchAPI", 
            env_name=env_name,
            search_lambda=self.search_lambda_construct.function
        )
        
        # Stub: AWS Bedrock configuration (for later steps)
        self._create_bedrock_resources()
        
    def _apply_resource_tags(self) -> None:
        """Apply broad stack-level tags, specific service tags applied at resource level"""
        Tags.of(self).add("Project", "LaPlataCo-RAG")
        Tags.of(self).add("Environment", self.env_name)
        
    def _create_bedrock_resources(self) -> None:
        """
        Stub: AWS Bedrock configuration for LLM inference service integration
        """
        # Placeholder for Bedrock configuration
        # TODO: Configure Bedrock models and access policies
        pass
    
    # Convenience properties for accessing construct resources
    @property
    def search_lambda_function(self):
        """Get the search Lambda function"""
        return self.search_lambda_construct.function
    
    @property
    def search_api_gateway(self):
        """Get the search API Gateway"""
        return self.api_gateway_construct.api
    
    @property
    def search_endpoint_url(self):
        """Get the search endpoint URL"""
        return self.api_gateway_construct.search_endpoint