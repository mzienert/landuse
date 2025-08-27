from flask import Blueprint, request, Response, jsonify, current_app, stream_with_context
import json
import time

stream_bp = Blueprint('stream', __name__)

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

@stream_bp.route('/rag/answer/stream', methods=['POST', 'GET'])
def rag_answer_stream():
    rag_engine = current_app.config['RAG_ENGINE']
    model_mgr = rag_engine.model_mgr
    
    if request.method == "GET":
        data = {
            "query": request.args.get("query", ""),
            "collection": request.args.get("collection", "la_plata_county_code"),
            "num_results": request.args.get("num_results", 5),
            "max_tokens": request.args.get("max_tokens", 1200),
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
            # Retrieval with query normalization
            sources_meta = []
            if rag_engine.fetch_simple_search and rag_engine.build_prompt_with_sources:
                try:
                    k = int(data.get("num_results", 5))
                    # Use enhanced retrieval with normalization
                    results, used_query = rag_engine.enhanced_retrieval_with_normalization(query, collection=collection, num_results=k)
                    prompt, sources_meta = rag_engine.build_prompt_with_sources(query, results)
                except Exception as e:
                    prompt = f"User question:\n{query}\n\nAnswer concisely."
            else:
                prompt = f"User question:\n{query}\n\nAnswer concisely."
            # DEBUG: Log the prompt being sent to model
            print("=" * 80)
            print("STREAMING PROMPT BEING SENT TO MODEL:")
            print(prompt)
            print("=" * 80)
            
            try:
                tokens = []
                for t in model_mgr.stream_generate(
                    prompt,
                    max_tokens=int(data.get("max_tokens", 1200)),
                    temperature=float(data.get("temperature", 0.2)),
                    top_p=float(data.get("top_p", 0.9)),
                ):
                    tokens.append(t)
                    yield _sse({"event": "token", "text": t})
                
                # DEBUG: Log the complete model response
                complete_response = "".join(tokens)
                print("=" * 80)
                print("STREAMING MODEL RESPONSE:")
                print(repr(complete_response))
                print("=" * 80)
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