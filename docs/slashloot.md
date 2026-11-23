# SlashLoot: personal structure loot

Pack `26.3.0.1.6` adds [SlashLoot](https://modrinth.com/mod/slashloot) `0.6.0+mc26.3-fabric`, project `mRZVkEL7`, version `fCGypkiQ`, using its upstream defaults. The exact server-only JAR is pinned through Packwiz; existing Fabric API `0.165.0+26.3` satisfies its documented baseline. No client mod or second loot engine is added. This is repository readiness, not activation on an existing server or certification of Java/Bedrock gameplay.

## What changes

SlashLoot serves a persistent personal inventory for each player UUID at a supported source. A return visit reopens that copy, not a timed refill. Previously generated but unopened containers can qualify: eligibility depends on a surviving pending loot table, not chunk age. Recognized chests (including trapped), barrels, shulkers and lootable vehicles have source support. Double chests have a mixed-half exception described below; source support is not a preservation pass. Decorated pots are also instanced by default: a player hits an eligible pot for a personal roll once, and it does not break in survival. Custom structure membership alone proves nothing about a container.

Source inspection excludes standalone no-table player storage and previously unpacked empty or partially looted containers from personal-loot handling. This is not a blanket guarantee for a no-table half joined to an eligible loot chest. Already-unpacked containers are **not recovered**. The mod does not reconstruct original rolls, prior looters or missing tables. A table inserted by commands or another mod can also qualify; the marker is not proof of natural origin. Do not restore table NBT, adopt player containers or add another loot interceptor to compensate. The [dated investigation](loot-investigation.md) explains the historical recovery boundary. Its proposed trial settings are historical research, not the current pack policy or runtime approval.

## Mixed double chests: unresolved preservation gate

Do not join an eligible pending-table chest to ordinary player storage or a previously unpacked half. The inspected [interaction handler](https://github.com/slashdaemon/SlashLoot/blob/a565d5165e475a7520c2623a9498965d4609b244/mc-src/src/main/java/dev/blockacademy/slashloot/handler/ContainerInteractionHandler.java#L149-L158) checks eligibility only for the clicked half, then builds personal containers for both halves. It can create an empty private copy for a tableless half instead of exposing its physical inventory. The [personal-container validity check](https://github.com/slashdaemon/SlashLoot/blob/a565d5165e475a7520c2623a9498965d4609b244/mc-src/src/main/java/dev/blockacademy/slashloot/core/LootContainerBase.java#L93-L98) also rejects a tableless origin, so the resulting menu may not remain usable. Upstream cleanup can later forget that tableless private record. Clicking the other half follows a different eligibility path; that does not establish safe access to the combined inventory.

This is a source-traced limitation, not a runtime reproduction, proof of physical item deletion or proof that the selected binary is equivalent to the inspected source. It invalidates a blanket ordinary-storage preservation claim. The dated investigation remains historical evidence; its general no-table exclusion does not cover this paired interaction path.

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

Cleanup maintains SlashLoot records, not chunks or ordinary-storage contents. For loaded block positions, a missing container **or missing loot-table marker** can make a record stale; forgetting it deletes all private player copies at that source. Unloaded chunks are skipped. Disabling cleanup would instead retain potentially inaccessible records and increase storage use; it would not restore the source. A future nondefault policy needs a concrete compatibility/balance reason and a deliberate operator choice.

Hoppers do not extract private loot; comparators see the unrolled shared inventory rather than a personal copy. Delegated trapped-chest signals, pot drops and break, explosion, piston and vehicle behavior need full-stack acceptance. Server-only metadata and vanilla inventory menus are encouraging static evidence, **not a tested Geyser compatibility claim**.

## Retention, removal and administration

Personal inventories live in dimension-scoped `slashloot.dat` SavedData, separate from vanilla container slots. Retain the whole matching world, every dimension, player data/identities, exact mod and configs in a consistent stopped-instance backup. Source/player records still grow with exploration and active players; cleanup is not an age/size retention cap. Monitor world-data size and disk headroom alongside the [existing storage budget](storage-and-recovery.md).

Clearing a table, breaking/replacing a source or losing a vehicle can make private stacks unavailable and eligible for deletion. Vanilla block IDs do not make those stacks vanilla-readable. Disabling/removing the mod can expose a fresh shared roll from the preserved table while stranding private copies. UUID changes can create another entitlement. Do not promise lossless uninstall or accounting continuity.

Before cleanup, reset, migration or removal where remaining private items must be preserved, establish a rehearsed way to retain/export **all remaining private stacks for every player**, including offline players and inaccessible sources, into protected escrow. Reconcile source/UUID, items, components and counts; retain originals and verify a cold restore. No complete all-player exporter or safe lossless removal procedure is supplied here. A backup is a recovery point, not an export, and a successful boot proves neither. These are unresolved operational gates, not capabilities delivered by installing this mod. No Broadwater inspection, recovery or deployment is part of this change.

The upstream command root requires game-master authority (permission level 2); keep only the existing owner operator and authenticated console. Helpers and ordinary Java/Floodgate accounts must not gain that authority. This pack grants no new LuckPerms nodes. See [permission policy](permissions.md).

The following are **destructive reference commands, not a maintenance checklist**. Do not run them without a separately approved, backed-up operation and item-preservation assessment:

- `/slashloot forget here` and `/slashloot forget at <x> <y> <z>` discard all player copies at that block.
- `/slashloot forget player <player>` discards copies for the selected player in the current dimension.
- `/slashloot forget all` clears stored loot for the current dimension.
- `/slashloot prune` synchronously discards stale block records in loaded chunks, even if background pruning is later disabled. A still-present container without its table can count as stale. Unloaded chunks are skipped.
- `/slashloot import discard` discards staged import records. Import confirmation mutates staged state; import is not a historical-vanilla recovery or export command.

`/slashloot stats` reports current-dimension counts; `/slashloot reload` re-reads the config. Neither is an all-player item export. Do not grant broad command/OP access for these conveniences.

## Evidence and remaining gates

Source/archive tests pin the artifact, dependency intent, recipient notices and absence of a pack config override. Hosted `validate` exports the real Packwiz index. The existing hosted `native-acceptance` first install requires no preexisting SlashLoot config, then checks the loaded version/entrypoint, no config-load error and actual generated defaults on first boot and offline restart, retaining the existing save/exit/cleanup requirements. These assertions must pass on the exact PR head; this document does not claim they already ran. Successful boots do not exercise personal inventories.

Complete the [personal-loot acceptance matrix](acceptance-tests.md#personal-loot) on a separately authorized disposable world with unmodded Java and real Bedrock clients before claiming gameplay compatibility. Include two UUIDs, repeat visits, non-empty remainder persistence across restart, old pending-table sources, ordinary/partial/player-replaced storage, supported container families and pots, mixed double chests, automation and source-marker loss. All-player escrow/export, cold restoration and lossless removal remain unverified.

## Upstream basis and attribution

The [official exact version](https://api.modrinth.com/v2/version/fCGypkiQ) supplies the original download/hash/dependency identity. The JAR declares Slash as author and Copyright (c) 2026 The Block Academy under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/). The binary is unmodified. Complete embedded notice and legalcode accompany generated CREDITS/SOURCES/LICENSES; preserve attribution and later change notices without implying endorsement.

Configuration/loading, eligibility, persistence and destructive-command descriptions come from [upstream source at a565d516](https://github.com/slashdaemon/SlashLoot/tree/a565d5165e475a7520c2623a9498965d4609b244), specifically SlashLootConfig, Handling, interaction handlers, CleanupHandler, SlashLootState and SlashLootCommand. Artifact contacts identify this source; the older project API source pointer is stale. Source inspection is not proof of a reproducible build or gameplay.
