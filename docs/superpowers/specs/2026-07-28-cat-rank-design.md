# Cat Rank Design

## Goal

Rank every Binance USDT perpetual contract as a chart-and-volume observation priority using the trading heuristics attributed to Kang Cat: volume accumulation, accumulation movement, 4-hour/daily/weekly support, and breakout readiness.

## Scope

- Scan Binance USDT perpetual contracts only.
- Use Binance OHLCV and 24-hour market data only; no news, X, on-chain, or manually entered catalyst score.
- Display the top 20 ranked contracts in a Cat Rank tab and expose full results as JSON.
- The result is an observation priority, not a buy instruction or profitability claim.

## Score

| Factor | Maximum | Rule |
| --- | ---: | --- |
| Volume trend | 30 | Reward 4-hour volume above its 20-candle mean, with daily and weekly volume confirmation. |
| Accumulation movement | 25 | Reward range compression, higher lows, and elevated volume without a completed large breakout. |
| Support preservation | 25 | Reward closes above recent 4-hour, daily, and weekly support ranges; zero this factor after box-bottom failure. |
| Breakout readiness | 20 | Reward proximity to the range high and positive short-term momentum without overextension. |

## Risk Filters

- Exclude contracts below the minimum quote-volume threshold.
- Penalize sharp recent spikes and excessive wick/body volatility.
- Flag box-bottom or weekly-support failures as `support_break`.
- Flag abnormal short-term volatility as `hostile_movement`.

## Architecture

`CatRankScanner` obtains the active Binance USDT perpetual catalog and 4h/1d/1w kline windows, computes a typed `CatRankResult`, and caches the scan for 15 minutes. FastAPI serves `GET /v1/cat-rank` and a `/cat-rank` tab. On a provider failure, it returns the last successful cached result; if no successful result exists, it returns an explicit unavailable state.

## UI

The Cat Rank page shows scan timestamp, scanned/qualified counts, top-20 average score, the observation-only disclaimer, and a ranked table with factor scores and risk flags. Selecting a row shows factor explanations and a support-invalidated warning when present.

## Verification

- Unit-test each factor with deterministic candle fixtures.
- Test exclusion, risk flags, 15-minute cache reuse, stale-cache fallback, and an unavailable scan.
- Route-test the JSON API and HTML tab.
