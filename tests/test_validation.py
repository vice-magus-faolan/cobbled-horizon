"""Regression tests for Cobbled Horizon validation tooling."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


check_pack = load_script("check_pack")
readiness = load_script("check_target_readiness")
validate_mrpack = load_script("validate_mrpack")


class PackSourceTests(unittest.TestCase):
    def test_repository_passes_source_validation(self) -> None:
        errors, summary = check_pack.validate()
        self.assertEqual([], errors)
        self.assertEqual(20, summary.baseline_selected)
        self.assertEqual(4, summary.baseline_dependencies)
        self.assertEqual(3, summary.staged_selected)
        self.assertEqual(1, summary.staged_dependencies)
        self.assertEqual(5, summary.future_candidates)
        self.assertGreater(
            summary.indexed_files,
            summary.baseline_selected + summary.baseline_dependencies,
        )

    def test_safe_relative_paths(self) -> None:
        self.assertTrue(check_pack.safe_relative("mods/lithium.pw.toml"))
        self.assertFalse(check_pack.safe_relative("../key.pem"))
        self.assertFalse(check_pack.safe_relative("/etc/passwd"))
        self.assertFalse(check_pack.safe_relative("mods\\bad.jar"))


class ReadinessTests(unittest.TestCase):
    def test_exact_target_and_loader_are_required(self) -> None:
        versions = [
            {"game_versions": ["26.2"], "loaders": ["fabric"], "version_type": "release"},
            {"game_versions": ["26.3"], "loaders": ["neoforge"], "version_type": "release"},
            {"game_versions": ["26.3"], "loaders": ["fabric"], "version_type": "beta"},
        ]
        self.assertEqual(1, len(readiness.compatible_versions(versions, "26.3", False)))
        self.assertEqual([], readiness.compatible_versions(versions, "26.3", True))


class MrpackTests(unittest.TestCase):
    def test_safe_relative_paths(self) -> None:
        self.assertTrue(validate_mrpack.safe_relative("config/example.json"))
        self.assertFalse(validate_mrpack.safe_relative("../../escape"))
        self.assertFalse(validate_mrpack.safe_relative("C:\\escape"))

    def test_invalid_hash_is_rejected(self) -> None:
        entry = {
            "path": "mods/example.jar",
            "hashes": {"sha1": "bad", "sha512": "bad"},
            "fileSize": 1,
            "downloads": ["https://example.invalid/example.jar"],
            "env": {"server": "required"},
        }
        errors: list[str] = []
        path, environment = validate_mrpack.validate_entry(entry, 0, errors)
        self.assertEqual("mods/example.jar", path)
        self.assertEqual("required", environment)
        self.assertEqual(2, len(errors))


if __name__ == "__main__":
    unittest.main()
