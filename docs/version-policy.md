# Version and update policy

## Release versions

`pack.toml` is the source of truth for release versions and artifact names. Its `version` is `<Minecraft version>.<pack major>.<pack minor>.<pack patch>`, currently `26.2.0.1.0`. Git tags add a leading `v`, giving `v26.2.0.1.0`. The Minecraft prefix must match `versions.minecraft` exactly. Both exported manifests retain the complete pack version.

For a pack-only patch on Minecraft 26.2, use `26.2.0.1.1`. If Minecraft gains another version component, keep the complete prefix, for example `26.2.1.0.1.0` for Minecraft 26.2.1 and pack revision 0.1.0. Release tags currently accept numeric versions only, without prerelease suffixes.

Pushing a matching tag builds and publishes the `.mrpack`, server CurseForge-format `.zip`, and `.sha256` file to GitHub Releases. See the [release instructions](../README.md#github-releases). Publication to Modrinth or CurseForge is not configured.

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
7. Run `make release` to validate both pack formats and generate their checksums. Commit and push the source, then push its matching release tag. Retain the published archives and checksum file as the release record.
8. Back up production before deployment.
9. Deploy, verify, and retain the previous known-good pack for rollback.

## Moving to 26.3

Use:

```bash
python3 scripts/check_target_readiness.py --minecraft 26.3
```

A successful lookup is necessary but not sufficient. Stable Minecraft 26.3, Fabric Loader/API support, DatHost availability, a successful clean boot, Java/Bedrock testing, and world-generation inspection must all pass.

Geyser/Floodgate are hard gates if Bedrock support is required. JEB must publish a compatible release and pass fresh full and differential restore drills. Recheck its scheduling behavior across host restarts. Epic Villages Standalone must publish a matching Fabric release and pass fresh structure and cross-play tests. Krypton, Fast Noise, ScalableLux, and Spiral Tower Villages remain staged until their activation gates pass. Future-only Ledger and CTOV do not block the baseline.
