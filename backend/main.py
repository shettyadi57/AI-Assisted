"""
Reconstruct Forensics Workbench — FastAPI Application (Phase 0)

Skeleton API exposing:
- /health and /api/v1/health (200 OK)
- Versioned pipeline stage skeletons returning HTTP 501 (Not Implemented):
  - /api/v1/discovery/...       (Phase 1)
  - /api/v1/analysis/...        (Phase 2)
  - /api/v1/linking/...         (Phase 3)
  - /api/v1/reconstruction/...  (Phase 4)
  - /api/v1/export/...          (Phase 7)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import API_V1_PREFIX, CORS_ORIGINS
from backend.database import apply_migrations
from backend.routers import (
    analysis,
    discovery,
    export,
    health,
    linking,
    reconstruction,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reconstruct.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize database and schema on startup."""
    logger.info("Initializing Reconstruct SQLite schema...")
    try:
        applied = apply_migrations()
        logger.info("Successfully applied migrations: %s", applied)
    except Exception as e:
        logger.error("Failed to apply database migrations: %s", e)
    yield
    logger.info("Reconstruct backend shutting down.")


app = FastAPI(
    title="Reconstruct Forensics Workbench API",
    description=(
        "Forensic File Fragment Reconstruction API.\n\n"
        "Phase 0: Architecture Scaffolding. Pipeline stage endpoints return HTTP 501 "
        "with target phase specification."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# CORS configuration for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Unversioned top-level health check
app.include_router(health.router, tags=["Health"])

# Versioned /api/v1 routes
app.include_router(health.router, prefix=API_V1_PREFIX)
app.include_router(discovery.router, prefix=API_V1_PREFIX)
app.include_router(analysis.router, prefix=API_V1_PREFIX)
app.include_router(linking.router, prefix=API_V1_PREFIX)
app.include_router(reconstruction.router, prefix=API_V1_PREFIX)
app.include_router(export.router, prefix=API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
