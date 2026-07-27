# Event Scanner Dashboard Design

## Goal

Provide one browser-based operations dashboard for live signal review and historical signal-quality analysis without introducing a separate frontend deployment.

## Architecture

FastAPI serves `/dashboard` and `/analytics` HTML pages, shared CSS, and compact browser JavaScript. The UI reads new JSON aggregate endpoints backed by the existing SQLite assessment table. The current API stays compatible; additions are read-only.

## Pages

### `/dashboard`

- KPI cards: today’s total signals, High count, Medium count, and average score.
- Recent signal table: level, symbol, score, title, detected time, and evidence.
- Detail panel: source link, score reasons, and known market/on-chain evidence.
- Refreshes every 30 seconds; an empty state explains how to ingest an event.

### `/analytics`

- Filters for time window, signal level, and symbol.
- Aggregate cards for count, average score, and High rate.
- A signal-count-by-day chart rendered with native SVG, requiring no client dependency.
- A level-by-symbol table. Historical 5m/15m/1h/4h returns are shown as unavailable until the scanner records them; the UI must not invent performance data.

## API Additions

- `GET /v1/dashboard/summary` returns today counts, average score, and recent assessments.
- `GET /v1/analytics?days=30&level=high&symbol=BTCUSDT` returns filtered aggregates and daily counts.
- Invalid level, non-positive day count, or an unknown symbol returns HTTP 422.

## Data and Error Handling

- Existing assessment fields remain the source of truth.
- Use UTC in stored/API timestamps and render them in KST in the browser.
- Escape all values inserted into HTML to prevent event content from becoming executable markup.
- A database query failure returns JSON HTTP 500 for API routes and a readable error state for HTML pages.

## Verification

- Unit tests cover summary and analytics aggregation, including empty data and filters.
- Route tests verify `/dashboard`, `/analytics`, and the JSON endpoints.
- Browser JavaScript uses only same-origin fetch calls and a 30-second interval.

## Scope Boundary

The dashboard is an information and review surface. It does not place orders, offer account management, or claim profitability.
