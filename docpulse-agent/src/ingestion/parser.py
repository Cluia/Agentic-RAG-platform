"""Load plain text and PDF files into page-level text segments."""

from pathlib import Path

import pdfplumber

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def read_document(path: Path) -> list[tuple[str, int | None]]:
    """
    Return (text, page_number) segments.
    Plain text uses a single segment with page=None.
    PDFs yield one segment per page (1-based page index).
    """
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. Use one of: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8")
        return [(text, None)]

    pages: list[tuple[str, int | None]] = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append((page_text, page_num))
    return pages


def collect_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        files = [
            p
            for p in sorted(path.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        if not files:
            raise FileNotFoundError(f"No supported documents under {path}")
        return files
    raise FileNotFoundError(f"Path not found: {path}")
