#!/usr/bin/env python3
"""
Minimal RAG API scaffold (Step 1)
- Health/config endpoints
- Stubbed /rag/answer and /rag/answer/stream (no model loaded yet)

Keep separate from search_api.py for separation of concerns.
"""

from flask import Flask, request, Response, jsonify, stream_with_context
from flask_cors import CORS
import json
import time


app = Flask(__name__)
CORS(app)

# Optional: MLX model manager (loaded on demand)
try:
    from rag.inference import ModelManager
    model_mgr = ModelManager()
except Exception:
    model_mgr = None

try:
    from rag.retrieval import (
        fetch_simple_search,
        build_prompt_with_sources,
        rerank_results,
        extract_citations,
        auto_cite_answer,
    )
    from rag.verify import verify_answer_support
except Exception:
    fetch_simple_search = None
    build_prompt_with_sources = None


RAG_CONFIG = {
    "service": "RAG API",
    "version": "0.1.0",
    "model": {
        "target": "Llama3-LegalLM (Hugging Face)",
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


@app.route("/rag/health", methods=["GET"])
def rag_health():
    return jsonify(
        {
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
        }
    )


@app.route("/rag/config", methods=["GET"])
def rag_config():
    return jsonify(RAG_CONFIG)


@app.route("/rag/model/load", methods=["POST"])
def rag_model_load():
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


@app.route("/rag/answer", methods=["POST"])
def rag_answer():
    try:
        data = request.get_json(force=True, silent=True) or {}
        query = data.get("query", "").strip()
        collection = data.get("collection", "la_plata_county_code")
        num_results = int(data.get("num_results", 5))

        if not query:
            return jsonify({"error": "query is required"}), 400

        # If model loaded, include retrieval context (no reranking yet)
        if model_mgr and model_mgr.is_loaded:
            if fetch_simple_search and build_prompt_with_sources:
                try:
                    retrieval = fetch_simple_search(query, collection=collection, num_results=num_results)
                    raw_results = retrieval.get("results", [])
                    # Heuristic rerank + diversity selection (v1)
                    results = rerank_results(query, raw_results, top_k=min(num_results, 6))
                except Exception as e:
                    results = []
                    # Fall back to raw question if retrieval fails
                prompt, sources_meta = build_prompt_with_sources(query, results) if results else (
                    f"User question:\n{query}\n\nAnswer concisely.",
                    [],
                )
            else:
                prompt, sources_meta = f"User question:\n{query}\n\nAnswer concisely.", []
            tokens = []
            try:
                for t in model_mgr.stream_generate(
                    prompt,
                    max_tokens=int(data.get("max_tokens", 256)),
                    temperature=float(data.get("temperature", 0.2)),
                    top_p=float(data.get("top_p", 0.9)),
                ):
                    tokens.append(t)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
            answer_text = "".join(tokens).strip()
            citations, used_sources = extract_citations(answer_text, sources_meta)
            if not citations and sources_meta:
                # Best-effort auto-citation fallback
                answer_text, citations, used_sources = auto_cite_answer(answer_text, sources_meta)

            # Lightweight verification report
            annotated_answer, verification = verify_answer_support(answer_text, used_sources)
            answer_text = annotated_answer
        else:
            answer_text = (
                "[stub] Model not loaded. Load via POST /rag/model/load with {\"model_id\": \"...\"}."
            )

        return jsonify(
            {
                "query": query,
                "collection": collection,
                "num_results": num_results,
                "answer": answer_text,
                "citations": citations if model_mgr and model_mgr.is_loaded else [],
                "sources": used_sources if model_mgr and model_mgr.is_loaded else [],
                "verification": verification if model_mgr and model_mgr.is_loaded else None,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@app.route("/rag/answer/stream", methods=["POST", "GET"])
def rag_answer_stream():
    if request.method == "GET":
        data = {
            "query": request.args.get("query", ""),
            "collection": request.args.get("collection", "la_plata_county_code"),
            "num_results": request.args.get("num_results", 5),
            "max_tokens": request.args.get("max_tokens", 256),
            "temperature": request.args.get("temperature", 0.2),
            "top_p": request.args.get("top_p", 0.9),
        }
    else:
        data = request.get_json(force=True, silent=True) or {}

    query = (data.get("query", "") or "").strip()
    collection = data.get("collection", "la_plata_county_code")

    if not query:
        return jsonify({"error": "query is required"}), 400

    @stream_with_context
    def generate():
        yield _sse({
            "event": "start",
            "model_loaded": bool(model_mgr and model_mgr.is_loaded),
            "collection": collection,
        })
        # Large SSE comment padding to defeat buffering in certain proxies/browsers
        yield ": " + (" " * 2048) + "\n\n"

        if model_mgr and model_mgr.is_loaded:
            # Retrieval first (no reranking yet)
            sources_meta = []
            if fetch_simple_search and build_prompt_with_sources:
                try:
                    k = int(data.get("num_results", 5))
                    retrieval = fetch_simple_search(query, collection=collection, num_results=k)
                    raw_results = retrieval.get("results", [])
                    results = rerank_results(query, raw_results, top_k=min(k, 6))
                    prompt, sources_meta = build_prompt_with_sources(query, results)
                except Exception as e:
                    prompt = f"User question:\n{query}\n\nAnswer concisely."
            else:
                prompt = f"User question:\n{query}\n\nAnswer concisely."
            try:
                for t in model_mgr.stream_generate(
                    prompt,
                    max_tokens=int(data.get("max_tokens", 256)),
                    temperature=float(data.get("temperature", 0.2)),
                    top_p=float(data.get("top_p", 0.9)),
                ):
                    yield _sse({"event": "token", "text": t})
            except Exception as e:
                yield _sse({"event": "error", "message": str(e)})
        else:
            for t in ["Model", " not", " loaded."]:
                time.sleep(0.05)
                yield _sse({"event": "token", "text": t})

        # We cannot reliably compute final citations from a streaming session without
        # buffering the whole output. For now, end event does not carry final citations.
        yield _sse({"event": "end", "answer": None, "citations": [], "sources": []})

    resp = Response(generate(), mimetype="text/event-stream")
    # Encourage immediate flushing/streaming across proxies/browsers
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"  # nginx buffering hint
    resp.headers["Connection"] = "keep-alive"
    resp.headers["Content-Type"] = "text/event-stream; charset=utf-8"
    return resp


@app.route("/", methods=["GET"])
def index():
    return jsonify(
        {
            "name": "La Plata County RAG API",
            "version": RAG_CONFIG["version"],
            "description": "RAG endpoints with streaming (stubbed)",
            "endpoints": {
                "/rag/health": "Health check",
                "/rag/config": "RAG configuration",
                "/rag/answer": "Non-streaming answer (stubbed)",
                "/rag/answer/stream": "SSE streaming answer (stubbed)",
            },
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)


