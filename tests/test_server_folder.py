"""Real mrpack preparation with controlled project-owned upstream downloads."""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import unittest
import warnings
import zipfile
from unittest.mock import patch

from pack_fixtures import ROOT
import distribution
import permission_seed
import server_folder
import validate_mrpack

import test_distribution


class ServerFolderTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_distribution.DistributionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.prepare_archives()
        self.root = self.fixture.root
        self.source = self.fixture.mrpack
        self.output = self.root / "server"
        _, self.contents = validate_mrpack.read_index(self.source)
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
        with patch.object(server_folder.urllib.request, "urlopen", side_effect=[io.BytesIO(self.fixture.fixture.mod), io.BytesIO(self.fixture.override_bytes)]) as download:
            server_folder.materialize(self.source, destination or self.output, self.root)
        return download

    def test_complete_root_payload_and_input_preservation(self):
        before = self.source.read_bytes()
        download = self.materialize()
        self.assertEqual(2, download.call_count)
        self.assertEqual(before, self.source.read_bytes())
        self.assertEqual(set(self.payload), {path.relative_to(self.output).as_posix() for path in self.output.rglob("*") if path.is_file()})
        for name, data in self.payload.items():
            self.assertEqual(data, (self.output / name).read_bytes())
        self.assertEqual([], server_folder.validate_directory(self.output, self.root))
        self.assertEqual([], list(self.root.glob(".materialize-*")))

    def test_materialize_downloads_uncleared_pins_without_public_bypass(self):
        self.fixture.override_record["channels"]["github"] = "conditional"
        self.fixture.write_policy()
        argv = ["server_folder.py", "materialize", str(self.source), str(self.output)]
        with patch.object(server_folder, "ROOT", self.root), patch.object(sys, "argv", argv), \
                patch.object(server_folder.urllib.request, "urlopen", side_effect=[io.BytesIO(self.fixture.fixture.mod), io.BytesIO(self.fixture.override_bytes)]) as download:
            self.assertEqual(0, server_folder.main())
        self.assertEqual(2, download.call_count)
        self.assertEqual([], server_folder.validate_directory(self.output, self.root))
        with self.assertRaisesRegex(ValueError, "distribution not cleared"):
            distribution.clearance(self.root, "github")

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
                with patch.object(server_folder.urllib.request, "urlopen") as download:
                    with self.assertRaises(ValueError):
                        server_folder.materialize(self.source, self.output, self.root)
                download.assert_not_called()
                self.assertFalse(self.output.exists())
                self.assertFalse((self.root / "escape").exists())

    def test_missing_changed_and_private_root_files_are_rejected(self):
        self.materialize()
        for name, data in self.payload.items():
            target = self.output / name
            target.unlink()
            self.assertTrue(server_folder.validate_directory(self.output, self.root), name)
            target.write_bytes(b"changed")
            self.assertTrue(server_folder.validate_directory(self.output, self.root), name)
            target.write_bytes(data)
        for name in ("world/level.dat", "logs/latest.log", "config/floodgate/key.pem", "mods/client.jar", "mods/luckperms/users.json", "server.jar"):
            target = self.output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"private")
            self.assertIn("unexpected server entry: " + name, server_folder.validate_directory(self.output, self.root))
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
                with patch.object(server_folder.urllib.request, "urlopen") as download:
                    with self.assertRaises(FileExistsError):
                        server_folder.materialize(self.source, target, self.root)
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
                with patch.object(server_folder.urllib.request, "urlopen", side_effect=responses):
                    expected = OSError if failure == "transport" else ValueError
                    message = {"hash": "hash mismatch", "size": "size differs", "transport": "controlled failed download"}[failure]
                    with self.assertRaisesRegex(expected, message):
                        server_folder.materialize(self.source, self.output, self.root)
                self.assertFalse(self.output.exists())
                self.assertEqual([], list(self.root.glob(".materialize-*")))

    def test_symlink_cannot_masquerade_as_payload_or_directory(self):
        self.materialize()
        target = self.output / "mods/test.jar"
        target.unlink()
        target.symlink_to(self.source)
        self.assertIn("unsafe server entry type: mods/test.jar", server_folder.validate_directory(self.output, self.root))
        self.assertTrue(server_folder.validate_directory(self.output / "mods/test.jar", self.root))

    def test_source_side_and_unsafe_filename_are_rejected(self):
        path = self.fixture.metadata
        original = path.read_text()
        for text in (original.replace('side = "server"', 'side = "client"'), original.replace('filename = "test.jar"', 'filename = "../escape.jar"')):
            with self.subTest(text=text):
                path.write_text(text)
                with patch.object(server_folder.urllib.request, "urlopen") as download:
                    with self.assertRaises(ValueError):
                        server_folder.materialize(self.source, self.output, self.root)
                download.assert_not_called()
                self.assertFalse(self.output.exists())
        path.write_text(original)

    def test_malformed_input_does_not_create_folder_or_destroy_input(self):
        self.source.write_bytes(b"not a ZIP")
        with self.assertRaises(zipfile.BadZipFile):
            server_folder.materialize(self.source, self.output, self.root)
        self.assertEqual(b"not a ZIP", self.source.read_bytes())
        self.assertFalse(self.output.exists())

    def test_private_zip_has_deterministic_root_payload_and_metadata(self):
        self.materialize()
        first = self.root / "first.zip"
        size = server_folder.server_zip(self.output, first, self.root)
        self.assertEqual(first.stat().st_size, size)
        with zipfile.ZipFile(first) as archive:
            self.assertEqual(sorted(archive.namelist()), archive.namelist())
            self.assertEqual(set(self.payload), {info.filename for info in archive.infolist() if not info.is_dir()})
            for info in archive.infolist():
                self.assertEqual((1980, 1, 1, 0, 0, 0), info.date_time)
                self.assertEqual(3, info.create_system)
                self.assertEqual((stat.S_IFDIR | 0o755) if info.is_dir() else (stat.S_IFREG | 0o644), info.external_attr >> 16)
                self.assertEqual(0x10 if info.is_dir() else 0, info.external_attr & 0xFFFF)
                self.assertEqual(b"", info.comment)
                self.assertNotIn("\\", info.filename)
                self.assertFalse(info.filename.startswith(("/", "server/", "overrides/")))
                if not info.is_dir():
                    self.assertEqual(self.payload[info.filename], archive.read(info))
        for path in self.output.rglob("*"):
            path.chmod(0o700 if path.is_dir() else 0o600)
            os.utime(path, (1_700_000_000, 1_700_000_000))
        second = self.root / "second.zip"
        server_folder.server_zip(self.output, second, self.root)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual([], list(self.root.glob(".server-zip-*")))

    def test_zip_refuses_existing_paths_and_concurrent_creator(self):
        self.materialize()
        for kind in ("file", "directory", "symlink"):
            with self.subTest(kind=kind):
                target = self.root / (kind + ".zip")
                if kind == "directory":
                    target.mkdir()
                    (target / "canary").write_bytes(b"preserve")
                elif kind == "symlink":
                    target.symlink_to(self.root / "absent")
                else:
                    target.write_bytes(b"preserve")
                with self.assertRaises(FileExistsError):
                    server_folder.server_zip(self.output, target, self.root)
                if kind == "symlink":
                    self.assertTrue(target.is_symlink())
                else:
                    self.assertEqual(b"preserve", (target / "canary" if kind == "directory" else target).read_bytes())
        destination = self.root / "race.zip"
        link = os.link

        def competing_link(source, target):
            target.write_bytes(b"concurrent owner")
            link(source, target)

        with patch.object(server_folder.os, "link", side_effect=competing_link):
            with self.assertRaises(FileExistsError):
                server_folder.server_zip(self.output, destination, self.root)
        self.assertEqual(b"concurrent owner", destination.read_bytes())
        self.assertEqual([], list(self.root.glob(".server-zip-*")))

    def test_zip_revalidates_and_never_archives_private_or_changed_payload(self):
        self.materialize()
        destination = self.root / "private.zip"
        target = self.output / "mods/test.jar"
        original = target.read_bytes()
        target.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "server file hash differs from source: mods/test.jar"):
            server_folder.server_zip(self.output, destination, self.root)
        self.assertFalse(destination.exists())
        target.write_bytes(original)
        for name in ("world/level.dat", "config/floodgate/key.pem", "mods/luckperms/users.json"):
            target = self.output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"private")
        with self.assertRaisesRegex(ValueError, "invalid server folder"):
            server_folder.server_zip(self.output, destination, self.root)
        self.assertFalse(destination.exists())
        self.assertEqual([], list(self.root.glob(".server-zip-*")))

    def test_zip_write_failure_exposes_no_partial_archive(self):
        self.materialize()
        destination = self.root / "failed.zip"
        with patch.object(server_folder.shutil, "copyfileobj", side_effect=OSError("controlled write failure")):
            with self.assertRaisesRegex(OSError, "controlled write failure"):
                server_folder.server_zip(self.output, destination, self.root)
        self.assertFalse(destination.exists())
        self.assertEqual([], list(self.root.glob(".server-zip-*")))

    def test_zip_cli_reports_actual_size_and_warning_boundary_without_public_clearance(self):
        self.fixture.override_record["channels"]["github"] = "conditional"
        self.fixture.write_policy()
        self.materialize()
        reference = self.root / "reference.zip"
        size = server_folder.server_zip(self.output, reference, self.root)
        self.assertEqual(100_000_000, server_folder.WEB_UPLOAD_LIMIT)
        for limit, warning in ((size, False), (size - 1, True)):
            destination = self.root / (str(limit) + ".zip")
            output = io.StringIO()
            argv = ["server_folder.py", "zip", str(self.output), str(destination)]
            with patch.object(server_folder, "ROOT", self.root), patch.object(sys, "argv", argv), \
                    patch.object(server_folder, "WEB_UPLOAD_LIMIT", limit), patch("sys.stdout", output):
                self.assertEqual(0, server_folder.main())
            self.assertIn(f"({destination.stat().st_size} bytes)", output.getvalue())
            self.assertEqual(warning, "WARNING:" in output.getvalue())
            self.assertEqual(reference.read_bytes(), destination.read_bytes())
        with self.assertRaisesRegex(ValueError, "distribution not cleared"):
            distribution.clearance(self.root, "github")

    def test_public_selector_excludes_existing_private_zip_in_both_modes(self):
        self.materialize()
        private = self.root / "build/cobbled-horizon-26.2.0.1.0-server.zip"
        shutil.copytree(ROOT / "scripts", self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(ROOT / "Makefile", self.root / "Makefile")
        # The materializer is covered above. Exercise the real Make ZIP recipe
        # on its complete synthetic output, without downloads or source refresh.
        result = subprocess.run(["make", "-o", "materialize", "server-zip", "SERVER_DIR=" + str(self.output)],
                                cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn(f"({private.stat().st_size} bytes)", result.stdout)
        original = private.read_bytes()
        script = test_distribution.test_release.workflow_script("Evaluate public distribution clearance")
        for cleared in (False, True):
            with self.subTest(cleared=cleared):
                self.fixture.override_record["channels"]["github"] = "allowed" if cleared else "conditional"
                self.fixture.write_policy()
                output = self.root / "outputs"
                output.write_text("")
                result = subprocess.run(["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
                                        cwd=self.root, env={**os.environ, "GITHUB_REF_TYPE": "tag",
                                        "GITHUB_REF_NAME": "v26.2.0.1.0", "RUNNER_TEMP": str(self.root),
                                        "GITHUB_OUTPUT": str(output)}, capture_output=True, text=True, timeout=30)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                plan = json.loads((self.root / "release-plan.json").read_text())
                suffixes = (".mrpack", ".zip", ".sha256") if cleared else (".mrpack", ".mrpack.sha256")
                self.assertEqual(["cobbled-horizon-26.2.0.1.0" + suffix for suffix in suffixes], plan["assets"])
                self.assertEqual(["dist/" + name for name in plan["assets"]], output.read_text().splitlines()[2:-1])
                self.assertNotIn(private.name, plan["assets"])
                forged = {**plan, "assets": [*plan["assets"], private.name]}
                with self.assertRaisesRegex(ValueError, "release plan differs"):
                    distribution.verify_release(self.root, forged, private.parent)
                self.assertEqual(original, private.read_bytes())

    def test_workflow_keeps_private_build_out_of_build_upload_and_cache(self):
        # Inspect effect-bearing workflow fields, not global mentions in docs
        # or tests: CI may run synthetic archive regressions, never this build.
        workflow = (ROOT / ".github/workflows/validate.yml").read_text()
        self.assertNotRegex(workflow, r"(?m)^\s*uses:\s*actions/cache(?:/|@)")
        runs = re.findall(r"(?ms)^        run: (.*?)(?=^      - name:|^  [a-z]|\Z)", workflow)
        self.assertTrue(runs)
        for run in runs:
            self.assertNotRegex(run, r"\bmake\b[^\n]*\bserver-zip\b")
            self.assertNotRegex(run, r"server_folder\.py\s+zip\b")
        uploads = [block for block in workflow.split("      - name:") if "uses: actions/upload-artifact@" in block]
        self.assertEqual(2, len(uploads))
        self.assertIn("path: ${{ steps.rights.outputs.paths }}", uploads[0])
        paths = uploads[1].split("          path: |\n", 1)[1].split("          if-no-files-found:", 1)[0].splitlines()
        self.assertEqual({"summary.json", "installer.log", "first-boot.log", "offline-second-boot.log"},
                         {path.strip().rsplit("/", 1)[-1] for path in paths})
        self.assertTrue(all("/ch-native-evidence-" in path for path in paths))


if __name__ == "__main__":
    unittest.main()
