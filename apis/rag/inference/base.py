"""Abstract base class for inference managers.

This module defines the common interface that all inference managers must implement,
allowing for future extension with different inference strategies.
"""

from abc import ABC, abstractmethod
from typing import Generator, Optional, Dict, Any


class InferenceManagerBase(ABC):
    """Abstract base class for inference managers.
    
    This provides a common interface that all inference managers must implement,
    allowing for different inference strategies while maintaining compatibility
    with the existing RAG system.
    
    Examples:
        Implementing a custom inference manager:
        >>> class CustomInferenceManager(InferenceManagerBase):
        ...     def is_available(self) -> bool:
        ...         return True
        ...     
        ...     def load_model(self, model_id: str) -> dict:
        ...         return {"model_id": model_id}
    """
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if inference is available.
        
        Returns:
            bool: True if the inference manager can handle requests
        """
        pass
    
    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if a model is loaded and ready.
        
        Returns:
            bool: True if a model is loaded and ready for inference
        """
        pass
    
    @property
    @abstractmethod
    def model_id(self) -> Optional[str]:
        """Get the currently loaded model ID.
        
        Returns:
            Optional[str]: Model identifier or None if no model loaded
        """
        pass
    
    @property
    @abstractmethod
    def max_context(self) -> Optional[int]:
        """Get the maximum context length for the current model.
        
        Returns:
            Optional[int]: Maximum context tokens or None if unknown
        """
        pass
    
    @abstractmethod
    def load_model(self, model_id: str) -> Dict[str, Any]:
        """Load a model for inference.
        
        Args:
            model_id: Identifier of the model to load
            
        Returns:
            Dict[str, Any]: Information about the loaded model
            
        Raises:
            RuntimeError: If model loading fails
        """
        pass
    
    @abstractmethod
    def stream_generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 1200,
        temperature: float = 0.2,
        top_p: float = 0.9,
    ) -> Generator[str, None, None]:
        """Generate streaming text from a prompt.
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter
            
        Yields:
            str: Generated text tokens
            
        Raises:
            RuntimeError: If generation fails
        """
        pass
    
    def generate_text(
        self,
        prompt: str,
        *,
        max_tokens: int = 1200,
        temperature: float = 0.2,
        top_p: float = 0.9,
    ) -> str:
        """Generate complete text from a prompt.
        
        This is a convenience method that collects all tokens from
        stream_generate into a single string.
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter
            
        Returns:
            str: Complete generated text
            
        Raises:
            RuntimeError: If generation fails
        """
        tokens = []
        for token in self.stream_generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        ):
            tokens.append(token)
        return "".join(tokens)