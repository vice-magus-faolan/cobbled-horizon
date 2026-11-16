"""Release identity and CurseForge archive regression tests."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap
import tempfile
import unittest
import warnings
import zipfile
from unittest.mock import patch

from test_validation import load_script

release_metadata = load_script("release_metadata")
validate_curseforge = load_script("validate_curseforge")


class ReleaseMetadataTests(unittest.TestCase):
    def test_minecraft_prefixed_release_tag(self) -> None:
        for minecraft in ("26.2", "26.3"):
            with self.subTest(minecraft=minecraft):
                version = f"{minecraft}.0.1.0"
                pack = {"version": version, "versions": {"minecraft": minecraft}}
                values = release_metadata.metadata(pack, f"v{version}")
                self.assertEqual(version, values["version"])
                self.assertEqual(f"cobbled-horizon-{version}", values["basename"])

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

    def test_independent_branch_expectation_rejects_coordinated_retarget(self) -> None:
        for target, branch in (("26.2", "26.3"), ("26.3", "26.2")):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                # Both files agree: only the independently supplied branch can reject this.
                (root / "pack.toml").write_text(f'version = "{target}.0.1.0"\n[versions]\nminecraft = "{target}"\n')
                (root / "collection.toml").write_text(f'minecraft = "{target}"\nloader = "fabric"\n')
                for expected, accepted in ((target, True), (branch, False), ("topic/not-a-version", False)):
                    output, diagnostic = io.StringIO(), io.StringIO()
                    with patch.object(release_metadata, "ROOT", root), patch.object(sys, "argv", ["release_metadata.py", "--expected-minecraft", expected]), contextlib.redirect_stdout(output), contextlib.redirect_stderr(diagnostic):
                        if accepted:
                            self.assertEqual(0, release_metadata.main())
                            self.assertIn(f"minecraft={target}", output.getvalue())
                        else:
                            with self.assertRaises(SystemExit) as raised:
                                release_metadata.main()
                            self.assertEqual(2, raised.exception.code)
                            self.assertEqual("", output.getvalue())
                            self.assertIn("must match version branch", diagnostic.getvalue())

    def test_missing_and_malformed_minecraft_targets_are_rejected(self) -> None:
        for target in (None, "", "26", "26.x", "26.03", "26.3\n", 26):
            with self.subTest(target=target), self.assertRaises(ValueError):
                release_metadata.metadata({"version": "26.3.0.1.0", "versions": {"minecraft": target}})


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

    def test_setup_payload_and_indexed_private_state(self) -> None:
        from test_validation import permission_seed
        for relative in sorted(permission_seed.SEED_PATHS):
            source = self.root / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes((pathlib.Path(__file__).resolve().parents[1] / relative).read_bytes())
            with (self.root / "index.toml").open("a") as handle:
                handle.write(f"[[files]]\nfile = {json.dumps(relative)}\n")
            self.files["overrides/" + relative] = source.read_bytes()
        self.assertEqual([], self.validate())
        for relative in sorted(permission_seed.SEED_PATHS):
            key = "overrides/" + relative
            original = self.files.pop(key)
            self.assertIn("missing exported file: " + key, self.validate())
            self.files[key] = b"changed"
            self.assertIn("exported file hash differs from source: " + key, self.validate())
            self.files[key] = original
        for relative in ("config/luckperms/users.json", "config/cobbled-horizon/extra.json", "mods/luckperms/luckperms-h2.mv.db"):
            with self.subTest(relative=relative):
                target = self.root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"private canary")
                original = (self.root / "index.toml").read_text()
                (self.root / "index.toml").write_text(original + f"[[files]]\nfile = {json.dumps(relative)}\n")
                self.files["overrides/" + relative] = b"private canary"
                self.assertIn("unexpected source override: " + relative, self.validate())
                (self.root / "index.toml").write_text(original)
                del self.files["overrides/" + relative]
                target.unlink()

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


def workflow_script(step: str) -> str:
    """Execute a shipped run block without duplicating its publication logic."""
    root = pathlib.Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/validate.yml").read_text()
    block = workflow.split("      - name: " + step + "\n", 1)[1]
    return textwrap.dedent(block.split("run: |\n", 1)[1].split("\n      - name:", 1)[0])


class TaggedPublisherTests(unittest.TestCase):
    """Real selector/Make/validators/publisher, synthetic provider transport only."""

    def setUp(self):
        import test_distribution
        self.fixture = test_distribution.DistributionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        source, server = self.fixture.prepare_archives(hosted=False)
        test_distribution.server_pack.build_archive(source, server, self.root, self.fixture.mrpack)
        self.dist = self.root / "dist"
        self.dist.mkdir()
        self.basename = "cobbled-horizon-26.2.0.1.0"
        self.tag = "v26.2.0.1.0"
        self.archives = {".mrpack": self.fixture.mrpack.read_bytes(), ".zip": source.read_bytes(),
                         "-server.zip": server.read_bytes()}
        root = pathlib.Path(__file__).resolve().parents[1]
        shutil.copytree(root / "scripts", self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(root / "Makefile", self.root / "Makefile")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.provider = self.root / "provider.json"
        self.calls = self.root / "provider-calls.jsonl"
        # The substitute owns only provider state/transport. All publication
        # decisions and archive validation run unchanged production code.
        transport = self.bin / "gh"
        transport.write_text("#!" + sys.executable + "\n" + textwrap.dedent('''\
            import json, os, pathlib, subprocess, sys
            root = pathlib.Path(os.environ["PROVIDER_ROOT"])
            args = sys.argv[1:]
            with (root / "provider-calls.jsonl").open("a") as stream:
                stream.write(json.dumps(args) + "\\n")
            path = root / "provider.json"
            state = json.loads(path.read_text()) if path.exists() else None
            action = args[1]
            if action == "view":
                if state is None:
                    sys.exit(1)
                query = args[args.index("--jq") + 1]
                result = subprocess.run(["jq", "-r", query], input=json.dumps(state), text=True, timeout=5)
                sys.exit(result.returncode)
            if action == "create":
                assert "--draft" in args and "--verify-tag" in args
                state = {"isDraft": True, "assets": []}
            elif action == "upload":
                assert state["isDraft"] is True
                for name in args[3:]:
                    if name == "--clobber":
                        continue
                    state["assets"] = [item for item in state["assets"] if item["name"] != name]
                    if os.environ.get("PROVIDER_OMIT") == name:
                        continue
                    size = pathlib.Path(name).stat().st_size
                    if os.environ.get("PROVIDER_EMPTY"):
                        size = 0
                    state["assets"].append({"name": name, "size": size})
                    path.write_text(json.dumps(state))
                    if os.environ.get("PROVIDER_UPLOAD_FAIL"):
                        sys.exit(1)  # Preserve a genuinely partial upload for retry.
            elif action == "edit":
                assert "--draft=false" in args and "--verify-tag" in args
                state["isDraft"] = False
            else:
                raise AssertionError(args)
            if "--notes-file" in args:
                state["notes"] = pathlib.Path(args[args.index("--notes-file") + 1]).read_text()
            path.write_text(json.dumps(state))
            '''))
        transport.chmod(0o700)

    def stage(self, cleared: bool):
        self.fixture.record["channels"]["github"] = "allowed" if cleared else "conditional"
        self.fixture.write_policy()
        suffixes = (".mrpack", ".zip", "-server.zip") if cleared else (".mrpack",)
        for suffix in suffixes:
            (self.dist / (self.basename + suffix)).write_bytes(self.archives[suffix])
        self.checksum = self.basename + (".sha256" if cleared else ".mrpack.sha256")
        self.rehash()

    def rehash(self):
        names = sorted(path.name for path in self.dist.iterdir() if path.suffix in {".mrpack", ".zip"})
        # Contract order is mrpack, CurseForge, server (not lexical sorting).
        names.sort(key=lambda name: (not name.endswith(".mrpack"), name.endswith("-server.zip")))
        (self.dist / self.checksum).write_text("".join(
            hashlib.sha256((self.dist / name).read_bytes()).hexdigest() + "  " + name + "\n" for name in names))

    def publish(self, **extra):
        env = {"PATH": str(self.bin) + os.pathsep + os.environ["PATH"], "PYTHONDONTWRITEBYTECODE": "1",
               "RUNNER_TEMP": str(self.root), "TMPDIR": str(self.root), "PROVIDER_ROOT": str(self.root),
               "GITHUB_REF_NAME": self.tag, "GH_REPO": "owned/synthetic", **extra}
        result = subprocess.run(["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c",
                                 workflow_script("Reassess, validate and publish selected GitHub release")],
                                cwd=self.root, env=env, capture_output=True, text=True, timeout=30)
        calls = [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []
        return result, calls

    def assert_no_upload(self, result, calls):
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertFalse(any(call[1] in {"create", "upload", "edit"} for call in calls), calls)

    def test_both_modes_publish_exact_assets_and_refuse_published_rerun(self):
        for cleared in (False, True):
            with self.subTest(cleared=cleared):
                # Each independent provider/pack starts with ordinary fixture defaults.
                case = TaggedPublisherTests()
                case.setUp()
                try:
                    case.stage(cleared)
                    result, calls = case.publish()
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                    state = json.loads(case.provider.read_text())
                    self.assertFalse(state["isDraft"])
                    expected = [case.basename + suffix for suffix in
                                ((".mrpack", ".zip", "-server.zip", ".sha256") if cleared else (".mrpack", ".mrpack.sha256"))]
                    self.assertEqual(sorted(expected), sorted(item["name"] for item in state["assets"]))
                    self.assertTrue(all(item["size"] > 0 for item in state["assets"]))
                    self.assertIn("PASS: metadata-only .mrpack", result.stdout)
                    self.assertEqual(cleared, "PASS: complete server ZIP membership" in result.stdout)
                    if not cleared:
                        self.assertIn(case.fixture.record["name"], state["notes"])
                        self.assertIn("ZIPs are withheld", state["notes"])
                    previous = case.provider.read_bytes()
                    prior_calls = len(calls)
                    result, calls = case.publish()
                    case.assert_no_upload(result, calls[prior_calls:])
                    self.assertEqual(previous, case.provider.read_bytes())
                finally:
                    case.doCleanups()

    def test_bad_policy_identity_text_or_checksum_has_zero_provider_effects(self):
        self.stage(False)
        original = (self.root / "distribution/permissions.toml").read_bytes()
        for corrupt in ("policy", "identity", "text", "checksum", "tag", "extra", "empty", "missing"):
            with self.subTest(corrupt=corrupt):
                policy = self.root / "distribution/permissions.toml"
                metadata = self.fixture.metadata
                text = self.root / "distribution/texts" / (self.fixture.digest + ".txt")
                paths = [policy, metadata, text, *self.dist.iterdir()]
                before = {path: path.read_bytes() for path in paths}
                if corrupt == "policy":
                    policy.write_text("invalid TOML!")
                elif corrupt == "identity":
                    metadata.write_bytes(metadata.read_bytes() + b"\n# changed pin identity\n")
                elif corrupt == "text":
                    text.write_bytes(b"changed")
                elif corrupt == "checksum":
                    (self.dist / self.checksum).write_text("0" * 64 + "  " + self.basename + ".mrpack\n")
                elif corrupt == "tag":
                    self.tag = "v26.3.0.1.0"
                elif corrupt == "extra":
                    (self.dist / "unexpected.zip").write_bytes(b"must not upload")
                elif corrupt == "empty":
                    (self.dist / (self.basename + ".mrpack")).write_bytes(b"")
                    self.rehash()
                else:
                    (self.dist / (self.basename + ".mrpack")).unlink()
                result, calls = self.publish()
                self.assert_no_upload(result, calls)
                self.assertEqual([], calls)
                for path, data in before.items():
                    path.write_bytes(data)
                (self.dist / "unexpected.zip").unlink(missing_ok=True)
                self.tag = "v26.2.0.1.0"
        self.assertEqual(original, (self.root / "distribution/permissions.toml").read_bytes())

    def test_both_zip_validators_and_no_jar_metadata_are_enforced_before_upload(self):
        self.stage(True)
        for suffix in (".mrpack", ".zip", "-server.zip"):
            with self.subTest(suffix=suffix):
                path = self.dist / (self.basename + suffix)
                original = path.read_bytes()
                with zipfile.ZipFile(path, "a") as archive:
                    archive.writestr("overrides/mods/hidden.jar" if suffix == ".mrpack" else "secret.pem", b"invalid payload")
                self.rehash()  # Correct checksums cannot hide invalid archive contents.
                result, calls = self.publish()
                self.assert_no_upload(result, calls)
                self.assertEqual([], calls)
                path.write_bytes(original)
        self.rehash()

    def test_both_modes_recover_existing_and_partially_uploaded_drafts(self):
        for cleared in (False, True):
            for partial in (False, True):
                with self.subTest(cleared=cleared, partial=partial):
                    case = TaggedPublisherTests()
                    case.setUp()
                    try:
                        case.stage(cleared)
                        case.provider.write_text(json.dumps({"isDraft": True, "assets": []}))
                        expected = [case.basename + suffix for suffix in
                                    ((".mrpack", ".zip", "-server.zip", ".sha256") if cleared else (".mrpack", ".mrpack.sha256"))]
                        prior_calls = 0
                        if partial:
                            result, calls = case.publish(PROVIDER_UPLOAD_FAIL="1")
                            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                            state = json.loads(case.provider.read_text())
                            self.assertTrue(state["isDraft"])
                            self.assertEqual([expected[0]], [item["name"] for item in state["assets"]])
                            self.assertFalse(any(call[1] in {"create", "edit", "delete"} for call in calls))
                            prior_calls = len(calls)
                        result, calls = case.publish()
                        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                        state = json.loads(case.provider.read_text())
                        self.assertFalse(state["isDraft"])
                        self.assertEqual(sorted(expected), sorted(item["name"] for item in state["assets"]))
                        self.assertTrue(all(item["size"] > 0 for item in state["assets"]))
                        retry = calls[prior_calls:]
                        self.assertEqual(["release", "upload", case.tag, *expected, "--clobber"],
                                         next(call for call in retry if call[1] == "upload"))
                        self.assertEqual("edit", retry[-1][1])
                        self.assertFalse(any(call[1] in {"create", "delete"} for call in calls))
                    finally:
                        case.doCleanups()

    def test_both_modes_draft_missing_extra_empty_and_failed_upload_never_publish(self):
        for cleared in (False, True):
            with self.subTest(cleared=cleared):
                case = TaggedPublisherTests()
                case.setUp()
                try:
                    case.stage(cleared)
                    prior_calls = 0
                    for failure in ("missing", "extra", "empty", "transport"):
                        with self.subTest(failure=failure):
                            case.provider.write_text(json.dumps({"isDraft": True, "assets":
                                [{"name": "unexpected.zip", "size": 1}] if failure == "extra" else []}))
                            env = {"missing": {"PROVIDER_OMIT": case.checksum},
                                   "extra": {}, "empty": {"PROVIDER_EMPTY": "1"},
                                   "transport": {"PROVIDER_UPLOAD_FAIL": "1"}}[failure]
                            result, all_calls = case.publish(**env)
                            calls = all_calls[prior_calls:]
                            prior_calls = len(all_calls)
                            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                            state = json.loads(case.provider.read_text())
                            self.assertTrue(state["isDraft"])
                            self.assertTrue(any(call[1] == "upload" for call in calls))
                            if failure == "missing":
                                self.assertNotIn(case.checksum, [item["name"] for item in state["assets"]])
                            elif failure == "empty":
                                self.assertTrue(any(item["size"] == 0 for item in state["assets"]))
                            self.assertFalse(any(call[1] in {"create", "edit", "delete"} for call in calls))
                finally:
                    case.doCleanups()


if __name__ == "__main__":
    unittest.main()
