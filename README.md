# Cobbled Horizon

A reproducible, server-side Fabric collection for a Vanilla+ Minecraft world focused on performance, exploration, and restrained quality-of-life improvements.

The current baseline targets **Minecraft Java 26.2** with **Fabric Loader 0.19.5**. It contains 23 deliberately selected projects plus five dependencies resolved by packwiz. Just Enough Backups (JEB) replaces the obsolete Textile Backup candidate.

Java players should not need this pack on their clients: every packwiz entry is marked `side = "server"`. Bedrock access is provided by Geyser and Floodgate and still requires a reachable UDP port on the host.

## Included collection

### Platform and cross-play

- Fabric API
- Polymer *(dependency)*
- Cristel Lib *(dependency)*
- Cloth Config API *(dependency of Cristel Lib)*
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
- [Villager Names](https://modrinth.com/mod/villager-names-serilum)
- [Villagers Tasks](https://modrinth.com/mod/villagers-tasks)
- Collective *(dependency of Villager Names)*
- [Towns and Towers](https://modrinth.com/mod/towns-and-towers)
- [Epic Structures: Villages Standalone Edition](https://modrinth.com/mod/epic-structures-villages-standalone-edition)
- [Explorify](https://modrinth.com/mod/explorify)
- [Hopo Better Mineshaft](https://modrinth.com/mod/hopo-better-mineshaft)
- [Dungeons and Taverns Stronghold Overhaul Lite](https://modrinth.com/mod/dnt-stronghold-overhaul-lite-edition)
- [Moog's Soaring Structures](https://modrinth.com/mod/mss-moogs-soaring-structures)
- Moog's Structure Lib *(dependency)*

Exact baseline project IDs, version IDs, download URLs, and SHA-512 hashes live in `mods/*.pw.toml`. All entries are pinned.

### Staged and future candidates

Krypton, Fast Noise with ZConfig, ScalableLux, and Spiral Tower Villages retain pinned metadata under `staged/`, but they are excluded from the baseline export. C2ME, VMP, Clumps, Ledger, Sparse Structures, and ChoiceTheorem's Overhauled Village (CTOV) are future candidates with explicit activation gates in [`candidates.toml`](candidates.toml). Spiral Tower Villages is the preferred next village addition, ahead of CTOV. Ledger is intentionally absent from launch: its proposed bounded MySQL deployment is documented in [`docs/storage-and-recovery.md`](docs/storage-and-recovery.md).

## Intent versus dependency closure

Packwiz writes the same `.pw.toml` shape for a project whether it was selected directly or pulled in as a dependency. Removing a resolved dependency's metadata would make the exported pack incomplete, so the distinction should not be encoded by deleting or relocating those files.

This repository keeps the two concerns separate:

- [`collection.toml`](collection.toml) defines the active baseline: 23 selected projects and five resolved dependencies.
- [`candidates.toml`](candidates.toml) defines staged and future projects, why they are inactive, and the evidence required to promote them.
- `mods/*.pw.toml` is the machine-maintained baseline lock layer. It contains the 28 projects exported by the standard pack.
- `staged/mods/*.pw.toml` retains five pinned candidate records outside packwiz's active index.

Fabric API is the only explicitly selected platform library. Polymer, Cristel Lib, Cloth Config API, Moog's Structure Lib, and Collective close baseline dependencies. ZConfig is staged beside Fast Noise. Cristel Lib demonstrates why dependency chains matter: Towns and Towers requires Cristel Lib, which in turn requires Cloth Config API and Fabric API. Villager Names requires Collective.

`scripts/check_pack.py` verifies that both layers agree, so a dependency cannot silently disappear or become an undeclared top-level choice.

## Initial policy choices

- Geyser uses Floodgate authentication; generated Floodgate keys are never committed.
- ServerCore's non-vanilla-parity optimizations remain disabled.
- Moog's structures use a `2.0` spacing multiplier so they remain uncommon.
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
dist/cobbled-horizon-26.2.0.1.0.mrpack
```

On the designated Minecraft test host, materialize a clean server tree with:

```bash
make materialize
```

Do not upload the `.mrpack` to an undocumented DatHost field. Build and test on the designated Minecraft host, then upload the materialized `mods/`, `config/`, and `squaremap/` directories as described in [`docs/deployment.md`](docs/deployment.md).

## GitHub releases

Release tags use `v<Minecraft version>.<pack major>.<pack minor>.<pack patch>`. For the current pack, use `v26.2.0.1.0`, for Minecraft `26.2` and pack revision `0.1.0`. `pack.toml` stores the complete version, `26.2.0.1.0`, without the leading `v`.

To build and validate both release formats locally, run:

```bash
make test
make release
```

The release files are:

```text
dist/cobbled-horizon-26.2.0.1.0.mrpack
dist/cobbled-horizon-26.2.0.1.0.zip
dist/cobbled-horizon-26.2.0.1.0.sha256
```

Both archives describe the server pack. The `.mrpack` preserves the server-only flags and references pinned Modrinth downloads. The CurseForge-format ZIP bundles those mod JARs under `overrides/mods/`, along with the configuration overrides. It is larger and is not a ready-to-run server directory. Java players do not need either archive to join.

After committing and pushing the intended release changes, create and push the matching tag:

```bash
git tag -a v26.2.0.1.0 -m "Cobbled Horizon v26.2.0.1.0"
git push origin v26.2.0.1.0
```

GitHub Actions checks the version, tests the tooling, verifies the source index, and validates both exports. It then creates a GitHub release with both archives, their SHA-256 checksums, and generated release notes. Publishing uses the built-in `GITHUB_TOKEN`; no additional secrets are required. This workflow uploads to GitHub only.

The workflow uploads into a draft and publishes it after all three files arrive. If an upload fails, rerun the failed job to complete the draft. A rerun refuses to replace assets on an already published release. Use a new pack version and tag for a corrected release. Branch, pull request, and manual workflow runs build artifacts without publishing.

Release automation performs static validation. Complete the designated-host acceptance tests before treating a release as production-ready. See [`docs/version-policy.md`](docs/version-policy.md) for the update procedure.

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
- [`docs/storage-and-recovery.md`](docs/storage-and-recovery.md)
- [`docs/acceptance-tests.md`](docs/acceptance-tests.md)
- [`docs/version-policy.md`](docs/version-policy.md)
- [`docs/verification.md`](docs/verification.md)

## Ownership and licensing

Jimmy McCann ([@jabez007](https://github.com/jabez007)) directs the project. See [`CONTRIBUTORS.md`](CONTRIBUTORS.md).

The repository-authored tooling and documentation are MIT licensed. Referenced mods and Minecraft remain under their own licenses and terms.
