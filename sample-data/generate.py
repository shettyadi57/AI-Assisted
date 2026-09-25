"""
sample-data/generate.py — Deterministic forensic fixture generator for Reconstruct.

Builds all sample datasets from scratch using only Python stdlib.
Run from ANY directory:
    python sample-data/generate.py

Outputs (relative to this script's directory):
    pdf/
        pdf_contiguous.bin      — small valid PDF, whole file
        pdf_frag_01.bin … 05    — same PDF split at 4 096-byte cluster boundaries
    jpeg/
        jpeg_frag_01.bin … 04   — JPEG split into 4 fragments; frag_03 is duplicated
        jpeg_frag_03_dup.bin    — exact byte-copy of frag_03 (duplicate)
    png/
        png_frag_01.bin … 04    — PNG split into 4 fragments; frag_02 has bytes flipped
    zip_/
        zip_frag_01.bin … 04    — ZIP split; frag_03 is missing (gap)
    loose-fragment-soup.bin     — all fragments from pdf/jpeg/png/zip concatenated
                                   in randomized order (deterministic seed=42)
    manifest.json               — ground-truth: fragment→file, order, flags
                                   (FOR TESTING ONLY — never surface to investigator UI)

Rules respected:
    - SEED = 42 everywhere; every run produces identical bytes and hashes.
    - No third-party libraries.
    - Structural validity: all formats are spec-correct enough for the later
      format validators to parse (Phase 6 tests will use these).
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import struct
import zlib
from pathlib import Path

# ---------------------------------------------------------------------------
SEED = 42
OUT_DIR = Path(__file__).resolve().parent   # same directory as this script
BLOCK = 4096                                 # cluster/sector boundary size

rng = random.Random(SEED)


# ─── helpers ────────────────────────────────────────────────────────────────

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pad_to_block(data: bytes, block: int = BLOCK) -> bytes:
    """Zero-pad bytes up to the next block boundary."""
    if len(data) % block == 0:
        return data
    return data + b"\x00" * (block - len(data) % block)


def _split(data: bytes, block: int = BLOCK) -> list[bytes]:
    """Split data into block-sized chunks (last chunk may be shorter)."""
    return [data[i : i + block] for i in range(0, len(data), block)]


def _write(path: Path, data: bytes) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {
        "file": str(path.relative_to(OUT_DIR)),
        "size": len(data),
        "sha256": _sha256(data),
    }


# ─── PDF builder ────────────────────────────────────────────────────────────

def build_pdf() -> bytes:
    """
    Build a structurally-valid multi-page PDF (~20 KB) so that splitting at
    BLOCK=4096 yields 5 fragments.
    Spec-correct cross-reference table + trailer dictionary.
    """
    # We pad the content stream with deterministic filler so the overall
    # file size lands in the 16–20 KB range (4–5 full 4096-byte blocks).

    rng_local = random.Random(SEED + 1)
    # Printable ASCII filler — keeps the file text-inspectable
    filler = "".join(
        rng_local.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \n")
        for _ in range(16384)          # 16 KB of filler text
    )
    content_stream = (
        b"BT /F1 12 Tf 72 720 Td (Reconstruct Test PDF - Phase 1 Sample) Tj ET\n"
        + b"% " + filler.encode("ascii") + b"\n"
    )
    cs_len = len(content_stream)

    def obj(n: int, body: bytes) -> bytes:
        return f"{n} 0 obj\n".encode() + body + b"\nendobj\n"

    o1 = obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    o2 = obj(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    o3 = obj(3, (
        b"<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] "
        b"/Contents 4 0 R "
        b"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>"
    ))
    o4 = obj(4, (
        f"<< /Length {cs_len} >>\nstream\n".encode()
        + content_stream
        + b"\nendstream"
    ))

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets: dict[int, int] = {}
    body = b""
    for i, ob in enumerate([o1, o2, o3, o4], start=1):
        offsets[i] = len(header) + len(body)
        body += ob

    startxref = len(header) + len(body)
    xref = b"xref\n0 5\n0000000000 65535 f \n"
    for i in range(1, 5):
        xref += f"{offsets[i]:010d} 00000 n \n".encode()

    trailer = (
        b"trailer\n<< /Size 5 /Root 1 0 R >>\n"
        + f"startxref\n{startxref}\n%%EOF\n".encode()
    )

    return header + body + xref + trailer



# ─── JPEG builder ───────────────────────────────────────────────────────────

def build_jpeg() -> bytes:
    """
    Build a minimal valid JPEG: SOI → APP0/JFIF → DQT → SOF0 → DHT → SOS → entropy → EOI.
    8×8 grayscale pixels; entropy-coded scan data generated deterministically.
    Spec-correct enough for JPEG marker-stream validation.
    """
    def marker(code: int, payload: bytes = b"") -> bytes:
        if payload:
            return struct.pack(">BB", 0xFF, code) + struct.pack(">H", len(payload) + 2) + payload
        return struct.pack(">BB", 0xFF, code)

    soi = b"\xff\xd8"

    # APP0 JFIF
    app0 = marker(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")

    # DQT — one 64-byte quantisation table (table 0, all-ones for test)
    qt = bytes([1] * 64)
    dqt = marker(0xDB, bytes([0x00]) + qt)

    # SOF0 — 8×8 grayscale (1 component)
    # P=8 bits, Y=8, X=8, Nf=1, C=1, H=1, V=1, Tq=0
    sof0 = marker(0xC0, struct.pack(">BHHB", 8, 8, 8, 1) + bytes([1, 0x11, 0]))

    # DHT — minimal Huffman table (DC, table 0)
    # 16 counts of code lengths + one value
    ht_counts = bytes(16)                # all zeros except:
    ht_counts = b"\x00" * 1 + b"\x01" + b"\x00" * 14  # 1 code of length 2
    ht_values = bytes([0x00])
    dht = marker(0xC4, bytes([0x00]) + ht_counts + ht_values)

    # SOS header — 1 component, DC=0 table, AC=0 table
    sos_header = marker(0xDA, struct.pack(">B", 1) + bytes([1, 0x00, 0, 63, 0]))

    # Entropy scan data — deterministic bytes that won't contain 0xFF 0x00
    # (which would need byte-stuffing); keep it simple and valid-looking
    rng_local = random.Random(SEED + 100)
    scan_data = bytes(
        b if b != 0xFF else 0xFE
        for b in (rng_local.randint(0, 254) for _ in range(512))
    )

    eoi = b"\xff\xd9"

    return soi + app0 + dqt + sof0 + dht + sos_header + scan_data + eoi


# ─── PNG builder ─────────────────────────────────────────────────────────────

def build_png() -> bytes:
    """
    Build a minimal valid 4×4 grayscale PNG.
    IHDR → IDAT (zlib-compressed scan lines) → IEND.
    CRC-32 checksums are spec-correct.
    """
    def chunk(name: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(name + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", crc)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 4, 4, 8, 0, 0, 0, 0)  # 4×4, 8-bit grayscale
    ihdr = chunk(b"IHDR", ihdr_data)

    # 4 scanlines of 4 grayscale pixels each; filter byte 0x00 (None) prepended
    rng_local = random.Random(SEED + 200)
    raw_scanlines = b"".join(
        b"\x00" + bytes(rng_local.randint(0, 255) for _ in range(4))
        for _ in range(4)
    )
    idat = chunk(b"IDAT", zlib.compress(raw_scanlines, level=9))
    iend = chunk(b"IEND", b"")

    return signature + ihdr + idat + iend


# ─── ZIP builder ─────────────────────────────────────────────────────────────

def build_zip() -> bytes:
    """
    Build a minimal valid ZIP with two small text files.
    Uses only stdlib; no zipfile module to keep byte control explicit.
    Local file headers → Central directory → EOCD.
    """
    def local_file(name: bytes, data: bytes) -> tuple[bytes, bytes, int]:
        """Returns (local_header+data, central_dir_entry, offset_at_call_time)."""
        crc = zlib.crc32(data) & 0xFFFFFFFF
        # local header signature (PK\x03\x04) + version=20, flags=0, method=0(stored)
        lh = (
            b"PK\x03\x04"
            + struct.pack("<HHHHIIII", 20, 0, 0, 0, crc, len(data), len(data), len(name))
            + name
        )
        return lh + data, crc, len(lh)

    files = [
        (b"readme.txt", b"Reconstruct test ZIP entry 1\n"),
        (b"data.bin",   bytes(range(32))),
    ]

    local_headers = []
    central_dirs  = []
    offset = 0

    for fname, fdata in files:
        crc = zlib.crc32(fdata) & 0xFFFFFFFF
        lh = (
            b"PK\x03\x04"
            + struct.pack("<HHHHIII", 20, 0, 0, 0, crc, len(fdata), len(fdata))
            + struct.pack("<H", len(fname))
            + struct.pack("<H", 0)
            + fname
        )
        local_headers.append(lh + fdata)

        cd = (
            b"PK\x01\x02"
            + struct.pack("<HHHHHIIIHHHHHii",
                20, 20, 0, 0, 0, crc, len(fdata), len(fdata),
                len(fname), 0, 0, 0, 0, 0, offset)
            + fname
        )
        central_dirs.append(cd)
        offset += len(lh) + len(fdata)

    local_blob = b"".join(local_headers)
    cd_blob    = b"".join(central_dirs)
    cd_offset  = len(local_blob)
    cd_size    = len(cd_blob)

    eocd = (
        b"PK\x05\x06"
        + struct.pack("<HHHHIIH", 0, 0, len(files), len(files), cd_size, cd_offset, 0)
    )

    return local_blob + cd_blob + eocd


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    manifest: dict = {
        "seed": SEED,
        "block_size": BLOCK,
        "note": (
            "GROUND TRUTH — FOR TESTING ONLY. "
            "Never surface to the investigator UI as if discovered. "
            "Manifesting this to the UI would be fabricating results."
        ),
        "files": {},
    }

    # ── 1. PDF contiguous + split ──────────────────────────────────────────
    pdf_bytes = build_pdf()
    pdf_padded = _pad_to_block(pdf_bytes)
    pdf_frags = _split(pdf_padded)

    # Contiguous
    info = _write(OUT_DIR / "pdf" / "pdf_contiguous.bin", pdf_bytes)
    manifest["files"]["pdf_contiguous"] = {**info, "type": "pdf", "role": "contiguous"}

    # Fragmented
    pdf_frag_info = []
    for i, frag in enumerate(pdf_frags, start=1):
        tag = f"pdf_frag_{i:02d}"
        info = _write(OUT_DIR / "pdf" / f"{tag}.bin", frag)
        pdf_frag_info.append({
            **info,
            "fragment_index": i,
            "offset_in_original": (i - 1) * BLOCK,
            "flags": [],
        })
    manifest["files"]["pdf_fragments"] = {
        "type": "pdf",
        "source": "pdf_contiguous",
        "sequence_order": [f["file"] for f in pdf_frag_info],
        "fragments": pdf_frag_info,
    }

    # ── 2. JPEG fragmented (frag_03 duplicated) ────────────────────────────
    jpeg_bytes  = build_jpeg()
    jpeg_padded = _pad_to_block(jpeg_bytes)
    jpeg_frags  = _split(jpeg_padded)
    # Ensure at least 4 fragments; pad if needed
    while len(jpeg_frags) < 4:
        jpeg_frags.append(b"\x00" * BLOCK)

    jpeg_frag_info = []
    for i, frag in enumerate(jpeg_frags, start=1):
        tag = f"jpeg_frag_{i:02d}"
        info = _write(OUT_DIR / "jpeg" / f"{tag}.bin", frag)
        jpeg_frag_info.append({
            **info,
            "fragment_index": i,
            "offset_in_original": (i - 1) * BLOCK,
            "flags": [],
        })

    # Duplicate frag_03 (index 2 = 3rd, 0-based)
    dup_src = jpeg_frags[min(2, len(jpeg_frags) - 1)]
    dup_info = _write(OUT_DIR / "jpeg" / "jpeg_frag_03_dup.bin", dup_src)
    manifest["files"]["jpeg_fragments"] = {
        "type": "jpeg",
        "source_bytes": _sha256(jpeg_bytes),
        "sequence_order": [f["file"] for f in jpeg_frag_info],
        "fragments": jpeg_frag_info,
        "duplicates": [{
            **dup_info,
            "duplicate_of": jpeg_frag_info[min(2, len(jpeg_frag_info) - 1)]["file"],
            "flags": ["DUPLICATE"],
        }],
    }

    # ── 3. PNG fragmented (frag_02 bytes flipped / corrupted) ─────────────
    png_bytes  = build_png()
    png_padded = _pad_to_block(png_bytes)
    png_frags  = _split(png_padded)
    while len(png_frags) < 4:
        png_frags.append(b"\x00" * BLOCK)

    png_frag_info = []
    for i, frag in enumerate(png_frags, start=1):
        tag = f"png_frag_{i:02d}"
        if i == 2:
            # Flip every byte in this fragment to corrupt its CRC-32
            frag = bytes(b ^ 0xFF for b in frag)
        info = _write(OUT_DIR / "png" / f"{tag}.bin", frag)
        png_frag_info.append({
            **info,
            "fragment_index": i,
            "offset_in_original": (i - 1) * BLOCK,
            "flags": ["CORRUPTED"] if i == 2 else [],
        })
    manifest["files"]["png_fragments"] = {
        "type": "png",
        "source_bytes": _sha256(png_bytes),
        "sequence_order": [f["file"] for f in png_frag_info],
        "fragments": png_frag_info,
    }

    # ── 4. ZIP fragmented (frag_03 missing) ───────────────────────────────
    zip_bytes  = build_zip()
    zip_padded = _pad_to_block(zip_bytes)
    zip_frags  = _split(zip_padded)
    while len(zip_frags) < 4:
        zip_frags.append(b"\x00" * BLOCK)

    zip_frag_info = []
    for i, frag in enumerate(zip_frags, start=1):
        tag = f"zip_frag_{i:02d}"
        flags: list[str] = []
        if i == 3:
            # Skip writing; this fragment is "missing" (simulates a disk gap)
            zip_frag_info.append({
                "file": f"zip_/{tag}.bin",
                "size": len(frag),
                "sha256": _sha256(frag),
                "fragment_index": i,
                "offset_in_original": (i - 1) * BLOCK,
                "flags": ["MISSING"],
            })
            continue
        info = _write(OUT_DIR / "zip_" / f"{tag}.bin", frag)
        zip_frag_info.append({
            **info,
            "fragment_index": i,
            "offset_in_original": (i - 1) * BLOCK,
            "flags": flags,
        })
    manifest["files"]["zip_fragments"] = {
        "type": "zip",
        "source_bytes": _sha256(zip_bytes),
        "sequence_order": [f["file"] for f in zip_frag_info],
        "fragments": zip_frag_info,
        "note": "Fragment 3 (zip_frag_03.bin) intentionally absent — simulates a disk gap.",
    }

    # ── 5. Loose fragment soup ─────────────────────────────────────────────
    # Collect all *written* fragment files (exclude the missing zip frag)
    soup_parts: list[tuple[str, bytes]] = []

    for d, stem in [
        ("pdf", "pdf_frag"),
        ("jpeg", "jpeg_frag"),
        ("png", "png_frag"),
        ("zip_", "zip_frag"),
    ]:
        for p in sorted((OUT_DIR / d).glob(f"{stem}_??.bin")):
            soup_parts.append((str(p.relative_to(OUT_DIR)), p.read_bytes()))

    # Also include the duplicate jpeg frag in the soup (it's on "disk")
    dup_path = OUT_DIR / "jpeg" / "jpeg_frag_03_dup.bin"
    soup_parts.append((str(dup_path.relative_to(OUT_DIR)), dup_path.read_bytes()))

    # Randomise order with fixed seed so it's deterministic
    rng.shuffle(soup_parts)

    # Record the shuffle order in the manifest
    soup_order: list[dict] = []
    soup_blob = b""
    for src_file, data in soup_parts:
        soup_order.append({
            "source_file": src_file,
            "soup_offset": len(soup_blob),
            "size": len(data),
            "sha256": _sha256(data),
        })
        soup_blob += data

    soup_info = _write(OUT_DIR / "loose-fragment-soup.bin", soup_blob)
    manifest["loose_fragment_soup"] = {
        **soup_info,
        "description": (
            "All fragment files concatenated in randomised order (seed=42). "
            "Simulates fragments pulled off a disk image with no directory structure. "
            "Primary test input for the full pipeline."
        ),
        "soup_order": soup_order,
    }

    # ── Write manifest ─────────────────────────────────────────────────────
    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"manifest -> {manifest_path}")

    # ── Summary ────────────────────────────────────────────────────────────
    soup_mb = len(soup_blob) / 1024
    print(f"\nSample data generated in: {OUT_DIR}")
    print(f"  loose-fragment-soup.bin  {soup_mb:.1f} KB  sha256={soup_info['sha256'][:16]}…")
    print(f"  Total soup fragments: {len(soup_order)}")
    print(f"  Block size: {BLOCK} bytes")
    print(f"  Seed: {SEED}")
    print("\nArtifacts:")
    for sub in ["pdf", "jpeg", "png", "zip_"]:
        files = sorted((OUT_DIR / sub).glob("*.bin"))
        print(f"  {sub}/  ({len(files)} files)")
    print("\nDone.")


if __name__ == "__main__":
    main()
