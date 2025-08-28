import json
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

def lambda_handler(event, context):
    """
    Basic Lambda function handler for La Plata County search service.
    
    This is Step 1: Return "Hello World" to verify deployment works.
    """
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Get environment info
    environment = os.environ.get('ENVIRONMENT', 'unknown')
    
    # Basic response for Step 1
    response_body = {
        "message": "Hello World from La Plata County Search API",
        "environment": environment,
        "status": "online",
        "step": "1 - Basic Lambda Deployment (Asset-based + Watch Mode)",
        "timestamp": context.aws_request_id
    }
    
    # Handle both GET and POST requests
    http_method = event.get('httpMethod', 'UNKNOWN')
    logger.info(f"Handling {http_method} request")
    
    # If POST request, include any body data in response
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