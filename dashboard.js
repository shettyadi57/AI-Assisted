/**
 * RECONSTRUCT — RECOVERY RESULTS & FRAGMENT DETAIL CONTROLLER (Chunks 2 & 3)
 * Full forensics triage and fragment relationship inspection engine.
 */

// Comprehensive Forensic Recovery Dataset
const FORENSIC_ITEMS = [
  {
    id: "REC-001",
    filename: "evidence_vault.db",
    meta: "SQLite 3 format 3 (WAL mode active)",
    type: "database",
    typeName: "Database",
    typeIcon: "database",
    confidence: 99.4,
    status: "high",
    statusLabel: "99.4% Confident",
    statusBadgeClass: "badge-status-high",
    blockCount: 1420,
    hash: "3a8f102c91b84e55a01bc894ef2098bc5100fa12c98d44719001bfa8290cc411",
    inferredDetails: {
      format: "SQLite Database (version 3.39.4)",
      pageSize: "4,096 B",
      records: "184,920 rows",
      tables: ["credentials", "audit_log", "vault_sessions", "encryption_keys"],
      walStatus: "WAL Frame #001 through #842 synced",
      encoding: "UTF-8 text / BLOB binary"
    },
    schemaText: `CREATE TABLE vault_sessions (
  session_id TEXT PRIMARY KEY, /* UUIDv4 */
  user_id    INTEGER NOT NULL,
  auth_token BLOB NOT NULL,    /* AES-256-GCM encrypted */
  created_at INTEGER NOT NULL, /* Epoch ms */
  expires_at INTEGER NOT NULL
);

CREATE TABLE audit_log (
  event_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_ip   TEXT NOT NULL,
  action     TEXT NOT NULL,    /* 'READ_SECTOR', 'KEY_ROTATION' */
  timestamp  TEXT NOT NULL
);`,
    fragments: [
      { seq: "01", blockId: "BLK-0x004F:SEC-8192", offset: "0x001A8F00", size: "4,096 B", status: "clean", label: "Clean / Header" },
      { seq: "02", blockId: "BLK-0x004F:SEC-8193", offset: "0x001A9F00", size: "4,096 B", status: "clean", label: "Clean / Schema Page" },
      { seq: "03", blockId: "BLK-0x0050:SEC-8204", offset: "0x001B4000", size: "4,096 B", status: "clean", label: "Clean / Table Root" },
      { seq: "04", blockId: "BLK-0x0052:SEC-8220", offset: "0x001C4000", size: "4,096 B", status: "clean", label: "Clean / B-Tree Leaf" },
      { seq: "05", blockId: "BLK-0x0058:SEC-8340", offset: "0x001E8000", size: "4,096 B", status: "clean", label: "Clean / Overflow Page" },
      { seq: "06", blockId: "BLK-0x0061:SEC-8500", offset: "0x00210000", size: "4,096 B", status: "clean", label: "Clean / WAL Journal" }
    ],
    confidenceFactors: [
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "Header Signature Match",
        desc: "Magic byte sequence 'SQLite format 3' verified with 100% bit-exact parity at offset 0x00000000.",
        metric: "SIGNATURE: VALID (53 51 4C 69 74 65)"
      },
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "Sequence & Relationship Integrity",
        desc: "B-Tree interior pointer chain resolves to contiguous and non-contiguous physical sector runs without gaps.",
        metric: "POINTER CHAIN: 100% RESOLVED"
      },
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "Zero Sector Corruption",
        desc: "All 1,420 assembled blocks verified clean; checksums match internal database page header validation.",
        metric: "CORRUPTED BLOCKS: 0 / 1,420"
      }
    ]
  },
  {
    id: "REC-002",
    filename: "incident_report_2026_q3.pdf",
    meta: "Adobe PDF v1.7 (xref reconstructed)",
    type: "document",
    typeName: "Document",
    typeIcon: "fileText",
    confidence: 96.8,
    status: "high",
    statusLabel: "96.8% Confident",
    statusBadgeClass: "badge-status-high",
    blockCount: 852,
    hash: "7f4c01e92d8a4328bc1001ee4a991823bc4401bb8909ffaa123089c104ab3401",
    inferredDetails: {
      format: "PDF Document (ISO 32000-1)",
      pages: "18 pages identified",
      creator: "LaTeX with hyperref / pdfTeX-1.40.21",
      encryption: "None (plaintext trailer)",
      streamFilter: "FlateDecode (valid streams)"
    },
    sampleText: `%PDF-1.7
%âãÏÓ
1 0 obj
<< /Type /Catalog /Pages 2 0 R /Metadata 3 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [4 0 R 5 0 R 6 0 R] /Count 3 >>
endobj
4 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 7 0 R >>
endobj
7 0 obj
<< /Length 1420 /Filter /FlateDecode >>
stream
[CONFIDENTIAL INCIDENT REPORT - FORENSIC SECTOR INVESTIGATION]
Target: Host 10.42.0.18 - Storage partition nvme0n1p3
Incident Type: Suspicious Mass-Deletion via SDelete Slack Fill
Reconstructed Objects: 10 artifacts salvaged via neural block carving
Classification: TOP-SECRET // CYBER FORENSICS TRIAGE
endstream
endobj`,
    fragments: [
      { seq: "01", blockId: "BLK-0x007A:SEC-9100", offset: "0x002A0000", size: "4,096 B", status: "clean", label: "Clean / PDF Header" },
      { seq: "02", blockId: "BLK-0x007A:SEC-9101", offset: "0x002A1000", size: "4,096 B", status: "clean", label: "Clean / Object Catalog" },
      { seq: "03", blockId: "BLK-0x007B:SEC-9120", offset: "0x002B4000", size: "4,096 B", status: "clean", label: "Clean / Page Stream" },
      { seq: "04", blockId: "BLK-0x007E:SEC-9200", offset: "0x002E0000", size: "4,096 B", status: "clean", label: "Clean / XREF Table" }
    ],
    confidenceFactors: [
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "PDF Catalog & XREF Integrity",
        desc: "Cross-reference table reconstructed and verified against linearized object hierarchy.",
        metric: "XREF VALID: 18 / 18 OBJECTS"
      },
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "Deflate Stream Decodability",
        desc: "All FlateDecode text streams decompressed without zlib checksum errors.",
        metric: "DECOMPRESSION: SUCCESS (0 ERRORS)"
      },
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "Sequential Block Alignment",
        desc: "Contiguous physical runs match inferred page index without sector interleaving.",
        metric: "BLOCK RUNS: 4 OF 4 CONCURRENT"
      }
    ]
  },
  {
    id: "REC-004",
    filename: "frame_capture_cam04.jpg",
    meta: "JFIF JPEG (valid SOI/EOI bounds)",
    type: "image",
    typeName: "Image",
    typeIcon: "fileImage",
    confidence: 78.5,
    status: "medium",
    statusLabel: "78.5% Review",
    statusBadgeClass: "badge-status-medium",
    blockCount: 540,
    hash: "45a89df2001ca889b019ee02f431c99877401aab9001cc4918230bba9810a9f2",
    inferredDetails: {
      format: "JPEG / JFIF Baseline Standard",
      dimensions: "1920 × 1080 px (1080p)",
      colorSpace: "YCbCr 4:2:0 subsampling",
      quantization: "Standard DQT tables recovered",
      warning: "Partial scanline tearing at vertical line 820"
    },
    fragments: [
      { seq: "01", blockId: "BLK-0x011A:SEC-12000", offset: "0x004E0000", size: "4,096 B", status: "clean", label: "Clean / SOI Header" },
      { seq: "02", blockId: "BLK-0x011A:SEC-12001", offset: "0x004E1000", size: "4,096 B", status: "clean", label: "Clean / Huffman Table" },
      { seq: "03", blockId: "BLK-0x011B:SEC-12040", offset: "0x004F4000", size: "4,096 B", status: "clean", label: "Clean / Scan Segment" },
      { seq: "04", blockId: "BLK-0x0120:SEC-12150", offset: "0x00520000", size: "4,096 B", status: "review", label: "Needs Review / Slack Gap" },
      { seq: "05", blockId: "BLK-0x0122:SEC-12210", offset: "0x00538000", size: "4,096 B", status: "clean", label: "Clean / EOI Marker" }
    ],
    confidenceFactors: [
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "JPEG SOI / EOI Markers Present",
        desc: "Valid Start-of-Image (FF D8) and End-of-Image (FF D9) delimiters safely bounded.",
        metric: "MARKERS: 0xFFD8 ... 0xFFD9"
      },
      {
        icon: "alertTriangle",
        iconColor: "var(--status-medium)",
        label: "Huffman Restart Synchronization",
        desc: "Block #04 experienced partial bitstream drift before recovering at RST2 marker.",
        metric: "SLACK DRIFT: 128 BYTES"
      },
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "Quantization Table Recovery",
        desc: "Both luminance and chrominance tables recovered intact without distortion.",
        metric: "DQT TABLES: 2 / 2 INTACT"
      }
    ]
  },
  {
    id: "REC-006",
    filename: "auth_audit.log",
    meta: "UTF-8 Syslog stream (neural carved)",
    type: "document",
    typeName: "Document",
    typeIcon: "fileText",
    confidence: 61.9,
    status: "medium",
    statusLabel: "61.9% Review",
    statusBadgeClass: "badge-status-medium",
    blockCount: 184,
    hash: "88cc401f993e11029ab48102ff3991823bc0192eaab019230981ba001299c811",
    inferredDetails: {
      format: "Plaintext UTF-8 Log Stream",
      lines: "2,410 log entries parsed",
      timeSpan: "2026-09-24T18:00:00Z to 2026-09-25T04:30:00Z",
      severity: "AUTH_FAILURE alerts clustered in block #02"
    },
    sampleText: `2026-09-24T23:14:02.109Z srv-auth01 sshd[18492]: Failed password for invalid user admin from 198.51.100.44 port 48102 ssh2
2026-09-24T23:14:05.441Z srv-auth01 sshd[18493]: Failed password for invalid user root from 198.51.100.44 port 48108 ssh2
2026-09-24T23:14:09.810Z srv-auth01 sshd[18494]: Accepted publickey for forensics_agent from 10.0.1.5 port 51230 ssh2: RSA SHA256:4b...
2026-09-24T23:15:00.001Z srv-auth01 sudo[18501]: forensics_agent : TTY=pts/1 ; PWD=/var/log ; USER=root ; COMMAND=/bin/dd if=/dev/nvme0n1
2026-09-24T23:16:30.884Z srv-auth01 kernel: [Slack_Carve] Detected fragmented cluster release at sector 0x002B4800
2026-09-24T23:17:10.002Z srv-auth01 auditd[912]: USER_LOGIN pid=18520 uid=0 auid=1000 ses=4 msg='op=login id=0 res=success'`,
    fragments: [
      { seq: "01", blockId: "BLK-0x0180:SEC-16400", offset: "0x006A0000", size: "4,096 B", status: "clean", label: "Clean / Log Header" },
      { seq: "02", blockId: "BLK-0x0180:SEC-16401", offset: "0x006A1000", size: "4,096 B", status: "review", label: "Needs Review / Corrupt Lines" },
      { seq: "03", blockId: "BLK-0x0182:SEC-16490", offset: "0x006B5000", size: "4,096 B", status: "clean", label: "Clean / Continuation" }
    ],
    confidenceFactors: [
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "RFC-5424 Syslog Pattern Match",
        desc: "Regular ISO-8601 timestamps and syslog facility tags verified across 84% of lines.",
        metric: "REGEX CONFORMANCE: 84.2%"
      },
      {
        icon: "alertTriangle",
        iconColor: "var(--status-medium)",
        label: "Truncated Line Wraps",
        desc: "Block #02 contains non-printable binary artifacts indicating partially overwritten file slack.",
        metric: "CORRUPTED BYTES: 384 BYTES"
      },
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "Chronological Sequence Integrity",
        desc: "Extracted timestamps progress monotonically without retrograde time jumps.",
        metric: "MONOTONIC TIME: VERIFIED"
      }
    ]
  },
  {
    id: "REC-008",
    filename: "malware_dropper.elf",
    meta: "ELF 64-bit LSB (section headers wiped)",
    type: "binary",
    typeName: "Binary",
    typeIcon: "fileCode",
    confidence: 24.5,
    status: "low",
    statusLabel: "24.5% Corrupted",
    statusBadgeClass: "badge-status-low",
    blockCount: 410,
    hash: "00fa9912bc8700192aab8102ff3991823bc0192eaab019230981ba001299c811",
    inferredDetails: {
      format: "ELF 64-bit LSB pie executable",
      architecture: "x86-64 (AMD x86-64)",
      entryPoint: "0x00001080 (inferred)",
      damage: "Section header table truncated; zero-filled overwrites",
      threatRating: "CRITICAL MALICIOUS PAYLOAD"
    },
    sampleText: `ELF Header (Partial Recovery):
  Magic:   7F 45 4C 46 02 01 01 00 00 00 00 00 00 00 00 00
  Class:                             ELF64
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  Type:                              DYN (Position-Independent Executable)
  Machine:                           Advanced Micro Devices X86-64
  Entry point address:               0x1080
  Start of program headers:          64 (bytes into file)
  Start of section headers:          [CORRUPTED - VALUE 0x00000000]
  Flags:                             0x0
  Size of this header:               64 (bytes)
  Number of program headers:         11
  Size of section headers:           [INVALID]`,
    fragments: [
      { seq: "01", blockId: "BLK-0x0210:SEC-21000", offset: "0x00880000", size: "4,096 B", status: "clean", label: "Clean / ELF Magic" },
      { seq: "02", blockId: "BLK-0x0210:SEC-21001", offset: "0x00881000", size: "4,096 B", status: "corrupted", label: "Corrupted / Overwritten" },
      { seq: "03", blockId: "BLK-0x0214:SEC-21090", offset: "0x008A2000", size: "4,096 B", status: "corrupted", label: "Corrupted / Zero-Fill" }
    ],
    confidenceFactors: [
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "ELF Magic Signature Found",
        desc: "Leading 4 bytes match standard ELF magic (0x7F 'E' 'L' 'F').",
        metric: "SIGNATURE: 0x7F454C46"
      },
      {
        icon: "xCircle",
        iconColor: "var(--status-low)",
        label: "Section Table Annihilation",
        desc: "Section header offset points to an overwritten cluster containing zero-fill patterns.",
        metric: "SECTION STATUS: TRUNCATED"
      },
      {
        icon: "xCircle",
        iconColor: "var(--status-low)",
        label: "High Block Discontinuity",
        desc: "Over 75% of expected code pages were overwritten by unallocated slack filler.",
        metric: "SLACK OVERWRITE: 75.5%"
      }
    ]
  },
  {
    id: "REC-009",
    filename: "unallocated_sector_slack.raw",
    meta: "Zero-filled slack space cluster run",
    type: "binary",
    typeName: "Binary",
    typeIcon: "fileCode",
    confidence: 0.0,
    status: "low",
    statusLabel: "0.0% Corrupted",
    statusBadgeClass: "badge-status-low",
    blockCount: 1024,
    hash: "0000000000000000000000000000000000000000000000000000000000000000",
    inferredDetails: {
      format: "Raw Physical Sector Slub",
      entropy: "0.0000 (Pure Zeroes)",
      content: "Unallocated slack space; zero payload recovered"
    },
    sampleText: `00000000: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
00000010: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
00000020: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
00000030: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
* (All remaining sectors zero-filled)`,
    fragments: [
      { seq: "01", blockId: "BLK-0x0300:SEC-30000", offset: "0x00C00000", size: "4,096 B", status: "corrupted", label: "Corrupted / Zero-Fill" },
      { seq: "02", blockId: "BLK-0x0300:SEC-30001", offset: "0x00C01000", size: "4,096 B", status: "corrupted", label: "Corrupted / Zero-Fill" }
    ],
    confidenceFactors: [
      {
        icon: "xCircle",
        iconColor: "var(--status-low)",
        label: "Zero Magic Signature",
        desc: "No recognized file format header detected across raw sectors.",
        metric: "MAGIC: 0x00000000"
      },
      {
        icon: "xCircle",
        iconColor: "var(--status-low)",
        label: "Zero Shannon Entropy",
        desc: "Calculated entropy is 0.000 bits/byte indicating uniform unallocated null bytes.",
        metric: "ENTROPY: 0.0000"
      }
    ]
  },
  {
    id: "REC-003",
    filename: "$MFT_Mirror_Fragment.bin",
    meta: "NTFS MFT mirror segment (8 records)",
    type: "binary",
    typeName: "Binary",
    typeIcon: "fileCode",
    confidence: 94.1,
    status: "high",
    statusLabel: "94.1% Confident",
    statusBadgeClass: "badge-status-high",
    blockCount: 320,
    hash: "91b4c73a110f88a9102bc99401ab349918230bb8829910aab019230981ba0012",
    inferredDetails: {
      format: "NTFS File System Metadata ($MFTMIRR)",
      recordSize: "1,024 B per FILE record",
      signature: "'FILE' magic (0x46494C45)",
      recordCount: "8 records recovered ($MFT, $MFTMirr, $LogFile, $Volume)"
    },
    sampleText: `MFT Record #0 ($MFT):
  Magic: 'FILE' (0x454C4946)
  Update Sequence Array Offset: 0x0030
  Fixup entries: 3 valid fixup pairs
  LogFile Sequence Number: 0x000000000A891240
  Sequence Number: 1
  Hard Link Count: 1
  First Attribute Offset: 0x0038
  Flags: 0x0001 (IN_USE)
  Attributes Found:
    - $STANDARD_INFORMATION (0x10): Times match master volume
    - $FILE_NAME (0x30): Name='$MFT'
    - $DATA (0x80): Non-resident data run pointer recovered`,
    fragments: [
      { seq: "01", blockId: "BLK-0x0010:SEC-1024", offset: "0x00040000", size: "4,096 B", status: "clean", label: "Clean / $MFT Mirr" },
      { seq: "02", blockId: "BLK-0x0010:SEC-1025", offset: "0x00041000", size: "4,096 B", status: "clean", label: "Clean / Record 4-8" }
    ],
    confidenceFactors: [
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "NTFS 'FILE' Magic Validation",
        desc: "All 8 MFT records contain valid 'FILE' headers with correct fixup arrays.",
        metric: "SIGNATURE: 0x46494C45"
      },
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "USA Fixup Array Integrity",
        desc: "Update sequence arrays match sector end-words without corruption.",
        metric: "USA FIXUPS: 8 / 8 VALID"
      }
    ]
  },
  {
    id: "REC-005",
    filename: "corporate_seal_fragment.png",
    meta: "PNG chunk sequence (missing IEND)",
    type: "image",
    typeName: "Image",
    typeIcon: "fileImage",
    confidence: 68.2,
    status: "medium",
    statusLabel: "68.2% Review",
    statusBadgeClass: "badge-status-medium",
    blockCount: 216,
    hash: "12d8a90bb4c10029aa8102ff3991823bc0192eaab019230981ba001299c811",
    inferredDetails: {
      format: "PNG (Portable Network Graphics)",
      dimensions: "512 × 512 px",
      colorType: "RGBA (32-bit with Alpha)",
      missingChunk: "IEND terminating chunk truncated"
    },
    fragments: [
      { seq: "01", blockId: "BLK-0x0090:SEC-9900", offset: "0x00320000", size: "4,096 B", status: "clean", label: "Clean / PNG Header" },
      { seq: "02", blockId: "BLK-0x0090:SEC-9901", offset: "0x00321000", size: "4,096 B", status: "clean", label: "Clean / IHDR Chunk" },
      { seq: "03", blockId: "BLK-0x0091:SEC-9910", offset: "0x00328000", size: "4,096 B", status: "review", label: "Needs Review / IDAT Cut" }
    ],
    confidenceFactors: [
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "Valid 8-byte PNG Signature",
        desc: "Magic byte sequence 89 50 4E 47 0D 0A 1A 0A confirmed.",
        metric: "PNG SIGNATURE: VALID"
      },
      {
        icon: "alertTriangle",
        iconColor: "var(--status-medium)",
        label: "Missing IEND Trailer",
        desc: "Final IDAT chunk ends abruptly without valid IEND chunk CRC footer.",
        metric: "IEND CHUNK: MISSING"
      }
    ]
  },
  {
    id: "REC-007",
    filename: "backup_keys_enc.tar.gz",
    meta: "GZIP archive (truncated CRC32 trailer)",
    type: "archive",
    typeName: "Archive",
    typeIcon: "archive",
    confidence: 54.0,
    status: "medium",
    statusLabel: "54.0% Review",
    statusBadgeClass: "badge-status-medium",
    blockCount: 960,
    hash: "e5401188ba920019aa8102ff3991823bc0192eaab019230981ba001299c811",
    inferredDetails: {
      format: "GZIP Compressed Tarball",
      header: "1F 8B 08 (Deflate)",
      filename: "keys_backup_2026.tar (embedded)",
      warning: "CRC32 trailer truncated by unallocated sector boundary"
    },
    fragments: [
      { seq: "01", blockId: "BLK-0x0150:SEC-14200", offset: "0x00580000", size: "4,096 B", status: "clean", label: "Clean / GZIP Header" },
      { seq: "02", blockId: "BLK-0x0150:SEC-14201", offset: "0x00581000", size: "4,096 B", status: "review", label: "Needs Review / Stream Tail" }
    ],
    confidenceFactors: [
      {
        icon: "checkCircle",
        iconColor: "var(--status-high)",
        label: "GZIP Magic ID1/ID2",
        desc: "Magic header 1F 8B verified with DEFLATE compression method 08.",
        metric: "GZIP MAGIC: VALID"
      },
      {
        icon: "alertTriangle",
        iconColor: "var(--status-medium)",
        label: "Truncated Archive Trailer",
        desc: "ISIZE and CRC-32 trailer fields truncated in disk slack run.",
        metric: "CRC32 FOOTER: CUT"
      }
    ]
  },
  {
    id: "REC-010",
    filename: "fve_metadata_block.bin",
    meta: "BitLocker metadata block (unreadable)",
    type: "binary",
    typeName: "Binary",
    typeIcon: "fileCode",
    confidence: 18.2,
    status: "low",
    statusLabel: "18.2% Corrupted",
    statusBadgeClass: "badge-status-low",
    blockCount: 64,
    hash: "c4118809aa1e0019aa8102ff3991823bc0192eaab019230981ba001299c811",
    inferredDetails: {
      format: "BitLocker Full Volume Encryption Header",
      guid: "Damaged FVE-FS GUID signature",
      warning: "Volume Master Key (VMK) encrypted block unrecoverable"
    },
    fragments: [
      { seq: "01", blockId: "BLK-0x0002:SEC-128", offset: "0x00008000", size: "4,096 B", status: "corrupted", label: "Corrupted / Header" }
    ],
    confidenceFactors: [
      {
        icon: "alertTriangle",
        iconColor: "var(--status-medium)",
        label: "Partial FVE Signature",
        desc: "Found damaged -FVE-FS- marker with corrupted block CRC.",
        metric: "SIGNATURE: PARTIAL"
      },
      {
        icon: "xCircle",
        iconColor: "var(--status-low)",
        label: "Key Block Overwritten",
        desc: "VMK entry block overwritten by NTFS journal logs.",
        metric: "KEY BLOCK: CORRUPTED"
      }
    ]
  }
];

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const tableBody = document.getElementById('triage-table-body');
  const searchInput = document.getElementById('search-input');
  const typeFilter = document.getElementById('type-filter');
  const statusFilter = document.getElementById('status-filter');
  const sortSelect = document.getElementById('sort-select');
  const rowCountDisplay = document.getElementById('row-count-display');
  const sidebar = document.getElementById('app-sidebar');
  const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
  const sidebarToggleIcon = document.getElementById('sidebar-toggle-icon');
  
  // View Containers (Triage Dashboard vs Fragment Detail)
  const triageViewContainer = document.getElementById('triage-view-container');
  const detailViewContainer = document.getElementById('detail-view-container');

  // Dashboard Sub-containers
  const tableContainer = document.getElementById('table-wrapper');
  const emptyStateContainer = document.getElementById('empty-state-wrapper');
  const scanningStateContainer = document.getElementById('scanning-state-wrapper');
  const scanProgressStrip = document.getElementById('scan-progress-strip');
  const activeScanIndicator = document.getElementById('active-scan-indicator');

  // Stats Counters
  const statTotal = document.getElementById('stat-total');
  const statHigh = document.getElementById('stat-high');
  const statMedium = document.getElementById('stat-medium');
  const statLow = document.getElementById('stat-low');

  // Detail View Elements
  const detailBackBtn = document.getElementById('detail-back-btn');
  const detailFileIcon = document.getElementById('detail-file-icon');
  const detailFilename = document.getElementById('detail-filename');
  const detailMeta = document.getElementById('detail-meta');
  const detailBadgeContainer = document.getElementById('detail-badge-container');
  const detailPreviewTitle = document.getElementById('detail-preview-title');
  const detailPreviewViewport = document.getElementById('detail-preview-viewport');
  const detailChainContainer = document.getElementById('detail-chain-container');
  const detailChainCount = document.getElementById('detail-chain-count');
  const detailBreakdownList = document.getElementById('detail-breakdown-list');
  const detailFileSelector = document.getElementById('detail-file-selector');

  // Sidebar Collapse / Expand
  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      const isCollapsed = sidebar.classList.contains('collapsed');
      if (sidebarToggleIcon) {
        sidebarToggleIcon.setAttribute('data-icon', isCollapsed ? 'panelLeftOpen' : 'panelLeftClose');
      }
      if (typeof renderIcons === 'function') {
        renderIcons();
      }
    });
  }

  // Triage View Switcher (Populated / Scanning / Empty)
  const stateBtns = document.querySelectorAll('.state-btn');
  stateBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      stateBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const targetState = btn.getAttribute('data-state');
      setDashboardState(targetState);
    });
  });

  function setDashboardState(state) {
    if (state === 'empty') {
      if (tableContainer) tableContainer.style.display = 'none';
      if (scanningStateContainer) scanningStateContainer.style.display = 'none';
      if (emptyStateContainer) emptyStateContainer.style.display = 'block';
      if (scanProgressStrip) scanProgressStrip.classList.remove('active');
      if (activeScanIndicator) activeScanIndicator.style.display = 'none';
      updateStatsCounters(0, 0, 0, 0);
    } else if (state === 'scanning') {
      if (tableContainer) tableContainer.style.display = 'none';
      if (emptyStateContainer) emptyStateContainer.style.display = 'none';
      if (scanningStateContainer) scanningStateContainer.style.display = 'block';
      if (scanProgressStrip) scanProgressStrip.classList.add('active');
      if (activeScanIndicator) activeScanIndicator.style.display = 'inline-flex';
      updateStatsCounters('...', '...', '...', '...');
    } else {
      // Populated default
      if (emptyStateContainer) emptyStateContainer.style.display = 'none';
      if (scanningStateContainer) scanningStateContainer.style.display = 'none';
      if (tableContainer) tableContainer.style.display = 'block';
      if (scanProgressStrip) scanProgressStrip.classList.remove('active');
      if (activeScanIndicator) activeScanIndicator.style.display = 'inline-flex';
      renderTable();
    }
    if (typeof renderIcons === 'function') {
      renderIcons();
    }
  }

  function updateStatsCounters(total, high, medium, low) {
    if (statTotal) statTotal.textContent = total;
    if (statHigh) statHigh.textContent = high;
    if (statMedium) statMedium.textContent = medium;
    if (statLow) statLow.textContent = low;
  }

  // Render Table with strict column alignment (Chunk 2)
  function renderTable() {
    if (!tableBody) return;

    let items = [...FORENSIC_ITEMS];

    // Filter by Search Query
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    if (query) {
      items = items.filter(item => 
        item.filename.toLowerCase().includes(query) ||
        item.meta.toLowerCase().includes(query) ||
        item.id.toLowerCase().includes(query)
      );
    }

    // Filter by Type
    const selectedType = typeFilter ? typeFilter.value : 'all';
    if (selectedType !== 'all') {
      items = items.filter(item => item.type === selectedType);
    }

    // Filter by Status
    const selectedStatus = statusFilter ? statusFilter.value : 'all';
    if (selectedStatus !== 'all') {
      items = items.filter(item => item.status === selectedStatus);
    }

    // Sort
    const sortVal = sortSelect ? sortSelect.value : 'confidence-desc';
    if (sortVal === 'confidence-desc') {
      items.sort((a, b) => b.confidence - a.confidence);
    } else if (sortVal === 'confidence-asc') {
      items.sort((a, b) => a.confidence - b.confidence);
    } else if (sortVal === 'filename-asc') {
      items.sort((a, b) => a.filename.localeCompare(b.filename));
    } else if (sortVal === 'blocks-desc') {
      items.sort((a, b) => b.blockCount - a.blockCount);
    }

    // Update Summary Stats with original totals
    const totalCount = FORENSIC_ITEMS.length;
    const highCount = FORENSIC_ITEMS.filter(i => i.status === 'high').length;
    const mediumCount = FORENSIC_ITEMS.filter(i => i.status === 'medium').length;
    const lowCount = FORENSIC_ITEMS.filter(i => i.status === 'low').length;
    updateStatsCounters(totalCount, highCount, mediumCount, lowCount);

    if (rowCountDisplay) {
      rowCountDisplay.textContent = `Showing ${items.length} of ${totalCount} recovered items`;
    }

    if (items.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: var(--space-32); color: var(--text-muted);">
            No matching forensic items found for the active filter query.
          </td>
        </tr>
      `;
      return;
    }

    // Generate table rows
    tableBody.innerHTML = items.map(item => {
      const barClass = item.status === 'high' 
        ? 'confidence-bar-high' 
        : item.status === 'medium' 
          ? 'confidence-bar-medium' 
          : 'confidence-bar-low';

      return `
        <tr tabindex="0" data-item-id="${item.id}">
          <!-- Col 1: Filename (Left-aligned) -->
          <td class="col-filename">
            <div class="filename-cell">
              <span class="filename-text">${item.filename}</span>
              <span class="filename-meta">${item.meta} • <span style="color: var(--accent-ai);">${item.id}</span></span>
            </div>
          </td>

          <!-- Col 2: Type (Left-aligned) -->
          <td class="col-type">
            <span class="type-cell">
              <span data-icon="${item.typeIcon}" data-icon-size="16"></span>
              <span>${item.typeName}</span>
            </span>
          </td>

          <!-- Col 3: Confidence Score (Right-aligned) -->
          <td class="col-confidence">
            <div class="confidence-cell">
              <div class="confidence-bar-track">
                <div class="confidence-bar-fill ${barClass}" style="width: ${item.confidence}%;"></div>
              </div>
              <span class="confidence-pct">${item.confidence.toFixed(1)}%</span>
            </div>
          </td>

          <!-- Col 4: Status Badge (Center-aligned) -->
          <td class="col-status">
            <div class="status-badge-cell">
              <span class="badge ${item.statusBadgeClass}">
                <span class="pulse-indicator" style="background-color: var(--status-${item.status});"></span>
                ${item.statusLabel}
              </span>
            </div>
          </td>

          <!-- Col 5: Block Count (Right-aligned) -->
          <td class="col-blocks">
            <span class="block-count-cell">${item.blockCount.toLocaleString()} BLKS</span>
          </td>

          <!-- Col 6: Action (Center-aligned) -->
          <td class="col-action">
            <button class="action-btn" data-detail-id="${item.id}">
              <span>View Detail</span>
              <span data-icon="arrowRight" data-icon-size="16"></span>
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Re-render icons
    if (typeof renderIcons === 'function') {
      renderIcons();
    }

    // Attach row click & button listeners to trigger Chunk 3 Detail View
    tableBody.querySelectorAll('[data-detail-id]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = btn.getAttribute('data-detail-id');
        openDetailView(id);
      });
    });

    tableBody.querySelectorAll('tr[data-item-id]').forEach(row => {
      row.addEventListener('click', () => {
        const id = row.getAttribute('data-item-id');
        openDetailView(id);
      });
    });
  }

  // ========================================================================
  // CHUNK 3: FRAGMENT DETAIL & RELATIONSHIP VIEW CONTROLLER
  // ========================================================================
  function openDetailView(itemId) {
    const item = FORENSIC_ITEMS.find(i => i.id === itemId) || FORENSIC_ITEMS[0];

    // Populate Detail Header
    if (detailFilename) detailFilename.textContent = item.filename;
    if (detailFileIcon) detailFileIcon.setAttribute('data-icon', item.typeIcon);
    if (detailMeta) {
      detailMeta.innerHTML = `
        <span>ID: <strong class="forensic-mono" style="color: var(--accent-ai);">${item.id}</strong></span>
        <span>•</span>
        <span>Type: <strong>${item.typeName}</strong></span>
        <span>•</span>
        <span>Assembled: <strong class="forensic-mono">${item.blockCount.toLocaleString()} Blocks</strong></span>
        <span>•</span>
        <span>SHA-256: <span class="file-hash">${item.hash.substring(0, 16)}...</span></span>
      `;
    }

    // Status Badge: Pixel-identical to Chunk 2 table
    if (detailBadgeContainer) {
      detailBadgeContainer.innerHTML = `
        <span class="badge ${item.statusBadgeClass}">
          <span class="pulse-indicator" style="background-color: var(--status-${item.status});"></span>
          ${item.statusLabel}
        </span>
      `;
    }

    // Populate Left Column: Content Preview
    renderContentPreview(item);

    // Populate Right Column: Fragment Chain (ordered sequence)
    renderFragmentChain(item);

    // Populate Full-Width Confidence Breakdown
    renderConfidenceBreakdown(item);

    // Populate Quick Selector Dropdown
    if (detailFileSelector) {
      detailFileSelector.innerHTML = FORENSIC_ITEMS.map(f => 
        `<option value="${f.id}" ${f.id === item.id ? 'selected' : ''}>${f.filename} (${f.confidence.toFixed(1)}%)</option>`
      ).join('');
    }

    // Transition Views
    if (triageViewContainer) triageViewContainer.style.display = 'none';
    if (detailViewContainer) detailViewContainer.style.display = 'block';

    window.scrollTo({ top: 0, behavior: 'smooth' });

    if (typeof renderIcons === 'function') {
      renderIcons();
    }
  }

  function closeDetailView() {
    if (detailViewContainer) detailViewContainer.style.display = 'none';
    if (triageViewContainer) triageViewContainer.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Left Column Content Preview Renderer
  function renderContentPreview(item) {
    if (!detailPreviewViewport) return;

    if (detailPreviewTitle) {
      detailPreviewTitle.innerHTML = `
        <span data-icon="${item.typeIcon}" data-icon-size="16"></span>
        <span>Content Preview // ${item.typeName}</span>
      `;
    }

    if (item.type === 'document' && item.sampleText) {
      // Text / JSON / Log Preview (Monospace, scrollable, bounded)
      detailPreviewViewport.innerHTML = `
        <pre class="code-viewport">${escapeHtml(item.sampleText)}</pre>
      `;
    } else if (item.type === 'image') {
      // Image Preview (Inline rendered, max-width 100%)
      detailPreviewViewport.innerHTML = `
        <div class="image-preview-box">
          <svg class="image-preview-render" width="100%" height="220" viewBox="0 0 400 220" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="220" fill="#0B0F17" rx="6"/>
            <!-- Forensic Scan Grids -->
            <path d="M0 40h400M0 80h400M0 120h400M0 160h400M0 200h400" stroke="#1E293B" stroke-width="0.5"/>
            <path d="M40 0v220M80 0v220M120 0v220M160 0v220M200 0v220M240 0v220M280 0v220M320 0v220M360 0v220" stroke="#1E293B" stroke-width="0.5"/>
            <!-- Salvaged Vector Frame -->
            <circle cx="200" cy="110" r="50" stroke="${item.status === 'high' ? 'var(--status-high)' : 'var(--status-medium)'}" stroke-width="2" stroke-dasharray="4 2"/>
            <path d="M170 110h60M200 80v60" stroke="${item.status === 'high' ? 'var(--status-high)' : 'var(--status-medium)'}" stroke-width="1.5"/>
            <text x="200" y="175" fill="var(--text-secondary)" font-family="monospace" font-size="11" text-anchor="middle">
              SURVEILLANCE FRAME [RECONSTRUCTED]
            </text>
            <text x="200" y="195" fill="var(--accent-ai)" font-family="monospace" font-size="10" text-anchor="middle">
              ${item.inferredDetails ? item.inferredDetails.dimensions : '1920x1080'} • ${item.confidence.toFixed(1)}% PARITY
            </text>
          </svg>

          <div class="metadata-grid" style="width: 100%;">
            <div class="metadata-item">
              <span class="metadata-label">Dimensions</span>
              <span class="metadata-value">${item.inferredDetails ? item.inferredDetails.dimensions : 'Unknown'}</span>
            </div>
            <div class="metadata-item">
              <span class="metadata-label">Color Space</span>
              <span class="metadata-value">${item.inferredDetails ? item.inferredDetails.colorSpace : 'sRGB'}</span>
            </div>
          </div>
        </div>
      `;
    } else if (item.type === 'database') {
      // Database Preview (Inferred metadata, table names, schema in monospace)
      detailPreviewViewport.innerHTML = `
        <div class="metadata-view-container">
          <div class="meta-notice-banner">
            <span data-icon="info" data-icon-size="16" style="color: var(--accent-ai);"></span>
            <span>No binary graphical preview. Inferred structured schema and WAL journal state rendered below:</span>
          </div>

          <div class="metadata-grid">
            <div class="metadata-item">
              <span class="metadata-label">Inferred Format</span>
              <span class="metadata-value">${item.inferredDetails.format}</span>
            </div>
            <div class="metadata-item">
              <span class="metadata-label">Total Extracted Records</span>
              <span class="metadata-value">${item.inferredDetails.records}</span>
            </div>
            <div class="metadata-item">
              <span class="metadata-label">Page Size</span>
              <span class="metadata-value">${item.inferredDetails.pageSize}</span>
            </div>
            <div class="metadata-item">
              <span class="metadata-label">WAL Status</span>
              <span class="metadata-value" style="color: var(--status-high);">${item.inferredDetails.walStatus}</span>
            </div>
          </div>

          <div>
            <div class="form-label" style="margin-bottom: var(--space-8);">Reconstructed DDL Schema (.sql)</div>
            <pre class="code-viewport">${escapeHtml(item.schemaText || '-- No schema extracted')}</pre>
          </div>
        </div>
      `;
    } else {
      // Binary / Executable / Slack Space Preview
      detailPreviewViewport.innerHTML = `
        <div class="metadata-view-container">
          <div class="meta-notice-banner">
            <span data-icon="info" data-icon-size="16" style="color: var(--status-${item.status});"></span>
            <span>${item.meta} — Parsed header inspection and byte telemetry:</span>
          </div>

          <div class="metadata-grid">
            <div class="metadata-item">
              <span class="metadata-label">Inferred Architecture</span>
              <span class="metadata-value">${item.inferredDetails ? (item.inferredDetails.architecture || item.inferredDetails.format) : 'Raw Storage Stream'}</span>
            </div>
            <div class="metadata-item">
              <span class="metadata-label">Damage Telemetry</span>
              <span class="metadata-value" style="color: var(--status-low);">${item.inferredDetails ? (item.inferredDetails.damage || item.inferredDetails.warning || 'Zero-fill') : 'Corrupted'}</span>
            </div>
          </div>

          <div>
            <div class="form-label" style="margin-bottom: var(--space-8);">Extracted Header Disassembly / Raw Stream</div>
            <pre class="code-viewport">${escapeHtml(item.sampleText || '00000000: 00 00 00 00 00 00 00 00 ... [UNALLOCATED SECTOR]')}</pre>
          </div>
        </div>
      `;
    }
  }

  // Right Column Fragment Chain Renderer (Sequence order & Block chips)
  function renderFragmentChain(item) {
    if (!detailChainContainer) return;
    const fragments = item.fragments || [];

    if (detailChainCount) {
      detailChainCount.textContent = `${fragments.length} Assembled Chunks`;
    }

    detailChainContainer.innerHTML = fragments.map((frag, idx) => {
      const isLast = idx === fragments.length - 1;
      return `
        <div class="chain-step">
          <div class="block-chip" tabindex="0">
            <!-- Left: Dot + Seq + Monospace Block ID -->
            <div class="chip-identity">
              <span class="chip-status-dot ${frag.status}"></span>
              <span class="chip-seq-num">#${frag.seq}</span>
              <span class="chip-block-id">${frag.blockId}</span>
            </div>

            <!-- Right: Status Tag -->
            <span class="chip-tag ${frag.status}">${frag.status.toUpperCase()}</span>

            <!-- Tooltip with raw byte offset & size in monospace -->
            <div class="chip-tooltip">
              <div class="tooltip-line">Block: <strong>${frag.blockId}</strong></div>
              <div class="tooltip-line">Offset: <strong>${frag.offset}</strong></div>
              <div class="tooltip-line">Size: <strong>${frag.size}</strong></div>
              <div class="tooltip-line">Condition: <strong>${frag.label}</strong></div>
            </div>
          </div>

          <!-- Thin connecting sequence line -->
          ${!isLast ? '<div class="chain-connector"></div>' : ''}
        </div>
      `;
    }).join('');
  }

  // Full-width Confidence Breakdown Renderer
  function renderConfidenceBreakdown(item) {
    if (!detailBreakdownList) return;
    const factors = item.confidenceFactors || [];

    detailBreakdownList.innerHTML = factors.map(factor => `
      <div class="breakdown-item">
        <div class="breakdown-icon-box" style="color: ${factor.iconColor};">
          <span data-icon="${factor.icon}" data-icon-size="16"></span>
        </div>
        <div class="breakdown-content">
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--space-8);">
            <span class="breakdown-label">${factor.label}</span>
            <span class="breakdown-metric">${factor.metric}</span>
          </div>
          <p class="breakdown-desc">${factor.desc}</p>
        </div>
      </div>
    `).join('');
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // Detail View Event Handlers
  if (detailBackBtn) {
    detailBackBtn.addEventListener('click', closeDetailView);
  }

  if (detailFileSelector) {
    detailFileSelector.addEventListener('change', (e) => {
      openDetailView(e.target.value);
    });
  }

  // Event Listeners for Filters & Sorting (Chunk 2)
  if (searchInput) searchInput.addEventListener('input', renderTable);
  if (typeFilter) typeFilter.addEventListener('change', renderTable);
  if (statusFilter) statusFilter.addEventListener('change', renderTable);
  if (sortSelect) sortSelect.addEventListener('change', renderTable);

  // Initial Table Render
  renderTable();

  // Reset Filters button
  const resetBtn = document.getElementById('reset-filters-btn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      if (typeFilter) typeFilter.value = 'all';
      if (statusFilter) statusFilter.value = 'all';
      if (sortSelect) sortSelect.value = 'confidence-desc';
      renderTable();
    });
  }

  // Start a Scan CTA Button (In Empty State)
  const startScanBtn = document.getElementById('start-scan-btn');
  if (startScanBtn) {
    startScanBtn.addEventListener('click', () => {
      const scanBtn = document.querySelector('.state-btn[data-state="scanning"]');
      if (scanBtn) scanBtn.click();
      setTimeout(() => {
        const popBtn = document.querySelector('.state-btn[data-state="populated"]');
        if (popBtn) popBtn.click();
      }, 2500);
    });
  }
});
