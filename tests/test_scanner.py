from datetime import datetime, timezone

from fastapi.testclient import TestClient

from event_scanner.config import Settings
from event_scanner.domain import MarketSnapshot, RawEvent, SignalLevel
from event_scanner.main import create_app
from event_scanner.scoring import assess_event


def event(token="ABC"):
    return RawEvent(title="ABC protocol hack confirmed", body="exploit caused losses", source_url="https://x.com/abc/status/1", source_name="ABC", token=token, trusted=True, occurred_at=datetime.now(timezone.utc))


def test_health_is_ok():
    client = TestClient(create_app(Settings(db_path=":memory:")))
    assert client.get("/health").json() == {"status": "ok"}


def test_root_serves_dashboard():
    client = TestClient(create_app(Settings(db_path=":memory:")))
    response = client.get("/")
    assert response.status_code == 200
    assert "Crypto Event-Driven Scanner" in response.text


def test_trusted_hack_with_market_confirmation_is_high():
    result = assess_event(event(), {"ABC": "ABCUSDT"}, MarketSnapshot(price_change_pct=-4, quote_volume=2_000_000), False)
    assert result.level is SignalLevel.HIGH


def test_unmapped_token_is_hold():
    assert assess_event(event("MISSING"), {}, MarketSnapshot(price_change_pct=-4), False).level is SignalLevel.HOLD
