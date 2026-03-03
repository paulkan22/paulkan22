import unittest

from core_service.src.telethon_mutual import TelethonMutualEngine


class TelethonMutualTests(unittest.TestCase):
    def test_parse_proxy_with_auth(self):
        engine = TelethonMutualEngine()
        parsed = engine._parse_proxy('socks5://user:pass@127.0.0.1:1080')
        self.assertEqual(parsed[0], 'socks5')
        self.assertEqual(parsed[1], '127.0.0.1')
        self.assertEqual(parsed[2], 1080)

    def test_parse_proxy_invalid_scheme(self):
        engine = TelethonMutualEngine()
        with self.assertRaises(ValueError):
            engine._parse_proxy('http://127.0.0.1:8080')


if __name__ == '__main__':
    unittest.main()
