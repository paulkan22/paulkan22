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
