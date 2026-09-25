# Reconstruct // Forensic File Fragment Reconstruction Workbench

> **Phase 0 — Project Skeleton & Architecture Scaffolding**  
> An investigator-grade digital forensics workbench designed to triage, evaluate, and reconstruct file fragments carved from damaged, deleted, and slack storage media. Formulates fragment ordering as a scored graph-construction problem with transparent, inspectable evidence per edge.
>
> ⚠️ **PORTFOLIO / PROTOTYPE TOOL — NOT LEGALLY ADMISSIBLE**

---

## 1. Prior Art & Technical Differentiation

### Prior Art & Shared Limitations

In digital forensics, file carving is the process of extracting files from raw disk images or unallocated space without relying on filesystem metadata:

| Tool | Approach | Limitation |
|------|----------|------------|
| **Scalpel** | Header/footer signature carving | Finds fragments; cannot explain *why* they were ordered or assess ordering confidence |
| **PhotoRec** | Broad-format batch carving | Produces outputs, not reasoning — no fragment relationship transparency |
| **bulk_extractor** | Byte-level feature scanning | Surface-level feature tagging; no structural validation of fragment sequences |

**Shared Blind Spot:** None of these tools expose *reconstruction reasoning* — why fragments were ordered in a particular sequence, what the confidence of each edge is and why, or allow a human investigator to accept or reject an individual fragment relationship before the file is finalized. They are **batch tools, not investigation workbenches.**

---

### Our Approach: Transparent Graph Scored Reconstruction

Reconstruct treats file fragment reassembly as a **scored graph-construction problem** with inspectable, decomposed evidence per edge:

```
Fragment A ──[edge: 0.91]──► Fragment B ──[edge: 0.74]──► Fragment C
             │                             │
             ├─ Signature match: ✓          ├─ Signature match: ✓
             ├─ Offset continuity: ✓        ├─ Offset continuity: ~
             ├─ Structural validity: ✓      ├─ Structural validity: ✓
             └─ Entropy profile: ✓          └─ Entropy profile: ✗
```

Every candidate edge between fragments is **scored on five independent axes of evidence**, surfaced to the investigator as human-readable factors rather than an opaque black box:
1. **Signature Match:** Magic byte headers, chunk identifiers, and marker consistency.
2. **Offset Continuity:** Sector proximity and physical media sequence alignment.
3. **Structural Validity:** Format-internal structural parser validation (e.g. JPEG Huffman streams, PNG CRC-32, PDF xref tables).
4. **Entropy Profile Compatibility:** Shannon entropy transitions across fragment boundaries.
5. **Contradiction Count:** Penalization of conflicting markers or impossible length offsets.

### Technical Difference Summary

| Dimension | Batch Tools (Scalpel / PhotoRec) | Reconstruct Workbench |
|-----------|----------------------------------|-----------------------|
| **Fragment Ordering Model** | Heuristic / format-signature-driven | Candidate relationship scoring (graph edges with multi-factor evidence) |
| **Confidence Communication** | None, or opaque single percentage | Decomposed per-factor evidence: signature, continuity, structure, entropy |
| **Investigator Control** | None — batch accept-all | Accept / reject individual fragment relationships before file finalization |
| **Audit Trail & Provenance** | None | Full provenance: output byte → source fragment → edge evidence → investigator decision |
| **Workflow Model** | Automated pipeline, inspect output | **Human-in-the-loop investigation workbench** |

---

## 2. Monorepo Layout

```
/
├── frontend/               # React 18 + TypeScript + Vite forensics workbench
│   ├── src/
│   │   ├── tokens.ts       # Design tokens (6 forensic states, typography, monospace)
│   │   ├── styles/         # CSS variables (tokens.css) & forensic styling (index.css)
│   │   ├── context/        # InvestigationContext (global state, health probe)
│   │   ├── components/     # AppShell (topbar + left sidebar) & StatusBadge
│   │   ├── pages/          # 7 Pages per Spec Layout (Overview, Evidence, Fragments,
│   │   │                   # Reconstruction, Validation, Reports, Settings)
│   │   └── tests/          # Vitest test suite (tokens.test.ts)
│   └── package.json
│
├── backend/                # FastAPI application
│   ├── main.py             # App entrypoint, CORS, versioned /api/v1 routes
│   ├── config.py           # Configuration (CORS, database path, API prefix)
│   ├── database.py         # SQLite connection & migration runner
│   ├── schemas.py          # Pydantic response models
│   ├── routers/            # Health + 5 Pipeline Stage Skeletons (returning HTTP 501):
│   │   ├── health.py       # GET /health & GET /api/v1/health (200 OK)
│   │   ├── discovery.py    # POST/GET /api/v1/discovery/... (Phase 1)
│   │   ├── analysis.py     # POST/GET /api/v1/analysis/... (Phase 2)
│   │   ├── linking.py      # POST/GET /api/v1/linking/... (Phase 3)
│   │   ├── reconstruction.py # POST/GET /api/v1/reconstruction/... (Phase 4)
│   │   └── export.py       # POST/GET /api/v1/export/... (Phase 7)
│   ├── migrations/         # Raw SQL migrations (001_initial_schema.sql)
│   └── tests/              # Backend test suite (test_backend.py)
│
├── core/                   # Pure-Python analysis modules (NO FastAPI imports)
│   ├── integrity_analyzer.py    # SHA-256 evidence hashing & stream verification interface
│   ├── signature_registry.py    # Magic headers, trailers, & format scanning interface
│   ├── fragment_analyzer.py     # Shannon entropy profiling & boundary detection interface
│   ├── relationship_engine.py   # Multi-factor edge scoring interface
│   ├── reconstruction_engine.py # Graph traversal & bit-level provenance byte-mapping interface
│   ├── validators/              # Format structural validators (PDF, JPEG, PNG, ZIP)
│   ├── ml/                      # ML relationship scorer interface (Sections 12 & 21)
│   └── tests/                   # Pytest test suite (test_core_interfaces.py)
│
├── sample-data/            # Synthetic forensic test fragments (read-only)
│   ├── README.md           # Dataset documentation
│   ├── manifest.json       # SHA-256 hashes and ground-truth sequence
│   ├── fragment_001_jpeg_header.bin
│   ├── fragment_002_jpeg_entropy.bin
│   ├── fragment_003_jpeg_eoi.bin
│   └── fragment_004_corrupted_slack.bin
│
├── docs/                   # Documentation & prior art
│   └── PRIOR_ART.md        # Comprehensive technical differentiation dossier
│
├── migrations/             # Top-level mirror of SQLite migrations
│   └── 001_initial_schema.sql
│
├── package.json            # Unified monorepo scripts
├── Makefile                # Standard make test / dev commands
└── pytest.ini              # Pytest configuration
```

