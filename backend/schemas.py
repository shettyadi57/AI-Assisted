"""
Pydantic Schemas for API Requests & Responses — Phase 1 + Phase 2.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="healthy", description="Service health status")
    version: str = Field(default="0.1.0", description="Application version")
    api_version: str = Field(default="v1", description="API version")
    current_phase: int = Field(default=2, description="Active development phase")
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


# ─── Phase 2: Fragment Analysis ───────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Request body for triggering fragment analysis on an evidence record."""
    evidence_id: str = Field(description="UUID of the evidence record to analyze")
    block_size: int = Field(
        default=4096,
        ge=256,
        le=65536,
        description="Block/cluster size in bytes used to split the evidence blob",
    )
    force_reanalyze: bool = Field(
        default=False,
        description="If True, delete existing fragments and re-analyze from scratch",
    )


class FragmentRecord(BaseModel):
    """A single fragment as returned by the API."""
    id: str
    evidence_id: str
    offset_start: int
    offset_end: int
    size_bytes: int
    sha256_hash: str
    entropy: float
    status: str

    # Phase 2 preliminary classification (NOT signature detection — that's Phase 3)
    entropy_class: str = Field(
        description="PRELIMINARY Phase 2 heuristic: HIGH_ENTROPY | MEDIUM_ENTROPY | LOW_ENTROPY"
    )
    content_class: str = Field(
        description="PRELIMINARY Phase 2 heuristic: PRINTABLE | BINARY | MIXED"
    )
    hex_preview: str = Field(description="First 32 bytes as space-separated uppercase hex")
    flags: list[str] = Field(default_factory=list)

    # Phase 3+ — always null/unknown at this stage
    inferred_format: str | None = Field(
        default=None,
        description="File type — null until Phase 3 signature detection"
    )
    created_at: str
    updated_at: str


class AnalyzeResponse(BaseModel):
    """Result of a fragment analysis run."""
    evidence_id: str
    evidence_filename: str
    fragment_count: int
    duplicate_count: int
    block_size_used: int
    fragments: list[FragmentRecord]
    disclaimer: str = (
        "Phase 2 preliminary analysis only. "
        "Entropy class and content class are heuristics, not forensic conclusions. "
        "File-type identification scheduled for Phase 3."
    )


class FragmentListResponse(BaseModel):
    """List of fragments for an evidence record."""
    evidence_id: str
    total: int
    fragments: list[FragmentRecord]
