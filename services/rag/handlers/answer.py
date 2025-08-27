from flask import Blueprint, request, jsonify, current_app

answer_bp = Blueprint('answer', __name__)

@answer_bp.route('/rag/answer', methods=['POST'])
def rag_answer():
    rag_engine = current_app.config['RAG_ENGINE']
    model_mgr = rag_engine.model_mgr
    
    try:
        data = request.get_json(force=True, silent=True) or {}
        query = data.get("query", "").strip()
        collection = data.get("collection", "la_plata_county_code")
        num_results = int(data.get("num_results", 5))

        if not query:
            return jsonify({"error": "query is required"}), 400

        # If inference available, include retrieval context with query normalization
        if model_mgr and model_mgr.is_available:
            if rag_engine.fetch_simple_search and rag_engine.build_prompt_with_sources:
                try:
                    # Use enhanced retrieval with normalization
                    results, used_query = rag_engine.enhanced_retrieval_with_normalization(query, collection=collection, num_results=num_results)
                except Exception as e:
                    results = []
                    used_query = query
                    # Fall back to raw question if retrieval fails
                prompt, sources_meta = rag_engine.build_prompt_with_sources(query, results) if results else (
                    f"User question:\n{query}\n\nAnswer concisely.",
                    [],
                )
            else:
                prompt, sources_meta = f"User question:\n{query}\n\nAnswer concisely.", []
            # DEBUG: Log the prompt being sent to model
            print("=" * 80)
            print("PROMPT BEING SENT TO MODEL:")
            print(prompt)
            print("=" * 80)
            
            tokens = []
            try:
                for t in model_mgr.stream_generate(
                    prompt,
                    max_tokens=int(data.get("max_tokens", 2500)),
                    temperature=float(data.get("temperature", 0.2)),
                    top_p=float(data.get("top_p", 0.9)),
                ):
                    tokens.append(t)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
            answer_text = "".join(tokens).strip()
            
            # DEBUG: Log the model's response
            print("=" * 80)
            print("MODEL RESPONSE:")
            print(repr(answer_text))
            print("=" * 80)
            
            citations, used_sources = rag_engine.extract_citations(answer_text, sources_meta)
            if not citations and sources_meta:
                # Best-effort auto-citation fallback
                answer_text, citations, used_sources = rag_engine.auto_cite_answer(answer_text, sources_meta)

            # Lightweight verification report
            # TEMPORARILY DISABLED FOR DEBUGGING
            # annotated_answer, verification = rag_engine.verify_answer_support(answer_text, used_sources)
            # answer_text = annotated_answer
            verification = None
        else:
            answer_text = "[stub] Inference not available."

        return jsonify({
            "query": query,
            "collection": collection,
            "num_results": num_results,
            "answer": answer_text,
            "citations": citations if model_mgr and model_mgr.is_available else [],
            "sources": used_sources if model_mgr and model_mgr.is_available else [],
            "verification": verification if model_mgr and model_mgr.is_available else None,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500