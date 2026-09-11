# DatHost deployment

DatHost documents Fabric support and manual uploads of mods and configuration files. It does not currently document direct packwiz or `.mrpack` import, so the pack is materialized and tested before upload.

## Preflight

- Confirm DatHost offers Fabric 0.19.5 for Minecraft 26.2 or an equivalent supported Fabric installation path.
- Confirm a reachable UDP allocation for Geyser.
- Confirm an HTTP port or proxy arrangement for squaremap.
- Confirm DatHost's daily-backup retention, restore scope, and whether it counts against the 30 GB allocation.
- Confirm at least 8 GB remains free after the world, squaremap tiles, logs, and current JEB backups are present.
- Disable automatic mod/server-version updates.
- Establish the [full-backup procedure across restarts](storage-and-recovery.md#create-full-backups-across-restarts) before enabling unattended restarts.
- Take a host-level backup before replacing an existing installation.

## Build

Run server materialization on the designated Minecraft test host, not on a lightweight control machine:

```bash
make test
make validate
make materialize
```

The generated server tree is `build/server/`. Inspect it before upload. It must contain the 24 active baseline project JARs and reviewed config overrides, but no staged/client-only JARs or credentials.

## Upload

With the DatHost server stopped:

1. Set the server type and version to Fabric / Minecraft 26.2.
2. Upload `build/server/mods/` into DatHost's `/mods`.
3. Upload `build/server/config/` into `/config`.
4. Upload `build/server/squaremap/` into `/squaremap`.
5. Apply selected values from `server.properties.example`, including `online-mode=true` and `enforce-secure-profile=false`; preserve DatHost-managed ports and secrets.
6. Start once so Floodgate creates its key.
7. Recheck the Geyser UDP port and squaremap web address against DatHost allocations.
8. Run `/jeb next` and verify the configured schedules and backup directory.
9. Create and verify the initial full backup before admitting players.
10. Restart and run the acceptance tests, including Java and Bedrock chat and separate-instance full and differential restore drills.

## Rollback

If startup fails, stop the server before making further changes. Restore the prior `/mods`, `/config`, `/squaremap`, and world snapshot together. Do not allow a failed version migration to keep writing into the only world copy.

## Backups

JEB replaces Textile Backup in the 26.2 baseline. Its checked-in policy limits retained backups to 6 GB and preserves an 8 GB free-space reserve. Keep DatHost's daily backup enabled as an independent layer and download an off-host snapshot before every pack or loader update.

JEB resets its automatic timers at startup and config reload. Coordinate explicit full backups with the host's restart schedule, and verify completion before each scheduled restart. Follow [`storage-and-recovery.md`](storage-and-recovery.md) for the operating procedure and required full and differential restore drills.

## Optional Ledger deployment

Do not upload Ledger or Ledger Databases at launch. If their activation gate is later approved, use the proposed bounded MySQL configuration in [`storage-and-recovery.md`](storage-and-recovery.md), inject credentials on DatHost, and complete the documented failure and recovery tests first.
