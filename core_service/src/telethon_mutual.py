from dataclasses import dataclass


@dataclass
class TelethonAccountContext:
    api_id: int
    api_hash: str
    session_path: str
    proxy: str | None = None


class TelethonMutualEngine:
    """Live Telethon mutual checker.

    Imports Telethon lazily to keep unit tests dependency-light.
    """

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
        from telethon.tl.functions.messages import GetCommonChatsRequest

        proxy_cfg = None
        if proxy:
            # expected format socks5://user:pass@host:port or socks5://host:port
            proxy_cfg = self._parse_proxy(proxy)

        client = TelegramClient(session_path, api_id, api_hash, proxy=proxy_cfg)
        await client.connect()
        try:
            result = await client(GetCommonChatsRequest(user_id=user_id, max_id=0, limit=100))
            chats = getattr(result, 'chats', []) or []
            common_ids = {int(getattr(c, 'id', 0)) for c in chats}
            return len(common_ids.intersection(reference_group_ids))
        finally:
            await client.disconnect()

    def _parse_proxy(self, proxy_url: str):
        from urllib.parse import urlparse

        parsed = urlparse(proxy_url)
        if parsed.scheme != 'socks5':
            raise ValueError('Only socks5 proxy URL is supported')
        if not parsed.hostname or not parsed.port:
            raise ValueError('Invalid proxy URL')

        if parsed.username and parsed.password:
            return ('socks5', parsed.hostname, parsed.port, True, parsed.username, parsed.password)
        return ('socks5', parsed.hostname, parsed.port)
