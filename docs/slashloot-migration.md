# Broadwater: one-time historical loot migration

`scripts/recover_structure_loot.py` scans a **stopped Minecraft 26.3 world** and restores pending loot-table metadata on compatible empty structure containers. Ordinary unmodified SlashLoot then supplies per-player loot. This is an optional operator tool, not an installation hook, permanent mod dependency, terrain reset or permission to access Broadwater. Normal new worlds do not need it.

## Eligibility and coverage

One world-level migration approval is sufficient. An expected structure/template position, identified available loot table and compatible empty unmanaged container qualify. No per-chest manifest, continuity witness or original seed is required. An empty player replacement at the expected position can qualify; that risk and new entitlements for previous looters are accepted. Concrete inventory, layout or metadata conflicts still cause individual skips.

The scanner reads stored structure pieces rather than sweeping every empty chest. It supports native shipwreck marker-to-chest positions with their stored origin, rotation and pivot. The same template extraction supports rigid single/legacy-single jigsaw pieces whose processor reference is literally `minecraft:empty`, with baked chest, trapped-chest or barrel tables. Multiple palettes qualify only when their container/table claims agree. Resource conflicts are never resolved by guessing datapack order.

Occupied containers, double/composite chests, incompatible/missing blocks, custom components or unexplained metadata, conflicting tables and existing private claims are not overwritten. Existing matching tables are left alone, including unopened containers. Unsupported piece types, non-rigid or processed jigsaws, missing templates, differing palettes and unknown tables stay outside supported coverage. The tool does not reconstruct procedural dungeons/mineshafts, donor terrain or every modded structure. Its summary is a measured supported subset, not a world-wide loot total.

New seeds are the first eight SHA-256 bytes, interpreted as signed big-endian, of compact JSON `["slashloot-recovery-v1", world-root-relative-dimension-path, [x,y,z], table]`. The dimension path is relative to the world root, for example `dimensions/minecraft/overworld` or `.` for a legacy overworld. This is deterministic per location within that world layout, not recovery of vanished historical randomness. It avoids using a common zero seed for every source. SlashLoot combines that seed with the player UUID. No private loot or prior-player records are inserted.

## Operator procedure

Use Linux/POSIX, Python 3.11 or later and enough disk for region backups plus rewritten regions. Run the tool **as the server user**, not root. Supply matching trusted server/mod/datapack resources; the inner vanilla server JAR is normally `versions/26.3/server-26.3.jar`, not the outer launcher. Include active mod/datapack overrides through repeated `--resources` arguments; conflicting bytes are not resolved by guessing load order.

1. Cleanly stop the server and keep players and other world-writing tools out. Take a complete, consistent **world snapshot**, including all dimensions, player data and private-mod state. The tool backs up changed regions only, not the whole world.
2. If needed, prepare the optional dependency in a dedicated environment. The script and dependency are not exported in the pack:

   ```sh
   python3 -m venv ../recovery-venv
   ../recovery-venv/bin/python -m pip install -r scripts/requirements-recovery.txt
   ```

3. Invoke apply manually with the matching resources and a **new backup directory outside the world**:

   ```sh
   ../recovery-venv/bin/python scripts/recover_structure_loot.py /server/world --resources /server/versions/26.3/server-26.3.jar --resources /server/mods/structures.jar --apply --backup /recovery/regions-before-first-apply
   ```

The script holds the native POSIX session lock, rereads inventories, backs up each changed region and atomically replaces that region. It adds only `LootTable` and `LootTableSeed` to eligible containers; other logical chunk data is preserved. It never clears Items, replaces blocks, rewrites player files or creates private claims. Untouched chunk sectors remain verbatim. Replacement retains the original mode and refuses if the temporary file has a different owner or group; it does not change ownership to force the operation through.

No region is repaired. All allocated sector ranges must be outside the header, non-overlapping and wholly inside the file; inline length and compression limits still apply. Before any mutation, every chunk in a target region must decode and re-encode to exactly its original decompressed NBT bytes, and all consumed discovery/target shapes must be readable. This deliberately skips whole regions containing Java modified-UTF-8 NUL/emoji strings that nbtlib cannot preserve, truncated NBT, malformed coordinates/shapes or unsupported encoding. Discovery and target input failures are reported and skipped while later healthy regions and dimensions continue. A skipped region stays byte-identical, not silently normalized.

Backup, replacement serialization, write, fsync, ownership and readback failures stop the operation, as does unknown private-state schema. Earlier regions may already be applied. Keep the server stopped and either resume unchanged eligible sources after resolving the failure or restore the complete snapshot. Region replacement is atomic, not an all-world transaction or power-loss guarantee. Never remove private claims to make a rerun eligible.

Before any claim, region backups can restore pre-apply metadata while stopped. After loot moves into player inventories, restore the consistent full world snapshot: restoring only regions or only the private ledger can duplicate or lose items. Existing [accepted private-inventory destruction loss](slashloot.md#retention-removal-and-administration) and mixed-double limitations remain unchanged.

## Optional result checks

These exercises verify results; they are not required operator gates. You may rehearse restoration or try the utility on a disposable copy first. Omitting `--apply` and `--backup` performs a no-write scan with the same resources. Review its JSON/stderr if you want to assess coverage before applying:

- `discovered` counts distinct expected positions from readable supported pieces. Position categories such as eligible, occupied and structurally_ambiguous describe those positions.
- Unsupported/ambiguous pieces and `unreadable_regions` are separate discovery gaps, not additional recovered containers. `unreadable_target_positions` counts discovered positions whose target region cannot safely be consumed; those positions are skipped, not eligible or recovered. A partially readable world is not certified consistent.
- A repeat apply with another new backup directory should report applied=0 for unchanged inputs.
- A two-UUID trial can check independent loot, A-empty/B-remaining after draining A, then persistence of slots/items/components after a clean restart. Also compare occupied/ordinary storage and player data. A marker alone does not prove gameplay recovery. Real Java/Bedrock access needs separate verification before claiming client compatibility.

## Source comparison

Inspected ChestShare+ [restore-empty-structures](https://github.com/PsycloneTM/ChestShare-plus/blob/3603bfc5fc721177225f7fd707d3c92955dad03d/src/main/java/dev/chestshare/StructureContainerRestorer.java), [adopt-structure](https://github.com/PsycloneTM/ChestShare-plus/blob/3603bfc5fc721177225f7fd707d3c92955dad03d/src/main/java/dev/chestshare/command/ChestShareCommands.java), FingerprintRegistry and ContainerRegistrar at that frozen revision. Its [MIT LICENSE](https://github.com/PsycloneTM/ChestShare-plus/blob/3603bfc5fc721177225f7fd707d3c92955dad03d/LICENSE) credits Copyright (c) 2026 Calamech and identifies the PsycloneTM fork. Passive matching uses an exact template position, block identity and empty/no-table state; it does not require historical continuity. Its jigsaw-only/Mirror.NONE matching does not establish shipwreck support. Its registrar clears inventory/table state and adoption can replace private entries; none of that replacement behavior is used here. This independently written utility borrows the matching idea, not source code or ChestShare saved-data machinery.

## Proof and remaining work

The [recovery evidence](verification.md#historical-loot-recovery) distinguishes real-engine proof from synthetic parser/guard tests. The generated-world proof is not a Broadwater coverage estimate or authenticated human/Bedrock test. A separately authorized clean stopped Broadwater copy and its resource set are needed to measure actual coverage. No live world or backup has been accessed, and no cutover is authorized. [Issue #56](https://github.com/vice-magus-faolan/cobbled-horizon/issues/56) tracks that remaining operation; source delivery does not auto-close it.
