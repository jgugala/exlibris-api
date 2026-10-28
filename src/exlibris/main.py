from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from exlibris import models  # noqa: F401  (registers tables on Base.metadata)
from exlibris.config import Settings
from exlibris.database import init_db


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
