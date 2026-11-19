#!/usr/bin/env python3
"""Read release identity and version-bound publication eligibility."""

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


def publication_prerelease(version: str, policy: dict) -> str:
    """Only an explicit approval for this exact version permits stable publication."""
    if set(policy) - {"schema", "production"} or type(policy.get("schema")) is not int or policy["schema"] != 1:
        raise ValueError("invalid release policy schema or unknown fields")
    if "production" not in policy:
        return "true"
    approval = policy["production"]
    if not isinstance(approval, dict) or set(approval) != {"version", "approval-reference"}:
        raise ValueError("production eligibility requires version and approval-reference")
    if approval["version"] != version:
        raise ValueError("production eligibility is stale: version must match pack.toml exactly")
    reference = approval["approval-reference"]
    if not isinstance(reference, str) or not reference.strip() or len(reference) > 512 or any(ord(char) < 32 for char in reference):
        raise ValueError("production approval-reference must be nonempty single-line text (at most 512 characters)")
    return "false"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag")
    parser.add_argument("--expected-minecraft", help="independent version branch (PR base or push branch)")
    parser.add_argument("--publication", action="store_true", help="validate release-policy.toml and include prerelease classification")
    parser.add_argument("--field", choices=("version", "minecraft", "tag", "basename", "prerelease"))
    args = parser.parse_args()
    try:
        with (ROOT / "pack.toml").open("rb") as handle:
            values = metadata(tomllib.load(handle), args.tag, args.expected_minecraft)
        if args.publication:
            path = ROOT / "release-policy.toml"
            try:
                with path.open("rb") as handle:
                    policy = tomllib.load(handle)
            except FileNotFoundError:
                policy = {"schema": 1}  # Absence never grants production eligibility.
            values["prerelease"] = publication_prerelease(values["version"], policy)
        if args.field:
            print(values[args.field])
        else:
            for key, value in values.items():
                print(f"{key}={value}")
    except (OSError, KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
