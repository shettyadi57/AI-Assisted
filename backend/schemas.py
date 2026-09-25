"""
Pydantic Schemas for API Requests & Responses
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="healthy", description="Service health status")
    version: str = Field(default="0.1.0", description="Application version")
    api_version: str = Field(default="v1", description="API version")
    current_phase: int = Field(default=0, description="Active development phase")
    disclaimer: str = Field(
        default="Portfolio / prototype tool. Not legally admissible.",
        description="Non-negotiable legal disclaimer"
    )


class PhaseNotImplementedResponse(BaseModel):
    """Standard response for endpoints scheduled for future phases."""
    status_code: int = Field(default=501, description="HTTP status code")
    detail: str = Field(..., description="Explanation of deferred phase")
    phase: str = Field(..., description="Target implementation phase")
    stage: str = Field(..., description="Pipeline stage identifier")
    payload: dict[str, Any] | None = Field(default=None, description="Optional request echo or context")
