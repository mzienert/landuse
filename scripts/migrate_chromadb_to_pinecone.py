#!/usr/bin/env python3
"""
Migration script to move La Plata County code data from ChromaDB to Pinecone.

This script:
1. Connects to the existing ChromaDB collection
2. Extracts all vectors, metadata, and IDs
3. Uploads them to a Pinecone index
4. Validates the migration

Usage:
    python migrate_chromadb_to_pinecone.py

Environment Variables Required:
    PINECONE_API_KEY: Your Pinecone API key
    PINECONE_ENVIRONMENT: Your Pinecone environment (e.g., 'us-west-2-aws')
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
import logging

# Add the services directory to the path so we can import the search config
sys.path.append(str(Path(__file__).parent.parent / 'services' / 'search'))

try:
    import chromadb
    from pinecone import Pinecone, ServerlessSpec
except ImportError as e:
    print(f"Missing required packages. Install with:")
    print(f"pip install chromadb pinecone-client")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChromaToPinecone:
    def __init__(self, chroma_db_path: str = None, pinecone_api_key: str = None, pinecone_environment: str = None):
        self.chroma_db_path = chroma_db_path or '../chroma_db'
        self.pinecone_api_key = pinecone_api_key or os.getenv('PINECONE_API_KEY')
        self.pinecone_environment = pinecone_environment or os.getenv('PINECONE_ENVIRONMENT')
        
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        self.chroma_client = None
        self.pinecone_client = None
        self.index = None

    def connect_to_chromadb(self) -> bool:
        """Connect to the existing ChromaDB database"""
        try:
            logger.info(f"Connecting to ChromaDB at {self.chroma_db_path}")
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_db_path)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            return False

    def connect_to_pinecone(self) -> bool:
        """Initialize Pinecone client"""
        try:
            logger.info("Connecting to Pinecone")
            self.pinecone_client = Pinecone(api_key=self.pinecone_api_key)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
            return False

    def get_chroma_collection(self, collection_name: str = 'la_plata_county_code'):
        """Get the ChromaDB collection"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            doc_count = collection.count()
            logger.info(f"Found ChromaDB collection '{collection_name}' with {doc_count} documents")
            return collection
        except Exception as e:
            logger.error(f"Failed to get collection '{collection_name}': {e}")
            return None

    def create_pinecone_index(self, index_name: str = 'la-plata-county-code', dimension: int = 1024):
        """Create Pinecone index if it doesn't exist"""
        try:
            # Check if index already exists
            existing_indexes = self.pinecone_client.list_indexes()
            index_names = [idx['name'] for idx in existing_indexes]
            
            if index_name in index_names:
                logger.info(f"Pinecone index '{index_name}' already exists")
                self.index = self.pinecone_client.Index(index_name)
                stats = self.index.describe_index_stats()
                logger.info(f"Existing index stats: {stats['total_vector_count']} vectors")
                return True
            
            # Create new index
            logger.info(f"Creating Pinecone index '{index_name}' with {dimension} dimensions")
            self.pinecone_client.create_index(
                name=index_name,
                dimension=dimension,
                metric='cosine',  # ChromaDB uses cosine distance by default
                spec=ServerlessSpec(
                    cloud='aws',
                    region=self.pinecone_environment or 'us-west-2'
                )
            )
            
            # Wait for index to be ready
            import time
            logger.info("Waiting for index to be ready...")
            time.sleep(10)
            
            self.index = self.pinecone_client.Index(index_name)
            logger.info(f"Pinecone index '{index_name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Pinecone index: {e}")
            return False

    def extract_from_chromadb(self, collection) -> List[Dict[str, Any]]:
        """Extract all data from ChromaDB collection"""
        try:
            # Get all data from ChromaDB
            logger.info("Extracting data from ChromaDB...")
            
            # ChromaDB get() with no IDs returns all documents
            results = collection.get(
                include=['embeddings', 'metadatas', 'documents']
            )
            
            total_docs = len(results['ids'])
            logger.info(f"Extracted {total_docs} documents from ChromaDB")
            
            # Convert to format suitable for Pinecone
            vectors_to_upsert = []
            for i in range(total_docs):
                vector_data = {
                    'id': results['ids'][i],
                    'values': results['embeddings'][i],
                    'metadata': results['metadatas'][i] if results['metadatas'] else {}
                }
                vectors_to_upsert.append(vector_data)
            
            return vectors_to_upsert
            
        except Exception as e:
            logger.error(f"Failed to extract data from ChromaDB: {e}")
            return []

    def upload_to_pinecone(self, vectors: List[Dict[str, Any]], batch_size: int = 100):
        """Upload vectors to Pinecone in batches"""
        try:
            total_vectors = len(vectors)
            logger.info(f"Uploading {total_vectors} vectors to Pinecone in batches of {batch_size}")
            
            for i in tqdm(range(0, total_vectors, batch_size), desc="Uploading batches"):
                batch = vectors[i:i + batch_size]
                
                # Prepare batch for Pinecone
                batch_data = []
                for vector in batch:
                    # Pinecone has limits on metadata size, so we might need to truncate large text
                    metadata = vector['metadata'].copy()
                    if 'text' in metadata and len(metadata['text']) > 40000:  # Pinecone metadata limit
                        metadata['text_truncated'] = True
                        metadata['original_text_length'] = len(metadata['text'])
                        metadata['text'] = metadata['text'][:40000]  # Keep first 40k chars
                    
                    batch_data.append({
                        'id': vector['id'],
                        'values': vector['values'],
                        'metadata': metadata
                    })
                
                # Upload batch to Pinecone
                self.index.upsert(vectors=batch_data)
                
            logger.info(f"Successfully uploaded {total_vectors} vectors to Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload to Pinecone: {e}")
            return False

    def validate_migration(self, original_count: int):
        """Validate that the migration was successful"""
        try:
            # Get Pinecone index stats
            stats = self.index.describe_index_stats()
            pinecone_count = stats['total_vector_count']
            
            logger.info(f"Migration validation:")
            logger.info(f"  ChromaDB documents: {original_count}")
            logger.info(f"  Pinecone vectors: {pinecone_count}")
            
            if pinecone_count == original_count:
                logger.info("✅ Migration validation successful - counts match!")
                return True
            else:
                logger.warning(f"⚠️  Count mismatch: ChromaDB={original_count}, Pinecone={pinecone_count}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to validate migration: {e}")
            return False

    def test_search(self):
        """Test search functionality on migrated data"""
        try:
            # We would need the embedding model to create query embeddings
            # For now, just check if we can query the index
            logger.info(f"Testing search functionality...")
            stats = self.index.describe_index_stats()
            if stats['total_vector_count'] > 0:
                logger.info("✅ Index is ready for queries")
                # Note: Actual search testing would require the embedding model
                logger.info("Note: Full search testing requires embedding model integration")
                return True
            else:
                logger.error("❌ Index is empty")
                return False
                
        except Exception as e:
            logger.error(f"Failed to test search: {e}")
            return False

    def run_migration(self, collection_name: str = 'la_plata_county_code', index_name: str = 'la-plata-county-code'):
        """Run the complete migration process"""
        logger.info("🚀 Starting ChromaDB to Pinecone migration")
        
        # Step 1: Connect to ChromaDB
        if not self.connect_to_chromadb():
            return False
            
        # Step 2: Connect to Pinecone
        if not self.connect_to_pinecone():
            return False
            
        # Step 3: Get ChromaDB collection
        collection = self.get_chroma_collection(collection_name)
        if not collection:
            return False
            
        original_count = collection.count()
        
        # Step 4: Create Pinecone index (default 1024 dimensions for e5-large-v2)
        if not self.create_pinecone_index(index_name, dimension=1024):
            return False
            
        # Step 5: Extract data from ChromaDB
        vectors = self.extract_from_chromadb(collection)
        if not vectors:
            return False
            
        # Step 6: Upload to Pinecone
        if not self.upload_to_pinecone(vectors):
            return False
            
        # Step 7: Validate migration
        if not self.validate_migration(original_count):
            return False
            
        # Step 8: Test search
        self.test_search()
        
        logger.info("✅ Migration completed successfully!")
        logger.info(f"📊 Migrated {len(vectors)} vectors from ChromaDB to Pinecone")
        logger.info(f"🔍 Index '{index_name}' is ready for use")
        
        return True


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Migrate data from ChromaDB to Pinecone",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate county code collection (default)
  python migrate_chromadb_to_pinecone.py
  
  # Specify custom collection and index names
  python migrate_chromadb_to_pinecone.py \\
    --chroma-collection la_plata_assessor \\
    --pinecone-index la-plata-assessor-data
  
  # Use custom ChromaDB path
  python migrate_chromadb_to_pinecone.py \\
    --chroma-path /path/to/custom/chroma_db
        """
    )
    
    parser.add_argument(
        '--chroma-collection',
        default='la_plata_county_code',
        help='ChromaDB collection name to migrate from (default: la_plata_county_code)'
    )
    
    parser.add_argument(
        '--pinecone-index', 
        default='la-plata-county-code',
        help='Pinecone index name to create/migrate to (default: la-plata-county-code)'
    )
    
    parser.add_argument(
        '--chroma-path',
        default='../chroma_db',
        help='Path to ChromaDB database (default: ../chroma_db)'
    )
    
    parser.add_argument(
        '--dimension',
        type=int,
        default=1024,
        help='Vector dimension for Pinecone index (default: 1024)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for uploading to Pinecone (default: 100)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without actually doing it'
    )
    
    return parser.parse_args()


def main():
    """Main migration function"""
    args = parse_arguments()
    
    print("🔄 ChromaDB → Pinecone Migration")
    print("=" * 50)
    print(f"📁 ChromaDB path: {args.chroma_path}")
    print(f"📚 ChromaDB collection: {args.chroma_collection}")
    print(f"🎯 Pinecone index: {args.pinecone_index}")
    print(f"📏 Vector dimensions: {args.dimension}")
    print(f"📦 Batch size: {args.batch_size}")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No data will be migrated")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv('PINECONE_API_KEY')
    if not api_key:
        print("❌ Error: PINECONE_API_KEY environment variable not set")
        print("Please set your Pinecone API key:")
        print("export PINECONE_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    environment = os.getenv('PINECONE_ENVIRONMENT')
    if environment:
        print(f"🌍 Using Pinecone environment: {environment}")
    else:
        print("🌍 Using default Pinecone environment: us-west-2")
    
    # Initialize migrator
    migrator = ChromaToPinecone(chroma_db_path=args.chroma_path)
    
    if args.dry_run:
        # Dry run - just check connections and show what would be migrated
        print("\n🔍 DRY RUN: Checking connections and data...")
        
        if not migrator.connect_to_chromadb():
            sys.exit(1)
        if not migrator.connect_to_pinecone():
            sys.exit(1)
            
        collection = migrator.get_chroma_collection(args.chroma_collection)
        if not collection:
            sys.exit(1)
            
        doc_count = collection.count()
        print(f"✅ Would migrate {doc_count} documents")
        print(f"✅ Would create/use Pinecone index: {args.pinecone_index}")
        print("🔍 Dry run completed - no data was migrated")
        return
    
    # Run actual migration
    success = migrator.run_migration(
        collection_name=args.chroma_collection,
        index_name=args.pinecone_index
    )
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("Next steps:")
        print("1. Update search service configuration to use Pinecone")
        print("2. Test search functionality with the new Pinecone index")
        print("3. Consider backing up ChromaDB data before removing it")
    else:
        print("\n❌ Migration failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()