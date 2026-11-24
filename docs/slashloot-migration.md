# Broadwater: one-time historical loot migration

`scripts/recover_structure_loot.py` scans a **stopped Minecraft 26.3 world copy** and restores pending loot-table metadata on compatible empty structure containers. Ordinary unmodified SlashLoot then supplies per-player loot. This is an optional operator tool, not an installation hook, permanent mod dependency, terrain reset or permission to access Broadwater. Normal new worlds do not need it.

## Eligibility and coverage

One world-level migration approval is sufficient. An expected structure/template position, identified available loot table and compatible empty unmanaged container qualify. No per-chest manifest, continuity witness or original seed is required. An empty player replacement at the expected position can qualify; that risk and new entitlements for previous looters are accepted. Concrete inventory, layout or metadata conflicts still cause individual skips.

The scanner reads stored structure pieces rather than sweeping every empty chest. It supports native shipwreck marker-to-chest positions with their stored origin, rotation and pivot. The same template extraction supports rigid single/legacy-single jigsaw pieces with empty processor lists and baked chest/barrel tables. Multiple palettes qualify only when their container/table claims agree. Resource conflicts are never resolved by guessing datapack order.

Occupied containers, double/composite chests, incompatible/missing blocks, custom components or unexplained metadata, conflicting tables and existing private claims are not overwritten. Existing matching tables are left alone, including unopened containers. Unsupported piece types, non-rigid or processed jigsaws, missing templates, differing palettes and unknown tables stay outside supported coverage. The tool does not reconstruct procedural dungeons/mineshafts, donor terrain or every modded structure. Its summary is a measured supported subset, not a world-wide loot total.

New seeds are the first eight SHA-256 bytes, interpreted as signed big-endian, of compact JSON `["slashloot-recovery-v1", dimension-relative-directory, [x,y,z], table]`. This is deterministic per location within that world layout, not recovery of vanished historical randomness. It avoids using a common zero seed for every source. SlashLoot combines that seed with the player UUID. No private loot or prior-player records are inserted.

## Operator procedure

Use Linux/POSIX, Python 3.11 or later, sufficient disk for region backups plus rewritten regions, and matching trusted server/mod/datapack resources. The inner vanilla server JAR is normally `versions/26.3/server-26.3.jar`, not the outer launcher. Include relevant mod JARs and datapack ZIPs/directories through repeated `--resources` arguments. Do not omit an active override and then claim the result represents that resource set.

1. Approve the migration for the named world. Cleanly stop the server and keep other tools/players out. Take a complete consistent snapshot of all world/dimension, player, private-mod state and configuration files. Rehearse restoration separately; the utility backups cover only changed region files.
2. Work on an independently owned copy first. Install the optional tooling dependency in a dedicated environment. Neither these dependencies nor this script are exported in the pack:

   ```sh
   python3 -m venv ../recovery-venv
   ../recovery-venv/bin/python -m pip install -r scripts/requirements-recovery.txt
   ../recovery-venv/bin/python scripts/recover_structure_loot.py /copies/world --resources /server/versions/26.3/server-26.3.jar --resources /server/mods/structures.jar
   ```

3. Review the JSON counts and stderr warnings. `discovered` counts distinct expected positions from supported pieces; eligible/occupied/structurally_ambiguous/unknown_table and additional exclusion categories describe those positions. Unsupported/ambiguous pieces and unreadable regions are separate coverage gaps, not additional recovered containers. Resolve or consciously exclude gaps before operation; never call a partially readable world consistent.
4. Apply using the same resources and a **new backup directory outside the world**:

   ```sh
   ../recovery-venv/bin/python scripts/recover_structure_loot.py /copies/world --resources /server/versions/26.3/server-26.3.jar --resources /server/mods/structures.jar --apply --backup /recovery/regions-before-first-apply
   ```

   The script holds the native POSIX session lock, rereads current inventories, backs up each changed region, then atomically replaces that region. It adds only `LootTable` and `LootTableSeed`; it never clears Items, replaces blocks, rewrites player files or creates private claims. Unchanged chunk sectors remain verbatim. A second apply with another new backup directory must report applied=0 for unchanged inputs.
5. Start the copy with the exact selected unmodified SlashLoot and its ordinary defaults. Use two distinct UUIDs to open a recovered source normally. Drain A, require independent loot for B, repeat, then cleanly stop/restart and compare A-empty and B remaining slots/items/components. Check occupied and ordinary storage and player data. A marker alone is not successful recovery. Validate real Java/Bedrock access separately before claiming client compatibility.

No region is repaired by this tool. Invalid length/allocation/compression is rejected; unreadable discovery regions are reported and skipped. An error during application can leave earlier regions applied. Keep the server stopped, inspect the retained backups/results and either resume unchanged eligible sources or restore the complete snapshot. Region replacement is atomic, not an all-world transaction or power-loss guarantee. Never remove private claims to make a rerun eligible.

Before any claim, the backed-up regions can restore the pre-apply metadata while stopped. After loot moves into player inventories, use the consistent full snapshot: restoring only regions or only the private ledger can duplicate or lose items. Existing [accepted private-inventory destruction loss](slashloot.md#retention-removal-and-administration) and the separate mixed-double limitations remain unchanged.

## Source comparison

Inspected ChestShare+ [restore-empty-structures](https://github.com/PsycloneTM/ChestShare-plus/blob/3603bfc5fc721177225f7fd707d3c92955dad03d/src/main/java/dev/chestshare/StructureContainerRestorer.java), [adopt-structure](https://github.com/PsycloneTM/ChestShare-plus/blob/3603bfc5fc721177225f7fd707d3c92955dad03d/src/main/java/dev/chestshare/command/ChestShareCommands.java), FingerprintRegistry and ContainerRegistrar at that frozen revision. Its [MIT LICENSE](https://github.com/PsycloneTM/ChestShare-plus/blob/3603bfc5fc721177225f7fd707d3c92955dad03d/LICENSE) credits Copyright (c) 2026 Calamech and identifies the PsycloneTM fork. Passive matching uses an exact template position, block identity and empty/no-table state; it does not require historical continuity. Its jigsaw-only/Mirror.NONE matching does not establish shipwreck support. Its registrar clears inventory/table state and adoption can replace private entries; none of that replacement behavior is used here. This independently written utility borrows the matching idea, not source code or ChestShare saved-data machinery.

## Proof and remaining work

The [recovery evidence](verification.md#historical-loot-recovery) distinguishes real-engine proof from synthetic parser/guard tests. The generated-world proof is not a Broadwater coverage estimate or authenticated human/Bedrock test. A separately authorized clean stopped Broadwater copy and its resource set are needed to measure actual coverage. No live world or backup has been accessed, and no cutover is authorized. [Issue #56](https://github.com/vice-magus-faolan/cobbled-horizon/issues/56) tracks that remaining operation; source delivery does not auto-close it.
