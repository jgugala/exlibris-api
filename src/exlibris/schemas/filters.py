from typing import Annotated

from pydantic import Field
from pydantic.dataclasses import dataclass

from exlibris.models import ReadingStatus
from exlibris.schemas.book import ShortText


@dataclass
class BookFilters:
    """Filters for ``GET /books``, combined with AND.

    Used as a class dependency (``Annotated[BookFilters, Depends()]``): FastAPI reads the
    ``__init__`` parameters as query parameters. The constraints are plain Pydantic ones,
    so services can take this class without depending on FastAPI, and being a Pydantic
    dataclass it validates on direct construction too (a blank ``author`` would
    otherwise become ``%%`` and match every book). The newer alternative
    is a Pydantic model declared with ``Annotated[BookFilters, Query()]``, which can also
    reject unknown parameters via ``extra="forbid"``.
    """

    status: ReadingStatus | None = None
    # Not the strict Rating type: query parameters arrive as strings.
    min_rating: Annotated[int | None, Field(ge=1, le=5)] = None
    # Case-insensitive substring of the author; blank values are rejected.
    author: ShortText | None = None
