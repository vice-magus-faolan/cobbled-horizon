"""Shared override allowlist; 26.2 retains its manual permission bootstrap.

The two group-policy paths are admitted for archive compatibility and synthetic
regressions. This line does not generate or package a production permission seed.
"""
from __future__ import annotations

SEED_SOURCE = "config/cobbled-horizon/luckperms-groups.json"
SEED_IMPORT = SEED_SOURCE + ".gz"
SEED_PATHS = {SEED_SOURCE, SEED_IMPORT}


def is_pack_override(relative: str) -> bool:
    """Admit only the two policy encodings, never LuckPerms runtime state."""
    if relative.startswith("config/cobbled-horizon/"):
        return relative in SEED_PATHS
    return relative.startswith(("config/", "squaremap/")) and not relative.startswith("config/luckperms/")
