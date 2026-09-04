import httpx
import logging
import asyncio
from typing import List
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class OllamaEmbeddings:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")
        self.model = self.settings.ollama_embedding_model
        self.expected_dim = self.settings.pgvector_dimensions
        
        # Concurrency limit to avoid overwhelming local Ollama instance
        self.semaphore = asyncio.Semaphore(5)

    async def _embed_single(self, text: str, client: httpx.AsyncClient) -> List[float]:
        async with self.semaphore:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding", [])
            
            if len(embedding) != self.expected_dim:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.expected_dim}, got {len(embedding)}. "
                    f"Ensure Ollama model '{self.model}' is correct."
                )
            return embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a batch of texts using Ollama asynchronously.
        """
        async with httpx.AsyncClient() as client:
            tasks = [self._embed_single(text, client) for text in texts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            embeddings = []
            for i, res in enumerate(results):
                if isinstance(res, Exception):
                    logger.error(f"Failed to embed text chunk {i}: {res}")
                    raise res
                embeddings.append(res)
                
            return embeddings

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                
                has_model = any(m.get("name", "").startswith(self.model) for m in models)
                if not has_model:
                    logger.warning(f"Ollama is reachable, but model '{self.model}' was not found. Please run 'ollama pull {self.model}'.")
                    return False
                return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
