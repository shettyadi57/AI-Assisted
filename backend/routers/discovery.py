"""
Discovery Stage Router (Phase 1 — Evidence Ingest & Sector Discovery)
"""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from backend.schemas import PhaseNotImplementedResponse

router = APIRouter(prefix="/discovery", tags=["Pipeline Stage: Discovery"])


@router.post("/ingest", status_code=status.HTTP_501_NOT_IMPLEMENTED, response_model=PhaseNotImplementedResponse)
async def ingest_evidence() -> JSONResponse:
    """Ingest raw storage media or disk image (Read-only, SHA-256 hashed)."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "status_code": 501,
            "detail": "Not implemented — Phase 1: Evidence Discovery and Ingest",
            "phase": "Phase 1 — Evidence Ingest",
            "stage": "discovery",
            "payload": None,
        },
    )


@router.get("/evidence", status_code=status.HTTP_501_NOT_IMPLEMENTED, response_model=PhaseNotImplementedResponse)
async def list_evidence() -> JSONResponse:
    """List ingested evidence artifacts and verification states."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "status_code": 501,
            "detail": "Not implemented — Phase 1: Evidence Discovery and Ingest",
            "phase": "Phase 1 — Evidence Ingest",
            "stage": "discovery",
            "payload": None,
        },
    )
