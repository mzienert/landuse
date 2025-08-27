from constructs import Construct
from aws_cdk import (
    Tags,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    CfnOutput,
)


class SearchApiGateway(Construct):
    """
    Search API Gateway Construct
    
    Creates an API Gateway REST API for the search service with:
    - Environment-specific naming and stage configuration
    - CORS support for cross-origin requests
    - Lambda integration for /search endpoint
    - GET and POST method support
    - CloudFormation output for endpoint URL
    """
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        env_name: str,
        search_lambda: _lambda.Function,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.search_lambda = search_lambda
        
        # Create the REST API
        self.api = self._create_rest_api()
        
        # Configure Lambda integration
        self.integration = self._create_lambda_integration()
        
        # Add search endpoint
        self._add_search_endpoint()
        
        # Apply resource-level tags
        self._apply_tags()
        
        # Create CloudFormation output
        self._create_output()
    
    def _create_rest_api(self) -> apigw.RestApi:
        """Create the REST API with environment-specific configuration"""
        
        api = apigw.RestApi(
            self,
            "RestApi",
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
        
        return api
    
    def _create_lambda_integration(self) -> apigw.LambdaIntegration:
        """Create Lambda integration for API Gateway"""
        
        integration = apigw.LambdaIntegration(
            self.search_lambda,
            request_templates={"application/json": '{"statusCode": 200}'},
            proxy=True  # Use Lambda proxy integration for full request/response control
        )
        
        return integration
    
    def _add_search_endpoint(self) -> None:
        """Add the /search endpoint with GET and POST methods"""
        
        # Add /search resource
        search_resource = self.api.root.add_resource("search")
        
        # Add methods
        search_resource.add_method("GET", self.integration)
        search_resource.add_method("POST", self.integration)
    
    def _apply_tags(self) -> None:
        """Apply consistent resource-level tags"""
        Tags.of(self.api).add("Service", "Search")
        Tags.of(self.api).add("Component", "API-Gateway")
    
    def _create_output(self) -> None:
        """Create CloudFormation output for the API endpoint"""
        CfnOutput(
            self,
            f"APIEndpoint",
            value=f"{self.api.url}search",
            description=f"Search API endpoint URL for {self.env_name} environment",
            export_name=f"LanduseSearchAPI-{self.env_name}"
        )
    
    def add_resource(self, path: str) -> apigw.Resource:
        """Add a new resource to the API"""
        return self.api.root.add_resource(path)
    
    def add_method(self, resource: apigw.Resource, method: str, integration: apigw.Integration) -> apigw.Method:
        """Add a method to a resource"""
        return resource.add_method(method, integration)
    
    @property
    def api_id(self) -> str:
        """Get the API Gateway ID"""
        return self.api.rest_api_id
    
    @property
    def api_url(self) -> str:
        """Get the API Gateway URL"""
        return self.api.url
    
    @property
    def search_endpoint(self) -> str:
        """Get the full search endpoint URL"""
        return f"{self.api.url}search"