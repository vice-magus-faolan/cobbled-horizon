# Renewable and per-player structure loot on Fabric 26.3

> **Historical research, superseded policy recommendations.** The findings below retain their original research scope, not current adoption gates. Use the [current SlashLoot guide](slashloot.md) and [Broadwater-only one-time recovery utility](slashloot-migration.md). The operator selected upstream defaults and accepted source-destruction/private-item loss (including deposited valuables). The old blanket escrow/lossless-removal gate and permanent-extension recommendation below are not current requirements. The optional offline utility now restores supported empty structure positions under world-level approval, including possible empty replacements; SavedData alone still cannot enable handling. Mixed-double/ordinary-storage, real Java/Bedrock, private-restart and basic rollback evidence remain independently required. No live Broadwater world or backup was accessed.

**Investigation date:** 23 November 2026. **Status:** research and design, not an installation recommendation or runtime certification.

**Repository baseline:** `26.3` at `ad603ee5191987e74d2a544a7c6cde4b0058009f`, pack `26.3.0.1.5`, Fabric Loader `0.20.1`. This is the inspected published branch, not an assertion about Broadwater's current on-disk configuration.[1]

## 1. Executive decision

**We can add fair rewards without resetting terrain. We cannot safely and automatically recover every historical loot container from the surviving world alone.** The reviewed 26.3 candidates can recognize supported containers whose original loot-table marker still exists. None provides a demonstrated safe retrofit for arbitrary previously opened, emptied, reused or replaced containers.[11][41][32]

**Recommend an existing mod with a narrow, separately reviewed recovery extension:** evaluate **SlashLoot 0.6.0+mc26.3-fabric** first for intact loot-table containers; design a report-only recovery planner and explicitly approved, additive virtual rewards for historical locations. Fair Loot is the secondary non-converting comparison. Do not port or install ChestShare+ wholesale, and do not combine two loot interceptors.[8][11][46]

**This is a shortlist, not a claim that any candidate currently satisfies every hard requirement.** Lossless export/removal and private-copy cleanup are unresolved acceptance gates; SlashLoot's default lifecycle can delete private inventories when its source marker disappears.[93]

The preservation-first choice is **Model A, one persistent personal inventory per source and player, with timed refresh off**. New players can benefit from old exploration; repeat visits by the same account do not become a resource timer. Rewards for previously looted locations would be a deliberate new entitlement, not restoration of the original randomized roll or proof of who already collected it. This balance policy needs explicit acceptance before implementation.

ChestShare+ demonstrates that some retrospective **loot-table/template recovery is technically possible**. Its 1.21.1 implementation finds expected container positions from structure templates. However, direct adoption clears physical slots, while even its guarded empty-container path cannot distinguish an identical player replacement at the original position. It does **not** satisfy this world's version and preservation requirements as shipped.[59][53][54]

**Hard limit:** if an empty generated chest and an empty player replacement have the same surviving state, a retrospective classifier cannot tell them apart. More scanning does not create the missing history. Uncertain containers must remain ordinary storage; if compensation is desired, a separate virtual claim can avoid adopting the physical inventory. No claim of zero-risk automatic archaeological recovery is justified.

### Evidence levels and limits

- **A — artifact:** exact published file or repository blob inspected; hashes/loader metadata checked. A 26.3 declaration is not a successful boot.
- **S — source:** behavior traced in retained upstream source at the recorded revision. Source-to-binary equivalence is not presumed.
- **D — documentation:** a maintainer's documented behavior, not independently exercised.
- **P — practical:** an actual isolated experiment. Here, P applies only to static ZIP/NBT parsing and checksum checks, **not Minecraft gameplay**.
- **U — unknown:** no relevant execution established the result.

No Minecraft server or client was launched. No Broadwater world, backups, credentials or live connection were accessed. Java-client interaction, Geyser/Floodgate behavior, restart durability under gameplay and mod removal remain practical acceptance gates. This investigation does not enumerate real Broadwater recovery coordinates.

## 2. Candidate comparison

### Exact target builds and dependencies

All version statements below are the captured 23 November listing/artifact state, not a promise of continued availability. The companion [evidence inventory](loot-investigation-evidence.json) retains source URLs, capture precision and hashes; binaries are not included in the repository.

| Candidate | Fabric 26.3 artifact observed | Dependencies and client boundary | Disposition |
|---|---|---|---|
| SlashLoot | `0.6.0+mc26.3-fabric`, Modrinth `fCGypkiQ`, 10 Nov 2026 | JAR: Loader >=0.15.11, Java >=25, Fabric API. No client entrypoint/custom replacement block required. README's 26.3 API baseline is 0.161.0+26.3.[8][10] | First isolated trial; not retrospective recovery by itself. |
| FreshLoot | `2.0.0+26.3`, `qK6VD1Sp`, Fabric file 26 Sep 2026 | JAR: Loader >=0.19.5, Java >=25, Fabric API. Later Forge/NeoForge files are not a newer Fabric build.[16] | Reject for this preservation-oriented rollout. |
| LootRestock | `1.0.3`, `M5kTZo9M`, 17 Oct 2026 | Listing targets Fabric 26.3; JAR text names Loader >=0.19.5, Java >=25, Fabric API, but embedded version is 1.0.0 and its description contains an unescaped newline: **strict JSON parsing fails**.[21][27] | Hold: runtime loadability unknown; shared refill is also the weaker gameplay fit. |
| Lootr + Lootr Polymer Patch | Lootr `1.25.42.124`, `gVwn7m2v`, 27 Sep; patch `1.3`, `DMk4xzkH`, 1 Oct 2026 | Lootr alone is client-required. Patch supplies the vanilla-client presentation path, requires Lootr/Fabric API/Loader >=0.19.5; bundles Polymer Core/Virtual Entity 0.18.2+26.3 and Server Translations API. Lootr bundles Resourceful Config. Patch API dependency list is empty despite JAR requirements.[28][29] | Broader coverage, higher migration/removal burden. |
| Fair Loot | `fairloot-fabric-26.3-0.1.0.jar`, release `v0.1.0`, 8 Nov 2026 | JAR: Minecraft >=26.3 <26.4, Loader >=0.16; no Fabric API requirement declared. Main-only entrypoint; vanilla inventory protocol design. CurseForge category alone is not its client requirement.[44][48] | Secondary non-converting comparison; very new. |
| ChestShare+ | Latest inspected `0.3.3`, CurseForge file `8985900` | **1.21.1 only**, Loader >=0.16, Java >=21, Fabric API; not a 26.3 artifact. Archive also contains three 1.21.1 storage-mod JARs at its root; presence is not evidence the loader loads them.[49][59] | Study recovery design; do not install on 26.3. |

### SlashLoot: best initial fit, not an archaeological recovery tool

**S:** `Handling.forBlock/forEntity` requires a non-null loot table, applies dimension/table exclusions and only suppresses vanilla unpacking when the corresponding interaction path will serve the container. The block and original loot-table metadata remain vanilla. Ordinary player storage with no table stays vanilla; a table added by a player, command or another mod is also eligible, so this is a state marker, not certified natural origin.[11]

**S/D:** source coverage includes single/double/trapped chests, barrels, shulkers and lootable vehicle paths; vehicle records use entity UUIDs. Decorated-pot handling is present in the newer release/source despite older project text excluding it. Unknown container handling defaults off; recognized subclasses/integrations are not a blanket promise for custom inventories.[8][10][11]

**S:** a personal inventory is selected/created on open. Normal returns reopen the saved copy; the initial roll mixes the container seed with the player's UUID. Existing chunks with untouched tables can work because generation time is not the eligibility criterion. Already-cleared empty or partial containers fail the table gate.[12]

