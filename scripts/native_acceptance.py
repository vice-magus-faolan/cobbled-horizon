#!/usr/bin/env python3
"""Hosted native acceptance of the same validated server ZIP; never a deployment tool."""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import subprocess
import time
import tomllib
import urllib.request
import zipfile

import permission_seed
import server_pack

ROOT = Path(__file__).resolve().parents[1]
JAVA_IMAGE = "eclipse-temurin:25-jdk@sha256:b8705e936964c228dfce359e63dbf08f6c69cb380ed1d576b1f6b1064f15567d"
INSTALLER_URL = "https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.1.2/fabric-installer-1.1.2.jar"
INSTALLER_SHA1 = "74685b5a0178c4dabd4be741a276d35c59b5ec96"
READY = r'\[Server thread/INFO\]: Done \([0-9.]+s\)! For help, type "help"'
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
LABEL = "com.docker.compose.project"
HELPER = "00000000-0000-4000-8000-000000000001"
OWNER = "00000000-0000-4000-8000-000000000002"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def docker(*args: str, timeout: float = 30) -> str:
    result = subprocess.run(["docker", *args], check=True, capture_output=True,
                            text=True, timeout=timeout)
    return result.stdout.strip()


def cleanup(project: str) -> None:
    """Remove only our containers; check every resource query's actual exit."""
    ids = docker("container", "ls", "--all", "--quiet", "--filter", f"label={LABEL}={project}").split()
    if ids:
        docker("container", "remove", "--force", *ids)
    for resource in ("container", "volume", "network"):
        arguments = [resource, "ls", "--quiet", "--filter", f"label={LABEL}={project}"]
        if resource == "container":
            arguments.append("--all")
        require(not docker(*arguments), f"owned {resource} resources remain")


def extract_server(archive: Path, destination: Path, source_root: Path = ROOT) -> None:
    """Existing exact membership/hash/type validator runs before any extraction."""
    errors = server_pack.validate_archive(archive, source_root)
    require(not errors, "invalid server archive: " + "; ".join(errors))
    destination.mkdir()  # Must be a fresh owned directory, never an existing server.
    with zipfile.ZipFile(archive) as payload:
        payload.extractall(destination)


def check_worldgen(server: Path, console: str, source_root: Path = ROOT) -> None:
    require(not list((server / "config").rglob("*had-error*")), "native config recovery file appeared")
    require(not re.search(r"(?:missing.{0,40}(?:structure|set)|(?:structure|set).{0,40}missing)",
                          console, re.IGNORECASE), "native missing-set recovery reported")
    fixture = json.loads((source_root / "tests/fixtures/worldgen-26.3.json").read_text())
    for name, directory in (("mss", "mss"), ("hopo", "hopobettermineshaft")):
        for field, filename in (("placement", "structure_placement_config.json5"),
                                ("toggles", "structure_toggle_config.json5")):
            actual = json.loads((server / "config/cristellib" / directory / filename).read_text())
            require(actual == fixture[name][field], f"native {name} {field} policy drift")
    moog = json.loads((server / "config/moogs_structures.json").read_text())
    expected = json.loads((source_root / "config/moogs_structures.json").read_text())
    expected.pop("_comment", None)
    spacing = expected.pop("spacing")
    expected["frequency"] = {
        "universal_multiplier": 1.0,
        "per_mod": {key: round(1 / value ** 2, 6) for key, value in spacing["per_mod"].items()},
        "per_structure": {},
    }
    moog.pop("_comment", None)
    require(moog == expected, "Moog namespace migration/policy drift")


def node_identity(node: dict) -> str:
    return json.dumps({key: value for key, value in node.items() if key != "value"}, sort_keys=True)


