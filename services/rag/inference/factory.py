"""Factory for creating inference managers based on configuration.

This module implements the Factory pattern to provide appropriate
inference managers with automatic configuration and fallback logic.
"""

import logging
import os
from typing import Optional

from .base import InferenceManagerBase
from .langchain_manager import LangChainInferenceManager
from ..config import Config

logger = logging.getLogger(__name__)


class InferenceManagerFactory:
    """Factory for creating environment-appropriate inference managers.
    
    This class implements the Factory pattern to instantiate the correct
    inference manager based on deployment environment and configuration.
    It supports different inference strategies and automatic fallback logic.
    
    Examples:
        Basic usage:
        >>> factory = InferenceManagerFactory()
        >>> manager = factory.get_manager('langchain')
        
        With automatic selection:
        >>> manager = factory.get_available_manager()
    """
    
    # Supported manager types in preference order
    _SUPPORTED_MANAGERS = ["langchain", "direct"]
    
    @classmethod
    def get_manager(cls, manager_type: Optional[str] = None) -> InferenceManagerBase:
        """Get inference manager based on type.
        
        Args:
            manager_type: Type of inference manager ('langchain', 'direct').
                If None, uses INFERENCE_MANAGER_TYPE or config default.
                
        Returns:
            InferenceManagerBase: Configured manager instance
            
        Raises:
            ValueError: If manager type is not supported
            RuntimeError: If manager cannot be created
            
        Examples:
            >>> manager = InferenceManagerFactory.get_manager('langchain')
            >>> manager = InferenceManagerFactory.get_manager()  # Uses env/config
        """
        if manager_type is None:
            manager_type = os.getenv("INFERENCE_MANAGER_TYPE", getattr(Config, "INFERENCE_MANAGER_TYPE", "langchain"))
            
        logger.debug(f"Creating inference manager of type: {manager_type}")
        
        if manager_type == "langchain":
            return cls._create_langchain_manager()
        elif manager_type == "direct":
            # Future: Could implement DirectInferenceManager for HTTP calls
            raise NotImplementedError("Direct inference manager not yet implemented")
        else:
            raise ValueError(
                f"Unknown manager type '{manager_type}'. "
                f"Supported: {', '.join(cls._SUPPORTED_MANAGERS)}"
            )
    
    @classmethod
    def get_available_manager(cls, preferred_type: Optional[str] = None) -> InferenceManagerBase:
        """Get first available inference manager with fallback logic.
        
        Args:
            preferred_type: Preferred manager type to try first.
                If None or unavailable, falls back through supported types.
                
        Returns:
            InferenceManagerBase: First available manager instance
            
        Raises:
            RuntimeError: If no managers are available
            
        Examples:
            >>> # Try langchain first, fallback to others if unavailable
            >>> manager = InferenceManagerFactory.get_available_manager('langchain')
            >>> 
            >>> # Try all manager types in order
            >>> manager = InferenceManagerFactory.get_available_manager()
        """
        types_to_try = []
        
        # Add preferred type first if specified
        if preferred_type and preferred_type in cls._SUPPORTED_MANAGERS:
            types_to_try.append(preferred_type)
            
        # Add remaining types in preference order
        for manager_type in cls._SUPPORTED_MANAGERS:
            if manager_type not in types_to_try:
                types_to_try.append(manager_type)
                
        logger.debug(f"Trying inference managers in order: {types_to_try}")
        
        for manager_type in types_to_try:
            try:
                manager = cls.get_manager(manager_type)
                if manager.is_available:
                    logger.info(f"Using {manager_type} inference manager: {type(manager).__name__}")
                    return manager
                else:
                    logger.debug(f"Inference manager {manager_type} not available")
            except Exception as e:
                logger.debug(f"Failed to create {manager_type} manager: {e}")
                continue
        
        raise RuntimeError(
            f"No inference managers are available. Tried: {', '.join(types_to_try)}"
        )
    
    @classmethod
    def _create_langchain_manager(cls) -> LangChainInferenceManager:
        """Create a LangChain inference manager.
        
        Returns:
            LangChainInferenceManager: Configured instance
            
        Raises:
            RuntimeError: If manager cannot be created
        """
        try:
            manager = LangChainInferenceManager()
            logger.debug("Created LangChain inference manager")
            return manager
        except Exception as e:
            logger.error(f"Failed to create LangChain inference manager: {e}")
            raise RuntimeError(f"Cannot create LangChain inference manager: {e}")
    
    @classmethod
    def get_manager_info(cls) -> dict:
        """Get information about available manager types.
        
        Returns:
            dict: Information about supported managers and their status
        """
        info = {
            "supported_managers": cls._SUPPORTED_MANAGERS,
            "default_manager": os.getenv("INFERENCE_MANAGER_TYPE", "langchain"),
            "manager_status": {}
        }
        
        for manager_type in cls._SUPPORTED_MANAGERS:
            try:
                if manager_type == "langchain":
                    manager = cls._create_langchain_manager()
                    info["manager_status"][manager_type] = {
                        "available": manager.is_available,
                        "provider_type": type(manager.provider).__name__ if hasattr(manager, 'provider') and manager.provider else "None"
                    }
                else:
                    info["manager_status"][manager_type] = {
                        "available": False,
                        "reason": "Not implemented"
                    }
            except Exception as e:
                info["manager_status"][manager_type] = {
                    "available": False,
                    "error": str(e)
                }
        
        return info