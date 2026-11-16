"""Distribution boundary and complete hosted-reference materialization regressions.

All binary/source/permission fixtures are project-owned synthetic bytes. They
establish producer behavior, never permission for the real selected modpack.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import pathlib
import subprocess
import sys
import unittest
import zipfile
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import distribution
import server_pack
import validate_curseforge
import validate_mrpack
import test_release


def toml_fields(values: dict) -> str:
    """Serialize the fixture's finite scalar/list/inline-table shape."""
    def value(item):
        if isinstance(item, dict):
            return "{ " + ", ".join(key + " = " + value(content) for key, content in item.items()) + " }"
        if isinstance(item, list):
            return "[" + ", ".join(value(content) for content in item) + "]"
        return json.dumps(item)
    return "\n".join(key + " = " + value(content) for key, content in values.items()) + "\n"


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_release.CurseForgeArchiveTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.metadata = self.root / "mods/test.pw.toml"
        with self.metadata.open("a") as stream:
            stream.write('[update.modrinth]\nmod-id = "owned"\nversion = "exact"\n')
        self.text = (ROOT / "LICENSE").read_bytes()
        self.digest = hashlib.sha256(self.text).hexdigest()
        texts = self.root / "distribution/texts"
        texts.mkdir(parents=True)
        (texts / (self.digest + ".txt")).write_bytes(self.text)
        self.record = {
            "project": "owned", "version": "exact", "name": "Project-owned fixture",
            "metafile_sha256": hashlib.sha256(self.metadata.read_bytes()).hexdigest(),
            "sha512": hashlib.sha512(self.fixture.mod).hexdigest(),
            "lines": ["26.2"], "side": "server", "license": "MIT",
            "credit": "Cobbled Horizon contributors; https://github.com/vice-magus-faolan/cobbled-horizon",
            "conditions": "Project-owned unmodified test bytes, not third-party permission.",
            "channels": {channel: "allowed" for channel in distribution.CHANNELS},
            "texts": [self.digest], "pending": [], "nested": "verified", "platform": "verified",
            "text_provenance": [{"url": "https://example.invalid/owned-license", "sha256": self.digest, "at": "2026-11-15"}],
            "source": {"status": "not-required", "basis": "Project-owned MIT fixture has no source-delivery duty."},
            "evidence": [{"url": "https://example.invalid/owned-permission", "sha256": self.digest, "at": "2026-11-15"}],
        }
        self.write_policy()

    def write_policy(self):
        (self.root / "distribution/permissions.toml").write_text("schema = 1\n[[components]]\n" + toml_fields(self.record))
        if hasattr(self, "override_record"):
            with (self.root / "distribution/permissions.toml").open("a") as stream:
                stream.write("[[components]]\n" + toml_fields(self.override_record))

    def prepare_archives(self, hosted=True):
        if hosted:
            with self.metadata.open("a") as stream:
                stream.write('[update.curseforge]\nproject-id = 1\nfile-id = 2\n')
            self.record["metafile_sha256"] = hashlib.sha256(self.metadata.read_bytes()).hexdigest()
            self.record["hosted"] = {"project-id": 1, "file-id": 2}
            self.record["hosted_evidence"] = "Synthetic fixture identity, checked against owned bytes."
            self.fixture.manifest["files"] = [{"projectID": 1, "fileID": 2, "required": True}]
            del self.fixture.files["overrides/mods/test.jar"]
        # Exercise a real mixed partition, not separate all-hosted/all-override cases.
        self.override_bytes = b"project-owned approved override bytes"
        extra = self.root / "mods/override.pw.toml"
        extra.write_text('filename = "override.jar"\nside = "server"\n[download]\nurl = "https://example.invalid/override.jar"\nhash-format = "sha512"\n' +
                         'hash = "' + hashlib.sha512(self.override_bytes).hexdigest() + '"\n[update.modrinth]\nmod-id = "owned-override"\nversion = "exact"\n')
        self.override_record = {**copy.deepcopy(self.record), "project": "owned-override",
                                "name": "Project-owned approved override", "sha512": hashlib.sha512(self.override_bytes).hexdigest(),
                                "metafile_sha256": hashlib.sha256(extra.read_bytes()).hexdigest()}
        self.override_record.pop("hosted", None)
        self.override_record.pop("hosted_evidence", None)
        with (self.root / "index.toml").open("a") as stream:
            stream.write('[[files]]\nfile = "mods/override.pw.toml"\nmetafile = true\n')
        self.fixture.files["overrides/mods/override.jar"] = self.override_bytes
        self.write_policy()
        self.fixture.files.update({"overrides/" + name: data for name, data in distribution.notice_members(self.root).items()})
        self.assertEqual([], self.fixture.validate())
        (self.root / "collection.toml").write_text('selected = [{ project-id = "owned" }, { project-id = "owned-override" }]\nresolved-dependency = []\n')
        self.index = {
            "formatVersion": 1, "game": "minecraft", "versionId": "26.2.0.1.0",
            "dependencies": {"minecraft": "26.2", "fabric-loader": "0.19.5"},
            "files": [{"path": "mods/test.jar", "hashes": {"sha1": hashlib.sha1(self.fixture.mod).hexdigest(), "sha512": self.record["sha512"]},
                       "fileSize": len(self.fixture.mod), "downloads": ["https://example.invalid/owned.jar"],
                       "env": {"server": "required", "client": "unsupported"}}],
        }
        self.index["files"].append({"path": "mods/override.jar", "hashes": {"sha1": hashlib.sha1(self.override_bytes).hexdigest(), "sha512": self.override_record["sha512"]},
                                    "fileSize": len(self.override_bytes), "downloads": ["https://example.invalid/override.jar"],
                                    "env": {"server": "required", "client": "unsupported"}})
        # Download identity in the source is authoritative, even for owned fixtures.
        text = self.metadata.read_text().replace('[download]\n', '[download]\nurl = "https://example.invalid/owned.jar"\n')
        self.metadata.write_text(text)
        self.record["metafile_sha256"] = hashlib.sha256(self.metadata.read_bytes()).hexdigest()
        self.write_policy()
        self.mrpack = self.root / "owned.mrpack"
        with zipfile.ZipFile(self.mrpack, "w") as archive:
            archive.writestr("modrinth.index.json", json.dumps(self.index))
            for name, data in self.fixture.files.items():
                if name.startswith("overrides/") and not name.startswith("overrides/mods/"):
                    archive.writestr(name, data)
        return self.root / "test.zip", self.root / "server.zip"

    def test_exact_fixture_clearance_and_deterministic_full_notices(self):
        for channel in distribution.CHANNELS:
            self.assertEqual(1, len(distribution.clearance(self.root, channel)))
        first = distribution.notice_members(self.root)
        self.assertEqual(first, distribution.notice_members(self.root))
        self.assertEqual(self.text, first["LICENSES/" + self.digest + ".txt"])
        self.assertIn(b"contributors", first["CREDITS.md"])
        self.assertIn(b"no source-delivery duty", first["SOURCES.md"])

    def test_changed_pin_url_side_and_new_identity_fail(self):
        original = self.metadata.read_bytes()
        for suffix in (b'\n# changed identity\n', b'\n[extra]\nurl = "https://example.invalid/new"\n'):
            self.metadata.write_bytes(original + suffix)
            with self.assertRaisesRegex(ValueError, "stale permission"):
                distribution.clearance(self.root, "github")
        self.metadata.write_bytes(original.replace(b'version = "exact"', b'version = "new"'))
        with self.assertRaisesRegex(ValueError, "new or changed pin"):
            distribution.clearance(self.root, "github")

    def test_channel_and_unfulfilled_obligations_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "unknown distribution channel"):
            distribution.clearance(self.root, "invented")
        original = copy.deepcopy(self.record)
        variants = [
            {"channels": {"github": "conditional", "curseforge": "allowed", "private": "allowed"}},
            {"pending": ["source not delivered"]}, {"nested": "unknown"},
            {"source": {"status": "unknown", "basis": "Not established"}},
            {"texts": []},
        ]
        for variant in variants:
            with self.subTest(variant=variant):
                self.record = {**original, **variant}
                self.write_policy()
                with self.assertRaises(ValueError):
                    distribution.clearance(self.root, "github")
        self.record = original
        self.write_policy()
        self.assertEqual(1, len(distribution.clearance(self.root, "github")))

    def test_missing_changed_or_symlink_license_text_fails(self):
        path = self.root / "distribution/texts" / (self.digest + ".txt")
        path.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed license"):
            distribution.clearance(self.root, "github")
        path.unlink()
        with self.assertRaisesRegex(ValueError, "missing regular license"):
            distribution.clearance(self.root, "github")
        path.symlink_to(ROOT / "LICENSE")
        with self.assertRaisesRegex(ValueError, "missing regular license"):
            distribution.clearance(self.root, "github")

    def test_full_text_requires_matching_primary_provenance(self):
        for provenance in ([], [{"url": "http://example.invalid/license", "sha256": self.digest, "at": "2026-11-15"}],
                           [{"url": "https://example.invalid/license", "sha256": "0" * 64, "at": "2026-11-15"}]):
            with self.subTest(provenance=provenance):
                self.record["text_provenance"] = provenance
                self.write_policy()
                with self.assertRaisesRegex(ValueError, "license-text provenance"):
                    distribution.records(self.root)

    def test_exact_equivalent_source_not_generic_homepage(self):
        revision = "1" * 40
        self.record["source"] = {"status": "equivalent-access", "basis": "Owned fixture exact complete source; fixture availability verified.", "revision": revision,
                                 "url": "https://example.invalid/archive/" + revision + ".zip", "sha256": self.digest,
                                 "directions": "Download the exact owned source archive beside this binary with equivalent access.", "verified_at": "2026-11-15"}
        self.write_policy()
        self.assertEqual(1, len(distribution.clearance(self.root, "github")))
        self.record["source"]["url"] = "https://example.invalid/project"
        self.write_policy()
        with self.assertRaisesRegex(ValueError, "not a homepage"):
            distribution.clearance(self.root, "github")

    def test_real_hosted_partition_and_complete_server(self):
        source, output = self.prepare_archives()
        distribution.clearance(self.root, "github")
        with patch.object(server_pack.urllib.request, "urlopen", return_value=io.BytesIO(self.fixture.mod)) as download:
            server_pack.build_archive(source, output, self.root, self.mrpack)
        self.assertEqual(1, download.call_count)
        with zipfile.ZipFile(source) as archive:
            self.assertNotIn("overrides/mods/test.jar", archive.namelist())
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(self.fixture.mod, archive.read("mods/test.jar"))
            self.assertEqual(self.override_bytes, archive.read("mods/override.jar"))
            self.assertEqual(b'{"enabled": true}', archive.read("config/test.json"))
            self.assertEqual(self.text, archive.read("LICENSES/" + self.digest + ".txt"))
        self.assertEqual([], server_pack.validate_archive(output, self.root))
        index, contents = validate_mrpack.read_index(self.mrpack)
        self.assertEqual([], validate_mrpack.validate_index(index, contents, "26.2", "fabric", self.root)[0])
        # JSON booleans/numbers must not compare equal to native reference IDs.
        for field, value in (("projectID", True), ("required", 1)):
            original = self.fixture.manifest["files"][0][field]
            self.fixture.manifest["files"][0][field] = value
            self.assertTrue(any(error.startswith("manifest.files") for error in self.fixture.validate()))
            self.fixture.manifest["files"][0][field] = original
        # A hosted binary cannot also appear as an override.
        self.fixture.files["overrides/mods/test.jar"] = self.fixture.mod
        self.assertIn("unexpected archive entry: overrides/mods/test.jar", self.fixture.validate())

    def test_bad_hosted_download_preserves_previous_output(self):
        source, output = self.prepare_archives()
        output.write_bytes(b"previous artifact")
        with patch.object(server_pack.urllib.request, "urlopen", return_value=io.BytesIO(b"wrong pin")):
            with self.assertRaisesRegex(ValueError, "differs from selected pin"):
                server_pack.build_archive(source, output, self.root, self.mrpack)
        self.assertEqual(b"previous artifact", output.read_bytes())

    def test_real_workflow_withholds_uncleared_uploads_and_rejects_tags(self):
        import os
        import tempfile
        import textwrap
        workflow = (ROOT / ".github/workflows/validate.yml").read_text()
        block = workflow.split("      - name: Evaluate public distribution clearance\n", 1)[1]
        script = textwrap.dedent(block.split("run: |\n", 1)[1].split("\n      - name:", 1)[0])
        for ref_type in ("branch", "tag"):
            with self.subTest(ref_type=ref_type), tempfile.TemporaryDirectory() as directory:
                output = pathlib.Path(directory) / "outputs"
                output.touch()
                result = subprocess.run(["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script], cwd=ROOT,
                                        env={"PATH": os.environ["PATH"], "PYTHONDONTWRITEBYTECODE": "1", "GITHUB_REF_TYPE": ref_type, "GITHUB_OUTPUT": str(output)},
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual("cleared=false\n", output.read_text())
                self.assertEqual(ref_type == "branch", result.returncode == 0, result.stdout + result.stderr)
                self.assertIn("public archives are withheld", result.stdout)

    def test_curated_inventory_has_both_lines_and_inactive_prospective_record(self):
        inventory = distribution.records(ROOT)
        identities = {(item["project"], item["version"], item["sha512"]) for item in inventory}
        self.assertEqual(len(inventory), len(identities))
        self.assertEqual(62, len(inventory))
        for line in ("26.2", "26.3"):
            self.assertEqual(32, sum(line in item["lines"] for item in inventory))
        self.assertEqual(["Cfbcv7uF"], [item["project"] for item in inventory if "prospective" in item["lines"]])
        self.assertNotIn("Cfbcv7uF", {item["project"] for _, item in distribution.selected(ROOT)})

    def test_channel_check_refuses_before_any_archive_or_network_effect(self):
        self.record["channels"]["github"] = "unknown"
        self.write_policy()
        with patch.object(distribution, "ROOT", self.root), patch.object(sys, "argv", ["distribution.py", "notices", "--channel", "github", "--archive", str(self.root / "absent.zip")]), patch.object(distribution.zipfile, "ZipFile") as archive:
            self.assertEqual(1, distribution.main())
        archive.assert_not_called()


if __name__ == "__main__":
    unittest.main()
