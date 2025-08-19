"""Inference management package for the RAG system.

This package provides inference managers that handle text generation
through different strategies (LangChain providers, direct HTTP calls, etc.).
"""

from .factory import InferenceManagerFactory
from .base import InferenceManagerBase
from .langchain_manager import LangChainInferenceManager

__all__ = [
    "InferenceManagerFactory",
    "InferenceManagerBase", 
    "LangChainInferenceManager"
]