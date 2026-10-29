"""Naive RAG: retrieve chunks then generate an answer with the LLM."""

from app.api.schemas import ChatResponse, SourceChunk
from core.config import Settings
from core.gemini_client import GeminiClient
from ingestion.vector_store import VectorStore

SYSTEM_PROMPT = """You are a financial and legal document assistant.
Answer the user's question using ONLY the context below.
If the context does not contain enough information, say so clearly.
When possible, mention which source file supports your answer.
Do not invent numbers or clauses not present in the context."""


def _format_context(hits: list[dict]) -> str:
    blocks: list[str] = []
    for i, hit in enumerate(hits, start=1):
        source = hit.get("source") or "unknown"
        page = hit.get("page")
        page_info = f", page {page}" if page else ""
        blocks.append(f"[{i}] Source: {source}{page_info}\n{hit.get('text', '')}")
    return "\n\n---\n\n".join(blocks)


def run_naive_rag(
    question: str,
    settings: Settings,
    store: VectorStore,
) -> ChatResponse:
    hits = store.search(question)
    if not hits:
        return ChatResponse(
            answer="No indexed documents found. Run ingestion on the sample data first.",
            sources=[],
            mode="naive_rag",
        )

    context = _format_context(hits)
    gemini = GeminiClient(settings)
    answer = gemini.generate_answer(
        context=context,
        question=question,
        system_prompt=SYSTEM_PROMPT,
    )

    sources = [
        SourceChunk(
            text=str(hit.get("text", "")),
            score=float(hit.get("score") or 0.0),
            source=hit.get("source"),
            page=hit.get("page"),
            chunk_index=hit.get("chunk_index"),
        )
        for hit in hits
    ]
    return ChatResponse(answer=answer, sources=sources, mode="naive_rag")
