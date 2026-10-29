"""Split document text into overlapping chunks for embedding."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    text: str
    chunk_index: int
    source: str
    page: int | None = None


def chunk_text(
    text: str,
    *,
    source: str,
    chunk_size: int,
    chunk_overlap: int,
    page: int | None = None,
) -> list[TextChunk]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    length = len(normalized)

    while start < length:
        end = min(start + chunk_size, length)
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(
                TextChunk(
                    text=piece,
                    chunk_index=index,
                    source=source,
                    page=page,
                )
            )
            index += 1
        if end >= length:
            break
        start = end - chunk_overlap

    return chunks
