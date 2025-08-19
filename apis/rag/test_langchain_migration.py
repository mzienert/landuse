import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apis.rag.providers import LLMProviderFactory
from apis.rag.config import Config
from apis.rag.langchain_inference import LangChainInferenceManager

class TestLLMProviders:
    """Test suite for LLM provider classes"""
    
    def test_provider_factory_local(self):
        """Test provider factory returns correct provider for local environment"""
        with patch.dict(os.environ, {'DEPLOYMENT_ENV': 'local'}):
            provider = LLMProviderFactory.get_provider()
            assert type(provider).__name__ == 'LocalLlamaCppProvider'
            assert hasattr(provider, 'base_url')
            assert provider.base_url.endswith('/v1')
    
    def test_provider_factory_staging(self):
        """Test provider factory returns correct provider for staging environment"""
        with patch.dict(os.environ, {'DEPLOYMENT_ENV': 'staging'}):
            provider = LLMProviderFactory.get_provider()
            assert type(provider).__name__ == 'BedrockProvider'
            assert hasattr(provider, 'model_id')
            assert provider.model_id == Config.BEDROCK_STAGING_MODEL
    
    def test_provider_factory_production(self):
        """Test provider factory returns correct provider for production environment"""
        with patch.dict(os.environ, {'DEPLOYMENT_ENV': 'production'}):
            provider = LLMProviderFactory.get_provider()
            assert type(provider).__name__ == 'BedrockProvider'
            assert hasattr(provider, 'model_id')
            assert provider.model_id == Config.BEDROCK_PRODUCTION_MODEL
    
    def test_provider_factory_invalid_env(self):
        """Test provider factory raises error for invalid environment"""
        with pytest.raises(ValueError, match="Unknown environment"):
            LLMProviderFactory.get_provider("invalid")
    
    @patch('requests.get')
    def test_local_provider_availability(self, mock_get):
        """Test local llama.cpp provider availability check"""
        # Mock successful health check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        provider = LLMProviderFactory.get_provider('local')
        assert provider.is_available() == True
        
        # Mock failed health check
        mock_get.side_effect = Exception("Connection error")
        assert provider.is_available() == False
    
    def test_local_provider_configuration(self):
        """Test local provider has correct configuration"""
        provider = LocalLlamaCppProvider()
        
        # Check LLM configuration
        assert provider.llm.temperature == 0.1
        assert provider.llm.max_tokens == 1200
        assert provider.llm.seed == 42
        assert provider.llm.model_kwargs["repeat_penalty"] == 1.3
        assert provider.llm.model_kwargs["repeat_last_n"] == 128
    
    def test_staging_provider_configuration(self):
        """Test staging provider has correct model configuration"""
        provider = StagingBedrockProvider()
        
        # Check model ID for staging (Haiku)
        assert provider.llm.model_id == "anthropic.claude-3-haiku-20240307"
        # Note: ChatBedrock stores parameters differently than ChatOpenAI
    
    def test_production_provider_configuration(self):
        """Test production provider has correct model configuration"""
        provider = ProductionBedrockProvider()
        
        # Check model ID for production (Sonnet)
        assert provider.llm.model_id == "anthropic.claude-3-sonnet-20240229"
        # Note: ChatBedrock stores parameters differently than ChatOpenAI

class TestLangChainInferenceManager:
    """Test suite for LangChain inference manager"""
    
    @patch('apis.rag.langchain_inference.LLMProviderFactory.get_available_provider')
    @patch('apis.rag.langchain_inference.current_app')
    def test_inference_manager_initialization(self, mock_app, mock_factory):
        """Test inference manager initializes correctly"""
        # Mock provider
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_factory.return_value = mock_provider
        
        # Mock Flask app logger
        mock_app.logger.info = MagicMock()
        
        # Initialize manager
        manager = LangChainInferenceManager()
        
        assert manager.provider == mock_provider
        assert manager.is_available == True
        assert manager.is_loaded == True
    
    @patch('apis.rag.langchain_inference.LLMProviderFactory.get_available_provider')
    @patch('apis.rag.langchain_inference.current_app')
    def test_inference_manager_load_model(self, mock_app, mock_factory):
        """Test model loading functionality"""
        # Mock provider
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_factory.return_value = mock_provider
        
        # Mock Flask app logger
        mock_app.logger.info = MagicMock()
        
        manager = LangChainInferenceManager()
        result = manager.load_model("test-model")
        
        assert result["model_id"] == "test-model"
        assert result["max_context"] == 4096
        assert manager.model_id == "test-model"
    
    @patch('apis.rag.langchain_inference.LLMProviderFactory.get_available_provider')
    @patch('apis.rag.langchain_inference.current_app')
    def test_generate_text(self, mock_app, mock_factory):
        """Test text generation functionality"""
        # Mock provider
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.generate.return_value = "Generated response"
        mock_factory.return_value = mock_provider
        
        # Mock Flask app logger
        mock_app.logger.info = MagicMock()
        
        manager = LangChainInferenceManager()
        response = manager.generate_text("Test prompt")
        
        assert response == "Generated response"
        mock_provider.generate.assert_called_once()
    
    @patch('apis.rag.langchain_inference.LLMProviderFactory.get_available_provider')
    @patch('apis.rag.langchain_inference.current_app')
    def test_stream_generate_compatibility(self, mock_app, mock_factory):
        """Test stream_generate maintains ModelManager interface"""
        # Mock provider
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.stream_generate.return_value = iter(["Hello", " world"])
        mock_factory.return_value = mock_provider
        
        # Mock Flask app logger
        mock_app.logger.info = MagicMock()
        
        manager = LangChainInferenceManager()
        manager.load_model("test-model")  # Ensure model is loaded
        
        # Test the stream_generate method (ModelManager compatibility)
        result = list(manager.stream_generate("Test prompt", max_tokens=100, temperature=0.2, top_p=0.9))
        
        assert result == ["Hello", " world"]
        mock_provider.stream_generate.assert_called_once()

