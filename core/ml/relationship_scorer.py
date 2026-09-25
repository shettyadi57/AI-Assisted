"""
ML Relationship Scorer Interface (Spec Sections 12 & 21)

Abstract Base Class defining the contract for machine-learning-assisted
edge scoring in the candidate graph.

Phase 0–8: Abstract interface only.
Phase 9: Real model implementation (classifier / scorer).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Mapping, Sequence


@dataclass(frozen=True)
class FeatureVector:
    """Extracted numerical and categorical features for edge prediction."""
    source_entropy: float
    target_entropy: float
    entropy_delta: float
    byte_transition_distance: float
    header_compatibility_score: float
    raw_feature_map: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class MLRelationshipScore:
    """Prediction output from ML relationship scorer."""
    score: float
    model_version: str
    feature_importances: Mapping[str, float] = field(default_factory=dict)
    inference_time_ms: float = 0.0


class RelationshipScorerInterface(ABC):
    """Abstract Base Class for ML-assisted fragment relationship scoring."""

    @abstractmethod
    def extract_features(
        self, source_bytes: bytes, target_bytes: bytes, context_format: str
    ) -> FeatureVector:
        """Extract multi-modal feature vector from adjacent byte slices."""
        raise NotImplementedError("Not implemented — Phase 9: ML Integration")

    @abstractmethod
    def predict_score(self, features: FeatureVector) -> MLRelationshipScore:
        """Predict edge likelihood score using trained scoring model."""
        raise NotImplementedError("Not implemented — Phase 9: ML Integration")

    @abstractmethod
    def batch_predict(
        self, feature_batch: Sequence[FeatureVector]
    ) -> list[MLRelationshipScore]:
        """Perform batch inference for high-throughput candidate evaluation."""
        raise NotImplementedError("Not implemented — Phase 9: ML Integration")

    @abstractmethod
    def is_model_loaded(self) -> bool:
        """Return True if model weights are initialized and ready for inference."""
        raise NotImplementedError("Not implemented — Phase 9: ML Integration")


class RelationshipScorer(RelationshipScorerInterface):
    """Empty implementation of ML Relationship Scorer raising NotImplementedError."""

    def extract_features(
        self, source_bytes: bytes, target_bytes: bytes, context_format: str
    ) -> FeatureVector:
        raise NotImplementedError("Not implemented — Phase 9: ML Integration")

    def predict_score(self, features: FeatureVector) -> MLRelationshipScore:
        raise NotImplementedError("Not implemented — Phase 9: ML Integration")

    def batch_predict(
        self, feature_batch: Sequence[FeatureVector]
    ) -> list[MLRelationshipScore]:
        raise NotImplementedError("Not implemented — Phase 9: ML Integration")

    def is_model_loaded(self) -> bool:
        raise NotImplementedError("Not implemented — Phase 9: ML Integration")
