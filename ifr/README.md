# Intelligent Fragment Reconstruction

**A real digital forensics tool** — not a demo. Fragment ordering as a scored
graph-construction problem with transparent, inspectable evidence per edge.

> **Portfolio / prototype tool. Not legally admissible.**

---

## What makes this different from Scalpel / PhotoRec / bulk\_extractor

| Dimension | Batch Tools | IFR |
|---|---|---|
| Fragment ordering | Heuristic / signature-driven | Scored graph edges, 5-signal evidence |
| Confidence | None, or opaque % | Decomposed: header match, offset continuity, structural validity, entropy, contradiction count |
| Investigator control | None — batch accept-all | Accept / reject individual edges before finalization |
| Audit trail | None | Full provenance: output byte → fragment → edge → decision |
| Workflow | Automated pipeline | Human-in-the-loop investigation workbench |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite |
| Backend | Python 3.11 + FastAPI + uvicorn |
| Database | SQLite (via SQLAlchemy async + aiosqlite) |
| Analysis core | Pure Python modules, independently testable |
| ML interface | Abstract ABC — stub in Phase 0–8, real in Phase 9 |

---

## Project Structure

```
ifr/
├── backend/
│   ├── main.py                      # FastAPI app, phase manifest
│   ├── database.py                  # SQLite async engine
│   ├── models.py                    # SQLAlchemy ORM (all tables)
│   ├── schemas.py                   # Pydantic request/response schemas
│   ├── conftest.py                  # pytest path setup
│   ├── requirements.txt
│   ├── analysis/
│   │   ├── integrity.py             # SHA-256 — COMPLETE (Phase 0)
│   │   ├── signature_registry.py    # 18 format signatures — COMPLETE (Phase 0)
│   │   ├── confidence_analyzer.py   # 5-signal model — FORMULA COMPLETE (Phase 0)
│   │   ├── fragment_analyzer.py     # Interface — Phase 2
│   │   ├── relationship_engine.py   # Interface — Phase 3
│   │   ├── validators.py            # Interface — Phase 6
│   │   └── reconstruction_engine.py # Interface — Phase 4
│   ├── services/
│   │   └── classifier_interface.py  # ML ABC + stubs — COMPLETE (Phase 0)
│   └── tests/
│       └── test_phase0.py           # 27 unit tests — all pass
├── frontend/
│   ├── src/
│   │   ├── types/index.ts           # TypeScript types mirroring all schemas
│   │   ├── styles/index.css         # Forensics design system
│   │   ├── components/layout/
│   │   │   └── AppShell.tsx         # Top bar + sidebar + main
│   │   ├── pages/
│   │   │   └── PhaseZeroPage.tsx    # System map + live data
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts               # /api proxy → localhost:8000
└── data/
    ├── evidence/                    # Read-only evidence storage (Phase 1)
    └── derived/                     # Analysis outputs (Phase 1+)
```

---

## How to Run (Phase 0)

### Backend

```bash
cd ifr/backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000
```

Live endpoints:
- `GET http://localhost:8000/api/health`
- `GET http://localhost:8000/api/phase`
- `GET http://localhost:8000/api/signatures`
- `GET http://localhost:8000/api/docs` (Swagger UI)

### Run Tests

```bash
cd ifr/backend
pytest tests/test_phase0.py -v
```

### Frontend

```bash
cd ifr/frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

The Vite dev server proxies `/api/*` to `localhost:8000` automatically.

---

## Non-Negotiable Rules (enforced in every phase)

1. **No fabricated results.** Every number comes from real computation or clearly-labeled sample data.
2. **Confidence scores are explainable.** Five independent signals stored and displayed alongside every composite score.
3. **Evidence is read-only.** Hashed on ingest; all analysis writes to `data/derived/`.
4. **Six status states.** `CONFIRMED / INFERRED / UNCERTAIN / MISSING / CORRUPTED / DUPLICATE` — never collapsed to a single color.
5. **Coming in Phase N.** Features not yet implemented are labeled, not stubbed with fake behavior.
6. **Human accept/reject required.** No candidate is finalized without an investigator decision. Rejections append to audit log.
7. **Not legally admissible.** Stated in the UI permanently.
