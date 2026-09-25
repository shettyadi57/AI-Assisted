"""
Intelligent Fragment Reconstruction — Signature Registry (Phase 0)

Defines the catalog of known file format signatures (magic bytes) used by
the FragmentAnalyzer and RelationshipEngine to identify fragment boundaries
and assess header-match scores.

This module is a pure Python data/logic module — no FastAPI, no SQLAlchemy.
It is independently importable and unit-testable.

Phase 0: Core signature catalog defined; lookup helpers implemented.
Phase 2: FragmentAnalyzer will call scan_for_signatures().
Phase 3: RelationshipEngine will call header_match_score() per edge.
"""

from __future__ import annotations

import dataclasses
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class FormatSignature:
    """
    Describes how to recognize one file format at a byte boundary.

    Attributes:
        format_id:    Machine-readable identifier (e.g. "jpeg", "sqlite3").
        display_name: Human-readable label shown in the UI.
        header_magic: Bytes that appear at the start of a valid file.
        footer_magic: Bytes that mark the end of a valid file (or None).
        header_offset: Byte offset within the file where header_magic appears.
                       Usually 0; GZIP is 0, ZIP central-dir is not at 0.
        mime_type:     IANA media type string.
        notes:         Any investigator-relevant caveats about this format.
    """

    format_id: str
    display_name: str
    header_magic: bytes
    footer_magic: Optional[bytes]
    header_offset: int
    mime_type: str
    notes: str = ""


# ---------------------------------------------------------------------------
# Canonical signature catalog
# ---------------------------------------------------------------------------
# Rules:
#   - header_magic must be ≥ 4 bytes to limit false positives
#   - footer_magic = None when the format has no reliable terminator
#   - All magic bytes are the raw byte literals — no wildcards yet
#     (wildcard support is planned for Phase 2)
# ---------------------------------------------------------------------------
SIGNATURE_REGISTRY: list[FormatSignature] = [
    # ── Images ────────────────────────────────────────────────────────────
    FormatSignature(
        format_id="jpeg",
        display_name="JPEG / JFIF",
        header_magic=b"\xFF\xD8\xFF",
        footer_magic=b"\xFF\xD9",
        header_offset=0,
        mime_type="image/jpeg",
        notes="SOI marker FF D8; EOI marker FF D9. Huffman tables may be split across fragments.",
    ),
    FormatSignature(
        format_id="png",
        display_name="PNG",
        header_magic=b"\x89PNG\r\n\x1a\n",
        footer_magic=b"IEND\xaeB`\x82",
        header_offset=0,
        mime_type="image/png",
        notes="8-byte signature. IEND chunk must have correct CRC (AE 42 60 82).",
    ),
    FormatSignature(
        format_id="gif87a",
        display_name="GIF87a",
        header_magic=b"GIF87a",
        footer_magic=b"\x00\x3B",
        header_offset=0,
        mime_type="image/gif",
    ),
    FormatSignature(
        format_id="gif89a",
        display_name="GIF89a",
        header_magic=b"GIF89a",
        footer_magic=b"\x00\x3B",
        header_offset=0,
        mime_type="image/gif",
    ),
    # ── Documents ─────────────────────────────────────────────────────────
    FormatSignature(
        format_id="pdf",
        display_name="PDF",
        header_magic=b"%PDF-",
        footer_magic=b"%%EOF",
        header_offset=0,
        mime_type="application/pdf",
        notes="Footer %%EOF may be followed by newline. xref table may be missing in damaged files.",
    ),
    FormatSignature(
        format_id="docx",
        display_name="DOCX / XLSX / PPTX (OOXML)",
        header_magic=b"PK\x03\x04",
        footer_magic=None,
        header_offset=0,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        notes="ZIP-based. Same magic as .zip — disambiguate by internal structure.",
    ),
    # ── Archives ──────────────────────────────────────────────────────────
    FormatSignature(
        format_id="zip",
        display_name="ZIP Archive",
        header_magic=b"PK\x03\x04",
        footer_magic=b"PK\x05\x06",
        header_offset=0,
        mime_type="application/zip",
        notes="Central directory at EOF; fragmentation often severs it.",
    ),
    FormatSignature(
        format_id="gzip",
        display_name="GZIP",
        header_magic=b"\x1F\x8B\x08",
        footer_magic=None,
        header_offset=0,
        mime_type="application/gzip",
        notes="Third byte is always 0x08 (DEFLATE). CRC32 and ISIZE in 8-byte trailer.",
    ),
    FormatSignature(
        format_id="tar",
        display_name="TAR Archive",
        header_magic=b"ustar",
        footer_magic=None,
        header_offset=257,
        mime_type="application/x-tar",
        notes="Magic at offset 257, not 0. Two 512-byte null blocks mark end-of-archive.",
    ),
    # ── Databases ─────────────────────────────────────────────────────────
    FormatSignature(
        format_id="sqlite3",
        display_name="SQLite 3 Database",
        header_magic=b"SQLite format 3\x00",
        footer_magic=None,
        header_offset=0,
        mime_type="application/x-sqlite3",
        notes="16-byte magic. Page size at offset 16 (big-endian u16).",
    ),
    # ── Executables / Binaries ────────────────────────────────────────────
    FormatSignature(
        format_id="elf",
        display_name="ELF Executable (Linux/Unix)",
        header_magic=b"\x7FELF",
        footer_magic=None,
        header_offset=0,
        mime_type="application/x-elf",
        notes="4-byte magic. EI_CLASS at offset 4 (1=32-bit, 2=64-bit).",
    ),
    FormatSignature(
        format_id="pe",
        display_name="PE Executable (Windows)",
        header_magic=b"MZ",
        footer_magic=None,
        header_offset=0,
        mime_type="application/x-msdownload",
        notes="DOS 'MZ' stub; PE signature 'PE\x00\x00' at offset pointed to by bytes 0x3C–0x3F.",
    ),
    # ── Filesystem Metadata ───────────────────────────────────────────────
    FormatSignature(
        format_id="ntfs_mft",
        display_name="NTFS MFT Record",
        header_magic=b"FILE",
        footer_magic=None,
        header_offset=0,
        mime_type="application/octet-stream",
        notes="'FILE' magic marks each 1 KiB MFT record. May also appear as 'BAAD' for damaged records.",
    ),
    FormatSignature(
        format_id="ntfs_baad",
        display_name="NTFS MFT Record (Damaged)",
        header_magic=b"BAAD",
        footer_magic=None,
        header_offset=0,
        mime_type="application/octet-stream",
        notes="Damaged MFT record; fixup array replacement failed.",
    ),
    FormatSignature(
        format_id="bitlocker_fve",
        display_name="BitLocker FVE Metadata",
        header_magic=b"-FVE-FS-",
        footer_magic=None,
        header_offset=3,
        mime_type="application/octet-stream",
        notes="FVE metadata block. VMK and FVEK blocks may be separately fragmented.",
    ),
    # ── Media ─────────────────────────────────────────────────────────────
    FormatSignature(
        format_id="mp4",
        display_name="MPEG-4 / MP4",
        header_magic=b"ftyp",
        footer_magic=None,
        header_offset=4,
        mime_type="video/mp4",
        notes="'ftyp' box at offset 4 (preceded by 4-byte big-endian box size).",
    ),
    FormatSignature(
        format_id="wav",
        display_name="WAV Audio",
        header_magic=b"RIFF",
        footer_magic=None,
        header_offset=0,
        mime_type="audio/wav",
        notes="'WAVE' fourcc at offset 8 disambiguates from other RIFF types.",
    ),
]

