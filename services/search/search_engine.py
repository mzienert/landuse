import chromadb
from sentence_transformers import SentenceTransformer
import logging
from .config import AVAILABLE_COLLECTIONS

logger = logging.getLogger(__name__)

class SearchEngine:
    def __init__(self):
        self.models = {}
        self.collections = {}
        self.client = None

    def initialize(self):
        """Initialize sentence transformer models and ChromaDB connections"""
        try:
            logger.info("Connecting to ChromaDB...")
            self.client = chromadb.PersistentClient(path="./chroma_db")
            
            # Initialize each collection and its corresponding model
            for collection_name, config in AVAILABLE_COLLECTIONS.items():
                try:
                    # Load model if not already loaded
                    model_name = config['model']
                    if model_name not in self.models:
                        logger.info(f"Loading model: {model_name}")
                        self.models[model_name] = SentenceTransformer(model_name)
                        logger.info(f"Model loaded: {model_name} ({config['dimensions']} dimensions)")
                    
                    # Connect to collection
                    collection = self.client.get_collection(collection_name)
                    self.collections[collection_name] = collection
                    logger.info(f"Connected to collection '{collection_name}': {collection.count()} documents")
                    
                except Exception as e:
                    logger.warning(f"Could not initialize collection '{collection_name}': {e}")
                    continue
            
            if self.collections:
                logger.info(f"Successfully initialized {len(self.collections)} collections")
                return True
            else:
                logger.error("No collections could be initialized")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing search system: {e}")
            return False

    def search(self, query, collection_name='la_plata_county_code', num_results=5):
        """Perform semantic search on the specified collection"""
        if not self.collections or collection_name not in self.collections:
            raise Exception(f"Collection '{collection_name}' not available")
        
        if collection_name not in AVAILABLE_COLLECTIONS:
            raise Exception(f"Unknown collection: {collection_name}")
        
        # Get the appropriate model and collection
        config = AVAILABLE_COLLECTIONS[collection_name]
        model_name = config['model']
        
        if model_name not in self.models:
            raise Exception(f"Model '{model_name}' not loaded")
        
        model = self.models[model_name]
        collection = self.collections[collection_name]
        
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

    def get_collection_info(self):
        """Get available collections and their info"""
        collection_info = {}
        for collection_name, config in AVAILABLE_COLLECTIONS.items():
            collection_info[collection_name] = {
                'name': config['name'],
                'description': config['description'],
                'model': config['model'],
                'dimensions': config['dimensions'],
                'available': collection_name in self.collections,
                'document_count': self.collections[collection_name].count() if collection_name in self.collections else 0
            }
        
        return {
            'collections': collection_info,
            'total_collections': len(collection_info),
            'available_collections': len(self.collections)
        }

    def get_health_status(self):
        """Get health check information"""
        total_documents = sum(collection.count() for collection in self.collections.values())
        
        return {
            'status': 'healthy',
            'models_loaded': len(self.models),
            'collections_connected': len(self.collections),
            'total_documents': total_documents,
            'available_collections': list(self.collections.keys())
        }