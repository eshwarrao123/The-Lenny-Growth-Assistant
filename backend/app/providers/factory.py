from app.providers.base import BaseLLMProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider
from app.core.config import get_settings

def get_llm_provider(provider_name: str) -> BaseLLMProvider:
    """
    Factory function to instantiate the correct LLM provider.
    """
    settings = get_settings()
    
    if provider_name == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            embed_model=settings.ollama_embedding_model
        )
    elif provider_name == "openai":
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            embed_model=settings.openai_embedding_model
        )
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")
