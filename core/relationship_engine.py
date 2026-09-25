"""
Relationship Engine Interface

Evaluates multi-factor candidate relationship scores between carved fragments
to construct a directed, scored fragment graph.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from core.fragment_analyzer import FragmentMetadata


class InvestigatorDecision(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class EdgeEvidenceFactors:
    """Decomposed independent signals contributing to relationship confidence."""
    signature_match: float          # [0.0 - 1.0] Format marker consistency
    offset_continuity: float        # [0.0 - 1.0] Physical/logical offset alignment
    structural_validity: float      # [0.0 - 1.0] Format-internal parser validity
    entropy_compatibility: float    # [0.0 - 1.0] Transition smoothness across boundary
    contradiction_count: int = 0    # Number of conflicting markers detected


@dataclass(frozen=True)
class FragmentRelationship:
    """A scored directed edge between two fragments in the candidate graph."""
    source_fragment_id: str
    target_fragment_id: str
    composite_confidence: float
    factors: EdgeEvidenceFactors
    decision: InvestigatorDecision = InvestigatorDecision.PENDING
    decision_rationale: str = ""
    flags: list[str] = field(default_factory=list)


class RelationshipEngineInterface(ABC):
    """Abstract interface for scoring candidate relationships between fragments."""

    @abstractmethod
    def evaluate_relationship(
        self,
        source_meta: FragmentMetadata,
        target_meta: FragmentMetadata,
        source_bytes: bytes,
        target_bytes: bytes,
        target_format: str,
    ) -> FragmentRelationship:
        """Score candidate relationship between two fragments across all 5 signals."""
        raise NotImplementedError("Not implemented — Phase 3: Relationship Scoring & Linking")

    @abstractmethod
    def compute_composite_score(self, factors: EdgeEvidenceFactors) -> float:
        """Compute the weighted composite confidence score from decomposed factors."""
        raise NotImplementedError("Not implemented — Phase 3: Relationship Scoring & Linking")

    @abstractmethod
    def build_candidate_graph(
        self, fragments: Sequence[FragmentMetadata], target_format: str
    ) -> list[FragmentRelationship]:
        """Construct candidate graph edges for a set of fragments."""
        raise NotImplementedError("Not implemented — Phase 3: Relationship Scoring & Linking")


class RelationshipEngine(RelationshipEngineInterface):
    """Empty implementation of the relationship engine raising NotImplementedError."""

    def evaluate_relationship(
        self,
        source_meta: FragmentMetadata,
        target_meta: FragmentMetadata,
        source_bytes: bytes,
        target_bytes: bytes,
        target_format: str,
    ) -> FragmentRelationship:
        raise NotImplementedError("Not implemented — Phase 3: Relationship Scoring & Linking")

    def compute_composite_score(self, factors: EdgeEvidenceFactors) -> float:
        raise NotImplementedError("Not implemented — Phase 3: Relationship Scoring & Linking")

    def build_candidate_graph(
        self, fragments: Sequence[FragmentMetadata], target_format: str
    ) -> list[FragmentRelationship]:
        raise NotImplementedError("Not implemented — Phase 3: Relationship Scoring & Linking")
