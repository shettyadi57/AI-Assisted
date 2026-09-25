"""
Intelligent Fragment Reconstruction — FastAPI Application (Phase 0)

Entry point for the backend. Registers routers, initializes the database,
configures CORS, and exposes /api/health and /api/phase as the only
live endpoints in Phase 0.

All other routes return 404 or FeatureUnavailableResponse until their
phase is implemented.
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import init_db
from schemas import FeatureUnavailableResponse, HealthResponse, PhaseInfo

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Phase manifest — single source of truth for what is available
# ---------------------------------------------------------------------------
CURRENT_PHASE = 0

PHASE_MANIFEST: dict[int, str] = {
    0: "Scaffolding — interfaces, schema, and project structure",
    1: "Evidence ingest — upload/register evidence files, SHA-256 on ingest",
    2: "Fragment identification — scan evidence, identify fragment boundaries",
    3: "Relationship scoring — score fragment edges, 5-signal confidence model",
    4: "Reconstruction candidates — graph traversal, candidate assembly",
    5: "Investigator workflow — accept/reject UI, audit log",
    6: "Structural validation — format-aware per-fragment and assembly checks",
    7: "Provenance export — full output-byte → fragment → edge → decision trail",
    8: "Reporting — candidate summary reports, audit log export",
    9: "ML integration — FragmentClassifier / RelationshipScorer implementation",
    10: "Hardening — performance, error handling, packaging",
}

FEATURES_AVAILABLE: list[str] = [
    "health_check",
    "phase_info",
    "signature_registry_query",
    "integrity_hashing",
]

FEATURES_COMING: dict[str, int] = {
    "evidence_ingest": 1,
    "fragment_identification": 2,
    "relationship_scoring": 3,
    "reconstruction_candidates": 4,
    "investigator_accept_reject": 5,
    "structural_validation": 6,
    "provenance_export": 7,
    "reporting": 8,
    "ml_classification": 9,
}


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("IFR backend starting", phase=CURRENT_PHASE)
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("IFR backend shutting down")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Intelligent Fragment Reconstruction API",
    description=(
        "Backend for the IFR forensic analysis tool. "
        "Phase 0: Scaffolding — only /api/health and /api/phase are live."
    ),
    version=f"0.{CURRENT_PHASE}.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS — dev-only: allow localhost React dev server
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default dev port
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Phase 0 live endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """
    Returns system health and the current phase manifest.

    This endpoint is always live regardless of phase.
    The frontend uses it to determine which features to enable/disable.
    """
    # Quick DB connectivity check
    db_ok = True
    try:
        from database import engine
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db_connected=db_ok,
        phase=PhaseInfo(
            current_phase=CURRENT_PHASE,
            phase_label=PHASE_MANIFEST[CURRENT_PHASE],
            features_available=FEATURES_AVAILABLE,
            features_coming=FEATURES_COMING,
        ),
        timestamp=datetime.now(tz=timezone.utc),
    )


@app.get("/api/phase", response_model=PhaseInfo, tags=["System"])
async def phase_info() -> PhaseInfo:
    """Returns the current phase manifest without the DB connectivity check."""
    return PhaseInfo(
        current_phase=CURRENT_PHASE,
        phase_label=PHASE_MANIFEST[CURRENT_PHASE],
        features_available=FEATURES_AVAILABLE,
        features_coming=FEATURES_COMING,
    )


@app.get(
    "/api/signatures",
    tags=["Analysis — Phase 0"],
    summary="List registered file format signatures",
)
async def list_signatures() -> dict:
    """
    Returns the signature registry: all known file format magic-byte patterns.
    This is live in Phase 0 because the signature_registry module is complete.
    """
    from analysis.signature_registry import SIGNATURE_REGISTRY

    return {
        "count": len(SIGNATURE_REGISTRY),
        "signatures": [
            {
                "format_id": sig.format_id,
                "display_name": sig.display_name,
                "header_magic_hex": sig.header_magic.hex(" ").upper(),
                "footer_magic_hex": sig.footer_magic.hex(" ").upper() if sig.footer_magic else None,
                "header_offset": sig.header_offset,
                "mime_type": sig.mime_type,
                "notes": sig.notes,
            }
            for sig in SIGNATURE_REGISTRY
        ],
    }


# ---------------------------------------------------------------------------
# Catch-all for not-yet-implemented Phase N endpoints
# This converts FeatureNotAvailableError raised by analysis modules into
# a clean 503 response rather than a 500.
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def feature_not_available_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    from analysis.fragment_analyzer import FeatureNotAvailableError

    if isinstance(exc, FeatureNotAvailableError):
        return JSONResponse(
            status_code=503,
            content=FeatureUnavailableResponse(
                available=False,
                feature=exc.feature,
                coming_in_phase=exc.coming_in_phase,
                message=(
                    f"'{exc.feature}' is not yet available in Phase {CURRENT_PHASE}. "
                    f"It will be implemented in Phase {exc.coming_in_phase}."
                ),
            ).model_dump(),
        )
    raise exc
