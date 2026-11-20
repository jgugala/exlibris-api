from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from exlibris.dependencies import SessionDep
from exlibris.models import Book, ReadingStatus
from exlibris.schemas import BookCreate, BookRead, BookUpdate
from exlibris.services import books as books_service
from exlibris.services.exceptions import BookNotFoundError, DuplicateIsbnError

# Ids are positive; the upper bound keeps them within SQLite's 64-bit INTEGER, so
# out-of-range values fail with 422, not 500.
BookId = Annotated[int, Path(ge=1, le=2**63 - 1)]
# Pagination: skip is bounded like BookId so an out-of-range offset fails with 422.
Skip = Annotated[int, Query(ge=0, le=2**63 - 1)]
Limit = Annotated[int, Query(ge=1, le=100)]

router = APIRouter(prefix="/books", tags=["books"])


def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")


# "" rather than "/" keeps the path at /books, without a trailing-slash redirect.
@router.post("", status_code=status.HTTP_201_CREATED, response_model=BookRead)
def create_book(data: BookCreate, session: SessionDep) -> Book:
    try:
        return books_service.create_book(session, data)
    except DuplicateIsbnError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None


@router.get("", response_model=list[BookRead])
def list_books(
    session: SessionDep,
    # Aliased so the parameter does not shadow the fastapi.status module.
    book_status: Annotated[ReadingStatus | None, Query(alias="status")] = None,
    skip: Skip = 0,
    limit: Limit = 20,
) -> Sequence[Book]:
    return books_service.list_books(session, status=book_status, skip=skip, limit=limit)


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: BookId, session: SessionDep) -> Book:
    try:
        return books_service.get_book(session, book_id)
    except BookNotFoundError:
        raise _not_found() from None


@router.patch("/{book_id}", response_model=BookRead)
def update_book(book_id: BookId, data: BookUpdate, session: SessionDep) -> Book:
    try:
        return books_service.update_book(session, book_id, data)
    except BookNotFoundError:
        raise _not_found() from None


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: BookId, session: SessionDep) -> None:
    try:
        books_service.delete_book(session, book_id)
    except BookNotFoundError:
        raise _not_found() from None
