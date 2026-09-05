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
        self.semaphore = asyncio.Semaphore(20)

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

    async def _embed_batch_api(self, texts: List[str], client: httpx.AsyncClient) -> List[List[float]]:
        response = await client.post(
            f"{self.base_url}/api/embed",
            json={"model": self.model, "input": texts},
            timeout=120.0
        )
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings", [])
        
        for emb in embeddings:
            if len(emb) != self.expected_dim:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.expected_dim}, got {len(emb)}. "
                    f"Ensure Ollama model '{self.model}' is correct."
                )
        return embeddings

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a batch of texts using Ollama asynchronously.
        Uses /api/embed for high-throughput batching, executing sub-batches of 50 concurrently.
        """
        if not texts:
            return []
            
        batch_size = 30
        sub_batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
        
        async with httpx.AsyncClient() as client:
            async def process_sub_batch(sub_batch: List[str]) -> List[List[float]]:
                try:
                    return await self._embed_batch_api(sub_batch, client)
                except Exception as e:
                    logger.warning(f"Batch embedding failed via /api/embed, falling back to individual calls: {e}")
                    tasks = [self._embed_single(text, client) for text in sub_batch]
                    return await asyncio.gather(*tasks, return_exceptions=False)

            results = await asyncio.gather(*[process_sub_batch(sb) for sb in sub_batches])
            
        all_embeddings = []
        for res in results:
            all_embeddings.extend(res)
            
        return all_embeddings

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
