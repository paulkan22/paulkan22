import asyncio
from dataclasses import dataclass
from random import randint

from sqlalchemy.ext.asyncio import async_sessionmaker

from .balancer import AccountRuntime, DynamicLimitPolicy
from .flood_control import classify_flood
from .repository import (
    acquire_next_task,
    get_reference_groups_count,
    list_reference_group_ids,
    mark_task_done,
    pick_available_account,
    requeue_task,
    sync_account_runtime,
    upsert_user_mutual,
)
from .runtime_state import RuntimeState


@dataclass
class FloodWaitError(Exception):
    wait_seconds: int


class MutualEngine:
    """Fallback mock mutual engine."""

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
        await asyncio.sleep(0)
        if user_id % 97 == 0:
            raise FloodWaitError(wait_seconds=randint(60, 500))
        return min(randint(0, 5), len(reference_group_ids))


async def run_worker(
    session_factory: async_sessionmaker,
    policy: DynamicLimitPolicy,
    engine,
    tick_seconds: int,
    state: RuntimeState,
) -> None:
    while True:
        if not await state.is_running():
            await asyncio.sleep(tick_seconds)
            continue

        async with session_factory() as session:
            task = await acquire_next_task(session)
            if task is None:
                await session.commit()
                await asyncio.sleep(tick_seconds)
                continue

            account = await pick_available_account(session, task.cluster_id)
            if account is None:
                await requeue_task(session, task)
                await session.commit()
                await asyncio.sleep(tick_seconds)
                continue

            reference_group_ids = await list_reference_group_ids(session, task.cluster_id)
            runtime = AccountRuntime(
                dynamic_limit=account.dynamic_limit,
                trust_score=account.trust_score,
            )
            try:
                mutual_count = await engine.fetch_mutual_reference_count(
                    task.user_id,
                    task.cluster_id,
                    account.session_path,
                    account.proxy,
                    int(account.api_id),
                    account.api_hash,
                    reference_group_ids,
                )
                await upsert_user_mutual(
                    session,
                    user_id=task.user_id,
                    mutual_reference_count=mutual_count,
                )
                await mark_task_done(session, task)
                runtime = policy.reward_stable_period(runtime)
            except FloodWaitError as flood:
                await requeue_task(session, task)
                decision = classify_flood(flood.wait_seconds)
                if decision.severity == 'small':
                    runtime = policy.on_small_flood(runtime)
                elif decision.severity == 'medium':
                    runtime = policy.on_long_flood(runtime, decision.cooldown_seconds)
                else:
                    runtime = policy.on_long_flood(runtime, decision.cooldown_seconds)
            except Exception:
                await requeue_task(session, task)
                runtime = policy.on_small_flood(runtime)

            await sync_account_runtime(
                session,
                account_id=account.id,
                dynamic_limit=runtime.dynamic_limit,
                trust_score=runtime.trust_score,
                status=runtime.status.value,
                sleep_until=runtime.sleep_until,
            )
            await session.commit()

        await asyncio.sleep(policy.next_delay())


async def inspect_reference_capacity(session_factory: async_sessionmaker) -> int:
    async with session_factory() as session:
        return await get_reference_groups_count(session)
