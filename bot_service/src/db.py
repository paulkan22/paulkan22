from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .config import Settings


def build_session_factory(settings: Settings) -> async_sessionmaker:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)