**S:** inventories are dimension-scoped SavedData (`slashloot.dat`).[13]

`CleanupHandler` prunes a loaded block position when `stillPhysicallyPresent` no longer finds a randomizable container **with a loot-table marker**; `forgetBlock` then deletes **every player's copy** at that source.[93][11]

Entity destruction similarly forgets its record; admin `forget`, `forget player` and `forget all` are destructive, not exports.[93][94]

**Trial/activation gate:** disable deletion-prone background and break cleanup during controlled item-preservation trials and restrict destructive commands; do not enable real-player use, cleanup, reset, migration or removal until **all players' remaining private stacks** can be retained/exported to protected escrow. Test marker clearing/replacement with non-empty private copies. Merely backing up or confirming vanilla block IDs is insufficient.

**D/S:** hoppers do not extract virtual loot and comparators see the unrolled shared inventory; changed break/explosion/redstone semantics need full-stack tests.[10]

**Removal:** base blocks remain readable by vanilla, but vanilla cannot expose the private copies. Preserved table metadata can produce another shared roll after disabling/removal. Therefore block-format reversibility is **not** lossless item/accounting migration. No complete export-to-vanilla/escrow procedure was established in this audit.[11][13]

The dry-run/confirm `import` command imports **pre-existing per-player mod records**, matched using table/seed information. It cannot derive missing historical metadata or prior looters from an emptied vanilla chest.[61]

### FreshLoot: rotation changes the container

**S:** it tracks player UUID versus dimension/position. For an eligible untouched single chest or barrel, closing the menu destroys and replaces the block with a newly table-backed container for the next player. `destroyBlock(..., true, ...)` requests drops: remainders become loose items rather than staying safely in a private inventory. This is not the preservation behavior requested.[17][18]

It recognizes a surviving loot table, not old generation history. Previously opened-empty and partial containers cannot be recovered. Its double-chest close path is skipped; no chest-minecart or arbitrary custom-container path was established. Saved looter records are persistent, but block replacement, dropped remainders and changed block-entity state make removal/restart and item safety very different from a virtual inventory.[17][18]

### LootRestock: shared timed refill with material caveats

**S:** tracked table/seed information is persisted in world-root `chest_reset_data.json`; scheduled work skips unloaded chunks. Defaults are seven days, empty-only resets and barrels excluded; chest minecarts have a separate path. It does not individualize chest loot.[22][23][24]

The table must still exist when a previously untracked container is registered. Thus a pre-install looted chest cannot be rediscovered merely because the chunk loads. With empty-only disabled the reset path clears contents before regeneration. Even empty-only cannot prove an emptied tracked container is not now player storage.[22]

The captured tracker includes open reports concerning concurrent modification during world ticks and unbreakable chests; these were not reproduced. A data-load error can reset the tracking map. File metadata problems described above are artifact findings, **not a proved Fabric Loader rejection**. On removal its ordinary physical inventories remain, but scheduled tracking ceases; no lossless lifecycle test was performed.[26][23][27]

Its separate opt-in Trial Vault timer expires rewarded-player UUIDs after post-install tracking. That can create additional vault rewards, not recover chest tables or historical rolls.[24]

### Lootr plus Polymer Patch: mature core, conversion costs

**S:** eligible loaded container/entity paths require a surviving, allowed loot table and a matching conversion provider. Block conversion waits for surrounding loaded chunks, copies selected state and replaces the original with a Lootr form. Supported families include chest/trapped chest/barrel/shulker and separate chest-minecart conversion; other families and modded integration rely on tags/providers/accessors. Custom structure placement of an ordinary chest is easier than an arbitrary custom inventory.[32][35]

**S:** personal inventories live in separate SavedData, not ordinary chest item NBT. Configurable refresh/decay exists; refreshing can clear saved copies. Hoppers are intentionally restricted. Existing-unopened is supportable in source, but cleared table metadata is not restored.[33][34][32]

Polymer Patch translates presentation; it does not undo Lootr's block/entity conversion or make its private inventories vanilla-readable. Its tracker records a historical unmodified-client join failure on 26.1.2, fixed according to the maintainer in 1.3. That is not a 26.3 cross-play pass.[38][39]

No demonstrated complete vanilla export/uninstall path was found in the inspected paths. Removing Lootr while custom IDs and separate inventories remain could strand data; the exact vanilla response was not tested. Retaining the full mod and SavedData/world backup is mandatory until a controlled removal rehearsal succeeds.[33]

### Fair Loot: attractive small design, young and destructive at some lifecycle boundaries

**S:** instances table-bearing chest/barrel/shulker block entities, preserves their vanilla blocks and table metadata, and uses personal vanilla menus. Double-chest halves are independent source positions; mixed ordinary/loot halves have an explicit ordinary-inventory path. Chest minecarts and unrelated custom classes are not covered. Previously-cleared containers are explicitly unchanged.[41][46]

A compressed world `data/fairloot.dat` stores player inventories/timestamps. It uses a temporary file and atomic replacement on save, but that is not proof of crash-atomic player-inventory plus loot-ledger transactions. Failed/partial loading can permit fresh rolls. Default refresh is zero/off; enabling expiry replaces an old personal copy, and operator reset forgets copies.[41][42][47]

Normal break protection can be bypassed by sneaking/creative behavior: the breaker gets their own copy and other players' entries are forgotten. No explosion-specific protection was established. Those details and private-inventory accessibility on removal prevent a present claim of lossless operation, despite the README's reassuring vanilla-block removal description.[41][46]

### Maintenance, adoption, licensing and source identity

These are dated platform counters, not active-server counts or a security score.

| Candidate | Captured activity/adoption | Actual license/source evidence and limitations |
|---|---|---|
| SlashLoot | 1,760 Modrinth downloads; GitHub 2 stars/1 fork, source push 10 Nov; no open issues at capture.[9][15] | CC-BY-4.0 license text. Structured Modrinth source pointer was stale; retained JAR/README point to `slashdaemon/SlashLoot`, inspected at `a565d5165e475a7520c2623a9498965d4609b244`.[14][10] |
| FreshLoot | 555 Modrinth downloads; source push 12 Nov; GitHub 0 stars/forks.[86][20] | Apache-2.0. Inspected Fabric source `a8da801c5dfa1bf1225b875778a9915d771934f8` postdates the Fabric file; not proven to be its build revision.[19][16] |
| LootRestock | 13,877 Modrinth downloads; open issue reports materially affect the shortlist.[85][26] | Repository GPL-3.0 text versus hosting metadata GPL-3.0-or-later; record exact terms for any later reuse/distribution. Source `cdc10143ce17fb3b889d6dff278eb9cb52b362cf` is inspected, not reproducibly bound to the JAR.[25][85] |
| Lootr | 24,530,514 project downloads / 1,534 followers; inspected 26.3 build has 63,434 downloads.[30][28] | MIT text; changelog identifies source `2a9c8307460e3ff5765ecd849b11a6faf06dfe8b`. Mature upstream adoption does not certify Patch or Broadwater interoperability.[36][28] |
| Polymer Patch | 4,369 downloads / 33 followers; source push 1 Oct; known join-fix history.[31][40][39] | MIT; inspected `688007ce5ea6aeb5edee52a9ba140651d601259b`. API/artifact dependencies disagree; account for bundled libraries.[37][29] |
| Fair Loot | First 0.1.0 release 8 Nov; source 0 stars/forks/issues and last push 8 Nov.[44][45] | MIT; release source `1e8ffacfd868a54bad6a959d9226f3ca7069a194`. GitHub/CurseForge downloads were byte-identical; this does not prove a reproducible build.[43][48] |
| ChestShare+ | Small fork: GitHub 1 star; push 27 Sep; 0.3.3 notes fixes for accidental storage capture and lost restart registrations.[60][50] | Source/JAR declare MIT, hosting calls it Custom License. Tag `v0.3.3` resolves to `3649476248db0b90c94b265909eab1999fc191e0`; default branch has later differences. Neither version is 26.3.[51][59] |

