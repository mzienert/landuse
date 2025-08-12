from flask import Flask
from flask_cors import CORS
import logging
from .search_engine import SearchEngine
from .routes import register_routes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize search engine
search_engine = SearchEngine()

# Register routes
register_routes(app, search_engine)

if __name__ == '__main__':
    # Initialize search system
    if search_engine.initialize():
        logger.info("Starting Flask server...")
        app.run(host='0.0.0.0', port=8000, debug=True)
    else:
        logger.error("Failed to initialize search system. Exiting.")