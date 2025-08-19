#!/usr/bin/env python3
"""Test script to validate the new factory structure."""

import sys
import os

# Add the apis directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

def test_inference_factory():
    """Test the inference manager factory public API."""
    print("Testing Inference Manager Factory...")
    
    try:
        from apis.rag.inference import InferenceManagerFactory
        print("✅ Successfully imported InferenceManagerFactory")
        
        # Test getting factory info
        info = InferenceManagerFactory.get_manager_info()
        print(f"✅ Factory info: {info}")
        
        # Test creating a manager
        manager = InferenceManagerFactory.get_available_manager()
        print(f"✅ Created manager: {type(manager).__name__}")
        
        # Test public interface methods exist
        assert hasattr(manager, 'is_available')
        assert hasattr(manager, 'generate') 
        assert hasattr(manager, 'stream_generate')
        print("✅ Manager has all required public interface methods")
        
        # Test manager is available
        assert manager.is_available
        print("✅ Manager reports as available")
        
        return True
        
    except Exception as e:
        print(f"❌ Inference factory test failed: {e}")
        return False

def test_provider_factory():
    """Test the LLM provider factory."""
    print("\nTesting LLM Provider Factory...")
    
    try:
        from apis.rag.providers import LLMProviderFactory
        print("✅ Successfully imported LLMProviderFactory")
        
        # Test creating a local provider
        provider = LLMProviderFactory.get_provider('local')
        print(f"✅ Created local provider: {type(provider).__name__}")
        
        # Test getting available provider
        available_provider = LLMProviderFactory.get_available_provider()
        print(f"✅ Got available provider: {type(available_provider).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider factory test failed: {e}")
        return False

def test_rag_engine_integration():
    """Test RAG engine integration with factory."""
    print("\nTesting RAG Engine Integration...")
    
    try:
        from apis.rag.rag_engine import RAGEngine
        print("✅ Successfully imported RAGEngine")
        
        # Test creating and initializing engine
        engine = RAGEngine()
        engine.initialize()
        print("✅ RAG engine initialized")
        
        if engine.model_mgr:
            print(f"✅ Model manager created: {type(engine.model_mgr).__name__}")
            print(f"✅ Model manager available: {engine.model_mgr.is_available}")
        else:
            print("⚠️  Model manager is None (might be expected in test environment)")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG engine integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing New Factory Structure\n")
    
    tests = [
        test_inference_factory,
        test_provider_factory,
        test_rag_engine_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All factory structure tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)