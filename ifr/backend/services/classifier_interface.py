"""
Intelligent Fragment Reconstruction — ML Service Interface (Phase 0)

Defines the interface that the reconstruction engine will call for optional
ML-based fragment classification and relationship scoring.

Rule (tech stack): ML is isolated behind this interface. The reconstruction
engine only calls FragmentClassifier and RelationshipScorer — never imports
any ML library directly. This allows the implementation to be:
  - Phase 0–8: NotImplementedError / "not yet available"
  - Phase 9:   A real model (sklearn, pytorch, etc.) behind this interface
  - Production: A separate microservice called over HTTP/gRPC

Phase 0: Full interface with type signatures. All methods raise
         ServiceUnavailableError (distinct from FeatureNotAvailableError,
         because the interface is permanent — only the implementation is absent).
Phase 9: Implementation injected via dependency injection.
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from typing import Optional


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class ServiceUnavailableError(RuntimeError):
    """
    Raised when the ML service is called but no implementation is available.
    Callers must handle this gracefully by falling back to heuristic scoring.
    """

    def __init__(self, service: str, coming_in_phase: int) -> None:
        self.service = service
        self.coming_in_phase = coming_in_phase
        super().__init__(
            f"ML service '{service}' is not available. "
            f"Heuristic fallback will be used. "
            f"Full ML implementation coming in Phase {coming_in_phase}."
        )


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class ClassificationResult:
    """
    Output of FragmentClassifier.classify().

    Attributes:
        format_id:    Predicted file format (from signature_registry), or None.
        confidence:   Model confidence in the prediction (0.0–1.0), or None
                      if the model is unavailable.
        is_available: False when the ML service is not yet implemented.
        fallback_used: True when heuristic (signature scan) was used instead.
    """

    format_id: Optional[str]
    confidence: Optional[float]
    is_available: bool
    fallback_used: bool
    model_version: Optional[str] = None


@dataclasses.dataclass
class RelationshipScore:
    """
    Output of RelationshipScorer.score().

    Attributes:
        score:        ML-predicted relationship likelihood (0.0–1.0), or None.
        is_available: False when the ML service is not yet implemented.
        fallback_used: True when heuristic scoring was used instead.
        model_version: Version string of the model used, if available.
    """

    score: Optional[float]
    is_available: bool
    fallback_used: bool
    model_version: Optional[str] = None


# ---------------------------------------------------------------------------
# Abstract interfaces
# ---------------------------------------------------------------------------
class FragmentClassifier(ABC):
    """
    Abstract interface for ML-based fragment format classification.

    The reconstruction engine calls classify() — it does not know or care
    whether the implementation is a local sklearn model, a remote service,
    or a heuristic fallback.
    """

    @abstractmethod
    def classify(self, fragment_bytes: bytes) -> ClassificationResult:
        """
        Predict the file format of *fragment_bytes*.

        Args:
            fragment_bytes: Raw bytes of the fragment (typically the first
                            1–4 KiB for header-focused models).

        Returns:
            ClassificationResult. If the service is unavailable, returns
            a result with is_available=False and fallback_used=True.
            Must never raise — always returns a result.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the underlying model is loaded and ready."""
        ...


class RelationshipScorer(ABC):
    """
    Abstract interface for ML-based fragment relationship scoring.

    Supplements (does not replace) the heuristic signal computation in
    confidence_analyzer. The ML score becomes an additional input, not
    the sole arbiter.
    """

    @abstractmethod
    def score(
        self,
        source_bytes: bytes,
        target_bytes: bytes,
    ) -> RelationshipScore:
        """
        Predict the likelihood that *target_bytes* follows *source_bytes*
        in the original file.

        Args:
            source_bytes: Tail bytes of the candidate predecessor fragment.
            target_bytes: Head bytes of the candidate successor fragment.

        Returns:
            RelationshipScore. If the service is unavailable, returns
            a result with is_available=False and fallback_used=True.
            Must never raise — always returns a result.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the underlying model is loaded and ready."""
        ...


# ---------------------------------------------------------------------------
# Phase 0 stub implementations
# ---------------------------------------------------------------------------
class StubFragmentClassifier(FragmentClassifier):
    """
    Stub implementation of FragmentClassifier for Phases 0–8.
    Always returns is_available=False with fallback_used=True.
    The reconstruction engine should fall back to signature_registry.
    """

    def classify(self, fragment_bytes: bytes) -> ClassificationResult:
        return ClassificationResult(
            format_id=None,
            confidence=None,
            is_available=False,
            fallback_used=True,
            model_version=None,
        )

    def is_available(self) -> bool:
        return False


class StubRelationshipScorer(RelationshipScorer):
    """
    Stub implementation of RelationshipScorer for Phases 0–8.
    Always returns is_available=False with fallback_used=True.
    The relationship engine should rely exclusively on heuristic signals.
    """

    def score(
        self,
        source_bytes: bytes,
        target_bytes: bytes,
    ) -> RelationshipScore:
        return RelationshipScore(
            score=None,
            is_available=False,
            fallback_used=True,
            model_version=None,
        )

    def is_available(self) -> bool:
        return False
