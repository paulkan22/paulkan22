import unittest

from core_service.src.proxy_utils import parse_socks5_proxy


class MonitorSourceUtilsTests(unittest.TestCase):
    def test_parse_proxy_ok(self):
        parsed = parse_socks5_proxy('socks5://u:p@127.0.0.1:1080')
        self.assertEqual(parsed[0], 'socks5')
        self.assertEqual(parsed[1], '127.0.0.1')
        self.assertEqual(parsed[2], 1080)

    def test_parse_proxy_invalid(self):
        self.assertIsNone(parse_socks5_proxy('http://127.0.0.1:8080'))
        self.assertIsNone(parse_socks5_proxy(None))


if __name__ == '__main__':
    unittest.main()
