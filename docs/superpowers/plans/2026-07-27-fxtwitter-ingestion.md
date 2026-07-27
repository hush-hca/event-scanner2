# FxTwitter Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingest configured official X accounts and manually submitted X status URLs through FxTwitter before existing event scoring.

**Architecture:** A focused FxTwitter client normalizes v2 responses into source events. A poller submits those events to `ScannerService`, while FastAPI provides URL-ingestion and single-poll control routes.

**Tech Stack:** Python 3.12, FastAPI, httpx, Pydantic, pytest.

## Global Constraints

- Use `https://api.fxtwitter.com/2` by default and validate response HTTP status plus JSON `code`.
- Only `x.com` and `twitter.com` status URLs are accepted.
- Trust derives only from `X_WATCHED_HANDLES`; explicit token attribution is required.
- FxTwitter failures never count as confirmation or halt other account polling.

---

### Task 1: FxTwitter client and normalized post model

**Files:** Create `src/event_scanner/providers/fxtwitter.py`; modify `config.py`; create `tests/test_fxtwitter.py`.

**Interfaces:** Produces `FxTwitterClient.get_status(url) -> XPost` and `FxTwitterClient.list_statuses(handle) -> list[XPost]`.

- [ ] Write mocked tests asserting a valid API response yields `XPost(id, handle, text, url, created_at)` and a non-200 JSON `code` raises `FxTwitterError`.
- [ ] Run `pytest tests/test_fxtwitter.py -v`; implement URL/handle request construction with 10-second timeout and response validation.
- [ ] Rerun tests and commit `feat: add fxtwitter client`.

### Task 2: Trusted ingestion and poll routes

**Files:** Modify `service.py`, `main.py`, `.env.example`, `README.md`; create `tests/test_x_ingestion.py`.

**Interfaces:** Produces `ScannerService.ingest_x_post(post, token)` and routes `POST /v1/x/ingest-url`, `POST /v1/x/poll`.

- [ ] Write route tests for rejected non-status URLs, allowlisted trust, duplicate status behavior, and partial poll failures.
- [ ] Run `pytest tests/test_x_ingestion.py -v`; implement explicit token payloads, server-side handle allowlist trust, conversion to `RawEvent`, and per-handle error collection.
- [ ] Document `X_WATCHED_HANDLES`, `FXTWITTER_BASE_URL`, and the two routes. Run `pytest -v` and commit `feat: ingest X posts through fxtwitter`.

## Self-review

- The plan implements automated allowlisted polling, manual URLs, response validation, deduplication through existing source URLs, and no token inference.
- `XPost`, `FxTwitterClient`, and `ScannerService.ingest_x_post` are defined before their consumers.
