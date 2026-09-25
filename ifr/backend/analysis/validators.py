"""
Intelligent Fragment Reconstruction — Validators (Phase 0 Interface)

Structural validation of fragment boundaries and assembled candidates.
"Structural" means format-aware checks: does the internal structure of the
bytes make sense for the claimed format?

This is distinct from signature matching (header_match_score in signature_registry)
and from entropy analysis. A file can have a valid magic header and still fail
structural validation if its internal data structures are inconsistent.

Phase 0: Full interface defined. All methods raise FeatureNotAvailableError.
Phase 2: check_fragment_structure() implemented per format.
Phase 4: validate_candidate_assembly() implemented.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from analysis.fragment_analyzer import FeatureNotAvailableError


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class ValidationResult:
    """
    Result of a structural validation check.

    Attributes:
        passed:      True if the structure is internally consistent.
        score:       0.0 (invalid), 0.5 (partial/uncertain), or 1.0 (valid).
        format_id:   The format that was checked against.
        findings:    Human-readable list of specific checks and their outcomes.
                     Each finding is a (check_name, passed, detail) tuple.
        fatal_errors: List of validation errors that make the fragment
                      definitively CORRUPTED (e.g. truncated required header field).
    """

    passed: bool
    score: float  # 0.0 / 0.5 / 1.0
    format_id: Optional[str]
    findings: list[tuple[str, bool, str]] = dataclasses.field(default_factory=list)
    fatal_errors: list[str] = dataclasses.field(default_factory=list)


# ---------------------------------------------------------------------------
# Validator class
# ---------------------------------------------------------------------------
class StructuralValidator:
    """
    Performs format-aware structural validation of fragments and candidates.

    Phase 0: Interface defined. All methods raise FeatureNotAvailableError.
    Phase 2: check_fragment_structure() implemented for core formats.
    Phase 4: validate_candidate_assembly() implemented.
    """

    #: Formats for which structural validation is implemented (Phase 2+).
    SUPPORTED_FORMATS: frozenset[str] = frozenset()  # populated in Phase 2

    def check_fragment_structure(
        self,
        fragment_bytes: bytes,
        format_id: str,
    ) -> ValidationResult:
        """
        Validate the internal structure of a single fragment's bytes against
        the rules for *format_id*.

        Examples of checks performed (Phase 2):
          - SQLite: page size field consistent with total fragment size
          - PDF: object cross-reference table parseable
          - JPEG: Huffman table markers present and consistent
          - ELF: program header count * header size ≤ fragment size

        Phase 0 STATUS: STUB
        Phase 2: Format-specific checks implemented.

        Args:
            fragment_bytes: Raw bytes of the fragment.
            format_id:      Registered format_id from signature_registry.

        Returns:
            ValidationResult with findings list.

        Raises:
            FeatureNotAvailableError: Phase 0 stub.
        """
        raise FeatureNotAvailableError(
            feature=f"Structural validation for format '{format_id}'",
            coming_in_phase=2,
        )

    def validate_candidate_assembly(
        self,
        ordered_fragment_bytes: list[bytes],
        format_id: str,
    ) -> ValidationResult:
        """
        Validate the structural integrity of an assembled candidate file
        constructed by concatenating *ordered_fragment_bytes* in order.

        This is stronger than per-fragment validation: it checks cross-fragment
        structural invariants (e.g. SQLite B-tree root page points to a page
        that exists in the assembled output).

        Phase 0 STATUS: STUB
        Phase 4: Implemented after ReconstructionEngine is built.

        Args:
            ordered_fragment_bytes: List of raw bytes for each fragment, in order.
            format_id:              Target format for assembly validation.

        Returns:
            ValidationResult with assembly-level findings.

        Raises:
            FeatureNotAvailableError: Phase 0/3 stub.
        """
        raise FeatureNotAvailableError(
            feature="Candidate assembly structural validation",
            coming_in_phase=4,
        )
