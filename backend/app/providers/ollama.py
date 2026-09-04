from typing import AsyncGenerator, List, Dict, Any
from app.providers.base import BaseLLMProvider

class OllamaProvider(BaseLLMProvider):
    """
    Local Ollama provider implementation.
    Connects to local Ollama daemon (e.g. host.docker.internal:11434).
    """
    
    def __init__(self, base_url: str, model: str = "qwen2.5:7b", embed_model: str = "nomic-embed-text"):
        self.base_url = base_url
        self.model = model
        self.embed_model = embed_model

    async def generate_stream(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        # Skeleton implementation
        yield {"event": "status", "data": {"message": "Streaming from local Ollama..."}}
        yield {"event": "done", "data": {}}
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Skeleton implementation
        return [[0.0] * 768 for _ in texts]
        
    async def health_check(self) -> bool:
        # Skeleton implementation
        return True
