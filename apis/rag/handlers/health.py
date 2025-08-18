from flask import Blueprint, jsonify, current_app
from datetime import datetime
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/rag/health', methods=['GET'])
def rag_health():
    rag_engine = current_app.config['RAG_ENGINE']
    model_mgr = rag_engine.model_mgr
    
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
    
    # Get LangSmith information
    langsmith_info = {
        "tracing_enabled": hasattr(model_mgr, 'tracer') and model_mgr.tracer is not None if model_mgr else False,
        "project": os.getenv("LANGSMITH_PROJECT", "landuse-rag")
    }
    
    overall_status = "healthy" if (model_mgr and model_mgr.is_available) else "degraded"
    
    return jsonify({
        "status": overall_status,
        "model_loaded": bool(model_mgr and model_mgr.is_loaded),
        "inference_available": bool(model_mgr and model_mgr.is_available),
        "model_id": model_mgr.model_id if model_mgr else None,
        "llm_provider": provider_info,
        "langsmith": langsmith_info,
        "streaming": True,
        "endpoints": [
            "/rag/health",
            "/rag/config",
            "/rag/model/load",
            "/rag/answer",
            "/rag/answer/stream",
        ],
        "timestamp": datetime.now().isoformat(),
        "version": "0.2.0-langchain"
    })