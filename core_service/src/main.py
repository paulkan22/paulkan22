import asyncio

from redis.asyncio import Redis

from .balancer import DynamicLimitPolicy
from .config import Settings
from .db import build_session_factory
from .monitor_ingestion import MockMonitorSource, run_monitor_ingestion_loop
from .runtime_state import RuntimeState
from .telethon_mutual import TelethonMutualEngine
from .worker import MutualEngine, inspect_reference_capacity, run_worker


def build_mutual_engine(mode: str):
    if mode == 'live':
        return TelethonMutualEngine()
    return MutualEngine()


async def run() -> None:
    settings = Settings()
    session_factory = build_session_factory(settings)
    policy = DynamicLimitPolicy(
        min_limit=settings.dynamic_limit_min,
        max_limit=settings.dynamic_limit_max,
        jitter_min_seconds=settings.mutual_jitter_min_seconds,
        jitter_max_seconds=settings.mutual_jitter_max_seconds,
        cooldown_min_minutes=settings.cooldown_min_minutes,
        cooldown_max_minutes=settings.cooldown_max_minutes,
    )

    reference_count = await inspect_reference_capacity(session_factory)
    print(f'core_service started, reference groups: {reference_count}, telethon_mode={settings.telethon_mode}')

    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    state = RuntimeState(redis_client)
    engine = build_mutual_engine(settings.telethon_mode)
    source = MockMonitorSource()

    try:
        await asyncio.gather(
            run_worker(session_factory, policy, engine, settings.worker_tick_seconds, state),
            run_monitor_ingestion_loop(
                session_factory,
                source,
                state,
                settings.monitor_scan_minutes_min,
                settings.monitor_scan_minutes_max,
            ),
        )
    finally:
        await redis_client.aclose()


if __name__ == '__main__':
    asyncio.run(run())
