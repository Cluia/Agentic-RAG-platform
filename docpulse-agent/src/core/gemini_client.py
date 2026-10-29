"""Google Gemini API — embeddings and text generation."""

from __future__ import annotations

import logging
import time

from google import genai
from google.genai import types
from google.genai.errors import ServerError

from core.config import Settings

logger = logging.getLogger(__name__)

_CHAT_MAX_ATTEMPTS = 5
_CHAT_BACKOFF_SECONDS = 2.0


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
            config=types.EmbedContentConfig(
                output_dimensionality=self._settings.embedding_dimensions,
            ),
        )
        if not response.embeddings:
            return []
        return [list(item.values) for item in response.embeddings]

    def generate_answer(self, *, context: str, question: str, system_prompt: str) -> str:
        prompt = f"Context:\n{context}\n\nQuestion: {question}"
        last_error: Exception | None = None
        for attempt in range(_CHAT_MAX_ATTEMPTS):
            try:
                response = self._client.models.generate_content(
                    model=self._settings.chat_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.2,
                    ),
                )
                return (response.text or "").strip()
            except ServerError as exc:
                last_error = exc
                if attempt + 1 >= _CHAT_MAX_ATTEMPTS:
                    break
                wait = _CHAT_BACKOFF_SECONDS * (2**attempt)
                logger.warning(
                    "Gemini chat unavailable (attempt %s/%s): %s — retry in %.0fs",
                    attempt + 1,
                    _CHAT_MAX_ATTEMPTS,
                    exc,
                    wait,
                )
                time.sleep(wait)
        assert last_error is not None
        raise last_error
