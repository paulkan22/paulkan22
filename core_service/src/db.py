from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import Settings


def build_engine(settings: Settings):
    return create_async_engine(settings.database_url, pool_pre_ping=True)


def build_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    engine = build_engine(settings)
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        yield session
