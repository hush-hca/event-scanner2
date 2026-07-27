import os
import importlib


def test_vercel_uses_writable_tmp_database(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    import event_scanner.config as config
    importlib.reload(config)
    assert config.Settings().db_path == "/tmp/event_scanner.db"
    monkeypatch.delenv("VERCEL", raising=False)
    importlib.reload(config)
