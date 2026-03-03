import unittest

from bot_service.src.account_package import AccountMetadata
from bot_service.src.admin_commands import parse_set_limit_command, parse_sleep_command


class AccountPackageTests(unittest.TestCase):
    def test_valid_account_package(self):
        payload = AccountMetadata.from_dict(
            {
                'api_id': 123,
                'api_hash': '0123456789abcdef0123456789abcdef',
                'device_model': 'Phone',
                'system_version': 'Android 14',
                'app_version': '10.0',
                'lang_code': 'ru',
                'system_lang_code': 'ru-RU',
                'proxy': {'scheme': 'socks5', 'host': '127.0.0.1', 'port': 1080},
                'cluster_id': 2,
            }
        )
        self.assertEqual(payload.cluster_id, 2)
        self.assertEqual(payload.proxy_as_url(), 'socks5://127.0.0.1:1080')

    def test_invalid_proxy_scheme(self):
        with self.assertRaises(ValueError):
            AccountMetadata.from_dict(
                {
                    'api_id': 123,
                    'api_hash': '0123456789abcdef0123456789abcdef',
                    'device_model': 'Phone',
                    'system_version': 'Android 14',
                    'app_version': '10.0',
                    'lang_code': 'ru',
                    'system_lang_code': 'ru-RU',
                    'proxy': {'scheme': 'http', 'host': '127.0.0.1', 'port': 8080},
                    'cluster_id': 2,
                }
            )


class AdminCommandsTests(unittest.TestCase):
    def test_parse_set_limit(self):
        account_id, limit = parse_set_limit_command('/set_limit 4 120')
        self.assertEqual(account_id, 4)
        self.assertEqual(limit, 120)

    def test_parse_sleep(self):
        account_id, minutes = parse_sleep_command('/sleep_account 3 45')
        self.assertEqual(account_id, 3)
        self.assertEqual(minutes, 45)


if __name__ == '__main__':
    unittest.main()
