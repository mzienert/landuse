"""LLM Provider Package.

This package provides a unified interface for different LLM providers through
the Factory pattern. It supports multiple environments (local, staging, production)
with automatic provider selection and fallback logic.

Examples:
    Basic usage:
    >>> from services.rag.providers import LLMProviderFactory
    >>> provider = LLMProviderFactory.get_provider('local')
    >>> response = provider.generate([HumanMessage(content="Hello")])
    
    Automatic provider selection with fallback:
    >>> provider = LLMProviderFactory.get_available_provider('staging')
    >>> for chunk in provider.stream_generate([HumanMessage(content="Hello")]):
    ...     print(chunk, end='')
"""

from .factory import LLMProviderFactory

# Public API exports - only expose what consumers actually need
__all__ = [
    'LLMProviderFactory'
]

# Internal components can be imported directly when needed:
# from services.rag.providers.base import LLMProvider
# from services.rag.providers.local_llamacpp import LocalLlamaCppProvider
# from services.rag.providers.bedrock import BedrockProvider