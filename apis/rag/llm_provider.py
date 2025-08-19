from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator, Optional
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock
from langchain_core.messages import BaseMessage, HumanMessage
from .config import Config

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
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or Config.LLAMA_CPP_BASE_URL
        self.llm = ChatOpenAI(
            base_url=self.base_url,
            api_key="dummy",  # llama.cpp doesn't validate
            model="gpt-3.5-turbo",  # Placeholder, ignored by llama.cpp
            temperature=Config.GENERATION_TEMPERATURE,
            max_tokens=Config.GENERATION_MAX_TOKENS,
            seed=Config.GENERATION_SEED,
            # Note: repeat_penalty not supported in OpenAI-compatible API
            # llama.cpp server should be configured with these parameters
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
            health_url = Config.LLAMA_CPP_HEALTH_URL or f"{self.base_url.replace('/v1', '')}/health"
            response = requests.get(health_url, timeout=Config.PROVIDER_HEALTH_CHECK_TIMEOUT)
            return response.status_code == 200
        except:
            return False

class BedrockProvider(LLMProvider):
    """LangChain provider for AWS Bedrock with configurable model"""
    
    def __init__(self, model_id: str, region: str = None):
        self.region = region or Config.AWS_REGION
        self.model_id = model_id
        self.llm = ChatBedrock(
            model_id=model_id,
            region=self.region,
            model_kwargs={
                "temperature": Config.GENERATION_TEMPERATURE,
                "max_tokens": Config.GENERATION_MAX_TOKENS
            }
        )
    
    def generate(self, messages: list[BaseMessage], **kwargs) -> str:
        """Generate response using AWS Bedrock"""
        response = self.llm.invoke(messages, **kwargs)
        return response.content
    
    def stream_generate(self, messages: list[BaseMessage], **kwargs) -> Iterator[str]:
        """Stream response using AWS Bedrock"""
        for chunk in self.llm.stream(messages, **kwargs):
            if chunk.content:
                yield chunk.content
    
    def is_available(self) -> bool:
        """Check if AWS Bedrock is accessible"""
        try:
            # Simple test call with minimal content
            test_messages = [HumanMessage(content="Hi")]
            self.llm.invoke(test_messages, max_tokens=1)
            return True
        except:
            return False

class LLMProviderFactory:
    """Factory for creating environment-appropriate LLM providers"""
    
    @staticmethod
    def get_provider(env: Optional[str] = None) -> LLMProvider:
        """Get LLM provider based on environment"""
        if env is None:
            import os
            env = os.getenv("DEPLOYMENT_ENV", Config.DEPLOYMENT_ENV)
        
        if env == "local":
            return LocalLlamaCppProvider()
        elif env == "staging":
            return BedrockProvider(Config.BEDROCK_STAGING_MODEL)
        elif env == "production":
            return BedrockProvider(Config.BEDROCK_PRODUCTION_MODEL)
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