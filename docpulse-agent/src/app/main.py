from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from core.config import get_settings
from ingestion.vector_store import VectorStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    store = VectorStore(settings)
    store.ensure_collection()
    yield


app = FastAPI(
    title="DocPulse API",
    description="Sprint 0 — baseline naive RAG over Qdrant",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "DocPulse",
        "docs": "/docs",
        "health": "/health",
    }
