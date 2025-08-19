from flask import Blueprint, request, jsonify, current_app

model_bp = Blueprint('model', __name__)

@model_bp.route('/rag/provider/switch', methods=['POST'])
def switch_provider():
    """Switch to a different LLM provider environment."""
    rag_engine = current_app.config['RAG_ENGINE']
    model_mgr = rag_engine.model_mgr
    
    if not model_mgr:
        return jsonify({"error": "Inference manager unavailable"}), 500

    data = request.get_json(force=True, silent=True) or {}
    env = data.get("environment", "").strip()
    
    if not env:
        return jsonify({"error": "environment is required (local, staging, production)"}), 400
    
    if env not in ["local", "staging", "production"]:
        return jsonify({"error": "environment must be local, staging, or production"}), 400

    try:
        old_provider = type(model_mgr.provider).__name__ if model_mgr.provider else "None"
        model_mgr.reload_provider(env)
        new_provider = type(model_mgr.provider).__name__ if model_mgr.provider else "None"
        
        return jsonify({
            "switched": True,
            "environment": env,
            "old_provider": old_provider,
            "new_provider": new_provider,
            "available": model_mgr.is_available
        })
    except Exception as e:
        return jsonify({"switched": False, "error": str(e)}), 500