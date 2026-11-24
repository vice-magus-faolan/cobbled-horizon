# SlashLoot: personal structure loot

Pack `26.3.0.1.6` adds [SlashLoot](https://modrinth.com/mod/slashloot) `0.6.0+mc26.3-fabric`, project `mRZVkEL7`, version `fCGypkiQ`, using its upstream defaults. The exact server-only JAR is pinned through Packwiz; existing Fabric API `0.165.0+26.3` satisfies its documented baseline. No client mod or second loot engine is added. This is repository readiness, not activation on an existing server or certification of Java/Bedrock gameplay.

## What changes

SlashLoot serves a persistent personal inventory for each player UUID at a supported source. A return visit reopens that copy, not a timed refill. Previously generated but unopened containers can qualify: eligibility depends on a surviving pending loot table, not chunk age. Recognized chests (including trapped), barrels, shulkers and lootable vehicles have source support. Double chests have a mixed-half exception described below; source support is not a preservation pass. Decorated pots are also instanced by default: a player hits an eligible pot for a personal roll once, and it does not break in survival. Custom structure membership alone proves nothing about a container.

Source inspection excludes standalone no-table player storage and previously unpacked empty or partially looted containers from personal-loot handling. This is not a blanket guarantee for a no-table half joined to an eligible loot chest. Already-unpacked containers are **not recovered**. The mod does not reconstruct original rolls, prior looters or missing tables. A table inserted by commands or another mod can also qualify; the marker is not proof of natural origin. Do not adopt player containers or add another loot interceptor. Only the separately approved, one-time [Broadwater migration procedure](slashloot-migration.md) may propose restoring verified metadata to a positively identified, physically empty original single container; it is not ordinary installation. The [dated investigation](loot-investigation.md) explains the historical recovery boundary. Its proposed trial settings are historical research, not the current pack policy or runtime approval.

## Mixed double chests: unresolved preservation gate

Do not join an eligible pending-table chest to ordinary player storage or a previously unpacked half. The inspected [interaction handler](https://github.com/slashdaemon/SlashLoot/blob/a565d5165e475a7520c2623a9498965d4609b244/mc-src/src/main/java/dev/blockacademy/slashloot/handler/ContainerInteractionHandler.java#L149-L158) checks eligibility only for the clicked half, then builds personal containers for both halves. It can create an empty private copy for a tableless half instead of exposing its physical inventory. The [personal-container validity check](https://github.com/slashdaemon/SlashLoot/blob/a565d5165e475a7520c2623a9498965d4609b244/mc-src/src/main/java/dev/blockacademy/slashloot/core/LootContainerBase.java#L93-L98) also rejects a tableless origin, so the resulting menu may not remain usable. Upstream cleanup can later forget that tableless private record. Clicking the tableless half instead returns to vanilla handling, which can expose the real combined inventory, including physical slots in the eligible half. This is not the same inventory as either UUID-private copy.

**Physical insertion can lose items on reload.** In the official Minecraft 26.3 path, `ChestBlock` opens its double-chest menu over a `CompoundContainer` of the real halves; its slot writes reach each physical block entity. A hopper can also insert into physical chest slots through `HopperBlockEntity.addItem` / `tryMoveInItem`, without opening a personal menu. The upstream [unpack mixin](https://github.com/slashdaemon/SlashLoot/blob/a565d5165e475a7520c2623a9498965d4609b244/mc-src/src/main/java/dev/blockacademy/slashloot/mixin/MixinRandomizableContainer.java#L33-L41) cancels unpack for an eligible half even with a null player, but does not cancel physical `setItem`. Thus a vanilla-menu or hopper insertion can leave real items in a chest that still has its pending table.

While that table remains, `ChestBlockEntity.saveAdditional` takes the `trySaveLootTable` branch instead of writing `Items`; loading initializes empty physical slots and takes the table branch instead of loading items. Physical stacks left there are omitted from the saved image and **lost when the chest is reloaded from that save**. Saving does not itself erase the still-loaded in-memory stacks. This includes eligible single chests receiving hopper input, not just mixed doubles. Do not use pending-table sources as physical storage or feed items into them.

Deposits through SlashLoot’s personal menu instead enter the UUID-private inventory in `slashloot.dat`; they are not those omitted physical `Items`. Their separate accepted destruction/cleanup loss is described below. The tableless half uses ordinary item serialization, but that does not make the paired menu or the eligible half safe. This is a source/official-bytecode trace, **not an in-game reproduction**, a demonstrated selected-binary/source equivalence or a fix. It invalidates a blanket ordinary-storage preservation claim. The dated investigation remains historical evidence; its general no-table exclusion does not cover this paired interaction path.

Before any live activation, complete the [mixed-double preservation trial](acceptance-tests.md#personal-loot) on the exact artifact in a separately authorized disposable world. Record both opening directions, distinctive physical remainders in the tableless half, menu validity, per-player state and preservation across restart. Keep eligible loot chests separate from ordinary/partially looted storage; do not break, rearrange or rewrite existing real containers as a workaround. A failed or incomplete trial leaves live activation blocked for an operator decision, not silently accepted by avoiding one test case. This pack does not fix the upstream behavior or claim that preservation has passed.

## Upstream default policy

The pack deliberately ships **no `config/slashloot.json` override**. The pinned mod generates it on first boot. Existing installations retain their own file: uploading this pack does not reset host overrides. Inspect and reconcile any existing settings deliberately before a separately approved installation; a clean hosted first install does not prove the effective policy of an existing host.

| Setting | Default | Consequence |
|---|---|---|
| `enabled` | `true` | Personal loot is enabled for supported pending-table sources. |
| `dimensionBlocklist`, `lootTableBlocklist` | empty | No additional source exclusions. |
| `handleUnknownContainers` | `false` | Unknown container classes stay vanilla. |
| `instancePots` | `true` | Eligible decorated pots give each player a personal roll once. |
| `cleanupOnBreak` | `true` | Broken-source checks are queued; destroyed container entities lose their private records. |
| `pruneIntervalTicks` | `6000` | A background pass starts every 6000 ticks; this is not a personal-loot renewal timer. |
| `pruneBatchSize` | `256` | Bounds entries examined per prune drain. |
| `delegateContainerAnimation`, `playOpenCloseSounds` | `true` | Delegate native lid/barrel/trapped-chest behavior; manual sounds apply only without delegation. |
| `debugLogging` | `false` | No routine position/table decision logging. |

Cleanup maintains SlashLoot records, not chunks or ordinary-storage contents. A player break queues the source for confirmation on the next tick rather than deleting its record before the outcome is known. Destroyed container entities have a separate immediate removal path. Independently, loaded-position pruning starts every 6000 ticks; a missing container **or missing loot-table marker** makes a block record stale. Forgetting a source deletes **every player’s private copy there**, including offline players, generated remainders and valuables deliberately deposited into those copies. Unloaded positions are skipped, not proven safe. Disabling break cleanup does not disable background pruning; retaining records does not necessarily retain access or prevent destruction.

**Accepted lifecycle limitation:** generated loot containers are not safe long-term storage. A player destroying one can discard other players’ private items, not just that player’s leftovers. This loss is accepted for normal adoption, not a deployment blocker or a reason to ship a cleanup override. It does not waive the separate mixed-double and ordinary-storage preservation checks. A future nondefault policy needs a deliberate operator choice.

Hoppers do not extract private loot; comparators see the unrolled shared inventory rather than a personal copy. Delegated trapped-chest signals, pot drops and break, explosion, piston and vehicle behavior need full-stack acceptance. Server-only metadata and vanilla inventory menus are encouraging static evidence, **not a tested Geyser compatibility claim**.

## Retention, removal and administration

Personal inventories live in dimension-scoped `slashloot.dat` SavedData, separate from vanilla container slots. Retain the whole matching world, every dimension, player data/identities, exact mod and configs in a consistent stopped-instance backup. Source/player records still grow with exploration and active players; cleanup is not an age/size retention cap. Monitor world-data size and disk headroom alongside the [existing storage budget](storage-and-recovery.md).

Clearing a table, breaking/replacing a source or losing a vehicle can make private stacks unavailable and eligible for deletion. Vanilla block IDs do not make those stacks vanilla-readable. Disabling/removing the mod can expose a fresh shared roll from the preserved table while stranding private copies. UUID changes can create another entitlement. Do not promise lossless uninstall or accounting continuity.

Require a consistent backup and rehearsed basic rollback before changing an installation. Restore the matching world and all dimensions, player inventories and identities, private mod state, mods and configs together while stopped; restoring only the loot ledger after rewards were taken can duplicate items. A backup is a recovery point, not an all-player export. No complete exporter or lossless uninstall is supplied or required as a blanket adoption gate. An operation that specifically promises to preserve every private stack needs its own demonstrated export/escrow procedure; ordinary adoption does not make that promise. Never call disabling/removing the mod lossless. Historical recovery is a separate optional [Broadwater-only operation](slashloot-migration.md), not a requirement for new worlds or future unopened loot sources.

The upstream command root requires game-master authority (permission level 2); keep only the existing owner operator and authenticated console. Helpers and ordinary Java/Floodgate accounts must not gain that authority. This pack grants no new LuckPerms nodes. See [permission policy](permissions.md).

The following are **destructive reference commands, not a maintenance checklist**. Do not run them without a separately approved, backed-up operation and item-preservation assessment:

- `/slashloot forget here` and `/slashloot forget at <x> <y> <z>` discard all player copies at that block.
- `/slashloot forget player <player>` discards copies for the selected player in the current dimension.
- `/slashloot forget all` clears stored loot for the current dimension.
- `/slashloot prune` synchronously discards stale block records in loaded chunks, even if background pruning is later disabled. A still-present container without its table can count as stale. Unloaded chunks are skipped.
- `/slashloot import discard` discards staged import records. Import confirmation mutates staged state; import is not a historical-vanilla recovery or export command.

`/slashloot stats` reports current-dimension counts; `/slashloot reload` re-reads the config. Neither is an all-player item export. Do not grant broad command/OP access for these conveniences.

## Evidence and remaining gates

Source/archive tests pin the artifact, dependency intent, recipient notices and absence of a pack config override. Hosted `validate` exports the real Packwiz index. The existing hosted `native-acceptance` first install requires no preexisting SlashLoot config, then checks the loaded version/entrypoint, no config-load error and actual generated defaults on first boot and offline restart, retaining the existing save/exit/cleanup requirements. These assertions must pass on the exact PR head; see the [dated evidence and limits](verification.md#slashloot-263). Successful boots do not exercise personal inventories.

Complete the [personal-loot acceptance matrix](acceptance-tests.md#personal-loot) on a separately authorized disposable world with unmodded Java and real Bedrock clients before claiming gameplay compatibility. Include two UUIDs, repeat visits, non-empty remainder persistence across restart, old pending-table sources, ordinary/partial/player-replaced storage, supported container families and pots, mixed double chests, automation and source-marker loss. Private-claim persistence, real-client behavior and basic consistent rollback remain separate observations. Accepted destruction/cleanup loss, absent timed refill and optional historical migration do not block normal adoption. Lossless removal remains unverified, not a blanket gate.

## Optional selective protection

Protection is a future improvement tracked in [issue #55](https://github.com/vice-magus-faolan/cobbled-horizon/issues/55), not a dependency or activation gate; this PR does not complete or close it. No additional protection mod is selected. SlashLoot has no protected-source setting. The selected Fabric API [0.165.0+26.3 BEFORE callback](https://github.com/FabricMC/fabric-api/blob/0.165.0%2B26.3/fabric-events-interaction-v0/src/main/java/net/fabricmc/fabric/api/event/player/PlayerBlockBreakEvents.java) can cancel server-side player breaks; an opt-in upstream change could narrowly protect verified managed sources. A loot marker alone is not natural-origin proof. This callback does not cover explosions, pistons, commands/edits, vehicles or mixed-double menu handling, and translated Bedrock breaks are not runtime-tested.

The bounded candidate review found no verified narrow fit, not an ecosystem-wide absence. [Safe Zone v1.6.0](https://github.com/joelra/safe-zone/blob/v1.6.0/README.md#known-limitations) documents broad full-height claims and a piston gap; its binary was not independently checked and it is not recommended for this purpose. If requested later, scope a player-break-only upstream option first (roughly 0.5–1 engineer-day plus client availability); all-destruction coverage requires a separate mechanism inventory and estimate. Upstream [mixed-double issue #2](https://github.com/slashdaemon/SlashLoot/issues/2) is a source report, not evidence of an executed failure or a fix.

## Upstream basis and attribution

The [official exact version](https://api.modrinth.com/v2/version/fCGypkiQ) supplies the original download/hash/dependency identity. The JAR declares Slash as author and Copyright (c) 2026 The Block Academy under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/). The binary is unmodified. Complete embedded notice and legalcode accompany generated CREDITS/SOURCES/LICENSES; preserve attribution and later change notices without implying endorsement.

Configuration/loading, eligibility, persistence and destructive-command descriptions come from [upstream source at a565d516](https://github.com/slashdaemon/SlashLoot/tree/a565d5165e475a7520c2623a9498965d4609b244), specifically SlashLootConfig, Handling, interaction handlers, CleanupHandler, SlashLootState and SlashLootCommand. Artifact contacts identify this source; the older project API source pointer is stale. Source inspection is not proof of a reproducible build or gameplay.
