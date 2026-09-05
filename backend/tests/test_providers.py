import pytest
from app.providers.factory import get_llm_provider
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider

def test_provider_factory():
    ollama = get_llm_provider("ollama")
    assert isinstance(ollama, OllamaProvider)
    
    openai = get_llm_provider("openai")
    assert isinstance(openai, OpenAIProvider)
    
    with pytest.raises(ValueError):
        get_llm_provider("unsupported")