Exact hashes pin what was inspected, not what will execute compatibly. Except where a release identifies a source revision, treat upstream source and binary as distinct evidence. License identification here is not legal clearance to redistribute the whole dependency closure.

### Additional options discovered

- **Unlimited Trial Vaults 1.0.9+26.3:** Fabric, server-side, GPL-3.0-or-later; permits repeat key-paid vault rewards, not chest/barrel recovery. Its source and README disagree about normal-vault defaults; set policy explicitly before any isolated trial. It solves a different problem.[62][64][63]
- **Phantom Loot 1.0.0 for 26.3:** server-only/virtual-loot claim, but all-rights-reserved and no source/issues link in the inspected listing; it also requires a surviving table. Not the auditable open-source recommendation.[66][67]
- **Equal Loot:** target-version server build, but per-player **mob drops**, not container recovery.[68]
- **Personal Treasure Loot / ChestRefill:** no published 26.3 file in the inspected version lists. **Lootin Remastered:** its actual 26.3 files target Bukkit-family servers, despite project-level Fabric metadata. Do not replace Fabric with a plugin hybrid for this task.[69][71][70]

## 3. Minecraft mechanics and the information boundary

### Exact-version identity

The retained official Mojang 26.3 metadata identifies release time `2026-09-15T11:23:02Z`, Java 25 and server SHA-1 `33680f5f2ac32864d6d7cf5e56a705fdb3e05f4c`. The downloaded 62,294,556-byte server artifact matches that official identity. It was inspected, not launched.[73][74]

**A/S — exact official bytecode:** the nested `META-INF/versions/26.3/server-26.3.jar` was extracted from the hash-verified official bundle; its SHA-256 is `a362163eec5d1612d520772bc16e5b39c09e3b234fdc045f56bf544284ee8ae6`. Six extracted class files were compared byte-for-byte with that nested JAR. A bounded class-file reader produced retained instruction traces without executing Minecraft or installing Java.[74]

| Exact 26.3 method | Inspected primary-byte finding |
|---|---|
| `RandomizableContainer.unpackLootTable` | Method Code offsets 75–81 call `setLootTable(null)`; offsets 137–143 pass the seed to loot fill.[74] |
| `RandomizableContainer.trySaveLootTable` | Offsets 0–12 return false for a null key; the other branch writes the table and only a nonzero seed.[74] |
| Chest/Barrel `saveAdditional` | Both call `trySaveLootTable`; false selects `ContainerHelper.saveAllItems`.[74] |
| `ContainerEntity` and `AbstractMinecartContainer` | Vehicle unpack clears the key; save/load select table/seed or item stacks, and the minecart delegates to those methods.[74] |

The trace SHA-256 is `03f21b93e52010c43de919b5236199e69bf72d524b612d06c7936c0100b4d165`. Class identities/methods are recorded in the companion evidence inventory. This proves the decisive ordinary-container metadata lifecycle, not runtime interoperability.

**Supplementary-reference limit:** automation and structure details below also use retained 26.3-labeled decompiled pages. Those pages are unofficial and include some Fabric integration; their correspondence to the official JAR was not independently established. They are explicitly attributed reference evidence, not additional exact-bytecode verification.

### Container lifecycle

Generation assigns pending table/seed data through template or structure placement paths in the supplementary reference code.[92] The exact official unpack/save methods confirm that rolling consumes the pending table key and subsequent chest/barrel serialization stores remaining item stacks instead.[74] Once those items are removed, the inspected content-save path retains no original table/seed association; a stale seed in memory does not change that persisted branch.[74]

Thus “opened” is shorthand for **unpacked**. The supplementary block-entity and hopper references show inventory access/removal/emptiness paths that can unpack loot without a player opening its GUI; this automation path was not separately bytecode-verified here.[87][88]

Their spectator menu restriction is not a general protection against automation.[87]

The exact vehicle persistence methods confirm analogous table/seed-versus-items behavior; mobile identity must still be handled separately.[74]

Other block/item metadata can survive as applicable, but the inspected ordinary-container save paths contain no historical per-container looter ledger or recovery copy of a consumed table.[74] A player's aggregate statistics do not resolve that missing per-coordinate history; no historical looter classification is claimed.

### Structure generation and persistence

**Supplementary reference finding:** structure starts serialize structure identity, start chunk, references and child pieces.[89]

Piece data can include a bounding box/orientation; template pieces retain template identity and origin.[90][91]

Template resources can retain local container/table data and placement can assign a new seed.[92]

These clues support **expected generation semantics**, not the current storage block's ownership; these structure paths were not included in the primary-bytecode audit.

A structure bounding box is not an inventory of all historical loot containers. Procedural structure pieces, features such as monster rooms, jigsaw processors, template palettes, terrain adaptation and mod-specific generation do not all expose the same reconstruction surface. A static template table/seed, often seed zero, need not equal the seed or realized contents produced at the historical live placement.

The inspected save/load paths serialize current container state; they do not restore a consumed key after restart.[74] Structure records provide their separate current piece metadata according to the supplementary reference.[89] A mod can retain prospective history, but installation cannot prove that such a record existed beforehand.

### What can and cannot be recovered

- **Intact pending table:** enough information to generate rewards through a supported per-player implementation; no terrain regeneration required.[11][12]
- **Pre-loot backup or prior mod ledger:** may contain the exact prior table/seed or personal inventory. Inspect a copy and establish identity; restoring whole old chunks is neither necessary nor authorized.[61]
- **Matching template/structure:** can often supply an expected table or baked template inventory. This enables new rewards, subject to validation; it is not necessarily an exact old item roll.[55]
- **No surviving historical information:** exact original table, random realization and previous looters are generally underdetermined. A uniform generic reward is a new policy, not recovered evidence.
- **Same-looking player replacement:** no purely state-based rule can establish natural ownership. This is a provenance limit, not just an unimplemented feature.

## 4. Existing-world recovery approaches

| Approach | Feasibility and reliability | Work/performance | Principal risk and safe boundary |
|---|---|---|---|
| A. Structure-aware reconstruction | Feasible for identified saved pieces with exact matching templates/transforms; weaker for procedural/features/custom storage. Recovers expected source semantics, not historical ownership.[54][55] | Index templates once; inspect bounded admitted chunks/structures and cache template lookups. Avoid whole-world scans in tick/open callbacks. | A nearby bounding box is insufficient. Require exact palette/block/position evidence; report ambiguity, never sweep all empty containers. |
| B. Separate same-seed world | Technically useful as an **evidence donor** when original version, seed, dimensions, generator settings, datapacks, mods/config, resource order and generation history match. Equality has not been tested here. | Potentially expensive disk/CPU/generation; reproduce only approved regions on an isolated host, without external integrations/production credentials. | Current pack/seed equality does not establish historical generation equality. Copy **only candidate metadata**, never donor chunks, region files, terrain, or whole level data. |
| C. One-time migration | Practical for an approved finite manifest of empty confirmed locations, or information recovered from an authoritative backup/ledger. Non-empty locations excluded from physical adoption. | Bounded resumable batches and a persistent migration receipt; no recurring scanner necessary for manually nominated sites. | Emptiness is not ownership. Apply-time checks can reject drift, but cannot manufacture pre-install provenance. |
| D. Hybrid | Best practical coverage: source/template matching nominates straightforward cases; explicit review handles uncertainty. Uncertain physical storage remains untouched. | Human review becomes the cost for scarce/valuable or modified sites; validate only admitted coordinates. | Human consent is not infallible provenance. Use a separate virtual reward action when storage ownership cannot be proved; do not authorize a destructive guess. |

