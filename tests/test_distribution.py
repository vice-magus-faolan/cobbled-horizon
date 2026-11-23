"""Distribution boundary and hosted-reference archive regressions.

All binary/source/permission fixtures are project-owned synthetic bytes. They
establish producer behavior, never permission for the real selected modpack.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
import unittest
import zipfile
from unittest.mock import patch

from pack_fixtures import ROOT
import distribution
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
            self.record["hosted_evidence"] = {"url": "https://www.curseforge.com/api/v1/mods/1/files/2/download",
                                               "sha256": hashlib.sha256(self.fixture.mod).hexdigest(),
                                               "sha512": self.record["sha512"], "at": "2026-11-16"}
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
        return self.root / "test.zip", self.root / "server"

    def test_exact_fixture_clearance_and_deterministic_full_notices(self):
        for channel in distribution.CHANNELS:
            self.assertEqual(1, len(distribution.clearance(self.root, channel)))
        first = distribution.notice_members(self.root)
        self.assertEqual(first, distribution.notice_members(self.root))
        self.assertEqual(self.text, first["LICENSES/" + self.digest + ".txt"])
        self.assertIn(b"Copyright (c) 2026 jabez007 and contributors\n", first["LICENSES/" + self.digest + ".txt"])
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
        self.assertEqual("jabez007 and contributors", distribution.load(ROOT / "pack.toml")["author"])
        for attribution in (
            b"jabez007's pack-owner risk decision of 2026-11-16",
            b"Pack owner jabez007 decided on 2026-11-17 to distribute this MIT-declared copy",
            b"Pack owner jabez007 decided on 2026-11-17 to distribute this distinct MIT-declared copy",
        ):
            with self.subTest(attribution=attribution):
                self.assertIn(attribution, notices["CREDITS.md"])
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

    def test_curseforge_platform_is_independent_of_otherwise_fulfilled_rights(self):
        # This is a bundled, otherwise fully eligible JAR, not a CF reference.
        self.record["platform"] = "unknown"
        self.write_policy()
        self.assertEqual(1, len(distribution.clearance(self.root, "github")))
        with self.assertRaisesRegex(ValueError, "distribution not cleared for curseforge"):
            distribution.clearance(self.root, "curseforge")
        self.record["platform"] = "verified"
        self.write_policy()
        self.assertEqual(1, len(distribution.clearance(self.root, "curseforge")))

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

    def test_real_hosted_partition_preserves_archive_contract(self):
        source, _ = self.prepare_archives()
        distribution.clearance(self.root, "github")
        with zipfile.ZipFile(source) as archive:
            self.assertNotIn("overrides/mods/test.jar", archive.namelist())
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

    def test_hosted_evidence_must_bind_selected_download_hash(self):
        self.prepare_archives()
        matching = copy.deepcopy(self.record["hosted_evidence"])
        self.assertEqual(2, len(distribution.clearance(self.root, "github")))
        for evidence in ({**matching, "sha512": "0" * 128}, "unstructured claim", {},
                         {**matching, "url": "http://example.invalid/owned.jar"}):
            with self.subTest(evidence=evidence):
                self.record["hosted_evidence"] = evidence
                self.write_policy()
                with self.assertRaisesRegex(ValueError, "hosted mapping evidence"):
                    distribution.clearance(self.root, "github")
        self.record["hosted_evidence"] = matching
        self.write_policy()
        self.assertEqual(2, len(distribution.clearance(self.root, "curseforge")))

    def test_equivalent_source_and_recipient_credits_are_actionable(self):
        revision = "1" * 40
        self.record["source"] = {"status": "equivalent-access", "basis": "Complete owned fixture source.",
                                 "revision": revision, "url": "https://example.invalid/archive/" + revision + ".zip",
                                 "sha256": self.digest, "directions": "Download this exact source archive.",
                                 "verified_at": "2026-11-16"}
        self.record["note"] = "Internal reviewer evidence note, not recipient terms."
        self.write_policy()
        distribution.clearance(self.root, "github")
        notices = distribution.notice_members(self.root)
        self.assertIn(self.record["source"]["url"].encode(), notices["SOURCES.md"])
        self.assertIn(revision.encode(), notices["SOURCES.md"])
        self.assertNotIn(self.record["note"].encode(), notices["CREDITS.md"])
        self.assertIn(b"\n\nLicense/permission:", notices["CREDITS.md"])

    def test_release_plan_selects_two_or_three_assets_and_only_bundled_blockers(self):
        self.prepare_archives(hosted=False)
        self.record["channels"]["github"] = "conditional"
        self.record["note"] = "PRIVATE assessment must not appear in release notes"
        self.write_policy()
        metadata = distribution.release_plan(self.root, "v26.2.0.1.0")
        basename = "cobbled-horizon-26.2.0.1.0"
        self.assertEqual([basename + ".mrpack", basename + ".mrpack.sha256"], metadata["assets"])
        self.assertEqual("metadata", metadata["mode"])
        self.assertIn(self.record["name"], metadata["notes"])
        self.assertNotIn(self.override_record["name"], metadata["notes"])
        self.assertNotIn(self.record["note"], metadata["notes"])
        self.record["channels"]["github"] = "allowed"
        self.write_policy()
        full = distribution.release_plan(self.root, "v26.2.0.1.0")
        self.assertEqual([basename + suffix for suffix in (".mrpack", ".zip", ".sha256")], full["assets"])
        self.assertEqual("full", full["mode"])
        with self.assertRaises(ValueError):
            distribution.release_plan(self.root, "v26.3.0.1.0")

    def test_release_plan_never_converts_invalid_input_to_metadata(self):
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

    def test_reference_unresolved_is_eligible_but_bundled_unresolved_withholds_zip(self):
        self.prepare_archives()
        self.record.update({"license": "ARR", "texts": [], "nested": "unknown", "pending": ["No binary redistribution grant"],
                            "channels": {channel: "unknown" for channel in distribution.CHANNELS},
                            "source": {"status": "unknown", "basis": "Not established"}})
        self.write_policy()
        self.assertEqual("full", distribution.release_plan(self.root)["mode"])
        self.assertEqual(2, len(distribution.clearance(self.root, "github")))
        self.override_record["channels"]["github"] = "unknown"
        self.write_policy()
        plan = distribution.release_plan(self.root)
        self.assertEqual("metadata", plan["mode"])
        self.assertIn(self.override_record["name"], plan["notes"])
        self.assertNotIn(self.record["name"], plan["notes"])
        # Without a verified mapping this is an unresolved bundled JAR, not
        # platform-wide absence. Metadata remains eligible.
        self.metadata.write_text(self.metadata.read_text().split('[update.curseforge]')[0])
        self.record.pop("hosted")
        self.record.pop("hosted_evidence")
        self.record["metafile_sha256"] = hashlib.sha256(self.metadata.read_bytes()).hexdigest()
        self.override_record["channels"]["github"] = "allowed"
        self.write_policy()
        self.assertEqual("metadata", distribution.release_plan(self.root)["mode"])

    def test_reference_mapping_corruption_is_fatal_even_when_bundle_is_uncleared(self):
        self.prepare_archives()
        self.override_record["channels"]["github"] = "unknown"
        original = copy.deepcopy(self.record)
        original_metadata = self.metadata.read_bytes()
        for defect in ("missing", "hash", "file", "native-file", "boolean", "source", "text"):
            with self.subTest(defect=defect):
                self.metadata.write_bytes(original_metadata)
                self.record = copy.deepcopy(original)
                if defect == "missing":
                    self.record.pop("hosted_evidence")
                elif defect == "hash":
                    self.record["hosted_evidence"]["sha512"] = "0" * 128
                elif defect == "file":
                    self.record["hosted_evidence"]["url"] = "https://www.curseforge.com/api/v1/mods/1/files/3/download"
                elif defect in {"native-file", "boolean"}:
                    value = "3" if defect == "native-file" else "true"
                    self.metadata.write_text(self.metadata.read_text().replace("file-id = 2", "file-id = " + value))
                    self.record["hosted"]["file-id"] = 3 if defect == "native-file" else True
                    self.record["metafile_sha256"] = hashlib.sha256(self.metadata.read_bytes()).hexdigest()
                elif defect == "source":
                    self.record["source"] = {"status": "equivalent-access", "basis": "missing exact identity"}
                else:
                    self.record["texts"] = ["0" * 64]
                self.write_policy()
                with self.assertRaises(ValueError):
                    distribution.release_plan(self.root)

    def test_selected_reference_partition_keeps_fabric_and_all_original_pins(self):
        items = distribution.selected(ROOT)
        references = validate_curseforge.hosted_files(ROOT)
        targets = {"mods/" + mod["filename"] for mod, _ in items}
        bundled = targets - references.keys()
        self.assertEqual(32, len(targets))
        self.assertEqual(6, len(references))
        self.assertEqual(26, len(bundled))
        self.assertFalse(bundled & references.keys())
        self.assertEqual(targets, bundled | references.keys())
        self.assertEqual({
            (306612, 9295874), (698309, 9509145), (342584, 9394030),
            (345854, 9272149), (920416, 8926271), (547434, 8938808),
        }, {(item["projectID"], item["fileID"]) for item in references.values()})
        self.assertTrue(all(item["required"] is True for item in references.values()))
        for mod, record in items:
            if "curseforge" in mod["update"]:
                if record["project"] == "ohNO6lps":
                    self.assertEqual("allowed", record["channels"]["github"])
                    self.assertEqual("b9339c21e14beec2eae0ca215317284bcaacef72e1d1dee8b3dfbe2de0eefaa758a172446df85419b6534557c479abe972d7d21f4ec194f2d436f9ed4329cb9f", mod["download"]["hash"])
                    self.assertNotIn("mods/" + mod["filename"], bundled)
                elif record["project"] != "P7dR8mSH":
                    self.assertEqual("unknown", record["channels"]["github"])
                self.assertEqual(mod["download"]["hash"], record["hosted_evidence"]["sha512"])

    def test_real_workflow_withholds_uncleared_uploads_and_accepts_metadata_tags(self):
        # Owned policy varies independently of the live pack's clearance state.
        import os
        import shutil
        self.prepare_archives(hosted=True)
        shutil.copytree(ROOT / "scripts", self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        script = test_release.workflow_script("Evaluate public distribution clearance")
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
                    self.assertTrue(output.read_text().startswith("cleared=" + str(cleared).lower() + "\n"))
                    plan = json.loads((self.root / "release-plan.json").read_text())
                    self.assertEqual(3 if cleared else 2, len(plan["assets"]))
                    self.assertEqual(["dist/" + name for name in plan["assets"]], output.read_text().splitlines()[2:-1])
                    self.assertEqual(not cleared, "public ZIP is withheld" in result.stdout)

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
        self.assertEqual(policy, (self.root / "distribution/permissions.toml").read_bytes())
        with self.assertRaisesRegex(ValueError, "distribution not cleared"):
            distribution.clearance(self.root, "github")

    def test_channel_check_refuses_before_any_archive_or_network_effect(self):
        self.record["channels"]["github"] = "unknown"
        self.write_policy()
        with patch.object(distribution, "ROOT", self.root), patch.object(sys, "argv", ["distribution.py", "notices", "--channel", "github", "--archive", str(self.root / "absent.zip")]), patch.object(distribution.zipfile, "ZipFile") as archive:
            self.assertEqual(1, distribution.main())
        archive.assert_not_called()


if __name__ == "__main__":
    unittest.main()
