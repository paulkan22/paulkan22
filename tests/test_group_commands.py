import unittest

from bot_service.src.group_commands import (
    extract_chat_identifier,
    parse_add_group_command,
    parse_proxy_value,
)


class GroupCommandsTests(unittest.TestCase):
    def test_parse_add_group(self):
        group_type, group_ref, cluster = parse_add_group_command('/add_group reference https://t.me/mygroup 2')
        self.assertEqual(group_type, 'reference')
        self.assertEqual(group_ref, 'https://t.me/mygroup')
        self.assertEqual(cluster, 2)

    def test_extract_chat_identifier(self):
        self.assertEqual(extract_chat_identifier('https://t.me/mygroup'), '@mygroup')
        self.assertEqual(extract_chat_identifier('https://t.me/c/123456/7'), '-100123456')
        self.assertEqual(extract_chat_identifier('-100987654321'), '-100987654321')

    def test_extract_invite_link_not_supported(self):
        with self.assertRaises(ValueError):
            extract_chat_identifier('https://t.me/+abcdef')

    def test_parse_proxy_value(self):
        self.assertEqual(
            parse_proxy_value('1.2.3.4:1080:user:pass'),
            'socks5://user:pass@1.2.3.4:1080',
        )


if __name__ == '__main__':
    unittest.main()
