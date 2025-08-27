"""Inference management package for the RAG system.

This package provides inference managers that handle text generation
through different strategies (LangChain providers, direct HTTP calls, etc.).

Public API:
    InferenceManagerFactory: Factory for creating inference managers
"""

from .factory import InferenceManagerFactory

__all__ = [
    "InferenceManagerFactory"
]