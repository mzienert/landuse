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
    MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '2500'))
    DEFAULT_TEMPERATURE = float(os.environ.get('DEFAULT_TEMPERATURE', '0.2'))
    DEFAULT_TOP_P = float(os.environ.get('DEFAULT_TOP_P', '0.9'))
    DEFAULT_NUM_RESULTS = int(os.environ.get('DEFAULT_NUM_RESULTS', '5'))
    
    # Retrieval settings
    DEFAULT_COLLECTION = os.environ.get('DEFAULT_COLLECTION') or 'la_plata_county_code'
    COLLECTIONS = ['la_plata_county_code', 'la_plata_assessor']
    
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
    "version": "0.1.0",
    "model": {
        "default": DEFAULT_MODEL_ID,
        "inference": "llama.cpp external service",
        "format": "GGUF",
        "quantization": "Q4_K_M (4-bit)",
        "context_window": "4K tokens",
    },
    "retrieval": {
        "store": "ChromaDB",
        "collections": ["la_plata_county_code", "la_plata_assessor"],
        "rerank": "heuristic v1 (cosine boost, redundancy penalty, diversity)",
    },
}