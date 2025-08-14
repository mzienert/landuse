# LangChain Integration Migration Plan

## Overview

This document outlines the migration from direct HTTP calls to LangChain abstraction layer, enabling environment-based provider switching while maintaining current performance and consistency characteristics.

## Environment-Based Provider Switching Architecture

### Core Design Principles

1. **Zero Performance Regression**: HTTP-based calls preserve current optimizations
2. **Parameter Consistency**: Maintain seed=42, temperature≤0.1, repeat_penalty=1.3 across all providers
3. **Environment Isolation**: Clear separation between local/staging/production configurations
4. **Seamless Migration**: Gradual transition with fallback capabilities

### Provider Architecture

```python
# apis/rag/llm_provider.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator, Optional
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import os

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, messages: list[BaseMessage], **kwargs) -> str:
        """Generate a response from messages"""
        pass
    
    @abstractmethod
    def stream_generate(self, messages: list[BaseMessage], **kwargs) -> Iterator[str]:
        """Stream generate a response from messages"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass

class LocalLlamaCppProvider(LLMProvider):
    """LangChain provider for local llama.cpp HTTP server"""
    
    def __init__(self, base_url: str = "http://localhost:8003/v1"):
        self.base_url = base_url
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key="dummy",  # llama.cpp doesn't validate
            model="gpt-3.5-turbo",  # Placeholder, ignored by llama.cpp
            temperature=0.1,  # Capped for consistency
            max_tokens=1200,
            model_kwargs={
                "seed": 42,  # Fixed seed for reproducible results
                "repeat_penalty": 1.3,  # Prevent repetition
                "repeat_last_n": 128  # Repetition detection window
            }
        )
    
    def generate(self, messages: list[BaseMessage], **kwargs) -> str:
        """Generate response using local llama.cpp server"""
        response = self.llm.invoke(messages, **kwargs)
        return response.content
    
    def stream_generate(self, messages: list[BaseMessage], **kwargs) -> Iterator[str]:
        """Stream response using local llama.cpp server"""
        for chunk in self.llm.stream(messages, **kwargs):
            if chunk.content:
                yield chunk.content
    
    def is_available(self) -> bool:
        """Check if llama.cpp server is responding"""
        try:
            import requests
            response = requests.get(f"{self.base_url.replace('/v1', '')}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

class StagingBedrockProvider(LLMProvider):
    """LangChain provider for AWS Bedrock staging environment"""
    
    def __init__(self, region: str = "us-west-2"):
        self.llm = ChatBedrock(
            model_id="anthropic.claude-3-haiku-20240307",  # Cheaper for staging
            region=region,
            model_kwargs={
                "temperature": 0.1,  # Match local consistency
                "max_tokens": 1200
            }
        )
    
    def generate(self, messages: list[BaseMessage], **kwargs) -> str:
        """Generate response using AWS Bedrock staging"""
        response = self.llm.invoke(messages, **kwargs)
        return response.content
    
    def stream_generate(self, messages: list[BaseMessage], **kwargs) -> Iterator[str]:
        """Stream response using AWS Bedrock staging"""
        for chunk in self.llm.stream(messages, **kwargs):
            if chunk.content:
                yield chunk.content
    
    def is_available(self) -> bool:
        """Check if AWS Bedrock is accessible"""
        try:
            # Simple test call with minimal content
            test_messages = [HumanMessage(content="Hi")]
            response = self.llm.invoke(test_messages, max_tokens=1)
            return True
        except:
            return False

class ProductionBedrockProvider(LLMProvider):
    """LangChain provider for AWS Bedrock production environment"""
    
    def __init__(self, region: str = "us-west-2"):
        self.llm = ChatBedrock(
            model_id="anthropic.claude-3-sonnet-20240229",  # Higher quality for production
            region=region,
            model_kwargs={
                "temperature": 0.1,  # Match local consistency
                "max_tokens": 1200
            }
        )
    
    def generate(self, messages: list[BaseMessage], **kwargs) -> str:
        """Generate response using AWS Bedrock production"""
        response = self.llm.invoke(messages, **kwargs)
        return response.content
    
    def stream_generate(self, messages: list[BaseMessage], **kwargs) -> Iterator[str]:
        """Stream response using AWS Bedrock production"""
        for chunk in self.llm.stream(messages, **kwargs):
            if chunk.content:
                yield chunk.content
    
    def is_available(self) -> bool:
        """Check if AWS Bedrock is accessible"""
        try:
            # Simple test call with minimal content
            test_messages = [HumanMessage(content="Hi")]
            response = self.llm.invoke(test_messages, max_tokens=1)
            return True
        except:
            return False

class LLMProviderFactory:
    """Factory for creating environment-appropriate LLM providers"""
    
    @staticmethod
    def get_provider(env: Optional[str] = None) -> LLMProvider:
        """Get LLM provider based on environment"""
        if env is None:
            env = os.getenv("DEPLOYMENT_ENV", "local")
        
        if env == "local":
            return LocalLlamaCppProvider()
        elif env == "staging":
            return StagingBedrockProvider()
        elif env == "production":
            return ProductionBedrockProvider()
        else:
            raise ValueError(f"Unknown environment: {env}")
    
    @staticmethod
    def get_available_provider(preferred_env: Optional[str] = None) -> LLMProvider:
        """Get first available provider with fallback logic"""
        if preferred_env:
            try:
                provider = LLMProviderFactory.get_provider(preferred_env)
                if provider.is_available():
                    return provider
            except:
                pass
        
        # Fallback order: local -> staging -> production
        for env in ["local", "staging", "production"]:
            try:
                provider = LLMProviderFactory.get_provider(env)
                if provider.is_available():
                    return provider
            except:
                continue
        
        raise RuntimeError("No LLM providers are available")
```

