from fastapi import FastAPI, HTTPException

from .config import Settings
from .domain import RawEvent
from .notifier import TelegramNotifier
from .repository import EventRepository
from .service import ScannerService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Crypto Event-Driven Scanner", version="0.1.0")
    service = ScannerService(EventRepository(settings.db_path), TelegramNotifier(settings))

    @app.get("/health")
    def health(): return {"status": "ok"}

    @app.get("/v1/assessments")
    def assessments(limit: int = 50): return service.repository.recent(min(max(limit, 1), 100))

    @app.post("/v1/events")
    async def ingest(event: RawEvent):
        try: assessment = await service.ingest(event)
        except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
        return assessment

    return app


app = create_app()
