"""
Intelligent Fragment Reconstruction — Relationship Engine (Phase 0 Interface)

Scores candidate relationships between fragments (directed edges in the
reconstruction graph). Each edge is scored on the five independent signals
defined in confidence_analyzer.ConfidenceEvidence.

Phase 0: Interface + data model defined. score_edge() raises FeatureNotAvailableError.
Phase 3: Full signal computation implemented.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from analysis.confidence_analyzer import ConfidenceEvidence, stub_evidence
from analysis.fragment_analyzer import FeatureNotAvailableError, FragmentCandidate


# ---------------------------------------------------------------------------
# Edge candidate data model
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class EdgeCandidate:
    """
    A proposed directed relationship: source → target (target follows source).

    Produced by RelationshipEngine.generate_candidates() and scored by
    score_edge(). Only edges that pass the minimum score threshold are
    returned to the ReconstructionEngine.
    """

    source: FragmentCandidate
    target: FragmentCandidate
    evidence: ConfidenceEvidence
    is_rejected: bool = False       # Set to True if investigator rejects


# ---------------------------------------------------------------------------
# Engine class
# ---------------------------------------------------------------------------
class RelationshipEngine:
    """
    Generates and scores directed edges between fragment candidates.

    Usage (Phase 3+)::

        engine = RelationshipEngine(fragments, block_size=4096)
        edges = engine.score_all_pairs()

    Phase 0: Full interface defined. All scoring methods raise FeatureNotAvailableError.
    Phase 3: score_edge() implemented with all five signals.
    """

    #: Edges with composite_score below this threshold are not persisted.
    #: Phase 3 may make this configurable per format.
    MIN_SCORE_THRESHOLD: float = 0.20

    def __init__(
        self,
        fragments: list[FragmentCandidate],
        block_size: int = 4096,
        evidence_path: Optional[object] = None,
    ) -> None:
        """
        Args:
            fragments:      List of FragmentCandidate from FragmentAnalyzer.
            block_size:     Sector size used to compute expected byte offsets.
            evidence_path:  Path to the evidence file (for reading raw bytes
                            at each fragment boundary). Required in Phase 3.
        """
        self.fragments = fragments
        self.block_size = block_size
        self.evidence_path = evidence_path

    def score_edge(
        self,
        source: FragmentCandidate,
        target: FragmentCandidate,
    ) -> EdgeCandidate:
        """
        Score the candidate relationship source → target.

        Returns an EdgeCandidate with a fully-populated ConfidenceEvidence
        (all five signals + composite_score + evidence_status).

        Phase 0 STATUS: STUB — returns EdgeCandidate with stub evidence.
        Phase 3: Reads tail bytes of source and head bytes of target from
                 evidence_path and computes all five signals.

        Raises:
            FeatureNotAvailableError: Phase 0 stub.
        """
        raise FeatureNotAvailableError(
            feature="Fragment edge scoring (5-signal model)",
            coming_in_phase=3,
        )

    def generate_candidates(
        self, max_candidates_per_fragment: int = 5
    ) -> list[tuple[FragmentCandidate, FragmentCandidate]]:
        """
        Generate a list of (source, target) pairs to score.

        Strategy: for each fragment, consider the N nearest fragments by
        byte offset as candidate successors. This limits the O(n²) scoring
        problem to O(n * max_candidates_per_fragment).

        Phase 0 STATUS: STUB — raises FeatureNotAvailableError.
        Phase 3: Implemented with proximity-based candidate selection.
        """
        raise FeatureNotAvailableError(
            feature="Candidate pair generation",
            coming_in_phase=3,
        )

    def score_all_pairs(
        self, max_candidates_per_fragment: int = 5
    ) -> list[EdgeCandidate]:
        """
        Generate and score all candidate edges.

        Returns only edges whose composite_score ≥ MIN_SCORE_THRESHOLD.

        Phase 0 STATUS: STUB — raises FeatureNotAvailableError.
        Phase 3: Calls generate_candidates() then score_edge() for each pair.
        """
        raise FeatureNotAvailableError(
            feature="Full relationship graph scoring",
            coming_in_phase=3,
        )
