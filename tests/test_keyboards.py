import ast
import unittest
from pathlib import Path


KEYBOARDS_FILE = Path('bot_service/src/keyboards.py')


class KeyboardsSourceTests(unittest.TestCase):
    @staticmethod
    def _extract_button_rows(function_name: str):
        source = KEYBOARDS_FILE.read_text(encoding='utf-8')
        module = ast.parse(source)
        func = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == function_name)
        call = func.body[0].value
        inline_keyboard_kw = next(kw for kw in call.keywords if kw.arg == 'inline_keyboard')

        rows = []
        for row_node in inline_keyboard_kw.value.elts:
            row = []
            for button_node in row_node.elts:
                kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in button_node.keywords}
                row.append((kwargs['text'], kwargs['callback_data']))
            rows.append(row)
        return rows

    def test_main_menu_labels_and_callbacks(self):
        self.assertEqual(
            self._extract_button_rows('main_menu'),
            [
                [('📊 Статистика', 'stats')],
                [('👥 Аккаунты', 'accounts')],
                [('📂 Группы', 'groups')],
                [('📤 Экспорт', 'export_menu')],
                [('🧠 Балансировщик', 'balancer')],
                [('▶️ Старт', 'start_system'), ('🛑 Стоп', 'stop_system')],
            ],
        )

    def test_export_menu_labels_and_callbacks(self):
        self.assertEqual(
            self._extract_button_rows('export_menu'),
            [
                [('📆 За 7 дней', 'export_7')],
                [('📆 За 30 дней', 'export_30')],
                [('🔥 Только горячие', 'export_hot')],
                [('⬅️ Назад', 'main')],
            ],
        )

    def test_account_actions_menu_labels_and_callbacks(self):
        self.assertEqual(
            self._extract_button_rows('account_actions_menu'),
            [
                [('➕ Загрузить аккаунт', 'act_upload_account')],
                [('🌐 Установить прокси', 'act_set_proxy')],
                [('⚖️ Установить лимит', 'act_set_limit')],
                [('😴 Отправить в SLEEP', 'act_sleep_account')],
                [('💾 Отметить backup', 'act_mark_backup')],
                [('⬅️ Назад', 'main')],
            ],
        )

    def test_group_actions_menu_labels_and_callbacks(self):
        self.assertEqual(
            self._extract_button_rows('group_actions_menu'),
            [
                [('➕ Добавить reference', 'act_add_group_reference')],
                [('➕ Добавить monitor', 'act_add_group_monitor')],
                [('⬅️ Назад', 'main')],
            ],
        )


if __name__ == '__main__':
    unittest.main()
