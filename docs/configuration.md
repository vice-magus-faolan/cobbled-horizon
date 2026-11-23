# Configuration decisions

The retained overrides originated in a historical Minecraft 26.2 server boot and were then changed deliberately. The 26.3 pack does not ship legacy Explorify overrides or the retired Lite override. A server upgraded from 26.2 may still have the old files. Remove or set them aside as described in the [deployment runbook](deployment.md#upload). Retained values are policy inputs, not proof that every updated mod accepts its schema. See the [deployment report](verification.md#current-deployment). The [verification record](verification.md#current-263-evidence) distinguishes successful hosted config assertions from outstanding real-host checks. Restored Explorify uses packaged defaults pending generated-config review. Naturally Trimmed and Crops Love Rain were added from their documented schemas after that runtime capture. Avoid regenerating overrides blindly; review diffs when mods update their schemas. Villager Names and Collective were also added after the original runtime capture, so any configuration they generate must still be reviewed on the designated test host. Villagers Tasks exposes per-profession scoreboard controls rather than a standalone configuration file.

## Geyser and Floodgate

`config/Geyser-Fabric/config.yml` uses `auth-type: floodgate`, disables IP-address logging and metrics, and supplies Cobbled Horizon display text.

Outstanding Geyser/Floodgate checks for this pack, and safeguards for subsequent host changes:

1. Verify the exact-build [Geyser network arrangement](deployment.md#geyser-networking): suitable UDP reachability and either TCP on the Bedrock port for built-in signaling, distinct from Java's TCP listener, or an explicitly configured and verified external signaling service. Use verified host allocations, not an assumed `19132` UDP-only setup.
2. Leave `online-mode=true` in `server.properties`.
3. Set `enforce-secure-profile=false` so Bedrock players can chat. See [Geyser's secure-chat documentation](https://geysermc.org/wiki/geyser/secure-chat/).
4. Preserve an existing `config/floodgate/key.pem`; let Floodgate generate it only for a new instance.
5. Never copy or commit that private key.
6. Test login and chat with both Java and Bedrock clients.

The included Floodgate configuration permits optional account linking but does not require it.

The exact 26.3 Geyser pin `2.12.1-b1281` remains beta in this pack. Schema migration, actual listeners and advertised addresses, signaling, login, chat and identity with real Java/Bedrock clients remain outstanding checks; earlier cross-play evidence does not establish them for this version. Retain the existing authentication/privacy policy. Follow the linked network procedure without silently enabling an external service or assuming host support.

## Server access and world interaction

`server.properties.example` retains PvP and protects the default 16-block radius around world spawn. The whitelist is an identity gate, not land or container protection: ordinary members can still alter blocks and containers outside spawn. Only the owner should be an operator. Helpers inherit ordinary-player permissions without operator status; the baseline grants no helper-specific nodes, and future support capabilities must be granted individually. See [`permissions.md`](permissions.md).

## Server-Side Waystones

The checked-in config charges two XP levels for same-dimension travel, applies a 30-second combat lock after both player and mob attacks, and limits each player to ten player-owned waystones. Server-owned waystones do not count against that limit.

LuckPerms allows ordinary players to place waystones while reserving global and server-owned waystones for the owner. Server-owned waystones are visible to everyone. Player-owned waystones are initially known only to their owner, but they are discoverable: another player who physically finds and interacts with one can subsequently teleport to it. Version 1.3.2 has no strict owner-only access flag.

Version 1.3.2 also has no true cross-dimensional disable option. `cross_dimension_xp_cost` is set to the maximum signed integer (`2147483647`), making cross-dimension travel infeasible for survival players. Creative players pay no XP and can bypass this, so the setting is an effective survival policy rather than a hard technical prohibition. Creative mode remains owner-only.

## Universal Graves

- Non-owner protection: one real-time hour
- Expiration: 24 real-time hours
- XP restored: 75%
- Items drop when a grave expires

The generous expiry limits loss from outages or cross-play UI trouble while preserving a meaningful XP penalty. Bedrock checks of the grave model and inventory interface remain outstanding.

## Naturally Trimmed

Naturally Trimmed is server-only in the pack and is constrained to vanilla trim materials and patterns. Found trimmed equipment does not grant or duplicate smithing templates; the mod changes generated equipment rather than adding a template extraction path.

The baseline keeps the effect uncommon: 75% of eligible mobs receive no trims, then each equipped armor piece has a 35% chance. Generated loot uses a 15% chance and level-three-or-higher trades use 10%. Dedicated servers cannot validate client trim textures, so `texture_validation_filtering` is disabled and `vanilla_only` provides the enforceable boundary. Verify representative mob, loot, and trade trims on both unmodded Java and Bedrock clients.

## Crops Love Rain

Crops Love Rain adds one extra growth-stage opportunity during an applicable random tick while it is raining; its numeric values are chance denominators, not speed multipliers. Directly exposed ordinary crops and cocoa use `10` (a 1-in-10 chance), while saplings, sugar cane, sweet berries, melons, and pumpkins use `15` (a 1-in-15 chance).

Bamboo's value is `0` because the exact mod checks global rain for bamboo instead of rain exposure at the plant. Regular growth remains enabled, and debug logging is disabled. Forge Config API Port is included only as the required configuration dependency. Exposed-versus-covered behavior and storm-time tick cost remain outstanding checks.

## ServerCore

Gameplay-affecting features in `config.yml` remain disabled. All entries in `optimizations.yml` that declare imperfect vanilla parity are also disabled initially. Enable them only after a spark profile and targeted regression test justify the change.

## Polymer

`config/polymer/resource-pack.json` does not import `world/resources.zip`. This prevents an untracked, mutable world file from silently entering the generated Polymer resource pack. Any future custom resource pack should be reviewed and committed through an explicit source path.

## Staged performance candidates

Krypton, Fast Noise with ZConfig, and ScalableLux are not part of the baseline export. Their pinned metadata lives under `staged/mods/`; Fast Noise and ScalableLux configuration lives under `staged/config/`. Promote them only after the activation gates in `candidates.toml` pass.

## Just Enough Backups

`config/justenoughbackups.json` enables full backups at 24-hour intervals and differential backups at three-hour intervals after player activity. In pinned JEB 1.2.0.10+26.3, [`BackupConfig.normalize()`](https://github.com/frandm16/JustEnoughBackups/blob/1da38a569dcafda9cd5a0f3c2c48e443a9fcab59/src/main/java/com/frandm/justenoughbackups/config/BackupConfig.java#L190-L209) reads legacy `automaticBackupsEnabled` and `automaticIntervalMinutes` only when `automaticSchedule` is absent. Our schedule is present: its per-type `enabled`/interval values govern, and the legacy `false` does not disable it. Do not flip that field to repair an already enabled schedule.

From the authenticated server console, `jeb next` reports enabled schedules and `jeb list` lists available archives (use `/jeb next` and `/jeb list` in-game as the owner). Neither proves a completed backup or successful restoration. Ordinary world autosaves update the working world; a completed archive is a separate recovery point, and only a separate-instance restore drill establishes recoverability.

The previously inspected JEB 1.2.0.6 resets timers at startup and config reload. Keep the conservative restart procedure and verify timing on this exact 1.2.0.10+26.3 runtime; the full-backup interval is not a calendar-day guarantee. Static schedule/source inspection does not complete the pending runtime and restore checks.

Partial, startup, and shutdown backups remain disabled. The operating procedure requires an initial full backup and explicit full backups coordinated with host restarts. See [Create full backups across restarts](storage-and-recovery.md#create-full-backups-across-restarts).

JEB's command permission level is `4`, reserving backup and restore commands for the owner operator or authenticated server console. Helpers are deliberately not operators.

Retention requests two full backups and sixteen differential backups, subject to their dependency chains and the 6,144 MB per-world cap. JEB preserves an 8,192 MB minimum free-space reserve. Strict integrity checking and two worker threads limit backup load.

These are safety limits, not proof that recovery works. The separate-instance cold-restore drill in [`storage-and-recovery.md`](storage-and-recovery.md) remains outstanding evidence for this pack.

## Ledger (future only)

Ledger is not present in `mods/` or the standard export. Its proposed deployment uses a finite 30-day retention window and a verified, separately budgeted MySQL service, with credentials injected only on the deployment host. Promotion also requires least-privilege permissions, database-aware backups, growth monitoring, and database-outage tests. See [`storage-and-recovery.md`](storage-and-recovery.md) for the proposed configuration and gates; the current provider's advertised MySQL offering and outstanding account checks are recorded in the [DatHost profile](providers/dathost.md).

## Structure generation

- Towns and Towers retains its Cristel Lib overrides. Hopo 1.3.8 retains default placement and all enabled members, now including explicit `mineshaft/poplar_mineshaft` and `mineshaft/biomes/sulfur_mineshaft` controls under `mineshafts`. MSS 2.2.0 uses 28 placement sets and 35 enabled structures: `trees` groups all eight tree variants, with its packaged spacing `58`, separation `29`, salt `731846205` and placement frequency `0.6`. Eight other sets also retain packaged `0.6` frequency; omitted frequencies retain the native default. The large raw jungle/mushroom salts are decoded to signed 32-bit integers by the pinned loader, not copied as overflowing values. Generic Cristel Lib settings and its Towns and Towers waystone patch remain unchanged. Confirm no missing-set recovery or new `-had-error` files on the disposable instance; this does not certify density or generation cost.
- Explorify v1.6.6 replaces interim Structory; Formations is not installed. All 14 packaged placement sets match the former 26.2 placement policy, with structures enabled, so no density override is needed. Fabric API is required; Cristel Lib is optional for Explorify and remains required by Towns and Towers. The legacy `config/cristellib/explorify/structure_placement_config.json5` and `config/cristellib/explorify/structure_toggle_config.json5` are not shipped because their current schema is unverified, not because Explorify is absent. During stopped-server [deployment reconciliation](deployment.md#upload), preserve rollback copies and set aside only these legacy active-host copies before reviewing freshly generated configs against the intended defaults. Do not copy old schemas blindly. Black Spiral remains enabled; measure Nether generation stalls and tick cost explicitly. Older upstream performance reports do not establish a defect or fix on this exact Fabric runtime.
- Standalone Dungeons and Taverns Stronghold Overhaul 3.0.1 (`hNKbQ85c`) replaces retired Lite. The obsolete Lite-only file is `config/cristellib/mr_dnt_strongholdoverhaulliteedition/structure_toggle_config.json5`; remove only its active-host copy through the same reconciliation procedure, and do not copy it to the replacement namespace. This standalone pack replaces vanilla stronghold generation; it is not equivalent to Lite and is not the broad DnT collection. The [October 6, 2026 exact-archive investigation in issue #1](https://github.com/vice-magus-faolan/cobbled-horizon/issues/1) found no custom enchantment registry definitions in this exact version. That finding does not rule out vanilla-enchanted loot or prove progression, balance or cross-play compatibility. Upstream artifact notes warn about a first-generation freeze: generation-stall measurements and checks of Eyes of Ender, portals, loot (including vanilla enchantments), trades and Java/Bedrock interactions remain outstanding and are required before Chunky pre-generation.
- Moog's Structure Lib 3.4.2 keeps the checked-in legacy spacing inputs unchanged: universal `1.0`, Soaring Structures `mss = 2.0`, Ocean Structures `mos = 3.0`. Its supported migration computes `frequency = 1 / spacing²`: MSS becomes `0.25`, MOS becomes `0.111111` after formatting. These namespace rarity controls are distinct from individual placement frequencies such as MSS trees' `0.6`; never copy `2` or `3` into frequency fields. Adding another Moog pack will not silently inherit either namespace setting.
- MOS 1.1.1 supplies vanilla-block ocean ruins, wrecks, ships, temples, rafts, and seafloor oddities. Its static server-only packaging is favorable for unmodded Java and Geyser, but structure visibility, entities, containers, loot, density, and overlap with Towns and Towers remain runtime acceptance items on both Java and Bedrock.
- Epic Structures: Villages Standalone Edition 1.0.0 adds five village styles without replacing vanilla village templates. The unchanged JAR ships one `epic:villages` structure set at spacing `40` and separation `11`. The pack overrides only that set to spacing `80` and separation `22` chunks, retaining salt `50387312` and neutral frequency `1.0`. Doubling spacing means 75% fewer Epic candidate-grid positions per area, not a measured reduction in generated settlements or all structures. Biome and terrain checks still apply; there is no cross-mod exclusion zone or guaranteed separation from vanilla villages, Towns and Towers or other settlements.
- Epic's override is `config/cristellib/mr_epic_structuresvillagesstandaloneedition/structure_placement_config.json5`, containing only the fully qualified key `epic:villages`. Cristel's existing automatic configuration uses the owning Fabric loader ID for the directory, not the worldgen namespace `epic`. Its automatic filename is `structure_placement_config.json5`, not the separate BuiltInAPI name `placement_structure_config`. The JSON5 file deliberately uses plain JSON syntax for dependency-free policy tests. Existing auto-config settings, Cristel pins, village styles/weights and other structure policies are unchanged. Static library/artifact inspection supports this mechanism; actual config loading and fresh-chunk generation on the designated test host remain outstanding checks.
- Structure generation changes affect newly generated chunks; they do not rewrite existing structures. Standalone DnT's data can also change progression outside generation. Test on a disposable world copy, preserve a full rollback snapshot, review newly generated configs, and freeze the approved composition before Chunky pre-generation. No live-world migration is established by this source update.

Spiral Tower Villages 0.0.3 is staged with no configuration override. Its exclusion zones reference the vanilla village set, not `epic:villages`. Promotion requires checking proximity to Epic towns, loot balance, and hidden redstone mechanisms with Alternate Current.

CTOV remains future-only, behind Spiral Tower Villages. Its evaluated Fabric 4.1.0 JAR requires Lithostitched even though that release's Modrinth dependency list omits it. Neither CTOV nor Lithostitched is included in the active or staged pack metadata.

## SlashLoot

No SlashLoot config override is shipped. The pinned mod generates upstream defaults: enabled once-per-player pending-table loot, pot instancing and break/entity/background orphan-record cleanup on, unknown containers off. Existing host overrides are not reset. This does not recover unpacked historical loot or export private inventories. Read the [default policy and lifecycle limits](slashloot.md) before any separately approved installation. Standalone no-table storage is excluded by the inspected eligibility path, but a tableless half joined to an eligible loot chest has an unresolved [mixed-double preservation limitation and activation gate](slashloot.md#mixed-double-chests-unresolved-preservation-gate). Do not treat ordinary-storage preservation as verified.

## squaremap

The checked-in `squaremap/config.yml`:

- disables Nether and End maps
- lowers maximum/default/extra zoom
- enables image compression
- reduces background chunks processed per interval
- retains the public live player tracker, including player location, health, armor, and externally fetched player-head images

The live tracker is an explicit friends-and-family policy choice, not an access control. Anyone who can reach the map endpoint can see this information; squaremap provides no built-in login boundary for this configuration. `web-address` and the internal web-server port remain deployment placeholders. Confirm an HTTP port or supported proxy with the selected host before public exposure. Avoid a full pre-generated public render if undiscovered geography is meant to remain part of exploration.

## Chunky

The repository does not automatically pre-generate a world. After the seed and all world-generation files are frozen, use Chunky to generate the intended Overworld radius and then capture a spark baseline.

## Villagers Tasks (3.1.0)

This pin has no standalone config file. Its `data/villagers_tasks/function/load.mcfunction` initializes twelve per-profession flags in `v_tasks.cfg` to `1` only if they are not already `0` or `1`; reload preserves valid choices. `tick_jobs.mcfunction` gates jobs on those flags. Defaults remain enabled in this pack; changing gameplay policy is an explicit operator decision.

Use the authenticated console to inspect, disable and re-enable just the butcher job (no leading slash in console):

```text
scoreboard players get #butcher v_tasks.cfg
scoreboard players set #butcher v_tasks.cfg 0
scoreboard players get #butcher v_tasks.cfg
scoreboard players set #butcher v_tasks.cfg 1
scoreboard players get #butcher v_tasks.cfg
```

`0` disables and `1` enables that profession across the world, not one villager. Substitute `farmer`, `cleric`, `mason`, `fisherman`, `shepherd`, `nitwit`, `weaponsmith`, `toolsmith`, `librarian`, `cartographer` or `leatherworker` for `butcher`. Keep the `#` prefix. Restore the recorded original value after a test instead of enabling a job that was deliberately disabled.

For the human-readable status, an owner player can run `/function villagers_tasks:menu/status`. Console must supply a player executor: `execute as <ONLINE_OWNER_USERNAME> run function villagers_tasks:menu/status`, because the function sends `tellraw @s` (the console is not a player). The menu apply function is a macro requiring all twelve named profession arguments, with `2` meaning keep the current value; a bare `function villagers_tasks:menu/apply` is incomplete. Direct scoreboard commands above avoid macro arguments entirely. Do not grant helpers OP or broad function/scoreboard rights to use this workflow.

The job selectors target loaded Overworld villagers by profession, with no new-spawn requirement: villagers in an existing village qualify too. Jobs normally run each 20 game ticks; per-villager timers, daytime and action conditions still apply, and unloaded chunks do not keep working. For example, farmers check nearby breed targets every 20 job cycles (about 20 seconds at 20 TPS), within 12 blocks and below 40 targets; butchers check adult targets every five cycles (about five seconds), within 12 blocks and above 50 adults. Breeding/culling can therefore change livestock around existing villages. Disabling a job stops future actions, not effects already produced. These commands/selectors are supported by the SHA-512-pinned 3.1.0 resources, not proof of live balance or Java/Bedrock behavior; the disposable balance and Java/Bedrock tests remain outstanding. Do not transplant this guidance onto the 26.2 line, which pins Tasks 1.1.3.
