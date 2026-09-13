#!/usr/bin/env python3
"""Validate a Modrinth .mrpack and its server-side contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import tomllib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
HEX_LENGTHS = {"sha1": 40, "sha512": 128}
VALID_ENVIRONMENTS = {"required", "optional", "unsupported"}


def safe_relative(path: str) -> bool:
    candidate = pathlib.PurePosixPath(path)
    return bool(path) and not candidate.is_absolute() and ".." not in candidate.parts and "\\" not in path and ":" not in path


def read_index(source: pathlib.Path) -> tuple[dict, dict[str, bytes]]:
    if source.suffix.lower() != ".mrpack":
        raise ValueError("validation requires a .mrpack archive, including its configuration overrides")
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("archive contains duplicate paths")
        contents = {name: archive.read(name) for name in names}
        return json.loads(contents["modrinth.index.json"]), contents


def validate_entry(entry: object, position: int, errors: list[str]) -> tuple[str | None, str | None]:
    if not isinstance(entry, dict):
        errors.append(f"files[{position}] is not an object")
        return None, None
    path = entry.get("path")
    if not isinstance(path, str) or not safe_relative(path):
        errors.append(f"files[{position}] has unsafe path {path!r}")
        return None, None
    hashes = entry.get("hashes")
    if not isinstance(hashes, dict):
        errors.append(f"{path}: hashes object is missing")
        hashes = {}
    for algorithm, length in HEX_LENGTHS.items():
        value = hashes.get(algorithm)
        if not isinstance(value, str) or not re.fullmatch(rf"[0-9a-fA-F]{{{length}}}", value):
            errors.append(f"{path}: {algorithm} must be {length} hexadecimal characters")
    if not isinstance(entry.get("fileSize"), int) or entry["fileSize"] < 0:
        errors.append(f"{path}: fileSize must be a non-negative integer")
    downloads = entry.get("downloads")
    if not isinstance(downloads, list) or not downloads or not all(isinstance(url, str) and url.startswith("https://") for url in downloads):
        errors.append(f"{path}: downloads must contain HTTPS URLs")
    environment = entry.get("env")
    if not isinstance(environment, dict):
        errors.append(f"{path}: env must explicitly require the server and exclude the client")
        return path, None
    server_environment = environment.get("server")
    if not isinstance(server_environment, str) or server_environment not in VALID_ENVIRONMENTS:
        errors.append(f"{path}: invalid env.server value {server_environment!r}")
    if server_environment != "required" or environment.get("client") != "unsupported":
        errors.append(f"{path}: expected env.server='required' and env.client='unsupported'")
    return path, server_environment


def validate_contract(index: dict, archive_files: dict[str, bytes], source_root: pathlib.Path, errors: list[str]) -> None:
    """Compare the export with the repository's pins and indexed overrides."""
    pack = tomllib.loads((source_root / "pack.toml").read_text(encoding="utf-8"))
    if index.get("versionId") != pack["version"]:
        errors.append("versionId must match pack.toml")
    expected_dependencies = {
        "minecraft": pack["versions"]["minecraft"],
        "fabric-loader": pack["versions"]["fabric"],
    }
    if index.get("dependencies") != expected_dependencies:
        errors.append(f"dependencies must match pack.toml exactly: {expected_dependencies}")

    collection = tomllib.loads((source_root / "collection.toml").read_text(encoding="utf-8"))
    project_ids = {entry["project-id"] for key in ("selected", "resolved-dependency") for entry in collection[key]}
    expected_mods = {}
    found_projects = set()
    for path in sorted((source_root / "mods").glob("*.pw.toml")):
        metadata = tomllib.loads(path.read_text(encoding="utf-8"))
        project_id = metadata["update"]["modrinth"]["mod-id"]
        target = "mods/" + metadata["filename"]
        if project_id in found_projects or target in expected_mods:
            errors.append(f"duplicate source mod: {path.name}")
        found_projects.add(project_id)
        expected_mods[target] = metadata
    if found_projects != project_ids:
        errors.append("source mod metadata must match collection.toml")

    actual_mods = {entry["path"]: entry for entry in index.get("files", []) if isinstance(entry, dict) and isinstance(entry.get("path"), str)}
    for path in sorted(expected_mods.keys() - actual_mods.keys()):
        errors.append(f"missing baseline mod: {path}")
    for path in sorted(actual_mods.keys() - expected_mods.keys()):
        errors.append(f"unexpected exported file: {path}")
    for path in sorted(expected_mods.keys() & actual_mods.keys()):
        expected = expected_mods[path]["download"]
        actual = actual_mods[path]
        hashes = actual.get("hashes")
        if not isinstance(hashes, dict) or hashes.get("sha512") != expected["hash"]:
            errors.append(f"{path}: SHA-512 must match the pinned mod")
        if actual.get("downloads") != [expected["url"]]:
            errors.append(f"{path}: download URL must match the pinned mod")

    source_index = tomllib.loads((source_root / "index.toml").read_text(encoding="utf-8"))
    expected_overrides = {}
    for entry in source_index["files"]:
        if entry.get("metafile"):
            continue
        relative = entry["file"]
        if not safe_relative(relative) or not relative.startswith(("config/", "squaremap/")):
            errors.append(f"unexpected source override: {relative}")
            continue
        expected_overrides["overrides/" + relative] = (source_root / relative).read_bytes()
    # Also catch configs omitted from the source index, so refresh cannot silently
    # drop a required configuration from the exported contract.
    for directory in ("config", "squaremap"):
        for path in (source_root / directory).rglob("*"):
            if path.is_file():
                relative = path.relative_to(source_root).as_posix()
                if "overrides/" + relative not in expected_overrides:
                    errors.append(f"source config is not indexed: {relative}")
    allowed = {"modrinth.index.json", *expected_overrides}
    allowed_directories = {"overrides/"}
    for path in expected_overrides:
        allowed_directories.update(str(parent) + "/" for parent in pathlib.PurePosixPath(path).parents if str(parent) != ".")
    for path in sorted(archive_files.keys() - allowed - allowed_directories):
        errors.append(f"unexpected archive entry: {path}")
    for path, expected in expected_overrides.items():
        if path not in archive_files:
            errors.append(f"missing configuration override: {path}")
        elif archive_files[path] != expected:
            errors.append(f"configuration override differs from source: {path}")


