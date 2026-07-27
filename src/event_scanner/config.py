import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    db_path: str = os.getenv("EVENT_SCANNER_DB_PATH", "event_scanner.db")
    x_watched_handles: tuple[str, ...] = tuple(x.strip().lower().lstrip("@") for x in os.getenv("X_WATCHED_HANDLES", "").split(",") if x.strip())
    fxtwitter_base_url: str = os.getenv("FXTWITTER_BASE_URL", "https://api.fxtwitter.com/2")
