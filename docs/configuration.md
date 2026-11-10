# Configuration decisions

The retained overrides originated in a historical Minecraft 26.2 server boot and were then changed deliberately. The 26.3 candidate does not ship legacy Explorify overrides or the retired Lite override; retained values are policy inputs, not proof that updated mods accept their schemas. Restored Explorify uses packaged defaults pending generated-config review. Naturally Trimmed and Crops Love Rain were added from their documented schemas after that runtime capture. Avoid regenerating overrides blindly; review diffs when mods update their schemas. Villager Names and Collective were also added after the original runtime capture, so any configuration they generate must still be reviewed on the designated test host. Villagers Tasks exposes no configuration surface.

## Geyser and Floodgate

`config/Geyser-Fabric/config.yml` uses `auth-type: floodgate`, disables IP-address logging and metrics, and supplies Cobbled Horizon display text.

Before DatHost deployment:

1. Verify the exact-build [Geyser network arrangement](deployment.md#geyser-networking): suitable UDP reachability and either TCP on the Bedrock port for built-in signaling, distinct from Java's TCP listener, or an explicitly configured and verified external signaling service. Use verified host allocations, not an assumed `19132` UDP-only setup.
2. Leave `online-mode=true` in `server.properties`.
3. Set `enforce-secure-profile=false` so Bedrock players can chat. See [Geyser's secure-chat documentation](https://geysermc.org/wiki/geyser/secure-chat/).
4. Preserve an existing `config/floodgate/key.pem`; let Floodgate generate it only for a new instance.
5. Never copy or commit that private key.
6. Test login and chat with both Java and Bedrock clients.

The included Floodgate configuration permits optional account linking but does not require it.

The exact 26.3 Geyser pin `2.12.1-b1281` is beta. Retain the existing authentication/privacy policy, but recheck schema migration, actual listeners and advertised addresses, signaling, login, chat and identity with real Java/Bedrock clients before deployment; earlier cross-play evidence does not transfer to this candidate. Follow the linked network procedure without silently enabling an external service or assuming host support.

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

The generous expiry limits loss from outages or cross-play UI trouble while preserving a meaningful XP penalty. Test the grave model and inventory interface from Bedrock before launch.

## Naturally Trimmed

Naturally Trimmed is server-only in the pack and is constrained to vanilla trim materials and patterns. Found trimmed equipment does not grant or duplicate smithing templates; the mod changes generated equipment rather than adding a template extraction path.

The baseline keeps the effect uncommon: 75% of eligible mobs receive no trims, then each equipped armor piece has a 35% chance. Generated loot uses a 15% chance and level-three-or-higher trades use 10%. Dedicated servers cannot validate client trim textures, so `texture_validation_filtering` is disabled and `vanilla_only` provides the enforceable boundary. Verify representative mob, loot, and trade trims on both unmodded Java and Bedrock clients.

## Crops Love Rain

Crops Love Rain adds one extra growth-stage opportunity during an applicable random tick while it is raining; its numeric values are chance denominators, not speed multipliers. Directly exposed ordinary crops and cocoa use `10` (a 1-in-10 chance), while saplings, sugar cane, sweet berries, melons, and pumpkins use `15` (a 1-in-15 chance).

Bamboo's value is `0` because the exact mod checks global rain for bamboo instead of rain exposure at the plant. Regular growth remains enabled, and debug logging is disabled. Forge Config API Port is included only as the required configuration dependency. Verify exposed-versus-covered behavior and storm-time tick cost before production.

## ServerCore

Gameplay-affecting features in `config.yml` remain disabled. All entries in `optimizations.yml` that declare imperfect vanilla parity are also disabled initially. Enable them only after a spark profile and targeted regression test justify the change.

## Polymer

`config/polymer/resource-pack.json` does not import `world/resources.zip`. This prevents an untracked, mutable world file from silently entering the generated Polymer resource pack. Any future custom resource pack should be reviewed and committed through an explicit source path.

## Staged performance candidates

Krypton, Fast Noise with ZConfig, and ScalableLux are not part of the baseline export. Their pinned metadata lives under `staged/mods/`; Fast Noise and ScalableLux configuration lives under `staged/config/`. Promote them only after the activation gates in `candidates.toml` pass.

## Just Enough Backups

`config/justenoughbackups.json` enables full backups at 24-hour intervals and differential backups at three-hour intervals after player activity. The previously inspected JEB 1.2.0.6 resets those timers at startup and config reload; retain the conservative restart procedure and verify it again with this candidate's 1.2.0.10+26.3. The full-backup interval is not a calendar-day guarantee. The historical `automaticBackupsEnabled` migration semantics must also be rechecked rather than assumed unchanged.

Partial, startup, and shutdown backups remain disabled. The operating procedure requires an initial full backup and explicit full backups coordinated with host restarts. See [Create full backups across restarts](storage-and-recovery.md#create-full-backups-across-restarts).

JEB's command permission level is `4`, reserving backup and restore commands for the owner operator or DatHost console. Helpers are deliberately not operators.

Retention requests two full backups and sixteen differential backups, subject to their dependency chains and the 6,144 MB per-world cap. JEB preserves an 8,192 MB minimum free-space reserve. Strict integrity checking and two worker threads limit backup load.

These are safety limits, not proof that recovery works. Complete the separate-instance cold-restore drill in [`storage-and-recovery.md`](storage-and-recovery.md) before production.

## Ledger (future only)

Ledger is not present in `mods/` or the standard export. Its proposed deployment uses a finite 30-day retention window and DatHost's included MySQL service, with credentials injected only on the live host. Promotion also requires least-privilege permissions, database-aware backups, growth monitoring, and database-outage tests. See [`storage-and-recovery.md`](storage-and-recovery.md) for the proposed configuration and gates.

## Structure generation

- Towns and Towers retains its Cristel Lib overrides; Hopo Better Mineshaft retains its packaged defaults. Generic Cristel Lib settings and its Towns and Towers waystone patch remain unchanged.
- Explorify v1.6.6 replaces interim Structory; Formations is not installed. All 14 packaged placement sets match the former 26.2 placement policy, with structures enabled, so no density override is needed. Fabric API is required; Cristel Lib is optional for Explorify and remains required by Towns and Towers. The legacy `config/cristellib/explorify/structure_placement_config.json5` and `config/cristellib/explorify/structure_toggle_config.json5` are not shipped because their current schema is unverified, not because Explorify is absent. During stopped-server [deployment reconciliation](deployment.md#upload), preserve rollback copies and set aside only these legacy active-host copies before reviewing freshly generated configs against the intended defaults. Do not copy old schemas blindly. Black Spiral remains enabled; measure Nether generation stalls and tick cost explicitly. Older upstream performance reports do not establish a defect or fix on this exact Fabric runtime.
- Standalone Dungeons and Taverns Stronghold Overhaul replaces retired Lite. The obsolete Lite-only file is `config/cristellib/mr_dnt_strongholdoverhaulliteedition/structure_toggle_config.json5`; remove only its active-host copy through the same reconciliation procedure, and do not copy it to the replacement namespace. This standalone pack replaces vanilla stronghold generation and includes enchantment/progression data, so it is not equivalent to Lite and is not the broad DnT collection. Upstream artifact notes warn about a first-generation freeze: measure generation stalls and verify portals, loot, trades, enchantments and Java/Bedrock interactions before production or Chunky pre-generation.
- Moog's Structure Lib keeps its universal multiplier at `1.0`. Namespace-specific multipliers preserve Soaring Structures at `mss = 2.0` and make Ocean Structures uncommon at `mos = 3.0`; adding another Moog pack will not silently inherit either setting.
- MOS 1.1.1 supplies vanilla-block ocean ruins, wrecks, ships, temples, rafts, and seafloor oddities. Its static server-only packaging is favorable for unmodded Java and Geyser, but structure visibility, entities, containers, loot, density, and overlap with Towns and Towers remain runtime acceptance items on both Java and Bedrock.
- Epic Structures: Villages Standalone Edition 1.0.0 adds five village styles without replacing vanilla village templates. The unchanged JAR ships one `epic:villages` structure set at spacing `40` and separation `11`. The pack overrides only that set to spacing `80` and separation `22` chunks, retaining salt `50387312` and neutral frequency `1.0`. Doubling spacing means 75% fewer Epic candidate-grid positions per area, not a measured reduction in generated settlements or all structures. Biome and terrain checks still apply; there is no cross-mod exclusion zone or guaranteed separation from vanilla villages, Towns and Towers or other settlements.
- Epic's override is `config/cristellib/mr_epic_structuresvillagesstandaloneedition/structure_placement_config.json5`, containing only the fully qualified key `epic:villages`. Cristel's existing automatic configuration uses the owning Fabric loader ID for the directory, not the worldgen namespace `epic`. Its automatic filename is `structure_placement_config.json5`, not the separate BuiltInAPI name `placement_structure_config`. The JSON5 file deliberately uses plain JSON syntax for dependency-free policy tests. Existing auto-config settings, Cristel pins, village styles/weights and other structure policies are unchanged. Static library/artifact inspection supports this mechanism; confirm actual config loading and fresh-chunk generation on the designated test host before deployment.
- Structure generation changes affect newly generated chunks; they do not rewrite existing structures. Standalone DnT's data can also change progression outside generation. Test on a disposable world copy, preserve a full rollback snapshot, review newly generated configs, and freeze the approved composition before Chunky pre-generation. No live-world migration is established by this source update.

Spiral Tower Villages 0.0.3 is staged with no configuration override. Its exclusion zones reference the vanilla village set, not `epic:villages`. Promotion requires checking proximity to Epic towns, loot balance, and hidden redstone mechanisms with Alternate Current.

CTOV remains future-only, behind Spiral Tower Villages. Its evaluated Fabric 4.1.0 JAR requires Lithostitched even though that release's Modrinth dependency list omits it. Neither CTOV nor Lithostitched is included in the active or staged pack metadata.

## squaremap

The checked-in `squaremap/config.yml`:

- disables Nether and End maps
- lowers maximum/default/extra zoom
- enables image compression
- reduces background chunks processed per interval
- retains the public live player tracker, including player location, health, armor, and externally fetched player-head images

The live tracker is an explicit friends-and-family policy choice, not an access control. Anyone who can reach the map endpoint can see this information; squaremap provides no built-in login boundary for this configuration. `web-address` and the internal web-server port remain deployment placeholders. Confirm an HTTP port or supported proxy with DatHost before public exposure. Avoid a full pre-generated public render if undiscovered geography is meant to remain part of exploration.

## Chunky

The repository does not automatically pre-generate a world. After the seed and all world-generation files are frozen, use Chunky to generate the intended Overworld radius and then capture a spark baseline.
