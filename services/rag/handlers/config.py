from flask import Blueprint, jsonify
from ..config import RAG_CONFIG

config_bp = Blueprint('config', __name__)

@config_bp.route('/rag/config', methods=['GET'])
def rag_config():
    return jsonify(RAG_CONFIG)