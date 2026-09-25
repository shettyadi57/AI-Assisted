"""
Intelligent Fragment Reconstruction — Fragment Analyzer (Phase 0 Interface)

Responsible for scanning an evidence file and identifying fragment boundaries:
contiguous byte runs that appear to belong to one logical file.

Phase 0: Full interface defined (inputs, outputs, exceptions, docstrings).
         Implementation is a stub — raises FeatureNotAvailableError.
Phase 2: Real implementation replaces the stub body.

This module is independently importable and independently unit-testable.
It does NOT import from FastAPI, SQLAlchemy, or any web layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import dataclasses

from analysis.signature_registry import FormatSignature, scan_for_signatures


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class FeatureNotAvailableError(NotImplementedError):
    """
    Raised when a method is called that has not been implemented yet.
    Callers should catch this and return a FeatureUnavailableResponse
    to the frontend rather than propagating as a 500.
    """

    def __init__(self, feature: str, coming_in_phase: int) -> None:
        self.feature = feature
        self.coming_in_phase = coming_in_phase
        super().__init__(
            f"'{feature}' is not yet available. Coming in Phase {coming_in_phase}."
        )


class EvidenceReadError(IOError):
    """Raised when an evidence file cannot be read (missing, permissions, etc.)."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class FragmentCandidate:
    """
    A candidate fragment identified within an evidence file.
    All fields are derived from raw byte analysis — none are guessed.
    """

    sequence_index: int
    byte_offset: int
    size_bytes: int
    sha256_hex: str
    inferred_format: Optional[str]       # format_id from signature_registry, or None
    matched_signature: Optional[FormatSignature]
    header_bytes_hex: str                # First 16 bytes as hex string
    # Status is UNCERTAIN until validators confirm structural integrity (Phase 2)
    status: str = "UNCERTAIN"


# ---------------------------------------------------------------------------
# Analyzer class
# ---------------------------------------------------------------------------
class FragmentAnalyzer:
    """
    Scans a binary evidence file and identifies fragment boundaries.

    Usage (Phase 2+)::

        analyzer = FragmentAnalyzer(evidence_path, block_size=4096)
        fragments = analyzer.identify_fragments()

    Phase 0: __init__ and identify_fragments() interface defined.
             identify_fragments() raises FeatureNotAvailableError.
    Phase 2: Full implementation using signature_registry.scan_for_signatures()
             and byte-level boundary heuristics.
    """

    #: Default sector/block size used when no explicit size is given.
    DEFAULT_BLOCK_SIZE: int = 4096

    def __init__(
        self,
        evidence_path: Path,
        block_size: int = DEFAULT_BLOCK_SIZE,
        max_scan_bytes: Optional[int] = None,
    ) -> None:
        """
        Args:
            evidence_path: Path to the (read-only) evidence file.
            block_size:    Logical block/sector size in bytes.
            max_scan_bytes: If set, stop scanning after this many bytes
                            (useful for testing on large images).

        Raises:
            EvidenceReadError: if evidence_path does not exist or is unreadable.
        """
        if not evidence_path.exists():
            raise EvidenceReadError(f"Evidence file not found: {evidence_path}")
        if not evidence_path.is_file():
            raise EvidenceReadError(f"Evidence path is not a file: {evidence_path}")

        self.evidence_path = evidence_path
        self.block_size = block_size
        self.max_scan_bytes = max_scan_bytes

    def identify_fragments(self) -> list[FragmentCandidate]:
        """
        Scan the evidence file and return a list of identified fragments,
        ordered by byte offset.

        Each fragment has:
          - an exact byte_offset and size_bytes within the evidence file
          - a SHA-256 hash of its raw bytes
          - an inferred format (from signature_registry), or None
          - first 16 header bytes as hex
          - status = UNCERTAIN (validators will upgrade/downgrade in Phase 2)

        Returns:
            List of FragmentCandidate objects, sorted ascending by byte_offset.

        Raises:
            FeatureNotAvailableError: Phase 0/1 stub.
            EvidenceReadError: if the evidence file becomes unreadable mid-scan.

        Phase 0 STATUS: STUB
        Phase 2: Real implementation.
        """
        raise FeatureNotAvailableError(
            feature="Fragment boundary identification",
            coming_in_phase=2,
        )

    def scan_signatures_only(self) -> list[tuple[int, str]]:
        """
        Quick scan: return (offset, format_id) for every signature hit in the
        evidence file, without computing hashes or sizes.

        This is a fast pre-pass used in Phase 2 to build the scan plan.

        Phase 0: Implemented (wraps signature_registry.scan_for_signatures).
        Phase 2: Called internally by identify_fragments().

        Returns:
            List of (byte_offset, format_id) tuples sorted by offset.

        Raises:
            EvidenceReadError: if the evidence file cannot be read.
        """
        try:
            data = self.evidence_path.read_bytes()
            if self.max_scan_bytes is not None:
                data = data[: self.max_scan_bytes]
        except OSError as exc:
            raise EvidenceReadError(str(exc)) from exc

        hits = scan_for_signatures(data)
        return [(offset, sig.format_id) for offset, sig in hits]