### What ChestShare+ actually demonstrates

At startup its fingerprint registry scans active structure NBT for storage positions, palette information, table IDs/seeds and baked items. Baked fingerprints record slot/item/count, not full components. Its placement resolver transforms piece-local positions; fallback layout/content alignment can help find likely matches, but matching common items is not proof.[55][56]

Its **explicit `adopt-structure` command is an immediate write**, not a preview. The registrar clears the pending table/seed and live slots, then installs shared state. Precise adoption can replace non-empty storage and old private copies; fallback may adopt generic storage in a piece's bounds. Do not run it on Broadwater.[57][53]

Its **optional empty restoration** is off by default. It requires an unshared empty container, a unique recognized template claim, matching block ID, non-empty template and no multi-palette ambiguity. This is meaningfully more careful, yet still accepts an identical empty player replacement at the template position. Multi-palette first-palette handling and component-loss in baked items further limit a direct port.[54][55]

Its **mirror export/import** only exports already-registered donor containers, not every loaded chest. Default import skips occupied destinations; `force` removes that safeguard. The payload does not prove donor/destination seed or generator equality, and import starts writing without a separate approval report. These are useful design lessons, not a safe migration recipe as shipped.[58][52]

### Modified structures and partial loot

Never replace a non-empty physical inventory. A partial chest may contain original loot, later player deposits or both; neither item labels nor structure membership resolves ownership. Leave its bytes and normal storage access unchanged. If fair rewards are separately approved, associate a virtual entitlement with the historical source rather than clear or merge the physical inventory.

Removed/moved containers must not be recreated automatically. An empty replacement at an expected coordinate remains ambiguous. Changes after enrollment should tombstone a source; they must not silently reset eligibility and grant another roll. Mobile minecarts require a separate, validated entity strategy, not a coordinate-based migration shortcut.

## 5. Gameplay model selection

| Criterion | A. Once-per-player | B. Shared timed restock | C. Personal loot plus refresh |
|---|---|---|---|
| New/existing player fairness | Each stable account gets an independent opportunity; original pre-install looters are unknown. | Early arrival after each timer still wins; newcomers can still find empty chests. | Fair access per cycle, but existing players gain recurring supply. |
| Exploration incentive | Strongest: a player must seek a new source after exhausting one. | Encourages memorized routes/camping, especially with waystones. | Revisiting is rewarded; balance needs caps/costs beyond a cooldown. |
| Exploitation | Alternate accounts, broken/replaced sources and ledger rollback must be controlled. | AFK automation and high-value route farming are concerns. | Adds timer-reset, account and repeated rare-item farming surfaces. |
| Persistence/performance | Storage scales with visited player-source pairs and remaining stacks. | Tracks sources/timers and scheduled loaded-chunk work. | Largest state/expiry surface; careless refresh can destroy leftovers. |
| Vanilla behavior | Vanilla-looking UI, but hopper/comparator/break semantics can differ. | More shared-inventory-like, but loot renewal is non-vanilla. | Most policy change; private inventory plus recurring generation. |
| Explored/modded locations | None can recover missing historical metadata merely by selecting this model. | Same recovery requirement; empty-only is not provenance. | Same recovery requirement, plus expiry safety and custom-container integration. |
| Maintenance | Prefer one engine and immutable source identity. | Scheduler/empty checks/removal rules need scrutiny. | More configuration, state transitions and upgrade tests. |

**Recommendation:** A initially; no automatic rare-loot refresh, no whole-world reset command for ordinary helpers, no first-player advantage repeated every week. Do not stack SlashLoot/Fair Loot/FreshLoot/Lootr/LootRestock on the same containers: they compete around unpacking, opening, conversion or resetting.[11][17][22]

If revisits become a deliberate later goal, use an explicit finite event or separately balanced reward table, not periodic regeneration of every progression chest. Avoid promising bounded resources merely because the cooldown is long.

## 6. Cobbled Horizon integration

### Inspected baseline

The pinned pack has 33 active exact project pins. Relevant selections include Towns and Towers 1.13.13, Epic Villages 1.0.0, Explorify 1.6.6, Hopo Better Mineshaft 1.3.8, DnT Stronghold Overhaul 3.0.1, MSS 2.2.0, MOS 1.1.1 and Moog's Structure Lib 3.4.2; Cristel Lib participates in structure policy. This is not a census of the live world's historical generation versions.[2]

Relevant surrounding systems are Naturally Trimmed 3.6.1, Universal Graves, Server-Side Waystones, Polymer 0.18.6+26.3, Fabric API 0.165.0+26.3, Geyser 2.12.1-b1281, Floodgate 2.2.7-b69, LuckPerms, Lithium, ServerCore, spark, Chunky and JEB. Existing baselines are not proof of the new mod's mixin compatibility or real Bedrock behavior.[2][5]

**Static experiment performed:** nine exact pinned JARs were downloaded and matched to repository SHA-512 pins. Their ZIP inventories and structure NBT were parsed without running mod code. The seven structure-content archives have data/template resources and no Java classes; Moog's library and Naturally Trimmed contain code. The recorded [artifact and template audit](loot-investigation-evidence.json) describes file counts as raw archive resources, **not distinct structures generated in Broadwater**.[75][82][83]

Examples from the parsed pinned templates:

- Towns and Towers contains table-backed ordinary/trapped chests and barrels, plus prefilled chests/barrels and deliberately empty storage. `kaisyn:outpost/exclusives/outpost_beach_barrel` is an actual custom table reference; not all loot lives in `minecraft:chests/*`.[75]
- Epic villages and Explorify likewise include table-backed and empty/prefilled cases; emptiness is not an adequate natural-loot classifier.[76][77]
- Hopo templates use table IDs such as `hopo:chests/mineshaft/big_rooms/archer` and `hopo:chests/mineshaft/base/archer`. DnT uses `nova_structures:chests/stronghold/library_eye` and also has a prefilled manufacturing-room chest.[78][79]
- MSS and MOS contain table-backed barrels as well as chests, including `mss:general` and `mos:ships/small_ship_stores`; barrels cannot be omitted from the trial.[80][81]

These are parsed archive examples; overlays, processors, resource priority and actual placement remain runtime concerns. No claim is made that every archived template is active or placed.

Naturally Trimmed's inspected source registers a Fabric loot-table modification function. Personal rolls should use the server's active registry/table pipeline, not copy vanilla JSON or bypass the modifier. Its source revision is not proven identical to the pinned JAR; verify trimmed loot in the full-stack trial.[84][83]

Do not mistake graves, storage-related helper blocks, player vaults or Waystones for natural loot simply because they use vanilla-looking blocks or Polymer. Keep unknown/custom containers excluded until their ownership and menu contracts have been individually traced. There is no new custom storage mod required by the recommended first trial.

### Dependencies, configuration and Packwiz

- SlashLoot's declared Loader/Java/Fabric API requirements are within the inspected branch's versions; that is a metadata comparison, not a mixin/boot pass. It requires no automatic Polymer upgrade.[1][2][10]
- Fair Loot has a public release asset but no native Modrinth version established here. A later Packwiz integration must use a verified supported CurseForge/GitHub/URL mechanism and adjust the repository's current Modrinth-identity validation deliberately, rather than invent a Modrinth ID or bypass checks.[44][5]
- Lootr/Patch adds dependency and registry-conversion complexity. The pack's Polymer 0.18.6 and Patch's bundled 0.18.2 components require actual loader resolution testing; neither automatic conflict nor compatibility follows from the two version strings.[29][2]
- Approved future integration would update `collection.toml`, exact `.pw.toml` pins, applicable distribution/notice records and only required dependency closure/config, then use maintained Packwiz refresh/validation/export. No such changes were made here.[5]
- A historical-source manifest cannot simply be injected into `slashloot.dat`: the current interaction classifier still requires the live table marker. Recovery needs an explicit supported source resolver/API or a narrowly reviewed upstream extension that is shared by all relevant handlers.[11][12]

