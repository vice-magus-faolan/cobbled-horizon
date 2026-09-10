#!/usr/bin/env python3
"""Report whether every pinned project has a build for a target Minecraft version."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tomllib
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
USER_AGENT = "cobbled-horizon-readiness/0.1 (+https://github.com/vice-magus-faolan/cobbled-horizon)"


def load_projects() -> list[tuple[str, str]]:
    projects: list[tuple[str, str]] = []
    for path in sorted((ROOT / "mods").glob("*.pw.toml")):
        with path.open("rb") as handle:
            data = tomllib.load(handle)
        projects.append((data["name"], data["update"]["modrinth"]["mod-id"]))
    return projects


def fetch_versions(project_id: str) -> list[dict]:
    request = urllib.request.Request(
        f"https://api.modrinth.com/v2/project/{project_id}/version",
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def compatible_versions(versions: list[dict], target: str, release_only: bool) -> list[dict]:
    matches = []
    for version in versions:
        if target not in version.get("game_versions", []):
            continue
        if "fabric" not in version.get("loaders", []):
            continue
        if release_only and version.get("version_type") != "release":
            continue
        matches.append(version)
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minecraft", default="26.3", help="exact target version")
    parser.add_argument("--release-only", action="store_true", help="reject alpha and beta files")
    args = parser.parse_args()

    missing: list[str] = []
    for name, project_id in load_projects():
        try:
            versions = fetch_versions(project_id)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            print(f"ERROR  {name}: lookup failed: {exc}")
            missing.append(name)
            continue
        matches = compatible_versions(versions, args.minecraft, args.release_only)
        if not matches:
            print(f"WAIT   {name}: no matching Fabric {args.minecraft} file")
            missing.append(name)
            continue
        selected = matches[0]
        print(f"READY  {name}: {selected['version_number']} ({selected['version_type']})")

    if missing:
        print(f"\nNOT READY: {len(missing)} project(s) still block Minecraft {args.minecraft}")
        return 1
    print(f"\nREADY: all projects publish a Fabric {args.minecraft} file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
