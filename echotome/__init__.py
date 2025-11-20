"""
Echotome — Audio encryption + sigil generator core.

Designed for use inside Claude Code, ABX-Core style:
modular, deterministic, and pipeline-friendly.
"""

from .config import EchotomeConfig, EchotomeResult
from .pipeline import run_echotome

__all__ = [
    "EchotomeConfig",
    "EchotomeResult",
    "run_echotome",
]
