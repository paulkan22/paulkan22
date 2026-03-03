import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker

from .repository import record_backup_run


async def run_backup_once(session_factory: async_sessionmaker, database_url: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    outfile = output_dir / f'pg_backup_{ts}.sql'

    # Prefer pg_dump binary if available.
    cmd = f"pg_dump '{database_url}' > '{outfile}'"
    proc = await asyncio.create_subprocess_shell(cmd)
    code = await proc.wait()

    async with session_factory() as session:
        if code == 0:
            await record_backup_run(session, 'ok', str(outfile))
        else:
            await record_backup_run(session, 'failed', f'pg_dump exit={code}')
        await session.commit()


async def run_backup_loop(
    session_factory: async_sessionmaker,
    database_url: str,
    every_hours: int = 24,
    output_dir: str = 'data/backups',
) -> None:
    target = Path(output_dir)
    while True:
        await run_backup_once(session_factory, database_url, target)
        await asyncio.sleep(max(1, every_hours) * 3600)
