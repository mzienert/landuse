"""Abstract base class for inference managers.

This module defines the clean interface that all inference managers must implement.
"""

from abc import ABC, abstractmethod
from typing import Generator


class InferenceManagerBase(ABC):
    """Abstract base class for inference managers.
    
    Clean, minimal interface for text generation services.
    """
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if inference is available."""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate complete text from a prompt."""
        pass
    
    @abstractmethod
    def stream_generate(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate streaming text from a prompt."""
        pass