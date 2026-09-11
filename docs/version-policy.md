# Version and update policy

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
7. Export an immutable `.mrpack` and record its checksum in release notes.
8. Back up production before deployment.
9. Deploy, verify, and retain the previous known-good pack for rollback.

## Moving to 26.3

Use:

```bash
python3 scripts/check_target_readiness.py --minecraft 26.3
```

A successful lookup is necessary but not sufficient. Stable Minecraft 26.3, Fabric Loader/API support, DatHost availability, a successful clean boot, Java/Bedrock testing, and world-generation inspection must all pass.

Geyser/Floodgate are hard gates if Bedrock support is required. JEB must publish a compatible release and pass a fresh cold-restore drill. Krypton, Fast Noise, and ScalableLux remain staged risk items until their activation gates pass. Future-only Ledger does not block the baseline.
