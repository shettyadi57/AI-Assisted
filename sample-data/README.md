# Sample Forensic Data

This directory contains synthetic file fragments and sector dumps designed for development and testing of the Reconstruct file fragment reconstruction pipeline.

## Dataset: Synthetic JPEG Carving Cluster
This cluster simulates three 512-byte fragments carved from a damaged FAT32/exFAT disk image, plus an unallocated slack sector.

### Files & Characteristics

| File | Size (Bytes) | Role | Key Markers |
|---|---|---|---|
| `fragment_001_jpeg_header.bin` | 512 | Header Block | SOI (`0xFFD8`), APP0/JFIF (`0xFFE0`), DQT (`0xFFDB`) |
| `fragment_002_jpeg_entropy.bin` | 512 | Middle Block | Entropy-coded scan stream (high Shannon entropy ~7.95) |
| `fragment_003_jpeg_eoi.bin` | 512 | Footer Block | Scan tail terminating in EOI marker (`0xFFD9`) |
| `fragment_004_corrupted_slack.bin` | 512 | Corrupted Slack | Interleaved parity bytes and trailing zero-padding |

### Ground Truth Sequence
- Correct order: `fragment_001` ➔ `fragment_002` ➔ `fragment_003`
- Total reconstructed size: 1,536 bytes
- Expected format: `image/jpeg`
- Validation target: Structural JPEG validator confirms valid SOI-to-EOI stream

### Provenance Manifest
See `sample-data/manifest.json` for exact SHA-256 cryptographic hashes for each fragment.
Raw evidence in this folder is strictly **read-only**.
