# Cobbled Horizon

A reproducible, server-side Fabric collection for a Vanilla+ Minecraft world focused on performance, exploration, and restrained quality-of-life improvements.

The current baseline targets **Minecraft Java 26.2** with **Fabric Loader 0.19.5**. It contains the 24 requested mods plus three resolved dependencies. Textile Backup is intentionally excluded.

Java players should not need this pack on their clients: every packwiz entry is marked `side = "server"`. Bedrock access is provided by Geyser and Floodgate and still requires a reachable UDP port on the host.

## Included collection

### Platform and cross-play

- Fabric API
- Polymer
- Cristel Lib
- Cloth Config API *(dependency)*
- LuckPerms
- Geyser
- Floodgate

### Performance and administration

- Lithium
- FerriteCore
- Krypton
- Alternate Current
- Fast Noise
- ZConfig *(dependency)*
- ScalableLux
- ServerCore
- spark
- Chunky
- squaremap

### Quality of life and exploration

- Server-Side Waystones
- Universal Graves
- Creeper No Break Blocks
- Towns and Towers
- Explorify
- Hopo Better Mineshaft
- Dungeons and Taverns Stronghold Overhaul Lite
- Moog's Soaring Structures
- Moog's Structure Lib *(dependency)*

Exact project IDs, version IDs, download URLs, and SHA-512 hashes live in `mods/*.pw.toml`. All entries are pinned.

## Initial policy choices

- Geyser uses Floodgate authentication; generated Floodgate keys are never committed.
- ServerCore's non-vanilla-parity optimizations remain disabled.
- Fast Noise's explicitly risky biome options are disabled.
- Moog's structures use a `2.0` spacing multiplier so they remain uncommon.
- Universal Graves retains 75% of XP, protects graves for one hour, and expires them after 24 real-time hours.
- squaremap enables only the Overworld, limits zoom, and reduces background rendering pressure.
- Global waystone creation is denied through LuckPerms bootstrap commands.
- Server-Side Waystones 1.3.2 does not expose a true cross-dimensional disable switch; this remains an acceptance-test item rather than a falsely claimed setting.

See [`docs/configuration.md`](docs/configuration.md) for the rationale and unresolved deployment values.

## Prerequisites

- Python 3.11+
- [packwiz](https://packwiz.infra.link/)
- [mrpack-install](https://github.com/nothub/mrpack-install) for local server materialization
- Java 25 for running Minecraft 26.2

## Validate and build

```bash
make test
make validate
make export
```

The export lands at:

```text
dist/cobbled-horizon-0.1.0+mc26.2.mrpack
```

Materialize a clean server tree with:

```bash
make materialize
```

Do not upload the `.mrpack` to an undocumented DatHost field. Build and test locally, then upload the materialized `mods/`, `config/`, and `squaremap/` directories as described in [`docs/deployment.md`](docs/deployment.md).

## Updating

Do not run unreviewed floating updates on `main`. Use a branch, select exact version IDs, regenerate the index and export, then repeat the clean boot and acceptance tests.

To see which projects have begun publishing for 26.3:

```bash
python3 scripts/check_target_readiness.py --minecraft 26.3
```

A nonzero exit means at least one project remains unavailable. `--release-only` also rejects alpha/beta files.

## Documentation

- [`docs/configuration.md`](docs/configuration.md)
- [`docs/permissions.md`](docs/permissions.md)
- [`docs/deployment.md`](docs/deployment.md)
- [`docs/acceptance-tests.md`](docs/acceptance-tests.md)
- [`docs/version-policy.md`](docs/version-policy.md)
- [`docs/verification.md`](docs/verification.md)

## Ownership and licensing

Jimmy McCann ([@jabez007](https://github.com/jabez007)) directs the project. See [`CONTRIBUTORS.md`](CONTRIBUTORS.md).

The repository-authored tooling and documentation are MIT licensed. Referenced mods and Minecraft remain under their own licenses and terms.
