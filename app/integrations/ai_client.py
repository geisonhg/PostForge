"""
PostForge — AI Client
Centralized interface to Anthropic Claude API.
Designed to be swappable with OpenAI or other providers.
"""
import json
from typing import Any
from loguru import logger

import anthropic

from app.config import get_settings

settings = get_settings()


class AIClient:
    """Thin wrapper around the Anthropic client for PostForge use cases."""

    def __init__(self):
        self._client: anthropic.Anthropic | None = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            if not settings.anthropic_api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY is not set. Add it to your .env file."
                )
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    def complete(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """
        Send a prompt to Claude and return the text response.
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs: dict[str, Any] = {
            "model": settings.anthropic_model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        logger.debug(f"AI request → model={settings.anthropic_model} tokens={max_tokens}")

        response = self.client.messages.create(**kwargs)
        text = response.content[0].text
        logger.debug(f"AI response received ({len(text)} chars)")
        return text

    def complete_json(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 2048,
    ) -> dict:
        """
        Send a prompt expecting a JSON response.
        Strips markdown code fences if present.
        """
        raw = self.complete(prompt=prompt, system=system, max_tokens=max_tokens)

        # Strip markdown fences
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {e}\nRaw: {raw[:500]}")
            raise ValueError(f"AI returned invalid JSON: {e}") from e


# Singleton instance
ai_client = AIClient()
