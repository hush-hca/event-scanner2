import httpx

from ..domain import MarketSnapshot


class BinanceClient:
    base_url = "https://fapi.binance.com"

    async def refresh_catalog(self) -> dict[str, str]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.base_url}/fapi/v1/exchangeInfo")
            response.raise_for_status()
        return {item["baseAsset"].upper(): item["symbol"] for item in response.json()["symbols"] if item["contractType"] == "PERPETUAL" and item["quoteAsset"] == "USDT" and item["status"] == "TRADING"}

    async def market_snapshot(self, symbol: str) -> MarketSnapshot | None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/fapi/v1/ticker/24hr", params={"symbol": symbol})
                response.raise_for_status()
            data = response.json()
            return MarketSnapshot(price_change_pct=float(data["priceChangePercent"]), quote_volume=float(data["quoteVolume"]), liquid=float(data["quoteVolume"]) >= 1_000_000)
        except (httpx.HTTPError, KeyError, ValueError):
            return None
