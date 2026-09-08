"""BYOK LLM Client supporting Anthropic, OpenAI, and OpenAI-compatible endpoints."""

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional

from volf.credentials import load_credentials


@dataclass
class LLMConfig:
    provider: str
    api_key: str
    model: str
    base_url: Optional[str] = None
    timeout_seconds: int = 60


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


def resolve_llm_config(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Optional[LLMConfig]:
    """Resolve LLM configuration from parameters, environment variables, or stored credentials."""
    key = api_key or os.environ.get("VOLF_LLM_KEY")
    url = base_url or os.environ.get("OPENAI_BASE_URL")

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    # If no explicit args or env vars, check ~/.volf/credentials.json
    if not key and not anthropic_key and not openai_key and not url:
        try:
            stored = load_credentials()
            if stored:
                stored_prov = stored.get("provider", "openai").lower()
                stored_key = stored.get("api_key")
                stored_model = model or stored.get("model")
                stored_url = url or stored.get("base_url")

                if stored_prov == "anthropic" or (stored_key and stored_key.startswith("sk-ant-")):
                    return LLMConfig(
                        provider="anthropic",
                        api_key=stored_key,
                        model=stored_model or "claude-3-5-sonnet-20241022",
                        base_url=stored_url,
                    )
                elif stored_prov in ("ollama", "local", "openai_compatible"):
                    return LLMConfig(
                        provider="openai_compatible",
                        api_key=stored_key or "ollama_or_local",
                        model=stored_model or "deepseek-coder",
                        base_url=stored_url or "http://localhost:11434/v1",
                    )
                else:
                    return LLMConfig(
                        provider="openai",
                        api_key=stored_key,
                        model=stored_model or "gpt-4o",
                        base_url=stored_url,
                    )
        except Exception:
            pass

    if key:
        if key.startswith("sk-ant-") or (model and "claude" in model.lower()):
            return LLMConfig(
                provider="anthropic",
                api_key=key,
                model=model or "claude-3-5-sonnet-20241022",
                base_url=url,
            )
        return LLMConfig(
            provider="openai",
            api_key=key,
            model=model or "gpt-4o",
            base_url=url,
        )

    if anthropic_key:
        return LLMConfig(
            provider="anthropic",
            api_key=anthropic_key,
            model=model or "claude-3-5-sonnet-20241022",
            base_url=url,
        )

    if openai_key:
        return LLMConfig(
            provider="openai",
            api_key=openai_key,
            model=model or "gpt-4o",
            base_url=url,
        )

    if url:
        return LLMConfig(
            provider="openai_compatible",
            api_key="ollama_or_local",
            model=model or "deepseek-coder",
            base_url=url,
        )

    return None


class LLMClient:
    """Zero-dependency HTTP client for LLM API calls."""

    def __init__(self, config: LLMConfig):
        self.config = config

    def complete(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> LLMResponse:
        """Send completion request to configured provider."""
        if self.config.provider == "anthropic":
            return self._call_anthropic(messages, system_prompt)
        return self._call_openai(messages, system_prompt)

    def _call_anthropic(self, messages: List[Dict[str, str]], system_prompt: Optional[str]) -> LLMResponse:
        url = self.config.base_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
        }

        payload: Dict[str, object] = {
            "model": self.config.model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system_prompt:
            payload["system"] = system_prompt

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            model=data.get("model", self.config.model),
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
        )

    def _call_openai(self, messages: List[Dict[str, str]], system_prompt: Optional[str]) -> LLMResponse:
        base = self.config.base_url or "https://api.openai.com/v1"
        url = f"{base.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload = {
            "model": self.config.model,
            "messages": formatted_messages,
            "temperature": 0.0,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        content = ""
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")

        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            model=data.get("model", self.config.model),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
