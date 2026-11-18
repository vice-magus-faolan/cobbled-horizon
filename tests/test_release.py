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

from pack_fixtures import load_script
import permission_seed

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
        source, _ = self.fixture.prepare_archives(hosted=True)
        self.fixture.record["channels"] = {channel: "unknown" for channel in self.fixture.record["channels"]}
        self.fixture.write_policy()  # References never convey these uncleared bytes.
        self.dist = self.root / "dist"
        self.dist.mkdir()
        self.basename = "cobbled-horizon-26.2.0.1.0"
        self.tag = "v26.2.0.1.0"
        self.archives = {".mrpack": self.fixture.mrpack.read_bytes(), ".zip": source.read_bytes()}
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
            import json, os, pathlib, sys
            root = pathlib.Path(os.environ["PROVIDER_ROOT"])
            args = sys.argv[1:]
            with (root / "provider-calls.jsonl").open("a") as stream:
                stream.write(json.dumps(args) + "\\n")
            path = root / "provider.json"
            state = json.loads(path.read_text()) if path.exists() else None
            if args[0] == "api":
                assert args == ["api", "repos/{owner}/{repo}/releases", "--paginate", "--jq",
                                '.[] | select(.draft == false and .prerelease == false) | .tag_name'], args
                pages = json.loads(os.environ.get("PROVIDER_RELEASE_PAGES", "[[]]"))
                for page in pages:
                    for item in page:
                        if not item["draft"] and not item["prerelease"]:
                            print(item["tag_name"])
                if os.environ.get("PROVIDER_LIST_FAIL"):
                    sys.exit(1)  # Partial page output must not become success.
                sys.exit(0)
            action = args[1]
            if action == "view":
                if state is None:
                    sys.exit(1)
                fields = args[args.index("--json") + 1]
                query = args[args.index("--jq") + 1]
                expected_queries = {
                    "isDraft": ".isDraft",
                    "assets": 'if all(.assets[]; .size > 0) then .assets | map(.name) | sort | .[] else error("empty release asset") end',
                }
                assert query == expected_queries[fields], (fields, query)
                if fields == "isDraft":
                    print(json.dumps(state["isDraft"]))
                elif fields == "assets":
                    if any(item["size"] <= 0 for item in state["assets"]):
                        sys.exit(1)
                    for name in sorted(item["name"] for item in state["assets"]):
                        print(name)
                else:
                    raise AssertionError(fields)
                sys.exit(0)
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
                latest = [value for value in args if value.startswith("--latest=")]
                assert len(latest) == 1 and latest[0] in {"--latest=true", "--latest=false"}, args
                state["latest"] = latest[0] == "--latest=true"
                state["isDraft"] = False
            else:
                raise AssertionError(args)
            if "--notes-file" in args:
                state["notes"] = pathlib.Path(args[args.index("--notes-file") + 1]).read_text()
            path.write_text(json.dumps(state))
            '''))
        transport.chmod(0o700)
        # The existing fixture PATH contains only publication prerequisites,
        # deliberately not jq, even when it is installed on the test host.
        for name in ("bash", "make", "sha256sum", "sort"):
            (self.bin / name).symlink_to(shutil.which(name))
        (self.bin / "python3").symlink_to(sys.executable)

    def stage(self, cleared: bool):
        self.fixture.override_record["channels"]["github"] = "allowed" if cleared else "conditional"
        self.fixture.write_policy()
        suffixes = (".mrpack", ".zip") if cleared else (".mrpack",)
        for suffix in suffixes:
            (self.dist / (self.basename + suffix)).write_bytes(self.archives[suffix])
        self.checksum = self.basename + (".sha256" if cleared else ".mrpack.sha256")
        self.rehash()

    def rehash(self):
        names = sorted(path.name for path in self.dist.iterdir() if path.suffix in {".mrpack", ".zip"})
        # Contract order is mrpack, CurseForge (not lexical sorting).
        names.sort(key=lambda name: not name.endswith(".mrpack"))
        (self.dist / self.checksum).write_text("".join(
            hashlib.sha256((self.dist / name).read_bytes()).hexdigest() + "  " + name + "\n" for name in names))

    def publish(self, **extra):
        env = {"PATH": str(self.bin), "PYTHONDONTWRITEBYTECODE": "1",
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
                    self.assertTrue(state["latest"])  # Empty published inventory.
                    expected = [case.basename + suffix for suffix in
                                ((".mrpack", ".zip", ".sha256") if cleared else (".mrpack", ".mrpack.sha256"))]
                    self.assertEqual(sorted(expected), sorted(item["name"] for item in state["assets"]))
                    self.assertTrue(all(item["size"] > 0 for item in state["assets"]))
                    self.assertIn("PASS: metadata-only .mrpack", result.stdout)
                    self.assertEqual(cleared, "PASS: CurseForge-format ZIP" in result.stdout)
                    if not cleared:
                        self.assertIn(case.fixture.override_record["name"], state["notes"])
                        self.assertIn("ZIP is withheld", state["notes"])
                    previous = case.provider.read_bytes()
                    prior_calls = len(calls)
                    result, calls = case.publish()
                    case.assert_no_upload(result, calls[prior_calls:])
                    self.assertEqual(previous, case.provider.read_bytes())
                finally:
                    case.doCleanups()

    def test_latest_compares_versions_across_all_published_pages(self):
        def release(tag, **extra):
            return {"tag_name": tag, "draft": False, "prerelease": False, **extra}

        # Newer creation dates/order cannot conceal a higher old version on
        # another page. Also distinguish numeric from lexical version order.
        recent = [release(f"v26.1.0.0.{number}") for number in range(30)]
        inventories = (
            ([recent, [release("v26.3.0.1.4")]], False),
            ([[release("v26.10.0.0.0"), release("v26.1.0.99.99")]], False),
            ([[release("v26.1.0.99.99"), release("v99.0.0.0.0", draft=True),
               release("v99.0.0.0.1", prerelease=True)]], True),
        )
        for pages, expected in inventories:
            for cleared in (False, True):
                with self.subTest(pages=pages, cleared=cleared):
                    case = TaggedPublisherTests()
                    case.setUp()
                    try:
                        case.stage(cleared)
                        result, calls = case.publish(PROVIDER_RELEASE_PAGES=json.dumps(pages))
                        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                        state = json.loads(case.provider.read_text())
                        self.assertFalse(state["isDraft"])
                        self.assertEqual(expected, state["latest"])
                        self.assertIn("--latest=" + str(expected).lower(), calls[-1])
                        self.assertEqual("api", calls[0][0])
                    finally:
                        case.doCleanups()

    def test_unavailable_or_malformed_inventory_has_no_publication_effects(self):
        self.stage(False)
        published = [[{"tag_name": "v26.3.0.1.4", "draft": False, "prerelease": False}]]
        for extra in ({"PROVIDER_LIST_FAIL": "1", "PROVIDER_RELEASE_PAGES": json.dumps(published)},
                      {"PROVIDER_RELEASE_PAGES": json.dumps([[{"tag_name": "unparseable", "draft": False, "prerelease": False}]])}):
            with self.subTest(extra=extra):
                prior = len(self.calls.read_text().splitlines()) if self.calls.exists() else 0
                result, calls = self.publish(**extra)
                self.assert_no_upload(result, calls[prior:])
                self.assertFalse(self.provider.exists())

    def test_changed_provider_queries_fail_publisher_regression(self):
        script = workflow_script("Reassess, validate and publish selected GitHub release")
        for query, wrong in (("--jq .isDraft", "--jq .draft"),
                             ("map(.name)", "map(.size)"),
                             ("--paginate", "--no-paginate"),
                             (".tag_name", ".name")):
            with self.subTest(query=query):
                self.assertIn(query, script)
                # Run the existing real-publisher regression, including its
                # published-rerun assertions: a failed draft query can otherwise
                # fall through to creation and appear to publish successfully.
                case = TaggedPublisherTests("test_both_modes_publish_exact_assets_and_refuse_published_rerun")
                result = unittest.TestResult()
                with patch("test_release.workflow_script", return_value=script.replace(query, wrong)):
                    case.run(result)
                self.assertEqual([], result.errors)
                self.assertTrue(result.failures)
                self.assertIn(wrong.removeprefix("--jq "), result.failures[0][1])

    def test_default_build_refreshes_plan_but_explicit_plans_remain_frozen(self):
        import distribution
        self.stage(False)
        stale = distribution.release_plan(self.root, self.tag)
        default = self.root / "release-plan.json"
        default.write_text(json.dumps(stale))
        (self.dist / self.checksum).unlink()
        self.stage(True)
        # Real release recipe; the fixture's valid archives model completed
        # exporter targets. Do not run third-party downloads or source refresh.
        command = ["make", "-o", "export", "release", "MAKE=make -o export-curseforge"]
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("RELEASE_PLAN", None)
        result = subprocess.run(command, cwd=self.root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        fresh = distribution.release_plan(self.root, self.tag)
        self.assertEqual(fresh, json.loads(default.read_text()))
        self.assertFalse((self.dist / (self.basename + ".mrpack.sha256")).exists())
        self.assertIn("PASS: CurseForge-format ZIP", result.stdout)
        frozen = self.root / "frozen.json"
        for plan, accepted in ((fresh, True), (stale, False), ({**fresh, "tag": "v26.2.0.1.1"}, False)):
            with self.subTest(plan=plan["mode"], tag=plan["tag"]):
                frozen.write_text(json.dumps(plan, indent=2) + "\n")
                original = frozen.read_bytes()
                result = subprocess.run([*command, "RELEASE_PLAN=" + str(frozen)], cwd=self.root, env=env,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(accepted, result.returncode == 0, result.stdout + result.stderr)
                self.assertEqual(original, frozen.read_bytes())
                if not accepted:
                    self.assertIn("release plan differs", result.stdout)

    def test_verify_release_discriminates_frozen_plan_independently(self):
        import distribution
        for cleared in (False, True):
            with self.subTest(cleared=cleared):
                case = TaggedPublisherTests()
                case.setUp()
                try:
                    case.stage(cleared)
                    plan = distribution.release_plan(case.root, case.tag)
                    path = case.root / "frozen.json"
                    for changed in (None, "notes", "policy_sha256", "tag"):
                        with self.subTest(changed=changed):
                            edited = dict(plan)
                            if changed:
                                edited[changed] += "edited"
                            path.write_text(json.dumps(edited))
                            result = subprocess.run([sys.executable, "scripts/distribution.py", "verify-release",
                                                     "--plan", str(path), "--tag", case.tag], cwd=case.root,
                                                    capture_output=True, text=True, timeout=10)
                            self.assertEqual(changed is None, result.returncode == 0, result.stdout + result.stderr)
                            if changed:
                                self.assertIn("release plan differs", result.stdout)
                finally:
                    case.doCleanups()

    def test_native_download_consumer_checks_both_checksum_modes_without_reexport(self):
        script = workflow_script("Validate downloaded pack artifacts")
        for cleared in (False, True):
            case = TaggedPublisherTests()
            case.setUp()
            try:
                case.stage(cleared)
                for defect in (None, "hash", "missing"):
                    with self.subTest(cleared=cleared, defect=defect):
                        path = case.dist / (case.basename + ".mrpack")
                        original = path.read_bytes()
                        if defect == "hash":
                            path.write_bytes(original + b"corrupt")
                        elif defect == "missing":
                            path.unlink()
                        env = {"PATH": os.environ["PATH"], "PYTHONDONTWRITEBYTECODE": "1",
                               "GITHUB_REF_TYPE": "tag", "GITHUB_REF_NAME": case.tag, "RUNNER_TEMP": str(case.root)}
                        result = subprocess.run(["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
                                                cwd=case.root, env=env, capture_output=True, text=True, timeout=30)
                        self.assertEqual(defect is None, result.returncode == 0, result.stdout + result.stderr)
                        if defect == "missing":
                            self.assertFalse(path.exists())  # No fallback/re-export.
                        else:
                            self.assertEqual(original if defect is None else original + b"corrupt", path.read_bytes())
                        path.write_bytes(original)
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

    def test_primary_zip_and_no_jar_metadata_are_validated_before_upload(self):
        self.stage(True)
        for suffix in (".mrpack", ".zip"):
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
                                    ((".mrpack", ".zip", ".sha256") if cleared else (".mrpack", ".mrpack.sha256"))]
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
