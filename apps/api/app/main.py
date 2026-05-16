"""MedNexa API application entry."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

import app.models  # noqa: F401 — register ORM mappings
from app.routers import billing_queue, census, charges, facilities, health, notes, patients, visits

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MedNexa API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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
app.include_router(facilities.router)
app.include_router(census.router)
app.include_router(patients.router)
app.include_router(visits.router)
app.include_router(notes.router)
app.include_router(charges.router)
app.include_router(billing_queue.router)
