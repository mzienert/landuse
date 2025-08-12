#!/usr/bin/env python3
"""
RAG API with Flask Blueprints
- Modular structure with separated concerns
- Health/config endpoints
- RAG answer and streaming endpoints

Keep separate from search_api.py for separation of concerns.
"""

from flask import Flask
from flask_cors import CORS
from .rag_engine import RAGEngine
from .routes import register_blueprints

app = Flask(__name__)
CORS(app)

# Initialize RAG engine
rag_engine = RAGEngine()

# Store RAG engine in app config for blueprints to access
app.config['RAG_ENGINE'] = rag_engine

# Register blueprints
register_blueprints(app)


if __name__ == "__main__":
    # Initialize RAG engine
    rag_engine.initialize()
    # Auto-load default model on startup
    rag_engine.auto_load_default_model()
    app.run(host="0.0.0.0", port=8001, debug=True)