Use explicit table/dimension scope, keep unknown-container handling off, and disable timed refresh. Do not infer that all rare progression tables should be renewable. Blocklists alone are not ownership proof. Review deletion/pruning, inventory insertion, automation, creative/sneak bypasses, explosion effects and removal before calling the system safe.

### Existing delivery convention

Maintained entrypoints are `make validate`, `make test`, Packwiz refresh/export, the no-JAR mrpack/checksum contract, and exact-head hosted `validate`/`native-acceptance` jobs. Runtime boot/restart checks are distinct from real Java/Bedrock, gameplay and restore acceptance. Tag publication and production deployment are separate permissions. This documentation-only investigation changes none of those policies or the pack version.[5][6]

## 7. Required scenario matrix

For existing 26.3 candidates, “yes” below means source-supported behavior, **not a gameplay pass**. CS = ChestShare+ 1.21.1 reference design, not an installable 26.3 option. Remaining empirical tests use a purpose-built world or separately authorized copy, never Broadwater live.

| Scenario | Current evidence/result | Required discriminating isolated test |
|---|---|---|
| Newly generated unopened chest | S/A: SlashLoot/Fair/Lootr can individualize surviving tables; FreshLoot rotates singles; Restock tracks shared refills.[11][41][32] | Two distinct players take different personal inventories; same player reopens without new entitlement. |
| Existing chunk, never-unpacked chest | S: table-based paths do not require post-install generation. Lootr still has loaded-chunk conversion conditions.[11][32] | Generate and save **before** installing candidate; cold-start, then first open. |
| Existing chunk, opened and emptied chest | S: audited 26.3 candidates do not recover missing tables. CS can reconstruct some recognized template semantics, unsafely if used indiscriminately.[11][54] | Open/drain/save/restart without candidate first; prove metadata gone before attempting recovery. |
| Existing chunk, partial loot or deposited items | S: table-gated candidates leave pre-cleared physical storage alone. CS explicit adoption clears slots and is forbidden.[41][53] | Compare full item components/counts/slots before and after installation, recovery planning, denied apply and restart. |
| Previously looted barrel | Same metadata-loss problem; template matching can nominate a site, not establish ownership.[11][54] | Pre-loot and drain barrel before install; test both an untouched empty barrel and a player replacement. |
| Chest minecart | S: SlashLoot and Lootr cover intact-table vehicle paths; Restock supports carts; Fair/Fresh no such path established. CS documents carts, but block-template recovery is not mobile-entity recovery.[10][35][52] | Move cart, unload/reload/restart, break/recreate; verify UUID identity and no repeat-claim reset. |
| Player-placed chest/barrel | S: no-table ordinary storage is excluded by main 26.3 candidates. Empty table-backed or same-position replacement is not a certified natural object.[11][41] | Empty and filled storage inside/outside structures, replacements at exact expected coordinates, and merged double chests. |
| Structure modified by player | No general reliable archaeological classifier; CS same-block false positive remains.[54] | Alter palette, move/remove container, create nearby storage and replace the exact target; planner rejects uncertainty. |
| Modded structure, vanilla loot container | A/P: pinned structure archives demonstrably contain vanilla chests/barrels with custom table IDs; runtime interaction U.[78][81] | Test representative village, mineshaft, stronghold, aerial and ocean tables plus one prefilled/empty decorative case. |
| Modded container implementation | S: SlashLoot limited recognition/default fallback; Lootr providers; CS has 1.21.1 integrations. No blanket 26.3 pass.[11][32][52] | Only explicitly scoped classes; confirm normal storage is not intercepted. |
| Java, no client mod | D/S/A: vanilla menu design or Patch intent. P/U: no real client test.[10][48][38] | Clean vanilla Java client, concurrent opens, shift-click, drag, reconnect, double chest and blocked/locked container. |
| Bedrock through Geyser/Floodgate | U for every proposed candidate. Server-only is not cross-play evidence. | Real Bedrock client through exact bridge pins; distinct player views, slot sync, movement, claim identity and account-link behavior. |
| Server restart | S: persistent formats inspected; gameplay durability U.[13][41][33] | Claim partially, deposit a marked item, clean save/restart; then controlled interrupted-save recovery on disposable data. |
| Mod removal | S: private inventories are not vanilla-readable; Lootr also converts world IDs. Lossless removal U.[13][33][46] | Export/escrow all player-owned leftovers first; cold-remove candidate and verify blocks, items, accounting and no fresh-roll loophole. |

Additional negatives: hopper/hopper-minecart extraction and insertion, comparator/trapped-chest signals, explosions/pistons/fire, chunk borders/unloaded neighbors, concurrent opens and full player inventories. Baseline the same interactions without the mod. Save/copy tests must include ledger, entity/chunk data and player inventory together.

## 8. Recommended architecture and smallest implementation

### Scope choice

**Preferred: existing mod + a source-level extension**, preferably upstreamable to SlashLoot. Use the existing engine for intact table-backed sources; add an explicit, audited historical reward source independent of the physical container's consumed `LootTable` field. This is a proposed capability, not an available extension API.[11][12]

**Engine boundary, still to prove:** current SlashLoot gates on the live marker and keys inventories by block position or entity UUID, not the proposed immutable historical-source ID.[11][13] A manifest therefore needs an upstream engine change or a narrow reviewed fork sharing the source resolver, identity/store/menu path and cleanup rules. It is not a data-file import or an established drop-in compatibility module. If that seam cannot be kept small, a separate finite-source claim utility is an alternative, but it owns its own menu, inventory persistence and transaction/export behavior; it is not cost-free reuse. Run a bounded API/architecture spike before fixing its implementation estimate.

Start with a manually nominated finite source manifest. A generic whole-world archaeology scanner is not necessary to demonstrate useful retrospective rewards, and would dominate complexity. Later structure/template resolution may create proposals, never silently authorize adoption.

### Minimum contracts

**These are extension acceptance criteria, not properties already verified in SlashLoot or any other candidate.**

1. **Read-only plan.** An operator selects finite regions or coordinates on a copy. Record dimension/position or immutable source ID, structure piece/template/palette/transform, donor/backup provenance, table identifier, current block/entity type and complete physical inventory fingerprint, plus why it is approved or rejected. No world generation, block placement, table unpacking or dirty marking during planning. A normal inventory getter can itself unpack pending loot: use safe serialized inspection.
2. **Explicit approval.** Approve a frozen plan digest and exact source entries. No casual `force`; unknown identity, mismatched block/palette, non-empty physical inventory, foreign dimension/world, missing table, malformed data or changed preimage rejects apply. Never infer permission from a structure bounding box.
3. **Additive rewards, not physical rewrites.** Persist a sidecar source definition and player-claim ledger; do not replace blocks, clear slots, restore `LootTable` NBT, move terrain or copy donor regions. For a confirmed enrolled empty source, an explicit reward interaction may expose its virtual inventory while preserving ordinary storage access. For uncertain/partial/player-owned storage, leave normal interaction entirely unchanged; any approved compensation uses a separate claim command/menu.
4. **Stable identity and no repeated enrollment.** Key by world identity + dimension + immutable approved source ID + migration version, not just current block coordinates or table name. Track each player once per source. Block/entity removal/replacement after enrollment tombstones the source; moving a cart or re-importing a manifest must not create another entitlement. Pre-install ownership remains unknown even with these prospective guards.
5. **Durable, bounded state.** Prefer one established inventory engine if the source-level hook is viable; a standalone fallback must explicitly own its separate finite-source store/menu instead of pretending that reuse exists. Cap plan size, validation work per batch, query scope and audit retention; no tick-time whole-world/template scan and no automatic chunk generation. Store complete stack components. Treat ledger decode/write failures as disabled claims requiring recovery, not an empty ledger that grants fresh loot.
6. **Items and accounting.** Prefer withdraw-only reward menus in the minimum implementation so player deposits cannot become orphaned. Persist roll/remaining inventory and claim changes with a documented transaction/recovery model. A server crash between player inventory and ledger saves can duplicate or lose items; atomic replacement of one file alone is not the solution. Test/reconcile interrupted operations and keep full-state backups.
7. **Recovery and removal.** Keep audit receipts for source registration, claims, denials and tombstones. Require a tested export/escrow path for **all players' remaining private stacks** before deleting, pruning, resetting, expiring or removing private data; block marker loss/replacement and entity destruction must not silently bypass it. Rollback must restore a consistent player+world+reward snapshot or use a compensating transaction; simply restoring the loot ledger after rewards entered player inventories duplicates items. No silent history rewrites or cleanup of inventories still holding player items.

