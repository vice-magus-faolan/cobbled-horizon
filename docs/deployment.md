# DatHost deployment

DatHost documents Fabric support and manual uploads of mods and configuration files. It does not currently document direct packwiz or `.mrpack` import, so the pack is materialized and tested before upload.

## Preflight

- Confirm DatHost offers Fabric 0.19.5 for Minecraft 26.2 or an equivalent supported Fabric installation path.
- Confirm a reachable UDP allocation for Geyser.
- Confirm an HTTP port or proxy arrangement for squaremap.
- Disable automatic mod/server-version updates.
- Take a host-level backup before replacing an existing installation.

## Build

Run server materialization on the designated Minecraft test host, not on a lightweight control machine:

```bash
make test
make validate
make materialize
```

The generated server tree is `build/server/`. Inspect it before upload. It must contain the 27 resolved mod JARs and reviewed config overrides, but no client-only JARs or credentials.

## Upload

With the DatHost server stopped:

1. Set the server type and version to Fabric / Minecraft 26.2.
2. Upload `build/server/mods/` into DatHost's `/mods`.
3. Upload `build/server/config/` into `/config`.
4. Upload `build/server/squaremap/` into `/squaremap`.
5. Apply selected values from `server.properties.example`; preserve DatHost-managed ports and secrets.
6. Start once so Floodgate creates its key.
7. Recheck the Geyser UDP port and squaremap web address against DatHost allocations.
8. Restart and run the acceptance tests.

## Rollback

If startup fails, stop the server before making further changes. Restore the prior `/mods`, `/config`, `/squaremap`, and world snapshot together. Do not allow a failed version migration to keep writing into the only world copy.

## Backups

Textile Backup is intentionally absent. Until a replacement is selected and restore-tested, rely on DatHost's host-level backup plus an independently downloaded snapshot before every pack or loader update. A backup mechanism is not accepted merely because it produces an archive; restoration must be exercised.
