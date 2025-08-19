"""Abstract base class for LLM providers.

This module defines the interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Iterator

from langchain_core.messages import BaseMessage


class LLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    This class defines the interface that all LLM provider implementations
    must follow. It ensures consistent behavior across different provider types
    (local, cloud, etc.).
    """
    
    @abstractmethod
    def generate(self, messages: list[BaseMessage], **kwargs) -> str:
        """Generate a response from messages.
        
        Args:
            messages: List of LangChain messages to process
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
            
        Raises:
            RuntimeError: If generation fails
        """
        raise NotImplementedError
    
    @abstractmethod
    def stream_generate(self, messages: list[BaseMessage], **kwargs) -> Iterator[str]:
        """Stream generate a response from messages.
        
        Args:
            messages: List of LangChain messages to process
            **kwargs: Additional generation parameters
            
        Yields:
            str: Chunks of generated text
            
        Raises:
            RuntimeError: If streaming fails
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available.
        
        Returns:
            bool: True if provider can accept requests, False otherwise
        """
        raise NotImplementedError