import asyncio

from redis.asyncio import Redis

from .backup_runner import run_backup_loop
from .balancer import DynamicLimitPolicy
from .config import Settings
from .db import build_session_factory
from .monitor_ingestion import MockMonitorSource, TelethonMonitorSource, run_monitor_ingestion_loop
from .runtime_state import RuntimeState
from .telethon_mutual import TelethonMutualEngine
from .worker import MutualEngine, inspect_reference_capacity, run_worker


def build_mutual_engine(mode: str):
    if mode == 'live':
        return TelethonMutualEngine()
    return MutualEngine()


def build_monitor_source(mode: str, session_factory):
    if mode == 'live':
        return TelethonMonitorSource(session_factory)
    return MockMonitorSource()


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
    print(
        'core_service started, '
        f'reference groups: {reference_count}, '
        f'telethon_mode={settings.telethon_mode}, '
        f'monitor_source_mode={settings.monitor_source_mode}'
    )

    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    state = RuntimeState(redis_client)
    engine = build_mutual_engine(settings.telethon_mode)
    source = build_monitor_source(settings.monitor_source_mode, session_factory)

    tasks = [
        run_worker(session_factory, policy, engine, settings.worker_tick_seconds, state),
        run_monitor_ingestion_loop(
            session_factory,
            source,
            state,
            settings.monitor_scan_minutes_min,
            settings.monitor_scan_minutes_max,
        ),
    ]
    if settings.backup_enabled:
        tasks.append(
            run_backup_loop(
                session_factory,
                settings.database_url,
                every_hours=settings.backup_every_hours,
                output_dir=settings.backup_output_dir,
            )
        )

    try:
        await asyncio.gather(*tasks)
    finally:
        await redis_client.aclose()


if __name__ == '__main__':
    asyncio.run(run())
