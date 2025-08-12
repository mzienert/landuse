from flask import Blueprint, jsonify, current_app

collections_bp = Blueprint('collections', __name__)

@collections_bp.route('/collections', methods=['GET'])
def get_collections():
    """Get available collections and their info"""
    search_engine = current_app.config['SEARCH_ENGINE']
    return jsonify(search_engine.get_collection_info())