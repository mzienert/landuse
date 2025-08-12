from flask import request, jsonify
import logging
from .config import AVAILABLE_COLLECTIONS

logger = logging.getLogger(__name__)

def register_routes(app, search_engine):
    """Register all API routes with the Flask app"""
    
    @app.route('/collections', methods=['GET'])
    def get_collections():
        """Get available collections and their info"""
        return jsonify(search_engine.get_collection_info())

    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify(search_engine.get_health_status())

    @app.route('/search', methods=['GET', 'POST'])
    def search():
        """Search endpoint - accepts both GET and POST requests"""
        try:
            # Get query from request
            if request.method == 'POST':
                data = request.get_json()
                query = data.get('query', '') if data else ''
                num_results = data.get('num_results', 5) if data else 5
                collection_name = data.get('collection', 'la_plata_county_code') if data else 'la_plata_county_code'
            else:  # GET request
                query = request.args.get('query', '')
                num_results = int(request.args.get('num_results', 5))
                collection_name = request.args.get('collection', 'la_plata_county_code')
            
            if not query:
                return jsonify({'error': 'Query parameter is required'}), 400
            
            # Validate collection
            if collection_name not in AVAILABLE_COLLECTIONS:
                return jsonify({'error': f'Invalid collection. Available: {list(AVAILABLE_COLLECTIONS.keys())}'}), 400
            
            # Validate num_results
            num_results = max(1, min(50, num_results))  # Between 1 and 50
            
            logger.info(f"Searching '{collection_name}' for: '{query}' (returning {num_results} results)")
            
            # Perform search
            results = search_engine.search(query, collection_name, num_results)
            
            return jsonify({
                'query': query,
                'collection': collection_name,
                'collection_name': AVAILABLE_COLLECTIONS[collection_name]['name'],
                'num_results': len(results),
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/search/simple', methods=['GET'])
    def simple_search():
        """Simple search endpoint that returns just text content"""
        try:
            query = request.args.get('query', '')
            if not query:
                return jsonify({'error': 'Query parameter is required'}), 400
            
            num_results = int(request.args.get('num_results', 5))
            num_results = max(1, min(10, num_results))
            
            collection_name = request.args.get('collection', 'la_plata_county_code')
            
            # Validate collection
            if collection_name not in AVAILABLE_COLLECTIONS:
                return jsonify({'error': f'Invalid collection. Available: {list(AVAILABLE_COLLECTIONS.keys())}'}), 400
            
            results = search_engine.search(query, collection_name, num_results)
            
            # Simplify response - return full text without truncation
            simple_results = []
            for result in results:
                if result['content']:
                    simple_result = {
                        'text': result['content'],
                        'relevance': f"{1 / (1 + result['distance']):.3f}" if result['distance'] else 'N/A',
                        'collection': collection_name
                    }
                    
                    # Add collection-specific identifier
                    if collection_name == 'la_plata_county_code':
                        simple_result['section'] = result.get('section_id', result['id'])
                    elif collection_name == 'la_plata_assessor':
                        simple_result['account'] = result.get('account_number', result['id'])
                    else:
                        simple_result['id'] = result['id']
                    
                    simple_results.append(simple_result)
            
            return jsonify({
                'query': query,
                'collection': collection_name,
                'collection_name': AVAILABLE_COLLECTIONS[collection_name]['name'],
                'results': simple_results
            })
            
        except Exception as e:
            logger.error(f"Simple search error: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/', methods=['GET'])
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