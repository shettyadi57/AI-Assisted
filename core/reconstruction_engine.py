"""
Reconstruction Engine Interface

Traverses candidate relationship graphs, builds ordered fragment chains,
and generates bit-level provenance byte-maps for assembled files.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from core.relationship_engine import FragmentRelationship


@dataclass(frozen=True)
class ProvenanceByteSpan:
    """Provenance tracking for a span of bytes in the reconstructed output."""
    output_offset: int
    length_bytes: int
    source_fragment_id: str
    fragment_offset: int
    edge_confidence: float
    investigator_accepted: bool


@dataclass(frozen=True)
class ReconstructionCandidate:
    """An assembled file candidate representing an ordered sequence of fragments."""
    candidate_id: str
    target_format: str
    ordered_fragment_ids: list[str]
    total_size_bytes: int
    composite_confidence: float
    provenance_map: list[ProvenanceByteSpan] = field(default_factory=list)
    is_finalized: bool = False
    reconstructed_sha256: str | None = None


class ReconstructionEngineInterface(ABC):
    """Abstract interface for fragment chain assembly and provenance mapping."""

    @abstractmethod
    def assemble_candidate(
        self,
        candidate_id: str,
        target_format: str,
        edges: Sequence[FragmentRelationship],
        root_fragment_id: str,
    ) -> ReconstructionCandidate:
        """Find the optimal path in the relationship graph to assemble a candidate."""
        raise NotImplementedError("Not implemented — Phase 4: Candidate Reconstruction")

    @abstractmethod
    def synthesize_file(
        self,
        candidate: ReconstructionCandidate,
        fragment_store: Mapping[str, bytes],
    ) -> bytes:
        """Concatenate fragments according to the ordered candidate sequence."""
        raise NotImplementedError("Not implemented — Phase 4: Candidate Reconstruction")

    @abstractmethod
    def generate_provenance_map(
        self,
        candidate: ReconstructionCandidate,
        fragment_lengths: Mapping[str, int],
        edges: Sequence[FragmentRelationship],
    ) -> list[ProvenanceByteSpan]:
        """Generate a complete output-byte to source-fragment provenance map."""
        raise NotImplementedError("Not implemented — Phase 4: Candidate Reconstruction")


class ReconstructionEngine(ReconstructionEngineInterface):
    """Empty implementation of the reconstruction engine raising NotImplementedError."""

    def assemble_candidate(
        self,
        candidate_id: str,
        target_format: str,
        edges: Sequence[FragmentRelationship],
        root_fragment_id: str,
    ) -> ReconstructionCandidate:
        raise NotImplementedError("Not implemented — Phase 4: Candidate Reconstruction")

    def synthesize_file(
        self,
        candidate: ReconstructionCandidate,
        fragment_store: Mapping[str, bytes],
    ) -> bytes:
        raise NotImplementedError("Not implemented — Phase 4: Candidate Reconstruction")

    def generate_provenance_map(
        self,
        candidate: ReconstructionCandidate,
        fragment_lengths: Mapping[str, int],
        edges: Sequence[FragmentRelationship],
    ) -> list[ProvenanceByteSpan]:
        raise NotImplementedError("Not implemented — Phase 4: Candidate Reconstruction")
