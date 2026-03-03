from datetime import datetime, timedelta, timezone
from pathlib import Path

from openpyxl import Workbook
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .account_package import AccountMetadata

EXPORT_COLUMNS = [
    'username',
    'user_id',
    'source_chat',
    'mutual_reference_count',
    'reference_density',
    'monitor_group_count',
    'first_seen',
    'last_seen_category',
    'mutual_groups_list',
]


class BotDataService:
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def stats(self) -> dict:
        async with self.session_factory() as session:
            return {
                'users': await _scalar(session, 'SELECT COUNT(*) FROM users'),
                'groups_total': await _scalar(session, 'SELECT COUNT(*) FROM groups'),
                'groups_reference': await _scalar(
                    session, "SELECT COUNT(*) FROM groups WHERE type = 'reference'"
                ),
                'groups_monitor': await _scalar(
                    session, "SELECT COUNT(*) FROM groups WHERE type = 'monitor'"
                ),
                'accounts': await _scalar(session, 'SELECT COUNT(*) FROM accounts'),
                'tasks_queued': await _scalar(
                    session, "SELECT COUNT(*) FROM mutual_tasks WHERE status = 'queued'"
                ),
            }

    async def account_statuses(self) -> list[dict]:
        query = text(
            'SELECT id, status, dynamic_limit, trust_score, sleep_until, cluster_id FROM accounts ORDER BY id'
        )
        async with self.session_factory() as session:
            rows = (await session.execute(query)).mappings().all()
        return [dict(r) for r in rows]

    async def groups(self) -> list[dict]:
        query = text('SELECT group_id, title, type, status, cluster_id FROM groups ORDER BY id DESC LIMIT 50')
        async with self.session_factory() as session:
            rows = (await session.execute(query)).mappings().all()
        return [dict(r) for r in rows]


    async def set_account_limit(self, account_id: int, new_limit: int, min_limit: int = 40, max_limit: int = 150) -> None:
        if new_limit < min_limit or new_limit > max_limit:
            raise ValueError(f'limit must be in range {min_limit}-{max_limit}')
        query = text(
            "UPDATE accounts SET dynamic_limit = :limit, status = 'ACTIVE' WHERE id = :account_id"
        )
        async with self.session_factory() as session:
            await session.execute(query, {'limit': new_limit, 'account_id': account_id})
            await session.commit()

    async def set_account_sleep(self, account_id: int, minutes: int) -> None:
        if minutes <= 0:
            raise ValueError('minutes must be positive')
        sleep_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        query = text(
            "UPDATE accounts SET status = 'SLEEP', sleep_until = :sleep_until WHERE id = :account_id"
        )
        async with self.session_factory() as session:
            await session.execute(query, {'sleep_until': sleep_until, 'account_id': account_id})
            await session.commit()


    async def set_account_proxy(self, account_id: int, proxy_url: str) -> None:
        query = text(
            "UPDATE accounts SET proxy = :proxy WHERE id = :account_id"
        )
        async with self.session_factory() as session:
            await session.execute(query, {'proxy': proxy_url, 'account_id': account_id})
            await session.commit()

    async def upsert_group(self, group_id: int, title: str | None, group_type: str, cluster_id: int | None) -> None:
        query = text(
            """
            INSERT INTO groups (group_id, title, type, status, cluster_id, last_checked, last_scraped)
            VALUES (:group_id, :title, :type, 'OPEN', :cluster_id, NULL, NULL)
            ON CONFLICT (group_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                type = EXCLUDED.type,
                cluster_id = EXCLUDED.cluster_id
            """
        )
        async with self.session_factory() as session:
            await session.execute(
                query,
                {
                    'group_id': int(group_id),
                    'title': title,
                    'type': group_type,
                    'cluster_id': cluster_id,
                },
            )
            await session.commit()

    async def register_account_package(self, session_path: str, metadata: dict) -> None:
        payload = AccountMetadata.from_dict(metadata)
        query = text(
            """
            INSERT INTO accounts (session_path, api_id, api_hash, proxy, status, dynamic_limit, trust_score, sleep_until, cluster_id)
            VALUES (:session_path, :api_id, :api_hash, :proxy, 'ACTIVE', 80, 0, NULL, :cluster_id)
            """
        )
        async with self.session_factory() as session:
            await session.execute(
                query,
                {
                    'session_path': session_path,
                    'api_id': payload.api_id,
                    'api_hash': payload.api_hash,
                    'proxy': payload.proxy_as_url(),
                    'cluster_id': payload.cluster_id,
                },
            )
            await session.commit()


    async def log_action(self, actor_user_id: int, action: str, details_json: str = '{}') -> None:
        query = text(
            "INSERT INTO audit_logs (actor_user_id, action, details) VALUES (:actor_user_id, :action, CAST(:details AS JSONB))"
        )
        async with self.session_factory() as session:
            await session.execute(query, {'actor_user_id': actor_user_id, 'action': action, 'details': details_json})
            await session.commit()

    async def mark_backup_run(self, status: str, note: str | None = None) -> None:
        query = text(
            "INSERT INTO backup_runs (status, note) VALUES (:status, :note)"
        )
        async with self.session_factory() as session:
            await session.execute(query, {'status': status, 'note': note})
            await session.commit()

    async def export_weekly(self, output_dir: Path) -> Path:
        return await self._export_by_days(output_dir, 7)

    async def export_by_days(self, output_dir: Path, days: int) -> Path:
        return await self._export_by_days(output_dir, days)


    async def export_hot(self, output_dir: Path, days: int = 30) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        since = datetime.now(timezone.utc) - timedelta(days=days)

        query = text(
            """
            WITH ref AS (
                SELECT COUNT(*)::float AS total_reference
                FROM groups
                WHERE type = 'reference'
            )
            SELECT
                u.username,
                u.user_id,
                u.source_chat,
                u.mutual_reference_count,
                CASE
                    WHEN ref.total_reference = 0 THEN 0
                    ELSE ROUND(u.mutual_reference_count / ref.total_reference, 4)
                END AS reference_density,
                u.monitor_group_count,
                u.first_seen,
                u.last_seen_category,
                u.mutual_groups_json::text AS mutual_groups_list
            FROM users u
            CROSS JOIN ref
            WHERE u.mutual_reference_count >= 2
              AND (u.first_seen >= :since OR (u.last_mutual_check IS NOT NULL AND u.last_mutual_check >= :since))
            ORDER BY u.mutual_reference_count DESC, u.monitor_group_count DESC
            """
        )

        async with self.session_factory() as session:
            rows = (await session.execute(query, {'since': since})).mappings().all()

        wb = Workbook()
        ws = wb.active
        ws.title = f'export_hot_{days}d'
        ws.append(EXPORT_COLUMNS)
        for row in rows:
            ws.append([row.get(col) for col in EXPORT_COLUMNS])

        path = output_dir / f'lead_export_hot_{days}d_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.xlsx'
        wb.save(path)
        return path

    async def _export_by_days(self, output_dir: Path, days: int) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        since = datetime.now(timezone.utc) - timedelta(days=days)

        query = text(
            """
            WITH ref AS (
                SELECT COUNT(*)::float AS total_reference
                FROM groups
                WHERE type = 'reference'
            )
            SELECT
                u.username,
                u.user_id,
                u.source_chat,
                u.mutual_reference_count,
                CASE
                    WHEN ref.total_reference = 0 THEN 0
                    ELSE ROUND(u.mutual_reference_count / ref.total_reference, 4)
                END AS reference_density,
                u.monitor_group_count,
                u.first_seen,
                u.last_seen_category,
                u.mutual_groups_json::text AS mutual_groups_list
            FROM users u
            CROSS JOIN ref
            WHERE
                (
                    u.first_seen >= :since
                    OR (u.last_mutual_check IS NOT NULL AND u.last_mutual_check >= :since AND u.mutual_reference_count > 0)
                )
                AND NOT (u.mutual_reference_count = 0 AND COALESCE(u.last_seen_category, '') = 'long time ago')
            ORDER BY u.mutual_reference_count DESC, u.monitor_group_count DESC
            """
        )

        async with self.session_factory() as session:
            rows = (await session.execute(query, {'since': since})).mappings().all()

        wb = Workbook()
        ws = wb.active
        ws.title = f'export_{days}d'
        ws.append(EXPORT_COLUMNS)
        for row in rows:
            ws.append([row.get(col) for col in EXPORT_COLUMNS])

        path = output_dir / f'lead_export_{days}d_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.xlsx'
        wb.save(path)
        return path


async def _scalar(session: AsyncSession, sql: str) -> int:
    return int((await session.execute(text(sql))).scalar() or 0)
