# Cobbled Horizon

A reproducible, server-side Fabric collection for a Vanilla+ Minecraft world focused on performance, exploration, and restrained quality-of-life improvements.

The current baseline targets **Minecraft Java 26.2** with **Fabric Loader 0.19.5**. It contains 26 deliberately selected projects plus six dependencies resolved by packwiz. Just Enough Backups (JEB) replaces the obsolete Textile Backup candidate.

Java players should not need this pack on their clients: every packwiz entry is marked `side = "server"`. Bedrock access is provided by Geyser and Floodgate and still requires a reachable UDP port on the host.

### Compare active pins offline

With both refs already present locally, run:

```bash
python3 scripts/branch_delta.py 26.2 26.3
```

The read-only command freezes both refs to commits and emits complete, deterministic JSON
`REMOVED`, `ADDED`, `UPDATED` and `UNCHANGED` groups with counts, exact input commits,
Minecraft/loader versions and before/after pin records. Projects match by Modrinth project
ID, including resolved libraries. An update means an exact pin-record change, not merely
a different display name or metadata pathname; a changed version ID or hash still counts
when the JAR filename stays the same. Display labels and metadata paths remain visible.
Staged/future candidates and configuration changes are excluded. This is a lock comparison,
not compatibility evidence or synchronization. It never fetches, checks out, or writes;
unresolved/option-like refs and malformed, duplicate or missing identities fail without
partial JSON. Use `--repository PATH` to read another local repository.

## Included collection

### Platform and cross-play

- Fabric API
- Polymer *(dependency)*
- Cristel Lib *(dependency)*
- Cloth Config API *(dependency of Cristel Lib)*
- Forge Config API Port *(dependency of Crops Love Rain)*
- LuckPerms
- Geyser
- Floodgate

### Performance and administration

- Lithium
- FerriteCore
- Alternate Current
- ServerCore
- spark
- Chunky
- squaremap
- Just Enough Backups (JEB)

### Quality of life and exploration