A table plus a stored seed defines a new repeatable reward policy; exact original contents are not promised. Existing players may have their original loot and receive the new entitlement as well. Agree whether that is acceptable once, whether known historical claim records should be imported, and whether rare tables need reduced substitute rewards. Never pretend absent vanilla looter records prove someone has not collected loot.

### Reuse and maintenance tradeoff

Prefer a supported upstream registration/resolution hook that shares one classifier across cancellation, menu creation and cleanup. The current classifier's table requirement makes a data-only injection insufficient. If a stable hook cannot be provided without invasive mixins/private-SavedData mutation, compare a small independent **approved-source claim utility** with maintaining a private fork; do not promise a tiny drop-in plugin.[11][13]

Keep automatic template reconstruction optional in the first slice. This reduces the six-month maintainer burden: one rewards engine, a small manifest format and explicit source lifecycle, rather than a second generalized world-generation engine. Existing-world uncertainty stays visible instead of being hidden inside a confidence score.

## 9. Roadmap, risks and effort

### Next sequence before changing the pack

1. **Discriminating candidate trial:** on a purpose-built disposable 26.3 world, first create/save/restart new/unopened, old/unopened, old/drained, old/partial and player-replacement controls **without** a loot mod. Preserve their preimages. Then trial the exact SlashLoot artifact and existing full dependency composition; compare Fair Loot separately if needed. Do not install both at once.
2. Exercise two unmodded Java accounts and a real Bedrock account through the pinned Geyser/Floodgate path. Confirm stable account identity; do not change Floodgate/linking/online-mode policy to make tests pass. Test all selected structures/tables, containers, automation, break/explosion and restart/removal cases above.
3. Reject a candidate that loses remaining/deposited items, silently resets claims after load failure, interferes with ordinary storage, or cannot provide a viable uninstall/escrow policy. Report the actual failure rather than increasing unsafe defaults.
4. If intact-container trials pass, design the minimal explicit-source extension and its read-only planner. First prove two historic emptied containers can receive independent once-per-player rewards **without any physical NBT/slot/terrain change**, while an identical replacement, partial storage and an ambiguous template are rejected or use detached approved compensation.
5. Only after that review, separately authorize inspection of a **stopped, consistent copy** of Broadwater and available historical backups/generation manifests. Determine actual recoverable coverage; this research cannot supply a percentage. Protect player identifiers and private world data outside Git/public evidence.
6. Obtain explicit balance/migration approval, verified backups and restore rehearsal before any live enrollment. A later pack PR follows the existing review, Packwiz, artifact and hosted/native gates; production rollout remains a separate operation.[5]

### Risk register

| Risk | Consequence | Required mitigation / current status |
|---|---|---|
| False natural-container classification | Player storage captured or UI altered | No automatic empty-in-structure sweep; exact proposals, explicit approval, no physical writes, detached rewards for uncertainty. Historical certainty cannot be manufactured. |
| Existing remainder/deposited-item loss | Items dropped, cleared, expired or orphaned | Exclude non-empty physical adoption; withdraw-only minimum; never reset/delete private copies with items; escrow/export and adversarial lifecycle tests. FreshLoot/CS destructive routes rejected. |
| New shared roll after mod removal | Duplicate resources, inaccessible personal leftovers | Freeze claims, reconcile/export first; test rollback/removal. Vanilla block readability alone is insufficient. |
| Ledger corruption or interrupted save | Fresh rerolls, duplicate/lost inventory | Fail closed; versioned schema, validated backups and whole-operation recovery tests. Fair Loot's reroll-on-load-error behavior is a specific concern.[41] |
| Historical generator mismatch | Wrong source coordinates/table/reward | Record generation-era evidence and exact active resources; treat donor results as proposals. No terrain/chunk copying. |
| Exploit via identities/movement/reset | Repeat rare-loot claims | Stable authenticated UUID semantics, immutable source ID, tombstones, restricted reset/import permissions and duplicate-manifest tests. |
| Scan/storage growth | Tick stalls, large saves/backups | Bounded regions/batches; index templates once, no global per-open scan; measure player-source pairs, serialized stack bytes, save latency and backup size. No benchmark was run here. |
| Client/protocol or mixin conflict | Join failure, desync or lost transfers | Exact full-stack Java/Bedrock trial. Metadata and Polymer intent do not establish interoperability. |
| World upgrade/removal failure | Stranded custom IDs/data | Prefer vanilla-block approach; preserve full snapshot, exact mod versions and explicit export/restore path. No vanilla corruption/removal test passed yet. |

### Conditional effort estimates

These are engineering estimates, **not measured delivery promises**. Assume one developer familiar with current Fabric, an independent reviewer, available unmodded Java/Bedrock testers, an approved test host and no major upstream defects. Developer days exclude player coordination and large-world generation/review time; ranges are alternatives, not additive totals.

| Slice / alternative | Rough effort | Scope and uncertainty |
|---|---|---|
| Exact SlashLoot full-stack discrimination trial | 1–3 developer days plus client/tester availability | No production installation. Capture the negative controls and item/removal lifecycle, not only a successful boot. |
| API/architecture spike | 1–2 developer days | Determine an upstream hook or narrow-fork boundary; prove identity/store/menu and non-destructive cleanup fit before calling implementation small. |
| Manual approved-source manifest + narrow source-level engine extension | 5–10 developer days after the spike | Includes persistence, idempotency, denied cases, audit and review. Contingent on an accepted upstream hook or maintainably small reviewed fork; otherwise re-estimate. Standalone UI/transactions/export are not included by assumption. |
| Template-aware proposal planner for selected pack families | 5–10 additional developer days | Known palettes/pieces only, copy/offline scope, no claim of universal identification. Broader procedural/custom support can exceed this substantially. |
| Same-seed donor experiment | 2–5 developer days plus generation/IO time | Reconstruct a bounded region and compare expected metadata; historical environment availability is the main unknown. |
| Port ChestShare+ wholesale | Several weeks, plausibly 15–30+ developer days | 1.21.1→26.3 API/storage work, destructive recovery redesign, component fidelity, integrations and removal tests. Not the minimal path. |
| Standalone custom personal-loot engine | 15–30+ developer days | Duplicates menu/automation/state/lifecycle work already present upstream. Justify only if existing engines fail explicit safety gates. |
| Existing mod only | Trial effort plus ordinary pack review | Helps intact sources, **does not** deliver arbitrary already-looted recovery. Cannot be presented as meeting the whole objective. |

### Final answer

