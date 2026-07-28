# Volume Fire Design

## Goal

Add a Volume Fire page that shows only Binance USDT perpetual contracts whose current 4-hour candle volume is at least 2.0x the average volume of the immediately preceding 19 completed 4-hour candles.

## Rules

- Fetch 20 4-hour candles per contract.
- Treat the newest candle as the current candle and average candles 1 through 19 before it.
- Include a contract only when `current_volume / prior_19_average >= 2.0`.
- Sort descending by volume multiple.
- Show symbol, current 4-hour volume, prior-19 average, multiple, and Cat Rank score when available.
- Show an explicit empty state when no contracts pass the filter.
- This is a volume anomaly filter, not a trading recommendation.

## API and UI

- `GET /v1/volume-fire` returns all passing contracts.
- `GET /volume-fire` serves the ranked HTML page.
- Both reuse the 4-hour candle fetcher and cache results for 15 minutes.

## Verification

- Include a 2.0x boundary test, below-threshold exclusion, sorting test, and empty-result route test.
