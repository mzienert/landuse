from typing import Optional
from .base import LLMProvider
from .local_llamacpp import LocalLlamaCppProvider
from .bedrock import BedrockProvider
from ..config import Config


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