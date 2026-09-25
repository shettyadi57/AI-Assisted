"""
Fragment Analyzer Interface

Extracts byte slices, computes Shannon entropy profiles, detects sector boundaries,
and evaluates forensic status classification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class ForensicStatus(str, Enum):
    """The six strict forensic status states per project rules."""
    CONFIRMED = "CONFIRMED"
    INFERRED = "INFERRED"
    UNCERTAIN = "UNCERTAIN"
    MISSING = "MISSING"
    CORRUPTED = "CORRUPTED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True)
class EntropyProfile:
    """Entropy analysis over a byte fragment."""
    overall_entropy: float
    window_size: int
    distribution: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class FragmentBoundary:
    """Identified boundary between physical or logical fragments."""
    start_offset: int
    end_offset: int
    boundary_type: str
    confidence: float


@dataclass(frozen=True)
class FragmentMetadata:
    """Complete metadata for a single carved file fragment."""
    fragment_id: str
    evidence_id: str
    offset_start: int
    offset_end: int
    size_bytes: int
    sha256_hash: str
    entropy: float
    status: ForensicStatus
    inferred_format: str | None = None
    flags: list[str] = field(default_factory=list)


class FragmentAnalyzerInterface(ABC):
    """Abstract interface for fragment carving and statistical analysis."""

    @abstractmethod
    def analyze_fragment(
        self, raw_bytes: bytes, evidence_id: str, offset_start: int
    ) -> FragmentMetadata:
        """Analyze a carved fragment slice and construct its metadata."""
        raise NotImplementedError("Not implemented — Phase 2: Fragment Identification & Analysis")

    @abstractmethod
    def calculate_entropy(self, raw_bytes: bytes, window_size: int = 256) -> EntropyProfile:
        """Compute Shannon entropy and rolling window entropy profile."""
        raise NotImplementedError("Not implemented — Phase 2: Fragment Identification & Analysis")

    @abstractmethod
    def detect_boundaries(
        self, raw_bytes: bytes, sector_size: int = 512
    ) -> list[FragmentBoundary]:
        """Detect candidate fragmentation boundaries using entropy jumps and zero-padding."""
        raise NotImplementedError("Not implemented — Phase 2: Fragment Identification & Analysis")


class FragmentAnalyzer(FragmentAnalyzerInterface):
    """Empty implementation of the fragment analyzer raising NotImplementedError."""

    def analyze_fragment(
        self, raw_bytes: bytes, evidence_id: str, offset_start: int
    ) -> FragmentMetadata:
        raise NotImplementedError("Not implemented — Phase 2: Fragment Identification & Analysis")

    def calculate_entropy(self, raw_bytes: bytes, window_size: int = 256) -> EntropyProfile:
        raise NotImplementedError("Not implemented — Phase 2: Fragment Identification & Analysis")

    def detect_boundaries(
        self, raw_bytes: bytes, sector_size: int = 512
    ) -> list[FragmentBoundary]:
        raise NotImplementedError("Not implemented — Phase 2: Fragment Identification & Analysis")