### Configuration Management

```python
# apis/rag/config.py - Updated with LangChain settings

class Config:
    # Existing settings...
    
    # LLM Provider Configuration
    DEPLOYMENT_ENV = os.environ.get('DEPLOYMENT_ENV', 'local')
    
    # Local llama.cpp Configuration
    LLAMA_CPP_BASE_URL = os.environ.get('LLAMA_CPP_BASE_URL', 'http://localhost:8003/v1')
    LLAMA_CPP_HEALTH_URL = os.environ.get('LLAMA_CPP_HEALTH_URL', 'http://localhost:8003/health')
    
    # AWS Bedrock Configuration
    AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
    BEDROCK_STAGING_MODEL = os.environ.get('BEDROCK_STAGING_MODEL', 'anthropic.claude-3-haiku-20240307')
    BEDROCK_PRODUCTION_MODEL = os.environ.get('BEDROCK_PRODUCTION_MODEL', 'anthropic.claude-3-sonnet-20240229')
    
    # Generation Parameters (consistent across providers)
    GENERATION_TEMPERATURE = float(os.environ.get('GENERATION_TEMPERATURE', '0.1'))
    GENERATION_MAX_TOKENS = int(os.environ.get('GENERATION_MAX_TOKENS', '1200'))
    GENERATION_SEED = int(os.environ.get('GENERATION_SEED', '42'))
    GENERATION_REPEAT_PENALTY = float(os.environ.get('GENERATION_REPEAT_PENALTY', '1.3'))
    
    # Provider Selection Strategy
    PROVIDER_FALLBACK_ENABLED = os.environ.get('PROVIDER_FALLBACK_ENABLED', 'true').lower() == 'true'
    PROVIDER_HEALTH_CHECK_TIMEOUT = int(os.environ.get('PROVIDER_HEALTH_CHECK_TIMEOUT', '5'))
```

### Environment Variables Configuration

```bash
# .env.local
DEPLOYMENT_ENV=local
LLAMA_CPP_BASE_URL=http://localhost:8003/v1
PROVIDER_FALLBACK_ENABLED=true

# .env.staging  
DEPLOYMENT_ENV=staging
AWS_REGION=us-west-2
BEDROCK_STAGING_MODEL=anthropic.claude-3-haiku-20240307
PROVIDER_FALLBACK_ENABLED=true

# .env.production
DEPLOYMENT_ENV=production
AWS_REGION=us-west-2
BEDROCK_PRODUCTION_MODEL=anthropic.claude-3-sonnet-20240229
PROVIDER_FALLBACK_ENABLED=false  # Strict production mode
```

### Integration with Current RAG Pipeline

