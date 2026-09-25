"""
pytest configuration for the IFR backend.
Adds the backend directory to sys.path so modules import without packages.
"""
import sys
from pathlib import Path

# Add backend/ to path so `from analysis.integrity import ...` works
sys.path.insert(0, str(Path(__file__).parent))
