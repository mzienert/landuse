from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Tags,
    Duration,
    aws_apigateway as apigw,
    aws_bedrock as bedrock,
    aws_lambda as _lambda,
    aws_iam as iam,
)


class LanduseStack(Stack):
    """
    Main CDK stack for La Plata County RAG System
    
    Infrastructure components:
    - API Gateway for service routing
    - AWS Bedrock for LLM inference
    - Proactive resource tagging for cost analysis
    """
    
    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Apply consistent resource tagging strategy
        self._apply_resource_tags()
        
        # Create Search Lambda function
        self.search_lambda = self._create_search_lambda()
        
        # Create API Gateway with search endpoint
        self.api_gateway = self._create_api_gateway()
        
        # Stub: AWS Bedrock configuration (for later steps)
        self._create_bedrock_resources()
        
    def _apply_resource_tags(self) -> None:
        """Apply broad stack-level tags, specific service tags applied at resource level"""
        Tags.of(self).add("Project", "LaPlataCo-RAG")
        Tags.of(self).add("Environment", self.env_name)

    def _create_search_lambda(self) -> _lambda.Function:
        """Create the search Lambda function"""
        
        # Create Lambda function
        search_lambda = _lambda.Function(
            self, 
            f"SearchLambda-{self.env_name}",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/search"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "ENVIRONMENT": self.env_name,
                "LOG_LEVEL": "INFO"
            },
            function_name=f"landuse-search-{self.env_name}"
        )
        
        # Add resource-level tags for cost tracking
        Tags.of(search_lambda).add("Service", "Search")
        Tags.of(search_lambda).add("Component", "Lambda")
        
        return search_lambda
        
    def _create_api_gateway(self) -> apigw.RestApi:
        """Create API Gateway with search endpoint"""
        
        # Create REST API with explicit stage configuration
        api = apigw.RestApi(
            self,
            f"LanduseAPI-{self.env_name}",
            rest_api_name=f"landuse-api-{self.env_name}",
            description=f"La Plata County RAG API - {self.env_name}",
            deploy_options=apigw.StageOptions(
                stage_name=self.env_name,
                description=f"La Plata County RAG API - {self.env_name} stage"
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )
        
        # Create Lambda integration
        search_integration = apigw.LambdaIntegration(
            self.search_lambda,
            request_templates={"application/json": '{"statusCode": 200}'}
        )
        
        # Add /search resource and methods
        search_resource = api.root.add_resource("search")
        search_resource.add_method("GET", search_integration)
        search_resource.add_method("POST", search_integration)
        
        # Add resource-level tags
        Tags.of(api).add("Service", "Search")
        Tags.of(api).add("Component", "API-Gateway")
        
        # Output the API endpoint URL
        cdk.CfnOutput(
            self,
            f"APIEndpoint-{self.env_name}",
            value=api.url,
            description=f"API Gateway endpoint URL for {self.env_name} environment"
        )
        
        return api
        
    def _create_bedrock_resources(self) -> None:
        """
        Stub: AWS Bedrock configuration for LLM inference service integration
        """
        # Placeholder for Bedrock configuration
        # TODO: Configure Bedrock models and access policies
        pass