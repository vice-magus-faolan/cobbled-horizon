# Version and update policy

## Release versions

`pack.toml` is the source of truth for release versions and artifact names. Its `version` is `<Minecraft version>.<pack major>.<pack minor>.<pack patch>`, currently `26.2.0.1.3`. Git tags add a leading `v`, giving `v26.2.0.1.3`. The Minecraft prefix must match `versions.minecraft` exactly. The exported mrpack retains the complete pack version.

For the next pack-only patch on Minecraft 26.2, use `26.2.0.1.4`. If Minecraft gains another version component, keep the complete prefix, for example `26.2.1.0.1.0` for Minecraft 26.2.1 and pack revision 0.1.0. Release tags currently accept numeric versions only, without prerelease suffixes.

A valid matching tag always publishes exactly the validated no-JAR `.mrpack` and `.mrpack.sha256`, regardless of unresolved binary redistribution obligations. Release notes explain original-host downloads, configs and recipient notices. The selector owns one manifest for build/upload/draft comparison; the publisher independently reevaluates records and the exact tag, then validates the exact nonempty set, checksum and archive through `make check-release`. Invalid records, stale identities, missing/corrupt texts and failed archive/checksum checks are fatal. Hosted validate and native acceptance, draft-first exact-set checks and refusal to replace a published release remain required. Drafts with unexpected assets stay unpublished without automatic deletion. Existing releases retain their historical assets. See the [release instructions](../README.md#github-releases). Publication to Modrinth or CurseForge is not configured.

## Production pins

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

## Update procedure

1. Create a short-lived update branch.
2. Update `collection.toml` when selection intent or dependency relationships change.
3. Select exact new version IDs; do not use an unreviewed floating update on `main`.
4. Review changelogs, dependencies, environment metadata, and licenses.
5. Run `packwiz refresh --build`.
6. Run all automated and manual acceptance tests against a disposable copied world.
7. Inspect `python3 scripts/distribution.py release-plan` and use `make release` / `make check-release` for the exact public mrpack/checksum contract. Commit the coherent source and obtain independent exact-commit review; publish the reviewed topic PR and require exact-head validate and native-acceptance before the release owner creates a separately authorized new matching tag. Retain the published mrpack and checksum as the release record; never reuse a published tag or alter its historical assets.
8. Back up production before deployment.
9. Deploy, verify, and retain the previous known-good pack for rollback.

## Moving to 26.3

Use:

```bash
python3 scripts/check_target_readiness.py --minecraft 26.3
```

A successful lookup is necessary but not sufficient. Stable Minecraft 26.3, Fabric Loader/API support, DatHost availability, a successful clean boot, Java/Bedrock testing, and world-generation inspection must all pass.

Geyser/Floodgate are hard gates if Bedrock support is required. JEB must publish a compatible release and pass fresh full and differential restore drills. Recheck its scheduling behavior across host restarts. Epic Villages Standalone must publish a matching Fabric release and pass fresh structure and cross-play tests. Krypton, Fast Noise, ScalableLux, and Spiral Tower Villages remain staged until their activation gates pass. Future-only Ledger and CTOV do not block the baseline.
