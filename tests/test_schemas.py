import json
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from exlibris.models import Book, ReadingStatus
from exlibris.schemas import BookCreate, BookRead, BookUpdate


def book_data(**overrides: Any) -> dict[str, Any]:
    return {
        "isbn": "9780306406157",
        "title": "Effective Java",
        "author": "Joshua Bloch",
    } | overrides


# BookCreate


def test_create_book_minimal_applies_defaults() -> None:
    book = BookCreate.model_validate(book_data())

    assert book.status is ReadingStatus.WANT_TO_READ
    assert (book.pages, book.rating, book.review) == (None, None, None)


@pytest.mark.parametrize("isbn", ["0306406152", "080442957X", "9780306406157"])
def test_create_book_valid_isbn_passes(isbn: str) -> None:
    assert BookCreate.model_validate(book_data(isbn=isbn)).isbn == isbn


@pytest.mark.parametrize(
    "isbn",
    [
        "12345678901",  # 11 characters
        "030640615",  # 9 characters
        "97803064061570",  # 14 characters
        "080442957x",  # lowercase x
        "978030640615X",  # X is only allowed in ISBN-10
        "X306406152",  # X only as the last character
        "978-0306406157",  # hyphens are not stripped
        "٩٧٨٠٣٠٦٤٠٦١٥٧",  # Arabic-Indic digits
        "９７８０３０６４０６１５７",  # fullwidth digits
    ],
)
def test_create_book_invalid_isbn_raises(isbn: str) -> None:
    with pytest.raises(ValidationError):
        BookCreate.model_validate(book_data(isbn=isbn))


@pytest.mark.parametrize("rating", [0, 6])
def test_create_book_rating_out_of_range_raises(rating: int) -> None:
    with pytest.raises(ValidationError):
        BookCreate.model_validate(book_data(rating=rating))


@pytest.mark.parametrize("rating", [1, 5])
def test_create_book_rating_bounds_pass(rating: int) -> None:
    assert BookCreate.model_validate(book_data(rating=rating)).rating == rating


@pytest.mark.parametrize("pages", [0, -1, 100_001, 2**63])
def test_create_book_pages_out_of_range_raises(pages: int) -> None:
    with pytest.raises(ValidationError):
        BookCreate.model_validate(book_data(pages=pages))


@pytest.mark.parametrize("field", ["pages", "rating"])
@pytest.mark.parametrize("value", [True, 3.0, "3"])
def test_create_book_non_integer_json_value_raises(field: str, value: Any) -> None:
    payload = json.dumps(book_data(**{field: value}))

    with pytest.raises(ValidationError):
        BookCreate.model_validate_json(payload)


def test_create_book_unknown_status_raises() -> None:
    with pytest.raises(ValidationError):
        BookCreate.model_validate(book_data(status="finished"))


@pytest.mark.parametrize("field", ["title", "author"])
@pytest.mark.parametrize("value", ["", "   ", "x" * 256])
def test_create_book_invalid_title_or_author_raises(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        BookCreate.model_validate(book_data(**{field: value}))


def test_create_book_strips_title_whitespace() -> None:
    assert BookCreate.model_validate(book_data(title="  Dune  ")).title == "Dune"


@pytest.mark.parametrize("review", ["", "   ", "x" * 10_001])
def test_create_book_invalid_review_raises(review: str) -> None:
    with pytest.raises(ValidationError):
        BookCreate.model_validate(book_data(review=review))


def test_create_book_strips_review_whitespace() -> None:
    assert BookCreate.model_validate(book_data(review=" Great. ")).review == "Great."


@pytest.mark.parametrize("field", ["isbn", "title", "author"])
def test_create_book_missing_required_field_raises(field: str) -> None:
    data = book_data()
    del data[field]

    with pytest.raises(ValidationError):
        BookCreate.model_validate(data)


def test_create_book_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        BookCreate.model_validate(book_data(id=1))


# BookUpdate


def test_update_book_dump_exclude_unset_contains_only_sent_fields() -> None:
    update = BookUpdate.model_validate({"rating": 4})

    assert update.model_dump(exclude_unset=True) == {"rating": 4}


def test_update_book_isbn_raises() -> None:
    with pytest.raises(ValidationError):
        BookUpdate.model_validate({"isbn": "0306406152"})


def test_update_book_empty_payload_is_valid() -> None:
    assert BookUpdate.model_validate({}).model_dump(exclude_unset=True) == {}


@pytest.mark.parametrize("field", ["pages", "rating", "review"])
def test_update_book_null_clears_nullable_field(field: str) -> None:
    update = BookUpdate.model_validate({field: None})

    assert update.model_dump(exclude_unset=True) == {field: None}


@pytest.mark.parametrize("field", ["title", "author", "status"])
def test_update_book_null_for_required_field_raises(field: str) -> None:
    with pytest.raises(ValidationError):
        BookUpdate.model_validate({field: None})


@pytest.mark.parametrize(
    "payload",
    [{"rating": 6}, {"pages": 0}, {"title": "  "}, {"status": "finished"}],
)
def test_update_book_invalid_value_raises(payload: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        BookUpdate.model_validate(payload)


@pytest.mark.parametrize("field", ["title", "author", "status"])
def test_update_book_json_schema_has_no_null_default(field: str) -> None:
    schema = BookUpdate.model_json_schema()

    assert "default" not in schema["properties"][field]


# BookRead


def test_read_book_from_orm_object_maps_all_fields() -> None:
    created_at = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
    book = Book(
        id=7,
        isbn="9780306406157",
        title="Effective Java",
        author="Joshua Bloch",
        pages=412,
        status=ReadingStatus.READ,
        rating=5,
        review="Great.",
        created_at=created_at,
    )

    read = BookRead.model_validate(book)

    assert read.model_dump() == {
        "id": 7,
        "isbn": "9780306406157",
        "title": "Effective Java",
        "author": "Joshua Bloch",
        "pages": 412,
        "status": ReadingStatus.READ,
        "rating": 5,
        "review": "Great.",
        "created_at": created_at,
    }
