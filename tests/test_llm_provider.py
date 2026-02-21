# tests/test_llm_provider.py
import pytest
from core.llm_provider import LLMProvider

def test_llm_provider_init_defaults_to_anthropic():
    provider = LLMProvider(provider=None, api_key="test", model="test-model")
    assert provider.provider == "anthropic"

def test_llm_provider_init_lowercases_provider():
    provider = LLMProvider(provider="OpenAI", api_key="test", model="test-model")
    assert provider.provider == "openai"

def test_llm_provider_invalid_provider_raises_error():
    with pytest.raises(ValueError, match="Unknown provider"):
        LLMProvider(provider="unknown", api_key="test", model="test")
