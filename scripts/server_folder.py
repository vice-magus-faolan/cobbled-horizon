#!/usr/bin/env python3
"""Prepare a complete server folder or private installation ZIP from pinned inputs.

Preparation checks integrity, not public distribution clearance. It neither
installs Minecraft nor grants permission to redistribute the resulting binaries.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import shutil
import stat
import tempfile
import urllib.request
import zipfile

import validate_mrpack

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB_UPLOAD_LIMIT = 100_000_000  # DatHost's documented 100 MB web-upload limit.


def validate_directory(path: pathlib.Path, source_root: pathlib.Path = ROOT) -> list[str]:
    """Require exactly the pinned mods, indexed configs and recipient notices."""
    errors: list[str] = []
    hashes = validate_mrpack.payload_hashes(source_root, errors)
    directories = {str(parent) for name in hashes for parent in pathlib.PurePosixPath(name).parents if str(parent) != "."}
    if not path.is_dir() or path.is_symlink():
        return ["server folder must be a regular directory"]
    for member in path.rglob("*"):
        name = member.relative_to(path).as_posix()
        if member.is_symlink() or not (member.is_file() or member.is_dir()):
            errors.append("unsafe server entry type: " + name)
        elif (member.is_dir() and name not in directories) or (member.is_file() and name not in hashes):
            errors.append("unexpected server entry: " + name)
    if errors:
        return errors  # Never read through a rejected directory/symlink ancestor.
    for name, expected in hashes.items():
        member = path / name
        if not member.is_file() or member.is_symlink():
            errors.append("missing regular server file: " + name)
        else:
            with member.open("rb") as reader:
                if hashlib.file_digest(reader, "sha512").hexdigest() != expected:
                    errors.append("server file hash differs from source: " + name)
    return errors


def materialize(mrpack: pathlib.Path, destination: pathlib.Path, source_root: pathlib.Path = ROOT) -> None:
    """Validate before downloads; expose only a complete fresh server folder."""
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("server destination must be fresh: " + str(destination))
    index, contents = validate_mrpack.read_index(mrpack)
    pack = validate_mrpack.load_toml(source_root / "pack.toml")
    errors, _, entries = validate_mrpack.validate_index(index, contents, pack["versions"]["minecraft"], "fabric", source_root)
    if errors:
        raise ValueError("invalid materialization plan: " + "; ".join(errors))
    # Stage beside the destination: rename must not cross filesystems. Failure
    # removes only this invocation's own staging tree, never an existing server.
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".materialize-") as directory:
        candidate = pathlib.Path(directory) / "server"
        candidate.mkdir()
        for entry in entries:
            target = candidate / entry["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(entry["downloads"][0], timeout=60) as response, target.open("wb") as writer:
                shutil.copyfileobj(response, writer)
            if target.stat().st_size != entry["fileSize"]:
                raise ValueError("upstream download size differs from selected pin: " + entry["path"])
        validate_mrpack.validate_stage(candidate, entries, errors)
        if errors:
            raise ValueError("invalid downloaded payload: " + "; ".join(errors))
        for name, data in contents.items():
            if name.startswith("overrides/") and not name.endswith("/"):
                target = candidate / name.removeprefix("overrides/")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        errors = validate_directory(candidate, source_root)
        if errors:
            raise ValueError("invalid server folder: " + "; ".join(errors))
        if destination.exists() or destination.is_symlink():
            raise FileExistsError("server destination must be fresh: " + str(destination))
        candidate.rename(destination)


def server_zip(directory: pathlib.Path, destination: pathlib.Path, source_root: pathlib.Path = ROOT) -> int:
    """Archive a validated, quiescent folder; never replace an existing path.

    Stage beside the destination and link exclusively only after ZIP closure.
    This prevents both partial archives and a concurrent creator being clobbered.
    """
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("server ZIP destination must be fresh: " + str(destination))
    errors = validate_directory(directory, source_root)
    if errors:
        raise ValueError("invalid server folder: " + "; ".join(errors))
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".server-zip-") as staging:
        candidate = pathlib.Path(staging) / "server.zip"
        with zipfile.ZipFile(candidate, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(directory.rglob("*"), key=lambda item: item.relative_to(directory).as_posix()):
                is_directory = path.is_dir()
                name = path.relative_to(directory).as_posix() + ("/" if is_directory else "")
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = ((stat.S_IFDIR | 0o755) if is_directory else (stat.S_IFREG | 0o644)) << 16
                info.external_attr |= 0x10 if is_directory else 0
                info.compress_type = zipfile.ZIP_DEFLATED
                if is_directory:
                    archive.writestr(info, b"")
                else:
                    with path.open("rb") as reader, archive.open(info, "w", force_zip64=True) as writer:
                        shutil.copyfileobj(reader, writer)
        os.link(candidate, destination)
        return destination.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("materialize", help="prepare all pinned downloads without publication or runtime installation")
    prepare.add_argument("mrpack", type=pathlib.Path)
    prepare.add_argument("destination", type=pathlib.Path)
    validate = commands.add_parser("validate", help="check an unmodified materialized folder before runtime provisioning")
    validate.add_argument("directory", type=pathlib.Path)
    archive = commands.add_parser("zip", help="write a validated folder as a private owner-installation ZIP")
    archive.add_argument("directory", type=pathlib.Path)
    archive.add_argument("destination", type=pathlib.Path)
    args = parser.parse_args()
    try:
        if args.command == "materialize":
            materialize(args.mrpack, args.destination, ROOT)
            errors = []
        elif args.command == "zip":
            size = server_zip(args.directory, args.destination, ROOT)
            print(f"Private server ZIP: {args.destination} ({size} bytes)")
            if size > WEB_UPLOAD_LIMIT:
                print("WARNING: exceeds DatHost's 100 MB web-upload limit. Upload the extracted server folder over FTP instead.")
            errors = []
        else:
            errors = validate_directory(args.directory, ROOT)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"ERROR: cannot {args.command} server pack: {exc}")
        return 2
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("PASS: complete server folder membership, hashes, configs and notices match source; not public redistribution clearance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
