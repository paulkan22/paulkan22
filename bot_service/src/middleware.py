from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class WhitelistMiddleware(BaseMiddleware):
    def __init__(self, allowed: set[int]):
        self.allowed = allowed

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        if isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id in self.allowed:
            return await handler(event, data)

        if isinstance(event, Message):
            await event.answer('Доступ запрещен.')
        elif isinstance(event, CallbackQuery):
            await event.answer('Доступ запрещен.', show_alert=True)
        return None
