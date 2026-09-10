#!/usr/bin/env python3
"""Validate a Modrinth .mrpack and its server-side contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import zipfile

HEX_LENGTHS = {"sha1": 40, "sha512": 128}
VALID_ENVIRONMENTS = {"required", "optional", "unsupported"}


def safe_relative(path: str) -> bool:
    candidate = pathlib.PurePosixPath(path)
    return bool(path) and not candidate.is_absolute() and ".." not in candidate.parts and "\\" not in path


def read_index(source: pathlib.Path) -> tuple[dict, set[str]]:
    if source.suffix.lower() != ".mrpack":
        return json.loads(source.read_text(encoding="utf-8")), set()
    with zipfile.ZipFile(source) as archive:
        names = set(archive.namelist())
        return json.loads(archive.read("modrinth.index.json")), names


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
    environment = entry.get("env", {}) or {}
    server_environment = environment.get("server", "required") if isinstance(environment, dict) else "required"
    if server_environment not in VALID_ENVIRONMENTS:
        errors.append(f"{path}: invalid env.server value {server_environment!r}")
    return path, server_environment


def validate_index(index: dict, archive_names: set[str], minecraft: str, loader: str) -> tuple[list[str], list[str], list[dict]]:
    errors: list[str] = []
    warnings: list[str] = []
    required_server_files: list[dict] = []
    if index.get("formatVersion") != 1:
        errors.append("formatVersion must be 1")
    if index.get("game") != "minecraft":
        errors.append("game must be 'minecraft'")
    dependencies = index.get("dependencies", {})
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
    for name in archive_names:
        if not safe_relative(name):
            errors.append(f"archive contains unsafe path: {name!r}")
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
        index, archive_names = read_index(args.pack)
    except Exception as exc:
        print(f"ERROR: cannot read pack: {exc}")
        return 2
    if args.pack.suffix.lower() == ".mrpack" and "modrinth.index.json" not in archive_names:
        print("ERROR: .mrpack is missing root modrinth.index.json")
        return 1
    errors, warnings, required_server_files = validate_index(index, archive_names, args.minecraft, args.loader)
    if args.stage:
        validate_stage(args.stage, required_server_files, errors)
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(f"PASS: {len(required_server_files)} required server file(s); metadata and hashes are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
