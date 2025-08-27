#!/usr/bin/env python3
"""
Example usage of the search API application factory pattern
Shows how to create different app configurations
"""

from app_factory import create_app

def main():
    print("=== Search API Factory Pattern Demo ===\n")
    
    # Create development app
    print("1. Creating development app...")
    dev_app = create_app('development')
    print(f"   - Name: {dev_app.name}")
    print(f"   - Debug: {dev_app.config.get('DEBUG')}")
    print(f"   - Host: {dev_app.config.get('HOST')}")
    print(f"   - Port: {dev_app.config.get('PORT')}")
    print(f"   - ChromaDB Path: {dev_app.config.get('CHROMA_DB_PATH')}")
    print(f"   - Collections: {list(dev_app.config.get('AVAILABLE_COLLECTIONS', {}).keys())}")
    
    # Create testing app
    print("\n2. Creating testing app...")
    test_app = create_app('testing')
    print(f"   - Name: {test_app.name}")
    print(f"   - Debug: {test_app.config.get('DEBUG')}")
    print(f"   - Testing: {test_app.config.get('TESTING')}")
    print(f"   - ChromaDB Path: {test_app.config.get('CHROMA_DB_PATH')}")
    
    # Create production app
    print("\n3. Creating production app...")
    prod_app = create_app('production')
    print(f"   - Name: {prod_app.name}")
    print(f"   - Debug: {prod_app.config.get('DEBUG')}")
    print(f"   - Host: {prod_app.config.get('HOST')}")
    print(f"   - Port: {prod_app.config.get('PORT')}")
    
    # Show environment variable override
    import os
    os.environ['EMBEDDING_MODEL'] = 'custom-embedding-model'
    os.environ['DEFAULT_SEARCH_LIMIT'] = '20'
    print("\n4. Creating app with environment override...")
    custom_app = create_app('development')
    print(f"   - Custom Embedding Model: {custom_app.config.get('EMBEDDING_MODEL')}")
    print(f"   - Custom Search Limit: {custom_app.config.get('DEFAULT_SEARCH_LIMIT')}")
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()