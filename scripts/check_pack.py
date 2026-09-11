#!/usr/bin/env python3
"""Validate the Cobbled Horizon packwiz source tree."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
import tomllib
from collections.abc import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
COLLECTION_PATH = ROOT / "collection.toml"
HEX_LENGTHS = {"sha512": 128}


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def digest(path: pathlib.Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def safe_relative(path: str) -> bool:
    candidate = pathlib.PurePosixPath(path)
    return bool(path) and not candidate.is_absolute() and ".." not in candidate.parts and "\\" not in path


def collection_identity(entry: object, kind: str, errors: list[str]) -> tuple[dict, str, str] | None:
    if not isinstance(entry, dict):
        errors.append(f"collection.toml {kind} entry is not a table")
        return None
    values: dict[str, str] = {}
    for field in ("project-id", "name", "slug"):
        value = entry.get(field)
        if not isinstance(value, str) or not value:
            errors.append(f"collection.toml {kind} entry has an invalid {field}")
            return None
        values[field] = value
    return entry, values["project-id"], values["name"]


def validate_selected_entry(entry: dict, name: str, known_names: set[str], errors: list[str]) -> None:
    if entry.get("role") not in {"feature", "selected-library"}:
        errors.append(f"selected project {name} has an invalid role")
    if not isinstance(entry.get("category"), str):
        errors.append(f"selected project {name} must declare a category")
    dependants = entry.get("also-required-by", [])
    if not isinstance(dependants, list) or any(parent not in known_names for parent in dependants):
        errors.append(f"selected project {name} has an invalid also-required-by list")


def validate_resolved_entry(entry: dict, name: str, known_names: set[str], errors: list[str]) -> None:
    parents = entry.get("required-by")
    if not isinstance(parents, list) or not parents:
        errors.append(f"resolved dependency {name} must declare required-by")
    elif any(parent not in known_names for parent in parents):
        errors.append(f"resolved dependency {name} names an unknown parent")


def collect_projects(
    kind: str,
    entries: list,
    known_names: set[str],
    expected: dict[str, str],
    errors: list[str],
) -> None:
    for raw_entry in entries:
        identity = collection_identity(raw_entry, kind, errors)
        if identity is None:
            continue
        entry, project_id, name = identity
        if project_id in expected:
            errors.append(f"collection.toml repeats project ID {project_id}")
        expected[project_id] = name
        if kind == "selected":
            validate_selected_entry(entry, name, known_names, errors)
        else:
            validate_resolved_entry(entry, name, known_names, errors)


def load_collection(errors: list[str]) -> tuple[dict[str, str], int, int]:
    collection = load_toml(COLLECTION_PATH)
    if collection.get("schema") != 1:
        errors.append("collection.toml schema must be 1")
    if collection.get("minecraft") != "26.2" or collection.get("loader") != "fabric":
        errors.append("collection.toml target must be Fabric / Minecraft 26.2")
    selected = collection.get("selected", [])
    resolved = collection.get("resolved-dependency", [])
    if not isinstance(selected, list) or not isinstance(resolved, list):
        errors.append("collection.toml project sections must be arrays of tables")
        return {}, 0, 0
    all_entries = selected + resolved
    known_names: set[str] = {
        str(entry["name"])
        for entry in all_entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    expected: dict[str, str] = {}
    collect_projects("selected", selected, known_names, expected, errors)
    collect_projects("resolved-dependency", resolved, known_names, expected, errors)
    return expected, len(selected), len(resolved)


def validate_pack(errors: list[str]) -> dict:
    pack = load_toml(ROOT / "pack.toml")
    if pack.get("versions", {}).get("minecraft") != "26.2":
        errors.append("pack.toml must target Minecraft 26.2")
    if not pack.get("versions", {}).get("fabric"):
        errors.append("pack.toml must pin a Fabric Loader version")
    index_info = pack.get("index", {})
    index_path = ROOT / str(index_info.get("file", ""))
    if not index_path.is_file():
        errors.append("pack.toml index file is missing")
    elif digest(index_path, str(index_info.get("hash-format", ""))) != index_info.get("hash"):
        errors.append("pack.toml index hash is stale; run 'packwiz refresh --build'")
    return pack


def validate_metadata(errors: list[str], expected_projects: dict[str, str]) -> None:
    metadata_files = sorted((ROOT / "mods").glob("*.pw.toml"))
    found: dict[str, pathlib.Path] = {}
    for path in metadata_files:
        data = load_toml(path)
        project_id = data.get("update", {}).get("modrinth", {}).get("mod-id")
        if not isinstance(project_id, str):
            errors.append(f"{path.relative_to(ROOT)}: missing Modrinth project ID")
            continue
        if project_id in found:
            errors.append(f"duplicate Modrinth project ID {project_id}")
        found[project_id] = path
        if data.get("side") != "server":
            errors.append(f"{path.relative_to(ROOT)}: side must be 'server'")
        if data.get("pin") is not True:
            errors.append(f"{path.relative_to(ROOT)}: version must be pinned")
        download = data.get("download", {})
        if not str(download.get("url", "")).startswith("https://"):
            errors.append(f"{path.relative_to(ROOT)}: download URL must use HTTPS")
        algorithm = download.get("hash-format")
        value = download.get("hash")
        expected_length = HEX_LENGTHS.get(str(algorithm))
        if expected_length is None or not isinstance(value, str) or not re.fullmatch(rf"[0-9a-f]{{{expected_length}}}", value):
            errors.append(f"{path.relative_to(ROOT)}: expected a lowercase SHA-512 hash")
        if not data.get("update", {}).get("modrinth", {}).get("version"):
            errors.append(f"{path.relative_to(ROOT)}: missing pinned Modrinth version ID")
    missing = expected_projects.keys() - found.keys()
    extra = found.keys() - expected_projects.keys()
    for project_id in sorted(missing):
        errors.append(f"missing expected project {project_id} ({expected_projects[project_id]})")
    for project_id in sorted(extra):
        errors.append(f"unexpected project {project_id} in {found[project_id].relative_to(ROOT)}")


def validate_index(errors: list[str]) -> int:
    index = load_toml(ROOT / "index.toml")
    algorithm = str(index.get("hash-format", ""))
    entries = index.get("files", [])
    seen: set[str] = set()
    for entry in entries:
        relative = entry.get("file")
        if not isinstance(relative, str) or not safe_relative(relative):
            errors.append(f"index.toml contains unsafe path {relative!r}")
            continue
        if relative in seen:
            errors.append(f"index.toml contains duplicate path {relative}")
        seen.add(relative)
        path = ROOT / pathlib.PurePosixPath(relative)
        if not path.is_file():
            errors.append(f"index.toml references missing file {relative}")
        elif digest(path, algorithm) != entry.get("hash"):
            errors.append(f"index.toml hash is stale for {relative}")
    return len(entries)


def require_fragments(path: pathlib.Path, fragments: Iterable[str], errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for fragment in fragments:
        if fragment not in text:
            errors.append(f"{path.relative_to(ROOT)}: expected {fragment!r}")


def validate_configs(errors: list[str]) -> None:
    require_fragments(ROOT / "config/Geyser-Fabric/config.yml", ["auth-type: floodgate", "log-player-ip-addresses: false"], errors)
    require_fragments(ROOT / "config/servercore/optimizations.yml", ["reduce-sync-loads: false", "cache-ticking-chunks: false"], errors)
    require_fragments(ROOT / "config/moogs_structures.json", ['"universal_multiplier": 2.0'], errors)
    require_fragments(ROOT / "squaremap/config.yml", ["minecraft:the_nether:", "minecraft:the_end:", "enabled: false"], errors)
    graves = json.loads((ROOT / "config/universal-graves/config.json").read_text(encoding="utf-8"))
    if graves["storage"].get("experience_percent:setting_value") != 75.0:
        errors.append("Universal Graves must retain 75% of XP")
    if graves["protection"].get("self_destruction_time") != 86400:
        errors.append("Universal Graves expiry must remain 24 real-time hours")


def validate_no_secrets(errors: list[str]) -> None:
    forbidden_paths = [
        ROOT / "config/floodgate/key.pem",
        ROOT / "config/Geyser-Fabric/key.pem",
        ROOT / "config/Geyser-Fabric/saved-refresh-tokens.json",
    ]
    for path in forbidden_paths:
        if path.exists():
            errors.append(f"runtime secret must not exist in the source tree: {path.relative_to(ROOT)}")
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
        if private_key_marker in text:
            errors.append(f"private key material found in {path.relative_to(ROOT)}")


def validate() -> tuple[list[str], int, int, int]:
    errors: list[str] = []
    expected_projects, selected_count, dependency_count = load_collection(errors)
    validate_pack(errors)
    validate_metadata(errors, expected_projects)
    indexed = validate_index(errors)
    validate_configs(errors)
    validate_no_secrets(errors)
    return errors, indexed, selected_count, dependency_count


def main() -> int:
    errors, indexed, selected_count, dependency_count = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        f"PASS: {selected_count} selected + {dependency_count} resolved dependencies; "
        f"{indexed} indexed pack files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
