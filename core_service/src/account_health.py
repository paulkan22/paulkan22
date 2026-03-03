import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker

from .proxy_utils import parse_socks5_proxy
from .runtime_state import RuntimeState


async def run_account_health_loop(
    session_factory: async_sessionmaker,
    state: RuntimeState,
    every_minutes: int = 30,
    live_mode: bool = False,
) -> None:
    if not live_mode:
        return

    from telethon import TelegramClient
    from .repository import list_accounts

    while True:
        if await state.is_running():
            async with session_factory() as session:
                accounts = await list_accounts(session)
                for account in accounts:
                    proxy = parse_socks5_proxy(account.proxy)
                    client = TelegramClient(account.session_path, int(account.api_id), account.api_hash, proxy=proxy)
                    try:
                        await client.connect()
                        authorized = await client.is_user_authorized()
                        account.status = 'ACTIVE' if authorized else 'ERROR'
                    except Exception:
                        account.status = 'ERROR'
                    finally:
                        await client.disconnect()
                await session.commit()
        await asyncio.sleep(max(1, every_minutes) * 60)
