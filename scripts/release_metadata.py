#!/usr/bin/env python3
"""Read release identity from pack.toml and optionally verify a Git tag."""

from __future__ import annotations

import argparse
import pathlib
import re
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
NUMBER = r"(?:0|[1-9][0-9]*)"


def minecraft_version(pack: dict) -> str:
    """Return the authoritative numeric target, rejecting missing/malformed values."""
    versions = pack.get("versions")
    minecraft = versions.get("minecraft") if isinstance(versions, dict) else None
    if not isinstance(minecraft, str) or not re.fullmatch(rf"{NUMBER}(?:\.{NUMBER})+", minecraft):
        raise ValueError("release Minecraft version must contain dotted numbers")
    return minecraft


def metadata(
    pack: dict, tag: str | None = None, expected_minecraft: str | None = None
) -> dict[str, str]:
    minecraft = minecraft_version(pack)
    version = pack["version"]
    if expected_minecraft is not None and minecraft != expected_minecraft:
        raise ValueError(f"Minecraft target must match version branch {expected_minecraft!r}, got {minecraft!r}")
    if not re.fullmatch(rf"{re.escape(minecraft)}\.{NUMBER}\.{NUMBER}\.{NUMBER}", version):
        raise ValueError(f"pack version must be {minecraft}.MAJOR.MINOR.PATCH")
    expected_tag = f"v{version}"
    if tag is not None and tag != expected_tag:
        raise ValueError(f"release tag must be {expected_tag}, got {tag!r}")
    return {
        "version": version,
        "minecraft": minecraft,
        "tag": expected_tag,
        "basename": f"cobbled-horizon-{version}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag")
    parser.add_argument("--expected-minecraft", help="independent version branch (PR base or push branch)")
    parser.add_argument("--field", choices=("version", "minecraft", "tag", "basename"))
    args = parser.parse_args()
    try:
        with (ROOT / "pack.toml").open("rb") as handle:
            values = metadata(tomllib.load(handle), args.tag, args.expected_minecraft)
    except (KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    if args.field:
        print(values[args.field])
    else:
        for key, value in values.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
