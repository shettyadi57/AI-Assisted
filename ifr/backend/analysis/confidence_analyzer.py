"""
Intelligent Fragment Reconstruction — Confidence Analyzer (Phase 0)

Computes the composite confidence score from the five independent evidence
signals. This module is the sole authority on how signals are weighted and
combined into a composite score and an EvidenceStatus label.

Rules enforced here:
  Rule 2: composite_score is always accompanied by its backing evidence object.
  Rule 4: Status labels (CONFIRMED / INFERRED / UNCERTAIN / CORRUPTED) are
          derived mechanically from signal values — never hand-waved.

Phase 0: Data structures + composite_score formula defined.
         compute_edge_confidence() is stubbed (returns UNCERTAIN + None score)
         because it needs real fragment bytes, which Phase 2/3 provides.
Phase 3: Full implementation wired to FragmentEdge rows in the database.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Optional


# ---------------------------------------------------------------------------
# Evidence object (mirrors schemas.ConfidenceEvidence)
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class ConfidenceEvidence:
    """
    All five signals + derived composite. Returned by every score function.

    Never instantiate with only composite_score — always provide the
    individual signals or leave them None with a not_computed_reason.
    """

    sig_header_match: Optional[float] = None        # 0.0–1.0
    sig_offset_continuity: Optional[float] = None   # 0.0–1.0
    sig_structural_validity: Optional[float] = None # 0.0 / 0.5 / 1.0
    sig_entropy_profile: Optional[float] = None     # 0.0–1.0
    sig_contradiction_count: int = 0

    # Derived — computed by compute_composite(), never set externally
    composite_score: Optional[float] = None
    evidence_status: str = "UNCERTAIN"
    not_computed_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Signal weights (must sum to 1.0)
# Phase 3 may tune these based on format-specific knowledge.
# ---------------------------------------------------------------------------
_WEIGHTS: dict[str, float] = {
    "sig_header_match": 0.35,
    "sig_offset_continuity": 0.25,
    "sig_structural_validity": 0.25,
    "sig_entropy_profile": 0.15,
}
assert math.isclose(sum(_WEIGHTS.values()), 1.0), "Signal weights must sum to 1.0"


# ---------------------------------------------------------------------------
# Status thresholds
# ---------------------------------------------------------------------------
# CONFIRMED:  composite ≥ 0.85 AND contradiction_count == 0
# INFERRED:   composite ≥ 0.55 AND contradiction_count ≤ 1
# UNCERTAIN:  composite ≥ 0.25 OR contradiction_count > 1
# CORRUPTED:  composite < 0.25 (severe damage / unreadable)
_THRESHOLD_CONFIRMED = 0.85
_THRESHOLD_INFERRED = 0.55
_THRESHOLD_UNCERTAIN = 0.25


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def compute_composite(evidence: ConfidenceEvidence) -> ConfidenceEvidence:
    """
    Compute composite_score and evidence_status from the five signals.

    Only signals that are not None contribute to the weighted average.
    The weight of missing signals is redistributed proportionally among
    present signals so the composite always lies in [0.0, 1.0].

    Contradiction penalty: each contradiction reduces composite by 0.10,
    clamped to 0.0 minimum.

    Args:
        evidence: ConfidenceEvidence with at least one signal set.

    Returns:
        The same evidence object with composite_score and evidence_status
        populated. Mutates in place and also returns self for chaining.
    """
    signal_map = {
        "sig_header_match": evidence.sig_header_match,
        "sig_offset_continuity": evidence.sig_offset_continuity,
        "sig_structural_validity": evidence.sig_structural_validity,
        "sig_entropy_profile": evidence.sig_entropy_profile,
    }

    present = {k: v for k, v in signal_map.items() if v is not None}

    if not present:
        evidence.composite_score = None
        evidence.evidence_status = "UNCERTAIN"
        evidence.not_computed_reason = evidence.not_computed_reason or "No signals computed yet"
        return evidence

    # Redistribute weights among present signals
    total_weight = sum(_WEIGHTS[k] for k in present)
    weighted_sum = sum(
        v * (_WEIGHTS[k] / total_weight) for k, v in present.items()
    )

    # Contradiction penalty
    penalty = 0.10 * evidence.sig_contradiction_count
    composite = max(0.0, weighted_sum - penalty)

    evidence.composite_score = round(composite, 4)

    # Assign status
    contradictions = evidence.sig_contradiction_count
    if composite >= _THRESHOLD_CONFIRMED and contradictions == 0:
        evidence.evidence_status = "CONFIRMED"
    elif composite >= _THRESHOLD_INFERRED and contradictions <= 1:
        evidence.evidence_status = "INFERRED"
    elif composite >= _THRESHOLD_UNCERTAIN:
        evidence.evidence_status = "UNCERTAIN"
    else:
        evidence.evidence_status = "CORRUPTED"

    return evidence


def stub_evidence(reason: str, coming_in_phase: int) -> ConfidenceEvidence:
    """
    Return a clearly-labeled stub ConfidenceEvidence for features not yet
    implemented. Used by Phase 0 stubs to comply with Rule 5.

    Args:
        reason:           Human-readable explanation.
        coming_in_phase:  Phase number when real computation will be wired.

    Returns:
        ConfidenceEvidence with all signals None, status UNCERTAIN.
    """
    return ConfidenceEvidence(
        not_computed_reason=f"Coming in Phase {coming_in_phase}: {reason}",
        evidence_status="UNCERTAIN",
    )


def compute_edge_confidence(
    source_bytes: bytes,
    target_bytes: bytes,
    expected_format_id: Optional[str] = None,
) -> ConfidenceEvidence:
    """
    Compute the confidence evidence for a proposed source→target fragment edge.

    Phase 0 STATUS: STUB — returns UNCERTAIN with all signals None.
    Phase 3 will replace this body with real signal computation.

    Args:
        source_bytes:        Raw bytes of the source fragment (tail region used).
        target_bytes:        Raw bytes of the target fragment (head region used).
        expected_format_id:  If known, allows format-aware structural checks.

    Returns:
        ConfidenceEvidence with all signals populated (Phase 3+).
        Currently returns stub_evidence() with not_computed_reason set.
    """
    # ── Phase 3 implementation goes here ──────────────────────────────────
    # When implemented, this function should:
    #   1. Call signature_registry.header_match_score() for sig_header_match
    #   2. Compute byte-offset delta for sig_offset_continuity
    #   3. Call validators.check_structural_boundary() for sig_structural_validity
    #   4. Compute Shannon entropy of tail/head windows for sig_entropy_profile
    #   5. Count detected contradictions (e.g. entropy spike + valid structure)
    #   6. Call compute_composite() to derive composite_score + status
    # ──────────────────────────────────────────────────────────────────────
    return stub_evidence(
        reason="RelationshipEngine byte-level signal computation",
        coming_in_phase=3,
    )
