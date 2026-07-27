from zoneinfo import ZoneInfo

import httpx

from .config import Settings
from .domain import EventAssessment, RawEvent


class TelegramNotifier:
    def __init__(self, settings: Settings): self.settings = settings

    @staticmethod
    def format(event: RawEvent, assessment: EventAssessment) -> str:
        kst = assessment.detected_at.astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S KST")
        return f"[{assessment.level.value.upper()}] 구조적 리스크 감지\n자산: {assessment.symbol}\n이벤트: {event.title}\n감지: {kst}\n신뢰도: {assessment.score}/100\n근거: {', '.join(assessment.reasons)}\n원문: {event.source_url}\n주의: 자동매매 지시가 아닌, 검증된 이벤트 알림입니다."

    async def send(self, event: RawEvent, assessment: EventAssessment) -> bool:
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id: return False
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage", json={"chat_id": self.settings.telegram_chat_id, "text": self.format(event, assessment), "disable_web_page_preview": True})
            response.raise_for_status()
        return True
