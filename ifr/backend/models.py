"""
Intelligent Fragment Reconstruction — ORM Models (Phase 0)

Canonical database schema. Every table comment describes what Phase introduces it.
Evidence-side tables (EvidenceFile) are logically read-only after ingest.
All derived/analysis tables write to a separate artifact area.

Status vocabulary enforced at DB level via CHECK constraints mirrors the UI:
  CONFIRMED     — structurally validated
  INFERRED      — pattern/heuristic match, not structurally proven
  UNCERTAIN     — conflicting or weak evidence
  MISSING       — expected but absent
  CORRUPTED     — present but unreadable/damaged
  DUPLICATE     — byte-for-byte or near-duplicate of an existing fragment
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ---------------------------------------------------------------------------
# Enumerations (mirrored 1-to-1 in frontend TypeScript types)
# ---------------------------------------------------------------------------
class EvidenceStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    INFERRED = "INFERRED"
    UNCERTAIN = "UNCERTAIN"
    MISSING = "MISSING"
    CORRUPTED = "CORRUPTED"
    DUPLICATE = "DUPLICATE"


class DecisionOutcome(str, enum.Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"


class AuditAction(str, enum.Enum):
    EVIDENCE_INGESTED = "EVIDENCE_INGESTED"
    FRAGMENT_IDENTIFIED = "FRAGMENT_IDENTIFIED"
    CANDIDATE_CREATED = "CANDIDATE_CREATED"
    CANDIDATE_ACCEPTED = "CANDIDATE_ACCEPTED"
    CANDIDATE_REJECTED = "CANDIDATE_REJECTED"
    CANDIDATE_DEFERRED = "CANDIDATE_DEFERRED"
    ARTIFACT_EXPORTED = "ARTIFACT_EXPORTED"
    PHASE_FEATURE_UNAVAILABLE = "PHASE_FEATURE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# Phase 0 — Evidence file table (populated in Phase 1: ingest)
# ---------------------------------------------------------------------------
class EvidenceFile(Base):
    """
    Represents one ingested evidence source (disk image, raw blob, etc.).
    Logically read-only after creation — no analysis code may mutate it.
    Introduced: Phase 0 (schema); populated: Phase 1 (ingest endpoint).
    """

    __tablename__ = "evidence_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hex: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_sample_data: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    fragments: Mapped[list["Fragment"]] = relationship(
        "Fragment", back_populates="evidence_file", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Phase 0 — Fragment table (populated in Phase 2: fragment identification)
# ---------------------------------------------------------------------------
class Fragment(Base):
    """
    A contiguous run of bytes believed to belong to one logical file.
    Identified by the FragmentAnalyzer in Phase 2.
    status reflects how confidently the fragment is understood.
    """

    __tablename__ = "fragments"
    __table_args__ = (
        CheckConstraint(
            "byte_offset >= 0", name="ck_fragment_offset_nonneg"
        ),
        CheckConstraint(
            "size_bytes > 0", name="ck_fragment_size_pos"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evidence_file_id: Mapped[int] = mapped_column(
        ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    byte_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hex: Mapped[str] = mapped_column(String(64), nullable=False)

    # What the fragment appears to be (inferred, not guaranteed)
    inferred_format: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[EvidenceStatus] = mapped_column(
        Enum(EvidenceStatus), nullable=False, default=EvidenceStatus.UNCERTAIN
    )
    header_bytes_hex: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="First 16 bytes as hex string, for quick display"
    )

    identified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    evidence_file: Mapped["EvidenceFile"] = relationship(
        "EvidenceFile", back_populates="fragments"
    )
    outgoing_edges: Mapped[list["FragmentEdge"]] = relationship(
        "FragmentEdge",
        foreign_keys="FragmentEdge.source_fragment_id",
        back_populates="source_fragment",
        cascade="all, delete-orphan",
    )
    incoming_edges: Mapped[list["FragmentEdge"]] = relationship(
        "FragmentEdge",
        foreign_keys="FragmentEdge.target_fragment_id",
        back_populates="target_fragment",
    )


# ---------------------------------------------------------------------------
# Phase 0 — Fragment edge table (scored relationships, Phase 3)
# ---------------------------------------------------------------------------
class FragmentEdge(Base):
    """
    A scored candidate relationship between two fragments:
      source_fragment → target_fragment  (i.e., target follows source)

    Confidence is NOT a single percentage. It is the composite of five
    independent signals. The composite_score is computed from them but the
    individual signals are always stored and displayed.

    Introduced: Phase 0 (schema); populated: Phase 3 (relationship engine).
    """

    __tablename__ = "fragment_edges"
    __table_args__ = (
        UniqueConstraint(
            "source_fragment_id", "target_fragment_id", name="uq_edge_pair"
        ),
        CheckConstraint(
            "source_fragment_id != target_fragment_id", name="ck_edge_no_self_loop"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_fragment_id: Mapped[int] = mapped_column(
        ForeignKey("fragments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_fragment_id: Mapped[int] = mapped_column(
        ForeignKey("fragments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ---- The five evidence signals (Rule 2: never a bare percentage) ----
    # Each signal is 0.0–1.0, or NULL if not computed/applicable.
    sig_header_match: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Fraction of expected header bytes present at boundary (0.0–1.0)"
    )
    sig_offset_continuity: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="How well byte offsets align (1.0 = perfectly contiguous)"
    )
    sig_structural_validity: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Result of format-aware structural check (0.0 / 0.5 / 1.0)"
    )
    sig_entropy_profile: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Entropy similarity between tail of source and head of target"
    )
    sig_contradiction_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Number of mutually contradictory signals detected"
    )

    # Composite (computed by confidence_analyzer, stored for caching)
    composite_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evidence_status: Mapped[EvidenceStatus] = mapped_column(
        Enum(EvidenceStatus), nullable=False, default=EvidenceStatus.UNCERTAIN
    )

    computed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    source_fragment: Mapped["Fragment"] = relationship(
        "Fragment", foreign_keys=[source_fragment_id], back_populates="outgoing_edges"
    )
    target_fragment: Mapped["Fragment"] = relationship(
        "Fragment", foreign_keys=[target_fragment_id], back_populates="incoming_edges"
    )
    reconstruction_memberships: Mapped[list["ReconstructionCandidateEdge"]] = relationship(
        "ReconstructionCandidateEdge", back_populates="edge"
    )


# ---------------------------------------------------------------------------
# Phase 0 — Reconstruction candidate (Phase 4)
# ---------------------------------------------------------------------------
class ReconstructionCandidate(Base):
    """
    A proposed ordering of fragments assembled into a candidate file.
    Must go through investigator accept/reject before being treated as final
    (Rule 6). Rejection appends to audit_log, never mutates prior state.
    """

    __tablename__ = "reconstruction_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evidence_file_id: Mapped[int] = mapped_column(
        ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    inferred_format: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    total_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sha256_hex: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="Hash of assembled candidate bytes; NULL until finalized"
    )

    # Status lifecycle: PENDING → (ACCEPTED | REJECTED | DEFERRED)
    outcome: Mapped[Optional[DecisionOutcome]] = mapped_column(
        Enum(DecisionOutcome), nullable=True, default=None
    )
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finalized_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    edges: Mapped[list["ReconstructionCandidateEdge"]] = relationship(
        "ReconstructionCandidateEdge",
        back_populates="candidate",
        cascade="all, delete-orphan",
        order_by="ReconstructionCandidateEdge.position",
    )
    decisions: Mapped[list["InvestigatorDecision"]] = relationship(
        "InvestigatorDecision", back_populates="candidate"
    )


class ReconstructionCandidateEdge(Base):
    """Junction table: ordered edges within a candidate reconstruction."""

    __tablename__ = "reconstruction_candidate_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("reconstruction_candidates.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    edge_id: Mapped[int] = mapped_column(
        ForeignKey("fragment_edges.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Ordering position within this candidate (0-indexed)"
    )

    candidate: Mapped["ReconstructionCandidate"] = relationship(
        "ReconstructionCandidate", back_populates="edges"
    )
    edge: Mapped["FragmentEdge"] = relationship(
        "FragmentEdge", back_populates="reconstruction_memberships"
    )


# ---------------------------------------------------------------------------
# Phase 0 — Investigator decision log (Phase 5: accept/reject workflow)
# ---------------------------------------------------------------------------
class InvestigatorDecision(Base):
    """
    Records every accept/reject/defer action taken by an investigator.
    Append-only: never update or delete rows. Rejections do not mutate
    the candidate — they only add a row here and update candidate.outcome.
    """

    __tablename__ = "investigator_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("reconstruction_candidates.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    outcome: Mapped[DecisionOutcome] = mapped_column(
        Enum(DecisionOutcome), nullable=False
    )
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    candidate: Mapped["ReconstructionCandidate"] = relationship(
        "ReconstructionCandidate", back_populates="decisions"
    )


# ---------------------------------------------------------------------------
# Phase 0 — Audit log (append-only, every significant system action)
# ---------------------------------------------------------------------------
class AuditLogEntry(Base):
    """
    Append-only log of every significant action. Never updated or deleted.
    Used for provenance trail from output byte → source fragment → decision.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(
        String(128), nullable=False, default="system",
        comment="'system' or investigator identifier"
    )
    entity_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON-serialized detail payload"
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
