"""
ML Subsystem Interfaces and Implementations (Phase 9 — Spec Sections 12 & 21)

Exports:
- RelationshipScorerInterface, DeterministicRelationshipScorer, ONNXRelationshipScorer, get_relationship_scorer
- FragmentClassifierInterface, SignatureBasedClassifier, ONNXFragmentClassifier, get_fragment_classifier
- FeatureExtractor, PairFeatureVector, default_feature_extractor
- Config utilities: get_scorer_config, get_classifier_config
"""

from __future__ import annotations

from core.ml.config import get_classifier_config, get_scorer_config
from core.ml.feature_extractor import (
    FeatureExtractor,
    PairFeatureVector,
    compute_ascii_printable_ratio,
    compute_byte_frequency_histogram,
    compute_histogram_l1_distance,
    compute_shannon_entropy,
    default_feature_extractor,
)
from core.ml.fragment_classifier import (
    ClassificationResult,
    FragmentClassifierInterface,
    ONNXFragmentClassifier,
    SignatureBasedClassifier,
    get_fragment_classifier,
)
from core.ml.relationship_scorer import (
    DeterministicRelationshipScorer,
    FeatureVector,
    MLRelationshipScore,
    ONNXRelationshipScorer,
    RelationshipScorer,
    RelationshipScorerInterface,
    ScoredResult,
    get_relationship_scorer,
)

__all__ = [
    # Relationship Scorer
    "RelationshipScorerInterface",
    "DeterministicRelationshipScorer",
    "ONNXRelationshipScorer",
    "RelationshipScorer",
    "ScoredResult",
    "FeatureVector",
    "MLRelationshipScore",
    "get_relationship_scorer",
    # Fragment Classifier
    "FragmentClassifierInterface",
    "SignatureBasedClassifier",
    "ONNXFragmentClassifier",
    "ClassificationResult",
    "get_fragment_classifier",
    # Feature Extractor
    "FeatureExtractor",
    "PairFeatureVector",
    "default_feature_extractor",
    "compute_shannon_entropy",
    "compute_byte_frequency_histogram",
    "compute_histogram_l1_distance",
    "compute_ascii_printable_ratio",
    # Config
    "get_scorer_config",
    "get_classifier_config",
]
