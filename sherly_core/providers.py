"""
MULTI-MODEL PROVIDER ABSTRACTION — sherly_core/providers.py
Unified provider abstraction for Local Ollama, OpenAI, Google Gemini, and Groq.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger("sherly.providers")


class ModelCapability(str, Enum):
    TEXT = "text"
    CODING = "coding"
    REASONING = "reasoning"
    VISION = "vision"
    TOOL_CALLING = "tool_calling"
    STREAMING = "streaming"


class ModelMetadata(BaseModel):
    name: str
    provider: str
    family: str
    tag: str = "latest"
    size: int = 0
    local: bool = True
    capabilities: list[ModelCapability] = Field(default_factory=lambda: [ModelCapability.TEXT])
    context_limit: int = 4096


class CircuitBreaker:
    def __init__(self, fail_max: int = 3, reset_timeout: float = 30.0) -> None:
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.state = "closed"
        self.opened_at = 0.0

    def allow_call(self) -> bool:
        if self.state == "open":
            if time.time() - self.opened_at > self.reset_timeout:
                self.state = "half_open"
                return True
            return False
        return True

    def record_success(self) -> None:
        self.failures = 0
        self.state = "closed"

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.fail_max:
            self.state = "open"
            self.opened_at = time.time()


class BaseLLMProvider(ABC):
    def __init__(self, name: str) -> None:
        self.name = name
        self.breaker = CircuitBreaker(fail_max=3, reset_timeout=30.0)

    @abstractmethod
    def list_models(self) -> list[ModelMetadata]:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: float = 60.0,
    ) -> str:
        pass

    @abstractmethod
    def stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        pass

    def unload(self, model: str) -> None:
        pass


class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        super().__init__("ollama")
        self.base_url = base_url

    def health_check(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[ModelMetadata]:
        if not self.breaker.allow_call():
            return []
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=4.0)
            r.raise_for_status()
            data = r.json()
            models = []
            for m in data.get("models", []):
                raw_name = m.get("name", "")
                family = raw_name.split(":")[0] if ":" in raw_name else raw_name
                tag = raw_name.split(":")[1] if ":" in raw_name else "latest"
                is_coding = any(k in family.lower() for k in ("coder", "code", "starcoder", "deepseek"))
                caps = [ModelCapability.TEXT, ModelCapability.STREAMING, ModelCapability.TOOL_CALLING]
                if is_coding:
                    caps.append(ModelCapability.CODING)
                models.append(
                    ModelMetadata(
                        name=raw_name,
                        provider="ollama",
                        family=family,
                        tag=tag,
                        size=m.get("size", 0),
                        local=True,
                        capabilities=caps,
                    )
                )
            self.breaker.record_success()
            return models
        except Exception as exc:
            self.breaker.record_failure()
            logger.warning(f"Ollama list_models failed: {exc}")
            return []

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: float = 60.0,
    ) -> str:
        if not self.breaker.allow_call():
            raise RuntimeError("Ollama circuit breaker is OPEN")
        try:
            r = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
                timeout=timeout,
            )
            r.raise_for_status()
            self.breaker.record_success()
            return r.json().get("message", {}).get("content", "")
        except Exception:
            self.breaker.record_failure()
            raise

    def stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        if not self.breaker.allow_call():
            raise RuntimeError("Ollama circuit breaker is OPEN")
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
            timeout=60.0,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                except Exception:
                    continue

    def unload(self, model: str) -> None:
        try:
            httpx.post(
                f"{self.base_url}/api/generate",
                json={"model": model, "keep_alive": 0},
                timeout=3.0,
            )
            logger.info(f"Unloaded model {model} from Ollama VRAM.")
        except Exception as exc:
            logger.warning(f"Failed to unload {model}: {exc}")


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key_fn: Any) -> None:
        super().__init__("openai")
        self.api_key_fn = api_key_fn

    def health_check(self) -> bool:
        key = self.api_key_fn("openai")
        return bool(key and not key.startswith("YOUR_"))

    def list_models(self) -> list[ModelMetadata]:
        return [
            ModelMetadata(
                name="gpt-4o-mini",
                provider="openai",
                family="gpt-4o-mini",
                local=False,
                capabilities=[ModelCapability.TEXT, ModelCapability.CODING, ModelCapability.STREAMING, ModelCapability.TOOL_CALLING],
            ),
            ModelMetadata(
                name="gpt-4o",
                provider="openai",
                family="gpt-4o",
                local=False,
                capabilities=[ModelCapability.TEXT, ModelCapability.CODING, ModelCapability.REASONING, ModelCapability.VISION, ModelCapability.STREAMING, ModelCapability.TOOL_CALLING],
            ),
        ]

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: float = 30.0,
    ) -> str:
        key = self.api_key_fn("openai")
        if not key or key.startswith("YOUR_"):
            raise ValueError("OpenAI API key missing")
        r = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def stream(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        yield self.generate(messages, model, temperature, max_tokens)


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key_fn: Any) -> None:
        super().__init__("gemini")
        self.api_key_fn = api_key_fn

    def health_check(self) -> bool:
        key = self.api_key_fn("gemini")
        return bool(key and not key.startswith("YOUR_"))

    def list_models(self) -> list[ModelMetadata]:
        return [
            ModelMetadata(
                name="gemini-1.5-flash",
                provider="gemini",
                family="gemini-1.5-flash",
                local=False,
                capabilities=[ModelCapability.TEXT, ModelCapability.CODING, ModelCapability.STREAMING, ModelCapability.TOOL_CALLING],
            ),
            ModelMetadata(
                name="gemini-1.5-pro",
                provider="gemini",
                family="gemini-1.5-pro",
                local=False,
                capabilities=[ModelCapability.TEXT, ModelCapability.CODING, ModelCapability.REASONING, ModelCapability.STREAMING, ModelCapability.TOOL_CALLING],
            ),
        ]

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: float = 30.0,
    ) -> str:
        key = self.api_key_fn("gemini")
        if not key or key.startswith("YOUR_"):
            raise ValueError("Gemini API key missing")

        contents = []
        for m in messages:
            role = "user" if m.get("role") in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

        r = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
            json={"contents": contents, "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature}},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

    def stream(
        self,
        messages: list[dict[str, str]],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        yield self.generate(messages, model, temperature, max_tokens)


class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key_fn: Any) -> None:
        super().__init__("groq")
        self.api_key_fn = api_key_fn

    def health_check(self) -> bool:
        key = self.api_key_fn("groq")
        return bool(key and not key.startswith("YOUR_"))

    def list_models(self) -> list[ModelMetadata]:
        return [
            ModelMetadata(
                name="llama3-70b-8192",
                provider="groq",
                family="llama3",
                local=False,
                capabilities=[ModelCapability.TEXT, ModelCapability.CODING, ModelCapability.STREAMING, ModelCapability.TOOL_CALLING],
            )
        ]

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str = "llama3-70b-8192",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: float = 30.0,
    ) -> str:
        key = self.api_key_fn("groq")
        if not key or key.startswith("YOUR_"):
            raise ValueError("Groq API key missing")

        r = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def stream(
        self,
        messages: list[dict[str, str]],
        model: str = "llama3-70b-8192",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        yield self.generate(messages, model, temperature, max_tokens)
