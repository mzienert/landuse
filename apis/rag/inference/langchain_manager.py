"""LangChain-based inference manager implementation.

Clean implementation using LangChain providers for text generation.
"""

from typing import Generator
from langchain_core.messages import HumanMessage

from .base import InferenceManagerBase
from ..providers import LLMProviderFactory


class LangChainInferenceManager(InferenceManagerBase):
    """LangChain-based inference manager.
    
    Provides text generation through LangChain providers with automatic
    environment-based provider selection.
    """
    
    def __init__(self):
        self.provider = LLMProviderFactory.get_available_provider()
    
    @property
    def is_available(self) -> bool:
        """Check if inference is available."""
        return self.provider is not None and self.provider.is_available()
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate complete text from a prompt.
        
        Args:
            prompt: Input text prompt
            **kwargs: Additional generation parameters
            
        Returns:
            str: Generated text
        """
        if not self.is_available:
            raise RuntimeError("Inference not available")
        
        messages = [HumanMessage(content=prompt)]
        return self.provider.generate(messages, **kwargs)
    
    def stream_generate(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate streaming text from a prompt.
        
        Args:
            prompt: Input text prompt
            **kwargs: Additional generation parameters
            
        Yields:
            str: Generated text tokens
        """
        if not self.is_available:
            raise RuntimeError("Inference not available")
        
        messages = [HumanMessage(content=prompt)]
        yield from self.provider.stream_generate(messages, **kwargs)
    
    def reload_provider(self, env: str = None):
        """Reload provider for different environment.
        
        Args:
            env: Optional environment ('local', 'staging', 'production')
        """
        if env:
            self.provider = LLMProviderFactory.get_provider(env)
        else:
            self.provider = LLMProviderFactory.get_available_provider()