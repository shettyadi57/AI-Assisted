"""
Pydantic Schemas for API Requests & Responses — Phase 1 extended.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="healthy", description="Service health status")
    version: str = Field(default="0.1.0", description="Application version")
    api_version: str = Field(default="v1", description="API version")
    current_phase: int = Field(default=1, description="Active development phase")
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


# ─── Phase 1: Evidence ───────────────────────────────────────────────────────

class EvidenceRecord(BaseModel):
    """Persisted evidence record returned after ingest."""
    id: str
    filename: str
    file_size_bytes: int
    sha256_hash: str
    md5_hash: str | None
    source_type: str
    status: str
    is_sample_dataset: bool = Field(
        description="True if this is a sample fixture; always shown to UI for transparency."
    )
    disclaimer: str = "Sample dataset — not real evidence. Not legally admissible."
    created_at: str
    updated_at: str


class EvidenceIngestRequest(BaseModel):
    """Request body for registering evidence from a client-computed hash."""
    filename: str
    file_size_bytes: int
    sha256_hash: str = Field(
        description="SHA-256 hash computed client-side or uploaded by backend. Verified on ingest."
    )
    source_type: str = Field(
        default="binary_fragment_files",
        description=(
            "One of: raw_disk_image, forensic_image, binary_fragment_files, "
            "extracted_block_files, zip_of_fragments, sample_dataset"
        ),
    )
    is_sample_dataset: bool = Field(
        default=False,
        description="Set True when loading the built-in sample dataset."
    )


class EvidenceListResponse(BaseModel):
    """Paginated list of evidence records."""
    total: int
    items: list[EvidenceRecord]
