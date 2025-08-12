from flask import Blueprint, jsonify
from ..config import AVAILABLE_COLLECTIONS

index_bp = Blueprint('index', __name__)

@index_bp.route('/', methods=['GET'])
def index():
    """Basic info about the API"""
    return jsonify({
        'name': 'La Plata County Search API',
        'version': '2.0',
        'description': 'Semantic search across Land Use Code regulations and Property Assessor data',
        'endpoints': {
            '/health': 'Health check and system status',
            '/collections': 'Get available collections and their info',
            '/search?query=YOUR_QUERY&collection=COLLECTION': 'Full search (GET)',
            '/search': 'Full search (POST with JSON)',
            '/search/simple?query=YOUR_QUERY&collection=COLLECTION': 'Simplified search results'
        },
        'collections': list(AVAILABLE_COLLECTIONS.keys()),
        'examples': {
            'land_use': '/search/simple?query=building permits&collection=la_plata_county_code&num_results=3',
            'assessor': '/search/simple?query=Smith family property&collection=la_plata_assessor&num_results=3'
        }
    })