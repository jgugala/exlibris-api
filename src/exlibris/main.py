from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from exlibris.config import Settings
from exlibris.database import get_session, init_db
from exlibris.models import Book, ReadingStatus
from exlibris.schemas import BookCreate, BookRead


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = init_db(Settings().database_url)
    try:
        app.state.engine = engine
        app.state.session_factory = sessionmaker(engine)
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Ex Libris API", version="0.1.0", lifespan=lifespan)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/books", status_code=status.HTTP_201_CREATED, response_model=BookRead, tags=["books"])
def create_book(data: BookCreate, session: Annotated[Session, Depends(get_session)]) -> Book:
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


@app.get("/books", response_model=list[BookRead], tags=["books"])
def list_books(
    session: Annotated[Session, Depends(get_session)],
    # Aliased so the parameter does not shadow the fastapi.status module.
    book_status: Annotated[ReadingStatus | None, Query(alias="status")] = None,
) -> Sequence[Book]:
    query = select(Book).order_by(Book.id)
    if book_status is not None:
        query = query.where(Book.status == book_status)
    return session.scalars(query).all()


@app.get("/books/{book_id}", response_model=BookRead, tags=["books"])
def get_book(
    # The upper bound keeps the id within SQLite's 64-bit INTEGER (422, not 500).
    book_id: Annotated[int, Path(le=2**63 - 1)],
    session: Annotated[Session, Depends(get_session)],
) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    return book
