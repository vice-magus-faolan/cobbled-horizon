"""First-server policy and native index regressions (no Minecraft execution)."""

from __future__ import annotations

import contextlib
import gzip
import io
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from test_validation import ROOT, permission_seed


class WorldgenPolicyTests(unittest.TestCase):
    def test_overrides_match_frozen_pinned_resource_values(self) -> None:
        # Extracted from the exact SHA-512-pinned MSS 2.2.0 and Hopo 1.3.8
        # structure sets. Salts use the native signed-int decoding; only fields
        # controlled by our Cristel overrides are captured, not native defaults.
        fixture = json.loads((ROOT / "tests/fixtures/worldgen-26.3.json").read_text())
        for name, metadata, directory in (
            ("mss", "mss-moogs-soaring-structures.pw.toml", "mss"),
            ("hopo", "hopo-better-mineshaft.pw.toml", "hopobettermineshaft"),
        ):
            with self.subTest(name=name):
                pin = tomllib.loads((ROOT / "mods" / metadata).read_text())
                self.assertEqual(fixture[name]["artifact_sha512"], pin["download"]["hash"])
                base = ROOT / "config/cristellib" / directory
                for field, filename in (("placement", "structure_placement_config.json5"), ("toggles", "structure_toggle_config.json5")):
                    self.assertEqual(fixture[name][field], json.loads((base / filename).read_text()))
        mss = fixture["mss"]
        self.assertEqual(28, len(mss["placement"]))
        self.assertEqual(35, sum(len(members) for members in mss["toggles"].values()))
        self.assertEqual({f"tree_{number}": True for number in range(1, 9)}, mss["toggles"]["trees"])
        self.assertEqual(9, sum(values.get("frequency") == 0.6 for values in mss["placement"].values()))


