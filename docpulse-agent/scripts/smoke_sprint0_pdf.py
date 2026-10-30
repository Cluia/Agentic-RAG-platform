#!/usr/bin/env python3
"""Sprint 0 checklist item 3 — PDF ingest and chat."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import httpx

from e2e_live_helpers import INGEST_TIMEOUT_SECONDS, log, post_chat

PDF_REL = "sample/acme_fy2024_summary.pdf"
MARGIN_PATTERN = re.compile(r"18\.5\s*%|18\.5", re.IGNORECASE)
REVENUE_PATTERN = re.compile(r"99", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF ingest + chat smoke")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--generate-pdf",
        action="store_true",
        help="Run generate_sample_pdf.py if PDF missing",
    )
    args = parser.parse_args()
    verbose = args.verbose

    pdf_path = Path(__file__).resolve().parents[1] / "data" / PDF_REL
    if not pdf_path.is_file():
        if args.generate_pdf:
            subprocess.run([sys.executable, "generate_sample_pdf.py"], cwd=Path(__file__).parent, check=True)
        else:
            print(f"FAIL: missing {pdf_path} (run scripts/generate_sample_pdf.py)", file=sys.stderr)
            return 1

    base = args.base_url.rstrip("/")
    with httpx.Client(base_url=base) as client:
        log(f"POST /ingest path={PDF_REL}", verbose=verbose)
        ingest = client.post("/ingest", json={"path": PDF_REL}, timeout=INGEST_TIMEOUT_SECONDS)
        if ingest.status_code == 404:
            print("FAIL: PDF not visible in container — rebuild or mount data/", file=sys.stderr)
            return 1
        ingest.raise_for_status()
        count = ingest.json().get("chunks_indexed") or 0
        log(f"ingest: chunks_indexed={count}", verbose=verbose)
        if count < 1:
            print("FAIL: PDF produced zero chunks", file=sys.stderr)
            return 1

        answer = post_chat(
            client,
            "What was Acme net margin in the FY2024 PDF sample?",
            label="chat_pdf_margin",
            verbose=verbose,
        )
        answer.raise_for_status()
        text = answer.json().get("answer", "")
        log(f"answer preview: {text[:200]}...", verbose=verbose)
        if not (MARGIN_PATTERN.search(text) or REVENUE_PATTERN.search(text)):
            print("FAIL: answer missing 18.5% or revenue 99", file=sys.stderr)
            return 1

    print("PASS: PDF ingest and chat", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
