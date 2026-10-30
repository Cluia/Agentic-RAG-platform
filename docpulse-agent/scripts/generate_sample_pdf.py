"""Generate a minimal one-page PDF for Sprint 0 ingest tests."""

from __future__ import annotations

from pathlib import Path

# Minimal valid PDF 1.4 with one line of text (no external deps).
PDF_BYTES = b"""%PDF-1.4
1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj
2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj
3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj
4 0 obj<< /Length 105 >>stream
BT /F1 12 Tf 72 720 Td (Acme Holdings FY2024 PDF sample. Revenue USD 99.0 million. Net margin 18.5 percent.) Tj ET
endstream endobj
5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000423 00000 n 
trailer<< /Size 6 /Root 1 0 R >>
startxref
502
%%EOF"""


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "data" / "sample" / "acme_fy2024_summary.pdf"
    out.write_bytes(PDF_BYTES)
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
