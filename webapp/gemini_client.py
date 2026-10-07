"""Simple Gemini API client using OpenAI library.

This module provides a basic client for calling the Gemini API using OpenAI's interface.
"""
import os
from openai import OpenAI


class GeminiClient:
    def __init__(self, model_name: str = "gemini-3.8-flash"):
        self.model = model_name
        self._client = self._build_client()

    def _build_client(self):
        """Build OpenAI client configured for Gemini API"""
        api_base = os.environ.get("OPENAI_API_BASE")
        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_base or not api_key:
            raise ValueError("Missing required environment variables: OPENAI_API_BASE and/or OPENAI_API_KEY")

        return OpenAI(base_url=api_base, api_key=api_key)

    def complete(self, messages: list[dict], temperature: float = 0.0) -> str:
        """Send a list of chat messages to Gemini and return the reply text.

        Raises on API errors or an empty response so callers can report them.
        """
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            top_p=1.0,
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise RuntimeError("The model returned an empty response.")
        return content.strip()
