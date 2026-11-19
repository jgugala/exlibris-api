from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from exlibris.models import ReadingStatus

# ISBN-10 (nine digits plus a digit or "X") or ISBN-13. Checksums are not validated.
# [0-9] rather than \d, which also matches non-ASCII digits such as "٣".
ISBN = Annotated[str, Field(pattern=r"^([0-9]{9}[0-9X]|[0-9]{13})$", examples=["9780306406157"])]
# Non-blank text, stripped of surrounding whitespace. ShortText matches the String(255)
# columns (title, author); LongText is for the review, which clients clear with null.
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10_000)]
# strict: reject JSON booleans and floats (true would otherwise become 1). The upper bound
# on pages keeps values within SQLite's 64-bit INTEGER, so they fail with 422, not 500.
Pages = Annotated[int, Field(gt=0, le=100_000, strict=True)]
Rating = Annotated[int, Field(ge=1, le=5, strict=True)]


class BookCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    isbn: ISBN
    title: ShortText
    author: ShortText
    pages: Pages | None = None
    status: ReadingStatus = ReadingStatus.WANT_TO_READ
    rating: Rating | None = None
    review: LongText | None = None


def _drop_default(schema: dict[str, Any]) -> None:
    schema.pop("default", None)


# Omittable but not nullable: the None default is not validated, so omitting the field
# works while an explicit null fails validation. The default is hidden from the JSON
# schema, where "default": null would contradict the non-nullable type.
_OMITTABLE = {"default": None, "json_schema_extra": _drop_default}


class BookUpdate(BaseModel):
    """Partial update for PATCH; dump with ``exclude_unset=True``.

    ``isbn`` is immutable, so sending it is rejected by ``extra="forbid"``.
    ``title``, ``author`` and ``status`` may be omitted but not set to null (the columns
    are NOT NULL); a null ``pages``, ``rating`` or ``review`` clears the value.
    """

    model_config = ConfigDict(extra="forbid")

    title: ShortText = Field(**_OMITTABLE)
    author: ShortText = Field(**_OMITTABLE)
    status: ReadingStatus = Field(**_OMITTABLE)
    pages: Pages | None = None
    rating: Rating | None = None
    review: LongText | None = None


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    title: str
    author: str
    pages: int | None
    status: ReadingStatus
    rating: int | None
    review: str | None
    created_at: datetime
