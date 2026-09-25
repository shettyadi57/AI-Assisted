"""
PDF Structural Validator Interface
"""

from __future__ import annotations

from core.validators import FormatValidatorInterface, ValidationResult


class PDFValidator(FormatValidatorInterface):
    """Empty implementation of PDF structural validator raising NotImplementedError."""

    def validate(self, data: bytes) -> ValidationResult:
        """Validate PDF header (%PDF-), xref tables, trailers, and %%EOF marker."""
        raise NotImplementedError("Not implemented — Phase 6: PDF Structural Validation")

    def validate_fragment(self, data: bytes, is_header: bool = False, is_footer: bool = False) -> ValidationResult:
        raise NotImplementedError("Not implemented — Phase 6: PDF Structural Validation")
