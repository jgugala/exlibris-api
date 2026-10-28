from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from exlibris.database import Base, UTCDateTime


class ReadingStatus(StrEnum):
    WANT_TO_READ = "want_to_read"
    READING = "reading"
    READ = "read"


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    isbn: Mapped[str] = mapped_column(String(13), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(255))
    pages: Mapped[int | None]
    status: Mapped[ReadingStatus] = mapped_column(
        # Store enum values ("want_to_read"), not member names ("WANT_TO_READ").
        Enum(ReadingStatus, native_enum=False, values_callable=lambda e: [m.value for m in e]),
        default=ReadingStatus.WANT_TO_READ,
    )
    rating: Mapped[int | None]
    review: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=lambda: datetime.now(UTC))