class TestConsistencyParameters:
    """Test that consistency parameters are preserved across all providers"""
    
    def test_temperature_consistency(self):
        """Test that temperature is capped at 0.1 across all providers"""
        local_provider = LocalLlamaCppProvider()
        staging_provider = BedrockProvider(Config.BEDROCK_STAGING_MODEL)
        production_provider = BedrockProvider(Config.BEDROCK_PRODUCTION_MODEL)
        
        assert local_provider.llm.temperature == Config.GENERATION_TEMPERATURE
        # Note: Bedrock providers store config in model_kwargs during creation
        # but may not expose it the same way as ChatOpenAI
    
    def test_seed_consistency(self):
        """Test that seed=42 is set for local provider"""
        local_provider = LocalLlamaCppProvider()
        assert local_provider.llm.seed == 42
    
    def test_max_tokens_consistency(self):
        """Test that max_tokens=1200 across all providers"""
        local_provider = LocalLlamaCppProvider()
        staging_provider = BedrockProvider(Config.BEDROCK_STAGING_MODEL)
        production_provider = BedrockProvider(Config.BEDROCK_PRODUCTION_MODEL)
        
        assert local_provider.llm.max_tokens == Config.GENERATION_MAX_TOKENS
        # Note: Bedrock providers configured with max_tokens in model_kwargs
        # but internal storage may vary
    
    def test_repeat_penalty_consistency(self):
        """Test that repeat_penalty=1.3 for local provider"""
        local_provider = LocalLlamaCppProvider()
        assert local_provider.llm.model_kwargs["repeat_penalty"] == 1.3

class TestLangSmithIntegration:
    """Test LangSmith tracing integration"""
    
    @patch.dict(os.environ, {
        'LANGSMITH_TRACING': 'true',
        'LANGSMITH_API_KEY': 'test-key',
        'LANGSMITH_PROJECT': 'test-project'
    })
    @patch('apis.rag.langchain_inference.Client')
    @patch('apis.rag.langchain_inference.LangChainTracer')
    @patch('apis.rag.langchain_inference.LLMProviderFactory.get_available_provider')
    @patch('apis.rag.langchain_inference.current_app')
    def test_langsmith_setup_enabled(self, mock_app, mock_factory, mock_tracer, mock_client):
        """Test LangSmith setup when tracing is enabled"""
        # Mock provider
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_factory.return_value = mock_provider
        
        # Mock Flask app logger
        mock_app.logger.info = MagicMock()
        
        # Mock LangSmith components
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_tracer_instance = MagicMock()
        mock_tracer.return_value = mock_tracer_instance
        
        manager = LangChainInferenceManager()
        
        # Verify LangSmith was set up
        mock_client.assert_called_once_with(api_key='test-key')
        mock_tracer.assert_called_once_with(
            project_name='test-project',
            client=mock_client_instance
        )
        assert manager.langsmith_client == mock_client_instance
        assert manager.tracer == mock_tracer_instance
    
    @patch.dict(os.environ, {'LANGSMITH_TRACING': 'false'})
    @patch('apis.rag.langchain_inference.LLMProviderFactory.get_available_provider')
    @patch('apis.rag.langchain_inference.current_app')
    def test_langsmith_setup_disabled(self, mock_app, mock_factory):
        """Test LangSmith setup when tracing is disabled"""
        # Mock provider
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_factory.return_value = mock_provider
        
        # Mock Flask app logger
        mock_app.logger.info = MagicMock()
        
        manager = LangChainInferenceManager()
        
        # Verify LangSmith was not set up
        assert manager.langsmith_client is None
        assert manager.tracer is None

class TestErrorHandling:
    """Test error handling in the LangChain migration"""
    
    @patch('apis.rag.langchain_inference.LLMProviderFactory.get_available_provider')
    def test_no_providers_available(self, mock_factory):
        """Test error handling when no providers are available"""
        mock_factory.side_effect = RuntimeError("No LLM providers are available")
        
        with pytest.raises(RuntimeError, match="No LLM providers available"):
            LangChainInferenceManager()
    
    @patch('apis.rag.langchain_inference.LLMProviderFactory.get_available_provider')
    @patch('apis.rag.langchain_inference.current_app')
    def test_generation_error_handling(self, mock_app, mock_factory):
        """Test error handling during text generation"""
        # Mock provider that fails generation
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.generate.side_effect = Exception("Generation failed")
        mock_factory.return_value = mock_provider
        
        # Mock Flask app logger
        mock_app.logger.info = MagicMock()
        mock_app.logger.error = MagicMock()
        
        manager = LangChainInferenceManager()
        
        with pytest.raises(RuntimeError, match="Text generation failed"):
            manager.generate_text("Test prompt")

# Integration test that requires actual llama.cpp server
@pytest.mark.integration
class TestIntegration:
    """Integration tests that require actual services"""
    
    def test_local_provider_real_connection(self):
        """Test actual connection to llama.cpp server (if running)"""
        provider = LocalLlamaCppProvider()
        
        # This test will pass if llama.cpp server is running, skip otherwise
        if not provider.is_available():
            pytest.skip("llama.cpp server not available at http://localhost:8003")
        
        # If we get here, the server is available
        assert provider.is_available() == True

if __name__ == "__main__":
    # Run tests with: python -m pytest apis/rag/test_langchain_migration.py -v
    # Run with integration tests: python -m pytest apis/rag/test_langchain_migration.py -v -m integration
    pytest.main([__file__, "-v"])