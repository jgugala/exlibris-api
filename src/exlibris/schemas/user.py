from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field


def _lower(value: object) -> object:
    return value.lower() if isinstance(value, str) else value


# email-validator lowercases only the domain; the whole address is lowercased so that
# Ann@Example.com and ann@example.com are one account and the response shows what is
# stored. Lowercasing runs before validation, so the stored form is the validated one
# (Unicode case mapping can change a string, e.g. "İ" becomes "i" + a combining dot).
Email = Annotated[EmailStr, BeforeValidator(_lower)]
# Not stripped: whitespace is part of the password. The upper bound caps the work an
# attacker can force on the Argon2 hasher with a huge payload.
Password = Annotated[str, Field(min_length=8, max_length=128)]


class UserCreate(BaseModel):
    # extra="forbid": a client cannot register itself as an admin by sending is_admin.
    model_config = ConfigDict(extra="forbid")

    email: Email
    password: Password


class UserRead(BaseModel):
    """Public view of a user; used as response_model, so password_hash never leaves."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_admin: bool
    created_at: datetime
