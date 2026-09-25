"""
ML Fragment Classifier Architecture (Phase 9 — Spec Sections 12 & 21)

Defines the pluggable seam for fragment format and role classification.
Includes:
- FragmentClassifierInterface (Abstract Base Class)
- SignatureBasedClassifier (Wraps Phase 3 extensible signature registry)
- ONNXFragmentClassifier (Future ML model seam — raises explicit error when invoked)
- Factory get_fragment_classifier() respecting FRAGMENT_CLASSIFIER config
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping

from core.ml.config import get_classifier_config
from core.signature_registry import (
    FragmentRole,
    SignatureAnalysisResult,
    default_signature_registry,
)


@dataclass(frozen=True)
class ClassificationResult:
    """Outcome of classifying a fragment's format and role."""
    inferred_format: str
    role_guess: str
    confidence: float
    matched_magic_hex: str | None = None
    matched_footer_hex: str | None = None
    is_corrupted: bool = False
    classifier_type: str = "signature"
    notes: list[str] = field(default_factory=list)
    raw_metadata: Mapping[str, Any] = field(default_factory=dict)


class FragmentClassifierInterface(ABC):
    """Abstract contract for fragment type and role classification."""

    @abstractmethod
    def classify(
        self,
        fragment_bytes: bytes,
        offset: int = 0,
        context: dict | None = None,
    ) -> ClassificationResult:
        """Classify fragment bytes into format, role, and confidence."""
        raise NotImplementedError

    @abstractmethod
    def is_model_loaded(self) -> bool:
        """Return True if classification model is loaded and ready."""
        raise NotImplementedError


class SignatureBasedClassifier(FragmentClassifierInterface):
    """
    Default Phase 3 signature-registry-backed classifier implementing
    the FragmentClassifierInterface.
    """

    def __init__(self, registry=None) -> None:
        self.registry = registry or default_signature_registry

    def classify(
        self,
        fragment_bytes: bytes,
        offset: int = 0,
        context: dict | None = None,
    ) -> ClassificationResult:
        """
        Classify fragment by checking magic bytes and trailers in the registry.
        """
        match: SignatureAnalysisResult = self.registry.scan_fragment(
            data=fragment_bytes,
        )

        inferred = (match.format_id or "UNKNOWN").upper()
        role_str = match.role.value if hasattr(match.role, "value") else str(match.role)

        notes = [match.structural_notes] if match.structural_notes else []

        return ClassificationResult(
            inferred_format=inferred,
            role_guess=role_str,
            confidence=match.confidence,
            matched_magic_hex=match.matched_magic_hex,
            matched_footer_hex=match.matched_magic_hex if match.trailer_found else None,
            is_corrupted=match.is_corrupted,
            classifier_type="signature",
            notes=notes,
            raw_metadata={
                "offset": offset,
                "length": len(fragment_bytes),
                "corrupted_detail": getattr(match, "corrupted_detail", None),
            },
        )

    def is_model_loaded(self) -> bool:
        """Signature registry is deterministic and memory-resident; always ready."""
        return True


class ONNXFragmentClassifier(FragmentClassifierInterface):
    """
    ONNX Fragment Classifier Seam.
    Per Phase 9 specification: ships the interface only, no fabricated weights.
    Raises clear, honest runtime error when invoked or queried.
    """

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path
        self._raise_unsupported()

    def _raise_unsupported(self) -> None:
        raise RuntimeError(
            "ONNX classification not yet available — Phase 9 ships the interface only, no trained model"
        )

    def classify(
        self,
        fragment_bytes: bytes,
        offset: int = 0,
        context: dict | None = None,
    ) -> ClassificationResult:
        self._raise_unsupported()

    def is_model_loaded(self) -> bool:
        return False


def get_fragment_classifier(classifier_type: str | None = None) -> FragmentClassifierInterface:
    """
    Factory function returning the active FragmentClassifier.
    Defaults to 'signature'.
    """
    mode = (classifier_type or get_classifier_config()).lower()
    if mode == "onnx":
        return ONNXFragmentClassifier()
    return SignatureBasedClassifier()
