from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📊 Статистика', callback_data='stats')],
            [InlineKeyboardButton(text='👥 Аккаунты', callback_data='accounts')],
            [InlineKeyboardButton(text='📂 Группы', callback_data='groups')],
            [InlineKeyboardButton(text='📤 Экспорт', callback_data='export_menu')],
            [InlineKeyboardButton(text='🧠 Балансировщик', callback_data='balancer')],
            [
                InlineKeyboardButton(text='▶️ Старт', callback_data='start_system'),
                InlineKeyboardButton(text='🛑 Стоп', callback_data='stop_system'),
            ],
        ]
    )


def export_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📆 За 7 дней', callback_data='export_7')],
            [InlineKeyboardButton(text='📆 За 30 дней', callback_data='export_30')],
            [InlineKeyboardButton(text='🔥 Только горячие', callback_data='export_hot')],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='main')],
        ]
    )


def account_actions_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='➕ Загрузить аккаунт', callback_data='act_upload_account')],
            [InlineKeyboardButton(text='🌐 Установить прокси', callback_data='act_set_proxy')],
            [InlineKeyboardButton(text='⚖️ Установить лимит', callback_data='act_set_limit')],
            [InlineKeyboardButton(text='😴 Отправить в SLEEP', callback_data='act_sleep_account')],
            [InlineKeyboardButton(text='💾 Отметить backup', callback_data='act_mark_backup')],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='main')],
        ]
    )


def group_actions_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='➕ Добавить reference', callback_data='act_add_group_reference')],
            [InlineKeyboardButton(text='➕ Добавить monitor', callback_data='act_add_group_monitor')],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='main')],
        ]
    )
