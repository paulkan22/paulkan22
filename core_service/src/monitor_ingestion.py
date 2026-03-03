import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from random import randint

from sqlalchemy.ext.asyncio import async_sessionmaker

from .monitor_analysis import MessageSample, choose_monitor_parse_mode
from .repository import enqueue_mutual_task, list_monitor_groups, pick_available_account, touch_group_scraped
from .runtime_state import RuntimeState
from .proxy_utils import parse_socks5_proxy


@dataclass
class MonitorCandidate:
    user_id: int
    priority: int = 0


class MonitorSource:
    async def collect(self, group_id: int, parse_mode: str, cluster_id: int | None) -> list[MonitorCandidate]:
        raise NotImplementedError


class MockMonitorSource(MonitorSource):
    async def collect(self, group_id: int, parse_mode: str, cluster_id: int | None) -> list[MonitorCandidate]:
        await asyncio.sleep(0)
        base = abs(group_id) % 100000
        return [
            MonitorCandidate(user_id=base + i, priority=1 if parse_mode == 'messages_full_history' else 0)
            for i in range(1, 6)
        ]


class TelethonMonitorSource(MonitorSource):
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def collect(self, group_id: int, parse_mode: str, cluster_id: int | None) -> list[MonitorCandidate]:
        from telethon import TelegramClient

        async with self.session_factory() as session:
            account = await pick_available_account(session, cluster_id)
            await session.commit()
        if account is None:
            return []

        client = TelegramClient(account.session_path, int(account.api_id), account.api_hash, proxy=parse_socks5_proxy(account.proxy))
        await client.connect()
        try:
            entity = await client.get_entity(group_id)
            users: list[int] = []
            if parse_mode == 'members_list':
                async for participant in client.iter_participants(entity, limit=500):
                    if getattr(participant, 'id', None):
                        users.append(int(participant.id))
            else:
                limit = 1000 if parse_mode == 'messages_full_history' else 200
                async for message in client.iter_messages(entity, limit=limit):
                    sender_id = getattr(message, 'sender_id', None)
                    if sender_id:
                        users.append(int(sender_id))
            uniq = list(dict.fromkeys(users))
            priority = 1 if parse_mode == 'messages_full_history' else 0
            return [MonitorCandidate(user_id=u, priority=priority) for u in uniq[:500]]
        finally:
            await client.disconnect()


def _synthetic_messages() -> list[MessageSample]:
    start = datetime.now(timezone.utc) - timedelta(minutes=45)
    return [MessageSample(user_id=(idx % 18) + 1, sent_at=start + timedelta(minutes=idx)) for idx in range(36)]


async def run_monitor_ingestion_once(session_factory: async_sessionmaker, source: MonitorSource) -> int:
    queued = 0
    async with session_factory() as session:
        groups = await list_monitor_groups(session)
        for group in groups:
            decision = choose_monitor_parse_mode(
                members_open=(group.status or '').upper() == 'OPEN',
                messages=_synthetic_messages(),
            )
            candidates = await source.collect(group.group_id, decision.parse_mode, group.cluster_id)
            for candidate in candidates:
                await enqueue_mutual_task(session, candidate.user_id, group.cluster_id, candidate.priority)
                queued += 1
            await touch_group_scraped(session, group.group_id)
        await session.commit()
    return queued


async def run_monitor_ingestion_loop(
    session_factory: async_sessionmaker,
    source: MonitorSource,
    state: RuntimeState,
    scan_min_minutes: int,
    scan_max_minutes: int,
) -> None:
    while True:
        if await state.is_running():
            await run_monitor_ingestion_once(session_factory, source)
        await asyncio.sleep(randint(scan_min_minutes * 60, scan_max_minutes * 60))