**Conditionally yes: nominated already-looted locations can receive new, policy-approved virtual reward entitlements without chunk resets or terrain edits—not recovered historical rewards and not a universally safe automatic recovery inference.** Existing target-version mods address intact containers. The smallest credible addition is an explicitly approved historical-source manifest and non-destructive virtual reward enrollment, with read-only template/backup/donor evidence where available. Unknown or player-owned storage must remain untouched, and exact old randomized contents/looter history cannot be promised when their records are gone.

**Test next:** the exact SlashLoot build on purpose-built old-state controls, including a real Bedrock client and item-preserving removal. Then review a minimal explicit-source extension if that engine passes. Do not install ChestShare+, run its adoption/import commands, add production pins or modify Broadwater as a result of this investigation.

## Research verification record

- Executed `make validate` on the inspected documentation worktree: permission-seed, release-metadata and pack checks passed; 27 selected projects + 6 dependencies and 63 indexed pack files remained unchanged. This was source validation, not a game boot.
- Exact-artifact checks, static ZIP/template-NBT parsing and primary container-bytecode inspection were performed. Published artifact identity is kept separate from upstream source inspection.
- A focused independent review of the first frozen report checked the preservation conclusion and selected SlashLoot/Fair Loot/ChestShare+ source paths. Its requested engine-boundary, cleanup/export and historical-entitlement qualifications are incorporated here. Exact-official-JAR evidence closes its earlier vanilla-method gap. Review scope was not exhaustive replay of every source.
- Citation mapping and retained capture hashes were checked. Citation-marker statistics do not establish semantic support, and no arbitrary prose-coverage threshold is used.
- No pack pin, runtime configuration, world, production service, release or target branch was changed. No Java/Bedrock gameplay, load/restart under player activity, recovery apply, performance benchmark, cold restore or lossless uninstall passed in this research. Those gates remain explicit.

## Sources

