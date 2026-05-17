"""MedNexa API application entry."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

import app.models  # noqa: F401 — register ORM mappings
from app.core.config import get_settings
from app.routers import billing_queue, census, charges, debug, facilities, health, notes, patients, providers, visits

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MedNexa API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

_settings = get_settings()
# Browser CORS: defaults include local Next.js + Azure Container Apps web URL.
# Override via env CORS_ORIGINS (comma-separated) or legacy CORS_ALLOW_ORIGINS — see app.core.config.Settings.
_cors_list = [
    origin.strip()
    for origin in _settings.cors_allow_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Database error while handling %s %s", request.method, request.url.path)
    origin = getattr(exc, "orig", None)
    detail = str(origin or exc)
    return JSONResponse(
        status_code=500,
        content={"detail": detail[:500] if detail else "Database error"},
    )


app.include_router(health.router, prefix="/health", tags=["system"])
app.include_router(debug.router, prefix="/debug")
app.include_router(facilities.router)
app.include_router(census.router)
app.include_router(patients.router)
app.include_router(providers.router)
app.include_router(visits.router)
app.include_router(notes.router)
app.include_router(charges.router)
app.include_router(billing_queue.router)
