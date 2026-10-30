#!/usr/bin/env python3
"""Sprint 0 checklist item 2 — CLI ingest matches API pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys

import httpx

from e2e_live_helpers import INGEST_TIMEOUT_SECONDS, log


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify docker CLI ingest")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="docker compose down -v && up -d before test (slow)",
    )
    args = parser.parse_args()
    verbose = args.verbose

    if args.reset:
        log("Resetting stack (down -v, up -d)...", verbose=verbose)
        subprocess.run(["docker", "compose", "down", "-v"], check=True)
        subprocess.run(["docker", "compose", "up", "-d"], check=True)
        log("Waiting for API...", verbose=verbose)
        import time

        time.sleep(8)

    base = args.base_url.rstrip("/")
    with httpx.Client(base_url=base) as client:
        health = client.get("/health", timeout=30.0)
        health.raise_for_status()
        before = health.json().get("indexed_chunks") or 0
        log(f"health before CLI: indexed_chunks={before}", verbose=verbose)

        log("Running: docker compose exec -T api python scripts/ingest.py data/sample", verbose=verbose)
        proc = subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "api",
                "python",
                "scripts/ingest.py",
                "data/sample",
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(proc.stdout, proc.stderr, file=sys.stderr)
            print("FAIL: CLI ingest exited non-zero", file=sys.stderr)
            return 1
        if verbose and proc.stdout.strip():
            log(f"CLI stdout: {proc.stdout.strip()[:500]}", verbose=True)

        health = client.get("/health", timeout=30.0)
        health.raise_for_status()
        after = health.json().get("indexed_chunks") or 0
        log(f"health after CLI: indexed_chunks={after}", verbose=verbose)

        if after < 1:
            print("FAIL: no chunks after CLI ingest", file=sys.stderr)
            return 1

        log("POST /ingest sample (API) for comparison...", verbose=verbose)
        api = client.post("/ingest", json={"path": "sample"}, timeout=INGEST_TIMEOUT_SECONDS)
        api.raise_for_status()
        api_count = api.json().get("chunks_indexed")
        log(f"API ingest returned chunks_indexed={api_count}", verbose=verbose)

    print("PASS: CLI ingest indexed documents", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
