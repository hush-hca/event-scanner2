# Crypto Event-Driven Scanner MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an API that ingests trusted crypto events, verifies Binance USDT perpetual market reactions, records an auditable score, and sends Telegram alerts.

**Architecture:** FastAPI routes hand events to a typed rules engine. Provider adapters collect Binance/RSS evidence, a SQLite repository stores audit records, and a Telegram adapter sends High alerts. X and on-chain providers arrive through the same authenticated event-ingestion route.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy async, httpx, feedparser, APScheduler, SQLite, pytest.

## Global Constraints

- Monitor Binance USDT perpetual symbols only.
- High requires a trusted structural-risk event and at least one market or on-chain confirmation.
- Store times in UTC, display KST in alerts, and never log API keys or bot tokens.
- No order placement, custody, or investment-performance claims.

---

### Task 1: Application contracts and health endpoint

**Files:** Create `pyproject.toml`, `.env.example`, `README.md`, `src/event_scanner/config.py`, `src/event_scanner/domain.py`, `src/event_scanner/main.py`, and `tests/test_health.py`.

**Interfaces:** Produces `Settings`, `RawEvent`, `EventAssessment`, `SignalLevel`, and `create_app()`.

- [ ] Write a failing health test:

```python
def test_health_is_ok(client):
    assert client.get('/health').json() == {'status': 'ok'}
```

- [ ] Run `pytest tests/test_health.py -v`; implement `create_app()` with `GET /health`; rerun the test and `ruff check .`.
- [ ] Commit with `git commit -m "feat: bootstrap event scanner service"`.

### Task 2: Structural-risk scoring and perpetual symbol mapping

**Files:** Create `src/event_scanner/scoring.py`, `src/event_scanner/catalog.py`, and `tests/test_scoring.py`.

**Interfaces:** Consumes `RawEvent`; produces `assess_event(event, catalog, snapshot, onchain) -> EventAssessment`.

- [ ] Write failing tests:

```python
def test_trusted_hack_with_market_confirmation_is_high():
    assert assess_event(hack_event(), {'ABC': 'ABCUSDT'}, market_drop(), None).level.value == 'high'

def test_unmapped_token_is_hold():
    assert assess_event(hack_event('MISSING'), {}, market_drop(), None).level.value == 'hold'
```

- [ ] Run `pytest tests/test_scoring.py -v`; implement scores for structural terms, trusted source, mapping, market change, on-chain confirmation, and liquidity. Use High `>=70` plus confirmation, Medium `>=45`, otherwise Hold.
- [ ] Rerun tests/lint and commit `feat: add structural risk scoring`.

### Task 3: Providers, audit store, and Telegram formatting

**Files:** Create `src/event_scanner/providers/binance.py`, `src/event_scanner/providers/rss.py`, `src/event_scanner/repository.py`, `src/event_scanner/notifier.py`, `tests/test_binance.py`, and `tests/test_notifier.py`.

**Interfaces:** Produces async `BinanceClient.refresh_catalog()`, `market_snapshot(symbol)`, `RssSource.fetch()`, `EventRepository.save()`, and `TelegramNotifier.send(assessment)`.

- [ ] Write mocked Binance tests and a High formatting test that asserts KST plus `자동매매 지시가 아닌` are present.
- [ ] Run `pytest tests/test_binance.py tests/test_notifier.py -v`; implement 10-second HTTP timeouts, Binance Futures public calls, RSS parsing, SQLite audit tables, and Telegram `sendMessage`.
- [ ] An unavailable provider must contribute no confirmation, never positive confirmation. Rerun `pytest -v && ruff check .` and commit `feat: add market feeds persistence and telegram alerts`.

### Task 4: Ingestion route, scheduler, containerization, and delivery

**Files:** Modify `src/event_scanner/main.py`; create `src/event_scanner/service.py`, `tests/test_ingest_api.py`, `Dockerfile`, and `docker-compose.yml`; update `README.md`.

**Interfaces:** `POST /v1/events` accepts `RawEvent`, persists `EventAssessment`, returns the assessment with status 201 for High or 202 otherwise.

- [ ] Write a failing ingestion test:

```python
def test_ingest_returns_assessment(client):
    response = client.post('/v1/events', json=trusted_hack_payload())
    assert response.status_code in {201, 202}
    assert response.json()['level'] in {'high', 'medium', 'hold'}
```

- [ ] Run `pytest tests/test_ingest_api.py -v`; implement source-trust validation, URL/body-hash deduplication, scoring orchestration, immediate High notification, and scheduled configured RSS polling.
- [ ] Document local/Docker operation, secrets, webhooks for real X/on-chain providers, alert grades, and limitations. Run `pytest -v && ruff check . && docker compose config`.
- [ ] Commit `feat: deliver event scanner mvp`, then run `git push -u origin main`.

## Self-review

- Covers all PRD MVP components: sources, structural classification, Binance mapping, market/on-chain confirmation, High/Medium policy, audit logs, KST, reliability, and no-order boundary.
- Uses a single consistent contract: `RawEvent -> EventAssessment`.
- No unbounded implementation work is included; real X/on-chain credentials remain configuration at deployment.
