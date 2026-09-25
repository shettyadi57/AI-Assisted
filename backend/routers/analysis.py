"""
Analysis Stage Router (Phase 2 — Fragment Identification & Analysis)
"""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from backend.schemas import PhaseNotImplementedResponse

router = APIRouter(prefix="/analysis", tags=["Pipeline Stage: Analysis"])


@router.post("/fragments", status_code=status.HTTP_501_NOT_IMPLEMENTED, response_model=PhaseNotImplementedResponse)
async def carve_fragments() -> JSONResponse:
    """Carve fragments from evidence using entropy profiling and magic numbers."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "status_code": 501,
            "detail": "Not implemented — Phase 2: Fragment Identification and Analysis",
            "phase": "Phase 2 — Fragment Identification",
            "stage": "analysis",
            "payload": None,
        },
    )


@router.get("/fragments/{fragment_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED, response_model=PhaseNotImplementedResponse)
async def get_fragment(fragment_id: str) -> JSONResponse:
    """Retrieve detailed metadata and hex entropy distribution for a fragment."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "status_code": 501,
            "detail": "Not implemented — Phase 2: Fragment Identification and Analysis",
            "phase": "Phase 2 — Fragment Identification",
            "stage": "analysis",
            "payload": {"fragment_id": fragment_id},
        },
    )
