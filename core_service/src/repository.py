from datetime import datetime, timezone

from sqlalchemy import Select, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Account, Group, MutualTask, User


async def get_reference_groups_count(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(Group).where(Group.type == 'reference')
    return int(await session.scalar(stmt) or 0)


async def list_reference_group_ids(session: AsyncSession, cluster_id: int | None = None) -> set[int]:
    stmt = select(Group.group_id).where(Group.type == 'reference')
    if cluster_id is not None:
        stmt = stmt.where(Group.cluster_id == cluster_id)
    rows = list((await session.scalars(stmt)).all())
    return {int(v) for v in rows}


async def list_monitor_groups(session: AsyncSession) -> list[Group]:
    return list((await session.scalars(select(Group).where(Group.type == 'monitor'))).all())


async def enqueue_mutual_task(session: AsyncSession, user_id: int, cluster_id: int | None, priority: int = 0) -> None:
    existing = await session.scalar(
        select(MutualTask)
        .where(MutualTask.user_id == user_id)
        .where(MutualTask.status.in_(['queued', 'processing']))
        .limit(1)
    )
    if existing is not None:
        return
    session.add(
        MutualTask(
            user_id=user_id,
            priority=priority,
            attempts=0,
            status='queued',
            cluster_id=cluster_id,
        )
    )
    await session.flush()


async def touch_group_scraped(session: AsyncSession, group_id: int) -> None:
    stmt = (
        update(Group)
        .where(Group.group_id == group_id)
        .values(last_checked=datetime.now(timezone.utc), last_scraped=datetime.now(timezone.utc))
    )
    await session.execute(stmt)




async def list_accounts(session: AsyncSession) -> list[Account]:
    return list((await session.scalars(select(Account))).all())


async def pick_available_account(session: AsyncSession, cluster_id: int | None) -> Account | None:
    now = datetime.now(timezone.utc)
    stmt: Select[tuple[Account]] = (
        select(Account)
        .where(Account.status.in_(['ACTIVE', 'COOLDOWN']))
        .order_by(Account.trust_score.desc(), Account.dynamic_limit.desc(), Account.id.asc())
        .limit(1)
    )
    if cluster_id is not None:
        stmt = stmt.where(Account.cluster_id == cluster_id)

    rows = list((await session.scalars(stmt)).all())
    for account in rows:
        if account.status == 'COOLDOWN' and account.sleep_until and account.sleep_until > now:
            continue
        if account.status == 'COOLDOWN' and account.sleep_until and account.sleep_until <= now:
            account.status = 'ACTIVE'
            account.sleep_until = None
            await session.flush()
        return account
    return None


async def acquire_next_task(session: AsyncSession, cluster_id: int | None = None) -> MutualTask | None:
    stmt: Select[tuple[MutualTask]] = (
        select(MutualTask)
        .where(MutualTask.status == 'queued')
        .order_by(MutualTask.priority.desc(), MutualTask.id.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if cluster_id is not None:
        stmt = stmt.where(MutualTask.cluster_id == cluster_id)

    row = await session.scalar(stmt)
    if row is None:
        return None

    row.status = 'processing'
    row.attempts += 1
    await session.flush()
    return row


async def requeue_task(session: AsyncSession, task: MutualTask) -> None:
    task.status = 'queued'
    await session.flush()


async def mark_task_done(session: AsyncSession, task: MutualTask) -> None:
    task.status = 'done'
    await session.flush()


async def upsert_user_mutual(
    session: AsyncSession,
    *,
    user_id: int,
    mutual_reference_count: int,
    monitor_group_count: int = 1,
) -> None:
    user = await session.scalar(select(User).where(User.user_id == user_id).limit(1))
    now = datetime.now(timezone.utc)
    if user is None:
        user = User(
            user_id=user_id,
            username=None,
            first_seen=now,
            last_seen_category='recently',
            monitor_group_count=monitor_group_count,
            mutual_reference_count=mutual_reference_count,
            last_mutual_check=now,
            source_chat=None,
        )
        session.add(user)
    else:
        user.mutual_reference_count = max(user.mutual_reference_count, mutual_reference_count)
        user.monitor_group_count = max(user.monitor_group_count, monitor_group_count)
        user.last_mutual_check = now
    await session.flush()


async def sync_account_runtime(
    session: AsyncSession,
    account_id: int,
    dynamic_limit: int,
    trust_score: int,
    status: str,
    sleep_until,
) -> None:
    stmt = (
        update(Account)
        .where(Account.id == account_id)
        .values(
            dynamic_limit=dynamic_limit,
            trust_score=trust_score,
            status=status,
            sleep_until=sleep_until,
        )
    )
    await session.execute(stmt)




async def record_backup_run(session: AsyncSession, status: str, note: str | None = None) -> None:
    await session.execute(
        text('INSERT INTO backup_runs (status, note) VALUES (:status, :note)'),
        {'status': status, 'note': note},
    )


async def record_audit_log(session: AsyncSession, actor_user_id: int, action: str, details_json: str = '{}') -> None:
    await session.execute(
        text(
            'INSERT INTO audit_logs (actor_user_id, action, details) VALUES (:actor_user_id, :action, CAST(:details AS JSONB))'
        ),
        {'actor_user_id': actor_user_id, 'action': action, 'details': details_json},
    )
