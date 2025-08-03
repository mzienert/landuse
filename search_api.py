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

# Global variables for model and database
model = None
collection = None

def initialize_search():
    """Initialize the sentence transformer model and ChromaDB connection"""
    global model, collection
    
    try:
        logger.info("Loading sentence transformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Model loaded successfully")
        
        logger.info("Connecting to ChromaDB...")
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection("la_plata_county_code")
        logger.info(f"Connected to database with {collection.count()} documents")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing search: {e}")
        return False

def perform_search(query, num_results=5):
    """Perform semantic search on the query"""
    if not model or not collection:
        raise Exception("Search system not initialized")
    
    # Generate embedding for query
    query_embedding = model.encode([query]).tolist()[0]
    
    # Search in ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=num_results
    )
    
    # Format results
    formatted_results = []
    if results['ids'][0] and len(results['ids'][0]) > 0:
        for i, section_id in enumerate(results['ids'][0]):
            result = {
                'section_id': section_id,
                'distance': results['distances'][0][i] if results['distances'][0] else None,
                'content': None,
                'full_text_length': None
            }
            
            # Extract content from metadata
            if results['metadatas'][0] and i < len(results['metadatas'][0]):
                metadata = results['metadatas'][0][i]
                if metadata and 'text' in metadata:
                    result['content'] = metadata['text']
                    result['full_text_length'] = metadata.get('full_text_length')
            
            formatted_results.append(result)
    
    return formatted_results

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'database_connected': collection is not None,
        'document_count': collection.count() if collection else 0
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
        else:  # GET request
            query = request.args.get('query', '')
            num_results = int(request.args.get('num_results', 5))
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        # Validate num_results
        num_results = max(1, min(50, num_results))  # Between 1 and 50
        
        logger.info(f"Searching for: '{query}' (returning {num_results} results)")
        
        # Perform search
        results = perform_search(query, num_results)
        
        return jsonify({
            'query': query,
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
        
        results = perform_search(query, num_results)
        
        # Simplify response - return full text without truncation
        simple_results = []
        for result in results:
            if result['content']:
                simple_results.append({
                    'section': result['section_id'],
                    'text': result['content'],  # Return full text without truncation
                    'relevance': f"{1 - result['distance']:.3f}" if result['distance'] else 'N/A'
                })
        
        return jsonify({
            'query': query,
            'results': simple_results
        })
        
    except Exception as e:
        logger.error(f"Simple search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """Basic info about the API"""
    return jsonify({
        'name': 'La Plata County Code Search API',
        'version': '1.0',
        'endpoints': {
            '/health': 'Health check',
            '/search?query=YOUR_QUERY': 'Full search (GET)',
            '/search': 'Full search (POST with JSON)',
            '/search/simple?query=YOUR_QUERY': 'Simplified search results'
        },
        'example': '/search?query=building permits&num_results=3'
    })

if __name__ == '__main__':
    # Initialize search system
    if initialize_search():
        logger.info("Starting Flask server...")
        app.run(host='0.0.0.0', port=8000, debug=True)
    else:
        logger.error("Failed to initialize search system. Exiting.")