import tempfile
import time
import unittest
from pathlib import Path

from core_service.src.backup_utils import prune_old_backups


class BackupRunnerTests(unittest.TestCase):
    def test_prune_old_backups(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            oldf = d / 'pg_backup_old.sql'
            newf = d / 'pg_backup_new.sql'
            oldf.write_text('old', encoding='utf-8')
            newf.write_text('new', encoding='utf-8')

            old_ts = time.time() - 20 * 86400
            new_ts = time.time()
            oldf.touch()
            newf.touch()
            oldf.chmod(0o644)
            newf.chmod(0o644)
            # set mtimes
            import os

            os.utime(oldf, (old_ts, old_ts))
            os.utime(newf, (new_ts, new_ts))

            removed = prune_old_backups(d, retention_days=14)
            self.assertEqual(removed, 1)
            self.assertFalse(oldf.exists())
            self.assertTrue(newf.exists())


if __name__ == '__main__':
    unittest.main()
