"""
Validators Package

Defines the common contracts for format-specific structural validation
of reconstructed files and fragments.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class ValidationStatus(str, Enum):
    VALID = "VALID"
    CORRUPTED = "CORRUPTED"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of structural validation against format specifications."""
    format_id: str
    is_valid: bool
    status: ValidationStatus
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    structural_hash: str | None = None
    markers_found: list[str] = field(default_factory=list)


class FormatValidatorInterface(ABC):
    """Abstract interface for format-specific structural validation."""

    @abstractmethod
    def validate(self, data: bytes) -> ValidationResult:
        """Validate the byte stream against format specifications."""
        raise NotImplementedError("Not implemented — Phase 6: Structural Validation")

    @abstractmethod
    def validate_fragment(self, data: bytes, is_header: bool = False, is_footer: bool = False) -> ValidationResult:
        """Validate an isolated fragment for format-specific structural markers."""
        raise NotImplementedError("Not implemented — Phase 6: Structural Validation")
