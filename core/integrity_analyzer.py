"""
Integrity Analyzer Interface

Provides cryptographic verification and hashing contracts for evidence files,
in-memory byte fragments, and carved streams.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import BinaryIO


class HashAlgorithm(str, Enum):
    SHA256 = "sha256"
    MD5 = "md5"


@dataclass(frozen=True)
class IntegrityVerificationResult:
    """Result of an evidence integrity verification operation."""
    target_path: str
    algorithm: HashAlgorithm
    calculated_hash: str
    expected_hash: str
    is_valid: bool
    byte_count: int


class IntegrityAnalyzerInterface(ABC):
    """Abstract interface for evidence hashing and integrity verification."""

    @abstractmethod
    def hash_bytes(self, data: bytes, algorithm: HashAlgorithm = HashAlgorithm.SHA256) -> str:
        """Compute the cryptographic hash of an in-memory byte slice."""
        raise NotImplementedError("Not implemented — Phase 1: Evidence Ingest & Integrity")

    @abstractmethod
    def hash_stream(
        self, stream: BinaryIO, chunk_size: int = 65536, algorithm: HashAlgorithm = HashAlgorithm.SHA256
    ) -> str:
        """Stream an open file-like object and compute its cryptographic hash."""
        raise NotImplementedError("Not implemented — Phase 1: Evidence Ingest & Integrity")

    @abstractmethod
    def hash_file(
        self, filepath: Path | str, chunk_size: int = 65536, algorithm: HashAlgorithm = HashAlgorithm.SHA256
    ) -> str:
        """Compute the cryptographic hash of a file on disk."""
        raise NotImplementedError("Not implemented — Phase 1: Evidence Ingest & Integrity")

    @abstractmethod
    def verify_file(
        self, filepath: Path | str, expected_hash: str, algorithm: HashAlgorithm = HashAlgorithm.SHA256
    ) -> IntegrityVerificationResult:
        """Verify the integrity of a file against an expected hash."""
        raise NotImplementedError("Not implemented — Phase 1: Evidence Ingest & Integrity")


class IntegrityAnalyzer(IntegrityAnalyzerInterface):
    """Empty implementation of the integrity analyzer raising NotImplementedError."""

    def hash_bytes(self, data: bytes, algorithm: HashAlgorithm = HashAlgorithm.SHA256) -> str:
        raise NotImplementedError("Not implemented — Phase 1: Evidence Ingest & Integrity")

    def hash_stream(
        self, stream: BinaryIO, chunk_size: int = 65536, algorithm: HashAlgorithm = HashAlgorithm.SHA256
    ) -> str:
        raise NotImplementedError("Not implemented — Phase 1: Evidence Ingest & Integrity")

    def hash_file(
        self, filepath: Path | str, chunk_size: int = 65536, algorithm: HashAlgorithm = HashAlgorithm.SHA256
    ) -> str:
        raise NotImplementedError("Not implemented — Phase 1: Evidence Ingest & Integrity")

    def verify_file(
        self, filepath: Path | str, expected_hash: str, algorithm: HashAlgorithm = HashAlgorithm.SHA256
    ) -> IntegrityVerificationResult:
        raise NotImplementedError("Not implemented — Phase 1: Evidence Ingest & Integrity")
