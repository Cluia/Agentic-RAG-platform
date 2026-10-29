"""Live E2E against a running DocPulse stack (optional CI/local gate)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import pytest

# Reuse smoke HTTP helpers (progress + timeouts).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from e2e_live_helpers import (  # noqa: E402
    CHAT_TIMEOUT_SECONDS,
    INGEST_TIMEOUT_SECONDS,
    log,
    post_chat,
)

pytestmark = pytest.mark.e2e

BASE = os.environ.get("DOCPULSE_BASE_URL", "http://localhost:8000").rstrip("/")
RUN_LIVE = os.environ.get("DOCPULSE_E2E", "").lower() in {"1", "true", "yes"}
E2E_VERBOSE = os.environ.get("DOCPULSE_E2E_VERBOSE", "1").lower() in {"1", "true", "yes"}


def _skip_unless_live() -> None:
    if not RUN_LIVE:
        pytest.skip("Set DOCPULSE_E2E=1 to run live stack tests")


def test_cold_start_numeric_and_msa() -> None:
    _skip_unless_live()
    log("E2E: starting (run pytest with -s to see progress)", verbose=E2E_VERBOSE)
    with httpx.Client(base_url=BASE, timeout=CHAT_TIMEOUT_SECONDS) as client:
        log("E2E: GET /health", verbose=E2E_VERBOSE)
        health = client.get("/health")
        health.raise_for_status()
        if (health.json().get("indexed_chunks") or 0) == 0:
            log("E2E: POST /ingest sample", verbose=E2E_VERBOSE)
            ingest = client.post("/ingest", json={"path": "sample"}, timeout=INGEST_TIMEOUT_SECONDS)
            ingest.raise_for_status()
            assert ingest.json()["chunks_indexed"] >= 1

        numeric = post_chat(
            client,
            "What was Northwind net margin in FY2024?",
            label="E2E chat_numeric",
            verbose=E2E_VERBOSE,
        )
        numeric.raise_for_status()
        assert "20.3" in numeric.json()["answer"]

        msa = post_chat(
            client,
            "What is the initial term of the Master Services Agreement in months?",
            label="E2E chat_msa",
            verbose=E2E_VERBOSE,
        )
        msa.raise_for_status()
        answer = msa.json()["answer"].lower()
        assert "24" in answer or "twenty-four" in answer or "twenty four" in answer
        log("E2E: assertions passed", verbose=E2E_VERBOSE)
