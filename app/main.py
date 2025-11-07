from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Startup tasks (e.g., database connection) can be initialized here
    yield
    # Shutdown tasks (e.g., closing connections) can be handled here


def create_application() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.project_name,
        debug=settings.debug,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_application()
