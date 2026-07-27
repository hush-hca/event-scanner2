import json
import sqlite3

from .domain import EventAssessment, RawEvent


class EventRepository:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS assessments (event_id TEXT PRIMARY KEY, source_url TEXT UNIQUE, title TEXT, token TEXT, level TEXT, score INTEGER, symbol TEXT, reasons TEXT, created_at TEXT)")

    def is_duplicate(self, source_url: str) -> bool:
        return self.conn.execute("SELECT 1 FROM assessments WHERE source_url = ?", (source_url,)).fetchone() is not None

    def save(self, event: RawEvent, assessment: EventAssessment) -> None:
        self.conn.execute("INSERT OR IGNORE INTO assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (assessment.event_id, str(event.source_url), event.title, event.token.upper(), assessment.level.value, assessment.score, assessment.symbol, json.dumps(assessment.reasons), assessment.detected_at.isoformat()))
        self.conn.commit()

    def recent(self, limit: int = 50) -> list[dict]:
        rows = self.conn.execute("SELECT event_id, title, token, level, score, symbol, reasons, created_at FROM assessments ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"event_id": r[0], "title": r[1], "token": r[2], "level": r[3], "score": r[4], "symbol": r[5], "reasons": json.loads(r[6]), "detected_at": r[7]} for r in rows]
