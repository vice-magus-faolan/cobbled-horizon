# Version and update policy

## Production pins

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
2. Select exact new version IDs; do not use an unreviewed floating update on `main`.
3. Review changelogs, dependencies, environment metadata, and licenses.
4. Run `packwiz refresh --build`.
5. Run all automated and manual acceptance tests against a disposable copied world.
6. Export an immutable `.mrpack` and record its checksum in release notes.
7. Back up production before deployment.
8. Deploy, verify, and retain the previous known-good pack for rollback.

## Moving to 26.3

Use:

```bash
python3 scripts/check_target_readiness.py --minecraft 26.3
```

A successful lookup is necessary but not sufficient. Stable Minecraft 26.3, Fabric Loader/API support, DatHost availability, a successful clean boot, Java/Bedrock testing, and world-generation inspection must all pass.

Geyser/Floodgate are hard gates if Bedrock support is required. Fast Noise and ScalableLux remain explicit risk items while their selected files are alpha/beta channel releases.
