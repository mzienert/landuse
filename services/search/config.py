import os

# Configuration for the search API

AVAILABLE_COLLECTIONS = {
    'la_plata_county_code': {
        'name': 'Land Use Code',
        'model': 'intfloat/e5-large-v2',
        'dimensions': 1024,
        'description': 'La Plata County Land Use Code regulations'
    },
    'la_plata_assessor': {
        'name': 'Property Assessor Data',
        'model': 'intfloat/e5-large-v2',
        'dimensions': 1024,
        'description': 'Property assessment and ownership data'
    }
}

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Search Engine settings
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL') or 'intfloat/e5-large-v2'
    CHROMA_DB_PATH = os.environ.get('CHROMA_DB_PATH') or './chroma_db'
    
    # API settings
    DEFAULT_SEARCH_LIMIT = int(os.environ.get('DEFAULT_SEARCH_LIMIT', '10'))
    MAX_SEARCH_LIMIT = int(os.environ.get('MAX_SEARCH_LIMIT', '50'))
    
    # Collections
    AVAILABLE_COLLECTIONS = AVAILABLE_COLLECTIONS
    
    @staticmethod
    def init_app(app):
        """Initialize app with config-specific settings"""
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 8000

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    # Use in-memory or test-specific database path
    CHROMA_DB_PATH = ':memory:'
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', '8000'))
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/search_api.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Search API startup')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}