"""Synthetic payload regressions; real pinned archives are built and checked in CI."""

from __future__ import annotations

import hashlib
import json
import pathlib
import stat
import unittest
import warnings
import zipfile

import test_release
from test_validation import ROOT, load_script, permission_seed

server_pack = load_script("server_pack")


class ServerPackTests(unittest.TestCase):
    def setUp(self) -> None:
        # Reuse the existing CF producer fixture, not another manifest definition.
        self.fixture = test_release.CurseForgeArchiveTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        (self.root / "squaremap").mkdir()
        (self.root / "squaremap/config.yml").write_bytes(b"enabled: true\n")
        with (self.root / "index.toml").open("a") as index:
            index.write('[[files]]\nfile = "squaremap/config.yml"\n')
        self.fixture.files["overrides/squaremap/config.yml"] = b"enabled: true\n"
        for relative in sorted(permission_seed.SEED_PATHS):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
            with (self.root / "index.toml").open("a") as index:
                index.write(f"[[files]]\nfile = {json.dumps(relative)}\n")
            self.fixture.files["overrides/" + relative] = target.read_bytes()
        self.assertEqual([], self.fixture.validate())
        self.source = self.root / "test.zip"
        self.output = self.root / "server.zip"
        self.payload = {
            name.removeprefix("overrides/"): data
            for name, data in self.fixture.files.items()
            if name.startswith("overrides/")
        }

    def write_server(self, files: dict[str, bytes], duplicate: bool = False) -> None:
        with zipfile.ZipFile(self.output, "w") as archive:
            for name, contents in files.items():
                archive.writestr(name, contents)
            if duplicate:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr("mods/test.jar", self.fixture.mod)

    def test_build_has_exact_root_payload_and_preserves_input(self) -> None:
        before = self.source.read_bytes()
        server_pack.build_archive(self.source, self.output, self.root)
        self.assertEqual(before, self.source.read_bytes())
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(set(self.payload), set(archive.namelist()))
            self.assertEqual({"mods", "config", "squaremap"}, {
                pathlib.PurePosixPath(name).parts[0] for name in archive.namelist()
            })
            for name, contents in self.payload.items():
                self.assertEqual(hashlib.sha512(contents).digest(),
                                 hashlib.sha512(archive.read(name)).digest())
        self.assertEqual([], server_pack.validate_archive(self.output, self.root))

    def test_invalid_cf_is_rejected_before_output_is_opened(self) -> None:
        for defect in ("missing", "modified", "extra", "duplicate", "manifest"):
            with self.subTest(defect=defect):
                original = self.fixture.files.copy()
                manifest = self.fixture.manifest.copy()
                if defect == "missing":
                    del self.fixture.files["overrides/mods/test.jar"]
                elif defect == "modified":
                    self.fixture.files["overrides/config/test.json"] = b"changed"
                elif defect == "extra":
                    self.fixture.files["overrides/config/floodgate/key.pem"] = b"private"
                elif defect == "manifest":
                    self.fixture.manifest["files"] = [{"projectID": 1, "fileID": 2}]
                self.fixture.validate(duplicate=defect == "duplicate")
                self.output.write_bytes(b"previous artifact")
                with self.assertRaises(ValueError):
                    server_pack.build_archive(self.source, self.output, self.root)
                self.assertEqual(b"previous artifact", self.output.read_bytes())
                self.fixture.files = original
                self.fixture.manifest = manifest

    def test_missing_and_changed_root_files_are_rejected(self) -> None:
        for name in self.payload:
            for defect in ("missing", "modified"):
                with self.subTest(name=name, defect=defect):
                    files = self.payload.copy()
                    if defect == "missing":
                        del files[name]
                    else:
                        files[name] = b"changed"
                    self.write_server(files)
                    self.assertTrue(server_pack.validate_archive(self.output, self.root))

    def test_wrappers_and_unexpected_private_runtime_paths_are_rejected(self) -> None:
        for name in (
            "manifest.json", "modlist.html", "overrides/mods/test.jar",
            "server/mods/test.jar", "mods/staged.jar", "mods/client.jar",
            "mods/luckperms/config.yml", "mods/luckperms/users.json",
            "config/luckperms/users.json", "config/cobbled-horizon/extra.json",
            "config/floodgate/key.pem", "logs/latest.log", "world/level.dat",
            "server.jar", "../escape", "/absolute", "mods\\escape.jar",
            "mods/../escape.jar", "mods//test.jar",
        ):
            with self.subTest(name=name):
                self.write_server({**self.payload, name: b"unexpected"})
                self.assertIn(f"unexpected archive entry: {name}",
                              server_pack.validate_archive(self.output, self.root))

    def test_duplicate_root_entry_is_rejected(self) -> None:
        self.write_server(self.payload, duplicate=True)
        self.assertIn("archive contains duplicate paths",
                      server_pack.validate_archive(self.output, self.root))

    def test_symlink_cannot_masquerade_as_expected_payload(self) -> None:
        self.write_server({name: data for name, data in self.payload.items()
                           if name != "mods/test.jar"})
        with zipfile.ZipFile(self.output, "a") as archive:
            link = zipfile.ZipInfo("mods/test.jar")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(link, self.fixture.mod)
        self.assertIn("unsafe archive entry type: mods/test.jar",
                      server_pack.validate_archive(self.output, self.root))

    def test_source_side_and_unsafe_filename_are_rejected(self) -> None:
        path = self.root / "mods/test.pw.toml"
        original = path.read_text()
        for text in (original.replace('side = "server"', 'side = "client"'),
                     original.replace('filename = "test.jar"', 'filename = "../escape.jar"')):
            with self.subTest(text=text):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    server_pack.build_archive(self.source, self.output, self.root)
                self.assertFalse(self.output.exists())
        path.write_text(original)

    def test_malformed_input_and_same_output_path_do_not_destroy_input(self) -> None:
        before = self.source.read_bytes()
        with self.assertRaises(ValueError):
            server_pack.build_archive(self.source, self.source, self.root)
        self.assertEqual(before, self.source.read_bytes())
        self.source.write_bytes(b"not a ZIP")
        with self.assertRaises(zipfile.BadZipFile):
            server_pack.build_archive(self.source, self.output, self.root)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
