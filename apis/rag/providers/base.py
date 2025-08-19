from abc import ABC, abstractmethod
from typing import Iterator
from langchain_core.messages import BaseMessage


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