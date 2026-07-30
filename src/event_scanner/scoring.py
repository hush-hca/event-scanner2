from uuid import uuid4

from .domain import Direction, EventAssessment, EventType, MarketSnapshot, RawEvent, SignalLevel

STRUCTURAL_TERMS = {
    "hack": 45, "exploit": 45, "breach": 45, "해킹": 45, "익스플로잇": 45,
    "withdrawal suspended": 40, "출금 중단": 40, "depeg": 40, "디페그": 40,
    "investigation": 35, "조사": 35, "lawsuit": 30, "파산": 40,
}


def assess_event(event: RawEvent, catalog: dict[str, str], snapshot: MarketSnapshot | None, onchain: bool | None = None) -> EventAssessment:
    text = f"{event.title} {event.body}".lower()
    symbol = catalog.get(event.token.upper())
    reasons: list[str] = []
    score = 0
    term_score = max((points for term, points in STRUCTURAL_TERMS.items() if term in text), default=0)
    if term_score:
        score += term_score
        reasons.append("structural-risk keyword")
    if event.trusted:
        score += 20
        reasons.append("trusted source")
    if symbol:
        score += 10
        reasons.append(f"mapped to {symbol}")
    else:
        return EventAssessment(event_id=str(uuid4()), level=SignalLevel.HOLD, score=score, symbol=None, reasons=reasons + ["no Binance USDT perpetual mapping"], direction=Direction.BEARISH if term_score else Direction.NEUTRAL, volatility=3 if term_score else 1, confidence=score, correlation_id=str(event.source_url), summary=["Event detected", "No supported perpetual mapping", "Dashboard-only review"])
    confirmed = False
    if snapshot and snapshot.liquid and snapshot.price_change_pct <= -2:
        score += 20
        confirmed = True
        reasons.append(f"price move {snapshot.price_change_pct:.2f}%")
    if snapshot and snapshot.liquid and snapshot.quote_volume >= 1_000_000:
        score += 10
        reasons.append("liquid market")
    if onchain or event.onchain_confirmation:
        score += 20
        confirmed = True
        reasons.append("on-chain confirmation")
    level = SignalLevel.HIGH if score >= 70 and confirmed else SignalLevel.MEDIUM if score >= 45 else SignalLevel.HOLD
    volatility = 4 if level is SignalLevel.HIGH else 3 if level is SignalLevel.MEDIUM else 1
    direction = Direction.BEARISH if term_score else Direction.NEUTRAL
    return EventAssessment(event_id=str(uuid4()), level=level, score=min(score, 100), symbol=symbol, reasons=reasons, event_type=EventType.SECURITY_INCIDENT if term_score else EventType.PROTOCOL_CHANGE, direction=direction, volatility=volatility, confidence=min(score, 100), correlation_id=str(event.source_url), summary=[event.title[:140], f"{symbol} mapped with {direction.value} bias", "Review source and market evidence before acting"])
