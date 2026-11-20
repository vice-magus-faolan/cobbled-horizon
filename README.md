# Cobbled Horizon

<p align="center">
  <img src="docs/assets/cobbled-horizon-logo.png" alt="Cobbled Horizon logo" width="420">
</p>

A reproducible, server-side Fabric collection for a Vanilla+ Minecraft world focused on performance, exploration, and restrained quality-of-life improvements.

This **development candidate** targets **Minecraft Java 26.3** with **Fabric Loader 0.20.1**. It contains 27 deliberately selected projects plus six resolved dependencies. All 33 exact artifacts have published Fabric 26.3 support; 32 are release-designated and Geyser `2.12.1-b1281` (`MJYV1WUM`) is explicitly pinned as beta. The published `v26.3.0.1.4` passed hosted native install/restart, selected config and synthetic permission-import assertions; that evidence does not certify this changed candidate. See the [deployment report and outstanding checks](docs/verification.md#current-deployment). Just Enough Backups (JEB) retains the backup role.

Java players should not need this pack on their clients: every packwiz entry is marked `side = "server"`. Bedrock access is provided by Geyser and Floodgate. This Geyser build requires UDP for NetherNet media and either TCP on the Bedrock port for built-in signaling, distinct from Java's TCP listener, or an explicitly configured and verified external signaling service. Host support is unverified; see [`Geyser networking`](docs/deployment.md#geyser-networking).

## Version branches

- `26.2` preserves the original Minecraft 26.2 pack line.
- `26.3` is the default version line for the Minecraft 26.3 pack; see the [deployment report](docs/verification.md#current-deployment). Each subsequent source change still needs its own review and verification.
- Target pull requests at the intended version branch; backport shared fixes deliberately rather than automatically synchronizing the two lines.

See [`docs/version-policy.md`](docs/version-policy.md) for pack update and acceptance requirements.

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
- [Mc2Discord](docs/discord-journal.md) — dormant; private advancement-only activation required

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
- [Explorify](https://modrinth.com/mod/explorify)
- [Hopo Better Mineshaft](https://modrinth.com/mod/hopo-better-mineshaft)
- [Dungeons and Taverns Stronghold Overhaul](https://modrinth.com/mod/dungeons-and-taverns-stronghold-overhaul) *(standalone, not the broad DnT collection)*
- [Moog's Soaring Structures](https://modrinth.com/mod/mss-moogs-soaring-structures)
- [Moog's Ocean Structures](https://modrinth.com/mod/mos-moogs-ocean-structures)
- Moog's Structure Lib *(dependency)*

Exact baseline project IDs, version IDs, download URLs, and SHA-512 hashes live in `mods/*.pw.toml`. All entries are pinned.

The 26.3 line replaces Creeper No Break Blocks and retired DnT Stronghold Lite, and restores Explorify v1.6.6 in place of interim Structory; Formations is not added. Explorify uses packaged defaults, preserving the 26.2 placement policy without reinstating unverified legacy config schemas. Towns and Towers and Moog spacing policy remain unchanged. New structures affect newly generated chunks, not existing terrain. The October 6 exact-archive investigation found no custom enchantment registry definitions in standalone DnT 3.0.1 (`hNKbQ85c`); that is distinct from vanilla-enchanted loot and is not a runtime pass. Explorify's Nether Black Spiral generation/performance and DnT's stronghold progression, generation stalls, portal access and loot still require Java/Bedrock testing before pre-generation or migration. See [`docs/configuration.md`](docs/configuration.md#structure-generation) for the evidence and remaining gates.

### Staged and future candidates

Krypton, Fast Noise with ZConfig, ScalableLux, and Spiral Tower Villages retain pinned metadata under `staged/`, but they are excluded from the baseline export. C2ME, VMP, Clumps, Ledger, Sparse Structures, and ChoiceTheorem's Overhauled Village (CTOV) are future candidates with explicit activation gates in [`candidates.toml`](candidates.toml). Spiral Tower Villages is the preferred next village addition, ahead of CTOV. Ledger is intentionally absent from launch: its proposed bounded MySQL deployment is documented in [`docs/storage-and-recovery.md`](docs/storage-and-recovery.md).

## Intent versus dependency closure

Packwiz writes the same `.pw.toml` shape for a project whether it was selected directly or pulled in as a dependency. Removing a resolved dependency's metadata would make the exported pack incomplete, so the distinction should not be encoded by deleting or relocating those files.

This repository keeps the two concerns separate:

- [`collection.toml`](collection.toml) defines the active baseline: 27 selected projects and six resolved dependencies.
- [`candidates.toml`](candidates.toml) defines staged and future projects, why they are inactive, and the evidence required to promote them.
- `mods/*.pw.toml` is the machine-maintained baseline lock layer. It contains the 33 projects exported by the standard pack.
- `staged/mods/*.pw.toml` retains five pinned candidate records outside packwiz's active index.

Fabric API is the only explicitly selected platform library. Polymer, Cristel Lib, Cloth Config API, Forge Config API Port, Moog's Structure Lib, and Collective close baseline dependencies. ZConfig is staged beside Fast Noise. Cristel Lib demonstrates why dependency chains matter: Towns and Towers requires Cristel Lib, which in turn requires Cloth Config API and Fabric API. Explorify requires Fabric API; its Cristel Lib integration is optional. Crops Love Rain requires Forge Config API Port and Fabric API. Villager Names requires Collective.

`scripts/check_pack.py` verifies that both layers agree, so a dependency cannot silently disappear or become an undeclared top-level choice.

## Initial policy choices

- Geyser uses Floodgate authentication; generated Floodgate keys are never committed.
- ServerCore's non-vanilla-parity optimizations remain disabled.
- Naturally Trimmed uses only vanilla trim materials and patterns. Trimmed equipment remains uncommon: 75% of eligible mobs receive no trims, each remaining armor piece has a 35% chance, loot uses 15%, and level-three-or-higher trades use 10%.
- Crops Love Rain gives directly rain-exposed crops and cocoa a 1-in-10 extra-stage chance per applicable random tick; slower-growing plants use 1-in-15. Bamboo's rain bonus is disabled because the mod checks global rain rather than direct exposure for bamboo.
- Moog's spacing is scoped by namespace: Soaring Structures uses `2.0`, while Ocean Structures uses `3.0`. The universal multiplier remains `1.0` so future Moog packs do not inherit either rarity policy.
- Epic Villages Standalone preserves vanilla villages. Its Cristel placement override uses spacing `80` and separation `22`, retaining salt `50387312` and frequency `1.0`: 75% fewer Epic candidate-grid positions per area than the shipped `40`/`11` policy, not measured settlement totals or guaranteed cross-mod separation. Existing chunks are unchanged; actual config loading, fresh-chunk density and performance remain outstanding checks.
- Universal Graves retains 75% of XP, protects graves for one hour, and expires them after 24 real-time hours.
- squaremap enables only the Overworld, limits zoom, reduces background rendering pressure, and intentionally retains its live player tracker. The tracker becomes public to anyone who can reach the configured map endpoint.
- JEB uses 24-hour full and three-hour differential intervals, a 6 GB retention cap, an 8 GB free-space reserve, and operator-level-4 commands. The operating procedure requires an initial full backup and explicit daily full backups coordinated with host restarts because startup can reset the timers. Exact-pin scheduling checks and full and differential restore drills remain outstanding evidence.
- Ledger remains future-only. If promoted, it will use bounded retention and a verified, separately budgeted MySQL service rather than unbounded growth on the game filesystem; provider availability is not assumed.
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
line check, run `python3 scripts/release_metadata.py --expected-minecraft 26.3` (use `26.2`
when checking that line). Manual workflow runs must select the intended version branch;
tag runs instead retain the exact release-tag check.

`make export check-metadata` produces and validates a metadata-only archive, independently of JAR redistribution clearance. It contains exact download references, approved configuration overrides and finite recipient notices, never bundled JARs or private runtime files. The archive and its separate `.mrpack.sha256` checksum land at:

```text
dist/cobbled-horizon-26.3.0.1.5.mrpack
dist/cobbled-horizon-26.3.0.1.5.mrpack.sha256
```

On the designated Minecraft test host, prepare a private server ZIP with:

```bash
make server-zip
```

This first materializes and validates a fresh `build/server/`, then creates `build/cobbled-horizon-26.3.0.1.5-server.zip` with contents at the ZIP root, sorted names, fixed timestamps and normalized permissions. Existing folder and ZIP destinations are refused; keep the folder unchanged while archiving. `make materialize` remains available for folder-only preparation. Private installation on the owner's own server does not require a public redistribution-clearance record; that is not a public redistribution grant.

For DatHost, select this prepared `-server.zip` under **Mods & Plugins → Custom upload**, not a renamed `.mrpack`. The command reports actual bytes and warns above the documented **100 MB** web-upload limit; use authenticated FTP/file-manager transfer of the extracted contents for larger files, not another browser upload subject to the same limit. Before replacement, stop the instance and verify an off-host backup of the pack, configuration and matching world data, separately preserving the Floodgate key and `mods/luckperms/` data. Verify the panel's removal scope; use selective transfer if Custom upload cannot preserve host-owned files safely. Overlaying directories alone does not remove retired JARs or obsolete configs. Follow the [stopped-server reconciliation procedure](docs/deployment.md#upload) and [DatHost import guidance](docs/providers/dathost.md#modpack-import-options). Runtime/account compatibility remains unverified; these commands do not install or start Minecraft. CI never builds, uploads or caches a real complete server ZIP, and releases never select it.

## GitHub releases

Release tags use `v<Minecraft version>.<pack major>.<pack minor>.<pack patch>`. This candidate's source version is `26.3.0.1.5`, for Minecraft `26.3` and pack revision `0.1.5`. A matching tag would be `v26.3.0.1.5`; the numeric version is not a production approval. Do not tag this development candidate until separately approved for release.

A valid matching tag always selects exactly the validated no-JAR `.mrpack` and its `.mrpack.sha256`, regardless of unresolved binary redistribution obligations. Malformed records, stale identity, corrupt/missing required texts, invalid archives and checksum errors remain fatal. Native first-install/restart acceptance and separate release approval are still required.

Build and validate the public release files without starting Minecraft:

```bash
make test
make release
```

The public files are the same two files shown above. The `.mrpack` preserves server-only flags and exact original-host downloads. It includes the pack's configs and deterministic `CREDITS.md`, `SOURCES.md` and required `LICENSES/<hash>.txt` members, but no JARs, Minecraft/Fabric runtime, launch scripts, worlds or secrets. Java players do not need it to join. There is no public CurseForge ZIP producer or configured CurseForge listing; existing releases and their historical assets are unchanged.

### Using a downloaded release

For releases produced by this pipeline, download the `.mrpack` and its matching `.mrpack.sha256` into the same directory. Replace `<pack-version>` with that release's version, then verify:

```bash
MRPACK='cobbled-horizon-<pack-version>.mrpack'
sha256sum --check "$MRPACK.sha256"
```

Historical releases, including `v26.3.0.1.4`, retain their original asset sets; use the checksum supplied with that release instead of assuming a new per-mrpack checksum exists.

Choose one installation route:

- From the source revision matching that release, run `make materialize` to export, validate and prepare a fresh `build/server/` with every original pinned mod and indexed configs/notices. To consume the downloaded archive itself, place it under `dist/`, create `build/`, and run `python3 scripts/server_folder.py materialize "dist/$MRPACK" build/server`. Existing destinations are refused. Neither command starts Minecraft or grants binary sharing rights. `make server-zip` additionally packages the validated folder for private owner installation. Check the unmodified folder with `python3 scripts/server_folder.py validate build/server` before runtime provisioning; follow the [deployment runbook](docs/deployment.md#build) and [DatHost import limitations](docs/providers/dathost.md#modpack-import-options).
- Alternatively use the [`itzg/minecraft-server` image's Modrinth support](https://docker-minecraft-server.readthedocs.io/en/latest/types-and-platforms/mod-platforms/modrinth-modpacks/). Set `TYPE=MODRINTH` and `MODRINTH_MODPACK` to the release asset's hosted `.mrpack` URL, or to a mounted container path ending in `.mrpack`. Follow the image's setup instructions and the pack's Java, runtime and deployment requirements. This alternative is documented, not independently runtime-tested here.

Only with separately authorized publication, source review and passing hosted checks, create and push a new matching tag from the intended version line. Never reuse a published version/tag; `v26.3.0.1.4` and its assets are historical release records, not test targets.

```bash
git tag -a v<pack version> -m "Cobbled Horizon v<pack version>"
git push origin v<pack version>
```

GitHub Actions checks source/schema, versions, tests and the index independently of unresolved distribution rights. The `validate` job uploads exactly the validated `.mrpack` and `.mrpack.sha256`. On PR, branch and tag runs, `native-acceptance` downloads that immutable artifact ID, verifies the same set and checksum, and materializes its very `.mrpack` into a fresh complete folder before provisioning, boot and restart. There is no second export or fallback after download/hash failure; native `summary.json` records the consumed `archive_sha256`. It does not transfer JARs through artifacts or caches; only bounded allowlisted runtime evidence leaves that job. Tags require native success. Publishing uses the built-in `GITHUB_TOKEN`; this workflow uploads to GitHub only.

The workflow uses one asset manifest from `scripts/distribution.py release-plan`. Default Make plans are regenerated for current records/tag on each build/check; an explicit `RELEASE_PLAN=...` is frozen and must match exactly. The publish job reevaluates the records and exact tag, then `make check-release` validates the same selected nonempty files, exact checksum membership and archive contents through `make check-metadata`. Release notes use the plan's recipient-facing explanation, not generated GitHub changelog notes. Uploads go into a draft, which becomes public only after its complete nonempty asset set matches that manifest. Unexpected draft assets are not deleted automatically. If an upload fails, rerun the failed job to complete the draft. A rerun refuses to replace assets on an already published release. Use a new pack version and tag for a corrected release. Branch, pull request and manual runs upload eligible artifacts but do not create releases.

Release automation also requires the hosted native first-install/restart checks described in [`docs/acceptance-tests.md`](docs/acceptance-tests.md#automated-gates). A green job is not Java/Bedrock client, gameplay, density or backup-restore evidence; those designated-host checks remain outstanding for this pack. See [`docs/version-policy.md`](docs/version-policy.md) for the update procedure.

## Updating

Do not run unreviewed floating updates on `26.2` or `26.3`. Use a topic branch targeting the intended version line, select exact version IDs, regenerate the index and export, then repeat the clean boot and acceptance tests.

To discover upstream project availability for the exact Minecraft target 26.3:

```bash
python3 scripts/check_target_readiness.py --minecraft 26.3
```

A nonzero exit means at least one baseline project has no matching published file or its lookup failed. Staged candidates are reported separately and do not block the baseline. The checker queries all published versions of each project, not the selected lock ID. `--release-only` filters those results to release-designated Fabric files for the target Minecraft version; `--baseline-only` suppresses staged reporting.

This is an upgrade-discovery check, not an audit of pinned-pack stability: a later upstream release can make `--release-only` green while this pack still pins the Geyser beta `2.12.1-b1281`. That pin remains explicitly beta in this pack. Exact selected artifacts require the separate metadata/hash audit and runtime checks in [`docs/version-policy.md`](docs/version-policy.md#exact-pins); the exact-pin beta exception does not relax release-only filtering or permit other prereleases. Retained staged pins have not been refreshed or activated for 26.3.

## Documentation

- [`docs/configuration.md`](docs/configuration.md)
- [`docs/permissions.md`](docs/permissions.md)
- [`docs/deployment.md`](docs/deployment.md)
- [`docs/providers/dathost.md`](docs/providers/dathost.md) — current provider, advertised offerings and outstanding account checks
- [`docs/storage-and-recovery.md`](docs/storage-and-recovery.md)
- [`docs/acceptance-tests.md`](docs/acceptance-tests.md)
- [`docs/version-policy.md`](docs/version-policy.md)
- [`docs/verification.md`](docs/verification.md)

## Ownership and licensing

Permission records live in `distribution/permissions.toml`: exact project/version/SHA-512 plus the metafile digest bind URLs, side and pins. Native CurseForge updater metadata and captured evidence are retained for a possible future listing, not used to split public archives. The `channels` fields remain descriptive records; they do not select release files. Unknown and conditional are not approval. `python3 scripts/distribution.py status` reports their current values. Public builds contain no JARs and remain usable while binary rights are unresolved. Private installation on the owner's own server, including transfer of the prepared folder or ZIP to that server, does not require a public redistribution-clearance record. This does not grant public redistribution or sharing rights for the complete payload. DatHost import restrictions are documented separately.

Current records intentionally retain unresolved exact-version grants, nested/shaded coverage and covered-source delivery. Curated external texts include full GPL/LGPL terms, missing FerriteCore/JEB notices, the current Creeper MIT text, exact Cristel/Towns and Towers/Hopo author terms and known Guice/Jakarta/Mc2Discord dependency notices. Original embedded licenses and copyrights remain inside the unchanged, hash-validated JARs; external copies supplement rather than replace them. Full-text provenance records bind primary URLs and, for embedded texts, exact version/member identities. This is not complete dependency/source clearance or a cleared full-pack export. Exact source candidates are labeled as held until completeness and equivalent access are established; a source tag/homepage alone is not Corresponding Source. Generated notices cannot manufacture absent permission or relicense the whole pack. Existing public assets are not corrected by this source change alone.

[@jabez007](https://github.com/jabez007) directs the project. See [`CONTRIBUTORS.md`](CONTRIBUTORS.md).

The repository-authored tooling and documentation are MIT licensed. Referenced mods and Minecraft remain under their own licenses and terms.

Archive validation checks contents, not redistribution permission. Sharing a privately prepared JAR-bearing payload would require permission for the exact component versions and distribution channel, required license/credit/NOTICE preservation, and applicable source delivery. The public pipeline offers no such binary archive or clearance command. Neither a successful build nor server startup supplies permission or CurseForge submission approval.
