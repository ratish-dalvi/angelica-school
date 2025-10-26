"""Simple Gemini API client using OpenAI library.

This module provides a basic client for calling the Gemini API using OpenAI's interface.
"""
import os
from openai import OpenAI


class GeminiClient:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model = model_name
        self._client = self._build_client()

    def _build_client(self):
        """Build OpenAI client configured for Gemini API"""
        return OpenAI(
            base_url=os.environ["OPENAI_API_BASE"],
            api_key=os.environ["OPENAI_API_KEY"],
        )

    def ask_gemini(self, question: str) -> str:
        """Send a simple text question to Gemini"""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question}
                        ],
                    }
                ],
                temperature=0.0,
                top_p=1.0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return ""