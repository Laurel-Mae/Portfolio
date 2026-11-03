"""ASGI entrypoint for Uvicorn, Render and Vercel Python Functions."""
from __future__ import annotations
import sys
import types
from pathlib import Path

# When deploying server/ as the project root, expose it as the 'server' package.
# Development from the repository root already provides this package normally.
HERE = Path(__file__).resolve().parent
if 'server' not in sys.modules:
    package = types.ModuleType('server')
    package.__path__ = [str(HERE)]
    sys.modules['server'] = package

from server.app import create_app

app = create_app()
