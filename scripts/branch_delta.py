#!/usr/bin/env python3
"""Compare complete active Modrinth pins at two local Git refs, without writing."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import tomllib

from release_metadata import metadata

ROOT = pathlib.Path(__file__).resolve().parents[1]
IDENTITY = re.compile(r"[A-Za-z0-9]{8}")


def git(repository: pathlib.Path, *args: str) -> bytes:
    """Use only read-only Git plumbing; never fetch or inspect working-tree pins."""
    result = subprocess.run(
        ["git", "-C", str(repository), *args], capture_output=True, check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1"},
    )
    if result.returncode:
        raise ValueError(f"Git could not read {args[0]} input")
    return result.stdout


def freeze(repository: pathlib.Path, ref: str) -> str:
    if not ref or ref.startswith("-"):
        raise ValueError("refs must be nonempty and must not start with '-'")
    return git(repository, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").decode().strip()


def read_toml(repository: pathlib.Path, commit: str, path: str) -> dict:
    return tomllib.loads(git(repository, "show", f"{commit}:{path}").decode("utf-8"))


def project_id(value: object) -> str:
    if not isinstance(value, str) or IDENTITY.fullmatch(value) is None:
        raise ValueError("Modrinth project/version identity must be eight alphanumeric characters")
    return value


def active_projects(collection: dict, minecraft: str) -> set[str]:
    if collection.get("schema") != 1 or collection.get("minecraft") != minecraft or collection.get("loader") != "fabric":
        raise ValueError("collection target/schema must agree with the Fabric pack")
    projects: set[str] = set()
    for section in ("selected", "resolved-dependency"):
        entries = collection.get(section, [])
        if not isinstance(entries, list):
            raise ValueError(f"collection {section} must be an array of tables")
        for entry in entries:
            identity = project_id(entry["project-id"])
            if identity in projects:
                raise ValueError(f"duplicate active project identity {identity}")
            projects.add(identity)
    if not projects:
        raise ValueError("collection must contain active projects")
    return projects


def pin_record(data: dict, path: str) -> tuple[str, dict]:
    """Exclude display labels, not artifact filenames, from exact pin equality."""
    modrinth = data["update"]["modrinth"]
    identity = project_id(modrinth["mod-id"])
    project_id(modrinth["version"])
    download = data["download"]
    if data.get("pin") is not True or data.get("side") != "server":
        raise ValueError(f"{path}: expected a pinned server mod")
    for field in ("filename", "name"):
        if not isinstance(data.get(field), str) or not data[field]:
            raise ValueError(f"{path}: missing {field}")
    if download["hash-format"] != "sha512" or not isinstance(download["hash"], str) or re.fullmatch(r"[0-9a-f]{128}", download["hash"]) is None:
        raise ValueError(f"{path}: expected lowercase SHA-512")
    if not isinstance(download["url"], str) or not download["url"].startswith("https://"):
        raise ValueError(f"{path}: expected HTTPS download")
    pin = {key: value for key, value in data.items() if key != "name"}
    return identity, {"name": data["name"], "metadata": path, "pin": pin}


def snapshot(repository: pathlib.Path, commit: str) -> dict:
    pack = read_toml(repository, commit, "pack.toml")
    release = metadata(pack)
    fabric = pack["versions"]["fabric"]
    if not isinstance(fabric, str) or not fabric:
        raise ValueError("pack must pin Fabric Loader")
    expected = active_projects(read_toml(repository, commit, "collection.toml"), release["minecraft"])
    pins: dict[str, dict] = {}
    for item in git(repository, "ls-tree", "-r", "-z", commit, "--", "mods").split(b"\0"):
        if not item:
            continue
        header, raw_path = item.split(b"\t", 1)
        path = raw_path.decode("utf-8")
        if not path.endswith(".pw.toml"):
            continue
        mode, kind, _ = header.split()
        if mode not in (b"100644", b"100755") or kind != b"blob":
            raise ValueError(f"{path}: metadata must be an ordinary Git blob")
        identity, record = pin_record(read_toml(repository, commit, path), path)
        if identity in pins:
            raise ValueError(f"duplicate active pin identity {identity}")
        pins[identity] = record
    if pins.keys() != expected:
        raise ValueError("active pin identities must exactly match selected projects and resolved dependencies")
    return {"commit": commit, "minecraft": release["minecraft"], "fabric": fabric, "version": release["version"], "pins": pins}


def compare(repository: pathlib.Path, before_ref: str, after_ref: str) -> dict:
    """Freeze both refs before reading; output all members, never a sample."""
    before_commit, after_commit = freeze(repository, before_ref), freeze(repository, after_ref)
    before, after = snapshot(repository, before_commit), snapshot(repository, after_commit)
    groups: dict[str, list] = {name: [] for name in ("REMOVED", "ADDED", "UPDATED", "UNCHANGED")}
    for identity in sorted(before["pins"].keys() | after["pins"].keys()):
        old, new = before["pins"].get(identity), after["pins"].get(identity)
        if old is None:
            group = "ADDED"
        elif new is None:
            group = "REMOVED"
        elif old["pin"] != new["pin"]:
            group = "UPDATED"
        else:
            group = "UNCHANGED"
        groups[group].append({"project_id": identity, "before": old, "after": new})
    return {
        "before": {key: value for key, value in before.items() if key != "pins"},
        "after": {key: value for key, value in after.items() if key != "pins"},
        "counts": {name: len(entries) for name, entries in groups.items()},
        "groups": groups,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", help="local ref or commit; no fetch is performed")
    parser.add_argument("after", help="local ref or commit")
    parser.add_argument("--repository", type=pathlib.Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = compare(args.repository, args.before, args.after)
        # Serialize completely before exposing stdout; malformed inputs never yield a prefix.
        output = json.dumps(result, indent=2, sort_keys=True)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        parser.error(f"cannot compare active pins: {exc}")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
