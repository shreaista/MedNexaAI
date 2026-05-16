"""MedNexa API application entry."""

from fastapi import FastAPI

from app.routers import (
    billing_queue,
    census,
    charges,
    facilities,
    health,
    notes,
    patients,
    visits,
)

app = FastAPI(
    title="MedNexa API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health.router, prefix="/health", tags=["system"])
app.include_router(facilities.router)
app.include_router(census.router)
app.include_router(patients.router)
app.include_router(visits.router)
app.include_router(notes.router)
app.include_router(charges.router)
app.include_router(billing_queue.router)
