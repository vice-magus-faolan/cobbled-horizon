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

    def write_region(self):
        data = zlib.compress(r.encode_nbt(r.nbtlib.File(self.chunk)))
        record = (len(data) + 1).to_bytes(4, "big") + bytes([2]) + data
        raw = bytearray(8192)
        raw[260:264] = bytes([0, 0, 2, 1])
        raw.extend(record + bytes(4096 - len(record)))
        self.region.write_bytes(raw)

    def snapshot(self):
        return {p.relative_to(self.world): p.read_bytes() for p in self.world.rglob("*") if p.is_file()}

    def test_public_cli_dry_apply_repeat_preserve_all_other_data(self):
        (self.world / "player.dat").write_bytes(b"player sentinel")
        before = self.snapshot()
        env = dict(os.environ)
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        cmd = [sys.executable, str(ROOT / "scripts/recover_structure_loot.py"), str(self.world), "--resources", str(self.resources)]
        dry = subprocess.run(cmd, env=env, text=True, capture_output=True, check=True)
        self.assertIn("\"eligible\": 1", dry.stdout)
        self.assertEqual(before, self.snapshot())
        result = r.run(self.world, self.res, self.root / "backup")
        self.assertEqual(1, result["applied"])
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
        broken = self.dim / "region/r.1.1.mca"
        broken.write_bytes(b"incomplete region")
        result = r.run(self.world, self.res, self.root / "partial")
        self.assertEqual(1, result["unreadable_regions"])
        self.assertEqual(1, result["applied"])
        self.assertEqual(b"incomplete region", broken.read_bytes())

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
