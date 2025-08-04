from flask import Flask, request, jsonify
from flask_cors import CORS
import chromadb
from sentence_transformers import SentenceTransformer
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables for models and database
models = {}
collections = {}
client = None

# Available collections and their models
AVAILABLE_COLLECTIONS = {
    'la_plata_county_code': {
        'name': 'Land Use Code',
        'model': 'intfloat/e5-large-v2',
        'dimensions': 1024,
        'description': 'La Plata County Land Use Code regulations'
    },
    'la_plata_assessor': {
        'name': 'Property Assessor Data',
        'model': 'sentence-transformers/all-mpnet-base-v2',
        'dimensions': 768,
        'description': 'Property assessment and ownership data'
    }
}

def initialize_search():
    """Initialize sentence transformer models and ChromaDB connections"""
    global models, collections, client
    
    try:
        logger.info("Connecting to ChromaDB...")
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # Initialize each collection and its corresponding model
        for collection_name, config in AVAILABLE_COLLECTIONS.items():
            try:
                # Load model if not already loaded
                model_name = config['model']
                if model_name not in models:
                    logger.info(f"Loading model: {model_name}")
                    models[model_name] = SentenceTransformer(model_name)
                    logger.info(f"Model loaded: {model_name} ({config['dimensions']} dimensions)")
                
                # Connect to collection
                collection = client.get_collection(collection_name)
                collections[collection_name] = collection
                logger.info(f"Connected to collection '{collection_name}': {collection.count()} documents")
                
            except Exception as e:
                logger.warning(f"Could not initialize collection '{collection_name}': {e}")
                continue
        
        if collections:
            logger.info(f"Successfully initialized {len(collections)} collections")
            return True
        else:
            logger.error("No collections could be initialized")
            return False
            
    except Exception as e:
        logger.error(f"Error initializing search system: {e}")
        return False

def perform_search(query, collection_name='la_plata_county_code', num_results=5):
    """Perform semantic search on the specified collection"""
    if not collections or collection_name not in collections:
        raise Exception(f"Collection '{collection_name}' not available")
    
    if collection_name not in AVAILABLE_COLLECTIONS:
        raise Exception(f"Unknown collection: {collection_name}")
    
    # Get the appropriate model and collection
    config = AVAILABLE_COLLECTIONS[collection_name]
    model_name = config['model']
    
    if model_name not in models:
        raise Exception(f"Model '{model_name}' not loaded")
    
    model = models[model_name]
    collection = collections[collection_name]
    
    # Generate embedding for query
    query_embedding = model.encode([query]).tolist()[0]
    
    # Search in ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=num_results
    )
    
    # Format results based on collection type
    formatted_results = []
    if results['ids'][0] and len(results['ids'][0]) > 0:
        for i, item_id in enumerate(results['ids'][0]):
            result = {
                'id': item_id,
                'distance': results['distances'][0][i] if results['distances'][0] else None,
                'content': None,
                'collection': collection_name,
                'collection_name': config['name']
            }
            
            # Extract content from metadata
            if results['metadatas'][0] and i < len(results['metadatas'][0]):
                metadata = results['metadatas'][0][i]
                if metadata and 'text' in metadata:
                    result['content'] = metadata['text']
                    
                    # Add collection-specific metadata
                    if collection_name == 'la_plata_county_code':
                        result['section_id'] = item_id
                        result['full_text_length'] = metadata.get('full_text_length')
                    elif collection_name == 'la_plata_assessor':
                        result['account_number'] = metadata.get('account_number', item_id)
                        result['text_length'] = metadata.get('text_length')
            
            formatted_results.append(result)
    
    return formatted_results

@app.route('/collections', methods=['GET'])
def get_collections():
    """Get available collections and their info"""
    collection_info = {}
    for collection_name, config in AVAILABLE_COLLECTIONS.items():
        collection_info[collection_name] = {
            'name': config['name'],
            'description': config['description'],
            'model': config['model'],
            'dimensions': config['dimensions'],
            'available': collection_name in collections,
            'document_count': collections[collection_name].count() if collection_name in collections else 0
        }
    
    return jsonify({
        'collections': collection_info,
        'total_collections': len(collection_info),
        'available_collections': len(collections)
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    total_documents = sum(collection.count() for collection in collections.values())
    
    return jsonify({
        'status': 'healthy',
        'models_loaded': len(models),
        'collections_connected': len(collections),
        'total_documents': total_documents,
        'available_collections': list(collections.keys())
    })

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
        results = perform_search(query, collection_name, num_results)
        
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
        
        results = perform_search(query, collection_name, num_results)
        
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

if __name__ == '__main__':
    # Initialize search system
    if initialize_search():
        logger.info("Starting Flask server...")
        app.run(host='0.0.0.0', port=8000, debug=True)
    else:
        logger.error("Failed to initialize search system. Exiting.")