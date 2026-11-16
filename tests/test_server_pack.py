"""Real mrpack preparation with controlled project-owned upstream downloads."""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import stat
import unittest
import warnings
import zipfile
from unittest.mock import patch

import test_distribution
from test_validation import ROOT, permission_seed

server_pack = test_distribution.server_pack


class ServerPackTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_distribution.DistributionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.prepare_archives()
        self.root = self.fixture.root
        self.source = self.fixture.mrpack
        self.output = self.root / "server"
        _, self.contents = test_distribution.validate_mrpack.read_index(self.source)
        (self.root / "squaremap").mkdir()
        (self.root / "squaremap/config.yml").write_bytes(b"enabled: true\n")
        for relative in ("squaremap/config.yml", *sorted(permission_seed.SEED_PATHS)):
            target = self.root / relative
            if relative in permission_seed.SEED_PATHS:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            with (self.root / "index.toml").open("a") as index:
                index.write(f"[[files]]\nfile = {json.dumps(relative)}\n")
            self.contents["overrides/" + relative] = target.read_bytes()
        self.write_mrpack(self.contents)
        self.payload = {name.removeprefix("overrides/"): data for name, data in self.contents.items() if name.startswith("overrides/")}
        self.payload.update({"mods/test.jar": self.fixture.fixture.mod, "mods/override.jar": self.fixture.override_bytes})

    def write_mrpack(self, contents, duplicate=False, symlink=None):
        with zipfile.ZipFile(self.source, "w") as archive:
            for name, data in contents.items():
                member = zipfile.ZipInfo(name)
                member.external_attr = ((stat.S_IFLNK if name == symlink else stat.S_IFREG) | 0o644) << 16
                archive.writestr(member, data)
            if duplicate:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr("modrinth.index.json", contents["modrinth.index.json"])

    def materialize(self, destination=None):
        with patch.object(server_pack.urllib.request, "urlopen", side_effect=[io.BytesIO(self.fixture.fixture.mod), io.BytesIO(self.fixture.override_bytes)]) as download:
            server_pack.materialize(self.source, destination or self.output, self.root)
        return download

    def test_complete_root_payload_and_input_preservation(self):
        before = self.source.read_bytes()
        download = self.materialize()
        self.assertEqual(2, download.call_count)
        self.assertEqual(before, self.source.read_bytes())
        self.assertEqual(set(self.payload), {path.relative_to(self.output).as_posix() for path in self.output.rglob("*") if path.is_file()})
        for name, data in self.payload.items():
            self.assertEqual(data, (self.output / name).read_bytes())
        self.assertEqual([], server_pack.validate_directory(self.output, self.root))
        self.assertEqual([], list(self.root.glob(".materialize-*")))

    def test_invalid_archive_is_rejected_before_download_or_destination(self):
        for defect in ("missing", "modified", "extra", "duplicate", "symlink", "index", "traversal", "alias", "jar"):
            with self.subTest(defect=defect):
                contents = self.contents.copy()
                if defect == "missing":
                    del contents["overrides/config/test.json"]
                elif defect == "modified":
                    contents["overrides/config/test.json"] = b"changed"
                elif defect == "extra":
                    contents["overrides/config/floodgate/key.pem"] = b"private"
                elif defect == "index":
                    index = json.loads(contents["modrinth.index.json"])
                    index["files"].pop()
                    contents["modrinth.index.json"] = json.dumps(index).encode()
                elif defect in {"traversal", "alias", "jar"}:
                    name = {"traversal": "../escape", "alias": "overrides/config//test.json", "jar": "overrides/mods/hidden.JAR"}[defect]
                    contents[name] = b"bad"
                self.write_mrpack(contents, duplicate=defect == "duplicate", symlink="overrides/config/test.json" if defect == "symlink" else None)
                with patch.object(server_pack.urllib.request, "urlopen") as download:
                    with self.assertRaises(ValueError):
                        server_pack.materialize(self.source, self.output, self.root)
                download.assert_not_called()
                self.assertFalse(self.output.exists())
                self.assertFalse((self.root / "escape").exists())

    def test_missing_changed_and_private_root_files_are_rejected(self):
        self.materialize()
        for name, data in self.payload.items():
            target = self.output / name
            target.unlink()
            self.assertTrue(server_pack.validate_directory(self.output, self.root), name)
            target.write_bytes(b"changed")
            self.assertTrue(server_pack.validate_directory(self.output, self.root), name)
            target.write_bytes(data)
        for name in ("world/level.dat", "logs/latest.log", "config/floodgate/key.pem", "mods/client.jar", "mods/luckperms/users.json", "server.jar"):
            target = self.output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"private")
            self.assertIn("unexpected server entry: " + name, server_pack.validate_directory(self.output, self.root))
            target.unlink()
        self.assertEqual([], list(self.root.glob(".materialize-*")))

    def test_fresh_destination_refuses_files_directories_and_symlinks_without_network(self):
        for kind in ("file", "directory", "symlink"):
            with self.subTest(kind=kind):
                target = self.root / kind
                if kind == "file":
                    target.write_bytes(b"preserve")
                elif kind == "directory":
                    target.mkdir()
                    (target / "canary").write_bytes(b"preserve")
                else:
                    target.symlink_to(self.root / "absent", target_is_directory=True)
                with patch.object(server_pack.urllib.request, "urlopen") as download:
                    with self.assertRaises(FileExistsError):
                        server_pack.materialize(self.source, target, self.root)
                download.assert_not_called()
                if kind == "file":
                    self.assertEqual(b"preserve", target.read_bytes())
                elif kind == "directory":
                    self.assertEqual(b"preserve", (target / "canary").read_bytes())
                else:
                    self.assertTrue(target.is_symlink())

    def test_download_hash_size_and_transport_failures_leave_no_folder(self):
        for failure in ("hash", "size", "transport"):
            with self.subTest(failure=failure):
                responses = [io.BytesIO(b"x" * len(self.fixture.fixture.mod)), io.BytesIO(self.fixture.override_bytes)]
                if failure == "size":
                    responses[0] = io.BytesIO(b"short")
                if failure == "transport":
                    responses[1] = OSError("controlled failed download")
                with patch.object(server_pack.urllib.request, "urlopen", side_effect=responses):
                    with self.assertRaises((ValueError, OSError)):
                        server_pack.materialize(self.source, self.output, self.root)
                self.assertFalse(self.output.exists())
                self.assertEqual([], list(self.root.glob(".materialize-*")))

    def test_symlink_cannot_masquerade_as_payload_or_directory(self):
        self.materialize()
        target = self.output / "mods/test.jar"
        target.unlink()
        target.symlink_to(self.source)
        self.assertIn("unsafe server entry type: mods/test.jar", server_pack.validate_directory(self.output, self.root))
        self.assertTrue(server_pack.validate_directory(self.output / "mods/test.jar", self.root))

    def test_source_side_and_unsafe_filename_are_rejected(self):
        path = self.fixture.metadata
        original = path.read_text()
        for text in (original.replace('side = "server"', 'side = "client"'), original.replace('filename = "test.jar"', 'filename = "../escape.jar"')):
            with self.subTest(text=text):
                path.write_text(text)
                with patch.object(server_pack.urllib.request, "urlopen") as download:
                    with self.assertRaises(ValueError):
                        server_pack.materialize(self.source, self.output, self.root)
                download.assert_not_called()
                self.assertFalse(self.output.exists())
        path.write_text(original)

    def test_malformed_input_does_not_create_folder_or_destroy_input(self):
        self.source.write_bytes(b"not a ZIP")
        with self.assertRaises(zipfile.BadZipFile):
            server_pack.materialize(self.source, self.output, self.root)
        self.assertEqual(b"not a ZIP", self.source.read_bytes())
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