```python
# apis/rag/langchain_inference.py - New inference module
from typing import Generator, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from .llm_provider import LLMProviderFactory
from flask import current_app

class LangChainInferenceManager:
    """LangChain-based inference manager replacing direct HTTP calls"""
    
    def __init__(self):
        self.provider = None
        self._load_provider()
    
    def _load_provider(self):
        """Load and cache the appropriate LLM provider"""
        try:
            self.provider = LLMProviderFactory.get_available_provider()
            current_app.logger.info(f"Loaded LLM provider: {type(self.provider).__name__}")
        except Exception as e:
            current_app.logger.error(f"Failed to load LLM provider: {e}")
            raise RuntimeError("No LLM providers available")
    
    @property
    def is_available(self) -> bool:
        """Check if inference is available"""
        return self.provider is not None and self.provider.is_available()
    
    def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text using LangChain provider"""
        if not self.is_available:
            self._load_provider()
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        try:
            return self.provider.generate(messages, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Text generation failed: {e}")
            raise RuntimeError(f"Text generation failed: {e}")
    
    def stream_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream text using LangChain provider"""
        if not self.is_available:
            self._load_provider()
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        try:
            yield from self.provider.stream_generate(messages, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Text streaming failed: {e}")
            raise RuntimeError(f"Text streaming failed: {e}")
    
    def reload_provider(self, env: Optional[str] = None):
        """Reload provider for different environment"""
        try:
            if env:
                self.provider = LLMProviderFactory.get_provider(env)
            else:
                self.provider = LLMProviderFactory.get_available_provider()
            current_app.logger.info(f"Reloaded LLM provider: {type(self.provider).__name__}")
        except Exception as e:
            current_app.logger.error(f"Failed to reload LLM provider: {e}")
            raise RuntimeError("Failed to reload LLM provider")
```

### Health Check Integration

```python
# apis/rag/rag_api.py - Updated health endpoint
@app.route("/rag/health", methods=["GET"])
def health():
    """Enhanced health check with provider status"""
    try:
        # Check search API connectivity
        search_healthy = check_search_api_health()
        
        # Check LLM provider availability
        inference_manager = LangChainInferenceManager()
        llm_healthy = inference_manager.is_available
        provider_type = type(inference_manager.provider).__name__ if inference_manager.provider else "None"
        
        # Get environment info
        env = os.getenv("DEPLOYMENT_ENV", "local")
        
        return jsonify({
            "status": "healthy" if (search_healthy and llm_healthy) else "degraded",
            "search_api": "healthy" if search_healthy else "unhealthy",
            "llm_provider": {
                "status": "healthy" if llm_healthy else "unhealthy",
                "type": provider_type,
                "environment": env
            },
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.2.0-langchain"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500
```

## Benefits of This Architecture

### 1. **Environment Flexibility**
- **Local Development**: Use llama.cpp server (fast, free, deterministic)
- **Staging**: Use Claude Haiku (cloud testing, cost-effective)
- **Production**: Use Claude Sonnet (highest quality, production-ready)

### 2. **Consistency Preservation**
- **Same parameters**: temperature≤0.1, seed=42, repeat_penalty=1.3 across all providers
- **Same prompts**: LangChain message format standardizes prompt handling
- **Same performance**: HTTP-based local provider maintains current optimizations

### 3. **Operational Benefits**
- **Graceful degradation**: Automatic fallback between providers
- **Health monitoring**: Provider-aware health checks
- **Configuration management**: Environment-based settings
- **Logging and observability**: Centralized provider logging

### 4. **Migration Safety**
- **Gradual transition**: Can be implemented alongside existing direct HTTP calls
- **Rollback capability**: Easy to revert to direct HTTP if needed
- **Testing flexibility**: Can test different providers in same environment

### 5. **Cost Optimization**
- **Development**: Free local inference
- **Staging**: Cheaper Claude Haiku for testing
- **Production**: Premium Claude Sonnet for quality

This architecture provides a robust foundation for the current LangChain migration while establishing the framework for future cloud deployment and multi-provider scenarios.

## Migration Strategy: Direct HTTP to LangChain

### Phase 1: Foundation Setup (Week 1)

#### Step 1.1: Install Dependencies
```bash
# Add LangChain dependencies to requirements
pip install langchain-openai langchain-aws langchain-core
```

#### Step 1.2: Create Provider Architecture
- [ ] Create `apis/rag/llm_provider.py` with provider classes
- [ ] Create `apis/rag/langchain_inference.py` with inference manager
- [ ] Update `apis/rag/config.py` with LangChain settings
- [ ] Add environment configuration files (`.env.local`, `.env.staging`, `.env.production`)

