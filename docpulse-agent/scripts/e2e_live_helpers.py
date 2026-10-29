"""Shared HTTP helpers for Sprint 0 live/smoke tests (progress + retries)."""

from __future__ import annotations

import time
from typing import Any

import httpx

# One POST /chat may include several Gemini retries server-side (~5 × API latency).
CHAT_TIMEOUT_SECONDS = 420.0
INGEST_TIMEOUT_SECONDS = 120.0
HTTP_MAX_ATTEMPTS = 5


def log(message: str, *, verbose: bool = True) -> None:
    if verbose:
        elapsed = time.strftime("%H:%M:%S")
        print(f"[{elapsed}] {message}", flush=True)


def post_json_with_retry(
    client: httpx.Client,
    path: str,
    body: dict[str, Any],
    *,
    label: str,
    timeout: float = CHAT_TIMEOUT_SECONDS,
    verbose: bool = True,
    quiet: bool = False,
) -> httpx.Response:
    show = verbose and not quiet
    log(f"{label}: sending POST {path} (timeout {int(timeout)}s; Gemini may take 1–5 min)...", verbose=show)
    started = time.monotonic()
    last: httpx.Response | None = None
    for attempt in range(HTTP_MAX_ATTEMPTS):
        if attempt > 0:
            wait = 2.0 * (2 ** (attempt - 1))
            log(
                f"{label}: HTTP {last.status_code if last else '?'} — retry {attempt + 1}/{HTTP_MAX_ATTEMPTS} in {wait:.0f}s",
                verbose=show,
            )
            time.sleep(wait)
        last = client.post(path, json=body, timeout=timeout)
        if last.status_code < 500:
            elapsed = time.monotonic() - started
            log(f"{label}: done in {elapsed:.1f}s (HTTP {last.status_code})", verbose=show)
            return last
    assert last is not None
    elapsed = time.monotonic() - started
    log(f"{label}: failed after {elapsed:.1f}s (HTTP {last.status_code})", verbose=show)
    return last


def post_chat(
    client: httpx.Client,
    question: str,
    *,
    label: str,
    verbose: bool = True,
    quiet: bool = False,
) -> httpx.Response:
    short_q = question if len(question) <= 60 else f"{question[:57]}..."
    return post_json_with_retry(
        client,
        "/chat",
        {"question": question},
        label=f"{label} ({short_q})",
        verbose=verbose,
        quiet=quiet,
    )
