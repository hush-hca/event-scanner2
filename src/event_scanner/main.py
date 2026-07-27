from fastapi import FastAPI, HTTPException

from .config import Settings
from .domain import RawEvent
from .notifier import TelegramNotifier
from .repository import EventRepository
from .service import ScannerService
from .providers.fxtwitter import FxTwitterClient, FxTwitterError
from pydantic import BaseModel


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Crypto Event-Driven Scanner", version="0.1.0")
    try:
        repository = EventRepository(settings.db_path)
    except Exception:
        # Serverless startup must remain available if an ephemeral volume is unavailable.
        repository = EventRepository(":memory:")
    service = ScannerService(repository, TelegramNotifier(settings))
    fx = FxTwitterClient(settings.fxtwitter_base_url)
    class XUrlRequest(BaseModel): url: str; token: str

    @app.get("/health")
    def health(): return {"status": "ok"}

    @app.get("/v1/assessments")
    def assessments(limit: int = 50): return service.repository.recent(min(max(limit, 1), 100))

    @app.post("/v1/events")
    async def ingest(event: RawEvent):
        try: assessment = await service.ingest(event)
        except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
        return assessment

    @app.post('/v1/x/ingest-url')
    async def ingest_x_url(request: XUrlRequest):
        try: post = await fx.get_status(request.url)
        except FxTwitterError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
        event = RawEvent(title=post.text[:500], body=post.text, source_url=post.url, source_name=f'@{post.handle}', token=request.token, occurred_at=post.created_at, trusted=post.handle in settings.x_watched_handles)
        try: return await service.ingest(event)
        except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post('/v1/x/poll')
    async def poll_x(token: str):
        result={'processed': 0, 'duplicates': 0, 'failed': []}
        for handle in settings.x_watched_handles:
            try:
                for post in await fx.list_statuses(handle):
                    event=RawEvent(title=post.text[:500], body=post.text, source_url=post.url, source_name=f'@{post.handle}', token=token, occurred_at=post.created_at, trusted=True)
                    try: await service.ingest(event); result['processed'] += 1
                    except ValueError: result['duplicates'] += 1
            except FxTwitterError: result['failed'].append(handle)
        return result

    return app


app = create_app()
