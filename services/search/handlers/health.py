from flask import Blueprint, jsonify, current_app

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    search_engine = current_app.config['SEARCH_ENGINE']
    return jsonify(search_engine.get_health_status())