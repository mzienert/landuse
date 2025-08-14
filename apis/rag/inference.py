from __future__ import annotations

from typing import Generator, Optional
import requests
import os
from flask import current_app


class ModelManager:
    """HTTP client wrapper for llama.cpp server inference.
    
    Replaces MLX Python bindings with HTTP calls to external llama.cpp server.
    Maintains the same interface for compatibility with existing RAG pipeline.
    """

    def __init__(self) -> None:
        self._model_id: Optional[str] = None
        self._max_context: Optional[int] = None
        self._service_url = os.environ.get('INFERENCE_SERVICE_URL', 'http://localhost:8003')

    @property
    def is_available(self) -> bool:
        """Check if llama.cpp server is available"""
        try:
            response = requests.get(f"{self._service_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    @property
    def is_loaded(self) -> bool:
        """Check if a model is loaded in the server"""
        return self._model_id is not None and self.is_available

    @property
    def model_id(self) -> Optional[str]:
        return self._model_id

    @property
    def max_context(self) -> Optional[int]:
        return self._max_context

    def load_model(self, model_id: str) -> dict:
        """
        For llama.cpp, 'loading' means marking the model as active.
        The actual model loading happens when the llama.cpp server starts.
        
        In future, this could restart the server with a different model.
        """
        if not self.is_available:
            raise RuntimeError("llama.cpp server is not available at " + self._service_url)

        # For now, just mark the model as loaded
        # In production, this would restart the server with the specified model
        self._model_id = model_id
        self._max_context = 4096  # Default context from llama.cpp server
        
        return {"model_id": self._model_id, "max_context": self._max_context}

    def stream_generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 1200,
        temperature: float = 0.2,
        top_p: float = 0.9,
    ) -> Generator[str, None, None]:
        """
        Generate text using llama.cpp completion API.
        
        Note: This is not actually streaming - we get the complete response
        and yield it word by word to maintain compatibility with the existing
        streaming interface.
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # Make HTTP request to llama.cpp server
            response = requests.post(
                f"{self._service_url}/completion",
                json={
                    "prompt": prompt,
                    "n_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "repeat_penalty": 1.3,  # Stronger penalty to prevent repetition
                    "repeat_last_n": 128,   # Consider more tokens for repetition detection
                    "stream": False  # Get complete response
                },
                timeout=getattr(current_app.config, 'INFERENCE_SERVICE_TIMEOUT', 300)
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the generated text
            generated_text = result.get("content", "")
            
            # Yield word by word to simulate streaming
            words = generated_text.split(" ")
            for i, word in enumerate(words):
                if i == 0:
                    yield word
                else:
                    yield " " + word

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"llama.cpp server request failed: {e}")
        except Exception as e:
            raise RuntimeError(f"llama.cpp inference failed: {e}")