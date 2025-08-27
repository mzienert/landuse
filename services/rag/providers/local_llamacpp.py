from typing import Iterator
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from .base import LLMProvider
from ..config import Config


class LocalLlamaCppProvider(LLMProvider):
    """LangChain provider for local llama.cpp HTTP server"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or Config.LLAMA_CPP_BASE_URL
        self.llm = ChatOpenAI(
            base_url=self.base_url,
            api_key="dummy",  # llama.cpp doesn't validate
            model="gpt-3.5-turbo",  # Placeholder, ignored by llama.cpp
            temperature=Config.GENERATION_TEMPERATURE,
            max_tokens=Config.GENERATION_MAX_TOKENS,
            seed=Config.GENERATION_SEED,
            # Note: repeat_penalty not supported in OpenAI-compatible API
            # llama.cpp server should be configured with these parameters
        )
    
    def generate(self, messages: list[BaseMessage], **kwargs) -> str:
        """Generate response using local llama.cpp server"""
        response = self.llm.invoke(messages, **kwargs)
        return response.content
    
    def stream_generate(self, messages: list[BaseMessage], **kwargs) -> Iterator[str]:
        """Stream response using local llama.cpp server"""
        for chunk in self.llm.stream(messages, **kwargs):
            if chunk.content:
                yield chunk.content
    
    def is_available(self) -> bool:
        """Check if llama.cpp server is responding"""
        try:
            import requests
            health_url = Config.LLAMA_CPP_HEALTH_URL or f"{self.base_url.replace('/v1', '')}/health"
            response = requests.get(health_url, timeout=Config.PROVIDER_HEALTH_CHECK_TIMEOUT)
            return response.status_code == 200
        except:
            return False