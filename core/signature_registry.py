"""
Signature Registry Interface

Maintains file format signatures, magic byte definitions, trailer signatures,
and format detection contracts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class SignatureCategory(str, Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    DATABASE = "database"
    EXECUTABLE = "executable"
    CONTAINER = "container"


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
    sector_aligned: bool = True
    description: str = ""


@dataclass(frozen=True)
class SignatureMatch:
    """Result of matching raw bytes against a signature."""
    format_id: str
    offset: int
    confidence: float
    is_header: bool
    signature: FileSignature


class SignatureRegistryInterface(ABC):
    """Abstract interface for signature lookup and magic byte scanning."""

    @abstractmethod
    def get_signature(self, format_id: str) -> FileSignature | None:
        """Retrieve signature definition for a specific format ID."""
        raise NotImplementedError("Not implemented — Phase 2: Signature Registry")

    @abstractmethod
    def list_supported_formats(self) -> list[str]:
        """List all supported format identifiers."""
        raise NotImplementedError("Not implemented — Phase 2: Signature Registry")

    @abstractmethod
    def scan_for_signatures(self, data: bytes, min_confidence: float = 0.8) -> list[SignatureMatch]:
        """Scan a byte buffer for known header and trailer signatures."""
        raise NotImplementedError("Not implemented — Phase 2: Signature Registry")

    @abstractmethod
    def match_header(self, header_slice: bytes, format_id: str) -> float:
        """Calculate confidence score (0.0 to 1.0) of header bytes matching a format."""
        raise NotImplementedError("Not implemented — Phase 2: Signature Registry")

    @abstractmethod
    def match_trailer(self, trailer_slice: bytes, format_id: str) -> float:
        """Calculate confidence score (0.0 to 1.0) of trailer bytes matching a format."""
        raise NotImplementedError("Not implemented — Phase 2: Signature Registry")


class SignatureRegistry(SignatureRegistryInterface):
    """Empty implementation of the signature registry raising NotImplementedError."""

    def get_signature(self, format_id: str) -> FileSignature | None:
        raise NotImplementedError("Not implemented — Phase 2: Signature Registry")

    def list_supported_formats(self) -> list[str]:
        raise NotImplementedError("Not implemented — Phase 2: Signature Registry")

    def scan_for_signatures(self, data: bytes, min_confidence: float = 0.8) -> list[SignatureMatch]:
        raise NotImplementedError("Not implemented — Phase 2: Signature Registry")

    def match_header(self, header_slice: bytes, format_id: str) -> float:
        raise NotImplementedError("Not implemented — Phase 2: Signature Registry")

    def match_trailer(self, trailer_slice: bytes, format_id: str) -> float:
        raise NotImplementedError("Not implemented — Phase 2: Signature Registry")
