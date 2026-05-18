"""
FastAPI app entrypoint.

Run with:
    uvicorn cineiq.api.main:app --reload
or via the project script:
    python -m cineiq.api.main
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cineiq import __version__
from cineiq.api.routes import router
from cineiq.api.service import service
from cineiq.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fit on startup so the first request is fast.
    print("[startup] fitting recommendation models...")
    service.warm_up()
    print("[startup] ready.")
    yield


app = FastAPI(
    title="CINEIQ API",
    version=__version__,
    description="Open, explainable movie recommendation engine.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.api.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)


def main() -> None:
    uvicorn.run(
        "cineiq.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
