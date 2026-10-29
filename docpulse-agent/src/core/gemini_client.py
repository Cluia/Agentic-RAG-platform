"""Google Gemini API — embeddings and text generation."""

from __future__ import annotations

from google import genai
from google.genai import types

from core.config import Settings


class GeminiClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.models.embed_content(
            model=self._settings.embedding_model,
            contents=texts,
        )
        if not response.embeddings:
            return []
        return [list(item.values) for item in response.embeddings]

    def generate_answer(self, *, context: str, question: str, system_prompt: str) -> str:
        prompt = f"Context:\n{context}\n\nQuestion: {question}"
        response = self._client.models.generate_content(
            model=self._settings.chat_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            ),
        )
        return (response.text or "").strip()
