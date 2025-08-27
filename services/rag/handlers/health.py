from flask import Blueprint, jsonify, current_app
from datetime import datetime
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/rag/health', methods=['GET'])
def rag_health():
    rag_engine = current_app.config['RAG_ENGINE']
    model_mgr = rag_engine.model_mgr
    
    # Get inference manager information
    inference_manager_info = {
        "type": "None",
        "status": "unhealthy",
        "manager_type": os.getenv("INFERENCE_MANAGER_TYPE", "langchain")
    }
    
    if model_mgr:
        inference_manager_info.update({
            "type": type(model_mgr).__name__,
            "status": "healthy" if model_mgr.is_available else "unhealthy"
        })
    
    # Get provider information
    provider_info = {
        "status": "unhealthy",
        "type": "None",
        "environment": os.getenv("DEPLOYMENT_ENV", "local")
    }
    
    if model_mgr and hasattr(model_mgr, 'provider') and model_mgr.provider:
        provider_info.update({
            "status": "healthy" if model_mgr.is_available else "unhealthy",
            "type": type(model_mgr.provider).__name__
        })
    
    overall_status = "healthy" if (model_mgr and model_mgr.is_available) else "degraded"
    
    return jsonify({
        "status": overall_status,
        "inference_available": bool(model_mgr and model_mgr.is_available),
        "inference_manager": inference_manager_info,
        "llm_provider": provider_info,
        "streaming": True,
        "endpoints": [
            "/rag/health",
            "/rag/config", 
            "/rag/answer",
            "/rag/answer/stream",
            "/rag/provider/switch",
            "/rag/factory/info",
            "/rag/factory/managers", 
            "/rag/factory/providers"
        ],
        "timestamp": datetime.now().isoformat(),
        "version": "0.3.0-clean-factory"
    })