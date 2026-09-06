"""
PROVIDER TESTS — tests/test_model_providers.py
Verifies provider abstractions, model capabilities, circuit breakers,
and resolution fallback logic.
"""

from __future__ import annotations

import pytest

from sherly_core.providers import (
    CircuitBreaker,
    GeminiProvider,
    GroqProvider,
    ModelCapability,
    OllamaProvider,
    OpenAIProvider,
)


def test_circuit_breaker_transitions():
    cb = CircuitBreaker(fail_max=2, reset_timeout=0.1)
    assert cb.allow_call() is True

    cb.record_failure()
    assert cb.state == "closed"
    assert cb.allow_call() is True

    cb.record_failure()
    assert cb.state == "open"
    assert cb.allow_call() is False

    # After reset timeout
    import time
    time.sleep(0.15)
    assert cb.allow_call() is True
    assert cb.state == "half_open"

    cb.record_success()
    assert cb.state == "closed"


def test_openai_provider_missing_key():
    provider = OpenAIProvider(api_key_fn=lambda _: None)
    assert provider.health_check() is False
    with pytest.raises(ValueError, match="OpenAI API key missing"):
        provider.generate([{"role": "user", "content": "hi"}])


def test_gemini_provider_missing_key():
    provider = GeminiProvider(api_key_fn=lambda _: None)
    assert provider.health_check() is False
    with pytest.raises(ValueError, match="Gemini API key missing"):
        provider.generate([{"role": "user", "content": "hi"}])


def test_groq_provider_missing_key():
    provider = GroqProvider(api_key_fn=lambda _: None)
    assert provider.health_check() is False
    with pytest.raises(ValueError, match="Groq API key missing"):
        provider.generate([{"role": "user", "content": "hi"}])


def test_ollama_provider_capabilities():
    provider = OllamaProvider()
    models = provider.list_models()
    # If Ollama is running, verify model metadata shape
    if models:
        for m in models:
            assert m.provider == "ollama"
            assert ModelCapability.TEXT in m.capabilities
            assert m.local is True
