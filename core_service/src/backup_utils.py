from datetime import datetime, timezone
from pathlib import Path


def prune_old_backups(output_dir: Path, retention_days: int) -> int:
    if retention_days <= 0:
        return 0
    if not output_dir.exists():
        return 0

    threshold = datetime.now(timezone.utc).timestamp() - retention_days * 86400
    removed = 0
    for file in output_dir.glob('pg_backup_*.sql'):
        try:
            if file.stat().st_mtime < threshold:
                file.unlink(missing_ok=True)
                removed += 1
        except FileNotFoundError:
            continue
    return removed