---

## 3. How to Run

### Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- **Node.js 18+** & **npm 9+**

---

### Running the Backend (FastAPI)

```bash
# 1. Activate Python virtual environment (if not already activated)
# Windows:
backend\.venv\Scripts\activate
# macOS/Linux:
source backend/.venv/bin/activate

# 2. Run the FastAPI dev server
python -m uvicorn backend.main:app --reload --port 8000
# or from root:
npm run dev:backend
```

Live backend endpoints:
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/api/v1/health`
- **Discovery (Phase 1 Skeleton):** `POST http://localhost:8000/api/v1/discovery/ingest` (Returns HTTP 501)
- **Analysis (Phase 2 Skeleton):** `POST http://localhost:8000/api/v1/analysis/fragments` (Returns HTTP 501)
- **Linking (Phase 3 Skeleton):** `POST http://localhost:8000/api/v1/linking/score` (Returns HTTP 501)
- **Reconstruction (Phase 4 Skeleton):** `POST http://localhost:8000/api/v1/reconstruction/candidates` (Returns HTTP 501)
- **Export (Phase 7 Skeleton):** `POST http://localhost:8000/api/v1/export/provenance` (Returns HTTP 501)

---

### Running the Frontend (React + Vite)

```bash
# 1. Navigate to frontend (or run via root script)
cd frontend
npm run dev

# or directly from monorepo root:
npm run dev:frontend
```

Open your browser to:
- **Forensic Workbench App:** `http://localhost:5173`

The Vite development server automatically proxies `/api/*` requests to the FastAPI backend at `localhost:8000`.

---

### Running Tests

Run the complete monorepo test suite with a single command:

```bash
# Run both /core (pytest) and /frontend (vitest) tests:
npm test

# Run all test suites including backend routes:
npm run test:all

# Or using Make:
make test
```

#### Running Individual Test Suites:

```bash
# Run /core pure-Python interface tests:
npm run test:core
# or directly:
python -m pytest core/tests -v

# Run /frontend Vitest token and shell tests:
npm run test:frontend
# or directly:
cd frontend && npm test

# Run /backend FastAPI route and migration tests:
npm run test:backend
# or directly:
python -m pytest backend/tests -v
```

---

## 4. SQLite Schema (Inspectable SQL Migrations)

All database tables are defined as raw SQL migrations in `backend/migrations/001_initial_schema.sql` (no opaque ORM magic):

1. **`evidence`**: Raw ingested media (read-only, SHA-256 hashed on ingest per Section 20).
2. **`signatures`**: Format signatures, category classification, magic header/trailer bytes.
3. **`fragments`**: Carved contiguous byte blocks with offsets, SHA-256 hash, entropy, and forensic status.
4. **`candidates`**: Proposed file reconstruction assemblies with composite scores and reconstructed SHA-256 hash.
5. **`candidate_fragments`**: Ordered sequence of fragments in a candidate with edge evidence and investigator accept/reject decision.
6. **`validation_results`**: Structural format validation outputs and structural hash.
7. **`audit_log`**: Tamper-evident chain of custody log with cryptographic linkage (`prev_state_hash` ➔ `entry_hash`).

To manually inspect or initialize the SQLite database:
```bash
python -c "import sqlite3; con = sqlite3.connect('reconstruct.db'); con.executescript(open('backend/migrations/001_initial_schema.sql').read()); print('Initialized SQLite tables successfully!')"
```

---

## 5. Non-Negotiable Forensic Rules

Every component and subsequent phase strictly adheres to the following rules:

1. **No Fabricated Results:** All scores, metrics, and byte maps originate from real computation or clearly-labeled sample fixtures.
2. **Explainable Confidence:** Every edge score breaks down into its constituent signals (signature, offset, structure, entropy, contradictions).
3. **Evidence is Read-Only:** Ingested evidence is hashed immediately and stored as read-only media; all intermediate artifacts write to derived storage.
4. **Six Strict Forensic States:** `CONFIRMED`, `INFERRED`, `UNCERTAIN`, `MISSING`, `CORRUPTED`, `DUPLICATE` — never collapsed into a binary or generic state.
5. **Phase-Gated Skeletons (HTTP 501):** Features not yet implemented return HTTP 501 naming their phase, never fake success responses.
6. **Mandatory Human Verification:** Candidate files are never finalized without an explicit human investigator decision logged to the audit log.
7. **Permanent Legal Disclaimer:** Visible across all UI views and API responses: *"Portfolio / prototype tool. Not legally admissible."*
