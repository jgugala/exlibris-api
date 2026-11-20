from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from exlibris.models import Book, ReadingStatus
from exlibris.schemas import BookCreate, BookUpdate
from exlibris.services.exceptions import BookNotFoundError, DuplicateIsbnError


def create_book(session: Session, data: BookCreate) -> Book:
    book = Book(**data.model_dump())
    session.add(book)
    try:
        session.commit()
    except IntegrityError:
        # The UNIQUE constraint on isbn is the only one that can fail here: NOT NULL
        # columns are guaranteed by BookCreate. Relying on it instead of a pre-check
        # SELECT also covers two concurrent requests with the same ISBN. The rollback
        # leaves the session usable for the caller.
        session.rollback()
        raise DuplicateIsbnError(data.isbn) from None
    # Load the generated id and defaults now rather than lazily during serialization.
    session.refresh(book)
    return book


def list_books(
    session: Session,
    status: ReadingStatus | None = None,
    skip: int = 0,
    limit: int | None = None,
) -> Sequence[Book]:
    """Books ordered by id; ``limit=None`` means no limit (the API sets its own default).

    The stable ORDER BY is what keeps consecutive pages from overlapping.
    """
    query = select(Book).order_by(Book.id)
    if status is not None:
        query = query.where(Book.status == status)
    return session.scalars(query.offset(skip).limit(limit)).all()


def get_book(session: Session, book_id: int) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise BookNotFoundError(book_id)
    return book


def update_book(session: Session, book_id: int, data: BookUpdate) -> Book:
    book = get_book(session, book_id)
    # Only the fields the client sent: an omitted field stays unchanged, an explicit
    # null clears it (BookUpdate rejects null for the NOT NULL columns).
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    session.commit()
    session.refresh(book)
    return book


def delete_book(session: Session, book_id: int) -> None:
    book = get_book(session, book_id)
    session.delete(book)
    session.commit()
