from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from exlibris.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stored lowercase (UserCreate normalizes it), so the UNIQUE constraint alone rejects
    # the same address in a different case. 320 is the RFC 5321 maximum length.
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(default=False)
