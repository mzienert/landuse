#!/usr/bin/env python3
"""
Application factory for Search API
Creates and configures Flask app instances with proper configuration management
"""

import os
import logging
from flask import Flask
from flask_cors import CORS

from .config import config
from .search_engine import SearchEngine
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
    
    # Setup logging if not already configured
    if not app.logger.handlers:
        logging.basicConfig(level=logging.INFO)
    
    # Initialize search engine
    search_engine = SearchEngine()
    
    # Store search engine in app config for blueprints to access
    app.config['SEARCH_ENGINE'] = search_engine
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize search engine after app context is available
    with app.app_context():
        # Only initialize in non-testing mode (unless explicitly configured)
        if not app.config.get('TESTING', False):
            if not search_engine.initialize():
                app.logger.error("Failed to initialize search system")
                # Don't fail completely in factory mode - let the app start
                # This allows for testing and manual initialization
    
    return app