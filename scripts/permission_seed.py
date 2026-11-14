#!/usr/bin/env python3
"""Package the authored group policy for a one-time native LuckPerms import."""

from __future__ import annotations

import argparse
import gzip
import io
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED_SOURCE = "config/cobbled-horizon/luckperms-groups.json"
SEED_IMPORT = SEED_SOURCE + ".gz"
SEED_PATHS = {SEED_SOURCE, SEED_IMPORT}


def is_pack_override(relative: str) -> bool:
    """Admit only the two policy encodings, never LuckPerms runtime state."""
    if relative.startswith("config/cobbled-horizon/"):
        return relative in SEED_PATHS
    return relative.startswith(("config/", "squaremap/")) and not relative.startswith("config/luckperms/")


def valid_node(node: dict) -> bool:
    if set(node) != {"type", "key", "value"} or type(node["value"]) is not bool:
        return False
    if node["type"] == "inheritance":
        return node["key"] == "group.default" and node["value"] is True
    key = node["key"]
    return node["type"] == "permission" and isinstance(key, str) and key.startswith("sswaystones.") and "*" not in key


def policy_bytes(root: pathlib.Path) -> bytes:
    """Reject private metadata and contextual/temporary or non-policy grants."""
    data = (root / SEED_SOURCE).read_bytes()
    policy = json.loads(data)
    if set(policy) != {"groups", "tracks"} or policy["tracks"] != {}:
        raise ValueError("seed must contain only groups and empty tracks")
    if set(policy["groups"]) != {"default", "owner", "helper"}:
        raise ValueError("seed must contain only default, owner and helper")
    for group in policy["groups"].values():
        if set(group) != {"nodes"} or not isinstance(group["nodes"], list):
            raise ValueError("seed groups must contain only a nodes array")
        if not all(isinstance(node, dict) and valid_node(node) for node in group["nodes"]):
            raise ValueError("seed contains an unsupported node or private metadata")
    return data


def import_bytes(data: bytes) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as stream:
        stream.write(data)
    return output.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        data = policy_bytes(ROOT)
        target = ROOT / SEED_IMPORT
        if args.check:
            if gzip.decompress(target.read_bytes()) != data:
                raise ValueError("import seed differs from canonical JSON; run make refresh")
        else:
            target.write_bytes(import_bytes(data))
    except (OSError, ValueError, TypeError, KeyError, EOFError) as exc:
        print(f"ERROR: permission seed: {exc}")
        return 1
    print("PASS: group-only permission seed " + ("matches canonical JSON" if args.check else "packaged for import"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
