import ast
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session

import exlibris.services
from exlibris.models import Book, ReadingStatus
from exlibris.schemas import BookCreate, BookUpdate
from exlibris.services import books as books_service
from exlibris.services.exceptions import BookNotFoundError, DuplicateIsbnError


def book_create(**overrides: Any) -> BookCreate:
    data = {"isbn": "9780306406157", "title": "Effective Java", "author": "Joshua Bloch"}
    return BookCreate(**(data | overrides))


# Layering


def test_services_do_not_import_fastapi_or_starlette() -> None:
    package_dir = Path(exlibris.services.__file__).parent
    imported: set[str] = set()
    for path in package_dir.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)

    assert not {name for name in imported if name.split(".")[0] in {"fastapi", "starlette"}}


# create_book


def test_create_book_returns_book_with_id_and_defaults(db_session: Session) -> None:
    book = books_service.create_book(db_session, book_create())

    assert book.id is not None
    assert book.isbn == "9780306406157"
    assert book.status == ReadingStatus.WANT_TO_READ
    assert book.created_at is not None


def test_create_book_is_persisted(db_session: Session) -> None:
    book = books_service.create_book(db_session, book_create())
    db_session.expunge_all()

    assert db_session.get(Book, book.id) is not None


def test_create_book_duplicate_isbn_raises(db_session: Session) -> None:
    books_service.create_book(db_session, book_create())

    with pytest.raises(DuplicateIsbnError) as exc_info:
        books_service.create_book(db_session, book_create(title="Other"))

    assert exc_info.value.isbn == "9780306406157"


def test_create_book_after_duplicate_session_still_usable(db_session: Session) -> None:
    first = books_service.create_book(db_session, book_create())
    with pytest.raises(DuplicateIsbnError):
        books_service.create_book(db_session, book_create())

    second = books_service.create_book(db_session, book_create(isbn="9780134685991"))

    assert [b.id for b in books_service.list_books(db_session)] == [first.id, second.id]


# list_books


def test_list_books_empty_returns_empty_list(db_session: Session) -> None:
    assert books_service.list_books(db_session) == []


def test_list_books_returns_all_ordered_by_id(db_session: Session) -> None:
    first = books_service.create_book(db_session, book_create(isbn="9780134685991"))
    second = books_service.create_book(db_session, book_create(isbn="9780306406157"))

    assert [b.id for b in books_service.list_books(db_session)] == [first.id, second.id]


def test_list_books_filters_by_status(db_session: Session) -> None:
    books_service.create_book(db_session, book_create(isbn="9780134685991"))
    reading = books_service.create_book(
        db_session, book_create(isbn="9780306406157", status=ReadingStatus.READING)
    )

    result = books_service.list_books(db_session, status=ReadingStatus.READING)

    assert [b.id for b in result] == [reading.id]


# get_book


def test_get_book_returns_book(db_session: Session) -> None:
    created = books_service.create_book(db_session, book_create())

    assert books_service.get_book(db_session, created.id).isbn == created.isbn


def test_get_book_missing_raises(db_session: Session) -> None:
    with pytest.raises(BookNotFoundError) as exc_info:
        books_service.get_book(db_session, 999)

    assert exc_info.value.book_id == 999


# update_book


def test_update_book_changes_sent_field_and_keeps_others(db_session: Session) -> None:
    created = books_service.create_book(db_session, book_create(pages=412))

    book = books_service.update_book(db_session, created.id, BookUpdate(title="New title"))

    assert book.title == "New title"
    assert book.author == "Joshua Bloch"
    assert book.pages == 412


def test_update_book_null_clears_nullable_field(db_session: Session) -> None:
    created = books_service.create_book(db_session, book_create(rating=5))

    book = books_service.update_book(db_session, created.id, BookUpdate(rating=None))

    assert book.rating is None


def test_update_book_missing_raises(db_session: Session) -> None:
    with pytest.raises(BookNotFoundError):
        books_service.update_book(db_session, 999, BookUpdate(title="New title"))


# delete_book


def test_delete_book_removes_book(db_session: Session) -> None:
    created = books_service.create_book(db_session, book_create())

    books_service.delete_book(db_session, created.id)

    with pytest.raises(BookNotFoundError):
        books_service.get_book(db_session, created.id)


def test_delete_book_missing_raises(db_session: Session) -> None:
    with pytest.raises(BookNotFoundError):
        books_service.delete_book(db_session, 999)
