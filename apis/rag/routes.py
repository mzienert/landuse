from .handlers.health import health_bp
from .handlers.config import config_bp
from .handlers.model import model_bp
from .handlers.answer import answer_bp
from .handlers.stream import stream_bp
from .handlers.index import index_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(health_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(answer_bp)
    app.register_blueprint(stream_bp)
    app.register_blueprint(index_bp)