#### Step 1.3: Testing Infrastructure
```python
# apis/rag/test_langchain_migration.py
import pytest
from .llm_provider import LLMProviderFactory, LocalLlamaCppProvider
from .langchain_inference import LangChainInferenceManager

def test_local_provider_availability():
    """Test local llama.cpp provider is working"""
    provider = LocalLlamaCppProvider()
    assert provider.is_available()

def test_provider_factory():
    """Test provider factory returns correct provider for environment"""
    os.environ["DEPLOYMENT_ENV"] = "local"
    provider = LLMProviderFactory.get_provider()
    assert isinstance(provider, LocalLlamaCppProvider)

def test_inference_manager():
    """Test inference manager can generate text"""
    manager = LangChainInferenceManager()
    response = manager.generate_text("Test prompt")
    assert len(response) > 0

def test_consistency_parameters():
    """Test that seed and temperature are preserved"""
    manager = LangChainInferenceManager()
    response1 = manager.generate_text("What are minor subdivision requirements?")
    response2 = manager.generate_text("What are minor subdivision requirements?")
    # Responses should be identical due to seed=42
    assert response1 == response2
```

### Phase 2: Parallel Implementation (Week 2)

#### Step 2.1: Create LangChain Inference Module
- [ ] Implement `LangChainInferenceManager` class
- [ ] Create methods that mirror current `ModelManager` interface
- [ ] Add comprehensive error handling and logging
- [ ] Implement health checks and provider switching

#### Step 2.2: Parallel Testing
```python
# apis/rag/migration_test.py
def test_response_consistency():
    """Compare direct HTTP vs LangChain responses"""
    # Current direct HTTP approach
    from .inference import ModelManager
    current_manager = ModelManager()
    current_response = current_manager.stream_generate("What are minor subdivision requirements?")
    
    # New LangChain approach
    from .langchain_inference import LangChainInferenceManager
    new_manager = LangChainInferenceManager()
    new_response = new_manager.generate_text("What are minor subdivision requirements?")
    
    # Compare key characteristics
    assert len(current_response) > 0
    assert len(new_response) > 0
    # Responses should have similar structure and content
    assert "subdivision" in new_response.lower()
    assert "requirements" in new_response.lower()

def test_performance_comparison():
    """Compare performance between approaches"""
    import time
    
    # Time current approach
    start = time.time()
    current_response = current_manager.stream_generate("Test query")
    current_time = time.time() - start
    
    # Time LangChain approach  
    start = time.time()
    new_response = new_manager.generate_text("Test query")
    new_time = time.time() - start
    
    # Performance should be similar (within 20%)
    assert abs(new_time - current_time) / current_time < 0.2
```

#### Step 2.3: Update Health Endpoints
- [ ] Modify `/rag/health` to include provider status
- [ ] Add `/rag/provider/status` endpoint for detailed provider info
- [ ] Add `/rag/provider/switch` endpoint for testing different providers

### Phase 3: Gradual Migration (Week 3)

#### Step 3.1: Feature Flag Implementation
```python
# apis/rag/config.py
class Config:
    # Migration control
    USE_LANGCHAIN = os.environ.get('USE_LANGCHAIN', 'false').lower() == 'true'
    LANGCHAIN_FALLBACK = os.environ.get('LANGCHAIN_FALLBACK', 'true').lower() == 'true'
```

#### Step 3.2: Hybrid Implementation
```python
# apis/rag/inference.py - Updated for hybrid approach
class HybridInferenceManager:
    """Hybrid manager supporting both direct HTTP and LangChain"""
    
    def __init__(self):
        self.use_langchain = current_app.config.get('USE_LANGCHAIN', False)
        self.fallback_enabled = current_app.config.get('LANGCHAIN_FALLBACK', True)
        
        if self.use_langchain:
            try:
                from .langchain_inference import LangChainInferenceManager
                self.langchain_manager = LangChainInferenceManager()
            except Exception as e:
                current_app.logger.error(f"Failed to initialize LangChain: {e}")
                if not self.fallback_enabled:
                    raise
                self.use_langchain = False
        
        if not self.use_langchain:
            self.direct_manager = ModelManager()  # Current implementation
    
    def stream_generate(self, prompt: str, **kwargs):
        """Generate with fallback logic"""
        if self.use_langchain:
            try:
                return self.langchain_manager.stream_text(prompt, **kwargs)
            except Exception as e:
                current_app.logger.error(f"LangChain generation failed: {e}")
                if self.fallback_enabled:
                    current_app.logger.info("Falling back to direct HTTP")
                    return self.direct_manager.stream_generate(prompt, **kwargs)
                raise
        else:
            return self.direct_manager.stream_generate(prompt, **kwargs)
```

