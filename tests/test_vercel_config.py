import os
import importlib
from event_scanner.repository import EventRepository


def test_vercel_uses_writable_tmp_database(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    import event_scanner.config as config
    importlib.reload(config)
    assert config.Settings().db_path == "/tmp/event_scanner.db"
    monkeypatch.delenv("VERCEL", raising=False)
    importlib.reload(config)


def test_repository_can_use_memory_fallback():
    repository = EventRepository(":memory:")
    assert repository.recent() == []
