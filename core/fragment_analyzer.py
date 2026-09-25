"""
Fragment Analyzer — Phase 2 LIVE

Splits a raw byte blob (or pre-split files) into fixed-size block fragments,
then for each fragment computes:

  - Fragment ID (UUIDv4, deterministic per evidence_id + offset via UUID5)
  - Offset start / end
  - Size in bytes
  - SHA-256 content hash (for duplicate detection)
  - Shannon entropy [0.0 – 8.0]
  - Hex preview (first N bytes as space-separated uppercase hex)
  - Preliminary structural classification (HIGH/LOW entropy, PRINTABLE/BINARY)
    — clearly labelled as PRELIMINARY; real signature detection is Phase 3
  - Duplicate flag (set when sha256_hash matches a previously seen fragment)
  - ForensicStatus: DUPLICATE if exact match, else UNCERTAIN (Phase 3 upgrades this)

This module has ZERO dependencies on FastAPI or any web framework.
"""

from __future__ import annotations

import hashlib
import io
import math
import uuid
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


# ─── Forensic status enum (6 non-negotiable states) ──────────────────────────

class ForensicStatus(str, Enum):
    """The six strict forensic status states per project rules."""
    CONFIRMED  = "CONFIRMED"
    INFERRED   = "INFERRED"
    UNCERTAIN  = "UNCERTAIN"
    MISSING    = "MISSING"
    CORRUPTED  = "CORRUPTED"
    DUPLICATE  = "DUPLICATE"


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EntropyProfile:
    """Entropy analysis over a byte fragment."""
    overall_entropy: float          # Shannon entropy [0.0 – 8.0]
    window_size: int                # Window size used for rolling analysis
    distribution: list[float] = field(default_factory=list)  # per-window entropies


@dataclass(frozen=True)
class FragmentBoundary:
    """Identified boundary between physical or logical fragments."""
    start_offset: int
    end_offset: int
    boundary_type: str
    confidence: float


@dataclass
class FragmentMetadata:
    """
    Complete metadata for a single carved file fragment.

    Classification note: entropy_class and content_class are PRELIMINARY
    Phase 2 heuristics. Real file-type signature detection happens in Phase 3.
    """
    fragment_id: str
    evidence_id: str
    offset_start: int
    offset_end: int
    size_bytes: int
    sha256_hash: str
    entropy: float
    status: ForensicStatus

    # Preliminary structural indicators (Phase 2 — not signature detection)
    entropy_class: str        # "HIGH_ENTROPY" | "LOW_ENTROPY" | "MEDIUM_ENTROPY"
    content_class: str        # "PRINTABLE" | "BINARY" | "MIXED"

    hex_preview: str          # First 32 bytes as "AA BB CC …" uppercase hex
    flags: list[str] = field(default_factory=list)

    # Phase 3+ fields — always None/unknown at this stage
    inferred_format: str | None = None


# ─── Default constants ────────────────────────────────────────────────────────

DEFAULT_BLOCK_SIZE: int = 4096   # bytes — configurable, not hardcoded invisibly
HEX_PREVIEW_BYTES: int = 32      # bytes to include in hex_preview


# ─── Pure-function helpers ────────────────────────────────────────────────────

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _shannon_entropy(data: bytes) -> float:
    """
    Compute Shannon entropy of a byte sequence.
    Result is in bits per byte, range [0.0, 8.0].
    """
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    n = len(data)
    entropy = 0.0
    for c in counts:
        if c:
            p = c / n
            entropy -= p * math.log2(p)
    return round(entropy, 6)


def _rolling_entropy(data: bytes, window: int) -> list[float]:
    """Sliding-window entropy for internal profiling (not exposed to UI)."""
    if len(data) <= window:
        return [_shannon_entropy(data)]
    return [
        _shannon_entropy(data[i : i + window])
        for i in range(0, len(data) - window + 1, window)
    ]


def _entropy_class(entropy: float) -> str:
    """Preliminary entropy classification — Phase 2 heuristic."""
    if entropy >= 7.2:
        return "HIGH_ENTROPY"      # likely compressed / encrypted
    if entropy <= 2.5:
        return "LOW_ENTROPY"       # likely sparse / zeroed
    return "MEDIUM_ENTROPY"


