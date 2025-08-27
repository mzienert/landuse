from flask import Blueprint, request, jsonify, current_app
import logging
from ..config import AVAILABLE_COLLECTIONS

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET', 'POST'])
def search():
    """Search endpoint - accepts both GET and POST requests"""
    search_engine = current_app.config['SEARCH_ENGINE']
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

@search_bp.route('/search/simple', methods=['GET'])
def simple_search():
    """Simple search endpoint that returns just text content"""
    search_engine = current_app.config['SEARCH_ENGINE']
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