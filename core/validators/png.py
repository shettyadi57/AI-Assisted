"""
PNG Structural Validator Interface
"""

from __future__ import annotations

from core.validators import FormatValidatorInterface, ValidationResult


class PNGValidator(FormatValidatorInterface):
    """Empty implementation of PNG structural validator raising NotImplementedError."""

    def validate(self, data: bytes) -> ValidationResult:
        """Validate PNG 8-byte magic header, IHDR, chunk sequence, CRC-32, and IEND."""
        raise NotImplementedError("Not implemented — Phase 6: PNG Structural Validation")

    def validate_fragment(self, data: bytes, is_header: bool = False, is_footer: bool = False) -> ValidationResult:
        raise NotImplementedError("Not implemented — Phase 6: PNG Structural Validation")
