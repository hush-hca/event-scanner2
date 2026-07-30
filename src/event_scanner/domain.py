from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class SignalLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    HOLD = "hold"


class EventType(str, Enum):
    SECURITY_INCIDENT = "security_incident"
    EXCHANGE_POLICY = "exchange_policy"
    PROTOCOL_CHANGE = "protocol_ecosystem_change"
    KOL_STATEMENT = "kol_influencer_statement"
    ONCHAIN_ANOMALY = "onchain_anomaly"
    REGULATION = "regulation_legal"
    EXCHANGE_OUTAGE = "exchange_technical_outage"


class Direction(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    TWO_SIDED = "two_sided"


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
    event_type: EventType = EventType.SECURITY_INCIDENT
    direction: Direction = Direction.NEUTRAL
    volatility: int = Field(default=1, ge=1, le=4)
    confidence: int = Field(default=0, ge=0, le=100)
    correlation_id: str = ""
    summary: list[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