def domain_snapshot(export: dict) -> dict:
    """Ignore only export metadata and node order, never stored domain values."""
    require(all(isinstance(export.get(key), dict) for key in ("groups", "users", "tracks")),
            "native export missing domain sections")
    result = {key: copy.deepcopy(export[key]) for key in ("groups", "users", "tracks")}
    for section in ("groups", "users"):
        for holder in result[section].values():
            nodes = holder["nodes"]
            identities = [node_identity(node) for node in nodes]
            require(len(set(identities)) == len(nodes), "duplicate native node identity")
            holder["nodes"] = sorted(nodes, key=node_identity)
    return result


def merged_snapshot(before: dict, seed: dict) -> dict:
    """Expected native merge: matching nodes change; everything else survives."""
    expected = copy.deepcopy(before)
    for name, group in seed["groups"].items():
        holder = expected["groups"].setdefault(name, {"nodes": []})
        nodes = {node_identity(node): node for node in holder["nodes"]}
        nodes.update({node_identity(node): node for node in group["nodes"]})
        holder["nodes"] = list(nodes.values())
    return domain_snapshot(expected)


class Console:
    """Synchronize one native process's real output, with bounded deadlines."""

    def __init__(self, process: subprocess.Popen, log: Path, deadline: float):
        self.process = process
        self.deadline = deadline
        self.output = ""
        self.log = log.open("wb")
        self.selector = selectors.DefaultSelector()
        self.selector.register(process.stdout, selectors.EVENT_READ)

    def wait(self, pattern: str | None, start: int = 0, seconds: float = 45) -> str:
        """Wait for a pattern, or actual pipe EOF when pattern is None."""
        deadline = min(self.deadline, time.monotonic() + seconds)
        expected = pattern if pattern is not None else "stdout EOF"
        while time.monotonic() < deadline:
            match = re.search(pattern, self.output[start:]) if pattern is not None else None
            if match:
                return self.output[start:start + match.end()]
            events = self.selector.select(min(1, max(0, deadline - time.monotonic())))
            if events:
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    if pattern is None:
                        return self.output[start:]
                    raise RuntimeError("native process ended before required output: " + expected)
                self.log.write(chunk)
                self.log.flush()
                self.output += ANSI.sub("", chunk.decode("utf-8", errors="replace"))
                require(len(self.output) <= 16 * 1024 * 1024, "native console exceeds evidence bound")
            elif self.process.poll() is not None:
                raise RuntimeError("native process exited before required output: " + expected)
        raise TimeoutError("native deadline waiting for: " + expected)

    def command(self, command: str, pattern: str) -> str:
        start = len(self.output)
        self.process.stdin.write((command + "\n").encode())
        self.process.stdin.flush()
        return self.wait(pattern, start)

    def export(self, server: Path, name: str) -> dict:
        self.command("lp export " + name, r"Successfully exported to [^\r\n]*" + re.escape(name) + r"\.json\.gz")
        return domain_snapshot(json.loads(gzip.decompress(
            (server / "mods/luckperms" / (name + ".json.gz")).read_bytes())))

    def import_file(self, name: str) -> None:
        self.command("lp import " + name, r"\[LP\].*COMPLETED")

    def permission(self, target: str, node: str, expected: bool) -> None:
        output = self.command(f"lp {target} permission check {node}", r"Result: (?:true|false|undefined)")
        result = re.findall(r"Result: (true|false|undefined)", output)
        require(result == [str(expected).lower()], f"wrong effective permission: {target} {node}")

    def stop(self, name: str) -> None:
        start = len(self.output)
        announcement = self.command("stop", r"\[Server thread/INFO\]: Saving worlds")
        # Pinned 26.3 logs save starts, not the legacy storage-completion text.
        # Only shutdown-slice dimensions plus EOF AND zero exits prove completion.
        # Drain to EOF so attach cannot block on a full output pipe during save.
        shutdown = self.wait(None, start + len(announcement), seconds=60)
        check_saved_dimensions(shutdown)
        code = self.process.wait(timeout=max(1, min(10, self.deadline - time.monotonic())))
        require(code == 0, f"native attach exit {code}")
        state = json.loads(docker("inspect", "--format", "{{json .State}}", name))
        require(state["Status"] == "exited" and state["ExitCode"] == 0 and not state["OOMKilled"],
                "native server did not exit cleanly")

    def close(self) -> None:
        self.selector.close()
        self.log.close()
        for pipe in (self.process.stdin, self.process.stdout):
            pipe.close()


