"""Backend entrypoint compatible with TripStar-style gunicorn invocation.

This module makes the top-level `app` importable as
`backend.app.api.main:app` while reusing the existing application
package at the repository root (`app`). It adjusts `sys.path`
so the original `app` package is discoverable from the new
`backend` package layout.
"""
import sys
from pathlib import Path

# Ensure repository root (one level up from backend/) is on sys.path
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Optional: load backend/.env if present
env_path = REPO_ROOT / "backend" / ".env"
if env_path.exists():
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=str(env_path))

# Import the real FastAPI `app` from the original package
try:
    from app.main import app  # type: ignore
except Exception as exc:  # pragma: no cover - import-time safety
    raise RuntimeError("Failed to import application from app.main") from exc

# Expose `app` for WSGI/ASGI servers
__all__ = ["app"]
