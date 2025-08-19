"""Factory for creating LLM providers based on environment configuration.

This module implements the Factory pattern to provide environment-appropriate
LLM providers with automatic fallback logic.
"""

import logging
import os
from typing import Optional

from .base import LLMProvider
from .bedrock import BedrockProvider
from .local_llamacpp import LocalLlamaCppProvider
from ..config import Config

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """Factory for creating environment-appropriate LLM providers.
    
    This class implements the Factory pattern to instantiate the correct
    LLM provider based on deployment environment. It supports automatic
    fallback to available providers when the preferred option is unavailable.
    
    Examples:
        Basic usage:
        >>> factory = LLMProviderFactory()
        >>> provider = factory.get_provider('local')
        
        With automatic fallback:
        >>> provider = factory.get_available_provider('staging')
    """
    
    # Supported environments in fallback order
    _SUPPORTED_ENVIRONMENTS = ["local", "staging", "production"]
    
    @classmethod
    def get_provider(cls, env: Optional[str] = None) -> LLMProvider:
        """Get LLM provider based on environment.
        
        Args:
            env: Target environment ('local', 'staging', 'production').
                If None, uses DEPLOYMENT_ENV or config default.
                
        Returns:
            LLMProvider: Configured provider instance
            
        Raises:
            ValueError: If environment is not supported
            
        Examples:
            >>> provider = LLMProviderFactory.get_provider('local')
            >>> provider = LLMProviderFactory.get_provider()  # Uses env/config
        """
        if env is None:
            env = os.getenv("DEPLOYMENT_ENV", Config.DEPLOYMENT_ENV)
            
        logger.debug(f"Creating provider for environment: {env}")
        
        if env == "local":
            return LocalLlamaCppProvider()
        elif env == "staging":
            return BedrockProvider(Config.BEDROCK_STAGING_MODEL)
        elif env == "production":
            return BedrockProvider(Config.BEDROCK_PRODUCTION_MODEL)
        else:
            raise ValueError(
                f"Unknown environment '{env}'. "
                f"Supported: {', '.join(cls._SUPPORTED_ENVIRONMENTS)}"
            )
    
    @classmethod
    def get_available_provider(cls, preferred_env: Optional[str] = None) -> LLMProvider:
        """Get first available provider with fallback logic.
        
        Args:
            preferred_env: Preferred environment to try first.
                If None or unavailable, falls back through supported environments.
                
        Returns:
            LLMProvider: First available provider instance
            
        Raises:
            RuntimeError: If no providers are available
            
        Examples:
            >>> # Try staging first, fallback to others if unavailable
            >>> provider = LLMProviderFactory.get_available_provider('staging')
            >>> 
            >>> # Try all environments in order
            >>> provider = LLMProviderFactory.get_available_provider()
        """
        environments_to_try = []
        
        # Add preferred environment first if specified
        if preferred_env and preferred_env in cls._SUPPORTED_ENVIRONMENTS:
            environments_to_try.append(preferred_env)
            
        # Add remaining environments in fallback order
        for env in cls._SUPPORTED_ENVIRONMENTS:
            if env not in environments_to_try:
                environments_to_try.append(env)
                
        logger.debug(f"Trying providers in order: {environments_to_try}")
        
        for env in environments_to_try:
            try:
                provider = cls.get_provider(env)
                if provider.is_available():
                    logger.info(f"Using {env} provider: {type(provider).__name__}")
                    return provider
                else:
                    logger.debug(f"Provider {env} not available")
            except Exception as e:
                logger.debug(f"Failed to create {env} provider: {e}")
                continue
        
        raise RuntimeError(
            f"No LLM providers are available. Tried: {', '.join(environments_to_try)}"
        )