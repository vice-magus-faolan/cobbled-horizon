"""Regression tests for Cobbled Horizon validation tooling."""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import tomllib
import unittest
import warnings
import zipfile
from unittest.mock import patch

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
        self.assertEqual(23, summary.baseline_selected)
        self.assertEqual(5, summary.baseline_dependencies)
        self.assertEqual(4, summary.staged_selected)
        self.assertEqual(1, summary.staged_dependencies)
        self.assertEqual(6, summary.future_candidates)
        self.assertGreater(
            summary.indexed_files,
            summary.baseline_selected + summary.baseline_dependencies,
        )

    def test_friends_and_family_policy_is_pinned(self) -> None:
        waystones = json.loads((ROOT / "config/sswaystones.json").read_text())
        self.assertEqual(2, waystones["xp_cost"])
        self.assertEqual(2_147_483_647, waystones["cross_dimension_xp_cost"])
        self.assertEqual(30, waystones["combat_cooldown"])
        self.assertIs(True, waystones["pve_combat"])
        self.assertEqual(10, waystones["waystone_limit"])

        backups = json.loads((ROOT / "config/justenoughbackups.json").read_text())
        self.assertEqual(4, backups["commandPermissionLevel"])

        resource_pack = json.loads((ROOT / "config/polymer/resource-pack.json").read_text())
        self.assertEqual([], resource_pack["include_zips"])

        properties = {}
        for line in (ROOT / "server.properties.example").read_text().splitlines():
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                properties[key] = value
        self.assertEqual("true", properties["pvp"])
        self.assertEqual("16", properties["spawn-protection"])
        self.assertEqual("4", properties["op-permission-level"])

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
    def setUp(self) -> None:
        pack = tomllib.loads((ROOT / "pack.toml").read_text())
        self.index = {
            "versionId": pack["version"],
            "formatVersion": 1,
            "game": "minecraft",
            "dependencies": {"minecraft": pack["versions"]["minecraft"], "fabric-loader": pack["versions"]["fabric"]},
            "files": [],
        }
        for path in sorted((ROOT / "mods").glob("*.pw.toml")):
            mod = tomllib.loads(path.read_text())
            self.index["files"].append({
                "path": "mods/" + mod["filename"],
                "hashes": {"sha1": "0" * 40, "sha512": mod["download"]["hash"]},
                "fileSize": 1,
                "downloads": [mod["download"]["url"]],
                "env": {"server": "required", "client": "unsupported"},
            })
        self.overrides = {
            "overrides/" + path.relative_to(ROOT).as_posix(): path.read_bytes()
            for directory in ("config", "squaremap")
            for path in (ROOT / directory).rglob("*") if path.is_file()
        }

    def run_archive(self, index: dict, overrides: dict[str, bytes]) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "test.mrpack"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("modrinth.index.json", json.dumps(index))
                for name, contents in overrides.items():
                    archive.writestr(name, contents)
            output = io.StringIO()
            with patch.object(sys, "argv", ["validate_mrpack.py", str(path), "--minecraft", "26.2"]), contextlib.redirect_stdout(output):
                result = validate_mrpack.main()
            return result, output.getvalue()

    def assert_archive_rejected(self, index: dict, overrides: dict[str, bytes], message: str) -> None:
        result, output = self.run_archive(index, overrides)
        self.assertNotEqual(0, result, output)
        self.assertIn(message, output)

    def test_complete_server_archive_passes(self) -> None:
        result, output = self.run_archive(self.index, self.overrides)
        self.assertEqual(0, result, output)

    def test_wrong_release_version_is_rejected(self) -> None:
        self.assert_archive_rejected({**self.index, "versionId": "0.1.0"}, self.overrides, "versionId must match pack.toml")

    def test_missing_or_modified_config_is_rejected(self) -> None:
        key = "overrides/config/justenoughbackups.json"
        for label, overrides in (
            ("all missing", {}),
            ("one missing", {k: v for k, v in self.overrides.items() if k != key}),
            ("changed", {**self.overrides, key: b"{}"}),
        ):
            with self.subTest(label=label):
                self.assert_archive_rejected(self.index, overrides, "configuration override")

    def test_incorrect_environment_is_rejected(self) -> None:
        for env in (None, {}, [], {"server": "optional", "client": "unsupported"}, {"server": "unsupported", "client": "required"}, {"server": "required", "client": "required"}):
            with self.subTest(env=env):
                index = copy.deepcopy(self.index)
                for entry in index["files"]:
                    entry["env"] = env
                self.assert_archive_rejected(index, self.overrides, "env")

    def test_wrong_loader_pin_is_rejected(self) -> None:
        self.index["dependencies"]["fabric-loader"] = "0.1.0"
        self.assert_archive_rejected(self.index, self.overrides, "dependencies must match pack.toml")

    def test_missing_mod_is_rejected(self) -> None:
        self.index["files"].pop()
        self.assert_archive_rejected(self.index, self.overrides, "missing baseline mod")

    def test_changed_mod_pin_is_rejected(self) -> None:
        for field in ("hash", "url"):
            with self.subTest(field=field):
                index = copy.deepcopy(self.index)
                if field == "hash":
                    index["files"][0]["hashes"]["sha512"] = "0" * 128
                else:
                    index["files"][0]["downloads"] = ["https://example.invalid/other.jar"]
                self.assert_archive_rejected(index, self.overrides, "must match the pinned mod")

    def test_staged_mod_or_extra_override_is_rejected(self) -> None:
        extra = copy.deepcopy(self.index["files"][0])
        extra["path"] = "mods/krypton.jar"
        self.assert_archive_rejected({**self.index, "files": self.index["files"] + [extra]}, self.overrides, "unexpected exported file")
        for name in ("overrides/staged/config/example.json", "server-overrides/config/justenoughbackups.json", "overrides/mods/krypton.jar", "overrides/config/floodgate/key.pem"):
            with self.subTest(name=name):
                self.assert_archive_rejected(self.index, {**self.overrides, name: b"unexpected"}, "unexpected archive entry")

    def test_duplicate_archive_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "test.mrpack"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr("modrinth.index.json", json.dumps(self.index))
                    archive.writestr("modrinth.index.json", "{}")
            with self.assertRaisesRegex(ValueError, "duplicate paths"):
                validate_mrpack.read_index(path)

    def test_manifest_alone_cannot_bypass_override_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires a .mrpack archive"):
            validate_mrpack.read_index(pathlib.Path("modrinth.index.json"))

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
            "env": {"server": "required", "client": "unsupported"},
        }
        errors: list[str] = []
        path, environment = validate_mrpack.validate_entry(entry, 0, errors)
        self.assertEqual("mods/example.jar", path)
        self.assertEqual("required", environment)
        self.assertEqual(2, len(errors))


if __name__ == "__main__":
    unittest.main()
