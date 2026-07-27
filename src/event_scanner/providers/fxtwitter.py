from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse
import httpx

class FxTwitterError(RuntimeError): pass
@dataclass(frozen=True)
class XPost:
    id: str; handle: str; text: str; url: str; created_at: datetime

class FxTwitterClient:
    def __init__(self, base_url: str): self.base_url = base_url.rstrip('/')
    async def get_status(self, url: str) -> XPost:
        parts=urlparse(url); chunks=parts.path.strip('/').split('/')
        if parts.hostname not in {'x.com','www.x.com','twitter.com','www.twitter.com'} or len(chunks)<3 or chunks[-2]!='status' or not chunks[-1].isdigit(): raise FxTwitterError('invalid X status URL')
        async with httpx.AsyncClient(timeout=10) as c:
            r=await c.get(f'{self.base_url}/status/{chunks[-1]}'); r.raise_for_status(); data=r.json()
        if data.get('code') != 200 or not data.get('status'): raise FxTwitterError('FxTwitter response failed')
        s=data['status']; return XPost(str(s['id']), s['author']['screen_name'].lower(), s['text'], s['url'], datetime.fromisoformat(s['created_at'].replace('Z','+00:00')))
    async def list_statuses(self, handle: str) -> list[XPost]:
        async with httpx.AsyncClient(timeout=10) as c:
            r=await c.get(f'{self.base_url}/profile/{handle}/statuses', params={'count': 20})
            if r.status_code == 204: return []
            r.raise_for_status(); data=r.json()
        if data.get('code') != 200: raise FxTwitterError('FxTwitter response failed')
        return [XPost(str(s['id']), s['author']['screen_name'].lower(), s['text'], s['url'], datetime.fromisoformat(s['created_at'].replace('Z','+00:00'))) for s in data.get('results', []) if s.get('type') == 'status']
