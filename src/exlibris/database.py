from typing import Any

from sqlalchemy import Engine, StaticPool, create_engine

# Tables are registered on Base.metadata by models/__init__.py, which imports every
# model module; a model missing there is silently left out of create_all.
from exlibris.models import Base


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
