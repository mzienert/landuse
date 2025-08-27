"""Factory information endpoint for the RAG API.

This module provides endpoints to inspect the current factory configurations
and available managers/providers.
"""

from flask import Blueprint, jsonify
import os

factory_info_bp = Blueprint('factory_info', __name__)

@factory_info_bp.route('/rag/factory/info', methods=['GET'])
def factory_info():
    """Get information about available factories and their status.
    
    Returns comprehensive information about:
    - Available inference managers
    - Available LLM providers  
    - Current configuration
    - Factory status
    """
    try:
        # Get inference manager factory info
        from ..inference import InferenceManagerFactory
        inference_info = InferenceManagerFactory.get_manager_info()
        
        # Get LLM provider factory info
        provider_info = {}
        try:
            from ..providers import LLMProviderFactory
            
            provider_info = {
                "supported_environments": ["local", "staging", "production"],
                "current_environment": os.getenv("DEPLOYMENT_ENV", "local"),
                "provider_status": {}
            }
            
            # Check each provider environment
            for env in ["local", "staging", "production"]:
                try:
                    provider = LLMProviderFactory.get_provider(env)
                    provider_info["provider_status"][env] = {
                        "available": provider.is_available(),
                        "type": type(provider).__name__
                    }
                except Exception as e:
                    provider_info["provider_status"][env] = {
                        "available": False,
                        "error": str(e)
                    }
                    
        except Exception as e:
            provider_info = {"error": f"Cannot load LLM provider factory: {e}"}
        
        # Get current configuration
        config_info = {
            "inference_manager_type": os.getenv("INFERENCE_MANAGER_TYPE", "langchain"),
            "deployment_env": os.getenv("DEPLOYMENT_ENV", "local"),
            "langsmith_tracing": os.getenv("LANGSMITH_TRACING", "false"),
            "langsmith_project": os.getenv("LANGSMITH_PROJECT", "landuse-rag")
        }
        
        return jsonify({
            "inference_managers": inference_info,
            "llm_providers": provider_info,
            "configuration": config_info,
            "factory_pattern": {
                "inference_manager_factory": "InferenceManagerFactory.get_available_manager()",
                "llm_provider_factory": "LLMProviderFactory.get_available_provider()",
                "pattern": "Factory pattern with automatic fallback logic"
            }
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to get factory information: {e}",
            "available": False
        }), 500

@factory_info_bp.route('/rag/factory/managers', methods=['GET'])
def available_managers():
    """Get detailed information about available inference managers."""
    try:
        from ..inference import InferenceManagerFactory
        info = InferenceManagerFactory.get_manager_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({
            "error": f"Cannot load inference manager factory: {e}"
        }), 500

@factory_info_bp.route('/rag/factory/providers', methods=['GET'])
def available_providers():
    """Get detailed information about available LLM providers."""
    try:
        from ..providers import LLMProviderFactory
        
        provider_info = {
            "supported_environments": ["local", "staging", "production"],
            "current_environment": os.getenv("DEPLOYMENT_ENV", "local"),
            "provider_status": {}
        }
        
        # Check each provider environment
        for env in ["local", "staging", "production"]:
            try:
                provider = LLMProviderFactory.get_provider(env)
                provider_info["provider_status"][env] = {
                    "available": provider.is_available(),
                    "type": type(provider).__name__,
                    "config": {
                        "environment": env
                    }
                }
            except Exception as e:
                provider_info["provider_status"][env] = {
                    "available": False,
                    "error": str(e)
                }
        
        return jsonify(provider_info)
        
    except Exception as e:
        return jsonify({
            "error": f"Cannot load LLM provider factory: {e}"
        }), 500