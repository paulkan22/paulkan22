import ast
import unittest
from pathlib import Path


HANDLERS_FILE = Path('bot_service/src/handlers.py')


class HandlersMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HANDLERS_FILE.read_text(encoding='utf-8')
        cls.module = ast.parse(cls.source)

    def _function(self, name: str) -> ast.FunctionDef:
        build_router = next(node for node in self.module.body if isinstance(node, ast.FunctionDef) and node.name == 'build_router')
        return next(node for node in build_router.body if isinstance(node, ast.AsyncFunctionDef) and node.name == name)

    def _reply_markup_name(self, function_name: str) -> str:
        func = self._function(function_name)
        edit_call = next(
            node.value.value
            for node in ast.walk(func)
            if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Await)
            and isinstance(node.value.value, ast.Call)
            and isinstance(node.value.value.func, ast.Attribute)
            and node.value.value.func.attr == 'edit_text'
        )
        kw = next(kw for kw in edit_call.keywords if kw.arg == 'reply_markup')
        return kw.value.func.id if isinstance(kw.value, ast.Call) and isinstance(kw.value.func, ast.Name) else ''

    def test_accounts_uses_account_actions_menu(self):
        self.assertEqual(self._reply_markup_name('accounts'), 'account_actions_menu')

    def test_groups_uses_group_actions_menu(self):
        self.assertEqual(self._reply_markup_name('groups'), 'group_actions_menu')

    def test_action_callbacks_exist(self):
        expected = {
            'act_upload_account',
            'act_set_proxy',
            'act_set_limit',
            'act_sleep_account',
            'act_mark_backup',
            'act_add_group_reference',
            'act_add_group_monitor',
        }
        build_router = next(node for node in self.module.body if isinstance(node, ast.FunctionDef) and node.name == 'build_router')
        handlers = {node.name for node in build_router.body if isinstance(node, ast.AsyncFunctionDef)}
        self.assertTrue(expected.issubset(handlers))


if __name__ == '__main__':
    unittest.main()
