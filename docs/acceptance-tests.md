# Acceptance tests

Run these against a disposable world before production and again after every mod or loader update.

All Minecraft server startup, world-generation, and gameplay tests must run on the designated, adequately resourced Minecraft test host. A control/orchestration machine may perform static validation and export only.

## Automated gates

```bash
make test
make validate
make export
python3 scripts/validate_mrpack.py dist/cobbled-horizon-26.2.0.1.0.mrpack --minecraft 26.2
```

## Server lifecycle

- [ ] Clean server reaches `Done` with no missing dependency or wrong-version error.
- [ ] A second boot succeeds using the generated world and configs.
- [ ] `stop` exits cleanly and saves all dimensions.
- [ ] No private key, refresh token, player database, world, or log enters Git.
- [ ] PvP remains enabled outside spawn, while an ordinary non-operator cannot normally break or place blocks inside the 16-block spawn-protection radius. Do not treat vanilla spawn protection as comprehensive land or mechanism protection.

## Clients and cross-play

- [ ] Unmodded Java 26.2 client joins successfully.
- [ ] Bedrock client joins through the assigned Geyser UDP port.
- [ ] Floodgate player reconnects with the same identity and inventory.
- [ ] `online-mode=true` and `enforce-secure-profile=false` are applied on the host; both Java and Bedrock players can send and receive chat.
- [ ] Java and Bedrock chat, inventory, doors, boats, and combat behave acceptably.

## Quality of life

- [ ] Ordinary players can place waystones but cannot create global, team, or server-owned waystones or use `/sswaystones` administration.
- [ ] The owner can create a server-owned waystone; it is visible and usable from both Java and Bedrock and ordinary players cannot break it.
- [ ] Same-dimension travel costs two XP levels on both clients.
- [ ] Player and mob attacks both prevent opening a waystone for 30 seconds.
- [ ] Each player can create ten player-owned waystones; an eleventh is rejected, while server-owned waystones do not consume that allowance.
- [ ] A player-owned waystone is initially known only to its owner, but another player can discover it by physically interacting with it. Record this as a limitation rather than claiming strict privacy.
- [ ] A survival player cannot pay the configured `2147483647`-level cross-dimension cost. Confirm that creative owner bypass still exists and do not describe this as a hard mod-level disable.
- [ ] Java and Bedrock players can see, open, and completely recover a grave.
- [ ] Grave XP recovery and real-time expiry match policy.
- [ ] Creepers damage entities without breaking blocks; unrelated mob behavior remains normal.
- [ ] Java and Bedrock players see persistent villager names and can trade normally; profession text may differ because the client-side enhancement is optional.
- [ ] Each Villagers Tasks profession action uses only vanilla-visible entities, items, particles, inventories, and sounds on both Java and Bedrock clients.
- [ ] Villagers Tasks culling, breeding, healing, resource generation, fishing, and shearing rates are acceptable for balance and occupied-village tick cost.
- [ ] On unmodded Java and Bedrock clients, vanilla trim materials and patterns render correctly on representative naturally equipped mobs, generated loot, and level-three-or-higher trade equipment.
- [ ] Naturally Trimmed does not create or duplicate smithing templates, and observed mob, loot, and trade frequencies remain uncommon enough to preserve discovery.
- [ ] During rain, directly exposed crops receive occasional extra growth while covered crops do not; normal growth remains unchanged when weather is clear.
- [ ] Bamboo receives no extra rain growth, and the tuned crop, sapling, sugar cane, berry, melon, and pumpkin rates feel useful without trivializing farming.
- [ ] Java and Bedrock players interact normally with every affected crop, and a large loaded farm shows acceptable storm-time tick cost in spark.

## World generation

Use disposable seeds and `/locate structure` where available.

- [ ] Inspect several Towns and Towers structures.
- [ ] Locate Epic Standalone's plains, taiga, snowy, desert, and savanna villages in newly generated chunks; inspect terrain joins and villager access to beds and workstations.
- [ ] Confirm vanilla villages and Towns and Towers settlements still generate alongside Epic towns; inspect settlement density, overlap, and loot progression.
- [ ] Test trading, containers, and village traversal with unmodded Java and Bedrock clients in Epic towns.
- [ ] Compare chunk-generation cost and occupied-settlement tick time against the baseline without Epic Standalone using the same seed and test area.
- [ ] Inspect several Explorify structures, including campsite-like structures.
- [ ] Inspect Hopo mineshafts at different depths.
- [ ] Locate and enter a DnT Lite stronghold; verify portal and loot progression.
- [ ] Inspect several Moog floating structures and confirm rarity feels intentional.
- [ ] Locate several MOS structures in newly generated ordinary, deep, warm, and cold ocean chunks; include seafloor ruins and surface ships or rafts.
- [ ] On both unmodded Java and Bedrock, inspect MOS blocks and entities, open every encountered container type, and verify loot and hostile encounters remain usable and balanced.
- [ ] Sail through a repeatable test route and confirm `mos = 3.0` produces worthwhile discoveries without crowding vanilla shipwrecks, Towns and Towers fleets, or the horizon.
- [ ] If ScalableLux is promoted, generate chunks under load and inspect lighting and relighting behavior.
- [ ] If Spiral Tower Villages is promoted, inspect proximity to Epic towns, reward frequency, books, and hidden redstone mechanisms with Alternate Current on both clients.

Do not run final Chunky pre-generation until this section passes and the seed is accepted.

## Operations

- [ ] spark profile captures idle and active baselines.
- [ ] squaremap renders only the Overworld and uses the assigned HTTP endpoint; its public tracker visibly reports player position, health, and armor as intentionally configured.
- [ ] LuckPerms contains the intended default, helper, and owner groups; only the owner is present in `ops.json`.
- [ ] Ordinary and helper accounts cannot run `/sswaystones`, Chunky operations, creative-mode commands, or JEB commands.
- [ ] The owner can run the required administrative commands without a wildcard LuckPerms grant.
- [ ] `/jeb next` reports the 24-hour full and three-hour differential intervals.
- [ ] Startup and config reload reset the timers as expected; the host's full-backup procedure still completes across scheduled restarts.
- [ ] The initial full backup completes and is recorded before players are admitted.
- [ ] The daily full-backup operation has an assigned schedule, responsible operator, completion check, and failure notification.
- [ ] Scheduled restarts wait for full-backup completion; failed or overdue backups produce an alert.
- [ ] JEB creates a named full backup and a later differential backup without save errors.
- [ ] JEB backup and restore commands require permission level 4 and are available only to the owner operator or DatHost console.
- [ ] JEB skips inactive intervals when no player has been online.
- [ ] Retention never exceeds 6,144 MB and a low-space preflight fails without filling the filesystem.
- [ ] The named full backup is cold-restored into a separate disposable instance using the exact pack commit.
- [ ] A differential backup is restored with its base full archive into a fresh disposable instance; changes made after the full backup are present.
- [ ] Java and Bedrock login, representative chunks, inventory, and a clean shutdown pass after restoration.
- [ ] The restore result is recorded in `docs/verification.md`; archive creation alone is not a pass.
- [ ] DatHost's daily-backup retention, quota accounting, and restore scope are confirmed.

Ledger is not a launch test because it is not active. If it is later promoted, add tests for database loss/latency, bounded queue shutdown, purge, inspect, rollback, permissions, and database-aware restoration before deployment.
