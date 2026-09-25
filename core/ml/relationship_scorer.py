"""
ML Relationship Scorer Architecture (Phase 9 — Spec Sections 12 & 21)

Defines the pluggable seam for relationship scoring between fragments.
Includes:
- RelationshipScorerInterface (Abstract Base Class)
- DeterministicRelationshipScorer (Wraps Phase 4 heuristic multi-factor scoring)
- ONNXRelationshipScorer (Future ML model seam — raises explicit error when invoked)
- Factory get_relationship_scorer() respecting RECONSTRUCTION_SCORER config
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from core.ml.config import get_scorer_config
from core.ml.feature_extractor import (
    FeatureExtractor,
    PairFeatureVector,
    default_feature_extractor,
)


@dataclass(frozen=True)
class ScoredResult:
    """Outcome of scoring an edge between two fragments."""
    score: float
    confidence_breakdown: Mapping[str, float]
    contradiction_count: int
    evidence_strings: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    scorer_type: str = "deterministic"
    feature_vector: list[float] = field(default_factory=list)


# Backward-compatible dataclasses for Phase 0 tests
@dataclass(frozen=True)
class FeatureVector:
    """Legacy feature vector representation."""
    source_entropy: float
    target_entropy: float
    entropy_delta: float
    byte_transition_distance: float
    header_compatibility_score: float
    raw_feature_map: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class MLRelationshipScore:
    """Legacy ML scoring prediction result."""
    score: float
    model_version: str
    feature_importances: Mapping[str, float] = field(default_factory=dict)
    inference_time_ms: float = 0.0


# ─── Abstract Base Interface ──────────────────────────────────────────────────

class RelationshipScorerInterface(ABC):
    """Abstract contract for fragment relationship scoring."""

    @abstractmethod
    def score(
        self,
        fragment_a: Any,
        fragment_b: Any,
        source_bytes: bytes = b"",
        target_bytes: bytes = b"",
        context: dict | None = None,
    ) -> ScoredResult:
        """Score the directional edge fragment_a -> fragment_b."""
        raise NotImplementedError

    @abstractmethod
    def extract_features(
        self,
        fragment_a: Any,
        fragment_b: Any,
        source_bytes: bytes = b"",
        target_bytes: bytes = b"",
    ) -> PairFeatureVector:
        """Extract multi-modal numeric feature vector."""
        raise NotImplementedError

    @abstractmethod
    def is_model_loaded(self) -> bool:
        """Return True if model weights are loaded and ready."""
        raise NotImplementedError


# ─── Deterministic Scorer Implementation ──────────────────────────────────────

class DeterministicRelationshipScorer(RelationshipScorerInterface):
    """
    Wraps Phase 4's multi-factor heuristic scoring engine as the default
    implementation of RelationshipScorerInterface.
    """

    def __init__(self, feature_extractor: FeatureExtractor | None = None) -> None:
        self.feature_extractor = feature_extractor or default_feature_extractor

    def extract_features(
        self,
        fragment_a: Any,
        fragment_b: Any,
        source_bytes: bytes = b"",
        target_bytes: bytes = b"",
    ) -> PairFeatureVector:
        """Extract numeric features suitable for future ML scoring models."""
        return self.feature_extractor.extract_pair_features(
            source_meta=fragment_a,
            target_meta=fragment_b,
            source_bytes=source_bytes,
            target_bytes=target_bytes,
        )

    def score(
        self,
        fragment_a: Any,
        fragment_b: Any,
        source_bytes: bytes = b"",
        target_bytes: bytes = b"",
        context: dict | None = None,
    ) -> ScoredResult:
        """
        Execute deterministic 5-signal heuristic scoring and extract features.
        """
        from core.fragment_analyzer import FragmentMetadata, ForensicStatus
        from core.relationship_engine import default_relationship_engine
        from core.signature_registry import FragmentRole
        import hashlib

        def _to_meta(item: Any, default_bytes: bytes) -> FragmentMetadata:
            if isinstance(item, FragmentMetadata):
                return item
            if isinstance(item, dict):
                fid = item.get("fragment_id") or item.get("id") or "frag_unknown"
                fmt = item.get("inferred_format", "UNKNOWN")
                role_val = item.get("role_guess", "UNKNOWN")
                start = item.get("offset_start", 0)
                sz = item.get("size_bytes", len(default_bytes))
                hex_p = default_bytes[:32].hex(" ").upper() if default_bytes else "00"
                ent = float(item.get("entropy", 0.0) or 0.0)
                return FragmentMetadata(
                    fragment_id=fid,
                    evidence_id=item.get("evidence_id", "evidence_unknown"),
                    offset_start=start,
                    offset_end=item.get("offset_end", start + sz),
                    size_bytes=sz,
                    sha256_hash=item.get("sha256_hash", hashlib.sha256(default_bytes).hexdigest()),
                    entropy=ent,
                    status=ForensicStatus.CONFIRMED,
                    entropy_class="HIGH_ENTROPY" if ent > 7.0 else "LOW_ENTROPY" if ent < 3.0 else "MEDIUM_ENTROPY",
                    content_class="BINARY",
                    hex_preview=hex_p,
                    flags=item.get("flags", []),
                    inferred_format=fmt,
                    role_guess=role_val,
                    signature_confidence=float(item.get("signature_confidence", 0.0) or 0.0),
                )
            return item

        meta_a = _to_meta(fragment_a, source_bytes)
        meta_b = _to_meta(fragment_b, target_bytes)

        target_format = (context or {}).get("target_format")
        edge = default_relationship_engine.evaluate_relationship(
            source_meta=meta_a,
            target_meta=meta_b,
            source_bytes=source_bytes,
            target_bytes=target_bytes,
            target_format=target_format,
        )

        features = self.extract_features(meta_a, meta_b, source_bytes, target_bytes)

        breakdown = {
            "signature_match": edge.factors.signature_match,
            "structural_validity": edge.factors.structural_validity,
            "offset_continuity": edge.factors.offset_continuity,
            "entropy_compatibility": edge.factors.entropy_compatibility,
        }

        return ScoredResult(
            score=edge.composite_confidence,
            confidence_breakdown=breakdown,
            contradiction_count=edge.factors.contradiction_count,
            evidence_strings=list(edge.evidence_strings),
            flags=list(edge.flags),
            scorer_type="deterministic",
            feature_vector=features.as_vector(),
        )

    def is_model_loaded(self) -> bool:
        """Deterministic scorer has no neural weights to load; always ready."""
        return True


# ─── ONNX Seam Implementation (Spec Section 12 & 21) ──────────────────────────

class ONNXRelationshipScorer(RelationshipScorerInterface):
    """
    ONNX ML Model Seam.
    Per Phase 9 specification: ships the interface only, no fabricated weights.
    Raises clear, honest runtime error when invoked or queried.
    """

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path
        self._raise_unsupported()

    def _raise_unsupported(self) -> None:
        raise RuntimeError(
            "ONNX scoring not yet available — Phase 9 ships the interface only, no trained model"
        )

    def score(
        self,
        fragment_a: Any,
        fragment_b: Any,
        source_bytes: bytes = b"",
        target_bytes: bytes = b"",
        context: dict | None = None,
    ) -> ScoredResult:
        self._raise_unsupported()

    def extract_features(
        self,
        fragment_a: Any,
        fragment_b: Any,
        source_bytes: bytes = b"",
        target_bytes: bytes = b"",
    ) -> PairFeatureVector:
        self._raise_unsupported()

    def is_model_loaded(self) -> bool:
        return False


# Legacy alias for backward compatibility with Phase 0 tests
class RelationshipScorer(RelationshipScorerInterface):
    """Legacy alias raising NotImplementedError for uninitialized scoring."""

    def score(
        self,
        fragment_a: Any,
        fragment_b: Any,
        source_bytes: bytes = b"",
        target_bytes: bytes = b"",
        context: dict | None = None,
    ) -> ScoredResult:
        raise NotImplementedError("Not implemented — use DeterministicRelationshipScorer")

    def extract_features(
        self,
        fragment_a: Any,
        fragment_b: Any,
        source_bytes: bytes = b"",
        target_bytes: bytes = b"",
    ) -> PairFeatureVector:
        raise NotImplementedError("Not implemented — use DeterministicRelationshipScorer")

    def predict_score(self, features: Any) -> MLRelationshipScore:
        raise NotImplementedError("Not implemented — Phase 9 interface")

    def batch_predict(self, feature_batch: Sequence[Any]) -> list[MLRelationshipScore]:
        raise NotImplementedError("Not implemented — Phase 9 interface")

    def is_model_loaded(self) -> bool:
        raise NotImplementedError("Not implemented — Phase 9: ML Integration")


def get_relationship_scorer(scorer_type: str | None = None) -> RelationshipScorerInterface:
    """
    Factory function returning the active RelationshipScorer.
    Defaults to 'deterministic'.
    """
    mode = (scorer_type or get_scorer_config()).lower()
    if mode == "onnx":
        return ONNXRelationshipScorer()
    return DeterministicRelationshipScorer()
