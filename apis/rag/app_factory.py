#!/usr/bin/env python3
"""
Application factory for RAG API
Creates and configures Flask app instances with proper configuration management
"""

import os
from flask import Flask
from flask_cors import CORS

from .config import config
from .rag_engine import RAGEngine
from .routes import register_blueprints


def create_app(config_name=None):
    """
    Application factory function
    
    Args:
        config_name: Configuration to use ('development', 'testing', 'production')
                    If None, uses FLASK_ENV environment variable or defaults to 'development'
    
    Returns:
        Flask application instance
    """
    # Determine config name
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize configuration-specific settings
    config[config_name].init_app(app)
    
    # Enable CORS
    CORS(app)
    
    # Initialize RAG engine
    rag_engine = RAGEngine()
    
    # Store RAG engine in app config for blueprints to access
    app.config['RAG_ENGINE'] = rag_engine
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize RAG engine after app context is available
    with app.app_context():
        rag_engine.initialize()
        
        # Auto-load default model on startup (only in development/production)
        if not app.config.get('TESTING', False):
            rag_engine.auto_load_default_model()
    
    return app