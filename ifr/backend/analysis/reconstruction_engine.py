"""
Intelligent Fragment Reconstruction — Reconstruction Engine (Phase 0 Interface)

Assembles accepted fragment edges (from RelationshipEngine) into ordered
reconstruction candidates, assigns them labels, and prepares them for the
investigator accept/reject workflow.

Phase 0: Interface defined. All methods raise FeatureNotAvailableError.
Phase 4: Full implementation.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Optional

from analysis.confidence_analyzer import ConfidenceEvidence
from analysis.fragment_analyzer import FeatureNotAvailableError, FragmentCandidate
from analysis.relationship_engine import EdgeCandidate


# ---------------------------------------------------------------------------
# Assembled candidate data model
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class AssembledCandidate:
    """
    A proposed file reconstruction: an ordered list of fragments connected
    by accepted edges.

    This is the pre-persistence representation. The ReconstructionEngine
    hands this to the API layer which persists it as a ReconstructionCandidate
    + ReconstructionCandidateEdge rows and queues it for investigator review.

    IMPORTANT: is_finalized is always False when first created by the engine.
    The investigator accept/reject step (Phase 5) finalizes it.
    """

    candidate_id: Optional[int]         # None until persisted
    evidence_file_id: int
    ordered_fragments: list[FragmentCandidate]
    ordered_edges: list[EdgeCandidate]
    inferred_format: Optional[str]
    label: str                          # e.g. "Candidate #1 — JPEG (78.3%)"
    overall_evidence: ConfidenceEvidence # Aggregate of all edge evidences
    is_finalized: bool = False          # Always False from the engine
    assembled_sha256: Optional[str] = None  # Hash of assembled bytes; None until exported


# ---------------------------------------------------------------------------
# Reconstruction engine
# ---------------------------------------------------------------------------
class ReconstructionEngine:
    """
    Builds ordered reconstruction candidates from a set of scored edges.

    Phase 0: Interface defined. All methods raise FeatureNotAvailableError.
    Phase 4: Graph traversal + candidate ordering implemented.
    """

    def __init__(
        self,
        scored_edges: list[EdgeCandidate],
        min_fragment_count: int = 2,
    ) -> None:
        """
        Args:
            scored_edges:        All scored EdgeCandidate objects (from RelationshipEngine).
            min_fragment_count:  Candidates with fewer fragments are discarded.
        """
        self.scored_edges = scored_edges
        self.min_fragment_count = min_fragment_count

    def build_candidates(self, evidence_file_id: int) -> list[AssembledCandidate]:
        """
        Build all plausible reconstruction candidates from the edge graph.

        Algorithm (Phase 4):
          1. Build a directed weighted graph from scored_edges.
          2. Find all connected components.
          3. For each component, find the highest-scoring linear path
             (greedy on composite_score, with tie-breaking by offset continuity).
          4. Return each path as an AssembledCandidate.

        Multiple overlapping candidates may be returned — the investigator
        chooses which (if any) to accept (Phase 5).

        Phase 0 STATUS: STUB

        Args:
            evidence_file_id: ID of the evidence source.

        Returns:
            Ordered list of AssembledCandidate, sorted descending by
            overall_evidence.composite_score.

        Raises:
            FeatureNotAvailableError: Phase 0 stub.
        """
        raise FeatureNotAvailableError(
            feature="Reconstruction candidate graph traversal",
            coming_in_phase=4,
        )

    def export_candidate(
        self,
        candidate: AssembledCandidate,
        evidence_path: Path,
        output_dir: Path,
    ) -> Path:
        """
        Assemble the candidate bytes from *evidence_path* and write to *output_dir*.

        The exported file is SHA-256 hashed and the hash is stored in
        candidate.assembled_sha256. The export path follows the pattern:
          <output_dir>/candidate_<id>_<sha256[:8]>.<ext>

        Rule 3: evidence_path is read-only. Writes go only to output_dir.

        Phase 0 STATUS: STUB
        Phase 4: Implemented.

        Args:
            candidate:     The candidate to export.
            evidence_path: Read-only path to the evidence file.
            output_dir:    Writable derived-artifacts directory.

        Returns:
            Path to the exported file.

        Raises:
            FeatureNotAvailableError: Phase 0 stub.
        """
        raise FeatureNotAvailableError(
            feature="Candidate byte assembly and export",
            coming_in_phase=4,
        )
