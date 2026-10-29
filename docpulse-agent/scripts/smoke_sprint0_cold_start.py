#!/usr/bin/env python3
"""
Sprint 0 — cold-start smoke (run after `docker compose down -v` && `up`).

Checks: empty index → ingest sample → numeric + MSA chat answers.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time

import httpx

from e2e_live_helpers import (
    INGEST_TIMEOUT_SECONDS,
    log,
    post_chat,
)

DEFAULT_BASE = "http://localhost:8000"
NUMERIC_QUESTION = "What was Northwind net margin in FY2024?"
MSA_QUESTION = "What is the initial term of the Master Services Agreement in months?"
NUMERIC_PATTERN = re.compile(r"20\.3\s*%|20\.3", re.IGNORECASE)
MSA_PATTERN = re.compile(r"\b24\b|twenty[- ]four", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprint 0 cold-start smoke test")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("DOCPULSE_BASE_URL", DEFAULT_BASE),
    )
    parser.add_argument(
        "--require-empty",
        action="store_true",
        help="Fail if indexed_chunks != 0 before ingest",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Extra detail (HTTP retries, timings; step lines always print unless --quiet)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print PASS/FAIL and errors",
    )
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    verbose = args.verbose or not args.quiet
    quiet = args.quiet

    log("Sprint 0 cold-start smoke — expect ~2–10 min (2× /chat via Gemini)", verbose=verbose and not quiet)

    with httpx.Client(base_url=base) as client:
        log("Step 1/4: GET /health", verbose=verbose and not quiet)
        t0 = time.monotonic()
        health = client.get("/health", timeout=30.0)
        health.raise_for_status()
        payload = health.json()
        chunks = payload.get("indexed_chunks") or 0
        log(
            f"health: status={payload.get('status')} indexed_chunks={chunks} ({time.monotonic() - t0:.1f}s)",
            verbose=verbose and not quiet,
        )

        if args.require_empty and chunks != 0:
            print("FAIL: expected empty index before ingest (run docker compose down -v)", file=sys.stderr)
            return 1

        if chunks == 0:
            log("Step 2/4: POST /ingest sample", verbose=verbose and not quiet)
            ingest = client.post("/ingest", json={"path": "sample"}, timeout=INGEST_TIMEOUT_SECONDS)
            ingest.raise_for_status()
            data = ingest.json()
            log(
                f"ingest: chunks_indexed={data.get('chunks_indexed')} path={data.get('path')}",
                verbose=verbose and not quiet,
            )
        else:
            log("Step 2/4: ingest skipped (index already populated)", verbose=verbose and not quiet)

        health = client.get("/health", timeout=30.0)
        health.raise_for_status()
        chunks = health.json().get("indexed_chunks") or 0
        if chunks < 1:
            print("FAIL: no chunks after ingest", file=sys.stderr)
            return 1

        log("Step 3/4: POST /chat (numeric)", verbose=verbose and not quiet)
        numeric = post_chat(
            client,
            NUMERIC_QUESTION,
            label="chat_numeric",
            verbose=verbose,
            quiet=quiet,
        )
        numeric.raise_for_status()
        answer_num = numeric.json().get("answer", "")
        if verbose and not quiet:
            log(f"chat_numeric answer preview: {answer_num[:200]}...", verbose=True)
        if not NUMERIC_PATTERN.search(answer_num):
            print("FAIL: numeric answer missing 20.3%", file=sys.stderr)
            return 1

        log("Step 4/4: POST /chat (MSA)", verbose=verbose and not quiet)
        msa = post_chat(
            client,
            MSA_QUESTION,
            label="chat_msa",
            verbose=verbose,
            quiet=quiet,
        )
        msa.raise_for_status()
        answer_msa = msa.json().get("answer", "")
        if verbose and not quiet:
            log(f"chat_msa answer preview: {answer_msa[:200]}...", verbose=True)
        if not MSA_PATTERN.search(answer_msa):
            print("FAIL: MSA answer missing 24 months", file=sys.stderr)
            return 1

    print("PASS: Sprint 0 cold-start smoke", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
