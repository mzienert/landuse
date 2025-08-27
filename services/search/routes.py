from .handlers.collections import collections_bp
from .handlers.health import health_bp
from .handlers.search import search_bp
from .handlers.index import index_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(collections_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(index_bp)