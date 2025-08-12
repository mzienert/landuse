from flask import Blueprint, jsonify, current_app

health_bp = Blueprint('health', __name__)

@health_bp.route('/rag/health', methods=['GET'])
def rag_health():
    rag_engine = current_app.config['RAG_ENGINE']
    model_mgr = rag_engine.model_mgr
    
    return jsonify({
        "status": "healthy",
        "model_loaded": bool(model_mgr and model_mgr.is_loaded),
        "mlx_available": bool(model_mgr and model_mgr.is_available),
        "model_id": model_mgr.model_id if model_mgr else None,
        "streaming": True,
        "endpoints": [
            "/rag/health",
            "/rag/config",
            "/rag/model/load",
            "/rag/answer",
            "/rag/answer/stream",
        ],
    })