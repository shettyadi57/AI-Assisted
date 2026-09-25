"""
ZIP Structural Validator Interface
"""

from __future__ import annotations

from core.validators import FormatValidatorInterface, ValidationResult


class ZIPValidator(FormatValidatorInterface):
    """Empty implementation of ZIP structural validator raising NotImplementedError."""

    def validate(self, data: bytes) -> ValidationResult:
        """Validate ZIP Local File Headers (PK\x03\x04), Central Directory, and EOCD (PK\x05\x06)."""
        raise NotImplementedError("Not implemented — Phase 6: ZIP Structural Validation")

    def validate_fragment(self, data: bytes, is_header: bool = False, is_footer: bool = False) -> ValidationResult:
        raise NotImplementedError("Not implemented — Phase 6: ZIP Structural Validation")
