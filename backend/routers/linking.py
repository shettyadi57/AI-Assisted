"""
Linking Stage Router (Phase 3 — Relationship Scoring & Edge Evaluation)
"""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from backend.schemas import PhaseNotImplementedResponse

router = APIRouter(prefix="/linking", tags=["Pipeline Stage: Linking"])


@router.post("/score", status_code=status.HTTP_501_NOT_IMPLEMENTED, response_model=PhaseNotImplementedResponse)
async def score_relationship() -> JSONResponse:
    """Evaluate multi-signal candidate relationship between two fragments."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "status_code": 501,
            "detail": "Not implemented — Phase 3: Relationship Scoring and Graph Linking",
            "phase": "Phase 3 — Relationship Scoring",
            "stage": "linking",
            "payload": None,
        },
    )


@router.get("/relationships", status_code=status.HTTP_501_NOT_IMPLEMENTED, response_model=PhaseNotImplementedResponse)
async def list_relationships() -> JSONResponse:
    """Retrieve candidate relationship graph edges with decomposed scores."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "status_code": 501,
            "detail": "Not implemented — Phase 3: Relationship Scoring and Graph Linking",
            "phase": "Phase 3 — Relationship Scoring",
            "stage": "linking",
            "payload": None,
        },
    )
