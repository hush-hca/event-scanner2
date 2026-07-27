from .domain import EventAssessment, RawEvent
from .notifier import TelegramNotifier
from .providers.binance import BinanceClient
from .repository import EventRepository
from .scoring import assess_event


class ScannerService:
    def __init__(self, repository: EventRepository, notifier: TelegramNotifier, binance: BinanceClient | None = None):
        self.repository, self.notifier, self.binance, self.catalog = repository, notifier, binance or BinanceClient(), {}

    async def ingest(self, event: RawEvent) -> EventAssessment:
        if self.repository.is_duplicate(str(event.source_url)):
            raise ValueError("duplicate event")
        if not self.catalog:
            self.catalog = await self.binance.refresh_catalog()
        symbol = self.catalog.get(event.token.upper())
        snapshot = await self.binance.market_snapshot(symbol) if symbol else None
        assessment = assess_event(event, self.catalog, snapshot, event.onchain_confirmation)
        self.repository.save(event, assessment)
        if assessment.level.value == "high": await self.notifier.send(event, assessment)
        return assessment
