#!/usr/bin/env python3
"""
RAG API with Flask Blueprints
- Modular structure with separated concerns
- Health/config endpoints
- RAG answer and streaming endpoints

Keep separate from search_api.py for separation of concerns.
"""

import os
from .app_factory import create_app

# Create app using factory pattern
app = create_app()

if __name__ == "__main__":
    # Get configuration values
    config_name = os.environ.get('FLASK_ENV', 'development')
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 8001)
    debug = app.config.get('DEBUG', True)
    
    app.run(host=host, port=port, debug=debug)


