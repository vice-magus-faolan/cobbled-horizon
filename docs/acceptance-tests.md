# Acceptance tests

Run these against a disposable world to establish the outstanding assurance for the deployed 26.3 pack and again after every mod or loader update.

Published `v26.3.0.1.4` passed the bounded hosted native assertions described below; Jimmy's November 19, 2026 DatHost deployment report is separate, owner-reported evidence. Neither establishes real-client, host-network, gameplay/worldgen/performance or full/differential restore acceptance. See the [dated evidence](verification.md#current-263-evidence). The unchecked lists remain designated-host acceptance, not conditions for the deployment that already happened or a claim that the overlapping CI assertions have never run; historical 26.2 results do not certify this version.

All Minecraft server startup, world-generation, and gameplay tests must run on the designated, adequately resourced Minecraft test host. A control/orchestration machine may perform static validation and export only.

## Automated gates

```bash
make test
make validate
make export check-metadata
```

Public ZIP export via `make release` additionally requires clearance for every bundled
JAR. Unresolved bundled obligations select only the validated no-JAR `.mrpack` and
`.mrpack.sha256`; the cleared set is `.mrpack`, the primary CurseForge ZIP and the
combined `.sha256`. Both tagged-release modes require successful hosted native
acceptance.

The hosted `native-acceptance` job downloads the immutable artifact ID produced by
`validate`, revalidates its exact selected files and checksum (combined in full mode,
per-mrpack in metadata mode), then materializes that very `.mrpack` into a fresh
complete server folder. Download/hash failures are fatal, never a reason to re-export.
`summary.json` records the consumed `archive_sha256`. It does not rebuild or
substitute mods. In one disposable non-root Java 25 container
at a time (4 GB heap, no published ports), the first boot permits public dependency
bootstrap and the second runs offline. It checks Minecraft readiness, MSS/Hopo and
Moog policy, fresh group creation, native import/repeat/conflict/roundtrip preservation,
effective synthetic-account permissions, no startup reapplication, and completed
all-dimension saves with zero exits. Bounded logs and `summary.json` are Actions artifacts.

## Server lifecycle

