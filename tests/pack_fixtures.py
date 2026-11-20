"""Shared repository root and script loader for pack-tool regressions."""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import textwrap

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def workflow_script(step: str) -> str:
    """Execute a shipped run block without duplicating its publication logic."""
    workflow = (ROOT / ".github/workflows/validate.yml").read_text()
    block = workflow.split("      - name: " + step + "\n", 1)[1]
    return textwrap.dedent(block.split("run: |\n", 1)[1].split("\n      - name:", 1)[0])