def check_saved_dimensions(output: str) -> None:
    """Require pinned save-start lines; stop also requires EOF and clean exits."""
    for dimension in ("overworld", "the_nether", "the_end"):
        pattern = (r"\[Server thread/INFO\]: Saving chunks for level "
                   rf"\x27ServerLevel\[world\]\x27/minecraft:{dimension}\r?$")
        require(re.search(pattern, output, re.MULTILINE) is not None,
                f"native shutdown save missing for {dimension}")


def create_container(project: str, phase: str, server: Path, command: list[str], offline: bool) -> str:
    name = project + "-" + phase
    docker("create", "--name", name, "--label", f"{LABEL}={project}",
           "--user", f"{os.getuid()}:{os.getgid()}", "--read-only", "--cap-drop=ALL",
           "--security-opt=no-new-privileges", "--memory=6g", "--memory-swap=6g",
           "--cpus=2", "--pids-limit=512", "--network", "none" if offline else "bridge",
           "--interactive", "--workdir=/work", "--env=HOME=/work/home",
           "--env=TMPDIR=/work/tmp", "--mount", f"type=bind,src={server},dst=/work",
           "--tmpfs=/tmp:rw,exec,nosuid,size=128m,mode=1777", JAVA_IMAGE, *command)
    return name


def boot(project: str, phase: str, server: Path, work: Path, deadline: float, offline: bool) -> tuple[str, Console]:
    name = create_container(project, phase, server,
                            ["java", "-Xms512M", "-Xmx4G", "-Djava.io.tmpdir=/work/tmp",
                             "-Djna.tmpdir=/work/tmp", "-jar", "fabric-server-launch.jar", "nogui"], offline)
    process = subprocess.Popen(["docker", "start", "--attach", "--interactive", name],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    console = Console(process, work / (phase + ".log"), deadline)
    return name, console


def provision(server: Path, project: str, work: Path, deadline: float) -> None:
    with urllib.request.urlopen(INSTALLER_URL, timeout=30) as response:
        installer = response.read(4 * 1024 * 1024)
    require(hashlib.sha1(installer).hexdigest() == INSTALLER_SHA1, "Fabric installer checksum mismatch")
    (server / "installer.jar").write_bytes(installer)
    pins = tomllib.loads((ROOT / "pack.toml").read_text())["versions"]
    for directory in ("home", "tmp"):
        (server / directory).mkdir()
    name = create_container(project, "installer", server,
                            ["java", "-Djava.io.tmpdir=/work/tmp", "-jar", "installer.jar", "server",
                             "-mcversion", pins["minecraft"], "-loader", pins["fabric"], "-downloadMinecraft"], False)
    with (work / "installer.log").open("wb") as log:
        subprocess.run(["docker", "start", "--attach", name], stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=max(1, min(180, deadline - time.monotonic())))
    state = json.loads(docker("inspect", "--format", "{{json .State}}", name))
    require(state["Status"] == "exited" and state["ExitCode"] == 0 and not state["OOMKilled"],
            "Fabric installer did not exit cleanly")
    require((server / "fabric-server-launch.jar").is_file(), "Fabric launcher missing")
    cleanup(project)  # Failure cleanup belongs to main, preserving the original error.
    (server / "eula.txt").write_text("eula=true\n")
    (server / "server.properties").write_text(
        "server-ip=127.0.0.1\nonline-mode=true\nenforce-secure-profile=false\n"
        "level-seed=37569\nview-distance=2\nsimulation-distance=2\nmax-players=2\n"
        "enable-rcon=false\nenable-query=false\nspawn-protection=16\npvp=true\n")


def prepare_permissions(console: Console) -> None:
    console.command("lp creategroup ci-sentinel", r"was successfully created")
    commands = (
        "lp group ci-sentinel permission set ci.sentinel true",
        "lp group default permission set ci.custom true",
        "lp group default permission set ci.context true world=ci-context",
        "lp group default permission set sswaystones.create.global true",
        "lp group owner parent add ci-sentinel",
        f"lp user {HELPER} parent add helper",
        f"lp user {HELPER} parent add ci-sentinel",
        f"lp user {HELPER} permission set ci.user true",
        f"lp user {HELPER} permission set ci.usercontext false world=ci-context",
        f"lp user {OWNER} parent add owner",
    )
    for command in commands:
        console.command(command, r"(?:Set .+ to (?:true|false)|now inherits permissions from)")


def check_effective(console: Console) -> None:
    cases = (
        ("group default", "sswaystones.create.place", True),
        ("group default", "sswaystones.create.global", False),
        ("group default", "sswaystones.create.team", False),
        ("group helper", "group.default", True),
        ("group owner", "group.default", True),
        ("group helper", "sswaystones.command", False),
        ("group owner", "sswaystones.create.server", True),
        (f"user {HELPER}", "sswaystones.create.place", True),
        (f"user {HELPER}", "sswaystones.command", False),
        (f"user {HELPER}", "ci.sentinel", True),
        (f"user {OWNER}", "sswaystones.create.server", True),
    )
    for target, node, value in cases:
        console.permission(target, node, value)
    # Check inherited account resolution, not just the nodes on the owner group.
    for suffix in ("create.global", "create.server", "command", "manager", "manager.bypass_limit", "showall"):
        node = "sswaystones." + suffix
        console.permission(f"user {OWNER}", node, True)
        console.permission("group default", node, False)
        console.permission("group helper", node, False)
        console.permission(f"user {HELPER}", node, False)
    console.permission("group owner", "sswaystones.create.team", False)
    console.permission(f"user {OWNER}", "sswaystones.create.team", False)
    console.permission(f"user {HELPER}", "sswaystones.create.team", False)
    console.permission(f"user {OWNER}", "sswaystones.create.place", True)


def clean_bootstrap(console: Console, server: Path, seed: dict) -> None:
    before = console.export(server, "ci-clean-before")
    require(set(before["groups"]) == {"default"} and not before["users"] and not before["tracks"],
            "first-install fixture is not default-only")
    console.import_file("luckperms-groups.json.gz")
    require(console.export(server, "ci-clean-after") == merged_snapshot(before, seed),
            "fresh native import did not create the complete baseline")
    for target in ("group helper", "group owner"):
        console.permission(target, "group.default", True)
    console.permission("group default", "sswaystones.create.place", True)


def first_boot(console: Console, server: Path) -> dict:
    console.wait(READY, seconds=240)
    check_worldgen(server, console.output)
    shutil.copyfile(server / permission_seed.SEED_IMPORT, server / "mods/luckperms/luckperms-groups.json.gz")
    seed = json.loads(permission_seed.policy_bytes(ROOT))
    clean_bootstrap(console, server, seed)
    prepare_permissions(console)
    before = console.export(server, "ci-before")
    require(before["groups"]["default"]["nodes"], "pre-import state is empty")
    console.permission("group default", "sswaystones.create.global", True)
    expected = merged_snapshot(before, seed)
    console.import_file("luckperms-groups.json.gz")
    require(console.export(server, "ci-first") == expected, "native import/conflict/preservation mismatch")
    check_effective(console)
    console.import_file("luckperms-groups.json.gz")
    require(console.export(server, "ci-repeat") == expected, "repeat changed native domain state")
    # A deliberately changed node distinguishes a real roundtrip from a no-op.
    console.command("lp group default permission set ci.custom false", r"Set .+ to false")
    require(console.export(server, "ci-mutated") != expected, "roundtrip negative control did not mutate")
    console.permission("group default", "ci.custom", False)
    console.import_file("ci-first.json.gz")
    require(console.export(server, "ci-roundtrip") == expected, "native roundtrip did not restore complete state")
    console.permission("group default", "ci.custom", True)
    check_effective(console)
    # Persist a change to a seed node: a startup reapplication would erase it.
    console.command("lp group default permission set sswaystones.create.place false", r"Set .+ to false")
    saved = console.export(server, "ci-pre-stop")
    require(saved != expected, "restart negative control did not mutate")
    return saved


def native_run(archive: Path, work: Path, project: str, summary: dict) -> None:
    deadline = time.monotonic() + 720
    server = work / "server"
    extract_server(archive, server)
    with archive.open("rb") as stream:
        summary["archive_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
    provision(server, project, work, deadline)
    name, console = boot(project, "first-boot", server, work, deadline, False)
    try:
        saved = first_boot(console, server)
        console.stop(name)
        check_worldgen(server, console.output)
        summary["first_install_and_import_repeat_conflict_roundtrip_preservation"] = "passed"
    finally:
        console.close()
    # On failure main records the product error before its guaranteed cleanup.
    cleanup(project)
    require((server / "world/level.dat").is_file(), "world was not saved")
    name, console = boot(project, "offline-second-boot", server, work, deadline, True)
    try:
        console.wait(READY, seconds=180)
        check_worldgen(server, console.output)
        require(console.export(server, "ci-restarted") == saved, "restart changed persisted permissions/startup reapplied seed")
        console.permission("group default", "sswaystones.create.place", False)
        console.import_file("luckperms-groups.json.gz")
        require(console.export(server, "ci-reconciled") == merged_snapshot(saved, json.loads(permission_seed.policy_bytes(ROOT))),
                "post-restart reconciliation failed")
        check_effective(console)
        console.stop(name)
        check_worldgen(server, console.output)
        summary["offline_second_boot_save_exit_no_startup_reapplication"] = "passed"
    finally:
        console.close()


def selected_logs(work: Path, evidence: Path) -> None:
    # Deliberate allowlist: never publish generated configs, exports, keys or worlds.
    for name in ("installer.log", "first-boot.log", "offline-second-boot.log"):
        path = work / name
        if path.is_file():
            with path.open("rb") as reader:
                reader.seek(max(0, path.stat().st_size - 512 * 1024))
                (evidence / name).write_bytes(reader.read(512 * 1024))


def cancelled(signum: int, frame: object) -> None:
    raise InterruptedError("job cancelled")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "cleanup"))
    parser.add_argument("--project", required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    require(bool(re.fullmatch(r"ch-native-[0-9]+-[0-9]+", args.project)), "invalid owned project label")
    if args.command == "cleanup":
        cleanup(args.project)
        return 0
    require(all((args.archive, args.work, args.evidence)), "run requires archive, work and evidence")
    args.work.mkdir()  # Refuse reuse, including an interrupted previous fixture.
    args.evidence.mkdir()
    signal.signal(signal.SIGTERM, cancelled)
    summary = {"passed": False, "java_image": JAVA_IMAGE, "cleanup": "pending"}
    result = 0
    try:
        native_run(args.archive, args.work, args.project, summary)
        summary["passed"] = True
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        summary["error"] = str(exc)
        if isinstance(exc, subprocess.CalledProcessError):
            summary["stderr"] = (exc.stderr or "")[-4096:]
        result = 1
    finally:
        try:
            cleanup(args.project)
            summary["cleanup"] = "all owned container/volume/network queries empty"
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            summary["cleanup"] = str(exc)
            summary["passed"] = False
            result = result or 1
        selected_logs(args.work, args.evidence)
        (args.evidence / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
