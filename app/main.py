from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    # Add CORS middleware to allow frontend requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:5173",  # Vite default
            "https://main.d1hf5ka9zgg3di.amplifyapp.com",  # Production frontend
        ],
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
    )

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_application()
