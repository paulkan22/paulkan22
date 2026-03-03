from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(Text)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_category: Mapped[str | None] = mapped_column(Text)
    monitor_group_count: Mapped[int] = mapped_column(Integer, default=0)
    mutual_reference_count: Mapped[int] = mapped_column(Integer, default=0)
    last_mutual_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_chat: Mapped[str | None] = mapped_column(Text)


class Group(Base):
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    cluster_id: Mapped[int | None] = mapped_column(Integer)


class Account(Base):
    __tablename__ = 'accounts'

    id: Mapped[int] = mapped_column(primary_key=True)
    session_path: Mapped[str] = mapped_column(Text)
    api_id: Mapped[int] = mapped_column(Integer, default=0)
    api_hash: Mapped[str] = mapped_column(Text, default='')
    proxy: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    dynamic_limit: Mapped[int] = mapped_column(Integer, default=80)
    trust_score: Mapped[int] = mapped_column(Integer, default=0)
    sleep_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cluster_id: Mapped[int | None] = mapped_column(Integer)


class MutualTask(Base):
    __tablename__ = 'mutual_tasks'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(Text, index=True)
    cluster_id: Mapped[int | None] = mapped_column(Integer)
