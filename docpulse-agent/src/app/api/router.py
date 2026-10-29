from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
)
from app.services.rag import run_naive_rag
from core.config import Settings, get_settings
from ingestion.pipeline import ingest_path
from ingestion.vector_store import VectorStore

router = APIRouter()


def get_vector_store(settings: Settings = Depends(get_settings)) -> VectorStore:
    return VectorStore(settings)


def _data_root(settings: Settings) -> Path:
    return settings.data_dir.resolve()


def _resolve_data_path(relative: str, settings: Settings) -> Path:
    root = _data_root(settings)
    candidate = (root / relative).resolve()
    if root not in candidate.parents and candidate != root:
        raise HTTPException(status_code=400, detail="Path must stay inside data/")
    return candidate


@router.get("/health", response_model=HealthResponse)
def health(
    settings: Settings = Depends(get_settings),
    store: VectorStore = Depends(get_vector_store),
) -> HealthResponse:
    if not store.is_ready():
        return HealthResponse(
            status="degraded",
            qdrant="reachable",
            collection="missing",
            indexed_chunks=0,
        )
    try:
        count = store.count_points()
    except Exception:
        count = None
    return HealthResponse(
        status="ok",
        qdrant="reachable",
        collection=settings.qdrant_collection,
        indexed_chunks=count,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
    store: VectorStore = Depends(get_vector_store),
) -> ChatResponse:
    store.ensure_collection()
    return run_naive_rag(body.question, settings, store)


@router.post("/ingest", response_model=IngestResponse)
def ingest(
    body: IngestRequest,
    settings: Settings = Depends(get_settings),
) -> IngestResponse:
    target = _resolve_data_path(body.path, settings)
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {body.path}")
    try:
        count = ingest_path(target)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestResponse(chunks_indexed=count, path=body.path)
