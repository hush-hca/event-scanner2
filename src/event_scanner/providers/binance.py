import httpx

from ..domain import MarketSnapshot
from ..cat_rank import Candle


class BinanceClient:
    base_url = "https://fapi.binance.com"

    async def refresh_catalog(self) -> dict[str, str]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/fapi/v1/exchangeInfo")
                response.raise_for_status()
            return {item["baseAsset"].upper(): item["symbol"] for item in response.json()["symbols"] if item["contractType"] == "PERPETUAL" and item["quoteAsset"] == "USDT" and item["status"] == "TRADING"}
        except (httpx.HTTPError, KeyError, ValueError):
            return {}

    async def market_snapshot(self, symbol: str) -> MarketSnapshot | None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/fapi/v1/ticker/24hr", params={"symbol": symbol})
                response.raise_for_status()
            data = response.json()
            return MarketSnapshot(price_change_pct=float(data["priceChangePercent"]), quote_volume=float(data["quoteVolume"]), liquid=float(data["quoteVolume"]) >= 1_000_000)
        except (httpx.HTTPError, KeyError, ValueError):
            return None

    async def klines(self, symbol: str, interval: str, limit: int = 30) -> list[Candle]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response=await client.get(f"{self.base_url}/fapi/v1/klines",params={"symbol":symbol,"interval":interval,"limit":limit}); response.raise_for_status()
            return [Candle(float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])) for x in response.json()]
        except (httpx.HTTPError, ValueError, IndexError): return []
