import json
import tempfile
import unittest
from pathlib import Path

from bot_service.src.upload_flow import UploadState, load_metadata_json, sanitize_filename


class UploadFlowTests(unittest.TestCase):
    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename('acc 01.session'), 'acc_01.session')
        self.assertEqual(sanitize_filename('..evil../a.json'), 'evil.._a.json')

    def test_upload_state_ready(self):
        state = UploadState()
        self.assertFalse(state.ready())
        state.session_path = Path('a.session')
        self.assertFalse(state.ready())
        state.metadata_path = Path('a.json')
        self.assertTrue(state.ready())

    def test_load_metadata_json(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'meta.json'
            p.write_text(json.dumps({'api_id': 1, 'proxy': {'scheme': 'socks5', 'host': '1.1.1.1', 'port': 1080}}), encoding='utf-8')
            data = load_metadata_json(p)
            self.assertIsInstance(data, dict)
            self.assertEqual(data['api_id'], 1)


if __name__ == '__main__':
    unittest.main()
