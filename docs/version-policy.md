# Version and update policy

## Release versions

`pack.toml` is the source of truth for release versions and artifact names. Its `version` is `<Minecraft version>.<pack major>.<pack minor>.<pack patch>`, currently `26.3.0.1.5`. Git tags add a leading `v`, giving `v26.3.0.1.5`. The Minecraft prefix must match `versions.minecraft` exactly. The exported mrpack retains the complete pack version; a private server ZIP carries it in its filename. This numeric candidate identity does not establish runtime readiness or authorize a release.

The next pack-only patch on Minecraft 26.3 would use `26.3.0.1.6`. If Minecraft gains another version component, keep the complete prefix, for example `26.3.1.0.1.0` for Minecraft 26.3.1 and pack revision 0.1.0. Release tags currently accept numeric versions only, without prerelease suffixes.

A valid matching tag always publishes exactly the validated no-JAR `.mrpack` and `.mrpack.sha256`. Release notes explain its original-host downloads, configs and notices. The selector owns one manifest for build/upload/draft comparison; the publisher independently reevaluates records and validates the exact nonempty set, checksum and archive through `make check-release`. Invalid records, stale identities, missing/corrupt texts or failed archive/checksum checks are fatal. Native success, draft-first exact-set checks and refusal to replace a published release remain required. Drafts with unexpected assets remain unpublished without automatic deletion. Existing published assets remain historical records. See the [release instructions](../README.md#github-releases) and [distribution obligations](../README.md#ownership-and-licensing). Publication to Modrinth or CurseForge is not configured.

## Version branches

`26.2` retains the original Minecraft 26.2 line. `26.3` is the default version line for the pack; see the [deployment report](verification.md#current-deployment). Later changes still require review and verification. Topic pull requests target their intended version branch. Backport a shared fix deliberately in a separate reviewed change; never synchronize the lines wholesale or replace retained 26.2 pins with 26.3 artifacts. The former `main` and `upgrade/minecraft-26.3` branch names are historical, not operational targets.

The existing `Build and release pack` workflow, job `validate`, runs for pull requests and pushes to either version branch, not duplicate topic pushes. Pins, validators and export infrastructure share a broad contract, so these PRs use the full unit suite. Source/schema/tests/index checks and validated no-JAR metadata remain usable while binary rights are unresolved. The `native-acceptance` job downloads validate's immutable artifact ID, checks its selected checksum/set and materializes that very `.mrpack` into a fresh validated folder before boot/restart, without an uncleared JAR artifact/cache bridge. Its consumed archive hash is recorded; download/hash failures never cause re-export. The public pipeline never uploads mod binaries; tagged releases require native success. A source-only green job is not real export or runtime evidence.

## Exact pins

`collection.toml` records why each active baseline project exists. Add deliberately chosen projects under `[[selected]]`; add only packwiz-resolved libraries under `[[resolved-dependency]]` with their `required-by` parent. The validation gate requires the union of those sections to match `mods/*.pw.toml` exactly.

`candidates.toml` records staged and future projects. Staged projects retain pinned metadata under `staged/mods/`, which packwiz excludes from normal exports. Promotion requires moving both intent and metadata into the baseline in one reviewed change, with an exact distribution record. Resolve channel, notice and covered-source duties before binary transfer/publication; metadata and ephemeral verification do not clear them.

Every `mods/*.pw.toml` entry must contain:

- `side = "server"`
- `pin = true`
- an exact Modrinth project ID
- an exact Modrinth version ID
- an HTTPS download URL
- a SHA-512 hash

`distribution/permissions.toml` additionally binds the complete metafile digest and exact project/version/SHA-512 identity. Direct `scripts/check_pack.py` validation rejects missing/stale records, text bytes or text provenance without requiring unresolved rights to be misrepresented as allowed. Native CurseForge updater blocks and their captured evidence remain unchanged for a possible future listing. They no longer select a public manifest partition; the original Modrinth download identity and recipient notices remain authoritative. These records do not grant platform admission.

The Minecraft and Fabric Loader versions are pinned in `pack.toml`. Do not broaden acceptable game versions to force a 26.2 JAR onto 26.3.

The current development candidate uses Fabric Loader `0.20.1` and 33 exact Fabric 26.3 project versions. The sole explicit prerelease exception is Geyser `2.12.1-b1281`, project `wKkoqHrH`, version `MJYV1WUM` (beta). The other 32 versions are release-designated. This is not a global prerelease policy: `--release-only` must still reject beta/alpha records, and other prerelease-only candidates remain inactive. Primary metadata and verified artifact hashes do not establish dependency-range, server-boot, gameplay, or cross-play success.

Staged pins retain historical bytes, including 26.2 builds; they are excluded from active exports and are not certified for 26.3. Promotion requires selecting and verifying exact target-compatible versions as well as passing the existing activation gates. Future projects remain identity/gate entries only.

## Update procedure

1. Create a short-lived update branch from the intended version line and target that line in the pull request.
2. Update `collection.toml` when selection intent or dependency relationships change.
3. Select exact new version IDs; do not use an unreviewed floating update on `26.2` or `26.3`.
4. Review changelogs, dependencies, environment metadata, and licenses. Update the exact permission/evidence/text/source records, preserving unknown obligations rather than marking them allowed to obtain a build.
5. Run `packwiz refresh --build`.
6. Run useful development checks (`make validate`, `make test`); commit the coherent source and obtain independent exact-commit source review. Publish the reviewed topic PR and require its exact-head hosted `validate` and `native-acceptance` jobs, including real all-pin exports, native install/restart and validated no-JAR metadata artifacts. Run `make release` / `make check-release` for the exact public mrpack/checksum contract. Source-only success and private boot are not binary redistribution permission.
7. Record designated-host runtime results against a disposable world copy, distinguishing the hosted assertions already exercised from outstanding real-client, networking, gameplay and restore checks. Source approval and hosted static checks do not supply that missing evidence; see the [deployment report](verification.md#current-deployment).
8. Only with separate publication authorization, push a new matching release tag. The public set is always the no-JAR mrpack and its checksum; binary redistribution obligations do not change that set. Retain the selected published assets and checksums as the release record. Back up production before any separately authorized deployment.
9. For a future installation or update, complete the applicable deployment preflight, verify the result, and retain the previous known-good pack and matching world snapshot for rollback. Outstanding checks on the existing deployment are not retroactive deployment conditions.

## Current 26.3 deployment and outstanding evidence

Pack `26.3.0.1.5` adds stable server-only Mc2Discord 4.4.0 and an inert example for one-way advancement, death, join and leave posts, with private runtime configuration excluded from source and archives. Existing pins, worldgen, permission policy and 26.2 remain unchanged. See the [private activation guide](discord-journal.md); real pinned-artifact no-token hosted boots and later approved live event delivery are distinct gates.

Pack `26.3.0.1.4` corrects JEB/Tasks operator guidance, refreshes pinned MSS/Hopo schemas and packages a one-time group-only LuckPerms seed with an import-ready gzip. All mod/runtime pins, Moog rarity inputs and the separate 26.2 line are unchanged. Its published tag passed hosted archive and bounded native install/restart/config/import assertions. See the [deployment report](verification.md#current-deployment) and [dated verification record](verification.md#current-263-evidence) for exact source/run and outstanding designated-host checks. Neither evidence class certifies later changed source or untested behavior.

Pack `26.3.0.1.3` adds the standalone server archive without changing mod pins, runtime versions or configuration. Pack `26.3.0.1.2` introduced Epic's placement policy through the existing Cristel auto-config mechanism: `epic:villages` uses spacing `80`, separation `22`, salt `50387312` and frequency `1.0`. All mod/loader pins and other structure tuning remain unchanged. The 75% reduction is in Epic candidate-grid positions per area, not measured settlements. Actual config loading, fixed-seed fresh-chunk density/proximity, generation cost and Java/Bedrock interaction remain outstanding checks and are required before pre-generation; existing chunks are not retroactively changed. See [configuration rationale](configuration.md#structure-generation).

Use:

```bash
python3 scripts/check_target_readiness.py --minecraft 26.3
```

A successful lookup is necessary but not sufficient for an update. Use the [provider-neutral deployment preflight](deployment.md#preflight) for subsequent installations or changes; a provider advertisement or deployment report does not verify account allocations. Hosted clean boot does not replace designated-host Java/Bedrock testing, world-generation inspection or full/differential backup restoration. No new server launch, world mutation or migration is implied by this policy. Those checks are still outstanding for the 26.3 pack.

Real-client Geyser/Floodgate checks remain outstanding evidence for Bedrock support despite the accepted beta pin. JEB full and differential restore drills and exact-pin scheduling checks across restarts also remain outstanding. Creeper No Break must preserve entity damage/knockback and unrelated mob-griefing behavior. Explorify v1.6.6 restores the original project selection in place of interim Structory without adding Formations. Use its packaged placement defaults, review generated schemas rather than transplanting legacy Explorify configs, and explicitly measure Nether Black Spiral generation/performance with the structure enabled. Standalone DnT replaces retired Lite, not the broad DnT collection. Its exact 3.0.1 archive has [historical static evidence of no custom enchantment registry definitions](configuration.md#structure-generation), not a runtime pass; verify Eyes of Ender, stronghold portals, progression, vanilla-enchanted loot and first-generation stalls without transplanting the retired Lite override. Structures require fresh chunks, density/performance and cross-play checks before pre-generation. Krypton, Fast Noise, ScalableLux and Spiral Tower Villages remain staged; future-only projects are not part of this pack.
