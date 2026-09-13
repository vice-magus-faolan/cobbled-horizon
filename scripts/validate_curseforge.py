#!/usr/bin/env python3
"""Validate the server CurseForge ZIP against this Modrinth-pinned source tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import tomllib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def validate_archive(path: pathlib.Path, source_root: pathlib.Path = ROOT) -> list[str]:
    errors: list[str] = []
    pack = load_toml(source_root / "pack.toml")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            errors.append("archive contains duplicate paths")
        manifest = json.loads(archive.read("manifest.json"))
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
            # Current pins are all Modrinth downloads, bundled as overrides.
            "files": [],
        }
        for key, expected in expected_manifest.items():
            if manifest.get(key) != expected:
                errors.append(f"manifest.{key} must match source: {expected!r}")

        expected_hashes = {}
        for entry in load_toml(source_root / "index.toml")["files"]:
            relative = entry["file"]
            if entry.get("metafile"):
                mod = load_toml(source_root / relative)
                if mod.get("side") != "server" or "curseforge" in mod.get("update", {}):
                    errors.append(f"validator requires server-only Modrinth pins: {relative}")
                if mod["download"]["hash-format"] != "sha512":
                    errors.append(f"validator requires SHA-512 pins: {relative}")
                target = "overrides/" + str(pathlib.PurePosixPath(relative).parent / mod["filename"])
                digest = mod["download"]["hash"]
            else:
                if not relative.startswith(("config/", "squaremap/")):
                    errors.append(f"unexpected source override: {relative}")
                target = "overrides/" + relative
                digest = hashlib.sha512((source_root / relative).read_bytes()).hexdigest()
            if target in expected_hashes:
                errors.append(f"duplicate source target: {target}")
            expected_hashes[target] = digest

        for directory in ("config", "squaremap"):
            for config in (source_root / directory).rglob("*"):
                if config.is_file() and "overrides/" + config.relative_to(source_root).as_posix() not in expected_hashes:
                    errors.append(f"source config is not indexed: {config.relative_to(source_root)}")

        allowed = {"manifest.json", "modlist.html", *expected_hashes}
        directories = {"overrides/"}
        for name in expected_hashes:
            directories.update(str(parent) + "/" for parent in pathlib.PurePosixPath(name).parents if str(parent) != ".")
        for name in sorted(set(names) - allowed - directories):
            errors.append(f"unexpected archive entry: {name}")
        for name, expected in expected_hashes.items():
            if name not in names:
                errors.append(f"missing exported file: {name}")
            else:
                with archive.open(name) as handle:
                    actual = hashlib.file_digest(handle, "sha512").hexdigest()
                if actual != expected:
                    errors.append(f"exported file hash differs from source: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=pathlib.Path)
    args = parser.parse_args()
    try:
        errors = validate_archive(args.pack)
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERROR: cannot validate pack: {exc}")
        return 2
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("PASS: CurseForge server ZIP metadata, bundled mod hashes, and configs match source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
