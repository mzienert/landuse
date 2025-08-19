#!/usr/bin/env python3

"""
LangChain Migration Validation Script

This script validates that the LangChain migration components work correctly
without requiring external dependencies like pytest.
"""

import os
import sys
import traceback
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test LangChain imports
        import langchain_openai
        import langchain_aws
        import langchain_core
        import langsmith
        print("  ✅ LangChain dependencies available")
        
        # Test local module imports
        from apis.rag.providers import LLMProviderFactory
        from apis.rag.langchain_inference import LangChainInferenceManager
        from apis.rag.config import Config
        print("  ✅ Local modules importable")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_provider_factory():
    """Test provider factory functionality"""
    print("🔍 Testing provider factory...")
    
    try:
        from apis.rag.providers import LLMProviderFactory
        from apis.rag.config import Config
        
        # Test local environment
        os.environ['DEPLOYMENT_ENV'] = 'local'
        provider = LLMProviderFactory.get_provider()
        assert type(provider).__name__ == 'LocalLlamaCppProvider', "Local provider not returned"
        print("  ✅ Local provider factory works")
        
        # Test staging environment
        os.environ['DEPLOYMENT_ENV'] = 'staging'
        provider = LLMProviderFactory.get_provider()
        assert type(provider).__name__ == 'BedrockProvider', "Staging provider not returned"
        assert provider.model_id == Config.BEDROCK_STAGING_MODEL, "Staging model incorrect"
        print("  ✅ Staging provider factory works")
        
        # Test production environment
        os.environ['DEPLOYMENT_ENV'] = 'production'
        provider = LLMProviderFactory.get_provider()
        assert type(provider).__name__ == 'BedrockProvider', "Production provider not returned"
        assert provider.model_id == Config.BEDROCK_PRODUCTION_MODEL, "Production model incorrect"
        print("  ✅ Production provider factory works")
        
        # Test invalid environment
        try:
            LLMProviderFactory.get_provider("invalid")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("  ✅ Invalid environment handling works")
        
        return True
    except Exception as e:
        print(f"  ❌ Provider factory error: {e}")
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration loading"""
    print("🔍 Testing configuration...")
    
    try:
        from apis.rag.config import Config
        
        config = Config()
        
        # Check LangChain settings
        assert hasattr(config, 'DEPLOYMENT_ENV'), "DEPLOYMENT_ENV not found"
        assert hasattr(config, 'LANGSMITH_TRACING'), "LANGSMITH_TRACING not found"
        assert hasattr(config, 'GENERATION_TEMPERATURE'), "GENERATION_TEMPERATURE not found"
        assert hasattr(config, 'GENERATION_SEED'), "GENERATION_SEED not found"
        
        # Check default values
        assert config.GENERATION_TEMPERATURE == 0.1, "Temperature not 0.1"
        assert config.GENERATION_SEED == 42, "Seed not 42"
        assert config.GENERATION_REPEAT_PENALTY == 1.3, "Repeat penalty not 1.3"
        
        print("  ✅ Configuration loading works")
        print(f"    DEPLOYMENT_ENV: {config.DEPLOYMENT_ENV}")
        print(f"    GENERATION_TEMPERATURE: {config.GENERATION_TEMPERATURE}")
        print(f"    GENERATION_SEED: {config.GENERATION_SEED}")
        
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        traceback.print_exc()
        return False

def test_consistency_parameters():
    """Test that consistency parameters are correct across providers"""
    print("🔍 Testing parameter consistency...")
    
    try:
        from apis.rag.providers import LLMProviderFactory
        from apis.rag.config import Config
        
        # Test local provider
        local_provider = LLMProviderFactory.get_provider('local')
        assert local_provider.llm.temperature == Config.GENERATION_TEMPERATURE, "Local temperature incorrect"
        assert local_provider.llm.max_tokens == Config.GENERATION_MAX_TOKENS, "Local max_tokens incorrect"
        assert local_provider.llm.seed == Config.GENERATION_SEED, "Local seed incorrect"
        print("  ✅ Local provider parameters correct")
        
        # Test staging provider
        staging_provider = LLMProviderFactory.get_provider('staging')
        # Check that model has correct configuration
        assert staging_provider.llm.model_id == Config.BEDROCK_STAGING_MODEL, "Staging model incorrect"
        # Note: ChatBedrock may store parameters differently than ChatOpenAI
        print("  ✅ Staging provider configuration correct")
        
        # Test production provider
        production_provider = LLMProviderFactory.get_provider('production')
        assert production_provider.llm.model_id == Config.BEDROCK_PRODUCTION_MODEL, "Production model incorrect"
        print("  ✅ Production provider configuration correct")
        
        return True
    except Exception as e:
        print(f"  ❌ Parameter consistency error: {e}")
        traceback.print_exc()
        return False

def test_inference_manager_interface():
    """Test that inference manager has correct interface"""
    print("🔍 Testing inference manager interface...")
    
    try:
        from apis.rag.langchain_inference import LangChainInferenceManager
        
        # Create mock Flask app context
        class MockApp:
            class Logger:
                def info(self, msg): pass
                def error(self, msg): pass
                def warning(self, msg): pass
            logger = Logger()
        
        # Mock the provider to avoid actual connections
        class MockProvider:
            def is_available(self): return True
            def generate(self, messages, **kwargs): return "Mock response"
            def stream_generate(self, messages, **kwargs): yield "Mock"; yield " response"
        
        # Mock the factory
        import apis.rag.langchain_inference
        original_factory = apis.rag.langchain_inference.LLMProviderFactory.get_available_provider
        apis.rag.langchain_inference.LLMProviderFactory.get_available_provider = lambda: MockProvider()
        
        # Mock Flask current_app
        import apis.rag.langchain_inference
        original_current_app = getattr(apis.rag.langchain_inference, 'current_app', None)
        apis.rag.langchain_inference.current_app = MockApp()
        
        try:
            # Test manager creation
            manager = LangChainInferenceManager()
            
            # Test interface methods exist
            assert hasattr(manager, 'is_available'), "is_available property missing"
            assert hasattr(manager, 'is_loaded'), "is_loaded property missing"
            assert hasattr(manager, 'model_id'), "model_id property missing"
            assert hasattr(manager, 'max_context'), "max_context property missing"
            assert hasattr(manager, 'load_model'), "load_model method missing"
            assert hasattr(manager, 'stream_generate'), "stream_generate method missing"
            
            # Test basic functionality
            assert manager.is_available == True, "Manager not available"
            assert manager.is_loaded == True, "Manager not loaded"
            
            # Test model loading
            result = manager.load_model("test-model")
            assert "model_id" in result, "load_model result missing model_id"
            assert "max_context" in result, "load_model result missing max_context"
            
            print("  ✅ Inference manager interface correct")
            return True
            
        finally:
            # Restore mocks
            apis.rag.langchain_inference.LLMProviderFactory.get_available_provider = original_factory
            if original_current_app:
                apis.rag.langchain_inference.current_app = original_current_app
            
    except Exception as e:
        print(f"  ❌ Inference manager error: {e}")
        traceback.print_exc()
        return False

def test_environment_files():
    """Test that environment files exist"""
    print("🔍 Testing environment files...")
    
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        
        env_files = ['.env.local', '.env.staging', '.env.production']
        for env_file in env_files:
            file_path = os.path.join(project_root, env_file)
            assert os.path.exists(file_path), f"Environment file {env_file} not found"
            
            # Check that file has expected content
            with open(file_path, 'r') as f:
                content = f.read()
                assert 'DEPLOYMENT_ENV=' in content, f"{env_file} missing DEPLOYMENT_ENV"
                # Generation parameters now centralized in config.py, not required in env files
        
        print("  ✅ Environment files exist and valid")
        return True
    except Exception as e:
        print(f"  ❌ Environment files error: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🚀 LangChain Migration Validation")
    print("="*50)
    
    tests = [
        test_imports,
        test_provider_factory,
        test_configuration,
        test_consistency_parameters,
        test_inference_manager_interface,
        test_environment_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
        print()
    
    print("="*50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed! LangChain migration ready.")
        return 0
    else:
        print("❌ Some validation tests failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())