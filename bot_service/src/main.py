import asyncio
import logging

from aiogram import Bot, Dispatcher
from redis.asyncio import Redis

from .config import Settings
from .db import build_session_factory
from .handlers import build_router
from .middleware import WhitelistMiddleware
from .services import BotDataService
from .state import SystemStateStore


async def run() -> None:
    settings = Settings()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    state_store = SystemStateStore(redis_client)

    service = BotDataService(build_session_factory(settings))
    dp.message.middleware(WhitelistMiddleware(settings.whitelist_ids()))
    dp.callback_query.middleware(WhitelistMiddleware(settings.whitelist_ids()))
    dp.include_router(build_router(service, state_store))

    try:
        await dp.start_polling(bot)
    finally:
        await redis_client.aclose()
        await bot.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
