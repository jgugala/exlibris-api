import ast
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

import exlibris.services
from exlibris.models import Book, ReadingStatus
from exlibris.schemas import BookCreate, BookFilters, BookUpdate
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


def test_list_books_ordered_by_id(db_session: Session) -> None:
    first = books_service.create_book(db_session, book_create(isbn="9780134685991"))
    second = books_service.create_book(db_session, book_create(isbn="9780306406157"))

    assert [b.id for b in books_service.list_books(db_session)] == [first.id, second.id]


def test_list_books_filters_by_status(db_session: Session) -> None:
    books_service.create_book(db_session, book_create(isbn="9780134685991"))
    reading = books_service.create_book(
        db_session, book_create(isbn="9780306406157", status=ReadingStatus.READING)
    )

    result = books_service.list_books(db_session, BookFilters(status=ReadingStatus.READING))

    assert [b.id for b in result] == [reading.id]


def test_list_books_min_rating_excludes_lower_and_unrated(db_session: Session) -> None:
    books_service.create_book(db_session, book_create(isbn="9780000000001", rating=2))
    rated_4 = books_service.create_book(db_session, book_create(isbn="9780000000002", rating=4))
    books_service.create_book(db_session, book_create(isbn="9780000000003"))

    result = books_service.list_books(db_session, BookFilters(min_rating=3))

    assert [b.id for b in result] == [rated_4.id]


def test_list_books_author_is_case_insensitive_substring(db_session: Session) -> None:
    bloch = books_service.create_book(db_session, book_create(isbn="9780000000001"))
    books_service.create_book(db_session, book_create(isbn="9780000000002", author="Martin Fowler"))

    result = books_service.list_books(db_session, BookFilters(author="BLOCH"))

    assert [b.id for b in result] == [bloch.id]


@pytest.mark.parametrize("wildcard", ["%", "_", "\\"])
def test_list_books_author_matches_like_wildcards_literally(
    db_session: Session, wildcard: str
) -> None:
    literal = books_service.create_book(
        db_session, book_create(isbn="9780000000001", author=f"A{wildcard}B")
    )
    books_service.create_book(db_session, book_create(isbn="9780000000002", author="AxB"))

    result = books_service.list_books(db_session, BookFilters(author=f"a{wildcard}b"))

    assert [b.id for b in result] == [literal.id]


def test_list_books_combines_filters_with_and(db_session: Session) -> None:
    match = books_service.create_book(
        db_session, book_create(isbn="9780000000001", status=ReadingStatus.READ, rating=5)
    )
    books_service.create_book(
        db_session, book_create(isbn="9780000000002", status=ReadingStatus.READ, rating=2)
    )
    books_service.create_book(
        db_session, book_create(isbn="9780000000003", status=ReadingStatus.READING, rating=5)
    )
    books_service.create_book(
        db_session,
        book_create(isbn="9780000000004", status=ReadingStatus.READ, rating=5, author="Fowler"),
    )

    result = books_service.list_books(
        db_session, BookFilters(status=ReadingStatus.READ, min_rating=4, author="bloch")
    )

    assert [b.id for b in result] == [match.id]


@pytest.mark.parametrize("kwargs", [{"author": ""}, {"author": "  "}, {"min_rating": 0}])
def test_book_filters_invalid_values_raise_on_construction(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        BookFilters(**kwargs)


def test_list_books_applies_skip_and_limit(db_session: Session) -> None:
    ids = [
        books_service.create_book(db_session, book_create(isbn=f"{9780000000000 + n}")).id
        for n in range(5)
    ]

    result = books_service.list_books(db_session, skip=1, limit=2)

    assert [b.id for b in result] == ids[1:3]


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
