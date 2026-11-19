from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from exlibris.dependencies import SessionDep
from exlibris.models import Book, ReadingStatus
from exlibris.schemas import BookCreate, BookRead, BookUpdate

# Ids are positive; the upper bound keeps them within SQLite's 64-bit INTEGER, so
# out-of-range values fail with 422, not 500.
BookId = Annotated[int, Path(ge=1, le=2**63 - 1)]

router = APIRouter(prefix="/books", tags=["books"])


# "" rather than "/" keeps the path at /books, without a trailing-slash redirect.
@router.post("", status_code=status.HTTP_201_CREATED, response_model=BookRead)
def create_book(data: BookCreate, session: SessionDep) -> Book:
    book = Book(**data.model_dump())
    session.add(book)
    try:
        session.commit()
    except IntegrityError:
        # The UNIQUE constraint on isbn is the only one that can fail here: NOT NULL
        # columns are guaranteed by BookCreate. Relying on it instead of a pre-check
        # SELECT also covers two concurrent requests with the same ISBN.
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Book with ISBN {data.isbn} already exists"
        ) from None
    # Load the generated id and defaults now rather than lazily during serialization.
    session.refresh(book)
    return book


@router.get("", response_model=list[BookRead])
def list_books(
    session: SessionDep,
    # Aliased so the parameter does not shadow the fastapi.status module.
    book_status: Annotated[ReadingStatus | None, Query(alias="status")] = None,
) -> Sequence[Book]:
    query = select(Book).order_by(Book.id)
    if book_status is not None:
        query = query.where(Book.status == book_status)
    return session.scalars(query).all()


def _get_book_or_404(session: Session, book_id: int) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    return book


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: BookId, session: SessionDep) -> Book:
    return _get_book_or_404(session, book_id)


@router.patch("/{book_id}", response_model=BookRead)
def update_book(book_id: BookId, data: BookUpdate, session: SessionDep) -> Book:
    book = _get_book_or_404(session, book_id)
    # Only the fields the client sent: an omitted field stays unchanged, an explicit
    # null clears it (BookUpdate rejects null for the NOT NULL columns).
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    session.commit()
    session.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: BookId, session: SessionDep) -> None:
    book = _get_book_or_404(session, book_id)
    session.delete(book)
    session.commit()
