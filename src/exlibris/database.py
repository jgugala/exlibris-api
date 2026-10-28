from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from sqlalchemy import DateTime, Dialect, Engine, StaticPool, TypeDecorator, create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


class UTCDateTime(TypeDecorator[datetime]):
    """Timezone-aware datetime stored in UTC.

    SQLite drops the offset on write, so values are converted to UTC before storing
    and marked as UTC again when read.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is not None:
            if value.tzinfo is None:
                raise ValueError("naive datetime given, expected a timezone-aware one")
            value = value.astimezone(UTC)
        return value

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value


def create_db_engine(url: str) -> Engine:
    kwargs: dict[str, Any] = {}
    if url.startswith("sqlite"):
        # SQLite connections are bound to their thread by default, but sync endpoints
        # run in a thread pool, so a session may be used outside the creating thread.
        kwargs["connect_args"] = {"check_same_thread": False}
        if url in ("sqlite://", "sqlite:///:memory:"):
            # Each connection to :memory: is a separate database; share a single one.
            kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


def init_db(url: str) -> Engine:
    engine = create_db_engine(url)
    Base.metadata.create_all(engine)
    return engine


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session
