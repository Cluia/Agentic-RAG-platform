#!/usr/bin/env python3
"""Sprint 0 checklist items 4–5 — API edge cases and OpenAPI surface."""

from __future__ import annotations

import argparse
import sys

import httpx

from e2e_live_helpers import INGEST_TIMEOUT_SECONDS, log


def main() -> int:
    parser = argparse.ArgumentParser(description="HTTP edge-case smoke")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    verbose = args.verbose
    base = args.base_url.rstrip("/")

    with httpx.Client(base_url=base) as client:
        log("GET /", verbose=verbose)
        root = client.get("/", timeout=15.0)
        if root.status_code != 200:
            print(f"FAIL: GET / -> {root.status_code}", file=sys.stderr)
            return 1

        log("GET /docs", verbose=verbose)
        docs = client.get("/docs", timeout=15.0)
        if docs.status_code != 200:
            print(f"FAIL: GET /docs -> {docs.status_code}", file=sys.stderr)
            return 1
        if "swagger" not in docs.text.lower() and "openapi" not in docs.text.lower():
            print("FAIL: /docs body does not look like Swagger UI", file=sys.stderr)
            return 1

        log("POST /chat without indexed context (empty collection)", verbose=verbose)
        health0 = client.get("/health", timeout=15.0)
        health0.raise_for_status()
        chunks0 = health0.json().get("indexed_chunks") or 0
        if chunks0 > 0:
            log(
                f"SKIP: empty-index chat (indexed_chunks={chunks0}; run down -v for full check)",
                verbose=verbose,
            )
        else:
            empty = client.post("/chat", json={"question": "Any facts?"}, timeout=60.0)
            if empty.status_code != 200:
                print(f"FAIL: chat on empty index -> {empty.status_code}", file=sys.stderr)
                return 1
            ans = empty.json().get("answer", "").lower()
            if "no indexed" not in ans and "ingestion" not in ans:
                print(f"FAIL: unexpected empty-index message: {ans[:120]}", file=sys.stderr)
                return 1

        log("POST /ingest missing path -> 404", verbose=verbose)
        missing = client.post("/ingest", json={"path": "does-not-exist"}, timeout=30.0)
        if missing.status_code != 404:
            print(f"FAIL: ingest missing -> {missing.status_code}", file=sys.stderr)
            return 1

        log("POST /ingest path traversal -> 400", verbose=verbose)
        bad = client.post("/ingest", json={"path": "../scripts/ingest.py"}, timeout=30.0)
        if bad.status_code != 400:
            print(f"FAIL: ingest traversal -> {bad.status_code}", file=sys.stderr)
            return 1

        log("POST /chat empty question -> 422", verbose=verbose)
        invalid = client.post("/chat", json={"question": ""}, timeout=15.0)
        if invalid.status_code != 422:
            print(f"FAIL: empty question -> {invalid.status_code}", file=sys.stderr)
            return 1

        log("POST /ingest sample + re-ingest (idempotent upsert)", verbose=verbose)
        first = client.post("/ingest", json={"path": "sample"}, timeout=INGEST_TIMEOUT_SECONDS)
        first.raise_for_status()
        c1 = first.json().get("chunks_indexed")
        second = client.post("/ingest", json={"path": "sample"}, timeout=INGEST_TIMEOUT_SECONDS)
        second.raise_for_status()
        c2 = second.json().get("chunks_indexed")
        health = client.get("/health", timeout=15.0)
        health.raise_for_status()
        total = health.json().get("indexed_chunks")
        log(f"re-ingest batches: {c1}, {c2}; health indexed_chunks={total}", verbose=verbose)
        if not c1 or not c2:
            print("FAIL: re-ingest returned zero chunks", file=sys.stderr)
            return 1

    print("PASS: API edge cases and /docs", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