- [Server-Side Waystones](https://modrinth.com/mod/sswaystones)
- [Universal Graves](https://modrinth.com/mod/universal-graves)
- [Creeper No Break Blocks](https://modrinth.com/mod/creeper-no-break-blocks)
- [Naturally Trimmed](https://modrinth.com/mod/naturally-trimmed)
- [Crops Love Rain](https://modrinth.com/mod/crops-love-rain)
- [Villager Names](https://modrinth.com/mod/villager-names-serilum)
- [Villagers Tasks](https://modrinth.com/mod/villagers-tasks)
- Collective *(dependency of Villager Names)*
- [Towns and Towers](https://modrinth.com/mod/towns-and-towers)
- [Epic Structures: Villages Standalone Edition](https://modrinth.com/mod/epic-structures-villages-standalone-edition)
- [Explorify](https://modrinth.com/mod/explorify)
- [Hopo Better Mineshaft](https://modrinth.com/mod/hopo-better-mineshaft)
- [Dungeons and Taverns Stronghold Overhaul Lite](https://modrinth.com/mod/dnt-stronghold-overhaul-lite-edition)
- [Moog's Soaring Structures](https://modrinth.com/mod/mss-moogs-soaring-structures)
- [Moog's Ocean Structures](https://modrinth.com/mod/mos-moogs-ocean-structures)
- Moog's Structure Lib *(dependency)*

Exact baseline project IDs, version IDs, download URLs, and SHA-512 hashes live in `mods/*.pw.toml`. All entries are pinned.

### Staged and future candidates

Krypton, Fast Noise with ZConfig, ScalableLux, and Spiral Tower Villages retain pinned metadata under `staged/`, but they are excluded from the baseline export. C2ME, VMP, Clumps, Ledger, Sparse Structures, and ChoiceTheorem's Overhauled Village (CTOV) are future candidates with explicit activation gates in [`candidates.toml`](candidates.toml). Spiral Tower Villages is the preferred next village addition, ahead of CTOV. Ledger is intentionally absent from launch: its proposed bounded MySQL deployment is documented in [`docs/storage-and-recovery.md`](docs/storage-and-recovery.md).

## Intent versus dependency closure

Packwiz writes the same `.pw.toml` shape for a project whether it was selected directly or pulled in as a dependency. Removing a resolved dependency's metadata would make the exported pack incomplete, so the distinction should not be encoded by deleting or relocating those files.

This repository keeps the two concerns separate:

- [`collection.toml`](collection.toml) defines the active baseline: 26 selected projects and six resolved dependencies.
- [`candidates.toml`](candidates.toml) defines staged and future projects, why they are inactive, and the evidence required to promote them.
- `mods/*.pw.toml` is the machine-maintained baseline lock layer. It contains the 32 projects exported by the standard pack.
- `staged/mods/*.pw.toml` retains five pinned candidate records outside packwiz's active index.

Fabric API is the only explicitly selected platform library. Polymer, Cristel Lib, Cloth Config API, Forge Config API Port, Moog's Structure Lib, and Collective close baseline dependencies. ZConfig is staged beside Fast Noise. Cristel Lib demonstrates why dependency chains matter: Towns and Towers requires Cristel Lib, which in turn requires Cloth Config API and Fabric API. Crops Love Rain requires Forge Config API Port and Fabric API. Villager Names requires Collective.

`scripts/check_pack.py` verifies that both layers agree, so a dependency cannot silently disappear or become an undeclared top-level choice.

## Initial policy choices

- Geyser uses Floodgate authentication; generated Floodgate keys are never committed.
- ServerCore's non-vanilla-parity optimizations remain disabled.
- Naturally Trimmed uses only vanilla trim materials and patterns. Trimmed equipment remains uncommon: 75% of eligible mobs receive no trims, each remaining armor piece has a 35% chance, loot uses 15%, and level-three-or-higher trades use 10%.
- Crops Love Rain gives directly rain-exposed crops and cocoa a 1-in-10 extra-stage chance per applicable random tick; slower-growing plants use 1-in-15. Bamboo's rain bonus is disabled because the mod checks global rain rather than direct exposure for bamboo.
- Moog's spacing is scoped by namespace: Soaring Structures uses `2.0`, while Ocean Structures uses `3.0`. The universal multiplier remains `1.0` so future Moog packs do not inherit either rarity policy.
- Epic Villages Standalone preserves vanilla villages. Its Cristel placement override uses spacing `80` and separation `22`, with salt `50387312` and frequency `1.0` unchanged: 75% fewer Epic candidate-grid positions per area than packaged spacing `40`, not a measured settlement reduction or guaranteed cross-mod separation. Existing chunks are unchanged; fresh-chunk density and performance still require acceptance testing before deployment.
- Universal Graves retains 75% of XP, protects graves for one hour, and expires them after 24 real-time hours.
- squaremap enables only the Overworld, limits zoom, reduces background rendering pressure, and intentionally retains its live player tracker. The tracker becomes public to anyone who can reach the configured map endpoint.
- JEB uses 24-hour full and three-hour differential intervals, a 6 GB retention cap, an 8 GB free-space reserve, and operator-level-4 commands. Startup resets the timers, so deployment requires an initial full backup and explicit daily full backups coordinated with host restarts. Production launch requires full and differential restore drills.
- Ledger remains future-only. If promoted, it will use bounded retention and a verified, separately budgeted MySQL service rather than unbounded event-store growth on the game filesystem. DatHost's hosting page retrieved **2026-11-11** advertises **60 GB included NVMe storage** and an included database, not verified account capacity or backup coverage; see the [provider profile](docs/providers/dathost.md). JEB's configured retention cap and reserve remain unchanged.
- PvP remains enabled, world spawn has a 16-block protection radius, and only the owner is a Minecraft operator. Helpers inherit the ordinary-player policy without operator status; the baseline grants them no additional nodes, and any future support capability must be added as an explicit LuckPerms node.
- Same-dimension waystone travel costs two XP levels, has a 30-second PvP/PvE combat lock, and allows ten player-owned waystones per player. Only the owner may create global/server-owned waystones.
- Server-Side Waystones 1.3.2 has no hard cross-dimension switch or strictly private owner-only mode. Survival cross-dimension travel is made infeasible with the maximum XP cost, while creative-owner bypass and physical discovery of player waystones are documented limitations.

See [`docs/configuration.md`](docs/configuration.md) for the rationale and unresolved deployment values.

## Prerequisites

- Python 3.11+
- [packwiz](https://packwiz.infra.link/)
- Java 25 on the designated Minecraft test/deployment host

Server-folder preparation uses the repository's Python materializer; it needs no separate mrpack installer.

Do not start Minecraft server processes on lightweight control machines. Exporting and static validation are safe there; server materialization and boot tests belong on the designated, adequately resourced Minecraft test host.

## Validate and build

```bash
make test
make validate
make export
```

Export validation compares the exact mod pins, server/client flags, and configuration contents with this source tree. It rejects missing mods, missing or changed configs, and unexpected files, including staged candidates. Validation requires the complete `.mrpack` archive; a standalone manifest cannot prove that configs are included.

Ordinary source validation derives the numeric Minecraft target from `pack.toml` and
requires `collection.toml` to agree and use Fabric. CI additionally supplies the actual
pull-request base or push branch to `release_metadata.py --expected-minecraft`, so changing
both metadata files cannot silently retarget a version-line PR. For an independent local
line check, run `python3 scripts/release_metadata.py --expected-minecraft 26.2` (use `26.3`
when checking that line). Manual workflow runs must select the intended version branch;
tag runs instead retain the exact release-tag check.

The export lands at:

```text
dist/cobbled-horizon-26.2.0.1.3.mrpack
```

On the designated Minecraft test host, prepare a private server ZIP with:

```bash
make server-zip
```

This first materializes and validates a fresh `build/server/`, then creates `build/cobbled-horizon-26.2.0.1.3-server.zip` with contents at the ZIP root, sorted names, fixed timestamps and normalized permissions. Existing folder and ZIP destinations are refused; keep the folder unchanged while archiving. `make materialize` remains available for folder-only preparation. Private installation on the owner's own server does not require a public redistribution-clearance record; that is not a public redistribution grant.

For DatHost, select this prepared `-server.zip` under **Mods & Plugins → Custom upload**, not the public CurseForge-format manifest ZIP or a renamed `.mrpack`. The command reports actual bytes and warns above the documented **100 MB** (100,000,000 bytes) web-upload limit; use authenticated FTP/file-manager transfer of the extracted contents for larger files, not another browser upload subject to the same limit. Before replacement, stop the instance and verify an off-host backup of the pack, configuration and matching world data, separately preserving the Floodgate key and `mods/luckperms/` data. Verify the panel's removal scope; use selective transfer if Custom upload cannot preserve host-owned files safely. Overlaying directories alone does not remove retired JARs or obsolete configs. Follow the [stopped-server reconciliation procedure](docs/deployment.md#upload) and [DatHost import guidance](docs/providers/dathost.md#modpack-import-options). Runtime/account compatibility remains unverified; these commands do not install or start Minecraft. CI never builds, uploads or caches a real complete server ZIP, and releases never select it.

## GitHub releases

Release tags use `v<Minecraft version>.<pack major>.<pack minor>.<pack patch>`. For the current pack, use `v26.2.0.1.3`, for Minecraft `26.2` and pack revision `0.1.3`. `pack.toml` stores the complete version, `26.2.0.1.3`, without the leading `v`.

The derived distribution plan selects one public asset set:

- **Full mode (current 26.2):** `cobbled-horizon-26.2.0.1.3.mrpack`, `cobbled-horizon-26.2.0.1.3.zip` and the combined `cobbled-horizon-26.2.0.1.3.sha256`. Native CurseForge references and bundled binaries have separate exact-identity/evidence checks. A validation failure never downgrades a full release to metadata.
- **Metadata fallback:** the `.mrpack` and `.mrpack.sha256` when selected bundled records have well-formed unresolved binary obligations. The no-JAR archive contains exact upstream references, configuration and finite recipient notices.

Inspect the current plan and build its full release with:

```bash
python3 scripts/distribution.py release-plan
make validate test release
```

`make release` builds the full public archives only when distribution checks permit it; neither its asset set nor its checksum selects the local `-server.zip`. `make materialize` produces the complete local folder from the mrpack, and `make server-zip` additionally packages it for private owner installation. The host must supply Java 25, Minecraft 26.2 and Fabric Loader 0.19.5; runtime binaries, worlds and credentials are not packaged. Vanilla Java clients need no pack.

Only the release owner should create and push a matching version tag after review. GitHub Actions validates source, index and the selected archives, then independently boots a folder materialized from the validated mrpack, including in metadata mode. Native acceptance checks a clean install, effective permissions, conflict/repeat/roundtrip preservation, save/exit and an offline restart. Its test-owned permission import does not change this line's manual production bootstrap.

Publication reassesses the same frozen plan and checksum membership, uploads only its selected nonempty assets into a draft, compares the exact remote set, then publishes. Upload failures leave the draft recoverable; reruns refuse to alter published assets. Branch, pull-request and manual runs do not publish. Native evidence is a bounded log allowlist, never downloaded JARs, worlds, exports or credentials.

Exact-head hosted validate and native-acceptance must pass before accepting the pipeline. Production cross-play, provider access, world-generation/performance and restore tests remain separate designated-host requirements. See [`docs/version-policy.md`](docs/version-policy.md).

## Updating

Do not run unreviewed floating updates on `main`. Use a branch, select exact version IDs, regenerate the index and export, then repeat the clean boot and acceptance tests.

To see which projects have begun publishing for 26.3:

```bash
python3 scripts/check_target_readiness.py --minecraft 26.3
```

A nonzero exit means at least one baseline project remains unavailable. Staged candidates are reported separately and do not block the baseline. `--release-only` also rejects alpha/beta files; `--baseline-only` suppresses staged reporting.

## Documentation

- [`docs/configuration.md`](docs/configuration.md)
- [`docs/permissions.md`](docs/permissions.md)
- [`docs/deployment.md`](docs/deployment.md)
- [`docs/providers/dathost.md`](docs/providers/dathost.md)
- [`docs/storage-and-recovery.md`](docs/storage-and-recovery.md)
- [`docs/acceptance-tests.md`](docs/acceptance-tests.md)
- [`docs/version-policy.md`](docs/version-policy.md)
- [`docs/verification.md`](docs/verification.md)

## Ownership and licensing

Jimmy McCann ([@jabez007](https://github.com/jabez007)) directs the project. See [`CONTRIBUTORS.md`](CONTRIBUTORS.md).

The repository-authored tooling and documentation are MIT licensed. Referenced mods and Minecraft remain under their own licenses and terms. `distribution/permissions.toml` binds exact pins, channel decisions, source duties and captured license texts. Generated notices are not permission grants; unresolved records block public binary publication. Private owner installation does not require that public clearance record and grants no public redistribution rights.
