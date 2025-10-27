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
        try:
            # Check for required environment variables
            api_base = os.environ.get("OPENAI_API_BASE")
            api_key = os.environ.get("OPENAI_API_KEY")
            
            if not api_base or not api_key:
                raise ValueError("Missing required environment variables: OPENAI_API_BASE and/or OPENAI_API_KEY")
            
            # Create client with minimal configuration to avoid compatibility issues
            client = OpenAI(
                base_url=api_base,
                api_key=api_key,
            )
            return client
        except Exception as e:
            print(f"Error building Gemini client: {e}")
            raise

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
            return f"Error generating letter: {str(e)}"