[1] https://github.com/vice-magus-faolan/cobbled-horizon/blob/ad603ee5191987e74d2a544a7c6cde4b0058009f/pack.toml
[2] https://github.com/vice-magus-faolan/cobbled-horizon/blob/ad603ee5191987e74d2a544a7c6cde4b0058009f/collection.toml
[5] https://github.com/vice-magus-faolan/cobbled-horizon/blob/ad603ee5191987e74d2a544a7c6cde4b0058009f/docs/version-policy.md
[6] https://github.com/vice-magus-faolan/cobbled-horizon/blob/ad603ee5191987e74d2a544a7c6cde4b0058009f/.github/workflows/validate.yml
[8] https://api.modrinth.com/v2/project/slashloot/version
[9] https://api.modrinth.com/v2/project/slashloot
[10] https://raw.githubusercontent.com/slashdaemon/SlashLoot/a565d5165e475a7520c2623a9498965d4609b244/README.md
[11] https://raw.githubusercontent.com/slashdaemon/SlashLoot/a565d5165e475a7520c2623a9498965d4609b244/mc-src/src/main/java/dev/blockacademy/slashloot/core/Handling.java
[12] https://raw.githubusercontent.com/slashdaemon/SlashLoot/a565d5165e475a7520c2623a9498965d4609b244/mc-src/src/main/java/dev/blockacademy/slashloot/handler/ContainerInteractionHandler.java
[13] https://raw.githubusercontent.com/slashdaemon/SlashLoot/a565d5165e475a7520c2623a9498965d4609b244/compat/store-codec/src/main/java/dev/blockacademy/slashloot/store/SlashLootState.java
[14] https://raw.githubusercontent.com/slashdaemon/SlashLoot/a565d5165e475a7520c2623a9498965d4609b244/LICENSE
[15] https://api.github.com/repos/slashdaemon/SlashLoot
[16] https://api.modrinth.com/v2/project/jahus-freshloot/version
[17] https://raw.githubusercontent.com/DarthJahus/minecraft-freshloot/a8da801c5dfa1bf1225b875778a9915d771934f8/src/main/java/net/jahus/freshloot/LootContainerHandler.java
[18] https://raw.githubusercontent.com/DarthJahus/minecraft-freshloot/a8da801c5dfa1bf1225b875778a9915d771934f8/src/main/java/net/jahus/freshloot/LootRegistry.java
[19] https://raw.githubusercontent.com/DarthJahus/minecraft-freshloot/a8da801c5dfa1bf1225b875778a9915d771934f8/LICENCE.md
[20] https://api.github.com/repos/DarthJahus/minecraft-freshloot
[21] https://api.modrinth.com/v2/project/lootrestock/version
[22] https://raw.githubusercontent.com/Quackster/LootRestock/cdc10143ce17fb3b889d6dff278eb9cb52b362cf/src/main/java/org/oldskooler/lootrestock/handler/ChestResetHandler.java
[23] https://raw.githubusercontent.com/Quackster/LootRestock/cdc10143ce17fb3b889d6dff278eb9cb52b362cf/src/main/java/org/oldskooler/lootrestock/data/ChestDataManager.java
[24] https://raw.githubusercontent.com/Quackster/LootRestock/cdc10143ce17fb3b889d6dff278eb9cb52b362cf/src/main/java/org/oldskooler/lootrestock/config/ModConfig.java
[25] https://raw.githubusercontent.com/Quackster/LootRestock/cdc10143ce17fb3b889d6dff278eb9cb52b362cf/LICENSE
[26] https://api.github.com/repos/Quackster/LootRestock/issues?state=all&per_page=100
[27] https://cdn.modrinth.com/data/ddaWpjKK/versions/M5kTZo9M/LootRestock-1.0.3-26.3.jar
[28] https://api.modrinth.com/v2/version/gVwn7m2v
[29] https://api.modrinth.com/v2/version/DMk4xzkH
[30] https://api.modrinth.com/v2/project/lootr
[31] https://api.modrinth.com/v2/project/lootr-polymer-patch
[32] https://raw.githubusercontent.com/noobanidus/Lootr/2a9c8307460e3ff5765ecd849b11a6faf06dfe8b/common/src/main/java/noobanidus/mods/lootr/common/block/entity/BlockEntityTicker.java
[33] https://raw.githubusercontent.com/noobanidus/Lootr/2a9c8307460e3ff5765ecd849b11a6faf06dfe8b/common/src/main/java/noobanidus/mods/lootr/common/data/DataStorage.java
[34] https://raw.githubusercontent.com/noobanidus/Lootr/2a9c8307460e3ff5765ecd849b11a6faf06dfe8b/common/src/main/java/noobanidus/mods/lootr/common/api/config/LootrCommonConfig.java
[35] https://raw.githubusercontent.com/noobanidus/Lootr/2a9c8307460e3ff5765ecd849b11a6faf06dfe8b/fabric/src/main/java/noobanidus/mods/lootr/fabric/mixin/ticker/MixinPersistentEntitySectionManager.java
[36] https://raw.githubusercontent.com/noobanidus/Lootr/2a9c8307460e3ff5765ecd849b11a6faf06dfe8b/LICENSE
[37] https://raw.githubusercontent.com/T0RNATO/lootr-polymer/688007ce5ea6aeb5edee52a9ba140651d601259b/LICENSE.txt
[38] https://raw.githubusercontent.com/T0RNATO/lootr-polymer/688007ce5ea6aeb5edee52a9ba140651d601259b/src/main/java/tornato/lootr/mixin/ModBlocksMixin.java
[39] https://api.github.com/repos/T0RNATO/lootr-polymer/issues/11/comments
[40] https://api.github.com/repos/T0RNATO/lootr-polymer
[41] https://raw.githubusercontent.com/BackupBackupFede/fair-loot/1e8ffacfd868a54bad6a959d9226f3ca7069a194/common/src/main/java/net/emeraude/fairloot/Instancing.java
[42] https://raw.githubusercontent.com/BackupBackupFede/fair-loot/1e8ffacfd868a54bad6a959d9226f3ca7069a194/common/src/main/java/net/emeraude/fairloot/core/Ledger.java
[43] https://raw.githubusercontent.com/BackupBackupFede/fair-loot/1e8ffacfd868a54bad6a959d9226f3ca7069a194/LICENSE
[44] https://api.github.com/repos/BackupBackupFede/fair-loot/releases/tags/v0.1.0
[45] https://api.github.com/repos/BackupBackupFede/fair-loot
[46] https://raw.githubusercontent.com/BackupBackupFede/fair-loot/1e8ffacfd868a54bad6a959d9226f3ca7069a194/README.md
[47] https://raw.githubusercontent.com/BackupBackupFede/fair-loot/1e8ffacfd868a54bad6a959d9226f3ca7069a194/common/src/main/java/net/emeraude/fairloot/core/Config.java
[48] https://github.com/BackupBackupFede/fair-loot/releases/download/v0.1.0/fairloot-fabric-26.3-0.1.0.jar
[49] https://www.curseforge.com/api/v1/mods/1694851/files/8985900
[50] https://api.github.com/repos/PsycloneTM/ChestShare-plus/releases?per_page=100
[51] https://raw.githubusercontent.com/PsycloneTM/ChestShare-plus/3649476248db0b90c94b265909eab1999fc191e0/LICENSE
[52] https://raw.githubusercontent.com/PsycloneTM/ChestShare-plus/3649476248db0b90c94b265909eab1999fc191e0/README.md
[53] https://raw.githubusercontent.com/PsycloneTM/ChestShare-plus/3649476248db0b90c94b265909eab1999fc191e0/src/main/java/dev/chestshare/ContainerRegistrar.java
[54] https://raw.githubusercontent.com/PsycloneTM/ChestShare-plus/3649476248db0b90c94b265909eab1999fc191e0/src/main/java/dev/chestshare/StructureContainerRestorer.java
[55] https://raw.githubusercontent.com/PsycloneTM/ChestShare-plus/3649476248db0b90c94b265909eab1999fc191e0/src/main/java/dev/chestshare/compat/FingerprintRegistry.java
[56] https://raw.githubusercontent.com/PsycloneTM/ChestShare-plus/3649476248db0b90c94b265909eab1999fc191e0/src/main/java/dev/chestshare/compat/StructureAligner.java
[57] https://raw.githubusercontent.com/PsycloneTM/ChestShare-plus/3649476248db0b90c94b265909eab1999fc191e0/src/main/java/dev/chestshare/command/ChestShareCommands.java
[58] https://raw.githubusercontent.com/PsycloneTM/ChestShare-plus/3649476248db0b90c94b265909eab1999fc191e0/src/main/java/dev/chestshare/command/ImportJob.java
[59] https://raw.githubusercontent.com/PsycloneTM/ChestShare-plus/3649476248db0b90c94b265909eab1999fc191e0/src/main/resources/fabric.mod.json
[60] https://api.github.com/repos/PsycloneTM/ChestShare-plus
[61] https://raw.githubusercontent.com/slashdaemon/SlashLoot/a565d5165e475a7520c2623a9498965d4609b244/mc-src/src/main/java/dev/blockacademy/slashloot/store/LootImport.java
[62] https://api.modrinth.com/v2/version/JqOZeLvz
[63] https://raw.githubusercontent.com/Fayberr/unlimited-trial-vaults/90d2274da815f2d7cf1bd5946621e1ff508d0c8f/src/main/java/net/fayber/unlimitedtrialvaults/ModConfig.java
[64] https://raw.githubusercontent.com/Fayberr/unlimited-trial-vaults/90d2274da815f2d7cf1bd5946621e1ff508d0c8f/src/main/java/net/fayber/unlimitedtrialvaults/mixin/VaultServerDataMixin.java
[66] https://api.modrinth.com/v2/project/caaezIQ8
[67] https://api.modrinth.com/v2/project/caaezIQ8/version
[68] https://api.modrinth.com/v2/project/gycZJL9N
[69] https://api.modrinth.com/v2/project/personal-treasure-loot/version
[70] https://api.modrinth.com/v2/project/79PHFfQM/version
[71] https://api.modrinth.com/v2/project/sv1q6VzG/version
[73] https://piston-meta.mojang.com/v1/packages/ead839cbccf0ddf013c3f935f2840080b5cb0d26/26.3.json
[74] https://piston-data.mojang.com/v1/objects/33680f5f2ac32864d6d7cf5e56a705fdb3e05f4c/server.jar
[75] https://cdn.modrinth.com/data/DjLobEOy/versions/vHZIKy6e/t_and_t-fabric-neoforge-1.13.13.jar
[76] https://cdn.modrinth.com/data/3PvUBn3u/versions/OD6SDuW4/epic-structures-villages-standalone-edition-1.0.0.jar
[77] https://cdn.modrinth.com/data/HSfsxuTo/versions/oyrAnNG8/Explorify%20v1.6.6.mod.jar
[78] https://cdn.modrinth.com/data/9IxCUYAP/versions/avIdkeZp/HopoBetterMineshaft-%5B26.3%5D-1.3.8.jar
[79] https://cdn.modrinth.com/data/rYocd2LE/versions/hNKbQ85c/dungeons-and-taverns-stronghold-overhaul-3.0.1.jar
[80] https://cdn.modrinth.com/data/RJCLIx7k/versions/O20bIWkj/MoogsSoaringStructures-universal-1.21-2.2.0.jar
[81] https://cdn.modrinth.com/data/ZKBkklMv/versions/QfMITqh9/MoogsOceanStructures-universal-1.21-1.1.1.jar
[82] https://cdn.modrinth.com/data/1oUDhxuy/versions/SkD4H9XM/MoogsStructureLib-fabric-26.3-3.4.2.jar
[83] https://cdn.modrinth.com/data/hHVaPgFK/versions/h3K7LsVB/naturally_trimmed-3.6.1%2B26.3-fabric.jar
[84] https://raw.githubusercontent.com/Imajo24I/Mob-Armor-Trims-1.20.1/fb11a11ff9ff2c781a68975384c36d027f6bffcc/src/main/java/net/majo24/naturally_trimmed/Events.java
[85] https://api.modrinth.com/v2/project/lootrestock
[86] https://api.modrinth.com/v2/project/jahus-freshloot
[87] https://mc-packet-reference.netlify.app/26.x/source/net/minecraft/world/level/block/entity/randomizablecontainerblockentity
[88] https://mc-packet-reference.netlify.app/26.x/source/net/minecraft/world/level/block/entity/hopperblockentity
[89] https://mc-packet-reference.netlify.app/26.x/source/net/minecraft/world/level/levelgen/structure/structurestart
[90] https://mc-packet-reference.netlify.app/26.x/source/net/minecraft/world/level/levelgen/structure/structurepiece
[91] https://mc-packet-reference.netlify.app/26.x/source/net/minecraft/world/level/levelgen/structure/templatestructurepiece
[92] https://mc-packet-reference.netlify.app/26.x/source/net/minecraft/world/level/levelgen/structure/templatesystem/structuretemplate
[93] https://raw.githubusercontent.com/slashdaemon/SlashLoot/a565d5165e475a7520c2623a9498965d4609b244/mc-src/src/main/java/dev/blockacademy/slashloot/handler/CleanupHandler.java
[94] https://raw.githubusercontent.com/slashdaemon/SlashLoot/a565d5165e475a7520c2623a9498965d4609b244/mc-src/src/main/java/dev/blockacademy/slashloot/command/SlashLootCommand.java
