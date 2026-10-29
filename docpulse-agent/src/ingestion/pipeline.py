"""Ingest documents from disk into Qdrant."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from core.config import get_settings
from ingestion.chunking import chunk_text
from ingestion.parser import collect_files, read_document
from ingestion.vector_store import VectorStore

logger = logging.getLogger(__name__)

BATCH_SIZE = 32


def ingest_path(path: Path) -> int:
    settings = get_settings()
    store = VectorStore(settings)
    store.ensure_collection()

    all_chunks = []
    for file_path in collect_files(path):
        segments = read_document(file_path)
        source = str(file_path.as_posix())
        for text, page in segments:
            all_chunks.extend(
                chunk_text(
                    text,
                    source=source,
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap,
                    page=page,
                )
            )

    total = 0
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i : i + BATCH_SIZE]
        total += store.upsert_chunks(batch)
        logger.info("Upserted batch %s (%s chunks so far)", i // BATCH_SIZE + 1, total)

    return total


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Ingest documents into Qdrant")
    parser.add_argument(
        "path",
        type=Path,
        help="File or directory (.txt, .md, .pdf)",
    )
    args = parser.parse_args()
    count = ingest_path(args.path)
    logger.info("Ingestion complete: %s chunks indexed", count)


if __name__ == "__main__":
    main()
