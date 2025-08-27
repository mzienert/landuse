import os

# Configuration for the RAG API

DEFAULT_MODEL_ID = "qwen2.5-3b-instruct"  # llama.cpp server model

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # RAG Engine settings
    DEFAULT_MODEL_ID = os.environ.get('DEFAULT_MODEL_ID') or DEFAULT_MODEL_ID
    
    # llama.cpp Inference Service settings
    INFERENCE_SERVICE_URL = os.environ.get('INFERENCE_SERVICE_URL', 'http://localhost:8003')
    
    # API settings
    MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '1200'))  # Good balance of detail vs repetition prevention
    DEFAULT_TEMPERATURE = float(os.environ.get('DEFAULT_TEMPERATURE', '0.3'))  # Slightly higher for less repetition
    DEFAULT_TOP_P = float(os.environ.get('DEFAULT_TOP_P', '0.9'))
    DEFAULT_NUM_RESULTS = int(os.environ.get('DEFAULT_NUM_RESULTS', '4'))  # Fewer sources for faster processing
    
    # Inference service settings
    INFERENCE_SERVICE_TIMEOUT = int(os.environ.get('INFERENCE_SERVICE_TIMEOUT', '300'))  # 5 minutes
    MAX_CHUNK_CHARS = int(os.environ.get('MAX_CHUNK_CHARS', '3000'))  # Limit source text length for better performance
    
    # Retrieval settings
    DEFAULT_COLLECTION = os.environ.get('DEFAULT_COLLECTION') or 'la_plata_county_code'
    COLLECTIONS = ['la_plata_county_code', 'la_plata_assessor']
    
    # LLM Provider Configuration
    DEPLOYMENT_ENV = os.environ.get('DEPLOYMENT_ENV', 'local')
    
    # Local llama.cpp Configuration
    LLAMA_CPP_BASE_URL = os.environ.get('LLAMA_CPP_BASE_URL', 'http://localhost:8003/v1')
    LLAMA_CPP_HEALTH_URL = os.environ.get('LLAMA_CPP_HEALTH_URL', 'http://localhost:8003/health')
    
    # AWS Bedrock Configuration
    AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
    BEDROCK_STAGING_MODEL = os.environ.get('BEDROCK_STAGING_MODEL', 'anthropic.claude-3-haiku-20240307')
    BEDROCK_PRODUCTION_MODEL = os.environ.get('BEDROCK_PRODUCTION_MODEL', 'anthropic.claude-3-sonnet-20240229')
    
    # Generation Parameters (consistent across providers)
    GENERATION_TEMPERATURE = float(os.environ.get('GENERATION_TEMPERATURE', '0.1'))
    GENERATION_MAX_TOKENS = int(os.environ.get('GENERATION_MAX_TOKENS', '1200'))
    GENERATION_SEED = int(os.environ.get('GENERATION_SEED', '42'))
    GENERATION_REPEAT_PENALTY = float(os.environ.get('GENERATION_REPEAT_PENALTY', '1.3'))
    
    # Provider Selection Strategy
    PROVIDER_HEALTH_CHECK_TIMEOUT = int(os.environ.get('PROVIDER_HEALTH_CHECK_TIMEOUT', '5'))
    
    # Inference Manager Configuration
    INFERENCE_MANAGER_TYPE = os.environ.get('INFERENCE_MANAGER_TYPE', 'langchain')
    
    # LangSmith Configuration
    LANGSMITH_API_KEY = os.environ.get('LANGSMITH_API_KEY')
    LANGSMITH_PROJECT = os.environ.get('LANGSMITH_PROJECT', 'landuse-rag')
    LANGSMITH_TRACING = os.environ.get('LANGSMITH_TRACING', 'false').lower() == 'true'
    
    @staticmethod
    def init_app(app):
        """Initialize app with config-specific settings"""
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 8001

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    # Use in-memory or test-specific resources
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', '8001'))
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/rag_api.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('RAG API startup')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Legacy config for backward compatibility
RAG_CONFIG = {
    "service": "RAG API",
    "version": "0.2.0-langchain",
    "model": {
        "default": DEFAULT_MODEL_ID,
        "inference": "LangChain abstraction layer",
        "providers": {
            "local": "llama.cpp HTTP server",
            "staging": "AWS Bedrock Claude Haiku",
            "production": "AWS Bedrock Claude Sonnet"
        },
        "format": "GGUF (local) / API (cloud)",
        "quantization": "Q4_K_M (local only)",
        "context_window": "4K tokens",
        "consistency": "seed=42, temperature=0.1, repeat_penalty=1.3"
    },
    "retrieval": {
        "store": "ChromaDB",
        "collections": ["la_plata_county_code", "la_plata_assessor"],
        "rerank": "heuristic v1 (cosine boost, redundancy penalty, diversity)",
    },
    "observability": {
        "tracing": "LangSmith",
        "monitoring": "Environment-based",
        "logging": "Structured with provider info"
    }
}