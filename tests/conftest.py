from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from exlibris.database import init_db
from exlibris.main import app


@pytest.fixture(autouse=True)
def database_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Point every test at its own temporary SQLite file, never at exlibris.db."""
    url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    return url


@pytest.fixture
def client() -> Iterator[TestClient]:
    # The context manager runs the lifespan, which creates the engine and tables.
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session(database_url: str) -> Iterator[Session]:
    engine = init_db(database_url)
    with Session(engine) as session:
        yield session
    engine.dispose()
