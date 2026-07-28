# Volume Fire Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show only Binance USDT perpetual contracts whose current 4-hour volume is at least 2x the preceding 19-candle average.

**Architecture:** A pure volume filter consumes 20 candles per symbol; FastAPI caches and presents descending multiples through JSON and HTML routes.

**Tech Stack:** Python 3.12, FastAPI, httpx, pytest.

## Global Constraints

- Include only contracts where `current_4h_volume / mean(previous_19_4h_volumes) >= 2.0`.
- Sort descending by the ratio and present no trading recommendation.

### Task 1: Filter and routes

**Files:** Create `src/event_scanner/volume_fire.py`; modify `main.py`; create `tests/test_volume_fire.py`.

**Interfaces:** Produces `filter_volume_fire(symbol, candles) -> VolumeFireResult`, `GET /v1/volume-fire`, and `GET /volume-fire`.

- [ ] Write tests for a 2.0x inclusion, 1.99x exclusion, and descending sort.
- [ ] Run `pytest tests/test_volume_fire.py -v`; implement the filter, cached scan, JSON endpoint, and HTML table.
- [ ] Run `pytest -q -p no:cacheprovider`; commit and push `feat: add volume fire filter`.