def validate_index(index: dict, archive_files: dict[str, bytes], minecraft: str, loader: str, source_root: pathlib.Path = ROOT) -> tuple[list[str], list[str], list[dict]]:
    errors: list[str] = []
    warnings: list[str] = []
    required_server_files: list[dict] = []
    if not isinstance(index, dict):
        return ["modrinth.index.json must be an object"], warnings, required_server_files
    if index.get("formatVersion") != 1:
        errors.append("formatVersion must be 1")
    if index.get("game") != "minecraft":
        errors.append("game must be 'minecraft'")
    dependencies = index.get("dependencies", {})
    if not isinstance(dependencies, dict):
        dependencies = {}
    if dependencies.get("minecraft") != minecraft:
        errors.append(f"Minecraft dependency must be {minecraft!r}")
    if not dependencies.get(f"{loader}-loader"):
        errors.append(f"dependencies.{loader}-loader must pin a loader version")
    files = index.get("files")
    if not isinstance(files, list) or not files:
        errors.append("files must be a non-empty array")
        files = []
    seen: set[str] = set()
    for position, entry in enumerate(files):
        path, server_environment = validate_entry(entry, position, errors)
        if path is None:
            continue
        if path in seen:
            errors.append(f"duplicate file path: {path}")
        seen.add(path)
        if server_environment == "required":
            required_server_files.append(entry)
        elif server_environment == "optional":
            warnings.append(f"optional server file requires an explicit deployment decision: {path}")
        elif path.startswith("mods/"):
            warnings.append(f"client-only mod excluded from server: {path}")
    if not required_server_files:
        errors.append("pack must contain required server mods")
    for name in archive_files:
        if not safe_relative(name):
            errors.append(f"archive contains unsafe path: {name!r}")
    if not errors:
        validate_contract(index, archive_files, source_root, errors)
    return errors, warnings, required_server_files


def validate_stage(stage: pathlib.Path, entries: list[dict], errors: list[str]) -> None:
    for entry in entries:
        target = stage / pathlib.Path(*entry["path"].split("/"))
        if not target.is_file():
            errors.append(f"staged server file is missing: {entry['path']}")
            continue
        data = target.read_bytes()
        for algorithm in HEX_LENGTHS:
            actual = hashlib.new(algorithm, data).hexdigest()
            if actual != entry["hashes"][algorithm].lower():
                errors.append(f"staged server hash mismatch: {entry['path']} ({algorithm})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=pathlib.Path)
    parser.add_argument("--minecraft", required=True)
    parser.add_argument("--loader", default="fabric")
    parser.add_argument("--stage", type=pathlib.Path)
    args = parser.parse_args()
    try:
        index, archive_files = read_index(args.pack)
        errors, warnings, required_server_files = validate_index(index, archive_files, args.minecraft, args.loader)
    except Exception as exc:
        print(f"ERROR: cannot validate pack: {exc}")
        return 2
    if args.stage and not errors:
        validate_stage(args.stage, required_server_files, errors)
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(f"PASS: {len(required_server_files)} required server file(s); pins and configuration overrides match source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
