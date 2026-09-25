"""
Intelligent Fragment Reconstruction — Pydantic Schemas (Phase 0)

Request/response models for the API surface. These are the contracts that
frontend TypeScript types (src/types/index.ts) must mirror exactly.

Naming convention: <Entity>Read = response, <Entity>Create = request body.

Phase 0 only defines schemas. Endpoints will be wired in Phase 1+.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Status vocabulary — shared across all response types
# ---------------------------------------------------------------------------
EvidenceStatus = Literal[
    "CONFIRMED",   # structurally validated
    "INFERRED",    # pattern/heuristic match, not structurally proven
    "UNCERTAIN",   # conflicting or weak evidence
    "MISSING",     # expected fragment absent
    "CORRUPTED",   # present but damaged/unreadable
    "DUPLICATE",   # byte-identical to an existing fragment
]

DecisionOutcome = Literal["ACCEPTED", "REJECTED", "DEFERRED"]


# ---------------------------------------------------------------------------
# System / health
# ---------------------------------------------------------------------------
class PhaseInfo(BaseModel):
    current_phase: int = Field(0, description="Active development phase (0–10)")
    phase_label: str = Field("Scaffolding", description="Human-readable phase name")
    features_available: list[str] = Field(
        default_factory=list,
        description="Feature keys active in this phase",
    )
    features_coming: dict[str, int] = Field(
        default_factory=dict,
        description="feature_key → phase_number for not-yet-available features",
    )


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"] = "ok"
    db_connected: bool
    phase: PhaseInfo
    timestamp: datetime


# ---------------------------------------------------------------------------
# Confidence evidence (Rule 2: always expose individual signals)
# ---------------------------------------------------------------------------
class ConfidenceEvidence(BaseModel):
    """
    The full evidence object behind any confidence score.
    The composite_score is derived from signals — it is never stored or
    returned alone. If a signal was not computed, its value is None and
    the reason field explains why.
    """

    sig_header_match: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Fraction of expected header bytes present (0.0–1.0)"
    )
    sig_offset_continuity: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Byte-offset alignment score (1.0 = perfectly contiguous)"
    )
    sig_structural_validity: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Format-aware structural check result"
    )
    sig_entropy_profile: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Entropy similarity at fragment boundary"
    )
    sig_contradiction_count: int = Field(
        0, ge=0,
        description="Number of mutually contradictory signals detected"
    )
    composite_score: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Weighted composite of the above signals"
    )
    evidence_status: EvidenceStatus = "UNCERTAIN"
    not_computed_reason: Optional[str] = Field(
        None,
        description="If any signal is None, explains why (e.g. 'Coming in Phase 3')"
    )


# ---------------------------------------------------------------------------
# Evidence file
# ---------------------------------------------------------------------------
class EvidenceFileCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None


class EvidenceFileRead(BaseModel):
    id: int
    label: str
    original_filename: str
    size_bytes: int
    sha256_hex: str
    mime_type: Optional[str]
    is_sample_data: bool
    ingested_at: datetime
    notes: Optional[str]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Fragment
# ---------------------------------------------------------------------------
class FragmentRead(BaseModel):
    id: int
    evidence_file_id: int
    sequence_index: int
    byte_offset: int
    size_bytes: int
    sha256_hex: str
    inferred_format: Optional[str]
    status: EvidenceStatus
    header_bytes_hex: Optional[str]
    identified_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Fragment edge (scored relationship)
# ---------------------------------------------------------------------------
class FragmentEdgeRead(BaseModel):
    id: int
    source_fragment_id: int
    target_fragment_id: int
    evidence: ConfidenceEvidence
    computed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Reconstruction candidate
# ---------------------------------------------------------------------------
class ReconstructionCandidateRead(BaseModel):
    id: int
    evidence_file_id: int
    label: str
    inferred_format: Optional[str]
    total_size_bytes: Optional[int]
    sha256_hex: Optional[str]
    outcome: Optional[DecisionOutcome]
    is_finalized: bool
    created_at: datetime
    finalized_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Investigator decision
# ---------------------------------------------------------------------------
class InvestigatorDecisionCreate(BaseModel):
    outcome: DecisionOutcome
    rationale: Optional[str] = Field(
        None,
        description="Required when outcome is REJECTED. Optional otherwise."
    )

    @field_validator("rationale")
    @classmethod
    def rationale_required_on_reject(
        cls, v: Optional[str], info: Any
    ) -> Optional[str]:
        outcome = info.data.get("outcome")
        if outcome == "REJECTED" and not v:
            raise ValueError("Rationale is required when rejecting a candidate.")
        return v


class InvestigatorDecisionRead(BaseModel):
    id: int
    candidate_id: int
    outcome: DecisionOutcome
    rationale: Optional[str]
    decided_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------
class AuditLogEntryRead(BaseModel):
    id: int
    action: str
    actor: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    detail: Optional[str]
    occurred_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# "Not yet available" stub response (Rule 5)
# ---------------------------------------------------------------------------
class FeatureUnavailableResponse(BaseModel):
    available: Literal[False] = False
    feature: str
    coming_in_phase: int
    message: str
