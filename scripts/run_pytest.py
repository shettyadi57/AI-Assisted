"""
Cross-platform helper to invoke pytest using the local virtual environment or active Python.
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Check for backend venv pytest
venv_pytest_win = ROOT / "backend" / ".venv" / "Scripts" / "pytest.exe"
venv_pytest_unix = ROOT / "backend" / ".venv" / "bin" / "pytest"

args = sys.argv[1:] if len(sys.argv) > 1 else ["core/tests", "backend/tests"]

if venv_pytest_win.exists():
    cmd = [str(venv_pytest_win)] + args
elif venv_pytest_unix.exists():
    cmd = [str(venv_pytest_unix)] + args
else:
    cmd = [sys.executable, "-m", "pytest"] + args

res = subprocess.run(cmd, cwd=str(ROOT))
sys.exit(res.returncode)
