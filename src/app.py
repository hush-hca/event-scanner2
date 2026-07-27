"""Vercel FastAPI auto-discovery entrypoint.

Vercel imports this as ``src.app`` from the repository root, so use the
root-qualified package path rather than the local-development PYTHONPATH.
"""

from src.event_scanner.main import app

__all__ = ["app"]
