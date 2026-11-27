from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from exlibris.config import Settings
from exlibris.database import init_db
from exlibris.routers import auth, books, health


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
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(books.router)
