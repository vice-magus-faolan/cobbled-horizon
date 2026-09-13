"""Release identity and CurseForge archive regression tests."""

from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile
import unittest
import warnings
import zipfile

from test_validation import load_script

release_metadata = load_script("release_metadata")
validate_curseforge = load_script("validate_curseforge")


class ReleaseMetadataTests(unittest.TestCase):
    def test_minecraft_prefixed_release_tag(self) -> None:
        pack = {"version": "26.2.0.1.0", "versions": {"minecraft": "26.2"}}
        values = release_metadata.metadata(pack, "v26.2.0.1.0")
        self.assertEqual("26.2.0.1.0", values["version"])
        self.assertEqual("cobbled-horizon-26.2.0.1.0", values["basename"])

    def test_mismatched_and_malformed_tags_are_rejected(self) -> None:
        pack = {"version": "26.2.0.1.0", "versions": {"minecraft": "26.2"}}
        for tag in ("v0.1.0", "v26.3.0.1.0", "v26.2.0.1.1", "v26.2.0.1.0-rc1", "26.2.0.1.0", "v26.2.0.1.0\n"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                release_metadata.metadata(pack, tag)

    def test_pack_version_must_include_exact_minecraft_prefix(self) -> None:
        for version in ("0.1.0", "26.3.0.1.0", "26.2.0.1", "26.2.00.1.0", "26.2.0.1.0\n"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                release_metadata.metadata({"version": version, "versions": {"minecraft": "26.2"}})

    def test_minecraft_patch_version_is_not_confused_with_pack_version(self) -> None:
        values = release_metadata.metadata({"version": "26.2.1.0.2.0", "versions": {"minecraft": "26.2.1"}})
        self.assertEqual("v26.2.1.0.2.0", values["tag"])


class CurseForgeArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = pathlib.Path(temporary.name)
        (self.root / "mods").mkdir()
        (self.root / "config").mkdir()
        (self.root / "pack.toml").write_text(
            'name = "Test pack"\nversion = "26.2.0.1.0"\nauthor = "Test author"\n'
            '[versions]\nminecraft = "26.2"\nfabric = "0.19.5"\n'
        )
        self.mod = b"pinned server mod bytes"
        (self.root / "mods/test.pw.toml").write_text(
            'filename = "test.jar"\nside = "server"\n'
            '[download]\nhash-format = "sha512"\n'
            f'hash = "{hashlib.sha512(self.mod).hexdigest()}"\n'
        )
        (self.root / "config/test.json").write_bytes(b'{"enabled": true}')
        (self.root / "index.toml").write_text(
            '[[files]]\nfile = "mods/test.pw.toml"\nmetafile = true\n'
            '[[files]]\nfile = "config/test.json"\n'
        )
        self.manifest = {
            "manifestType": "minecraftModpack", "manifestVersion": 1,
            "name": "Test pack", "version": "26.2.0.1.0", "author": "Test author",
            "minecraft": {"version": "26.2", "modLoaders": [{"id": "fabric-0.19.5", "primary": True}]},
            "files": [], "overrides": "overrides",
        }
        self.files = {
            "overrides/mods/test.jar": self.mod,
            "overrides/config/test.json": b'{"enabled": true}',
            "modlist.html": b"<ul><li>Test mod</li></ul>",
        }

    def validate(self, duplicate: bool = False) -> list[str]:
        path = self.root / "test.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("manifest.json", json.dumps(self.manifest))
            for name, contents in self.files.items():
                archive.writestr(name, contents)
            if duplicate:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr("overrides/mods/test.jar", self.mod)
        return validate_curseforge.validate_archive(path, self.root)

    def test_complete_server_export_passes(self) -> None:
        self.assertEqual([], self.validate())

    def test_client_export_missing_server_mod_is_rejected(self) -> None:
        del self.files["overrides/mods/test.jar"]
        self.assertIn("missing exported file: overrides/mods/test.jar", self.validate())

    def test_modified_jar_and_configuration_are_rejected(self) -> None:
        for name in ("overrides/mods/test.jar", "overrides/config/test.json"):
            with self.subTest(name=name):
                original = self.files[name]
                self.files[name] = b"modified"
                self.assertIn(f"exported file hash differs from source: {name}", self.validate())
                self.files[name] = original

    def test_missing_configuration_is_rejected(self) -> None:
        del self.files["overrides/config/test.json"]
        self.assertIn("missing exported file: overrides/config/test.json", self.validate())

    def test_staged_secret_and_unsafe_entries_are_rejected(self) -> None:
        for name in ("overrides/mods/staged.jar", "overrides/config/floodgate/key.pem", "../escape"):
            with self.subTest(name=name):
                self.files[name] = b"unexpected"
                self.assertIn(f"unexpected archive entry: {name}", self.validate())
                del self.files[name]

    def test_wrong_versions_and_external_file_references_are_rejected(self) -> None:
        for key, value in (("version", "0.1.0"), ("minecraft", {"version": "26.3"}), ("files", [{"projectID": 1, "fileID": 2}])):
            with self.subTest(key=key):
                original = self.manifest[key]
                self.manifest[key] = value
                self.assertTrue(any(error.startswith(f"manifest.{key}") for error in self.validate()))
                self.manifest[key] = original

    def test_duplicate_archive_entry_is_rejected(self) -> None:
        self.assertIn("archive contains duplicate paths", self.validate(duplicate=True))

    def test_unindexed_source_config_is_rejected(self) -> None:
        (self.root / "config/forgotten.json").write_text("{}")
        self.assertIn("source config is not indexed: config/forgotten.json", self.validate())


if __name__ == "__main__":
    unittest.main()
