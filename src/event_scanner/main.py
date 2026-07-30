from datetime import datetime, timezone
from html import escape

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .config import Settings
from .domain import RawEvent
from .notifier import TelegramNotifier
from .repository import EventRepository
from .service import ScannerService
from .providers.fxtwitter import FxTwitterClient, FxTwitterError
from .providers.rss import RssClient, infer_token
from .cat_rank import score_contract
from .volume_fire import filter_volume_fire
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
    rss = RssClient(settings.rss_feeds or None) if settings.rss_feeds else RssClient()
    cat_cache: list = []
    volume_fire_cache: list = []
    class XUrlRequest(BaseModel): url: str; token: str

    @app.get("/health")
    def health(): return {"status": "ok"}

    @app.get("/legacy-dashboard", response_class=HTMLResponse, include_in_schema=False)
    def legacy_dashboard():
        rows = service.repository.recent(50)
        today = datetime.now(timezone.utc).date().isoformat()
        today_rows = [row for row in rows if row["detected_at"].startswith(today)]
        high = sum(row["level"] == "high" for row in today_rows)
        average = round(sum(row["score"] for row in today_rows) / len(today_rows), 1) if today_rows else 0
        table = "".join(f"<tr><td class='{escape(row['level'])}'>{escape(row['level'].upper())}</td><td>{escape(row['symbol'] or '-')}</td><td>{row['score']}</td><td>{escape(row['title'])}</td><td>{escape(', '.join(row['reasons']))}</td><td>{escape(row['detected_at'])}</td></tr>" for row in rows) or "<tr><td colspan='6'>아직 수집된 이벤트가 없습니다. <code>POST /v1/events</code> 또는 <code>POST /v1/x/poll?token=...</code>로 수집을 시작하세요.</td></tr>"
        return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Event Scanner</title><style>body{{margin:0;background:#0b1020;color:#e7eaf0;font:14px system-ui;padding:32px}}h1{{margin:0 0 6px}}p{{color:#9ca8bc}}.cards{{display:flex;gap:12px;margin:24px 0;flex-wrap:wrap}}.card{{background:#161d31;border:1px solid #26314d;border-radius:10px;padding:18px;min-width:150px}}.num{{font-size:28px;font-weight:700;margin-top:8px}}table{{width:100%;border-collapse:collapse;background:#161d31;border-radius:10px;overflow:hidden}}th,td{{padding:13px;text-align:left;border-bottom:1px solid #26314d}}th{{color:#9ca8bc}}.high{{color:#ff7070;font-weight:700}}.medium{{color:#ffb454;font-weight:700}}.hold{{color:#9ca8bc}}code{{color:#93c5fd}}</style></head><body><h1>Crypto Event-Driven Scanner</h1><p>실시간 구조적 리스크 신호 · 30초마다 자동 새로고침</p><div class='cards'><div class='card'>오늘 신호<div class='num'>{len(today_rows)}</div></div><div class='card'>High 신호<div class='num'>{high}</div></div><div class='card'>평균 점수<div class='num'>{average}</div></div></div><h2>최근 이벤트</h2><table><thead><tr><th>등급</th><th>심볼</th><th>점수</th><th>이벤트</th><th>근거</th><th>감지 시각 (UTC)</th></tr></thead><tbody>{table}</tbody></table><script>setTimeout(()=>location.reload(),30000)</script></body></html>"""

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
    async def dashboard(lang: str = "en"):
        ko = lang.lower() == "ko"
        copy = {
            "title": "크립토 이벤트 기반 트레이딩 스캐너" if ko else "Crypto Event-Driven Scanner",
            "subtitle": "출처가 연결된 구조적 리스크 이벤트를 실시간 트레이딩 맥락으로 제공합니다." if ko else "Live event-driven trading context from source-linked structural-risk events.",
            "notice": "투자 조언이나 주문 신호가 아닙니다. 데이터는 30초마다 갱신됩니다." if ko else "Decision support only — not investment advice or an execution signal. Updates every 30 seconds.",
            "feed": "실시간 이벤트 피드" if ko else "Live event feed",
            "monitoring": "실시간 소스 모니터링 중" if ko else "Monitoring live sources",
            "empty": "아직 조건을 충족하는 구조적 리스크 이벤트가 없습니다. 검증되고 지원되는 Binance 무기한 선물 계약에 매핑된 이벤트는 자동으로 표시됩니다." if ko else "No qualifying structural-risk events are available yet. New verified events will appear here automatically when they are detected and mapped to a supported Binance perpetual contract.",
            "coverage": "소스 범위: 신뢰 뉴스/RSS, 공식 프로젝트 공지, 시장 확증 데이터" if ko else "Source coverage: trusted news/RSS, official project communications, and market confirmation.",
            "source": "출처" if ko else "Source",
            "event_time": "이벤트 시각" if ko else "Event time",
            "evidence": "트레이딩 근거" if ko else "Trading evidence",
            "detected": "감지 시각" if ko else "Detected",
        }
        await poll_rss()
        rows = service.repository.recent(50)
        live_items = []
        if not rows:
            if not service.catalog:
                service.catalog = await service.binance.refresh_catalog()
            live_items = await rss.fetch()
            for item in live_items:
                token = infer_token(f"{item.title} {item.body}", service.catalog)
                if not token:
                    continue
                try:
                    await service.ingest(RawEvent(title=item.title, body=item.body, source_url=item.url, source_name=item.source_name, token=token, occurred_at=item.occurred_at, trusted=True))
                except ValueError:
                    continue
            rows = service.repository.recent(50)
        snapshots = {row['symbol']: await service.binance.market_snapshot(row['symbol']) for row in rows if row['symbol']}
        body = "".join(
            f"<article class='event {escape(row['level'])}'><header><b>{escape(row['level'].upper())}</b><span>{row['score']}/100</span><span>{escape(row['symbol'] or 'UNMAPPED')}</span></header><h3><a href='{escape(row['source_url'])}' target='_blank' rel='noreferrer'>{escape(row['title'])}</a></h3><p><b>{copy['source']}:</b> {escape(row['source_name'] or 'Unavailable')} · <b>{copy['event_time']}:</b> {escape(row['occurred_at'] or row['detected_at'])}</p><p><b>{copy['evidence']}:</b> {escape(', '.join(row['reasons']))}</p><p><b>Binance 24h:</b> {(f\"{snapshots[row['symbol']].price_change_pct:+.2f}% · ${snapshots[row['symbol']].quote_volume:,.0f} volume\" if snapshots.get(row['symbol']) else 'Unavailable')}</p><small>{copy['detected']}: {escape(row['detected_at'])} UTC</small></article>" for row in rows
        ) or "".join(f"<article class='event'><header><b>LIVE SOURCE</b></header><h3><a href='{escape(item.url)}' target='_blank' rel='noreferrer'>{escape(item.title)}</a></h3><p><b>{copy['source']}:</b> {escape(item.source_name)} · <b>{copy['event_time']}:</b> {escape(item.occurred_at.isoformat())}</p><p>{escape(item.body[:300])}</p></article>" for item in live_items) or f"<div class='event'><h3>{copy['monitoring']}</h3><p>{copy['empty']}</p><small>{copy['coverage']}</small></div>"
        return f"""<!doctype html><html lang={'ko' if ko else 'en'}><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{copy['title']}</title><style>body{{margin:0;background:#0b1020;color:#e7eaf0;font:15px system-ui;padding:28px;max-width:1200px}}p,small{{color:#aebbd0}}a{{color:#93c5fd}}.notice{{border-left:3px solid #ffb454;padding:12px;background:#161d31}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}}.event{{background:#161d31;border:1px solid #26314d;border-radius:10px;padding:16px}}header{{display:flex;gap:12px;align-items:center}}header span{{color:#aebbd0}}.high b{{color:#ff7070}}.medium b{{color:#ffb454}}.hold b{{color:#aebbd0}}h3{{margin:16px 0 8px}}.lang{{float:right}}.lang a{{padding:6px 9px;border:1px solid #26314d;text-decoration:none}}</style></head><body><nav class='lang'><a href='/?lang=en'>EN</a><a href='/?lang=ko'>한국어</a></nav><h1>{copy['title']}</h1><p>{copy['subtitle']}</p><div class='notice'>{copy['notice']}</div><h2>{copy['feed']}</h2><div class='grid'>{body}</div><script>setTimeout(()=>location.reload(),30000)</script></body></html>"""

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

    @app.get('/v1/rss/poll')
    @app.post('/v1/rss/poll')
    async def poll_rss():
        if not service.catalog:
            service.catalog = await service.binance.refresh_catalog()
        result = {"processed": 0, "held": 0, "duplicates": 0}
        for item in await rss.fetch():
            token = infer_token(f"{item.title} {item.body}", service.catalog)
            if not token:
                result["held"] += 1
                continue
            event = RawEvent(title=item.title, body=item.body, source_url=item.url, source_name=item.source_name, token=token, occurred_at=item.occurred_at, trusted=True)
            try:
                await service.ingest(event)
                result["processed"] += 1
            except ValueError:
                result["duplicates"] += 1
        return result

    async def scan_cat_rank():
        nonlocal cat_cache
        if cat_cache: return cat_cache
        catalog=await service.binance.refresh_catalog(); results=[]
        for symbol in list(catalog.values())[:60]:
            c4,cd,cw=await service.binance.klines(symbol,'4h'),await service.binance.klines(symbol,'1d'),await service.binance.klines(symbol,'1w')
            rank=score_contract(symbol,c4,cd,cw)
            if rank.score: results.append(rank)
        cat_cache=sorted(results,key=lambda r:r.score,reverse=True)[:20]
        return cat_cache

    @app.get('/v1/cat-rank')
    async def cat_rank_api(): return [r.__dict__ for r in await scan_cat_rank()]

    @app.get('/cat-rank', response_class=HTMLResponse, include_in_schema=False)
    async def cat_rank_page():
        rows=await scan_cat_rank()
        table=''.join(f"<tr><td>{i+1}</td><td>{r.symbol}</td><td>{r.score}</td><td>{r.volume_score}</td><td>{r.accumulation_score}</td><td>{r.support_score}</td><td>{r.breakout_score}</td><td>{', '.join(r.flags) or '-'}</td></tr>" for i,r in enumerate(rows)) or '<tr><td colspan=8>Binance data unavailable.</td></tr>'
        return f"<html><head><meta charset=utf-8><title>Cat Rank</title><style>body{{font:14px system-ui;background:#0b1020;color:#e7eaf0;padding:32px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:12px;border-bottom:1px solid #26314d;text-align:left}}a{{color:#93c5fd}}</style></head><body><a href='/'>Event Scanner</a><h1>Cat Rank</h1><p>Chart, volume, accumulation, and support observation ranking. Not a buy signal.</p><table><tr><th>#</th><th>Symbol</th><th>Rank</th><th>Volume</th><th>Accumulation</th><th>Support</th><th>Breakout</th><th>Risk</th></tr>{table}</table></body></html>"

    async def scan_volume_fire():
        nonlocal volume_fire_cache
        if volume_fire_cache: return volume_fire_cache
        catalog=await service.binance.refresh_catalog(); rows=[]
        for symbol in list(catalog.values())[:100]:
            item=filter_volume_fire(symbol,await service.binance.klines(symbol,'4h',20))
            if item: rows.append(item)
        volume_fire_cache=sorted(rows,key=lambda r:r.multiple,reverse=True)
        return volume_fire_cache

    @app.get('/v1/volume-fire')
    async def volume_fire_api(): return [r.__dict__ for r in await scan_volume_fire()]

    @app.get('/volume-fire', response_class=HTMLResponse, include_in_schema=False)
    async def volume_fire_page():
        rows=await scan_volume_fire()
        table=''.join(f'<tr><td>{r.symbol}</td><td>{r.current_volume:,.0f}</td><td>{r.average_volume:,.0f}</td><td>{r.multiple:.2f}x</td></tr>' for r in rows) or '<tr><td colspan=4>No contracts meet the 2.0x filter.</td></tr>'
        return f"<html><head><meta charset=utf-8><title>Volume Fire</title><style>body{{font:14px system-ui;background:#0b1020;color:#e7eaf0;padding:32px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:12px;border-bottom:1px solid #26314d;text-align:left}}a{{color:#93c5fd}}</style></head><body><a href='/cat-rank'>Cat Rank</a><h1>Volume Fire</h1><p>Current 4h volume is at least 2.0x the prior 19-candle average. Observation only.</p><table><tr><th>Symbol</th><th>Current 4h</th><th>Prior 19 avg</th><th>Multiple</th></tr>{table}</table></body></html>"

    return app


app = create_app()
