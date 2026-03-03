import asyncio
from dataclasses import dataclass

from .proxy_utils import parse_socks5_proxy


@dataclass
class TelethonAccountContext:
    api_id: int
    api_hash: str
    session_path: str
    proxy: str | None = None


class TelethonMutualEngine:
    """Live Telethon mutual checker with safe retries/flood mapping.

    Imports Telethon lazily to keep unit tests dependency-light.
    """

    def __init__(self, max_retries: int = 3, retry_delay_seconds: int = 2):
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

    async def fetch_mutual_reference_count(
        self,
        user_id: int,
        cluster_id: int | None,
        session_path: str,
        proxy: str | None,
        api_id: int,
        api_hash: str,
        reference_group_ids: set[int],
    ) -> int:
        from telethon import TelegramClient  # lazy import
        from telethon.errors import FloodWaitError as TelethonFloodWaitError
        from telethon.tl.functions.messages import GetCommonChatsRequest

        proxy_cfg = self._parse_proxy(proxy) if proxy else None

        attempt = 0
        while True:
            attempt += 1
            client = TelegramClient(session_path, api_id, api_hash, proxy=proxy_cfg)
            await client.connect()
            try:
                result = await client(GetCommonChatsRequest(user_id=user_id, max_id=0, limit=100))
                chats = getattr(result, 'chats', []) or []
                common_ids = {int(getattr(c, 'id', 0)) for c in chats}
                return len(common_ids.intersection(reference_group_ids))
            except TelethonFloodWaitError as flood:
                # map to internal FloodWaitError from worker module
                from .worker import FloodWaitError

                raise FloodWaitError(wait_seconds=int(getattr(flood, 'seconds', 60)))
            except Exception:
                if attempt >= self.max_retries:
                    raise
                await asyncio.sleep(self.retry_delay_seconds)
            finally:
                await client.disconnect()

    def _parse_proxy(self, proxy_url: str):
        parsed = parse_socks5_proxy(proxy_url)
        if parsed is None:
            raise ValueError('Only socks5 proxy URL is supported')
        return parsed
