from typing import Generator, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tracers.langchain import LangChainTracer
from langsmith import Client
from .llm_provider import LLMProviderFactory
from flask import current_app
import os

class LangChainInferenceManager:
    """LangChain-based inference manager replacing direct HTTP calls"""
    
    def __init__(self):
        self.provider = None
        self.langsmith_client = None
        self.tracer = None
        self._model_id: Optional[str] = None
        self._max_context: Optional[int] = 4096
        self._setup_langsmith()
        self._load_provider()
    
    def _setup_langsmith(self):
        """Setup LangSmith tracing if enabled"""
        try:
            if os.getenv('LANGSMITH_TRACING', 'false').lower() == 'true':
                api_key = os.getenv('LANGSMITH_API_KEY')
                project = os.getenv('LANGSMITH_PROJECT', 'landuse-rag')
                
                if api_key:
                    self.langsmith_client = Client(api_key=api_key)
                    self.tracer = LangChainTracer(
                        project_name=project,
                        client=self.langsmith_client
                    )
                    current_app.logger.info(f"LangSmith tracing enabled for project: {project}")
                else:
                    current_app.logger.warning("LANGSMITH_API_KEY not set, tracing disabled")
        except Exception as e:
            current_app.logger.error(f"Failed to setup LangSmith: {e}")
    
    def _load_provider(self):
        """Load and cache the appropriate LLM provider"""
        try:
            self.provider = LLMProviderFactory.get_available_provider()
            current_app.logger.info(f"Loaded LLM provider: {type(self.provider).__name__}")
        except Exception as e:
            current_app.logger.error(f"Failed to load LLM provider: {e}")
            raise RuntimeError("No LLM providers available")
    
    @property
    def is_available(self) -> bool:
        """Check if inference is available"""
        return self.provider is not None and self.provider.is_available()
    
    @property
    def is_loaded(self) -> bool:
        """Check if a model is loaded - always True for LangChain providers"""
        return self.is_available
    
    @property
    def model_id(self) -> Optional[str]:
        return self._model_id
    
    @property
    def max_context(self) -> Optional[int]:
        return self._max_context
    
    def load_model(self, model_id: str) -> dict:
        """
        For LangChain providers, 'loading' means marking the model as active.
        The actual model is already configured in the provider.
        """
        if not self.is_available:
            raise RuntimeError("LLM provider is not available")
        
        self._model_id = model_id
        return {"model_id": self._model_id, "max_context": self._max_context}
    
    def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text using LangChain provider"""
        if not self.is_available:
            self._load_provider()
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        try:
            # Add LangSmith tracing if enabled
            if self.tracer:
                kwargs['callbacks'] = [self.tracer]
            
            return self.provider.generate(messages, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Text generation failed: {e}")
            raise RuntimeError(f"Text generation failed: {e}")
    
    def stream_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream text using LangChain provider"""
        if not self.is_available:
            self._load_provider()
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        try:
            # Add LangSmith tracing if enabled
            if self.tracer:
                kwargs['callbacks'] = [self.tracer]
                
            yield from self.provider.stream_generate(messages, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Text streaming failed: {e}")
            raise RuntimeError(f"Text streaming failed: {e}")
    
    def stream_generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 1200,
        temperature: float = 0.2,
        top_p: float = 0.9,
    ) -> Generator[str, None, None]:
        """
        Generate text maintaining compatibility with existing ModelManager interface.
        Uses LangChain provider instead of direct HTTP calls.
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # Use the stream_text method with compatible parameters
            # Note: LangChain providers already have temperature=0.1 configured
            yield from self.stream_text(
                prompt=prompt,
                max_tokens=max_tokens,
                top_p=top_p
            )
        except Exception as e:
            current_app.logger.error(f"Stream generation failed: {e}")
            raise RuntimeError(f"LangChain inference failed: {e}")
    
    def reload_provider(self, env: Optional[str] = None):
        """Reload provider for different environment"""
        try:
            if env:
                self.provider = LLMProviderFactory.get_provider(env)
            else:
                self.provider = LLMProviderFactory.get_available_provider()
            current_app.logger.info(f"Reloaded LLM provider: {type(self.provider).__name__}")
        except Exception as e:
            current_app.logger.error(f"Failed to reload LLM provider: {e}")
            raise RuntimeError("Failed to reload LLM provider")