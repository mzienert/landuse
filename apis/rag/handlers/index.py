from flask import Blueprint, jsonify
from ..config import RAG_CONFIG

index_bp = Blueprint('index', __name__)

@index_bp.route('/', methods=['GET'])
def index():
    return jsonify({
        "name": "La Plata County RAG API",
        "version": RAG_CONFIG["version"],
        "description": "RAG endpoints with streaming (stubbed)",
        "endpoints": {
            "/rag/health": "Health check",
            "/rag/config": "RAG configuration",
            "/rag/answer": "Non-streaming answer (stubbed)",
            "/rag/answer/stream": "SSE streaming answer (stubbed)",
        },
    })