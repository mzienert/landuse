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
            seed=42,  # Fixed seed for reproducible results
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
            self.llm.invoke(test_messages, max_tokens=1)
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