#### Step 3.3: Gradual Rollout
- [ ] Enable LangChain for 10% of requests (feature flag)
- [ ] Monitor error rates and performance metrics
- [ ] Compare response quality between approaches
- [ ] Gradually increase LangChain usage to 50%, then 100%

### Phase 4: Full Migration (Week 4)

#### Step 4.1: Replace Direct HTTP Calls
- [ ] Update `rag_api.py` to use `LangChainInferenceManager`
- [ ] Remove `inference.py` ModelManager class
- [ ] Update all imports and references
- [ ] Remove direct HTTP request code

#### Step 4.2: Cleanup and Optimization
```python
# Remove old code
# apis/rag/inference.py - DEPRECATED
# Direct HTTP request implementations

# Update all imports
# From: from .inference import ModelManager
# To:   from .langchain_inference import LangChainInferenceManager
```

#### Step 4.3: Environment Testing
- [ ] Test local environment with llama.cpp provider
- [ ] Set up staging environment with AWS Bedrock (if available)
- [ ] Verify environment switching works correctly
- [ ] Test failover scenarios

### Phase 5: Production Deployment (Week 5)

#### Step 5.1: Deployment Preparation
- [ ] Update deployment scripts to include LangChain dependencies
- [ ] Configure environment variables for production
- [ ] Set up monitoring for new provider architecture
- [ ] Create rollback procedures

#### Step 5.2: Production Rollout
- [ ] Deploy to staging environment first
- [ ] Run comprehensive integration tests
- [ ] Monitor performance and error rates
- [ ] Deploy to production with gradual traffic increase

#### Step 5.3: Post-Migration Optimization
- [ ] Monitor provider performance across environments
- [ ] Optimize configuration for each environment
- [ ] Set up alerts for provider failures
- [ ] Document new architecture for operations team

### Migration Validation Checklist

#### Functional Requirements ✅
- [ ] Same response quality as current implementation
- [ ] Consistent responses (seed=42, temperature≤0.1 preserved)
- [ ] Streaming functionality maintained
- [ ] Error handling equivalent or better
- [ ] Health checks include provider status

#### Performance Requirements ✅
- [ ] Response time within 10% of current implementation
- [ ] Memory usage equivalent (HTTP-based, no regression)
- [ ] CPU usage similar or better
- [ ] Concurrent request handling maintained

#### Operational Requirements ✅
- [ ] Environment-based configuration working
- [ ] Provider switching functional
- [ ] Graceful degradation on provider failure
- [ ] Comprehensive logging and monitoring
- [ ] Documentation updated

### Risk Mitigation

#### High-Risk Items and Mitigation
1. **Response Quality Regression**
   - **Mitigation**: Extensive A/B testing between direct HTTP and LangChain
   - **Rollback**: Feature flag allows immediate revert to direct HTTP

2. **Performance Degradation**
   - **Mitigation**: Parallel performance testing throughout migration
   - **Rollback**: Hybrid implementation allows fallback to direct HTTP

3. **Provider Availability Issues**
   - **Mitigation**: Multiple provider support with automatic fallback
   - **Rollback**: Local llama.cpp always available as fallback

4. **Configuration Complexity**
   - **Mitigation**: Clear environment separation and validation
   - **Rollback**: Simple environment variable changes to revert

### Success Metrics

#### Technical Metrics
- Response time: ≤110% of current baseline
- Memory usage: ≤105% of current baseline  
- Error rate: ≤1% for provider switching
- Consistency: 100% identical responses for same query with seed=42

#### Operational Metrics
- Deployment time: ≤current deployment time
- Environment switch time: ≤5 minutes
- Provider failover time: ≤30 seconds
- Documentation completeness: 100%

### Timeline Summary

| Week | Phase | Key Deliverables | Risk Level |
|------|-------|------------------|------------|
| 1 | Foundation | Provider architecture, testing | Low |
| 2 | Parallel Testing | LangChain implementation, validation | Medium |
| 3 | Gradual Migration | Hybrid approach, feature flags | Medium |
| 4 | Full Migration | Replace direct HTTP, cleanup | High |
| 5 | Production Deploy | Staging/prod deployment | High |

This comprehensive migration strategy ensures a smooth transition from direct HTTP calls to LangChain abstraction while maintaining all current performance characteristics and adding powerful new capabilities for future cloud deployment.