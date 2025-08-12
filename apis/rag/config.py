# Configuration for the RAG API

DEFAULT_MODEL_ID = "mlx-community/Qwen3-4B-Thinking-2507-8bit"

RAG_CONFIG = {
    "service": "RAG API",
    "version": "0.1.0",
    "model": {
        "default": DEFAULT_MODEL_ID,
        "target": "Qwen3-4B-Thinking for legal reasoning",
        "fallback": "Llama 3 Instruct or legal LoRA",
        "quantization": "8-bit preferred; fallback to 4-bit",
        "context_window": "8K–16K tokens",
    },
    "retrieval": {
        "store": "ChromaDB",
        "collections": ["la_plata_county_code", "la_plata_assessor"],
        "rerank": "heuristic v1 (cosine boost, redundancy penalty, diversity)",
    },
}