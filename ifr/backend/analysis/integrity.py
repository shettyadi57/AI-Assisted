"""
Intelligent Fragment Reconstruction — Integrity Module (Phase 0)

Responsible for hashing evidence and derived artifacts.
This is the ONLY analysis module fully implemented in Phase 0
because it has zero external dependencies and is required by every later phase.

Rule 3: Evidence is read-only; this module hashes evidence on ingest
and hashes every exported artifact.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HASH_ALGORITHM = "sha256"
CHUNK_SIZE = 1024 * 1024  # 1 MiB — reduces memory pressure on large images


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def hash_file(path: Path) -> str:
    """
    Compute the SHA-256 digest of a file at *path*.

    Reads in 1 MiB chunks to handle large disk images without loading
    the entire file into memory.

    Args:
        path: Absolute path to the file. Must exist and be readable.

    Returns:
        Lowercase hex-encoded SHA-256 digest (64 characters).

    Raises:
        FileNotFoundError: if *path* does not exist.
        PermissionError: if *path* is not readable.
    """
    hasher = hashlib.new(HASH_ALGORITHM)
    with open(path, "rb") as fh:
        _hash_stream(fh, hasher)
    return hasher.hexdigest()


def hash_bytes(data: bytes) -> str:
    """
    Compute the SHA-256 digest of an in-memory byte buffer.

    Args:
        data: Raw bytes to hash.

    Returns:
        Lowercase hex-encoded SHA-256 digest (64 characters).
    """
    return hashlib.new(HASH_ALGORITHM, data).hexdigest()


def hash_stream(stream: BinaryIO) -> str:
    """
    Compute the SHA-256 digest of a readable binary stream.

    The caller is responsible for seeking the stream to position 0
    before calling this function if re-reading is intended.

    Args:
        stream: Any binary-readable file-like object.

    Returns:
        Lowercase hex-encoded SHA-256 digest (64 characters).
    """
    hasher = hashlib.new(HASH_ALGORITHM)
    _hash_stream(stream, hasher)
    return hasher.hexdigest()


def verify_file(path: Path, expected_hex: str) -> bool:
    """
    Verify that a file's SHA-256 digest matches *expected_hex*.

    Args:
        path: Path to the file to verify.
        expected_hex: The expected lowercase hex SHA-256 digest.

    Returns:
        True if the digest matches; False otherwise.
    """
    return hash_file(path) == expected_hex.lower()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _hash_stream(stream: BinaryIO, hasher: "hashlib._Hash") -> None:  # type: ignore[name-defined]
    for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
        hasher.update(chunk)
