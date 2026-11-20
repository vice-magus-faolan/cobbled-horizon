"""Permission-record, recipient-notice and public release-plan regressions.

All binary/source/permission fixtures are project-owned synthetic bytes. They
establish producer behavior, never permission for the real selected modpack.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from pack_fixtures import ROOT, workflow_script
import distribution
import validate_mrpack


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
        self.metadata = self.root / "mods/test.pw.toml"
        self.metadata.write_text(
            'filename = "test.jar"\nside = "server"\n'
            '[download]\nurl = "https://example.invalid/owned.jar"\nhash-format = "sha512"\n'
            f'hash = "{hashlib.sha512(self.mod).hexdigest()}"\n'
            '[update.modrinth]\nmod-id = "owned"\nversion = "exact"\n'
        )
        (self.root / "config/test.json").write_bytes(b'{"enabled": true}')
        (self.root / "index.toml").write_text(
            '[[files]]\nfile = "mods/test.pw.toml"\nmetafile = true\n'
            '[[files]]\nfile = "config/test.json"\n'
        )
        self.files = {"overrides/config/test.json": b'{"enabled": true}'}
        self.text = (ROOT / "LICENSE").read_bytes()
        self.digest = hashlib.sha256(self.text).hexdigest()
        texts = self.root / "distribution/texts"
        texts.mkdir(parents=True)
        (texts / (self.digest + ".txt")).write_bytes(self.text)
        self.record = {
            "project": "owned", "version": "exact", "name": "Project-owned fixture",
            "metafile_sha256": hashlib.sha256(self.metadata.read_bytes()).hexdigest(),
            "sha512": hashlib.sha512(self.mod).hexdigest(),
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
            self.record["hosted_evidence"] = {"url": "https://www.curseforge.com/api/v1/mods/1/files/2/download",
                                               "sha256": hashlib.sha256(self.mod).hexdigest(),
                                               "sha512": self.record["sha512"], "at": "2026-11-16"}
        # Both native updater metadata and ordinary original-host downloads must
        # survive in a no-JAR mrpack and materialize into a complete local folder.
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
        self.write_policy()
        self.files.update({"overrides/" + name: data for name, data in distribution.notice_members(self.root).items()})
        (self.root / "collection.toml").write_text('selected = [{ project-id = "owned" }, { project-id = "owned-override" }]\nresolved-dependency = []\n')
        self.index = {
            "formatVersion": 1, "game": "minecraft", "versionId": "26.2.0.1.0",
            "dependencies": {"minecraft": "26.2", "fabric-loader": "0.19.5"},
            "files": [{"path": "mods/test.jar", "hashes": {"sha1": hashlib.sha1(self.mod).hexdigest(), "sha512": self.record["sha512"]},
                       "fileSize": len(self.mod), "downloads": ["https://example.invalid/owned.jar"],
                       "env": {"server": "required", "client": "unsupported"}}],
        }
        self.index["files"].append({"path": "mods/override.jar", "hashes": {"sha1": hashlib.sha1(self.override_bytes).hexdigest(), "sha512": self.override_record["sha512"]},
                                    "fileSize": len(self.override_bytes), "downloads": ["https://example.invalid/override.jar"],
                                    "env": {"server": "required", "client": "unsupported"}})
        self.mrpack = self.root / "owned.mrpack"
        with zipfile.ZipFile(self.mrpack, "w") as archive:
            archive.writestr("modrinth.index.json", json.dumps(self.index))
            for name, data in self.files.items():
                archive.writestr(name, data)
        return self.mrpack, self.root / "server"

    def test_exact_fixture_and_deterministic_full_notices(self):
        self.assertEqual(1, len(distribution.selected(self.root)))
        first = distribution.notice_members(self.root)
        self.assertEqual(first, distribution.notice_members(self.root))
        self.assertEqual(self.text, first["LICENSES/" + self.digest + ".txt"])
        self.assertIn(b"contributors", first["CREDITS.md"])
        self.assertIn(b"no source-delivery duty", first["SOURCES.md"])

    def test_real_rendered_notices_keep_readable_labels(self):
        glued = re.compile(r"SHA-?256[0-9a-f]|Copyright[0-9]|[A-Za-z](?:[0-9]+(?:\.[0-9]+)+|[0-9]{4,})\b")
        # Literal URLs/digests and these observed handles/tags are identifiers,
        # not prose labels. Do not exempt arbitrary words containing digits.
        identifiers = re.compile(
            r"https?://[^\s]+|\b[0-9a-f]{7,128}\b|"
            r"\b(?:Wesley1808|wesley1808|malte0811|pop4959|v0\.7\.0|v1\.10|v4\.5|v1\.4\.3|v26\.3)(?!\w|\.[0-9])"
        )
        notices = distribution.notice_members(ROOT)
        cases = [(name, notices[name].decode(), False) for name in ("CREDITS.md", "SOURCES.md")]
        cases.extend((label, label, True) for label in (
            "Gson2.11.0", "ASM9.5", "AWS SDK2.31.78", "reg-sync0.18.2",
            "Alpine3.22", "Java-WebSocket2010-2020", "Widget2026", "Wesley1808.2",
            "Copyright2021", "SHA256abcdef",
        ))
        cases.append(("literal identifiers and readable labels", "Wesley1808 malte0811 pop4959 jose4j v1.10 v26.3 "
                      "Gson 2.11.0 ASM 9.5 Java-WebSocket 2010-2020 "
                      "https://example.invalid/Gson2.11.0 6d5108cb9bef4b07939fb579b5fc0b5e2589bb02", False))
        for name, text, should_fail in cases:
            with self.subTest(name=name):
                prose = identifiers.sub("", text)
                if should_fail:
                    self.assertRegex(prose, glued)
                else:
                    self.assertNotRegex(prose, glued)

    def test_changed_pin_url_side_and_new_identity_fail(self):
        original = self.metadata.read_bytes()
        for suffix in (b'\n# changed identity\n', b'\n[extra]\nurl = "https://example.invalid/new"\n'):
            self.metadata.write_bytes(original + suffix)
            with self.assertRaisesRegex(ValueError, "stale permission"):
                distribution.selected(self.root)
        self.metadata.write_bytes(original.replace(b'version = "exact"', b'version = "new"'))
        with self.assertRaisesRegex(ValueError, "new or changed pin"):
            distribution.selected(self.root)

    def test_missing_changed_or_symlink_license_text_fails(self):
        path = self.root / "distribution/texts" / (self.digest + ".txt")
        path.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed license"):
            distribution.selected(self.root)
        path.unlink()
        with self.assertRaisesRegex(ValueError, "missing regular license"):
            distribution.selected(self.root)
        path.symlink_to(ROOT / "LICENSE")
        with self.assertRaisesRegex(ValueError, "missing regular license"):
            distribution.selected(self.root)

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
        self.assertEqual(1, len(distribution.selected(self.root)))
        self.record["source"]["url"] = "https://example.invalid/project"
        self.write_policy()
        with self.assertRaisesRegex(ValueError, "not a homepage"):
            distribution.selected(self.root)

    def test_native_metadata_preserves_mrpack_contract(self):
        self.prepare_archives()
        index, contents = validate_mrpack.read_index(self.mrpack)
        self.assertEqual([], validate_mrpack.validate_index(index, contents, "26.2", "fabric", self.root)[0])
        self.assertEqual(2, len(index["files"]))
        self.assertFalse(any(name.lower().endswith(".jar") for name in contents))
        for name, data in distribution.notice_members(self.root).items():
            self.assertEqual(data, contents["overrides/" + name])

    def test_equivalent_source_and_recipient_credits_are_actionable(self):
        revision = "1" * 40
        self.record["source"] = {"status": "equivalent-access", "basis": "Complete owned fixture source.",
                                 "revision": revision, "url": "https://example.invalid/archive/" + revision + ".zip",
                                 "sha256": self.digest, "directions": "Download this exact source archive.",
                                 "verified_at": "2026-11-16"}
        self.record["note"] = "Internal reviewer evidence note, not recipient terms."
        self.write_policy()
        notices = distribution.notice_members(self.root)
        self.assertIn(self.record["source"]["url"].encode(), notices["SOURCES.md"])
        self.assertIn(revision.encode(), notices["SOURCES.md"])
        self.assertNotIn(self.record["note"].encode(), notices["CREDITS.md"])
        self.assertIn(b"\n\nLicense/permission:", notices["CREDITS.md"])

    def test_release_plan_always_selects_two_files_regardless_of_clearance(self):
        self.prepare_archives(hosted=False)
        self.record["note"] = "PRIVATE assessment must not appear in release notes"
        basename = "cobbled-horizon-26.2.0.1.0"
        for state in sorted(distribution.STATES):
            with self.subTest(state=state):
                self.record["channels"] = {channel: state for channel in distribution.CHANNELS}
                self.record.update({"texts": [], "nested": "unknown", "pending": ["No binary redistribution grant"],
                                    "source": {"status": "unknown", "basis": "Not established"}})
                self.write_policy()
                plan = distribution.release_plan(self.root, "v26.2.0.1.0")
                self.assertEqual([basename + ".mrpack", basename + ".mrpack.sha256"], plan["assets"])
                self.assertEqual(basename + ".mrpack.sha256", plan["checksum"])
                self.assertNotIn("mode", plan)
                self.assertIn("original host", plan["notes"])
                self.assertIn("configs and recipient notices", plan["notes"])
                self.assertNotIn(self.record["note"], plan["notes"])
        with self.assertRaises(ValueError):
            distribution.release_plan(self.root, "v26.3.0.1.0")

    def test_release_plan_rejects_invalid_records(self):
        self.prepare_archives(hosted=False)
        self.record["channels"]["github"] = "conditional"
        original = copy.deepcopy(self.record)
        for variant in ({"channels": {"github": "typo"}}, {"source": {"status": "typo"}},
                        {"pending": "not a list"}, {"metafile_sha256": "0" * 64},
                        {"source": {"status": "equivalent-access", "basis": "missing binding"}}):
            with self.subTest(variant=variant):
                self.record = {**original, **variant}
                self.write_policy()
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    distribution.release_plan(self.root)
        self.record = original
        self.write_policy()
        (self.root / "distribution/texts" / (self.digest + ".txt")).write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            distribution.release_plan(self.root)
        (self.root / "distribution/permissions.toml").write_text("not valid TOML!")
        with self.assertRaises(ValueError):
            distribution.release_plan(self.root)

    def test_real_workflow_selects_only_mrpack_and_checksum(self):
        self.prepare_archives()
        shutil.copytree(ROOT / "scripts", self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(ROOT / "Makefile", self.root / "Makefile")
        dist = self.root / "dist"
        dist.mkdir()
        basename = "cobbled-horizon-26.2.0.1.0"
        (dist / (basename + ".mrpack")).write_bytes(self.mrpack.read_bytes())
        (dist / (basename + ".mrpack.sha256")).write_text(
            hashlib.sha256(self.mrpack.read_bytes()).hexdigest() + "  " + basename + ".mrpack\n")
        script = workflow_script("Plan public release files")
        for cleared in (False, True):
            self.override_record["channels"]["github"] = "allowed" if cleared else "conditional"
            self.write_policy()
            for ref_type in ("branch", "tag"):
                with self.subTest(cleared=cleared, ref_type=ref_type):
                    output = self.root / "outputs"
                    output.write_text("")
                    result = subprocess.run(["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script], cwd=self.root,
                                            env={"PATH": os.environ["PATH"], "PYTHONDONTWRITEBYTECODE": "1", "GITHUB_REF_TYPE": ref_type,
                                                 "GITHUB_REF_NAME": "v26.2.0.1.0", "RUNNER_TEMP": str(self.root), "GITHUB_OUTPUT": str(output)},
                                            capture_output=True, text=True, timeout=30)
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                    plan = json.loads((self.root / "release-plan.json").read_text())
                    expected = [basename + ".mrpack", basename + ".mrpack.sha256"]
                    self.assertEqual(expected, plan["assets"])
                    self.assertEqual(["paths<<RELEASE_ASSETS", *("dist/" + name for name in expected), "RELEASE_ASSETS"],
                                     output.read_text().splitlines())
                    self.assertEqual(set(expected), {path.name for path in dist.iterdir()})

    def test_curated_inventory_has_both_lines_and_inactive_prospective_record(self):
        inventory = distribution.records(ROOT)
        identities = {(item["project"], item["version"], item["sha512"]) for item in inventory}
        self.assertEqual(len(inventory), len(identities))
        self.assertEqual(62, len(inventory))
        for line in ("26.2", "26.3"):
            self.assertEqual(32, sum(line in item["lines"] for item in inventory))
        self.assertEqual(["Cfbcv7uF"], [item["project"] for item in inventory if "prospective" in item["lines"]])
        self.assertNotIn("Cfbcv7uF", {item["project"] for _, item in distribution.selected(ROOT)})

    def test_uncleared_metadata_export_rejects_jars_and_private_members(self):
        self.prepare_archives()
        self.record["channels"]["github"] = "conditional"
        self.override_record["channels"]["github"] = "conditional"
        self.write_policy()
        policy = (self.root / "distribution/permissions.toml").read_bytes()
        _, contents = validate_mrpack.read_index(self.mrpack)
        base = {name: data for name, data in contents.items()
                if name == "modrinth.index.json" or name == "overrides/config/test.json"}
        for extra in (None, "overrides/mods/hidden.JAR", "overrides/config/floodgate/key.pem", "world/level.dat"):
            with self.subTest(extra=extra):
                with zipfile.ZipFile(self.mrpack, "w") as archive:
                    for name, data in base.items():
                        archive.writestr(name, data)
                    if extra:
                        archive.writestr(extra, b"must not publish")
                with patch.object(distribution, "ROOT", self.root), patch.object(sys, "argv", [
                        "distribution.py", "metadata-notices", "--archive", str(self.mrpack)]):
                    self.assertEqual(0 if extra is None else 1, distribution.main())
                if extra is None:
                    index, members = validate_mrpack.read_index(self.mrpack)
                    self.assertEqual([], validate_mrpack.validate_index(index, members, "26.2", "fabric", self.root)[0])
                    self.assertEqual(2, len(index["files"]))
                    self.assertFalse(any(name.lower().endswith(".jar") for name in members))
                    self.assertIn("overrides/CREDITS.md", members)
                    self.assertIn("overrides/SOURCES.md", members)
                    self.assertIn("overrides/LICENSES/" + self.digest + ".txt", members)
        self.assertEqual(policy, (self.root / "distribution/permissions.toml").read_bytes())


if __name__ == "__main__":
    unittest.main()
