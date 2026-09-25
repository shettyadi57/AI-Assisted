"""
Reconstruction Stage Router (Phase 4 — Candidate Traversal & Assembly)
"""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from backend.schemas import PhaseNotImplementedResponse

router = APIRouter(prefix="/reconstruction", tags=["Pipeline Stage: Reconstruction"])


@router.post("/candidates", status_code=status.HTTP_501_NOT_IMPLEMENTED, response_model=PhaseNotImplementedResponse)
async def generate_candidates() -> JSONResponse:
    """Traverse relationship graph and generate ranked candidate file reconstructions."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "status_code": 501,
            "detail": "Not implemented — Phase 4: Candidate Traversal and Reconstruction",
            "phase": "Phase 4 — Candidate Reconstruction",
            "stage": "reconstruction",
            "payload": None,
        },
    )


@router.get("/candidates/{candidate_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED, response_model=PhaseNotImplementedResponse)
async def get_candidate(candidate_id: str) -> JSONResponse:
    """Retrieve candidate reconstruction details, fragment sequence, and confidence breakdown."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "status_code": 501,
            "detail": "Not implemented — Phase 4: Candidate Traversal and Reconstruction",
            "phase": "Phase 4 — Candidate Reconstruction",
            "stage": "reconstruction",
            "payload": {"candidate_id": candidate_id},
        },
    )
