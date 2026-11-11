# Version and update policy

## Release versions

`pack.toml` is the source of truth for release versions and artifact names. Its `version` is `<Minecraft version>.<pack major>.<pack minor>.<pack patch>`, currently `26.3.0.1.2`. Git tags add a leading `v`, giving `v26.3.0.1.2`. The Minecraft prefix must match `versions.minecraft` exactly. Both exported manifests retain the complete pack version. This numeric candidate identity does not establish runtime readiness or authorize a release.

The next pack-only patch on Minecraft 26.3 would use `26.3.0.1.3`. If Minecraft gains another version component, keep the complete prefix, for example `26.3.1.0.1.0` for Minecraft 26.3.1 and pack revision 0.1.0. Release tags currently accept numeric versions only, without prerelease suffixes.

Pushing a matching tag builds and publishes the `.mrpack`, server CurseForge-format `.zip`, and `.sha256` file to GitHub Releases. See the [release instructions](../README.md#github-releases). Publication to Modrinth or CurseForge is not configured.

## Version branches

`26.2` retains the original Minecraft 26.2 line. `26.3` is the default development line; it is not production-approved merely because it is the default. Topic pull requests target their intended version branch. Backport a shared fix deliberately in a separate reviewed change; never synchronize the lines wholesale or replace retained 26.2 pins with 26.3 artifacts. The former `main` and `upgrade/minecraft-26.3` branch names are historical, not operational targets.

The existing `Build and release pack` workflow, job `validate`, runs for pull requests and pushes to either version branch, not duplicate topic pushes. Pins, validators and export infrastructure share a broad contract, so these PRs use the full unit suite. Tag publication remains separate from branch/PR artifact builds.

## Exact pins

`collection.toml` records why each active baseline project exists. Add deliberately chosen projects under `[[selected]]`; add only packwiz-resolved libraries under `[[resolved-dependency]]` with their `required-by` parent. The validation gate requires the union of those sections to match `mods/*.pw.toml` exactly.

`candidates.toml` records staged and future projects. Staged projects retain pinned metadata under `staged/mods/`, which packwiz excludes from normal exports. Promotion requires moving both intent and metadata into the baseline in one reviewed change.

Every `mods/*.pw.toml` entry must contain:

- `side = "server"`
- `pin = true`
- an exact Modrinth project ID
- an exact Modrinth version ID
- an HTTPS download URL
- a SHA-512 hash

The Minecraft and Fabric Loader versions are pinned in `pack.toml`. Do not broaden acceptable game versions to force a 26.2 JAR onto 26.3.

The current development candidate uses Fabric Loader `0.20.1` and 32 exact Fabric 26.3 project versions. The sole explicit prerelease exception is Geyser `2.12.1-b1281`, project `wKkoqHrH`, version `MJYV1WUM` (beta). The other 31 versions are release-designated. This is not a global prerelease policy: `--release-only` must still reject beta/alpha records, and other prerelease-only candidates remain inactive. Primary metadata and verified artifact hashes do not establish dependency-range, server-boot, gameplay, or cross-play success.

Staged pins retain historical bytes, including 26.2 builds; they are excluded from active exports and are not certified for 26.3. Promotion requires selecting and verifying exact target-compatible versions as well as passing the existing activation gates. Future projects remain identity/gate entries only.

## Update procedure

1. Create a short-lived update branch from the intended version line and target that line in the pull request.
2. Update `collection.toml` when selection intent or dependency relationships change.
3. Select exact new version IDs; do not use an unreviewed floating update on `26.2` or `26.3`.
4. Review changelogs, dependencies, environment metadata, and licenses.
5. Run `packwiz refresh --build`.
6. Run useful development checks (`make validate`, `make test`); commit the coherent source and obtain independent exact-commit source review. Publish the reviewed topic PR and require its exact-head hosted `validate` job, which refresh-checks the index and runs `make release` for both archive validators and checksums.
7. Separately authorize and complete all designated-host runtime acceptance against a disposable world copy. Source approval and hosted static checks do not satisfy this step.
8. Only with release approval, push the matching release tag. Retain published archives and checksums as the release record. Back up production before any separately authorized deployment.
9. Deploy only after its gates pass, verify, and retain the previous known-good pack and matching world snapshot for rollback.

## 26.3 candidate readiness

Pack `26.3.0.1.2` changes only Epic's placement policy through the existing Cristel auto-config mechanism: `epic:villages` uses spacing `80`, separation `22`, salt `50387312` and frequency `1.0`. All mod/loader pins and other structure tuning remain unchanged. The 75% reduction is in Epic candidate-grid positions per area, not measured settlements. Verify actual config loading, fixed-seed fresh-chunk density/proximity, generation cost and Java/Bedrock interaction before deployment or pre-generation; existing chunks are not retroactively changed. See [configuration rationale](configuration.md#structure-generation).

Use:

```bash
python3 scripts/check_target_readiness.py --minecraft 26.3
```

A successful lookup is necessary but not sufficient. The selected host must meet the [provider-neutral deployment requirements](deployment.md#preflight); a candidate-provider advertisement is not account acceptance. A successful clean boot, Java/Bedrock testing, world-generation inspection and full/differential backup restoration must all pass before production. No server launch, world mutation or migration is implied by the source update.

Geyser/Floodgate remain hard runtime gates for Bedrock support despite the accepted beta pin. JEB must pass fresh full and differential restore drills; recheck scheduling across restarts. Creeper No Break must preserve entity damage/knockback and unrelated mob-griefing behavior. Explorify v1.6.6 restores the original project selection in place of interim Structory without adding Formations. Use its packaged placement defaults, review generated schemas rather than transplanting legacy Explorify configs, and explicitly measure Nether Black Spiral generation/performance with the structure enabled. Standalone DnT replaces retired Lite, not the broad DnT collection. Its exact 3.0.1 archive has [historical static evidence of no custom enchantment registry definitions](configuration.md#structure-generation), not a runtime pass; verify Eyes of Ender, stronghold portals, progression, vanilla-enchanted loot and first-generation stalls without transplanting the retired Lite override. Structures require fresh chunks, density/performance and cross-play checks before pre-generation. Krypton, Fast Noise, ScalableLux and Spiral Tower Villages remain staged; future-only projects do not block the active candidate.
