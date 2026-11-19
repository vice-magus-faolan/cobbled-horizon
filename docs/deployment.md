# DatHost deployment

DatHost documents Fabric support, manual uploads and server-pack ZIP import. Prepare the exact selected server folder and local-only ZIP from the checksum-verified mrpack. The host must still provide Java 25, Minecraft 26.2 and Fabric Loader 0.19.5. Artifact generation is not runtime or account-import acceptance.

## Modpack import options

Use the prepared `-server.zip` under **Mods & Plugins → Custom upload**, not the public CurseForge-format manifest ZIP or a renamed `.mrpack`. DatHost's URL importer selects the newest server pack, not necessarily the linked version.

Private installation on the owner's own server does not require a public redistribution-clearance record; public sharing remains separately gated. Vanilla Java clients need no client pack, and Bedrock access retains the Geyser/Floodgate contract. No CurseForge listing or upload is configured.

Before Custom upload, verify the panel's removal scope and preserve the matching world, Floodgate key, `mods/luckperms/` data and host settings in a completed off-host backup. If safe preservation cannot be established, use the stopped-server selective upload below. Overlaying directories alone does not remove retired JARs or obsolete configs.

## Preflight

- Confirm DatHost offers Fabric 0.19.5 for Minecraft 26.2 or an equivalent supported Fabric installation path.
- Confirm a reachable UDP allocation for Geyser.
- Confirm an HTTP port or proxy arrangement for squaremap.
- Verify the account's usable storage quota and DatHost's daily-backup retention, restore scope and quota accounting. The hosting page retrieved **2026-11-11** advertises **60 GB included NVMe storage**, not a measured account allocation; see the [provider profile](providers/dathost.md#advertised-offering-not-verified-entitlement).
- Confirm at least 8 GB remains free after the world, squaremap tiles, logs, and current JEB backups are present. The advertisement does not change the 6,144 MB retention cap or 8,192 MB reserve.
- Disable automatic mod/server-version updates.
- Establish the [full-backup procedure across restarts](storage-and-recovery.md#create-full-backups-across-restarts) before enabling unattended restarts.
- Take a host-level backup before replacing an existing installation.

## Build

Use source matching the selected release. Download the full release's mrpack, ZIP and combined checksum into `dist/`, then verify the checksums before preparing the mrpack:

```bash
(cd dist && sha256sum --check cobbled-horizon-26.2.0.1.3.sha256)
mkdir -p build
python3 scripts/server_folder.py materialize dist/cobbled-horizon-26.2.0.1.3.mrpack build/server
python3 scripts/server_folder.py zip build/server build/cobbled-horizon-26.2.0.1.3-server.zip
```

Alternatively, build and prepare the exact reviewed source on the designated Minecraft test host:

```bash
make validate test server-zip
```

This uses `make export` and the existing materializer, validates all pinned files, then creates `build/cobbled-horizon-26.2.0.1.3-server.zip`. `make materialize` remains the folder-only route. The generated `build/server/` contains all 32 source-pinned JARs, configuration, squaremap and recipient notices, with no manifest wrapper, staged/client-only JARs, runtime binaries or credentials. ZIP contents are at the root, with sorted names, fixed timestamps and normalized permissions. Existing folder and ZIP destinations are refused; use fresh owned destinations and leave the folder unchanged while archiving. The command reports actual bytes and warns strictly above 100,000,000 bytes. Use authenticated FTP/file-manager transfer of extracted contents for larger packs; a browser file manager may share the web limit.

Preparation never installs or starts Minecraft. Inspect the complete folder before transfer and complete the designated-host acceptance tests before production use. Private owner installation is not permission to publish the complete ZIP: public archive clearance, notices and source-delivery obligations remain enforced. CI never builds, uploads or caches a real complete server ZIP, and the release plan never selects it.

## Upload

Before replacement, stop the DatHost instance and verify a completed off-host backup of the current pack, configuration and matching world data, separately preserving the Floodgate key and `mods/luckperms/` backend/exports/private data. Never remove these while clearing obsolete mod JARs. Use Custom upload only after verifying its removal/preservation scope; otherwise transfer selectively as follows.

With the DatHost server stopped:

1. Set the server type and version to Fabric / Minecraft 26.2.
2. Reconcile the inspected `mods/` from `build/server/` with DatHost's `/mods`; remove obsolete pack JARs so an overlay cannot leave stale versions active. Preserve `mods/luckperms/` and other host-owned data.
3. Upload the same payload's `config/` into `/config`. Reconcile any existing Epic Cristel placement file with the reviewed policy rather than keeping a host-generated default: `cristellib/mr_epic_structuresvillagesstandaloneedition/structure_placement_config.json5` must contain only `epic:villages`, with salt `50387312`, spacing `80`, separation `22`, and frequency `1.0`. Preserve unrelated host settings, secrets and the Floodgate key; reconcile obsolete pack configs rather than overlaying blindly.
4. Upload the same payload's `squaremap/` into `/squaremap`.
5. Apply selected values from `server.properties.example`, including `online-mode=true` and `enforce-secure-profile=false`; preserve DatHost-managed ports and secrets.
6. Start once so Floodgate creates its key on a fresh installation; retain the existing key on an update.
7. Recheck the Geyser UDP port and squaremap web address against DatHost allocations.
8. Run `/jeb next` and verify the configured schedules and backup directory.
9. Create and verify the initial full backup before admitting players.
10. Restart and run the acceptance tests, including Java and Bedrock chat and separate-instance full and differential restore drills.

Confirm the effective Cristel policy and complete the fresh-chunk comparison in [`acceptance-tests.md`](acceptance-tests.md) before final Chunky pre-generation. Existing chunks are not retuned; the setting does not enforce distance from other mods' settlements.

## Rollback

If startup fails, stop the server before making further changes. Restore the prior `/mods`, `/config`, `/squaremap`, and world snapshot together, including the matching Floodgate key and LuckPerms data. Do not allow a failed version migration to keep writing into the only world copy.

## Backups

JEB replaces Textile Backup in the 26.2 baseline. Its checked-in policy limits retained backups to 6 GB and preserves an 8 GB free-space reserve. Keep DatHost's daily backup enabled as an independent layer and download an off-host snapshot before every pack or loader update.

JEB resets its automatic timers at startup and config reload. Coordinate explicit full backups with the host's restart schedule, and verify completion before each scheduled restart. Follow [`storage-and-recovery.md`](storage-and-recovery.md) for the operating procedure and required full and differential restore drills.

## Optional Ledger deployment

Do not upload Ledger or Ledger Databases at launch. If their activation gate is later approved, use the proposed bounded MySQL configuration in [`storage-and-recovery.md`](storage-and-recovery.md), inject credentials on DatHost, and complete the documented failure and recovery tests first.
