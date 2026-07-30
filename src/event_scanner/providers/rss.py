from dataclasses import dataclass
from datetime import datetime, timezone
import re

import feedparser
import httpx


DEFAULT_RSS_FEEDS = (
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
)


@dataclass(frozen=True)
class RssItem:
    title: str
    body: str
    url: str
    source_name: str
    occurred_at: datetime


class RssClient:
    def __init__(self, feeds: tuple[str, ...] = DEFAULT_RSS_FEEDS):
        self.feeds = feeds

    async def fetch(self) -> list[RssItem]:
        result: list[RssItem] = []
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            for url in self.feeds:
                try:
                    response = await client.get(url, headers={"User-Agent": "EventScanner/1.0"})
                    response.raise_for_status()
                    parsed = feedparser.parse(response.text)
                    for item in parsed.entries[:30]:
                        link = item.get("link")
                        title = item.get("title", "").strip()
                        if not link or not title:
                            continue
                        published = item.get("published_parsed") or item.get("updated_parsed")
                        occurred = datetime(*published[:6], tzinfo=timezone.utc) if published else datetime.now(timezone.utc)
                        result.append(RssItem(title, re.sub("<[^>]+>", " ", item.get("summary", "")), link, parsed.feed.get("title", "RSS"), occurred))
                except (httpx.HTTPError, ValueError, TypeError):
                    continue
        return result


def infer_token(text: str, catalog: dict[str, str]) -> str | None:
    words = set(re.findall(r"\b[A-Za-z0-9]{2,12}\b", text.upper()))
    aliases = {"BITCOIN": "BTC", "ETHEREUM": "ETH", "SOLANA": "SOL", "DOGECOIN": "DOGE", "RIPPLE": "XRP", "AVALANCHE": "AVAX", "CHAINLINK": "LINK", "UNISWAP": "UNI", "AAVE": "AAVE"}
    words.update(aliases[word] for word in words.intersection(aliases))
    return next((token for token in catalog if token in words), None)
