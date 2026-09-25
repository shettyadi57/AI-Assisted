"""
ML Subsystem Configuration (Phase 9 — Spec Section 12 & 21)

Configurable seams for swappable relationship scorers and fragment classifiers.
Currently supports:
- RECONSTRUCTION_SCORER: "deterministic" (active) | "onnx" (interface ready, no trained weights)
- FRAGMENT_CLASSIFIER: "signature" (active) | "onnx" (interface ready, no trained weights)
"""

from __future__ import annotations

import os

RECONSTRUCTION_SCORER: str = os.environ.get("RECONSTRUCTION_SCORER", "deterministic").lower()
FRAGMENT_CLASSIFIER: str = os.environ.get("FRAGMENT_CLASSIFIER", "signature").lower()


def get_scorer_config() -> str:
    """Return active relationship scorer mode."""
    return os.environ.get("RECONSTRUCTION_SCORER", RECONSTRUCTION_SCORER).lower()


def get_classifier_config() -> str:
    """Return active fragment classifier mode."""
    return os.environ.get("FRAGMENT_CLASSIFIER", FRAGMENT_CLASSIFIER).lower()
