"""
ML Subsystem Interfaces

Defines the abstract contracts for machine-learning-assisted relationship
scoring and fragment classification.
"""

from __future__ import annotations

from core.ml.relationship_scorer import (
    FeatureVector,
    MLRelationshipScore,
    RelationshipScorer,
    RelationshipScorerInterface,
)

__all__ = [
    "FeatureVector",
    "MLRelationshipScore",
    "RelationshipScorerInterface",
    "RelationshipScorer",
]
