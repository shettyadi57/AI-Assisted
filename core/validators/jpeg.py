"""
JPEG Structural Validator Interface
"""

from __future__ import annotations

from core.validators import FormatValidatorInterface, ValidationResult


class JPEGValidator(FormatValidatorInterface):
    """Empty implementation of JPEG structural validator raising NotImplementedError."""

    def validate(self, data: bytes) -> ValidationResult:
        """Validate JPEG SOI (0xFFD8), SOF0/SOF2, SOS, entropy stream, and EOI (0xFFD9)."""
        raise NotImplementedError("Not implemented — Phase 6: JPEG Structural Validation")

    def validate_fragment(self, data: bytes, is_header: bool = False, is_footer: bool = False) -> ValidationResult:
        raise NotImplementedError("Not implemented — Phase 6: JPEG Structural Validation")
