#!/usr/bin/env python3
"""Read release identity from pack.toml and optionally verify a Git tag."""

from __future__ import annotations

import argparse
import pathlib
import re
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
NUMBER = r"(?:0|[1-9][0-9]*)"


def metadata(pack: dict, tag: str | None = None) -> dict[str, str]:
    minecraft = pack["versions"]["minecraft"]
    version = pack["version"]
    if not re.fullmatch(rf"{NUMBER}(?:\.{NUMBER})+", minecraft):
        raise ValueError("release Minecraft version must contain dotted numbers")
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
    parser.add_argument("--field", choices=("version", "minecraft", "tag", "basename"))
    args = parser.parse_args()
    try:
        with (ROOT / "pack.toml").open("rb") as handle:
            values = metadata(tomllib.load(handle), args.tag)
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
