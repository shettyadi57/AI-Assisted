"""
Signature Registry — Phase 3 LIVE

Extensible, data-driven registry of file format signatures, magic byte
definitions, trailer signatures, internal markers, and structural rules.
Zero dependencies on FastAPI or web frameworks.

Supported formats:
- PDF (Portable Document Format)
- JPEG (Joint Photographic Experts Group)
- PNG (Portable Network Graphics)
- ZIP (ZIP Archive)
- GIF (Graphics Interchange Format)
- SQLite (SQLite Database)
- MP3 (MPEG Audio Layer III with ID3)
- MP4 (MPEG-4 Container / ISO Base Media)
"""

from __future__ import annotations

import struct
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


# ─── Enums & Data Classes ───────────────────────────────────────────────────

class SignatureCategory(str, Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    DATABASE = "database"
    EXECUTABLE = "executable"
    CONTAINER = "container"
    AUDIO = "audio"
    VIDEO = "video"


class FragmentRole(str, Enum):
    FILE_START   = "FILE_START"
    CONTINUATION = "CONTINUATION"
    POSSIBLE_END = "POSSIBLE_END"
    UNKNOWN      = "UNKNOWN"


@dataclass(frozen=True)
class FileSignature:
    """Specification of a known file format signature."""
    format_id: str
    name: str
    extension: str
    category: SignatureCategory
    header_magic: bytes
    header_offset: int = 0
    trailer_magic: bytes | None = None
    trailer_max_distance_from_end: int = 1024
    sector_aligned: bool = True
    description: str = ""
    expected_structural_notes: str = ""
    typical_entropy_range: tuple[float, float] = (0.0, 8.0)
    internal_markers: tuple[bytes, ...] = field(default_factory=tuple)
    confidence_base: float = 0.85


@dataclass(frozen=True)
class SignatureMatch:
    """Result of matching raw bytes against a signature."""
    format_id: str
    offset: int
    confidence: float
    is_header: bool
    signature: FileSignature


@dataclass(frozen=True)
class SignatureAnalysisResult:
    """Complete signature and role assessment for a single fragment."""
    format_id: str | None
    role: FragmentRole
    confidence: float
    matched_magic_hex: str | None = None
    matched_magic_offset: int = 0
    matched_magic_length: int = 0
    trailer_found: bool = False
    trailer_offset: int | None = None
    structural_notes: str = ""
    is_corrupted: bool = False
    corruption_reason: str | None = None


# ─── Built-in Signature Definitions (Data-Driven) ───────────────────────────

BUILTIN_SIGNATURES: list[FileSignature] = [
    FileSignature(
        format_id="pdf",
        name="Portable Document Format",
        extension="pdf",
        category=SignatureCategory.DOCUMENT,
        header_magic=b"%PDF-",
        header_offset=0,
        trailer_magic=b"%%EOF",
        trailer_max_distance_from_end=4096,
        description="Adobe Portable Document Format",
        expected_structural_notes=(
            "PDF document header '%PDF-1.x'. Contains serialized indirect objects (obj/endobj), "
            "compressed FlateDecode stream objects, cross-reference table (xref), and trailer dictionary."
        ),
        typical_entropy_range=(4.0, 7.8),
        internal_markers=(
            b"obj\n", b"obj\r\n", b"endobj", b"stream\n", b"stream\r\n",
            b"endstream", b"xref\n", b"trailer", b"/Root", b"/Catalog", b"/Pages",
        ),
        confidence_base=0.90,
    ),
    FileSignature(
        format_id="jpeg",
        name="JPEG Image",
        extension="jpg",
        category=SignatureCategory.IMAGE,
        header_magic=b"\xFF\xD8\xFF",
        header_offset=0,
        trailer_magic=b"\xFF\xD9",
        trailer_max_distance_from_end=256,
        description="JPEG/JFIF or Exif raster image",
        expected_structural_notes=(
            "JPEG marker stream starting with SOI (0xFFD8). Contains APP0 (JFIF) or APP1 (Exif), "
            "quantization tables (DQT, 0xFFDB), frame header (SOF0, 0xFFC0), Huffman tables (DHT, 0xFFC4), "
            "and entropy-coded scan data (SOS, 0xFFDA) terminated by EOI (0xFFD9)."
        ),
        typical_entropy_range=(7.0, 8.0),
        internal_markers=(
            b"JFIF", b"Exif", b"\xFF\xDB", b"\xFF\xC0", b"\xFF\xC4", b"\xFF\xDA",
        ),
        confidence_base=0.92,
    ),
    FileSignature(
        format_id="png",
        name="Portable Network Graphics",
        extension="png",
        category=SignatureCategory.IMAGE,
        header_magic=b"\x89PNG\r\n\x1a\n",
        header_offset=0,
        trailer_magic=b"IEND\xaeB`\x82",
        trailer_max_distance_from_end=256,
        description="W3C Portable Network Graphics",
        expected_structural_notes=(
            "PNG 8-byte signature 89 50 4E 47 0D 0A 1A 0A followed immediately by mandatory IHDR chunk. "
            "Subsequent chunk sequence of IDAT (zlib compressed pixel rows) and IEND trailer chunk. "
            "Each chunk verified via 32-bit CRC."
        ),
        typical_entropy_range=(6.8, 8.0),
        internal_markers=(
            b"IHDR", b"IDAT", b"PLTE", b"tEXt", b"zTXt", b"pHYs", b"IEND",
        ),
        confidence_base=0.95,
    ),
    FileSignature(
        format_id="zip",
        name="ZIP Archive",
        extension="zip",
        category=SignatureCategory.ARCHIVE,
        header_magic=b"PK\x03\x04",
        header_offset=0,
        trailer_magic=b"PK\x05\x06",
        trailer_max_distance_from_end=1024,
        description="ZIP compressed container archive",
        expected_structural_notes=(
            "ZIP container archive. Series of local file records starting with PK\\x03\\x04, "
            "central directory records starting with PK\\x01\\x02, and terminated by the "
            "End of Central Directory (EOCD) record starting with PK\\x05\\x06."
        ),
        typical_entropy_range=(6.5, 8.0),
        internal_markers=(
            b"PK\x03\x04", b"PK\x01\x02", b"PK\x05\x06",
        ),
        confidence_base=0.90,
    ),
    FileSignature(
        format_id="gif",
        name="Graphics Interchange Format",
        extension="gif",
        category=SignatureCategory.IMAGE,
        header_magic=b"GIF89a",
        header_offset=0,
        trailer_magic=b"\x3B",
        trailer_max_distance_from_end=16,
        description="CompuServe GIF89a / GIF87a image",
        expected_structural_notes=(
            "GIF header 'GIF89a' or 'GIF87a' followed by Logical Screen Descriptor (7 bytes), "
            "optional Global Color Table, and graphic block sequence terminated by 0x3B."
        ),
        typical_entropy_range=(6.0, 7.8),
        internal_markers=(b"GIF87a", b"GIF89a", b"\x21\xF9\x04"),
        confidence_base=0.88,
    ),
    FileSignature(
        format_id="sqlite",
        name="SQLite Database",
        extension="sqlite",
        category=SignatureCategory.DATABASE,
        header_magic=b"SQLite format 3\x00",
        header_offset=0,
        trailer_magic=None,
        description="SQLite 3 database container",
        expected_structural_notes=(
            "100-byte SQLite database header starting with 'SQLite format 3\\0'. Contains page size, "
            "file change counter, freelist page count, and schema cookie."
        ),
        typical_entropy_range=(3.0, 7.5),
        internal_markers=(b"SQLite format 3\x00",),
        confidence_base=0.98,
    ),
    FileSignature(
        format_id="mp3",
        name="MPEG Audio Layer III",
        extension="mp3",
        category=SignatureCategory.AUDIO,
        header_magic=b"ID3",
        header_offset=0,
        trailer_magic=None,
        description="MPEG-1/2 Audio Layer 3 with ID3v2 header",
        expected_structural_notes="ID3v2 metadata header followed by synced MPEG audio frames (0xFFFB / 0xFFFA).",
        typical_entropy_range=(6.5, 8.0),
        internal_markers=(b"ID3", b"\xFF\xFB", b"\xFF\xFA"),
        confidence_base=0.85,
    ),
    FileSignature(
        format_id="mp4",
        name="MPEG-4 Container",
        extension="mp4",
        category=SignatureCategory.VIDEO,
        header_magic=b"ftyp",
        header_offset=4,
        trailer_magic=None,
        description="ISO Base Media File Format / MP4 container",
        expected_structural_notes="MP4 atom box container. Initial 'ftyp' box at byte offset 4 specifies major brand.",
        typical_entropy_range=(7.0, 8.0),
        internal_markers=(b"ftyp", b"moov", b"mdat", b"trak"),
        confidence_base=0.90,
    ),
]


# ─── Abstract Interface ─────────────────────────────────────────────────────

class SignatureRegistryInterface(ABC):
    """Abstract interface for signature lookup and magic byte scanning."""

    @abstractmethod
    def get_signature(self, format_id: str) -> FileSignature | None:
        """Retrieve signature definition for a specific format ID."""
        raise NotImplementedError

    @abstractmethod
    def list_supported_formats(self) -> list[str]:
        """List all supported format identifiers."""
        raise NotImplementedError

    @abstractmethod
    def scan_for_signatures(self, data: bytes, min_confidence: float = 0.8) -> list[SignatureMatch]:
        """Scan a byte buffer for known header and trailer signatures."""
        raise NotImplementedError

    @abstractmethod
    def match_header(self, header_slice: bytes, format_id: str) -> float:
        """Calculate confidence score (0.0 to 1.0) of header bytes matching a format."""
        raise NotImplementedError

    @abstractmethod
    def match_trailer(self, trailer_slice: bytes, format_id: str) -> float:
        """Calculate confidence score (0.0 to 1.0) of trailer bytes matching a format."""
        raise NotImplementedError


# ─── Live Signature Registry Implementation ─────────────────────────────────

class SignatureRegistry(SignatureRegistryInterface):
    """
    Extensible, data-driven file format signature registry.
    Loads built-in signatures on startup, supports dynamic registration of
    new formats without modifying engine code.
    """

    def __init__(self, custom_signatures: Sequence[FileSignature] | None = None) -> None:
        self._signatures: dict[str, FileSignature] = {}
        for sig in BUILTIN_SIGNATURES:
            self._signatures[sig.format_id.lower()] = sig
        if custom_signatures:
            for sig in custom_signatures:
                self._signatures[sig.format_id.lower()] = sig

    def register_signature(self, signature: FileSignature) -> None:
        """Register or override a file format signature."""
        self._signatures[signature.format_id.lower()] = signature

    def get_signature(self, format_id: str) -> FileSignature | None:
        return self._signatures.get(format_id.lower())

    def list_supported_formats(self) -> list[str]:
        return sorted(self._signatures.keys())

    def match_header(self, header_slice: bytes, format_id: str) -> float:
        sig = self.get_signature(format_id)
        if not sig:
            return 0.0
        needed = sig.header_offset + len(sig.header_magic)
        if len(header_slice) < needed:
            return 0.0
        actual = header_slice[sig.header_offset : needed]
        if actual == sig.header_magic:
            return 1.0
        # Partial match score
        matches = sum(1 for a, b in zip(actual, sig.header_magic) if a == b)
        return round(matches / len(sig.header_magic), 3)

    def match_trailer(self, trailer_slice: bytes, format_id: str) -> float:
        sig = self.get_signature(format_id)
        if not sig or not sig.trailer_magic:
            return 0.0
        if sig.trailer_magic in trailer_slice:
            return 1.0
        return 0.0

    def scan_for_signatures(self, data: bytes, min_confidence: float = 0.8) -> list[SignatureMatch]:
        """Scan a byte buffer for all known signatures."""
        matches: list[SignatureMatch] = []
        for sig in self._signatures.values():
            # Check header
            conf = self.match_header(data, sig.format_id)
            if conf >= min_confidence:
                matches.append(SignatureMatch(
                    format_id=sig.format_id,
                    offset=sig.header_offset,
                    confidence=conf,
                    is_header=True,
                    signature=sig,
                ))
            # Check trailer
            if sig.trailer_magic and sig.trailer_magic in data:
                offset = data.rfind(sig.trailer_magic)
                matches.append(SignatureMatch(
                    format_id=sig.format_id,
                    offset=offset,
                    confidence=0.9,
                    is_header=False,
                    signature=sig,
                ))
        return matches

    # ── Structural anomaly & corruption checking ─────────────────────────────

    def check_png_corruption(self, data: bytes) -> tuple[bool, str | None]:
        """
        Check if a block appears to be a corrupted PNG fragment.
        Detects flipped bytes, bad chunk CRCs, or broken chunk headers.
        """
        # All 0xFF or all 0x00 pattern in non-slack context
        if data and data == bytes([0xFF] * len(data)):
            return True, "All bytes flipped to 0xFF (bit-flip corruption detected)"

        # Check for chunk headers like IHDR, IDAT, IEND
        for chunk_tag in (b"IHDR", b"IDAT", b"PLTE", b"IEND"):
            pos = data.find(chunk_tag)
            while pos != -1:
                # If chunk starts at pos, chunk length is 4 bytes preceding
                if pos >= 4:
                    chunk_len = struct.unpack(">I", data[pos - 4 : pos])[0]
                    # If whole chunk is within fragment, verify CRC-32
                    if pos + 4 + chunk_len + 4 <= len(data):
                        expected_crc = struct.unpack(">I", data[pos + 4 + chunk_len : pos + 8 + chunk_len])[0]
                        calc_crc = zlib.crc32(data[pos : pos + 4 + chunk_len]) & 0xFFFFFFFF
                        if calc_crc != expected_crc:
                            return True, f"PNG chunk '{chunk_tag.decode('ascii', errors='ignore')}' CRC mismatch (expected 0x{expected_crc:08X}, got 0x{calc_crc:08X})"
                pos = data.find(chunk_tag, pos + 1)
        return False, None

    # ── Comprehensive Fragment Scanning ──────────────────────────────────────

    def scan_fragment(self, data: bytes, entropy: float | None = None) -> SignatureAnalysisResult:
        """
        Scan a fragment's bytes against all registered signatures.
        Classifies role as FILE_START, CONTINUATION, POSSIBLE_END, or UNKNOWN.
        Computes match confidence based on magic match, trailer presence,
        internal format markers, and entropy consistency.
        """
        if not data:
            return SignatureAnalysisResult(
                format_id=None,
                role=FragmentRole.UNKNOWN,
                confidence=0.0,
                structural_notes="Empty fragment",
            )

        # Check for known corruption patterns first
        png_corrupted, png_reason = self.check_png_corruption(data)
        if png_corrupted:
            return SignatureAnalysisResult(
                format_id="png",
                role=FragmentRole.CONTINUATION,
                confidence=0.35,
                structural_notes=f"Structural anomaly detected: {png_reason}",
                is_corrupted=True,
                corruption_reason=png_reason,
            )

        # 1. First priority: Check exact header magic at expected offset (FILE_START)
        for sig in self._signatures.values():
            needed = sig.header_offset + len(sig.header_magic)
            if len(data) >= needed:
                if data[sig.header_offset : needed] == sig.header_magic:
                    # Found FILE_START!
                    confidence = sig.confidence_base

                    # Bonus for trailer present in same fragment (small file)
                    trailer_found = False
                    trailer_offset = None
                    if sig.trailer_magic and sig.trailer_magic in data:
                        trailer_found = True
                        trailer_offset = data.rfind(sig.trailer_magic)
                        confidence = min(0.99, confidence + 0.08)

                    # Entropy consistency adjustment
                    if entropy is not None:
                        emin, emax = sig.typical_entropy_range
                        if emin <= entropy <= emax:
                            confidence = min(0.99, confidence + 0.04)
                        else:
                            confidence = max(0.50, confidence - 0.10)

                    return SignatureAnalysisResult(
                        format_id=sig.format_id,
                        role=FragmentRole.FILE_START,
                        confidence=round(confidence, 3),
                        matched_magic_hex=sig.header_magic.hex().upper(),
                        matched_magic_offset=sig.header_offset,
                        matched_magic_length=len(sig.header_magic),
                        trailer_found=trailer_found,
                        trailer_offset=trailer_offset,
                        structural_notes=(
                            f"Exact {sig.name} magic header matched at offset {sig.header_offset}. "
                            + sig.expected_structural_notes
                        ),
                    )

        # 2. Second priority: Check trailer / EOF markers (POSSIBLE_END)
        for sig in self._signatures.values():
            if sig.trailer_magic and sig.trailer_magic in data:
                t_offset = data.rfind(sig.trailer_magic)
                # Ensure trailer is near the end or within allowable distance
                dist_from_end = len(data) - (t_offset + len(sig.trailer_magic))
                if dist_from_end <= sig.trailer_max_distance_from_end:
                    confidence = 0.88
                    if entropy is not None:
                        emin, emax = sig.typical_entropy_range
                        if emin <= entropy <= emax:
                            confidence = min(0.98, confidence + 0.05)

                    return SignatureAnalysisResult(
                        format_id=sig.format_id,
                        role=FragmentRole.POSSIBLE_END,
                        confidence=round(confidence, 3),
                        matched_magic_hex=sig.trailer_magic.hex().upper(),
                        matched_magic_offset=t_offset,
                        matched_magic_length=len(sig.trailer_magic),
                        trailer_found=True,
                        trailer_offset=t_offset,
                        structural_notes=(
                            f"{sig.name} EOF/trailer marker '{sig.trailer_magic.decode('ascii', errors='ignore')}' "
                            f"found at offset {t_offset} ({dist_from_end} bytes from fragment boundary)."
                        ),
                    )

        # 3. Third priority: Check format-internal markers (CONTINUATION)
        # Check PDF markers
        pdf_sig = self.get_signature("pdf")
        if pdf_sig:
            found_markers = [m for m in pdf_sig.internal_markers if m in data]
            if len(found_markers) >= 2 or (len(found_markers) >= 1 and any(k in data for k in (b"stream", b"xref", b"trailer", b"obj"))):
                matched = found_markers[0]
                m_offset = data.find(matched)
                return SignatureAnalysisResult(
                    format_id="pdf",
                    role=FragmentRole.CONTINUATION,
                    confidence=0.82,
                    matched_magic_hex=matched.hex().upper(),
                    matched_magic_offset=m_offset,
                    matched_magic_length=len(matched),
                    structural_notes=f"PDF continuation fragment: detected structural tokens ({', '.join(m.decode('ascii', errors='ignore').strip() for m in found_markers[:4])}).",
                )

        # Check PNG markers (IDAT, etc.)
        png_sig = self.get_signature("png")
        if png_sig:
            for marker in (b"IDAT", b"PLTE", b"tEXt", b"pHYs"):
                if marker in data:
                    m_offset = data.find(marker)
                    return SignatureAnalysisResult(
                        format_id="png",
                        role=FragmentRole.CONTINUATION,
                        confidence=0.85,
                        matched_magic_hex=marker.hex().upper(),
                        matched_magic_offset=m_offset,
                        matched_magic_length=len(marker),
                        structural_notes=f"PNG continuation fragment: chunk identifier '{marker.decode('ascii')}' found.",
                    )

        # Check ZIP markers (PK\x01\x02 central directory)
        zip_sig = self.get_signature("zip")
        if zip_sig and b"PK\x01\x02" in data:
            m_offset = data.find(b"PK\x01\x02")
            return SignatureAnalysisResult(
                format_id="zip",
                role=FragmentRole.CONTINUATION,
                confidence=0.86,
                matched_magic_hex=b"PK\x01\x02".hex().upper(),
                matched_magic_offset=m_offset,
                matched_magic_length=4,
                structural_notes="ZIP continuation fragment: central directory header 'PK\\x01\\x02' found.",
            )

        # Check JPEG markers (DQT, DHT, SOS)
        jpeg_sig = self.get_signature("jpeg")
        if jpeg_sig:
            for j_marker in (b"\xFF\xDB", b"\xFF\xC0", b"\xFF\xC4", b"\xFF\xDA"):
                if j_marker in data:
                    m_offset = data.find(j_marker)
                    return SignatureAnalysisResult(
                        format_id="jpeg",
                        role=FragmentRole.CONTINUATION,
                        confidence=0.80,
                        matched_magic_hex=j_marker.hex().upper(),
                        matched_magic_offset=m_offset,
                        matched_magic_length=2,
                        structural_notes=f"JPEG continuation fragment: marker 0x{j_marker.hex().upper()} found.",
                    )

        # Check for zero-filled padding/slack blocks
        if data and data == bytes([0x00] * len(data)):
            return SignatureAnalysisResult(
                format_id=None,
                role=FragmentRole.CONTINUATION,
                confidence=0.20,
                structural_notes="Zero-filled padding / unallocated slack block.",
            )

        # Check for mostly printable ASCII text stream (common in PDF content streams / text)
        ascii_ratio = sum(1 for b in data if 0x20 <= b <= 0x7E or b in (9, 10, 13)) / len(data)
        if ascii_ratio >= 0.95:
            # Check if there are PDF-specific tokens or operators (BT, ET, Tj, Tw, Tf, cm, q, Q, re, rg)
            has_pdf_tokens = any(tok in data for tok in (b"Tj", b"ET", b"BT", b"Tw", b"Td", b"obj", b"stream"))
            return SignatureAnalysisResult(
                format_id="pdf" if has_pdf_tokens else None,
                role=FragmentRole.CONTINUATION,
                confidence=0.75 if has_pdf_tokens else 0.45,
                structural_notes=(
                    f"Printable ASCII text stream ({int(ascii_ratio * 100)}% printable). "
                    + ("Contains PDF text-drawing operators (BT/ET/Tj/Tw)." if has_pdf_tokens else "Plausible document stream continuation.")
                ),
            )

        # 4. Fallback: Unknown
        return SignatureAnalysisResult(
            format_id=None,
            role=FragmentRole.UNKNOWN,
            confidence=0.10,
            structural_notes="No definitive format signature or structural markers detected.",
        )


# Global default registry instance
default_signature_registry = SignatureRegistry()
