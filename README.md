# Cobbled Horizon

A reproducible, server-side Fabric collection for a Vanilla+ Minecraft world focused on performance, exploration, and restrained quality-of-life improvements.

The current baseline targets **Minecraft Java 26.2** with **Fabric Loader 0.19.5**. It contains 24 deliberately selected projects plus three dependencies resolved by packwiz. Textile Backup is intentionally excluded.

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

## Intent versus dependency closure

Packwiz writes the same `.pw.toml` shape for a project whether it was selected directly or pulled in as a dependency. Removing a resolved dependency's metadata would make the exported pack incomplete, so the distinction should not be encoded by deleting or relocating those files.

This repository keeps the two concerns separate:

- [`collection.toml`](collection.toml) is the human-maintained intent manifest. Its `[[selected]]` entries are the 24 projects deliberately requested. Its `[[resolved-dependency]]` entries are the three projects packwiz added to close dependency requirements.
- `mods/*.pw.toml` is the machine-maintained lock layer. It contains all 27 projects needed to build the pack, each with its exact version, download URL, side, and hash.

Fabric API, Polymer, and Cristel Lib remain in `[[selected]]` because they were deliberately named in the original collection, even though other selected mods also require them. Cloth Config API, ZConfig, and Moog's Structure Lib are purely transitive in the current baseline.

`scripts/check_pack.py` verifies that both layers agree, so a dependency cannot silently disappear or become an undeclared top-level choice.

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
- Java 25 on the designated Minecraft test/deployment host

Do not start Minecraft server processes on lightweight control machines. Exporting and static validation are safe there; server materialization and boot tests belong on the designated, adequately resourced Minecraft test host.

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
