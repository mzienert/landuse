from __future__ import annotations

from typing import Generator, Optional
import threading

try:
    from mlx_lm import load as mlx_load, generate as mlx_generate
    HAS_MLX = True
except Exception:
    HAS_MLX = False


class ModelManager:
    """Lazy-loading wrapper for an MLX LLM and tokenizer.

    This class intentionally does not choose a default model. Call load_model()
    with a specific model id (e.g., 'mlx-community/Llama-3.1-8B-Instruct-4bit')
    to download/load it via MLX-LM.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._model = None
        self._tokenizer = None
        self._model_id: Optional[str] = None
        self._max_context: Optional[int] = None

    @property
    def is_available(self) -> bool:
        return HAS_MLX

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    @property
    def model_id(self) -> Optional[str]:
        return self._model_id

    @property
    def max_context(self) -> Optional[int]:
        return self._max_context

    def load_model(self, model_id: str) -> dict:
        if not HAS_MLX:
            raise RuntimeError("mlx_lm is not available. Install with: pip install mlx mlx-lm")

        with self._lock:
            model, tokenizer = mlx_load(model_id)
            # Best-effort context length inference
            try:
                max_ctx = getattr(model.config, "max_position_embeddings", None)
            except Exception:
                max_ctx = None

            self._model = model
            self._tokenizer = tokenizer
            self._model_id = model_id
            self._max_context = max_ctx

        return {"model_id": self._model_id, "max_context": self._max_context}

    def stream_generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 256,
        temperature: float = 0.2,
        top_p: float = 0.9,
    ) -> Generator[str, None, None]:
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Prefer a minimal, broadly compatible call signature.
        # Many mlx-lm versions return a full string (non-streaming). If so,
        # chunk it into small pieces to provide a streamed interface.
        try:
            try:
                result = mlx_generate(
                    self._model,
                    self._tokenizer,
                    prompt,
                    max_tokens=max_tokens,
                )
            except TypeError:
                # Super-minimal fallback
                result = mlx_generate(self._model, self._tokenizer, prompt)

            # Case 1: result is full text (str)
            if isinstance(result, str):
                # Yield in word chunks for a smoother stream
                words = result.split(" ")
                for i, w in enumerate(words):
                    yield ("" if i == 0 else " ") + w
                    # Give event loop/browsers a chance to flush
                    try:
                        import time as _t
                        _t.sleep(0.01)
                    except Exception:
                        pass
                return

            # Case 2: result is a tuple like (text, tokens/meta)
            if isinstance(result, tuple) and len(result) >= 1 and isinstance(result[0], str):
                text = result[0]
                words = text.split(" ")
                for i, w in enumerate(words):
                    yield ("" if i == 0 else " ") + w
                    try:
                        import time as _t
                        _t.sleep(0.01)
                    except Exception:
                        pass
                return

            # Case 3: result is an iterator/generator (token stream)
            if hasattr(result, "__iter__") and not isinstance(result, (bytes, str)):
                for token in result:
                    yield token
                    try:
                        import time as _t
                        _t.sleep(0.005)
                    except Exception:
                        pass
                return

            # Unknown return type; coerce to string and stream
            text = str(result)
            for i, w in enumerate(text.split(" ")):
                yield ("" if i == 0 else " ") + w
                try:
                    import time as _t
                    _t.sleep(0.01)
                except Exception:
                    pass

        except Exception as e:
            raise RuntimeError(f"MLX generate failed: {e}")


