#!/usr/bin/env python3
"""
Delete the existing la_plata_assessor collection from ChromaDB
This is needed when changing embedding dimensions (384D -> 768D)
"""

import chromadb
import os

def delete_assessor_collection():
    """Delete the la_plata_assessor collection to prepare for new embeddings"""
    db_path = "./chroma_db"
    
    if not os.path.exists(db_path):
        print(f"❌ ChromaDB directory not found: {db_path}")
        return False
    
    try:
        print("🗂️  Connecting to ChromaDB...")
        client = chromadb.PersistentClient(path=db_path)
        
        # List all collections
        collections = client.list_collections()
        collection_names = [col.name for col in collections]
        
        print(f"📊 Found collections: {collection_names}")
        
        # Check if assessor collection exists
        if 'la_plata_assessor' in collection_names:
            # Get collection info before deletion
            assessor_collection = client.get_collection('la_plata_assessor')
            doc_count = assessor_collection.count()
            
            print(f"🏠 Found 'la_plata_assessor' collection with {doc_count} documents")
            
            # Confirm deletion
            confirm = input("❓ Are you sure you want to delete this collection? (yes/no): ").lower().strip()
            
            if confirm in ['yes', 'y']:
                # Delete the collection
                client.delete_collection('la_plata_assessor')
                print("✅ Successfully deleted 'la_plata_assessor' collection")
                
                # Verify deletion
                remaining_collections = client.list_collections()
                remaining_names = [col.name for col in remaining_collections]
                print(f"📊 Remaining collections: {remaining_names}")
                
                return True
            else:
                print("❌ Deletion cancelled")
                return False
        else:
            print("ℹ️  'la_plata_assessor' collection not found - nothing to delete")
            return True
            
    except Exception as e:
        print(f"❌ Error accessing ChromaDB: {e}")
        return False

def main():
    print("🧹 ChromaDB Collection Cleanup")
    print("=" * 40)
    print("This script will delete the existing 'la_plata_assessor' collection")
    print("to prepare for regenerating embeddings with higher dimensions (768D).")
    print()
    
    success = delete_assessor_collection()
    
    if success:
        print("\n✅ Collection cleanup complete!")
        print("Now you can run: python create_assessor_embeddings.py")
    else:
        print("\n❌ Collection cleanup failed!")

if __name__ == "__main__":
    main()