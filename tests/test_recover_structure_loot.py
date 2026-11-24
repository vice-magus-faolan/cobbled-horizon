"""Synthetic format/guard regressions; gameplay proof uses the real Minecraft engine."""
import copy
import gzip
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock
import zipfile
import zlib

from pack_fixtures import load_script, ROOT

r = load_script("recover_structure_loot")
POS = (20, 64, 47)
TABLE = "minecraft:chests/shipwreck_supply"


def hold_lock(path, pipe):
    with r.stopped_world(path):
        pipe.send(True)
        pipe.recv()


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.world = self.root / "world"
        self.dim = self.world / "dimensions/minecraft/overworld"
        (self.dim / "region").mkdir(parents=True)
        (self.world / "session.lock").write_bytes(bytes(8))
        self.region = self.dim / "region/r.0.0.mca"
        self.chunk = r.nbtlib.parse_nbt("""{xPos:1,zPos:2,sections:[{Y:4b,block_states:{palette:[{id:"minecraft:chest",properties:{type:"single"}}]}}],block_entities:[{id:"minecraft:chest",x:20,y:64,z:47,Items:[]},{id:"minecraft:chest",x:21,y:64,z:47,Items:[{id:"minecraft:diamond",count:13,Slot:0b}]}],structures:{starts:{test:{Children:[{id:"minecraft:shipwreck",Template:"minecraft:shipwreck/test",TPX:16,TPY:64,TPZ:32,Rot:"NONE"}]}}}}""")
        self.template = r.nbtlib.File(r.nbtlib.parse_nbt("""{palette:[{id:"minecraft:chest"},{id:"minecraft:structure_block"}],blocks:[{pos:[4,0,15],state:0},{pos:[4,1,15],state:1,nbt:{mode:"DATA",metadata:"supply_chest"}}]}"""))
        self.resources = self.root / "resources.jar"
        self.write_resources()
        self.write_region()

    def write_resources(self):
        with zipfile.ZipFile(self.resources, "w") as archive:
            archive.writestr("data/minecraft/structure/shipwreck/test.nbt", gzip.compress(r.encode_nbt(self.template)))
            archive.writestr("data/minecraft/loot_table/chests/shipwreck_supply.json", "{}")
        self.res = r.Resources([self.resources])

    def write_region(self, payload=None, compression=2, path=None):
        data = payload if payload is not None else {1: gzip.compress, 2: zlib.compress, 3: bytes}[compression](r.encode_nbt(r.nbtlib.File(self.chunk)))
        record = (len(data) + 1).to_bytes(4, "big") + bytes([compression]) + data
        raw = bytearray(8192)
        raw[260:264] = bytes([0, 0, 2, 1])
        raw.extend(record + bytes(4096 - len(record)))
        (path or self.region).write_bytes(raw)

    def snapshot(self):
        return {p.relative_to(self.world): p.read_bytes() for p in self.world.rglob("*") if p.is_file()}

    def test_public_cli_dry_apply_repeat_preserve_all_other_data(self):
        (self.world / "player.dat").write_bytes(b"player sentinel")
        before = self.snapshot()
        original_stat = self.region.stat()
        env = dict(os.environ)
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        cmd = [sys.executable, str(ROOT / "scripts/recover_structure_loot.py"), str(self.world), "--resources", str(self.resources)]
        dry = subprocess.run(cmd, env=env, text=True, capture_output=True, check=True)
        self.assertIn("\"eligible\": 1", dry.stdout)
        self.assertEqual(before, self.snapshot())
        result = r.run(self.world, self.res, self.root / "backup")
        self.assertEqual(1, result["applied"])
        final_stat = self.region.stat()
        self.assertEqual((original_stat.st_uid, original_stat.st_gid, original_stat.st_mode), (final_stat.st_uid, final_stat.st_gid, final_stat.st_mode))
        self.assertEqual(before[self.region.relative_to(self.world)], (self.root / "backup" / self.region.relative_to(self.world)).read_bytes())
        updated = dict(r.Region(self.region).chunks())[65]
        expected = copy.deepcopy(self.chunk)
        expected["block_entities"][0]["LootTable"] = r.nbtlib.String(TABLE)
        expected["block_entities"][0]["LootTableSeed"] = r.nbtlib.Long(r.location_seed("dimensions/minecraft/overworld", POS, TABLE))
        self.assertEqual(r.encode_nbt(r.nbtlib.File(expected)), r.encode_nbt(updated))
        self.assertEqual(b"player sentinel", (self.world / "player.dat").read_bytes())
        after = self.snapshot()
        self.assertEqual(0, r.run(self.world, self.res, self.root / "repeat")["applied"])
        self.assertEqual(after, self.snapshot())

    def test_individual_storage_conflicts_never_write(self):
        cases = {
            "occupied": {"Items": r.nbtlib.List[r.nbtlib.Compound]([r.nbtlib.Compound({"id": r.nbtlib.String("minecraft:diamond"), "count": r.nbtlib.Int(1)})])},
            "conflicting_table": {"LootTable": r.nbtlib.String("minecraft:chests/other")},
            "modified": {"LootTableSeed": r.nbtlib.Long(123)},
        }
        for category, changes in cases.items():
            with self.subTest(category=category):
                chunk = copy.deepcopy(self.chunk)
                chunk["block_entities"][0].update(changes)
                actual, entity = r.classify(chunk, POS, {("minecraft:chest", TABLE)}, set(), self.res)
                self.assertEqual(category, actual)
                self.assertIsNone(entity)
        self.assertEqual("private_claims", r.classify(self.chunk, POS, {("minecraft:chest", TABLE)}, {r.packed_pos(POS)}, self.res)[0])
        self.assertEqual("structurally_ambiguous", r.classify(self.chunk, POS, {("minecraft:chest", TABLE), ("minecraft:barrel", TABLE)}, set(), self.res)[0])
        self.assertEqual("unknown_table", r.classify(self.chunk, POS, {("minecraft:chest", "test:missing")}, set(), self.res)[0])
        self.chunk["sections"][0]["block_states"]["palette"][0]["properties"]["type"] = r.nbtlib.String("left")
        self.assertEqual("composite", r.classify(self.chunk, POS, {("minecraft:chest", TABLE)}, set(), self.res)[0])
        self.write_region()
        before = self.snapshot()
        self.assertEqual(0, r.run(self.world, self.res, self.root / "composite")["applied"])
        self.assertEqual(before, self.snapshot())

    def test_private_state_and_unknown_schema_fail_closed(self):
        directory = self.dim / "data/slashloot"
        directory.mkdir(parents=True)
        data = r.nbtlib.File({"data": r.nbtlib.Compound({"blocks": r.nbtlib.List[r.nbtlib.Compound]([r.nbtlib.Compound({"pos": r.nbtlib.Long(r.packed_pos(POS))})]), "entities": r.nbtlib.List[r.nbtlib.Compound]()})})
        data.save(directory / "slashloot.dat", gzipped=True)
        before = self.snapshot()
        result = r.run(self.world, self.res, self.root / "private")
        self.assertEqual(1, result["private_claims"])
        self.assertEqual(before, self.snapshot())
        r.nbtlib.File({"data": r.nbtlib.Compound()}).save(directory / "slashloot.dat", gzipped=True)
        with self.assertRaisesRegex(ValueError, "private-state schema"):
            r.run(self.world, self.res)

    def test_26_3_default_states_and_equivalent_palettes(self):
        for state in (r.nbtlib.String("minecraft:chest"), r.nbtlib.Compound({"": r.nbtlib.String("minecraft:chest")})):
            self.assertEqual("minecraft:chest", r.normalize_state(state)["id"])
        palette = self.template.pop("palette")
        self.template["palettes"] = r.nbtlib.List[r.nbtlib.List[r.nbtlib.Compound]]([palette, copy.deepcopy(palette)])
        self.assertEqual([((4, 0, 15), "minecraft:chest", TABLE)], r.template_claims(self.template, True))
        self.template["palettes"][1][0]["id"] = r.nbtlib.String("minecraft:barrel")
        self.assertIsNone(r.template_claims(self.template, True))

    def test_transforms_location_seed_and_rigid_jigsaw_scope(self):
        results = [r.transform((5, 2, 15), (10, 20, 30), rotation, (4, 0, 15)) for rotation in r.ROTATIONS]
        self.assertEqual([(15, 22, 45), (14, 22, 46), (13, 22, 45), (14, 22, 44)], results)
        seed = r.location_seed("overworld", POS, TABLE)
        self.assertEqual(seed, r.location_seed("overworld", POS, TABLE))
        self.assertNotEqual(seed, r.location_seed("nether", POS, TABLE))
        self.assertNotEqual(seed, r.location_seed("overworld", (21, 64, 47), TABLE))
        piece = dict(id="minecraft:jigsaw", pool_element=dict(element_type="minecraft:single_pool_element", projection="rigid", processors="minecraft:empty", location="test:room"), PosX=1, PosY=2, PosZ=3, rotation="NONE")
        self.assertEqual(("test:room", (1, 2, 3), "NONE", (0, 0, 0)), r.piece_placement(piece))
        piece["pool_element"]["processors"] = "test:processor"
        self.assertIsNone(r.piece_placement(piece))

    def test_baked_barrel_jigsaw_uses_shared_scan_and_apply(self):
        self.template = r.nbtlib.File(r.nbtlib.parse_nbt("""{palette:[{id:"minecraft:barrel"}],blocks:[{pos:[4,0,15],state:0,nbt:{LootTable:"minecraft:chests/shipwreck_supply"}}]}"""))
        self.write_resources()
        self.chunk["sections"][0]["block_states"]["palette"][0] = r.nbtlib.Compound({"id": r.nbtlib.String("minecraft:barrel")})
        self.chunk["block_entities"][0]["id"] = r.nbtlib.String("minecraft:barrel")
        self.chunk["structures"]["starts"]["test"]["Children"] = r.nbtlib.parse_nbt("""[{id:"minecraft:jigsaw",PosX:16,PosY:64,PosZ:32,rotation:"NONE",pool_element:{element_type:"minecraft:single_pool_element",projection:"rigid",processors:"minecraft:empty",location:"minecraft:shipwreck/test"}}]""")
        self.write_region()
        result = r.run(self.world, self.res, self.root / "jigsaw")
        self.assertEqual(1, result["applied"])
        target = dict(r.Region(self.region).chunks())[65]["block_entities"][0]
        self.assertEqual(TABLE, str(target["LootTable"]))

    def test_bad_region_does_not_discard_supported_sources(self):
        # A readable start claims a target across the region boundary. Its broken
        # region sorts before the healthy target, which must still be recovered.
        broken = self.dim / "region/r.-1.0.mca"
        broken.write_bytes(b"incomplete region")
        pieces = self.chunk["structures"]["starts"]["test"]["Children"]
        cross_boundary = copy.deepcopy(pieces[0])
        cross_boundary["TPX"] = r.nbtlib.Int(-512)
        pieces.append(cross_boundary)
        self.write_region()
        before = self.snapshot()
        dry = r.run(self.world, self.res)
        self.assertEqual(2, dry["discovered"])
        self.assertEqual(1, dry["unreadable_regions"])
        self.assertEqual(1, dry["unreadable_target_positions"])
        self.assertEqual(1, dry["eligible"])
        self.assertEqual(0, dry["applied"])
        self.assertEqual(before, self.snapshot())
        result = r.run(self.world, self.res, self.root / "partial")
        self.assertEqual(2, result["discovered"])
        self.assertEqual(1, result["unreadable_regions"])
        self.assertEqual(1, result["unreadable_target_positions"])
        self.assertEqual(1, result["applied"])
        target = dict(r.Region(self.region).chunks())[65]["block_entities"][0]
        self.assertEqual(TABLE, str(target["LootTable"]))
        self.assertEqual(before[broken.relative_to(self.world)], broken.read_bytes())
        after = self.snapshot()
        repeat = r.run(self.world, self.res, self.root / "partial-repeat")
        self.assertEqual(0, repeat["applied"])
        self.assertEqual(1, repeat["already_managed"])
        self.assertEqual(1, repeat["unreadable_target_positions"])
        self.assertEqual(after, self.snapshot())

    def check_skipped_input(self, payload, label, compression=2, allocation=None, target_only=False):
        # A bad SECOND dimension must neither abort after overworld replacement
        # nor prevent a THIRD healthy dimension from being recovered.
        bad = self.world / "dimensions/minecraft/the_nether/region/r.0.0.mca"
        later = self.world / "dimensions/test/healthy/region/r.0.0.mca"
        bad.parent.mkdir(parents=True, exist_ok=True)
        later.parent.mkdir(parents=True, exist_ok=True)
        self.write_region()
        self.write_region(path=later)
        self.write_region(payload=payload, compression=compression, path=bad)
        # A readable structure start also claims the bad target across its region
        # boundary, exercising target loading even when discovery skips bad bytes.
        source = copy.deepcopy(self.chunk)
        source["xPos"] = r.nbtlib.Int(-31)
        source["block_entities"] = r.nbtlib.List[r.nbtlib.Compound]()
        source["sections"] = r.nbtlib.List[r.nbtlib.Compound]()
        self.write_region(payload=zlib.compress(r.encode_nbt(r.nbtlib.File(source))), path=bad.with_name("r.-1.0.mca"))
        if allocation is not None:
            raw = bytearray(bad.read_bytes())
            key, value = allocation
            raw[key] = value
            bad.write_bytes(raw)
        (self.world / "player.dat").write_bytes(b"unrelated player sentinel")
        before = self.snapshot()
        dry = r.run(self.world, self.res)
        self.assertEqual(before, self.snapshot())
        applied = r.run(self.world, self.res, self.root / (label + "-backup"))
        after = self.snapshot()
        self.assertEqual(before[bad.relative_to(self.world)], bad.read_bytes())
        changed = {name for name in before if before[name] != after[name]}
        self.assertEqual({self.region.relative_to(self.world), later.relative_to(self.world)}, changed)
        self.assertEqual(set(before), set(after))
        discovered, unreadable, unreadable_targets = 3, 0 if target_only else 1, 1
        self.assertEqual((3, 2, 0), (dry["discovered"], dry["eligible"], dry["applied"]))
        self.assertEqual((discovered, 2, unreadable, unreadable_targets), (applied["discovered"], applied["applied"], applied.get("unreadable_regions", 0), applied.get("unreadable_target_positions", 0)))
        repeat = r.run(self.world, self.res, self.root / (label + "-repeat"))
        self.assertEqual((0, 2, unreadable), (repeat["applied"], repeat["already_managed"], repeat.get("unreadable_regions", 0)))
        self.assertEqual(after, self.snapshot())

    def test_java_modified_utf8_and_truncated_nbt_skip_without_text_loss(self):
        self.chunk["review_text"] = r.nbtlib.String("A!B")
        encoded = r.encode_nbt(r.nbtlib.File(self.chunk))
        cases = {
            "java-nul": encoded.replace(b"\x00\x03A!B", b"\x00\x04A\xc0\x80B"),
            "java-emoji": encoded.replace(b"\x00\x03A!B", b"\x00\x08A\xed\xa0\xbd\xed\xb8\x80B"),
            "truncated-nbt": encoded[:-1],
        }
        for label, data in cases.items():
            with self.subTest(label=label):
                self.assertNotEqual(encoded, data)
                self.check_skipped_input(zlib.compress(data), label)

    def test_malformed_later_dimension_does_not_abort_healthy_work(self):
        encoded = r.encode_nbt(r.nbtlib.File(self.chunk))
        missing_x = copy.deepcopy(self.chunk)
        del missing_x["xPos"]
        missing_z = copy.deepcopy(self.chunk)
        del missing_z["zPos"]
        bad_starts = copy.deepcopy(self.chunk)
        bad_starts["structures"] = r.nbtlib.String("not a compound")
        bad_entities = copy.deepcopy(self.chunk)
        del bad_entities["block_entities"][0]["x"]
        cases = {
            "gzip-eof": (gzip.compress(encoded)[:-5], 1),
            "unknown-tag": (zlib.compress(b"\xff\x00\x00"), 2),
            "non-compound-root": (zlib.compress(b"\x03\x00\x00\x00\x00\x00\x01"), 2),
            "missing-x": (zlib.compress(r.encode_nbt(r.nbtlib.File(missing_x))), 2),
            "missing-z": (zlib.compress(r.encode_nbt(r.nbtlib.File(missing_z))), 2),
            "bad-start-shape": (zlib.compress(r.encode_nbt(r.nbtlib.File(bad_starts))), 2),
            "bad-entity-shape": (zlib.compress(r.encode_nbt(r.nbtlib.File(bad_entities))), 2),
        }
        for label, (data, compression) in cases.items():
            with self.subTest(label=label):
                self.check_skipped_input(data, label, compression, target_only=label == "bad-entity-shape")

    def test_invalid_allocations_skip_without_duplicate_targets(self):
        cases = {
            "aliased": (slice(264, 268), bytes([0, 0, 2, 1])),
            "past-end": (263, 2),
            "header-alias": (slice(260, 264), bytes([0, 0, 1, 1])),
            "zero-offset-count": (slice(264, 268), bytes([0, 0, 0, 1])),
        }
        for label, allocation in cases.items():
            with self.subTest(label=label):
                self.check_skipped_input(None, label, allocation=allocation)

    def test_owner_mismatch_refuses_public_apply_without_chown(self):
        before = self.snapshot()
        actual_fstat = r.os.fstat
        for attribute in ("st_uid", "st_gid"):
            with self.subTest(attribute=attribute):
                def different_owner(fd):
                    info = actual_fstat(fd)
                    fields = dict(st_uid=info.st_uid, st_gid=info.st_gid)
                    fields[attribute] += 1
                    return SimpleNamespace(**fields)
                with mock.patch.object(r.os, "fstat", side_effect=different_owner):
                    with self.assertRaisesRegex(PermissionError, "ownership"):
                        r.run(self.world, self.res, self.root / ("owner-refusal-" + attribute))
                self.assertEqual(before, self.snapshot())

    def test_backup_serialization_and_replace_failures_remain_fatal(self):
        cases = [(r.os, "fsync", OSError("backup failure")),
                 (r.Region, "updated", ValueError("serialization failure")),
                 (r.os, "replace", OSError("replace failure"))]
        for index, (owner, method, error) in enumerate(cases):
            with self.subTest(method=method):
                before = self.snapshot()
                with mock.patch.object(owner, method, side_effect=error):
                    with self.assertRaisesRegex(type(error), str(error)):
                        r.run(self.world, self.res, self.root / ("fatal-" + str(index)))
                self.assertEqual(before, self.snapshot())
        with mock.patch.object(r.hashlib, "file_digest") as digest:
            digest.return_value.digest.return_value = b"incorrect readback"
            with self.assertRaisesRegex(OSError, "readback failed"):
                r.run(self.world, self.res, self.root / "readback-failure")
        self.assertNotEqual(before[self.region.relative_to(self.world)], self.region.read_bytes())
        self.assertEqual(before[self.region.relative_to(self.world)], (self.root / "readback-failure" / self.region.relative_to(self.world)).read_bytes())

    def test_corrupt_region_and_locked_world_are_not_accepted(self):
        self.region.write_bytes(self.region.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError, "region length"):
            r.Region(self.region)
        a, b = multiprocessing.Pipe()
        process = multiprocessing.Process(target=hold_lock, args=(self.world, b))
        process.start()
        try:
            self.assertTrue(a.poll(5))
            self.assertTrue(a.recv())
            with self.assertRaises(BlockingIOError):
                r.run(self.world, self.res, self.root / "locked")
            self.assertFalse((self.root / "locked").exists())
        finally:
            a.send(True)
            process.join(5)
            if process.is_alive():
                process.terminate()
                process.join()
            a.close()
            b.close()


if __name__ == "__main__":
    unittest.main()
