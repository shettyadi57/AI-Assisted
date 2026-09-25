"""
Backend Configuration Settings
"""

from __future__ import annotations

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "reconstruct.db"))
MIGRATIONS_DIR = BASE_DIR / "migrations"

# API & Server
API_V1_PREFIX = "/api/v1"
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