- [ ] Rehearse the stopped-server [deployment reconciliation](deployment.md#upload) on a disposable copy with a verified pack/config/world rollback backup. The active mods set matches the verified 32-project payload, including Explorify v1.6.6 but no Structory or superseded JARs. Remove the retired Lite config and set aside the two named legacy Explorify configs pending generated-schema review; preserve host settings, secrets, Floodgate key, unrelated files and rollback copies.
- [ ] Clean server reaches `Done` with no missing dependency or wrong-version error.
- [ ] A second boot succeeds using the generated world and configs.
- [ ] `stop` exits cleanly and saves all dimensions.
- [ ] No private key, refresh token, player database, world, or log enters Git.
- [ ] PvP remains enabled outside spawn, while an ordinary non-operator cannot normally break or place blocks inside the 16-block spawn-protection radius. Do not treat vanilla spawn protection as comprehensive land or mechanism protection.

## Clients and cross-play

- [ ] Unmodded Java 26.3 client joins successfully.
- [ ] Geyser `2.12.1-b1281` config migration, actual listeners and advertised addresses match the verified host allocations and [network arrangement](deployment.md#geyser-networking): UDP for NetherNet media plus TCP on the Bedrock port for built-in signaling, distinct from Java's TCP listener, or explicitly configured and verified external signaling with suitable UDP reachability. Authentication/privacy policy is unchanged; no host support or external-service approval is assumed.
- [ ] A real Bedrock client joins and reconnects through that verified arrangement; successful UDP binding alone is not a pass.
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
- [ ] Creeper No Break prevents creeper terrain destruction while preserving entity damage and knockback. Contrast a non-creeper explosion and unrelated mob-griefing behavior; do not disable the global gamerule to manufacture a pass.
- [ ] Java and Bedrock players see persistent villager names and can trade normally; profession text may differ because the client-side enhancement is optional.
- [ ] Rehearse the pinned [Tasks controls](configuration.md#villagers-tasks-310): inspect a profession, disable just it, observe no future actions on already loaded existing villagers, restore its recorded value and observe actions resume. Test farmer breeding and butcher culling with eligible animals; player-context status works without granting helper OP.
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
- [ ] Verify Cristel loads `config/cristellib/mr_epic_structuresvillagesstandaloneedition/structure_placement_config.json5` without discovery/schema errors and applies only `epic:villages`: spacing `80`, separation `22`, salt `50387312`, frequency `1.0`. Confirm existing auto-config, Towns and Towers and Moog policies remain intact.
- [ ] Within Minecraft 26.3, compare fixed-seed fresh-chunk routes with Epic's shipped `40`/`11` baseline and tuned `80`/`22` policy; record Epic counts, nearby settlements, terrain fit and generation cost. The 75% reduction concerns Epic candidate-grid positions per area, not guaranteed settlement counts or cross-mod separation. Existing chunks must remain unchanged.
- [ ] Locate Epic Standalone's plains, taiga, snowy, desert, and savanna villages in newly generated chunks; inspect terrain joins and villager access to beds and workstations.
- [ ] Confirm vanilla villages and Towns and Towers settlements still generate alongside Epic towns; inspect settlement density, overlap, and loot progression.
- [ ] Test trading, containers, and village traversal with unmodded Java and Bedrock clients in Epic towns.
- [ ] Compare chunk-generation cost and occupied-settlement tick time against the baseline without Epic Standalone using the same seed and test area.
- [ ] Inspect several Explorify structures in fresh chunks on Java and Bedrock; check terrain joins, loot, density and overlap with the other selected packs. Review generated configs against packaged defaults and the retained 26.2 placement intent without transplanting unverified legacy schemas.
- [ ] Locate and generate Explorify's Nether Black Spiral on a disposable world; measure generation stalls and tick cost alongside other Nether structures before pre-generation. Keep it enabled during acceptance; older upstream reports are neither a current-runtime failure nor a verified fix.
- [ ] MSS and Hopo configs load without missing-set recovery or new `-had-error` files. MSS retains 28 placement sets, all 35 structures/eight tree variants and nine packaged `0.6` frequencies; Hopo retains poplar and sulfur members under the correct set. Native/generated values match the shipped controls; Moog namespace migration retains MSS `0.25` and MOS `0.111111`, independent of placement-level frequencies.
- [ ] Inspect Hopo mineshafts at different depths.
- [ ] Locate and enter standalone DnT 3.0.1 (`hNKbQ85c`) strongholds; verify Eyes of Ender/locate behavior, functional portal access, surface rooms, trades, loot (including vanilla-enchanted items) and progression on Java and Bedrock. The [historical static absence of custom enchantment registry definitions](configuration.md#structure-generation) does not satisfy these checks. Measure first-generation stalls and generation cost before pre-generation; do not assume Lite's balance or config applies.
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
- [ ] Rehearse the native [one-time group import](permissions.md#one-time-group-import) from the supplied gzip using file access and console only. Native export/readback shows only the intended policy changes; unrelated group/user data, memberships, custom/contextual nodes and backend remain preserved. Contrast a pre-existing conflicting node, repeat the import deliberately and record actual merge behavior; there is no startup reapplication. Keep synthetic identities/private exports out of the pack.
- [ ] LuckPerms contains the intended default, helper, and owner groups; only the owner is present in `ops.json`.
- [ ] Ordinary and helper accounts cannot run `/sswaystones`, Chunky operations, creative-mode commands, or JEB commands.
- [ ] The owner can run the required administrative commands without a wildcard LuckPerms grant.
- [ ] Confirm the pinned JEB legacy flags migrate only when `automaticSchedule` is absent, not as a master disable for the shipped schedule. Console `jeb list` lists archives separately from schedule status; verify successful completion and recovery independently.
- [ ] `/jeb next` reports the 24-hour full and three-hour differential intervals.
- [ ] Startup and config reload reset the timers as expected; the host's full-backup procedure still completes across scheduled restarts.
- [ ] The initial full backup completes and is recorded before players are admitted.
- [ ] The daily full-backup operation has an assigned schedule, responsible operator, completion check, and failure notification.
- [ ] Scheduled restarts wait for full-backup completion; failed or overdue backups produce an alert.
- [ ] JEB creates a named full backup and a later differential backup without save errors.
- [ ] JEB backup and restore commands require permission level 4 and are available only to the owner operator or authenticated server console.
- [ ] JEB skips inactive intervals when no player has been online.
- [ ] Retention never exceeds 6,144 MB and a low-space preflight fails without filling the filesystem.
- [ ] The named full backup is cold-restored into a separate disposable instance using the exact pack commit.
- [ ] A differential backup is restored with its base full archive into a fresh disposable instance; changes made after the full backup are present.
- [ ] Java and Bedrock login, representative chunks, inventory, and a clean shutdown pass after restoration.
- [ ] The restore result is recorded in `docs/verification.md`; archive creation alone is not a pass.
- [ ] The selected host's independent daily backup layer is enabled; schedule, responsible operator, retention, quota accounting, world/config/key scope and off-host access are confirmed, and restoration is tested. Advertised provider backups do not substitute for either JEB restore drill. Resolve the [outstanding provider questions](providers/dathost.md) against the actual DatHost account.

Ledger is not a launch test because it is not active. If it is later promoted, add tests for database loss/latency, bounded queue shutdown, purge, inspect, rollback, permissions, and database-aware restoration before deployment.
