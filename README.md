# Crypto Event-Driven Scanner

MVP API for detecting trusted structural-risk events, mapping them to Binance USDT perpetuals, validating market response, and sending High alerts to Telegram. It never places orders.

## Run

```powershell
Copy-Item .env.example .env
$env:PYTHONPATH='src'
python -m uvicorn event_scanner.main:app --reload
```

`X_WATCHED_HANDLES` is pre-populated with global exchange, stablecoin, infrastructure, DeFi, and security-notice accounts. Treat it as a starting allowlist: remove accounts outside your risk policy before production. A watched account only makes a post eligible as a trusted source; it does not bypass structural-risk, Binance, or on-chain verification.

Open `http://localhost:8000/docs`. Use `POST /v1/events` for X/project/news/on-chain webhook payloads. Set `trusted: true` only after validating the provider; set `onchain_confirmation: true` only from a verified on-chain adapter.

## Event payload

```json
{"title":"Protocol exploit confirmed","body":"Funds affected","source_url":"https://x.com/project/status/1","source_name":"Project","token":"ABC","trusted":true,"onchain_confirmation":false}
```

High needs a structural-risk keyword, a Binance USDT perpetual mapping, and a market or on-chain confirmation. Telegram credentials are optional; without them alerts remain persisted but are not sent.

## Docker

```bash
docker compose up --build
```

X and on-chain vendors differ by credentials and policy, so this MVP receives their normalized authenticated webhook events through `/v1/events`; add gateway authentication before public deployment.
