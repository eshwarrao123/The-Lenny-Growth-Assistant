import json
import httpx
import logging
from typing import AsyncGenerator, List, Dict, Any
from app.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """
    Cloud OpenAI provider implementation.
    Requires OPENAI_API_KEY environment variable.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", embed_model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.embed_model = embed_model
        self.base_url = "https://api.openai.com/v1"

    async def generate_stream(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        if not self.api_key:
            yield {"event": "error", "data": {"code": "config_error", "message": "OpenAI API key is missing."}}
            yield {"event": "done", "data": {}}
            return

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        yield {"event": "status", "data": {"stage": "generating"}}

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", url, json=payload, headers=headers, timeout=60.0) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or line == "data: [DONE]":
                            continue
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content")
                                    if content:
                                        yield {"event": "token", "data": {"content": content}}
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to decode OpenAI stream line: {line}")
            
            yield {"event": "done", "data": {}}
                            
        except httpx.RequestError as e:
            logger.error(f"OpenAI request error: {e}")
            yield {"event": "error", "data": {"code": "provider_unavailable", "message": f"OpenAI is unreachable: {str(e)}"}}
            yield {"event": "done", "data": {}}
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI HTTP error: {e}")
            # Try to get more detail from response
            try:
                err_content = await e.response.aread()
                logger.error(f"OpenAI HTTP error detail: {err_content}")
            except:
                pass
            yield {"event": "error", "data": {"code": "provider_error", "message": f"OpenAI returned HTTP error: {e.response.status_code}"}}
            yield {"event": "done", "data": {}}
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI streaming: {e}")
            yield {"event": "error", "data": {"code": "internal_error", "message": "An unexpected error occurred during generation."}}
            yield {"event": "done", "data": {}}
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            return []
            
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"model": self.embed_model, "input": texts}, headers=headers, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data.get("data", [])]
        
    async def health_check(self) -> bool:
        if not self.api_key:
            return False
            
        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
