"""Controller unit regressions; synthetic streams are NOT native runtime evidence."""

from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import test_server_folder
from pack_fixtures import ROOT, load_script
import permission_seed

native = load_script("native_acceptance")
READY_LINE = "[12:00:00] [Server thread/INFO]: Done (1.2s)! For help, type \"help\"\n"
SAVED = "\n".join(
    f"[09:23:07] [Server thread/INFO]: Saving chunks for level \x27ServerLevel[world]\x27/minecraft:{name}"
    for name in ("overworld", "the_nether", "the_end")
) + "\n"
STOPPED = "[09:23:07] [Server thread/INFO]: Saving worlds\n" + SAVED
CLEAN_EXIT = {"Status": "exited", "ExitCode": 0, "OOMKilled": False}


class NativeAcceptanceTests(unittest.TestCase):
    def console(self, root: Path, output: str, deadline: float | None = None, *, eof: bool = True):
        reader, writer = os.pipe()
        os.write(writer, output.encode())
        if eof:
            os.close(writer)
        else:
            self.addCleanup(os.close, writer)
        process = Mock()
        process.stdout = os.fdopen(reader, "rb")
        process.stdin = io.BytesIO()
        process.wait.return_value = 0
        process.poll.return_value = None
        console = native.Console(process, root / "console.log", deadline or time.monotonic() + 5)
        self.addCleanup(console.close)
        return console

    def test_only_minecraft_server_readiness_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            console = self.console(root, "[Geyser-Spigot]: Done (1.2s)!\n" + READY_LINE)
            self.assertIn(READY_LINE.strip(), console.wait(native.READY))
        with tempfile.TemporaryDirectory() as directory:
            console = self.console(Path(directory), "[Geyser-Fabric]: Done (1.2s)!\n")
            with self.assertRaisesRegex(RuntimeError, "ended before"):
                console.wait(native.READY)

    def test_dead_process_and_expired_budget_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            console = self.console(Path(directory), "", time.monotonic() - 1)
            with self.assertRaises(TimeoutError):
                console.wait(native.READY)
        with tempfile.TemporaryDirectory() as directory:
            console = self.console(Path(directory), "dependency failed\n")
            with self.assertRaises(RuntimeError):
                console.wait(native.READY)

    def test_save_requires_each_shutdown_dimension_and_zero_exit(self):
        native.check_saved_dimensions(SAVED)
        for output in ("", "[Server thread/INFO]: Saving worlds\n",
                       SAVED + "[Server thread/INFO]: Saving worlds\n",
                       *(STOPPED.replace(line, "") for line in SAVED.splitlines(keepends=True)),
                       STOPPED.replace("[Server thread/INFO]: Saving chunks", "[Worker-Main/INFO]: Saving chunks")):
            with self.subTest(output=output), tempfile.TemporaryDirectory() as directory:
                console = self.console(Path(directory), output)
                with patch.object(native, "docker") as docker:
                    with self.assertRaises((ValueError, RuntimeError)):
                        console.stop("owned")
                console.process.wait.assert_not_called()
                docker.assert_not_called()
        with tempfile.TemporaryDirectory() as directory:
            console = self.console(Path(directory), STOPPED)
            console.process.wait.return_value = 1
            with self.assertRaisesRegex(ValueError, "attach exit 1"), patch.object(native, "docker") as docker:
                console.stop("owned")
            docker.assert_not_called()
        for state in (CLEAN_EXIT, {**CLEAN_EXIT, "Status": "running"},
                      {**CLEAN_EXIT, "ExitCode": 1}, {**CLEAN_EXIT, "OOMKilled": True}):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as directory:
                console = self.console(Path(directory), STOPPED)
                with patch.object(native, "docker", return_value=json.dumps(state)) as docker:
                    if state != CLEAN_EXIT:
                        with self.assertRaises(ValueError):
                            console.stop("owned")
                    else:
                        console.stop("owned")
                        self.assertEqual(b"stop\n", console.process.stdin.getvalue())
                        self.assertEqual(STOPPED, console.output)
                        self.assertEqual(STOPPED.encode(), (Path(directory) / "console.log").read_bytes())
                    console.process.wait.assert_called_once()
                    docker.assert_called_once_with("inspect", "--format", "{{json .State}}", "owned")

    def test_save_requires_bounded_pipe_eof_not_just_process_exit(self):
        for poll, error in ((None, TimeoutError), (0, RuntimeError)):
            with self.subTest(poll=poll), tempfile.TemporaryDirectory() as directory:
                console = self.console(Path(directory), STOPPED, time.monotonic() + 0.05, eof=False)
                console.process.poll.return_value = poll
                with patch.object(native, "docker") as docker:
                    with self.assertRaises(error):
                        console.stop("owned")
                self.assertEqual(STOPPED, console.output)
                console.process.wait.assert_not_called()
                docker.assert_not_called()

    def test_save_propagates_drain_failure_instead_of_treating_it_as_eof(self):
        with tempfile.TemporaryDirectory() as directory:
            console = self.console(Path(directory), STOPPED)
            with patch.object(console, "wait", side_effect=["Saving worlds", RuntimeError("drain failed")]), \
                 patch.object(native, "docker") as docker:
                with self.assertRaisesRegex(RuntimeError, "drain failed"):
                    console.stop("owned")
            console.process.wait.assert_not_called()
            docker.assert_not_called()

    def test_default_only_import_must_really_create_both_groups(self):
        before = {"groups": {"default": {"nodes": []}}, "users": {}, "tracks": {}}
        seed = json.loads(permission_seed.policy_bytes(ROOT))
        expected = native.merged_snapshot(before, seed)
        for after in (expected, before):
            console = Mock()
            console.export.side_effect = [before, after]
            if after == expected:
                native.clean_bootstrap(console, Path("unused"), seed)
                console.import_file.assert_called_once_with("luckperms-groups.json.gz")
            else:
                with self.assertRaisesRegex(ValueError, "did not create"):
                    native.clean_bootstrap(console, Path("unused"), seed)
        console = Mock()
        console.export.return_value = expected
        with self.assertRaisesRegex(ValueError, "not default-only"):
            native.clean_bootstrap(console, Path("unused"), seed)
        console.import_file.assert_not_called()

    def test_merge_oracle_preserves_complete_unrelated_context_and_user_state(self):
        seed = json.loads(permission_seed.policy_bytes(ROOT))
        node = {"type": "permission", "key": "sswaystones.create.global", "value": True}
        contextual = {**node, "context": {"world": ["ci-context"]}}
        before = {"groups": {"default": {"nodes": [node, contextual]},
                             "ci-sentinel": {"nodes": [{"type": "permission", "key": "ci.custom", "value": True}]}},
                  "users": {native.HELPER: {"primaryGroup": "helper", "nodes": [contextual]}},
                  "tracks": {"ci-track": {"groups": ["default", "ci-sentinel"]}}}
        frozen = copy.deepcopy(before)
        expected = native.merged_snapshot(before, seed)
        self.assertEqual(frozen, before)
        self.assertEqual(before["users"], expected["users"])
        self.assertEqual(before["tracks"], expected["tracks"])
        self.assertEqual(before["groups"]["ci-sentinel"], expected["groups"]["ci-sentinel"])
        self.assertIn({**node, "value": False}, expected["groups"]["default"]["nodes"])
        self.assertIn(contextual, expected["groups"]["default"]["nodes"])
        self.assertNotEqual(native.domain_snapshot(before), expected)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            native.domain_snapshot({**before, "groups": {"default": {"nodes": [node, {**node, "value": False}]}}})
        with self.assertRaisesRegex(ValueError, "missing domain"):
            native.domain_snapshot({"groups": {}})

    def test_slashloot_native_config_load_and_drift(self):
        loaded = "slashloot 0.6.0\nSlashLoot loaded - server-side per-player loot\n"
        policy = {
            "enabled": True, "dimensionBlocklist": [], "lootTableBlocklist": [],
            "handleUnknownContainers": False, "instancePots": True,
            "delegateContainerAnimation": True, "playOpenCloseSounds": True,
            "cleanupOnBreak": True, "pruneIntervalTicks": 6000,
            "pruneBatchSize": 256, "debugLogging": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            server = Path(directory)
            (server / "config").mkdir()
            target = server / "config/slashloot.json"
            target.write_text(json.dumps(policy, sort_keys=True))
            native.check_slashloot(server, loaded)
            for output in (READY_LINE, loaded.replace("0.6.0", "0.5.0"),
                           loaded + "Failed to load slashloot.json, using defaults"):
                with self.subTest(output=output), self.assertRaises(ValueError):
                    native.check_slashloot(server, output)
            for key, value in (("enabled", False), ("cleanupOnBreak", False),
                               ("pruneIntervalTicks", 0), ("instancePots", False),
                               ("handleUnknownContainers", True)):
                target.write_text(json.dumps({**policy, key: value}))
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, "policy drift"):
                    native.check_slashloot(server, loaded)
            target.write_text("invalid JSON")
            with self.assertRaises(ValueError):
                native.check_slashloot(server, loaded)

    def test_worldgen_migration_accepts_formatting_but_rejects_policy_drift_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            server = Path(directory)
            shutil.copytree(ROOT / "config", server / "config")
            moog = server / "config/moogs_structures.json"
            migrated = json.loads(moog.read_text())
            del migrated["spacing"]
            migrated["_comment"] = "native generated comment"
            migrated["frequency"] = {"universal_multiplier": 1, "per_mod": {"mos": 0.111111, "mss": 0.25}, "per_structure": {}}
            moog.write_text(json.dumps(migrated, sort_keys=True))
            native.check_worldgen(server, READY_LINE)
            with self.assertRaisesRegex(ValueError, "missing-set"):
                native.check_worldgen(server, "Missing structure set mss:trees")
            migrated["frequency"]["per_mod"]["mss"] = 2
            moog.write_text(json.dumps(migrated))
            with self.assertRaisesRegex(ValueError, "Moog"):
                native.check_worldgen(server, READY_LINE)
            migrated["frequency"]["per_mod"]["mss"] = 0.25
            moog.write_text(json.dumps(migrated))
            target = server / "config/cristellib/mss/structure_toggle_config.json5"
            original = target.read_bytes()
            data = json.loads(original)
            data["trees"]["tree_8"] = False
            target.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "mss toggles"):
                native.check_worldgen(server, READY_LINE)
            target.write_bytes(original)
            target.with_suffix(".json5-had-error").touch()
            with self.assertRaisesRegex(ValueError, "recovery file"):
                native.check_worldgen(server, READY_LINE)

    def test_native_prepares_the_complete_mrpack_folder_before_provisioning(self):
        fixture = test_server_folder.ServerFolderTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        work = fixture.root / "native-work"
        work.mkdir()
        summary = {}
        with patch.object(native, "ROOT", fixture.root), \
                patch.object(native.server_folder.urllib.request, "urlopen", side_effect=[io.BytesIO(fixture.fixture.mod), io.BytesIO(fixture.fixture.override_bytes)]), \
                patch.object(native, "provision", side_effect=RuntimeError("stop before runtime")) as provision:
            with self.assertRaisesRegex(RuntimeError, "stop before runtime"):
                native.native_run(fixture.source, work, "ch-native-1-1", summary)
        self.assertEqual(work / "server", provision.call_args.args[0])
        self.assertEqual([], native.server_folder.validate_directory(work / "server", fixture.root))
        self.assertEqual("validated mrpack to complete server folder", summary["preparation"])
        fixture.write_mrpack({**fixture.contents, "../escape": b"bad"})
        other = fixture.root / "invalid-work"
        other.mkdir()
        with patch.object(native, "ROOT", fixture.root), patch.object(native, "provision") as provision, \
                patch.object(native.server_folder.urllib.request, "urlopen") as download:
            with self.assertRaises(ValueError):
                native.native_run(fixture.source, other, "ch-native-1-1", {})
        provision.assert_not_called()
        download.assert_not_called()
        self.assertFalse((other / "server").exists())
        self.assertFalse((fixture.root / "escape").exists())

    def test_cleanup_queries_failure_and_leftovers_never_prove_absence(self):
        with patch.object(native, "docker", side_effect=["owned", "", "", "", ""]) as docker:
            native.cleanup("ch-native-1-1")
        self.assertIn(("container", "remove", "--force", "owned"), [call.args for call in docker.call_args_list])
        for responses in (["", "leftover"], ["", "", "leftover"],
                          ["", "", "", "leftover"], [subprocess.CalledProcessError(1, "docker")]):
            with self.subTest(responses=responses), patch.object(native, "docker", side_effect=responses):
                with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                    native.cleanup("ch-native-1-1")

    def test_installer_checksum_is_enforced_before_runtime_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            response = Mock()
            response.__enter__ = Mock(return_value=io.BytesIO(b"wrong installer bytes"))
            response.__exit__ = Mock(return_value=False)
            with patch.object(native.urllib.request, "urlopen", return_value=response), \
                 patch.object(native, "create_container") as create:
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    native.provision(root, "ch-native-1-1", root, time.monotonic() + 10)
            create.assert_not_called()
            self.assertFalse((root / "installer.jar").exists())

    def test_product_failure_and_cleanup_failure_are_reported_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            arguments = ["native_acceptance.py", "run", "--project", "ch-native-1-1",
                         "--archive", str(root / "unused.zip"), "--work", str(root / "work"),
                         "--evidence", str(root / "evidence")]
            with patch("sys.argv", arguments), patch.object(native.signal, "signal"), \
                 patch.object(native, "native_run", side_effect=ValueError("native product failed")), \
                 patch.object(native, "cleanup", side_effect=ValueError("cleanup failed")) as cleanup, \
                 patch("sys.stdout", io.StringIO()):
                self.assertEqual(1, native.main())
            summary = json.loads((root / "evidence/summary.json").read_text())
            self.assertFalse(summary["passed"])
            self.assertEqual("native product failed", summary["error"])
            self.assertEqual("cleanup failed", summary["cleanup"])
            cleanup.assert_called_once_with("ch-native-1-1")

    def test_evidence_allowlist_excludes_runtime_and_bounds_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory) / "work"
            evidence = Path(directory) / "evidence"
            work.mkdir()
            evidence.mkdir()
            (work / "private.json.gz").write_bytes(b"private canary")
            (work / "first-boot.log").write_bytes(b"x" * (600 * 1024))
            native.selected_logs(work, evidence)
            self.assertEqual(["first-boot.log"], [path.name for path in evidence.iterdir()])
            self.assertEqual(512 * 1024, (evidence / "first-boot.log").stat().st_size)


if __name__ == "__main__":
    unittest.main()
