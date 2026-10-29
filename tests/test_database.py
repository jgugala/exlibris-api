from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from exlibris.config import Settings
from exlibris.database import get_session, init_db
from exlibris.main import lifespan
from exlibris.models import Book, ReadingStatus


def make_book(isbn: str = "9780134685991") -> Book:
    return Book(isbn=isbn, title="Effective Java", author="Joshua Bloch")


def test_startup_creates_books_table(client: TestClient) -> None:
    engine = client.app.state.engine

    assert "books" in inspect(engine).get_table_names()


def test_startup_uses_database_url_from_env(client: TestClient, tmp_path: Path) -> None:
    engine = client.app.state.engine

    assert engine.url.database == str(tmp_path / "test.db")
    assert (tmp_path / "test.db").exists()


def test_settings_in_tests_never_point_at_default_database(tmp_path: Path) -> None:
    assert Settings().database_url == f"sqlite:///{tmp_path / 'test.db'}"


def test_create_book_sets_defaults(db_session: Session) -> None:
    book = make_book()
    db_session.add(book)
    db_session.commit()

    assert book.id is not None
    assert book.status is ReadingStatus.WANT_TO_READ
    assert book.created_at is not None
    assert book.pages is None
    assert book.rating is None
    assert book.review is None


def test_create_book_duplicate_isbn_raises_integrity_error(db_session: Session) -> None:
    db_session.add(make_book())
    db_session.commit()
    db_session.add(make_book())

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_get_session_yields_session_bound_to_app_database() -> None:
    # A throwaway app with the real lifespan, so no test route leaks into the main app.
    test_app = FastAPI(lifespan=lifespan)

    @test_app.post("/books-count")
    def count_after_insert(session: Annotated[Session, Depends(get_session)]) -> int:
        session.add(make_book())
        session.commit()
        return len(session.scalars(select(Book)).all())

    with TestClient(test_app) as test_client:
        response = test_client.post("/books-count")

    assert response.status_code == 200
    assert response.json() == 1


def test_created_at_is_utc_aware_after_reload(db_session: Session) -> None:
    book = make_book()
    db_session.add(book)
    db_session.commit()
    db_session.expire_all()

    reloaded = db_session.get(Book, book.id)

    assert reloaded is not None
    assert reloaded.created_at.tzinfo is UTC
    assert reloaded.created_at <= datetime.now(UTC)


def test_created_at_with_other_offset_is_stored_as_utc(db_session: Session) -> None:
    warsaw_noon = datetime(2026, 10, 28, 12, 0, tzinfo=timezone(timedelta(hours=1)))
    book = make_book()
    book.created_at = warsaw_noon
    db_session.add(book)
    db_session.commit()
    db_session.expire_all()

    reloaded = db_session.get(Book, book.id)

    assert reloaded is not None
    assert reloaded.created_at == datetime(2026, 10, 28, 11, 0, tzinfo=UTC)


def test_in_memory_database_is_shared_across_threads() -> None:
    engine = init_db("sqlite://")

    def table_names() -> list[str]:
        return inspect(engine).get_table_names()

    with ThreadPoolExecutor(max_workers=1) as executor:
        names = executor.submit(table_names).result()

    engine.dispose()
    assert "books" in names
