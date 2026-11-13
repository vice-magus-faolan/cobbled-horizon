#!/usr/bin/env python3
"""Build or validate a root-layout server ZIP using the native CurseForge payload."""

from __future__ import annotations

import argparse
import pathlib
import shutil
import zipfile

import validate_curseforge

ROOT = pathlib.Path(__file__).resolve().parents[1]


def validate_archive(path: pathlib.Path, source_root: pathlib.Path = ROOT) -> list[str]:
    """Require exactly the source-pinned mods and configuration at the ZIP root."""
    errors: list[str] = []
    hashes = validate_curseforge.payload_hashes(source_root, errors)
    with zipfile.ZipFile(path) as archive:
        errors.extend(validate_curseforge.validate_payload(archive, hashes))
    return errors


def build_archive(
    curseforge: pathlib.Path,
    output: pathlib.Path,
    source_root: pathlib.Path = ROOT,
) -> None:
    """Validate before opening output; stream payload files without extracting them."""
    if curseforge.resolve() == output.resolve():
        raise ValueError("server output must differ from the CurseForge input")
    errors = validate_curseforge.validate_archive(curseforge, source_root)
    if errors:
        raise ValueError("invalid CurseForge input: " + "; ".join(errors))
    # The validated allowlist is authoritative, not a prefix-only copy of the ZIP.
    hashes = validate_curseforge.payload_hashes(source_root, [])
    with zipfile.ZipFile(curseforge) as source, zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED
    ) as destination:
        for name in sorted(hashes):
            with source.open("overrides/" + name) as reader, destination.open(name, "w") as writer:
                shutil.copyfileobj(reader, writer)
    errors = validate_archive(output, source_root)
    if errors:
        raise ValueError("invalid server output: " + "; ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="copy the validated CF payload to a standalone ZIP")
    build.add_argument("curseforge", type=pathlib.Path)
    build.add_argument("output", type=pathlib.Path)
    validate = commands.add_parser("validate", help="check a complete standalone server ZIP")
    validate.add_argument("pack", type=pathlib.Path)
    args = parser.parse_args()
    try:
        if args.command == "build":
            build_archive(args.curseforge, args.output)
            errors = []
        else:
            errors = validate_archive(args.pack)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"ERROR: cannot {args.command} server pack: {exc}")
        return 2
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("PASS: standalone server ZIP membership, mod hashes, and configs match source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
