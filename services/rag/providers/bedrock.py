from typing import Iterator
from langchain_aws import ChatBedrock
from langchain_core.messages import BaseMessage, HumanMessage
from .base import LLMProvider
from ..config import Config


class BedrockProvider(LLMProvider):
    """LangChain provider for AWS Bedrock with configurable model"""
    
    def __init__(self, model_id: str, region: str = None):
        self.region = region or Config.AWS_REGION
        self.model_id = model_id
        self.llm = ChatBedrock(
            model_id=model_id,
            region=self.region,
            model_kwargs={
                "temperature": Config.GENERATION_TEMPERATURE,
                "max_tokens": Config.GENERATION_MAX_TOKENS
            }
        )
    
    def generate(self, messages: list[BaseMessage], **kwargs) -> str:
        """Generate response using AWS Bedrock"""
        response = self.llm.invoke(messages, **kwargs)
        return response.content
    
    def stream_generate(self, messages: list[BaseMessage], **kwargs) -> Iterator[str]:
        """Stream response using AWS Bedrock"""
        for chunk in self.llm.stream(messages, **kwargs):
            if chunk.content:
                yield chunk.content
    
    def is_available(self) -> bool:
        """Check if AWS Bedrock is accessible"""
        try:
            # Simple test call with minimal content
            test_messages = [HumanMessage(content="Hi")]
            self.llm.invoke(test_messages, max_tokens=1)
            return True
        except:
            return False