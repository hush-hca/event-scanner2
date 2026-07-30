# EventRadar P0 Design

EventRadar P0 migrates the scanner to a read-only, observable event pipeline. Public RSS plus Binance remains the initial real integration; X and paid/on-chain providers are optional adapters enabled only by environment configuration.

Local services use Docker Compose with PostgreSQL and Redis. The FastAPI application is split by ingestion, normalization, classification, routing, notifications, and API boundaries. A future Next.js web client consumes the API/SSE stream; the existing HTML dashboard remains a temporary compatibility view.

Every normalized event carries a stable ID, source timestamps, text, ticker mapping, event type, direction, volatility, severity, confidence, correlation ID, and raw-payload reference. No trading or exchange-write capability is included.
