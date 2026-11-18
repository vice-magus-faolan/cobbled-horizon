#!/usr/bin/env python3
"""Validate CurseForge manifest references and exact server overrides."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import stat
import tomllib
import zipfile

from collections.abc import Collection

from permission_seed import is_pack_override
import distribution

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def safe_relative(name: str) -> bool:
    """Require canonical portable ZIP paths before trusting source-derived names."""
    return bool(name) and not any(char in name for char in "\\:\x00") and all(
        part not in ("", ".", "..") for part in name.split("/")
    )


def mod_payload(source_root: pathlib.Path, relative: str, errors: list[str]) -> tuple[str, str]:
    mod = load_toml(source_root / relative)
    if mod.get("side") != "server":
        errors.append(f"validator requires server-only Modrinth pins: {relative}")
    if mod["download"]["hash-format"] != "sha512":
        errors.append(f"validator requires SHA-512 pins: {relative}")
    filename = mod["filename"]
    if not safe_relative(filename) or "/" in filename:
        raise ValueError(f"unsafe mod filename: {relative}")
    return "mods/" + filename, mod["download"]["hash"]


def hosted_files(source_root: pathlib.Path) -> dict[str, dict]:
    """Native packwiz CF metadata determines the exact reference partition.

    Distribution clearance independently verifies that these mappings are bound
    to the selected SHA-512; native updater metadata alone is not evidence.
    """
    result = {}
    for entry in load_toml(source_root / "index.toml")["files"]:
        if not entry.get("metafile"):
            continue
        mod = load_toml(source_root / entry["file"])
        hosted = mod.get("update", {}).get("curseforge")
        if hosted is None:
            continue
        if set(hosted) != {"project-id", "file-id"} or not all(type(value) is int and value > 0 for value in hosted.values()):
            raise ValueError("invalid native CurseForge mapping")
        reference = {"projectID": hosted["project-id"], "fileID": hosted["file-id"], "required": True}
        if reference in result.values():
            raise ValueError("duplicate native CurseForge reference")
        result["mods/" + mod["filename"]] = reference
    return result


def payload_hashes(source_root: pathlib.Path, errors: list[str]) -> dict[str, str]:
    """Derive the complete server payload, including deterministic notices."""
    expected_hashes: dict[str, str] = {}
    for entry in load_toml(source_root / "index.toml")["files"]:
        relative = entry["file"]
        if not safe_relative(relative):
            raise ValueError(f"unsafe source path: {relative}")
        if entry.get("metafile"):
            if pathlib.PurePosixPath(relative).parent != pathlib.PurePosixPath("mods"):
                raise ValueError(f"unexpected mod metadata path: {relative}")
            target, digest = mod_payload(source_root, relative, errors)
        else:
            if not is_pack_override(relative):
                errors.append(f"unexpected source override: {relative}")
            target = relative
            digest = hashlib.sha512((source_root / relative).read_bytes()).hexdigest()
        if target in expected_hashes:
            errors.append(f"duplicate source target: {target}")
        expected_hashes[target] = digest

    for directory in ("config", "squaremap"):
        for config in (source_root / directory).rglob("*"):
            if config.is_file() and config.relative_to(source_root).as_posix() not in expected_hashes:
                errors.append(f"source config is not indexed: {config.relative_to(source_root)}")
    for name, data in distribution.notice_members(source_root).items():
        if name in expected_hashes:
            errors.append(f"duplicate generated target: {name}")
        expected_hashes[name] = hashlib.sha512(data).hexdigest()
    return expected_hashes


def validate_payload(
    archive: zipfile.ZipFile,
    hashes: dict[str, str],
    prefix: str = "",
    extra_files: Collection[str] = (),
) -> list[str]:
    """Check exact ZIP membership, regular-file types and source-matching bytes."""
    errors: list[str] = []
    names = archive.namelist()
    if len(names) != len(set(names)):
        errors.append("archive contains duplicate paths")
    expected_hashes = {prefix + name: digest for name, digest in hashes.items()}
    directories = {prefix} if prefix else set()
    for name in expected_hashes:
        directories.update(str(parent) + "/" for parent in pathlib.PurePosixPath(name).parents if str(parent) != ".")
    for name in sorted(set(names) - set(expected_hashes) - set(extra_files) - directories):
        errors.append(f"unexpected archive entry: {name}")
    for entry in archive.infolist():
        kind = stat.S_IFMT(entry.external_attr >> 16)
        expected_kind = stat.S_IFDIR if entry.is_dir() else stat.S_IFREG
        if kind not in (0, expected_kind):
            errors.append(f"unsafe archive entry type: {entry.filename}")
    for name, expected in expected_hashes.items():
        if name not in names:
            errors.append(f"missing exported file: {name}")
        else:
            with archive.open(name) as handle:
                actual = hashlib.file_digest(handle, "sha512").hexdigest()
            if actual != expected:
                errors.append(f"exported file hash differs from source: {name}")
    return errors


def validate_archive(path: pathlib.Path, source_root: pathlib.Path = ROOT) -> list[str]:
    """Structural validation only; public entrypoints also require clearance."""
    errors: list[str] = []
    pack = load_toml(source_root / "pack.toml")
    hashes = payload_hashes(source_root, errors)
    references = hosted_files(source_root)
    hashes = {name: digest for name, digest in hashes.items() if name not in references}
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be an object")
        expected_manifest = {
            "manifestType": "minecraftModpack",
            "manifestVersion": 1,
            "name": pack["name"],
            "version": pack["version"],
            "author": pack["author"],
            "minecraft": {
                "version": pack["versions"]["minecraft"],
                "modLoaders": [{"id": "fabric-" + pack["versions"]["fabric"], "primary": True}],
            },
            "overrides": "overrides",
        }
        for key, expected in expected_manifest.items():
            if manifest.get(key) != expected:
                errors.append(f"manifest.{key} must match source: {expected!r}")
        actual = manifest.get("files")
        wanted = list(references.values())
        valid_types = isinstance(actual, list) and all(
            isinstance(item, dict) and type(item.get("projectID")) is int and type(item.get("fileID")) is int and item.get("required") is True
            for item in actual
        )
        if not valid_types or len(actual) != len(wanted) or any(item not in actual for item in wanted):
            errors.append(f"manifest.files must match source: {wanted!r}")
        errors.extend(validate_payload(archive, hashes, "overrides/", ("manifest.json", "modlist.html")))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=pathlib.Path)
    parser.add_argument("--channel", required=True, choices=sorted(distribution.CHANNELS))
    args = parser.parse_args()
    try:
        distribution.clearance(ROOT, args.channel)
        errors = validate_archive(args.pack)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"ERROR: cannot validate pack: {exc}")
        return 2
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("PASS: CurseForge-format ZIP references, overrides and notices match source; not moderation approval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
