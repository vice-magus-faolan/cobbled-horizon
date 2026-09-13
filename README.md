# Cobbled Horizon

A reproducible, server-side Fabric collection for a Vanilla+ Minecraft world focused on performance, exploration, and restrained quality-of-life improvements.

The current baseline targets **Minecraft Java 26.2** with **Fabric Loader 0.19.5**. It contains 21 deliberately selected projects plus four dependencies resolved by packwiz. Just Enough Backups (JEB) replaces the obsolete Textile Backup candidate.

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

- Server-Side Waystones
- Universal Graves
- Creeper No Break Blocks
- Towns and Towers
- [Epic Structures: Villages Standalone Edition](https://modrinth.com/datapack/epic-structures-villages-standalone-edition)
- Explorify
- Hopo Better Mineshaft
- Dungeons and Taverns Stronghold Overhaul Lite
- Moog's Soaring Structures
- Moog's Structure Lib *(dependency)*

Exact baseline project IDs, version IDs, download URLs, and SHA-512 hashes live in `mods/*.pw.toml`. All entries are pinned.

### Staged and future candidates

Krypton, Fast Noise with ZConfig, ScalableLux, and Spiral Tower Villages retain pinned metadata under `staged/`, but they are excluded from the baseline export. C2ME, VMP, Clumps, Ledger, Sparse Structures, and ChoiceTheorem's Overhauled Village (CTOV) are future candidates with explicit activation gates in [`candidates.toml`](candidates.toml). Spiral Tower Villages is the preferred next village addition, ahead of CTOV. Ledger is intentionally absent from launch: its proposed bounded MySQL deployment is documented in [`docs/storage-and-recovery.md`](docs/storage-and-recovery.md).

## Intent versus dependency closure

Packwiz writes the same `.pw.toml` shape for a project whether it was selected directly or pulled in as a dependency. Removing a resolved dependency's metadata would make the exported pack incomplete, so the distinction should not be encoded by deleting or relocating those files.

This repository keeps the two concerns separate:

- [`collection.toml`](collection.toml) defines the active baseline: 21 selected projects and four resolved dependencies.
- [`candidates.toml`](candidates.toml) defines staged and future projects, why they are inactive, and the evidence required to promote them.
- `mods/*.pw.toml` is the machine-maintained baseline lock layer. It contains the 25 projects exported by the standard pack.
- `staged/mods/*.pw.toml` retains five pinned candidate records outside packwiz's active index.

Fabric API is the only explicitly selected platform library. Polymer, Cristel Lib, Cloth Config API, and Moog's Structure Lib close baseline dependencies. ZConfig is staged beside Fast Noise. Cristel Lib demonstrates why dependency chains matter: Towns and Towers requires Cristel Lib, which in turn requires Cloth Config API and Fabric API.

`scripts/check_pack.py` verifies that both layers agree, so a dependency cannot silently disappear or become an undeclared top-level choice.

## Initial policy choices

- Geyser uses Floodgate authentication; generated Floodgate keys are never committed.
- ServerCore's non-vanilla-parity optimizations remain disabled.
- Moog's structures use a `2.0` spacing multiplier so they remain uncommon.
- Epic Villages Standalone preserves vanilla villages and initially uses its packaged placement defaults. Settlement density and performance still require acceptance testing before deployment.
- Universal Graves retains 75% of XP, protects graves for one hour, and expires them after 24 real-time hours.
- squaremap enables only the Overworld, limits zoom, and reduces background rendering pressure.
- JEB uses 24-hour full and three-hour differential intervals, a 6 GB retention cap, and an 8 GB free-space reserve. Startup resets the timers, so deployment requires an initial full backup and explicit daily full backups coordinated with host restarts. Production launch requires full and differential restore drills.
- Ledger remains future-only. If promoted, it will use bounded retention and preferably DatHost's included MySQL service rather than the 30 GB game filesystem.
- Global waystone creation is denied through LuckPerms bootstrap commands.
- Server-Side Waystones 1.3.2 does not expose a true cross-dimensional disable switch; this remains an acceptance-test item rather than a falsely claimed setting.

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
dist/cobbled-horizon-0.1.0+mc26.2.mrpack
```

On the designated Minecraft test host, materialize a clean server tree with:

```bash
make materialize
```

Do not upload the `.mrpack` to an undocumented DatHost field. Build and test on the designated Minecraft host, then upload the materialized `mods/`, `config/`, and `squaremap/` directories as described in [`docs/deployment.md`](docs/deployment.md).

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
