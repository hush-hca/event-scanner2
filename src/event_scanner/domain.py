from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class SignalLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    HOLD = "hold"


class RawEvent(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    body: str = Field(default="", max_length=10_000)
    source_url: HttpUrl
    source_name: str = Field(min_length=2, max_length=100)
    token: str = Field(min_length=2, max_length=20)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trusted: bool = False
    onchain_confirmation: bool = False


class MarketSnapshot(BaseModel):
    price_change_pct: float = 0
    quote_volume: float = 0
    open_interest_change_pct: float = 0
    funding_rate: float = 0
    liquid: bool = True


class EventAssessment(BaseModel):
    event_id: str
    level: SignalLevel
    score: int
    symbol: str | None
    reasons: list[str]
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
