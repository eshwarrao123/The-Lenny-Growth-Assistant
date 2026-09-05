import json
import httpx
import logging
from typing import AsyncGenerator, List, Dict, Any
from app.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    """
    Local Ollama provider implementation.
    Connects to local Ollama daemon (e.g. host.docker.internal:11434).
    """
    
    def __init__(self, base_url: str, model: str = "qwen2.5:7b", embed_model: str = "nomic-embed-text"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embed_model = embed_model

    async def generate_stream(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        
        yield {"event": "status", "data": {"stage": "generating"}}

        try:
            timeout_config = httpx.Timeout(300.0, connect=30.0)
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                token = data["message"]["content"]
                                if token:
                                    yield {"event": "token", "data": {"content": token}}
                            if data.get("done"):
                                yield {"event": "done", "data": {}}
                                return
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode Ollama stream line: {line}")
                            
        except httpx.RequestError as e:
            logger.error(f"Ollama request error ({type(e).__name__}): {e}")
            yield {"event": "error", "data": {"code": "provider_unavailable", "message": f"Ollama is unreachable or timed out: {str(e)}"}}
            yield {"event": "done", "data": {}}
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error ({e.response.status_code}): {e}")
            yield {"event": "error", "data": {"code": "provider_error", "message": f"Ollama returned HTTP error: {e.response.status_code}"}}
            yield {"event": "done", "data": {}}
        except Exception as e:
            logger.error(f"Unexpected error in Ollama streaming: {e}")
            yield {"event": "error", "data": {"code": "internal_error", "message": "An unexpected error occurred during generation."}}
            yield {"event": "done", "data": {}}
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Usually we use OllamaEmbeddings class from rag module directly, but this is the interface
        url = f"{self.base_url}/api/embed"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"model": self.embed_model, "input": texts}, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            return data.get("embeddings", [])
        
    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                has_model = any(m.get("name", "").startswith(self.model) for m in models)
                return has_model
        except Exception:
            return False

    async def detailed_health_check(self) -> Dict[str, Any]:
        """Fast tag-based health inspection checking model availability without running inference."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    return {"status": "unavailable", "reachable": False}
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                has_chat = any(name.startswith(self.model) for name in model_names)
                has_embed = any(name.startswith(self.embed_model) for name in model_names)
                if has_chat and has_embed:
                    return {"status": "ok", "reachable": True, "chat_model": True, "embed_model": True}
                elif has_chat or has_embed:
                    return {"status": "degraded", "reachable": True, "chat_model": has_chat, "embed_model": has_embed}
                else:
                    return {"status": "degraded", "reachable": True, "chat_model": False, "embed_model": False}
        except Exception:
            return {"status": "unavailable", "reachable": False}

