# Cobbled Horizon

A reproducible, server-side Fabric collection for a Vanilla+ Minecraft world focused on performance, exploration, and restrained quality-of-life improvements.

This **development candidate** targets **Minecraft Java 26.3** with **Fabric Loader 0.20.1**. It contains 26 deliberately selected projects plus six resolved dependencies. All 32 exact artifacts have published Fabric 26.3 support; 31 are release-designated and Geyser `2.12.1-b1281` (`MJYV1WUM`) is explicitly pinned as beta. This is not a clean-boot, gameplay, Bedrock, or production-readiness claim. Just Enough Backups (JEB) retains the backup role.

Java players should not need this pack on their clients: every packwiz entry is marked `side = "server"`. Bedrock access is provided by Geyser and Floodgate and still requires a reachable UDP port on the host.

## Version branches

- `26.2` preserves the original Minecraft 26.2 pack line.
- `26.3` is the default development line for the Minecraft 26.3 candidate. The branch name alone does not establish that the upgrade has been merged or runtime-tested.
- Target pull requests at the intended version branch; backport shared fixes deliberately rather than automatically synchronizing the two lines.

See [`docs/version-policy.md`](docs/version-policy.md) for pack update and acceptance requirements.

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
- [Creeper No Break](https://modrinth.com/mod/creeper-no-break)
- [Naturally Trimmed](https://modrinth.com/mod/naturally-trimmed)
- [Crops Love Rain](https://modrinth.com/mod/crops-love-rain)
- [Villager Names](https://modrinth.com/mod/villager-names-serilum)
- [Villagers Tasks](https://modrinth.com/mod/villagers-tasks)
- Collective *(dependency of Villager Names)*
- [Towns and Towers](https://modrinth.com/mod/towns-and-towers)
- [Epic Structures: Villages Standalone Edition](https://modrinth.com/mod/epic-structures-villages-standalone-edition)
- [Structory](https://modrinth.com/mod/structory)
- [Hopo Better Mineshaft](https://modrinth.com/mod/hopo-better-mineshaft)
- [Dungeons and Taverns Stronghold Overhaul](https://modrinth.com/mod/dungeons-and-taverns-stronghold-overhaul) *(standalone, not the broad DnT collection)*
- [Moog's Soaring Structures](https://modrinth.com/mod/mss-moogs-soaring-structures)
- [Moog's Ocean Structures](https://modrinth.com/mod/mos-moogs-ocean-structures)
- Moog's Structure Lib *(dependency)*

Exact baseline project IDs, version IDs, download URLs, and SHA-512 hashes live in `mods/*.pw.toml`. All entries are pinned.

The 26.3 line replaces Creeper No Break Blocks, Explorify, and retired DnT Stronghold Lite with the three entries above; Formations is not added. Obsolete Explorify/Lite overrides are removed, while Towns and Towers and Moog spacing policy remain. New structures affect newly generated chunks, not existing terrain. Standalone DnT changes stronghold progression and includes enchantment data; generation stalls, portal access, loot and Java/Bedrock behavior require testing before pre-generation or migration. See [`docs/configuration.md`](docs/configuration.md#structure-generation).

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
- Epic Villages Standalone preserves vanilla villages and initially uses its packaged placement defaults. Settlement density and performance still require acceptance testing before deployment.
- Universal Graves retains 75% of XP, protects graves for one hour, and expires them after 24 real-time hours.
- squaremap enables only the Overworld, limits zoom, reduces background rendering pressure, and intentionally retains its live player tracker. The tracker becomes public to anyone who can reach the configured map endpoint.
- JEB uses 24-hour full and three-hour differential intervals, a 6 GB retention cap, an 8 GB free-space reserve, and operator-level-4 commands. Startup resets the timers, so deployment requires an initial full backup and explicit daily full backups coordinated with host restarts. Production launch requires full and differential restore drills.
- Ledger remains future-only. If promoted, it will use bounded retention and preferably DatHost's included MySQL service rather than the 30 GB game filesystem.
- PvP remains enabled, world spawn has a 16-block protection radius, and only the owner is a Minecraft operator. Helpers inherit the ordinary-player policy without operator status; the baseline grants them no additional nodes, and any future support capability must be added as an explicit LuckPerms node.
- Same-dimension waystone travel costs two XP levels, has a 30-second PvP/PvE combat lock, and allows ten player-owned waystones per player. Only the owner may create global/server-owned waystones.
- Server-Side Waystones 1.3.2 has no hard cross-dimension switch or strictly private owner-only mode. Survival cross-dimension travel is made infeasible with the maximum XP cost, while creative-owner bypass and physical discovery of player waystones are documented limitations.

See [`docs/configuration.md`](docs/configuration.md) for the rationale and unresolved deployment values.

## Prerequisites

- Python 3.11+
- [packwiz](https://packwiz.infra.link/)
- [mrpack-install](https://github.com/nothub/mrpack-install) for local server materialization
- Java 25 on the designated Minecraft test/deployment host

Do not start Minecraft server processes on lightweight control machines. Exporting and static validation are safe there; server materialization and boot tests belong on the designated, adequately resourced Minecraft test host.

## Validate and build

```bash
make test
make validate
make export
```

Export validation compares the exact mod pins, server/client flags, and configuration contents with this source tree. It rejects missing mods, missing or changed configs, and unexpected files, including staged candidates. Validation requires the complete `.mrpack` archive; a standalone manifest cannot prove that configs are included.

The export lands at:

```text
dist/cobbled-horizon-26.3.0.1.0.mrpack
```

On the designated Minecraft test host, materialize a clean server tree with:

```bash
make materialize
```

Do not upload the `.mrpack` to an undocumented DatHost field. Build and test on the designated Minecraft host, then upload the materialized `mods/`, `config/`, and `squaremap/` directories as described in [`docs/deployment.md`](docs/deployment.md).

## GitHub releases

Release tags use `v<Minecraft version>.<pack major>.<pack minor>.<pack patch>`. This candidate's source version is `26.3.0.1.0`, for Minecraft `26.3` and pack revision `0.1.0`. A matching tag would be `v26.3.0.1.0`; the numeric version is not a production approval. Do not tag this development candidate until separately approved for release.

To build and validate both release formats locally, run:

```bash
make test
make release
```

The release files are:

```text
dist/cobbled-horizon-26.3.0.1.0.mrpack
dist/cobbled-horizon-26.3.0.1.0.zip
dist/cobbled-horizon-26.3.0.1.0.sha256
```

Both archives describe the server pack. The `.mrpack` preserves the server-only flags and references pinned Modrinth downloads. The CurseForge-format ZIP bundles those mod JARs under `overrides/mods/`, along with the configuration overrides. It is larger and is not a ready-to-run server directory. Java players do not need either archive to join.

Only after source review, passing hosted checks, designated-host acceptance and explicit release approval, create and push the matching tag from the intended version line:

```bash
git tag -a v26.3.0.1.0 -m "Cobbled Horizon v26.3.0.1.0"
git push origin v26.3.0.1.0
```

GitHub Actions checks the version, tests the tooling, verifies the source index, and validates both exports. It then creates a GitHub release with both archives, their SHA-256 checksums, and generated release notes. Publishing uses the built-in `GITHUB_TOKEN`; no additional secrets are required. This workflow uploads to GitHub only.

The workflow uploads into a draft and publishes it after all three files arrive. If an upload fails, rerun the failed job to complete the draft. A rerun refuses to replace assets on an already published release. Use a new pack version and tag for a corrected release. Branch, pull request, and manual workflow runs build artifacts without publishing.

Release automation performs static validation. Complete the designated-host acceptance tests before treating a release as production-ready. See [`docs/version-policy.md`](docs/version-policy.md) for the update procedure.

## Updating

Do not run unreviewed floating updates on `26.2` or `26.3`. Use a topic branch targeting the intended version line, select exact version IDs, regenerate the index and export, then repeat the clean boot and acceptance tests.

To recheck exact-version availability for the 26.3 line:

```bash
python3 scripts/check_target_readiness.py --minecraft 26.3
```

A nonzero exit means at least one baseline project remains unavailable. Staged candidates are reported separately and do not block the baseline. `--release-only` also rejects alpha/beta files; `--baseline-only` suppresses staged reporting.

The documented Geyser beta is a candidate-specific exception, not a relaxation of `--release-only`; that mode must continue rejecting it. Retained staged pins have not been refreshed or activated for 26.3.

## Documentation

- [`docs/configuration.md`](docs/configuration.md)
- [`docs/permissions.md`](docs/permissions.md)
- [`docs/deployment.md`](docs/deployment.md)
- [`docs/storage-and-recovery.md`](docs/storage-and-recovery.md)
- [`docs/acceptance-tests.md`](docs/acceptance-tests.md)
- [`docs/version-policy.md`](docs/version-policy.md)
- [`docs/verification.md`](docs/verification.md)

## Ownership and licensing

Jimmy McCann ([@jabez007](https://github.com/jabez007)) directs the project. See [`CONTRIBUTORS.md`](CONTRIBUTORS.md).

The repository-authored tooling and documentation are MIT licensed. Referenced mods and Minecraft remain under their own licenses and terms.
