#!/usr/bin/env python3
"""
Search API with Flask Blueprints
- Document search and retrieval functionality
- ChromaDB integration for vector search
- Support for multiple collections

Keep separate from rag_api.py for separation of concerns.
"""

import os
import logging
from .app_factory import create_app

# Create app using factory pattern
app = create_app()

if __name__ == '__main__':
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Get configuration values
    config_name = os.environ.get('FLASK_ENV', 'development')
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 8000)
    debug = app.config.get('DEBUG', True)
    
    # Initialize search system if not already done
    search_engine = app.config['SEARCH_ENGINE']
    if not app.config.get('TESTING', False):
        if not hasattr(search_engine, '_initialized') or not search_engine._initialized:
            if search_engine.initialize():
                logger.info("Search system initialized successfully")
            else:
                logger.error("Failed to initialize search system. Starting anyway...")
    
    logger.info(f"Starting Flask server in {config_name} mode...")
    app.run(host=host, port=port, debug=debug)