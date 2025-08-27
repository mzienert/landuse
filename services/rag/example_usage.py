#!/usr/bin/env python3
"""
Example usage of the application factory pattern
Shows how to create different app configurations
"""

from app_factory import create_app

def main():
    print("=== Application Factory Pattern Demo ===\n")
    
    # Create development app
    print("1. Creating development app...")
    dev_app = create_app('development')
    print(f"   - Name: {dev_app.name}")
    print(f"   - Debug: {dev_app.config.get('DEBUG')}")
    print(f"   - Host: {dev_app.config.get('HOST')}")
    print(f"   - Port: {dev_app.config.get('PORT')}")
    print(f"   - Default Model: {dev_app.config.get('DEFAULT_MODEL_ID')}")
    
    # Create testing app
    print("\n2. Creating testing app...")
    test_app = create_app('testing')
    print(f"   - Name: {test_app.name}")
    print(f"   - Debug: {test_app.config.get('DEBUG')}")
    print(f"   - Testing: {test_app.config.get('TESTING')}")
    
    # Create production app
    print("\n3. Creating production app...")
    prod_app = create_app('production')
    print(f"   - Name: {prod_app.name}")
    print(f"   - Debug: {prod_app.config.get('DEBUG')}")
    print(f"   - Host: {prod_app.config.get('HOST')}")
    print(f"   - Port: {prod_app.config.get('PORT')}")
    
    # Show environment variable override
    import os
    os.environ['DEFAULT_MODEL_ID'] = 'custom-model-id'
    print("\n4. Creating app with environment override...")
    custom_app = create_app('development')
    print(f"   - Custom Model ID: {custom_app.config.get('DEFAULT_MODEL_ID')}")
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()