from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any

class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers (e.g. Ollama, OpenAI).
    Ensures unified integration points for the API routes.
    """
    
    @abstractmethod
    async def generate_stream(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams structured tokens, sources, and artifact events based on SSE contract.
        """
        pass
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates dense vector embeddings for retrieval and ingestion.
        """
        pass
        
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Validates provider availability without causing exceptions.
        """
        pass
