#!/usr/bin/env python3
"""Build or validate a complete root-layout server ZIP, not a client manifest."""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import shutil
import tempfile
import urllib.request
import zipfile

import distribution
import validate_curseforge
import validate_mrpack

ROOT = pathlib.Path(__file__).resolve().parents[1]


def validate_archive(path: pathlib.Path, source_root: pathlib.Path = ROOT) -> list[str]:
    """Require exactly the source-pinned mods, configs and recipient notices."""
    errors: list[str] = []
    hashes = validate_curseforge.payload_hashes(source_root, errors)
    with zipfile.ZipFile(path) as archive:
        errors.extend(validate_curseforge.validate_payload(archive, hashes))
    return errors


def download_hosted(mrpack: pathlib.Path, root: pathlib.Path, work: pathlib.Path) -> dict[str, pathlib.Path]:
    """Use the validated native Modrinth plan; never resolve a replacement pin."""
    index, contents = validate_mrpack.read_index(mrpack)
    pack = validate_curseforge.load_toml(root / "pack.toml")
    errors, _, entries = validate_mrpack.validate_index(index, contents, pack["versions"]["minecraft"], "fabric", root)
    if errors:
        raise ValueError("invalid materialization plan: " + "; ".join(errors))
    hosted = validate_curseforge.hosted_files(root)
    result = {}
    for position, entry in enumerate(entries):
        if entry["path"] not in hosted:
            continue
        target = work / str(position)
        with urllib.request.urlopen(entry["downloads"][0], timeout=60) as response, target.open("wb") as writer:
            shutil.copyfileobj(response, writer)
        with target.open("rb") as reader:
            actual = hashlib.file_digest(reader, "sha512").hexdigest()
        if actual != entry["hashes"]["sha512"] or target.stat().st_size != entry["fileSize"]:
            raise ValueError("hosted upstream download differs from selected pin: " + entry["path"])
        result[entry["path"]] = target
    if set(result) != set(hosted):
        raise ValueError("materialization plan omits a selected hosted mod")
    return result


def build_archive(
    curseforge: pathlib.Path,
    output: pathlib.Path,
    source_root: pathlib.Path = ROOT,
    mrpack: pathlib.Path | None = None,
) -> None:
    """Integrity-only builder; the public CLI also requires channel clearance.

    Verify every upstream input before opening a candidate output, then validate
    and atomically replace. Never advertise a truncated or partially filled ZIP.
    """
    if curseforge.resolve() == output.resolve() or (mrpack and mrpack.resolve() == output.resolve()):
        raise ValueError("server output must differ from its inputs")
    errors = validate_curseforge.validate_archive(curseforge, source_root)
    if errors:
        raise ValueError("invalid CurseForge input: " + "; ".join(errors))
    hashes = validate_curseforge.payload_hashes(source_root, [])
    hosted = validate_curseforge.hosted_files(source_root)
    if hosted and mrpack is None:
        raise ValueError("hosted references require the complete native Modrinth download plan")
    with tempfile.TemporaryDirectory() as directory:
        work = pathlib.Path(directory)
        downloads = download_hosted(mrpack, source_root, work) if hosted else {}
        candidate = work / "server.zip"
        with zipfile.ZipFile(curseforge) as source, zipfile.ZipFile(candidate, "w", compression=zipfile.ZIP_DEFLATED) as destination:
            for name in sorted(hashes):
                reader = downloads[name].open("rb") if name in downloads else source.open("overrides/" + name)
                with reader, destination.open(name, "w") as writer:
                    shutil.copyfileobj(reader, writer)
        errors = validate_archive(candidate, source_root)
        if errors:
            raise ValueError("invalid server output: " + "; ".join(errors))
        # TMPDIR can be another filesystem: stage beside output for atomic replace.
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".server-", delete=False) as pending:
            pending_path = pathlib.Path(pending.name)
            try:
                with candidate.open("rb") as reader:
                    shutil.copyfileobj(reader, pending)
                pending.close()
                pending_path.replace(output)
            finally:
                pending_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=sorted(distribution.CHANNELS))
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "verify-build"):
        build = commands.add_parser(command, help="prepare complete ZIP; verify-build is nonpublishing integrity-only")
        build.add_argument("curseforge", type=pathlib.Path)
        build.add_argument("output", type=pathlib.Path)
        build.add_argument("--mrpack", type=pathlib.Path, required=True)
    validate = commands.add_parser("validate", help="check a complete standalone server ZIP")
    validate.add_argument("pack", type=pathlib.Path)
    args = parser.parse_args()
    try:
        if args.command != "verify-build":
            distribution.require(args.channel is not None, "explicit distribution channel is required")
            distribution.clearance(ROOT, args.channel)
        if args.command in {"build", "verify-build"}:
            build_archive(args.curseforge, args.output, source_root=ROOT, mrpack=args.mrpack)
            errors = []
        else:
            errors = validate_archive(args.pack, ROOT)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"ERROR: cannot {args.command} server pack: {exc}")
        return 2
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("PASS: complete server ZIP membership, hashes, configs and notices match source; integrity is not upload clearance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
