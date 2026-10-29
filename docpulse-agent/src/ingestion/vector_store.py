"""Qdrant collection setup, upsert, and vector search."""

from __future__ import annotations

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from core.config import Settings
from core.gemini_client import GeminiClient
from ingestion.chunking import TextChunk


class VectorStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = QdrantClient(url=settings.qdrant_url)
        self._gemini = GeminiClient(settings)

    def ensure_collection(self) -> None:
        name = self._settings.qdrant_collection
        if self._client.collection_exists(name):
            return
        self._client.create_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(
                size=self._settings.embedding_dimensions,
                distance=qmodels.Distance.COSINE,
            ),
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._gemini.embed_texts(texts)

    def upsert_chunks(self, chunks: list[TextChunk]) -> int:
        if not chunks:
            return 0

        texts = [c.text for c in chunks]
        vectors = self.embed_texts(texts)
        points: list[qmodels.PointStruct] = []

        for chunk, vector in zip(chunks, vectors, strict=True):
            payload: dict[str, Any] = {
                "text": chunk.text,
                "source": chunk.source,
                "chunk_index": chunk.chunk_index,
            }
            if chunk.page is not None:
                payload["page"] = chunk.page

            points.append(
                qmodels.PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{chunk.source}:{chunk.chunk_index}:{chunk.text[:64]}")),
                    vector=vector,
                    payload=payload,
                )
            )

        self._client.upsert(
            collection_name=self._settings.qdrant_collection,
            points=points,
        )
        return len(points)

    def search(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        limit = top_k or self._settings.retrieve_top_k
        query_vector = self.embed_texts([query])[0]
        hits = self._client.search(
            collection_name=self._settings.qdrant_collection,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )
        results: list[dict[str, Any]] = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                {
                    "text": payload.get("text", ""),
                    "score": hit.score,
                    "source": payload.get("source"),
                    "page": payload.get("page"),
                    "chunk_index": payload.get("chunk_index"),
                }
            )
        return results

    def count_points(self) -> int:
        info = self._client.get_collection(self._settings.qdrant_collection)
        return info.points_count or 0

    def is_ready(self) -> bool:
        try:
            return self._client.collection_exists(self._settings.qdrant_collection)
        except Exception:
            return False
