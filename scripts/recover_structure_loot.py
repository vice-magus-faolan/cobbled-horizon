#!/usr/bin/env python3
"""Offline, one-time structure loot recovery for Minecraft 26.3 (nbtlib 2.0.4)."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
import fcntl
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile
import zipfile
import zlib

sys.dont_write_bytecode = True
import nbtlib

CONTAINERS = {"minecraft:chest", "minecraft:trapped_chest", "minecraft:barrel"}
ROTATIONS = {"NONE": 0, "CLOCKWISE_90": 1, "CLOCKWISE_180": 2, "COUNTERCLOCKWISE_90": 3}
SHIP_TABLES = {name + "_chest": "minecraft:chests/shipwreck_" + name
               for name in ("supply", "map", "treasure")}
# Only catch these while loading or consuming untrusted world input.
INPUT_ERRORS = (ValueError, OSError, zlib.error, EOFError, KeyError, TypeError,
                IndexError, AttributeError, OverflowError, RecursionError, struct.error)
IDENTIFIER = re.compile(r"[a-z0-9_.-]+:[a-z0-9_./-]+")


def parse_nbt(data):
    return nbtlib.File.parse(io.BytesIO(data))


def encode_nbt(tag):
    out = io.BytesIO()
    tag.write(out)
    return out.getvalue()


class Region:
    """Keep untouched sectors verbatim; append replacements in an atomic file swap."""
    def __init__(self, path):
        self.path = path
        self.raw = path.read_bytes()
        if len(self.raw) < 8192 or len(self.raw) % 4096:
            raise ValueError(f"invalid region length: {path}")

    def allocations(self):
        used = {0, 1}
        for slot in range(1024):
            offset = int.from_bytes(self.raw[slot * 4:slot * 4 + 3], "big")
            sectors = self.raw[slot * 4 + 3]
            if not offset and not sectors:
                continue
            allocated = set(range(offset, offset + sectors))
            if not sectors or offset < 2 or offset + sectors > len(self.raw) // 4096 or used.intersection(allocated):
                raise ValueError(f"invalid/overlapping chunk allocation: {self.path}:{slot}")
            used.update(allocated)
            yield slot, offset * 4096, sectors

    def chunks(self):
        # Validate ALL header allocations before yielding any chunk/claim.
        allocations = list(self.allocations())
        for slot, offset, sectors in allocations:
            length = int.from_bytes(self.raw[offset:offset + 4], "big")
            if length < 1 or length + 4 > sectors * 4096:
                raise ValueError(f"invalid chunk length: {self.path}:{slot}")
            compression = self.raw[offset + 4]
            payload = self.raw[offset + 5:offset + length + 4]
            decoders = {1: gzip.decompress, 2: zlib.decompress, 3: bytes}
            if compression not in decoders:
                raise ValueError(f"unsupported compression/external chunk {compression}: {self.path}:{slot}")
            data = decoders[compression](payload)
            chunk = parse_nbt(data)
            # nbtlib uses standard UTF-8, not Java modified UTF-8, and accepts
            # some truncated NBT. Refuse lossy/noncanonical input, never repair it.
            if encode_nbt(chunk) != data:
                raise ValueError(f"NBT does not roundtrip losslessly: {self.path}:{slot}")
            # Require coordinates even when discovery itself never uses them.
            int(chunk["xPos"]), int(chunk["zPos"])
            yield slot, chunk

    def updated(self, chunks):
        raw = bytearray(self.raw)
        for slot, tag in chunks.items():
            data = zlib.compress(encode_nbt(tag))
            record = (len(data) + 1).to_bytes(4, "big") + bytes([2]) + data
            sectors = math.ceil(len(record) / 4096)
            offset = len(raw) // 4096
            if sectors > 255 or offset >= 2 ** 24:
                raise ValueError("replacement exceeds inline Anvil bounds")
            raw[slot * 4:slot * 4 + 4] = offset.to_bytes(3, "big") + bytes([sectors])
            raw.extend(record + bytes(sectors * 4096 - len(record)))
        return bytes(raw)


def transform(pos, origin, rotation, pivot=(0, 0, 0)):
    x, y, z = map(int, pos)
    px, _, pz = pivot
    for _ in range(ROTATIONS[rotation]):
        x, z = px + pz - z, pz - px + x
    return (x + origin[0], y + origin[1], z + origin[2])


def location_seed(dimension, pos, table):
    """New deterministic entitlement, not reconstruction of the lost original RNG."""
    identity = json.dumps(["slashloot-recovery-v1", dimension, list(pos), table], separators=(",", ":"))
    return int.from_bytes(hashlib.sha256(identity.encode()).digest()[:8], "big", signed=True)


class Resources:
    """Reject conflicting resources instead of guessing datapack/mod load order."""
    def __init__(self, paths):
        self.entries = {}
        for path in paths:
            self.add(path)

    def add(self, path):
        if path.is_dir():
            for file in path.glob("data/**/*"):
                if file.is_file():
                    self.record(file.relative_to(path).as_posix(), file.read_bytes())
        else:
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if name.startswith("data/") and ("/structure/" in name or "/loot_table/" in name):
                        self.record(name, archive.read(name))

    def record(self, name, data):
        if name not in self.entries:
            self.entries[name] = data
        elif self.entries[name] != data:
            self.entries[name] = None

    def get(self, identifier, kind, suffix):
        if not IDENTIFIER.fullmatch(identifier) or ".." in identifier.split(":", 1)[1].split("/"):
            return None
        namespace, name = identifier.split(":", 1)
        return self.entries.get(f"data/{namespace}/{kind}/{name}{suffix}")

    def template(self, name):
        data = self.get(name, "structure", ".nbt")
        return parse_nbt(gzip.decompress(data)) if data else None


def piece_placement(piece):
    """Only layouts whose exact placement semantics are supported here."""
    kind = str(piece.get("id", ""))
    if kind == "minecraft:shipwreck":
        name = str(piece["Template"])
        return name, tuple(int(piece["TP" + axis]) for axis in "XYZ"), str(piece["Rot"]), (4, 0, 15)
    if kind == "minecraft:jigsaw":
        element = piece.get("pool_element", {})
        if str(element.get("element_type")) not in {"minecraft:single_pool_element", "minecraft:legacy_single_pool_element"}:
            return None
        if str(element.get("projection")) != "rigid" or str(element.get("processors")) != "minecraft:empty":
            return None
        return str(element["location"]), tuple(int(piece[axis]) for axis in ("PosX", "PosY", "PosZ")), str(piece["rotation"]), (0, 0, 0)
    return None


def palette_claims(template, palette, shipwreck):
    """Extract baked tables, plus the native shipwreck marker-to-chest mapping."""
    blocks = {tuple(map(int, b["pos"])): b for b in template["blocks"]}
    claims = []
    for pos, block in blocks.items():
        state = palette[int(block["state"])]
        block_id = str(state.get("Name", state.get("id")))
        nbt = block.get("nbt", {})
        if block_id in CONTAINERS and "LootTable" in nbt:
            claims.append((pos, block_id, str(nbt["LootTable"])))
        if shipwreck and block_id == "minecraft:structure_block" and str(nbt.get("mode")) == "DATA":
            table = SHIP_TABLES.get(str(nbt.get("metadata")))
            below = (pos[0], pos[1] - 1, pos[2])
            chest = blocks.get(below)
            if table and chest is not None and str(palette[int(chest["state"])].get("Name", palette[int(chest["state"])].get("id"))) == "minecraft:chest":
                claims.append((below, "minecraft:chest", table))
    return claims


def template_claims(template, shipwreck):
    palettes = template.get("palettes", [template.get("palette")])
    variants = [set(palette_claims(template, palette, shipwreck)) for palette in palettes]
    if not variants or any(claims != variants[0] for claims in variants[1:]):
        return None
    return sorted(variants[0])


def discover_chunks(chunks, resources, counts):
    claims = defaultdict(set)
    for _, chunk in chunks:
        for start in chunk.get("structures", {}).get("starts", {}).values():
            for piece in start.get("Children", []):
                placement = piece_placement(piece)
                if placement is None:
                    counts["unsupported_pieces"] += 1
                    continue
                name, origin, rotation, pivot = placement
                template = resources.template(name)
                if template is None or rotation not in ROTATIONS:
                    counts["unsupported_pieces"] += 1
                    continue
                sources = template_claims(template, str(piece["id"]) == "minecraft:shipwreck")
                if sources is None:
                    counts["ambiguous_pieces"] += 1
                    continue
                for pos, block, table in sources:
                    claims[transform(pos, origin, rotation, pivot)].add((block, table))
    return claims


def discover(region_paths, resources, counts):
    claims = defaultdict(set)
    unreadable = set()
    for path in region_paths:
        region_counts = Counter()
        try:
            chunks = list(Region(path).chunks())
            found = discover_chunks(chunks, resources, region_counts)
        except INPUT_ERRORS as error:
            counts["unreadable_regions"] += 1
            unreadable.add(path)
            print(f"unreadable discovery region {path}: {error}", file=sys.stderr)
            continue
        # Do not retain partial claims/counts from a malformed region.
        counts.update(region_counts)
        for pos, candidates in found.items():
            claims[pos].update(candidates)
    return claims, unreadable


def block_state(chunk, pos):
    x, y, z = pos
    section = next((s for s in chunk.get("sections", []) if int(s["Y"]) == y // 16), None)
    if section is None:
        return None
    states = section.get("block_states", {})
    palette = states.get("palette", [])
    if len(palette) == 1:
        return normalize_state(palette[0])
    if not palette or "data" not in states:
        return None
    bits = max(4, (len(palette) - 1).bit_length())
    per_long = 64 // bits
    index = (y % 16) * 256 + (z % 16) * 16 + x % 16
    packed = int(states["data"][index // per_long]) & ((1 << 64) - 1)
    return normalize_state(palette[(packed >> ((index % per_long) * bits)) & ((1 << bits) - 1)])


def normalize_state(state):
    # 26.3 encodes default states as strings or an empty-key shorthand compound.
    if isinstance(state, str):
        return {"id": str(state)}
    if set(state) == {""}:
        return {"id": str(state[""])}
    return state


def packed_pos(pos):
    x, y, z = pos
    return ((x & 0x3ffffff) << 38 | (z & 0x3ffffff) << 12 | (y & 0xfff))


def private_positions(dimension):
    positions = set()
    for path in (dimension / "data").rglob("*.dat"):
        if "slashloot" not in str(path.relative_to(dimension)).lower() and "perplayerloot" not in path.name.lower():
            continue
        root = nbtlib.load(path)
        data = root.get("data", {})
        if "blocks" not in data or "entities" not in data:
            raise ValueError(f"unknown private-state schema: {path}")
        positions.update(int(row["pos"]) & ((1 << 64) - 1) for row in data["blocks"])
    return positions


def classify(chunk, pos, candidates, managed, resources):
    if len(candidates) != 1:
        return "structurally_ambiguous", None
    block, table = next(iter(candidates))
    if not resources.get(table, "loot_table", ".json"):
        return "unknown_table", None
    entities = [be for be in chunk.get("block_entities", []) if tuple(int(be[k]) for k in "xyz") == pos]
    state = block_state(chunk, pos)
    if len(entities) != 1 or state is None or str(state.get("Name", state.get("id"))) != block or str(entities[0]["id"]) != block:
        return "incompatible", None
    entity = entities[0]
    if str(state.get("Properties", state.get("properties", {})).get("type", "single")) != "single":
        return "composite", None
    if entity.get("Items"):
        return "occupied", None
    if "LootTable" in entity:
        return ("already_managed" if str(entity["LootTable"]) == table else "conflicting_table"), None
    if packed_pos(pos) in managed:
        return "private_claims", None
    if set(entity) - {"id", "x", "y", "z", "Items", "keepPacked", "components"} or entity.get("components"):
        return "modified", None
    return "eligible", entity


def replace_region(region, updates, backup, relative):
    destination = backup / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as out:
        out.write(region.raw)
        out.flush()
        os.fsync(out.fileno())
    data = region.updated(updates)
    original = region.path.stat()
    pending = None
    try:
        with tempfile.NamedTemporaryFile(dir=region.path.parent, prefix=".slashloot-recovery-", delete=False) as out:
            pending = Path(out.name)
            replacement = os.fstat(out.fileno())
            if (replacement.st_uid, replacement.st_gid) != (original.st_uid, original.st_gid):
                raise PermissionError(f"region ownership would change; run as the server user: {region.path}")
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        shutil.copymode(region.path, pending)
        os.replace(pending, region.path)
    finally:
        if pending is not None:
            pending.unlink(missing_ok=True)
    with region.path.open("rb") as check:
        if hashlib.file_digest(check, "sha256").digest() != hashlib.sha256(data).digest():
            raise OSError(f"region write readback failed: {region.path}")


def classify_targets(chunks, targets, managed, resources):
    # Consume every target shape before allowing any mutation of this region.
    for slot, chunk in chunks:
        chunk_pos = (int(chunk["xPos"]), int(chunk["zPos"]))
        for pos in targets:
            if (pos[0] // 16, pos[2] // 16) == chunk_pos:
                category, entity = classify(chunk, pos, targets[pos], managed, resources)
                yield slot, chunk, pos, category, entity


def process_dimension(world, dimension, resources, backup, counts):
    paths = sorted((dimension / "region").glob("r.*.*.mca"))
    claims, unreadable = discover(paths, resources, counts)
    counts["discovered"] += len(claims)
    managed = private_positions(dimension)
    grouped = defaultdict(dict)
    for pos, candidates in claims.items():
        x, _, z = pos
        grouped[dimension / "region" / f"r.{x // 512}.{z // 512}.mca"][pos] = candidates
    for path, targets in sorted(grouped.items()):
        # A readable neighbor can claim a target in a discovery-rejected region.
        if path in unreadable:
            counts["unreadable_target_positions"] += len(targets)
            continue
        if not path.exists():
            counts["missing_chunk"] += len(targets)
            continue
        try:
            region = Region(path)
            classified = list(classify_targets(region.chunks(), targets, managed, resources))
        except INPUT_ERRORS as error:
            counts["unreadable_target_positions"] += len(targets)
            print(f"unreadable target region {path}: {error}", file=sys.stderr)
            continue
        updates = {}
        remaining = set(targets)
        for slot, chunk, pos, category, entity in classified:
            remaining.discard(pos)
            counts[category] += 1
            if category == "eligible" and backup is not None:
                table = next(iter(targets[pos]))[1]
                entity["LootTable"] = nbtlib.String(table)
                entity["LootTableSeed"] = nbtlib.Long(location_seed(dimension.relative_to(world).as_posix(), pos, table))
                updates[slot] = chunk
                counts["applied"] += 1
        counts["missing_chunk"] += len(remaining)
        if updates:
            replace_region(region, updates, backup, path.relative_to(world))


@contextmanager
def stopped_world(world):
    """Use the same POSIX record lock as the Java session lock; never create it."""
    with (world / "session.lock").open("r+b") as lock:
        fcntl.lockf(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def run(world, resources, backup=None):
    world = world.resolve(strict=True)
    counts = Counter({key: 0 for key in ("discovered", "eligible", "occupied", "structurally_ambiguous", "unknown_table", "already_managed", "applied")})
    with stopped_world(world):
        if backup is not None:
            backup = backup.resolve()
            if backup == world or world in backup.parents:
                raise ValueError("backup must be outside world")
            backup.mkdir(exist_ok=False)
        dimensions = [p.parent for p in world.glob("dimensions/*/*/region")]
        dimensions += [p.parent for p in (world / "region", world / "DIM-1/region", world / "DIM1/region") if p.is_dir()]
        if not dimensions:
            raise ValueError("no supported region directories")
        for dimension in sorted(set(dimensions)):
            process_dimension(world, dimension, resources, backup, counts)
    return dict(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("world", type=Path)
    parser.add_argument("--resources", type=Path, action="append", required=True, help="matching server JAR, mod JARs or datapack roots; repeat as needed")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path, help="new directory outside world, required for apply")
    args = parser.parse_args()
    if args.apply != (args.backup is not None):
        parser.error("apply requires a new --backup directory; dry-run takes no backup")
    resources = Resources(args.resources)
    print(json.dumps(run(args.world, resources, args.backup), sort_keys=True))


if __name__ == "__main__":
    main()