def _content_class(data: bytes) -> str:
    """Preliminary printability classification — Phase 2 heuristic."""
    if not data:
        return "BINARY"
    printable = sum(
        1 for b in data
        if 0x20 <= b <= 0x7E or b in (0x09, 0x0A, 0x0D)  # tab, LF, CR
    )
    ratio = printable / len(data)
    if ratio >= 0.90:
        return "PRINTABLE"
    if ratio >= 0.50:
        return "MIXED"
    return "BINARY"


def _hex_preview(data: bytes, n: int = HEX_PREVIEW_BYTES) -> str:
    """First n bytes as space-separated uppercase hex string."""
    return " ".join(f"{b:02X}" for b in data[:n])


def _fragment_id(evidence_id: str, offset: int) -> str:
    """
    Deterministic fragment ID: UUID5(DNS namespace, '<evidence_id>:<offset>').
    Same evidence + offset always produces the same UUID, enabling idempotent re-runs.
    """
    name = f"{evidence_id}:{offset}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, name))


# ─── Main analyzer ────────────────────────────────────────────────────────────

class FragmentAnalyzer:
    """
    Phase 2 fragment analyzer.

    Usage — from a contiguous blob:
        analyzer = FragmentAnalyzer(block_size=4096)
        fragments = list(analyzer.analyze_blob(raw_bytes, evidence_id="<uuid>"))

    Usage — from pre-split files:
        fragments = list(analyzer.analyze_files([path1, path2, ...], evidence_id="<uuid>"))

    Usage — from a ZIP of fragment files:
        fragments = list(analyzer.analyze_zip(zip_path, evidence_id="<uuid>"))
    """

    def __init__(self, block_size: int = DEFAULT_BLOCK_SIZE) -> None:
        if block_size < 1:
            raise ValueError(f"block_size must be >= 1, got {block_size}")
        self.block_size = block_size

    # ── Core per-fragment analysis ─────────────────────────────────────────

    def analyze_fragment(
        self,
        raw_bytes: bytes,
        evidence_id: str,
        offset_start: int,
        seen_hashes: dict[str, str] | None = None,
    ) -> FragmentMetadata:
        """
        Analyze a single already-sliced fragment.

        Args:
            raw_bytes:    The raw fragment bytes.
            evidence_id:  UUID of the parent evidence record.
            offset_start: Byte offset within the parent evidence blob.
            seen_hashes:  Mutable dict {sha256 -> first fragment_id} for dedup;
                          if None, no duplicate detection is performed.

        Returns:
            FragmentMetadata with all Phase 2 fields populated.
        """
        if not raw_bytes:
            raise ValueError("Cannot analyze an empty fragment")

        size = len(raw_bytes)
        offset_end = offset_start + size
        sha256 = _sha256(raw_bytes)
        entropy = _shannon_entropy(raw_bytes)
        fid = _fragment_id(evidence_id, offset_start)
        flags: list[str] = []

        # Duplicate detection
        if seen_hashes is not None:
            if sha256 in seen_hashes:
                status = ForensicStatus.DUPLICATE
                flags.append(f"DUPLICATE_OF:{seen_hashes[sha256]}")
            else:
                seen_hashes[sha256] = fid
                status = ForensicStatus.UNCERTAIN
        else:
            status = ForensicStatus.UNCERTAIN

        return FragmentMetadata(
            fragment_id=fid,
            evidence_id=evidence_id,
            offset_start=offset_start,
            offset_end=offset_end,
            size_bytes=size,
            sha256_hash=sha256,
            entropy=entropy,
            status=status,
            entropy_class=_entropy_class(entropy),
            content_class=_content_class(raw_bytes),
            hex_preview=_hex_preview(raw_bytes),
            flags=flags,
            inferred_format=None,  # Phase 3
        )

    # ── Blob splitting ─────────────────────────────────────────────────────

    def analyze_blob(
        self,
        blob: bytes,
        evidence_id: str,
        offset_base: int = 0,
    ) -> Iterable[FragmentMetadata]:
        """
        Split a contiguous blob into block_size chunks and analyze each.

        The block_size is set in __init__ and documented clearly.
        The last chunk is kept even if smaller than block_size.

        Args:
            blob:        The raw bytes to split.
            evidence_id: UUID of the parent evidence record.
            offset_base: Starting offset (e.g. if blob is a slice of a larger image).

        Yields:
            FragmentMetadata for each block, in offset order.
        """
        seen: dict[str, str] = {}
        pos = 0
        while pos < len(blob):
            chunk = blob[pos : pos + self.block_size]
            yield self.analyze_fragment(chunk, evidence_id, offset_base + pos, seen)
            pos += self.block_size

    # ── Pre-split files ────────────────────────────────────────────────────

    def analyze_files(
        self,
        paths: list[Path | str],
        evidence_id: str,
    ) -> Iterable[FragmentMetadata]:
        """
        Analyze a list of pre-split fragment files.

        Each file is treated as one fragment at the natural byte offset
        (sum of all preceding file sizes).  Files are processed in the
        order provided.

        Yields:
            FragmentMetadata for each file, in order.
        """
        seen: dict[str, str] = {}
        offset = 0
        for p in paths:
            data = Path(p).read_bytes()
            meta = self.analyze_fragment(data, evidence_id, offset, seen)
            yield meta
            offset += len(data)

    # ── ZIP of fragments ───────────────────────────────────────────────────

    def analyze_zip(
        self,
        zip_path: Path | str,
        evidence_id: str,
    ) -> Iterable[FragmentMetadata]:
        """
        Analyze fragment files packed inside a ZIP archive.

        Files are processed in sorted name order so results are deterministic.

        Yields:
            FragmentMetadata for each member file, in sorted name order.
        """
        seen: dict[str, str] = {}
        offset = 0
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = sorted(zf.namelist())
            for name in names:
                with zf.open(name) as fh:
                    data = fh.read()
                meta = self.analyze_fragment(data, evidence_id, offset, seen)
                yield meta
                offset += len(data)

    # ── Entropy / boundary helpers (kept for interface compatibility) ──────

    def calculate_entropy(self, raw_bytes: bytes, window_size: int = 256) -> EntropyProfile:
        """Compute Shannon entropy and a rolling window profile."""
        overall = _shannon_entropy(raw_bytes)
        windows = _rolling_entropy(raw_bytes, window_size)
        return EntropyProfile(
            overall_entropy=overall,
            window_size=window_size,
            distribution=windows,
        )

    def detect_boundaries(
        self, raw_bytes: bytes, sector_size: int = 512
    ) -> list[FragmentBoundary]:
        """
        Detect candidate boundary transitions using entropy jumps.

        Marks every sector boundary where the entropy delta exceeds a
        threshold as a candidate fragmentation point.  Phase 3 will
        refine this with signature matching.
        """
        ENTROPY_JUMP_THRESHOLD = 2.0
        boundaries: list[FragmentBoundary] = []
        prev_entropy: float | None = None
        pos = 0
        while pos + sector_size <= len(raw_bytes):
            sector = raw_bytes[pos : pos + sector_size]
            ent = _shannon_entropy(sector)
            if prev_entropy is not None:
                delta = abs(ent - prev_entropy)
                if delta >= ENTROPY_JUMP_THRESHOLD:
                    confidence = min(1.0, delta / 8.0)
                    boundaries.append(FragmentBoundary(
                        start_offset=pos,
                        end_offset=pos + sector_size,
                        boundary_type="ENTROPY_JUMP",
                        confidence=round(confidence, 4),
                    ))
            prev_entropy = ent
            pos += sector_size
        return boundaries


# ─── Module-level interface alias (kept for test compatibility) ───────────────

class FragmentAnalyzerInterface:
    """
    Retained for test_core_interfaces.py isinstance checks.
    FragmentAnalyzer no longer raises NotImplementedError — it is live in Phase 2.
    """
    pass
