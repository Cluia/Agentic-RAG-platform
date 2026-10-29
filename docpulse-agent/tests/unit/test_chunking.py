from ingestion.chunking import chunk_text


def test_chunk_text_overlap_and_indices():
    text = "a" * 1000
    chunks = chunk_text(
        text,
        source="demo.txt",
        chunk_size=300,
        chunk_overlap=50,
    )
    assert len(chunks) >= 3
    assert chunks[0].chunk_index == 0
    assert all(c.source == "demo.txt" for c in chunks)


def test_chunk_text_empty():
    assert chunk_text("", source="x", chunk_size=100, chunk_overlap=10) == []
