from flask import Blueprint, request, jsonify, current_app

model_bp = Blueprint('model', __name__)

@model_bp.route('/rag/model/load', methods=['POST'])
def rag_model_load():
    rag_engine = current_app.config['RAG_ENGINE']
    model_mgr = rag_engine.model_mgr
    
    if not model_mgr:
        return jsonify({"error": "Model manager unavailable"}), 500

    data = request.get_json(force=True, silent=True) or {}
    model_id = data.get("model_id", "").strip()
    if not model_id:
        return jsonify({"error": "model_id is required"}), 400

    try:
        info = model_mgr.load_model(model_id)
        return jsonify({"loaded": True, **info})
    except Exception as e:
        return jsonify({"loaded": False, "error": str(e)}), 500