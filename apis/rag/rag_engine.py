from .config import DEFAULT_MODEL_ID

class RAGEngine:
    def __init__(self):
        self.model_mgr = None
        self.fetch_simple_search = None
        self.build_prompt_with_sources = None
        self.rerank_results = None
        self.extract_citations = None
        self.auto_cite_answer = None
        self.expand_query_with_references = None
        self.verify_answer_support = None
        self.normalize_legal_query = None
        self.get_query_variations = None
        
    def initialize(self):
        """Initialize the RAG engine with all dependencies"""
        # LangChain inference manager (loaded on demand)
        try:
            from .langchain_inference import LangChainInferenceManager
            self.model_mgr = LangChainInferenceManager()
        except Exception:
            self.model_mgr = None

        try:
            from .retrieval import (
                fetch_simple_search,
                build_prompt_with_sources,
                rerank_results,
                extract_citations,
                auto_cite_answer,
                expand_query_with_references,
            )
            from .verify import verify_answer_support
            from .normalize import normalize_legal_query, get_query_variations
            
            self.fetch_simple_search = fetch_simple_search
            self.build_prompt_with_sources = build_prompt_with_sources
            self.rerank_results = rerank_results
            self.extract_citations = extract_citations
            self.auto_cite_answer = auto_cite_answer
            self.expand_query_with_references = expand_query_with_references
            self.verify_answer_support = verify_answer_support
            self.normalize_legal_query = normalize_legal_query
            self.get_query_variations = get_query_variations
        except Exception:
            pass
            
    def auto_load_default_model(self):
        """Automatically load the default model on startup if none is loaded."""
        if self.model_mgr and not self.model_mgr.is_loaded:
            try:
                print(f"Auto-loading default model: {DEFAULT_MODEL_ID}")
                self.model_mgr.load_model(DEFAULT_MODEL_ID)
                provider_name = type(self.model_mgr.provider).__name__ if hasattr(self.model_mgr, 'provider') else 'Unknown'
                print(f"✅ Default model loaded successfully using {provider_name}")
            except Exception as e:
                print(f"⚠️  Failed to auto-load default model: {e}")
                print(f"   Model can be loaded manually via /rag/model/load endpoint")

    def enhanced_retrieval_with_normalization(self, query: str, collection: str = "la_plata_county_code", num_results: int = 5):
        """
        Perform retrieval with query normalization and fallback variations.
        
        Args:
            query: User query string
            collection: Collection to search
            num_results: Number of results to retrieve
            
        Returns:
            Tuple of (final_results, used_query) where final_results are the retrieved results
            and used_query is the query that worked best
        """
        if not self.fetch_simple_search or not self.expand_query_with_references:
            return [], query
        
        # Normalize the query
        normalized_query = self.normalize_legal_query(query)
        query_variations = self.get_query_variations(normalized_query)
        
        # Try each query variation until we get good results
        for i, variant_query in enumerate(query_variations):
            try:
                # Get initial results
                retrieval = self.fetch_simple_search(variant_query, collection=collection, num_results=num_results)
                initial_results = retrieval.get("results", [])
                
                # If we got results, apply enhanced retrieval (reference expansion)
                if initial_results:
                    expanded_results = self.expand_query_with_references(variant_query, initial_results, collection=collection)
                    final_results = self.rerank_results(variant_query, expanded_results, top_k=min(num_results, 6))
                    
                    # Return results if we found something substantial
                    if final_results:
                        # Log which query variation worked (for debugging)
                        if i > 0:  # Only log if we needed a fallback
                            print(f"Query normalization: '{query}' → '{variant_query}' (variation {i+1})")
                        return final_results, variant_query
                            
            except Exception as e:
                print(f"Error with query variation '{variant_query}': {e}")
                continue
        
        # If all variations failed, return empty results with original query
        print(f"All query variations failed for: '{query}'")
        return [], query