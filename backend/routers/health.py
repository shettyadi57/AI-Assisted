"""
Health Check Router
"""

from __future__ import annotations

from fastapi import APIRouter
from backend.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """System health check endpoint."""
    return HealthResponse()