# Keyed lookup for O(1) access
_REGISTRY_BY_ID: dict[str, FormatSignature] = {
    sig.format_id: sig for sig in SIGNATURE_REGISTRY
}


# ---------------------------------------------------------------------------
# Public lookup helpers
# ---------------------------------------------------------------------------
def get_signature(format_id: str) -> Optional[FormatSignature]:
    """Return the FormatSignature for *format_id*, or None if unknown."""
    return _REGISTRY_BY_ID.get(format_id)


def scan_for_signatures(data: bytes) -> list[tuple[int, FormatSignature]]:
    """
    Scan *data* for all known file format signatures.

    Returns a list of (offset, signature) tuples sorted by offset.
    An offset is included only if the magic bytes match exactly at
    (offset - signature.header_offset).

    Phase 0: Implemented (this module is independently unit-testable).
    Phase 2: Called by FragmentAnalyzer during fragment identification.
    """
    hits: list[tuple[int, FormatSignature]] = []
    for sig in SIGNATURE_REGISTRY:
        search_start = sig.header_offset
        while True:
            pos = data.find(sig.header_magic, search_start)
            if pos == -1:
                break
            # The true file start is pos - header_offset
            file_start = pos - sig.header_offset
            if file_start >= 0:
                hits.append((file_start, sig))
            search_start = pos + 1
    hits.sort(key=lambda t: t[0])
    return hits


def header_match_score(data: bytes, sig: FormatSignature) -> float:
    """
    Compute the header-match signal score for *data* against *sig*.

    Returns a value in [0.0, 1.0]:
      1.0 — magic bytes present and complete at the expected offset
      0.5 — partial magic match (first half present, second half missing/damaged)
      0.0 — no match

    Phase 0: Implemented (used in Phase 3 by RelationshipEngine).
    """
    magic = sig.header_magic
    offset = sig.header_offset
    actual = data[offset : offset + len(magic)]
    if actual == magic:
        return 1.0
    # Partial match: count matching leading bytes
    matched = sum(1 for a, b in zip(actual, magic) if a == b)
    return matched / len(magic)


def all_format_ids() -> list[str]:
    """Return a sorted list of all registered format IDs."""
    return sorted(_REGISTRY_BY_ID.keys())
