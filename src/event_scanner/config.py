import os
from dataclasses import dataclass


def _default_db_path() -> str:
    """Vercel's deployed filesystem is read-only; only /tmp is writable."""
    return "/tmp/event_scanner.db" if os.getenv("VERCEL") else "event_scanner.db"


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    db_path: str = os.getenv("EVENT_SCANNER_DB_PATH", _default_db_path())
    x_watched_handles: tuple[str, ...] = tuple(x.strip().lower().lstrip("@") for x in os.getenv("X_WATCHED_HANDLES", "").split(",") if x.strip())
    fxtwitter_base_url: str = os.getenv("FXTWITTER_BASE_URL", "https://api.fxtwitter.com/2")
    rss_feeds: tuple[str, ...] = tuple(url.strip() for url in os.getenv("RSS_FEEDS", "").split(",") if url.strip())
