from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


class SourceChunk(BaseModel):
    text: str
    score: float
    source: str | None = None
    page: int | None = None
    chunk_index: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    mode: str = "naive_rag"


class IngestRequest(BaseModel):
    path: str = Field(
        default="sample",
        description="Path relative to the data/ directory (file or folder)",
    )


class IngestResponse(BaseModel):
    chunks_indexed: int
    path: str


class HealthResponse(BaseModel):
    status: str
    qdrant: str
    collection: str
    indexed_chunks: int | None = None
