# DatHost deployment

DatHost documents Fabric support, manual uploads and server-pack ZIP import. The standalone release ZIP supplies the reviewed payload; the host must still provide Java 25, Minecraft 26.2 and Fabric Loader 0.19.5. Artifact generation is not runtime or account-import acceptance.

## Modpack import options

DatHost's [Minecraft: Installing Modpacks](https://help.dathost.net/article/179-minecraft-mods-modpacks) guide, inspected for this release tooling on **2026-11-13** (page updated November 3), documents CurseForge URL import under **Mods & Plugins → Mods & Modpacks** and server-pack ZIP import under **Mods & Plugins → Custom upload**. The URL importer selects the **newest available server pack**, even if the link points to an older version; it does not pin an older release. That field does not accept Modrinth URLs, and a `.mrpack` is not a prepared server ZIP.

For an exact Cobbled Horizon version, use its checksum-verified additional `-server.zip`, not the primary CurseForge manifest-format `.zip`. No CurseForge listing or upload is configured. Vanilla Java clients need no client pack. These are documented provider behaviors, not a tested DatHost import or deployment. Verify the actual account's import compatibility and runtime pins before use.

The guide calls for removing an installed modpack before Custom upload. Do not apply that action to an existing world or host-owned files without verifying its scope, preserving settings and Floodgate keys, and taking a complete off-host backup. Use the stopped-server selective upload below when safe preservation through the importer cannot be established.

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

Generate the complete standalone payload without starting Minecraft:

```bash
make test
make release
(cd dist && sha256sum --check cobbled-horizon-26.2.0.1.2.sha256)
```

The `cobbled-horizon-26.2.0.1.2-server.zip` root contains `mods/`, `config/` and `squaremap/`. Inspect or unpack it into a clean staging directory, not over a running server. It contains no Java/Minecraft/Fabric runtime. For a clean runtime test tree, retain the existing materialization route on the designated Minecraft test host:

```bash
make test
make validate
make materialize
```

The generated server tree is `build/server/`. Inspect it before upload. Either payload route must contain all 32 active project JARs (26 selected plus six dependencies) and reviewed config overrides, but no staged/client-only JARs or credentials. Complete the designated-host acceptance tests before production use.

## Upload

With the DatHost server stopped:

1. Set the server type and version to Fabric / Minecraft 26.2.
2. Reconcile the inspected `mods/` from the unpacked standalone ZIP or `build/server/` with DatHost's `/mods`; remove obsolete pack JARs so an overlay cannot leave stale versions active.
3. Upload the same payload's `config/` into `/config`. Reconcile any existing Epic Cristel placement file with the reviewed policy rather than keeping a host-generated default: `cristellib/mr_epic_structuresvillagesstandaloneedition/structure_placement_config.json5` must contain only `epic:villages`, with salt `50387312`, spacing `80`, separation `22`, and frequency `1.0`. Preserve unrelated host settings and secrets.
4. Upload the same payload's `squaremap/` into `/squaremap`.
5. Apply selected values from `server.properties.example`, including `online-mode=true` and `enforce-secure-profile=false`; preserve DatHost-managed ports and secrets.
6. Start once so Floodgate creates its key.
7. Recheck the Geyser UDP port and squaremap web address against DatHost allocations.
8. Run `/jeb next` and verify the configured schedules and backup directory.
9. Create and verify the initial full backup before admitting players.
10. Restart and run the acceptance tests, including Java and Bedrock chat and separate-instance full and differential restore drills.

Confirm the effective Cristel policy and complete the fresh-chunk comparison in [`acceptance-tests.md`](acceptance-tests.md) before final Chunky pre-generation. Existing chunks are not retuned; the setting does not enforce distance from other mods' settlements.

## Rollback

If startup fails, stop the server before making further changes. Restore the prior `/mods`, `/config`, `/squaremap`, and world snapshot together. Do not allow a failed version migration to keep writing into the only world copy.

## Backups

JEB replaces Textile Backup in the 26.2 baseline. Its checked-in policy limits retained backups to 6 GB and preserves an 8 GB free-space reserve. Keep DatHost's daily backup enabled as an independent layer and download an off-host snapshot before every pack or loader update.

JEB resets its automatic timers at startup and config reload. Coordinate explicit full backups with the host's restart schedule, and verify completion before each scheduled restart. Follow [`storage-and-recovery.md`](storage-and-recovery.md) for the operating procedure and required full and differential restore drills.

## Optional Ledger deployment

Do not upload Ledger or Ledger Databases at launch. If their activation gate is later approved, use the proposed bounded MySQL configuration in [`storage-and-recovery.md`](storage-and-recovery.md), inject credentials on DatHost, and complete the documented failure and recovery tests first.