class PermissionSeedTests(unittest.TestCase):
    def test_canonical_policy_and_import_payload(self) -> None:
        data = permission_seed.policy_bytes(ROOT)
        self.assertEqual((ROOT / permission_seed.SEED_SOURCE).read_bytes(), data)
        policy = json.loads(data)
        default = {"sswaystones.create.place": True}
        default.update({"sswaystones." + suffix: False for suffix in (
            "create.global", "create.team", "create.server", "command", "manager", "manager.bypass_limit", "showall",
        )})
        owner = {"group.default": True}
        owner.update({"sswaystones." + suffix: True for suffix in (
            "create.global", "create.server", "command", "manager", "manager.bypass_limit", "showall",
        )})
        expected = {"default": default, "owner": owner, "helper": {"group.default": True}}
        self.assertEqual({"groups", "tracks"}, set(policy))
        self.assertEqual({}, policy["tracks"])
        for name, nodes in expected.items():
            actual = policy["groups"][name]["nodes"]
            self.assertEqual(len(nodes), len(actual))
            self.assertEqual(nodes, {node["key"]: node["value"] for node in actual})
        packaged = (ROOT / permission_seed.SEED_IMPORT).read_bytes()
        self.assertEqual(data, gzip.decompress(packaged))
        self.assertEqual(permission_seed.import_bytes(data), permission_seed.import_bytes(data))
        index = tomllib.loads((ROOT / "index.toml").read_text())
        self.assertTrue(permission_seed.SEED_PATHS <= {entry["file"] for entry in index["files"]})

    def test_private_and_elevated_seed_variants_are_rejected(self) -> None:
        policy = json.loads(permission_seed.policy_bytes(ROOT))
        for extra in ({"users": {}}, {"metadata": {"actor": "private canary"}}):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                target = root / permission_seed.SEED_SOURCE
                target.parent.mkdir(parents=True)
                target.write_text(json.dumps({**policy, **extra}))
                with self.assertRaises(ValueError):
                    permission_seed.policy_bytes(root)
        for node in (
            {"type": "permission", "key": "*", "value": True},
            {"type": "permission", "key": "luckperms.admin", "value": True},
            {"type": "inheritance", "key": "group.owner", "value": True},
            {"type": "permission", "key": "sswaystones.command", "value": True, "context": {"server": "private canary"}},
        ):
            with self.subTest(node=node):
                self.assertFalse(permission_seed.valid_node(node))

    def test_duplicate_members_are_rejected_at_every_object_level(self) -> None:
        data = json.dumps(json.loads((ROOT / permission_seed.SEED_SOURCE).read_bytes()), separators=(",", ":"))
        variants = (
            ("{", '{"tracks":{"private":"private canary"},'),
            ("{", '{"tracks":{},'),
            ("{", r'{"tr\u0061cks":{},'),
            ('"default":{', '"default":{"private":"private canary"},"default":{'),
            ('"nodes":[', '"nodes":["private canary"],"nodes":['),
            ('"type":"permission"', '"type":"private canary","type":"permission"'),
            ('"key":"sswaystones.create.place"', '"key":"private canary","key":"sswaystones.create.place"'),
            ('"value":true', '"value":false,"value":true'),
        )
        for original, replacement in variants:
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as directory:
                self.assertIn(original, data)
                root = pathlib.Path(directory)
                target = root / permission_seed.SEED_SOURCE
                target.parent.mkdir(parents=True)
                target.write_text(data.replace(original, replacement, 1))
                with self.assertRaises(ValueError):
                    permission_seed.policy_bytes(root)

    def test_shadowed_private_members_cannot_be_checked_or_packaged(self) -> None:
        data = (ROOT / permission_seed.SEED_SOURCE).read_bytes()
        data = data.replace(b"{", b'{"tracks":{"private":"private canary"},', 1)
        for arguments in ([], ["--check"]):
            with self.subTest(arguments=arguments), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                target = root / permission_seed.SEED_SOURCE
                target.parent.mkdir(parents=True)
                target.write_bytes(data)
                packaged = root / permission_seed.SEED_IMPORT
                before = permission_seed.import_bytes(data) if arguments else b"existing import canary"
                packaged.write_bytes(before)
                output = io.StringIO()
                with patch.object(permission_seed, "ROOT", root), patch.object(sys, "argv", ["permission_seed.py", *arguments]), contextlib.redirect_stdout(output):
                    result = permission_seed.main()
                self.assertEqual(before, packaged.read_bytes())
                self.assertEqual(1, result)
                self.assertNotIn("PASS:", output.getvalue())
                self.assertNotIn("private canary", output.getvalue())

    def test_stale_missing_or_corrupt_import_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            target = root / permission_seed.SEED_SOURCE
            target.parent.mkdir(parents=True)
            target.write_bytes(permission_seed.policy_bytes(ROOT))
            for packaged in (None, b"not gzip", permission_seed.import_bytes(b"{}")):
                with self.subTest(packaged=packaged):
                    if packaged is not None:
                        (root / permission_seed.SEED_IMPORT).write_bytes(packaged)
                    with patch.object(permission_seed, "ROOT", root), patch.object(sys, "argv", ["permission_seed.py", "--check"]), contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(1, permission_seed.main())

    def test_native_refresh_indexes_seed_but_not_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for name in ("pack.toml", ".packwizignore", ".gitignore"):
                shutil.copyfile(ROOT / name, root / name)
            (root / "index.toml").write_text("hash-format = \"sha256\"\n")
            for relative in permission_seed.SEED_PATHS:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            private = (
                "mods/luckperms/luckperms-h2.mv.db", "mods/luckperms/config.yml",
                "mods/luckperms/exports/private.json.gz", "config/luckperms/users.json",
                "config/cobbled-horizon/extra.json", "config/floodgate/key.pem", "config/Geyser-Fabric/saved-refresh-tokens.json",
            )
            for relative in private:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"private canary")
            result = subprocess.run(["packwiz", "refresh", "--build"], cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            index = tomllib.loads((root / "index.toml").read_text())
            self.assertEqual(permission_seed.SEED_PATHS, {entry["file"] for entry in index["files"]})


if __name__ == "__main__":
    unittest.main()
