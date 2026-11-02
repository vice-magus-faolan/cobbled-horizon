# DatHost deployment

DatHost documents Fabric support and manual uploads of mods and configuration files. It does not currently document direct packwiz or `.mrpack` import, so the pack is materialized and tested before upload.

## Preflight

This 26.3 development candidate is not approved for deployment. Complete source/hosted review and the designated-host runtime acceptance first, including the Geyser beta and replacement structure gates. Preserve the 26.2 pack and its world snapshot as a separate rollback line.

- Confirm DatHost offers Fabric 0.20.1 for Minecraft 26.3 or an equivalent supported Fabric installation path.
- Confirm a suitable Geyser UDP allocation and signaling arrangement as described in [Geyser networking](#geyser-networking); UDP alone is insufficient for this build.
- Confirm an HTTP port or proxy arrangement for squaremap.
- Confirm DatHost's daily-backup retention, restore scope, and whether it counts against the 30 GB allocation.
- Confirm at least 8 GB remains free after the world, squaremap tiles, logs, and current JEB backups are present.
- Disable automatic mod/server-version updates.
- Establish the [full-backup procedure across restarts](storage-and-recovery.md#create-full-backups-across-restarts) before enabling unattended restarts.
- Take a host-level backup before replacing an existing installation.

## Geyser networking

The pinned beta `2.12.1-b1281` follows build 1280's removal of RakNet-only transport. Its signaling configuration defaults to `BUILTIN`: NetherNet media uses UDP, while built-in signaling uses TCP on the Bedrock port. Verify reachability for both protocols and use a Bedrock port distinct from Java's TCP listener. Alternatively, retain suitable UDP reachability and explicitly configure and verify an external signaling service. Do not assume DatHost supplies either arrangement or silently enable an external service; any such service needs explicit approval and must preserve the authentication/privacy policy.

Before deployment, verify the exact build's config migration, actual UDP/TCP listeners (or external signaling connection), allocated ports and advertised addresses on the designated test host. Confirm real Bedrock joins and reconnects through that arrangement; a UDP allocation or successful bind alone is not acceptance. See the [cross-play gates](acceptance-tests.md#clients-and-cross-play). The checked-in config remains a policy input, not a verified schema or live allocation. Exact-build references: [build 1280](https://download.geysermc.org/v2/projects/geyser/versions/2.12.1/builds/1280), [build 1281](https://download.geysermc.org/v2/projects/geyser/versions/2.12.1/builds/1281), and [signaling configuration source](https://github.com/GeyserMC/Geyser/blob/b9d535a67cb6ef75a38140db0bd5ac2ccbe1e9ba/core/src/main/java/org/geysermc/geyser/configuration/GeyserConfig.java#L129-L158).

## Build

Run server materialization on the designated Minecraft test host, not on a lightweight control machine:

```bash
make test
make validate
make materialize
```

The generated server tree is `build/server/`. Inspect it before upload. It must contain the 32 active project JARs and reviewed config overrides, but no staged/client-only JARs or credentials. Reconcile generated configs with the retained policy; remove the three obsolete Explorify/Lite files described in [`configuration.md`](configuration.md#structure-generation), without carrying them into the replacement namespaces.

## Upload

This procedure is operator guidance for a separately approved deployment, not permission to migrate or launch this candidate. With the DatHost server stopped:

1. Verify a completed host backup containing the current pack, configuration and matching world snapshot, with an off-host rollback copy. Preserve the 26.2 pack/world rollback line; do not alter backup copies during reconciliation.
2. Set the server type and version to Fabric / Minecraft 26.3 with the pinned loader.
3. Reconcile or replace only the active DatHost `/mods` set with the verified 32-project payload from `build/server/mods/`. Remove retired Creeper No Break Blocks, Explorify and DnT Stronghold Lite JARs, along with superseded versions, from that active set before startup; verify it matches the payload with no staged or extra JARs. A simple upload overlay leaves obsolete JARs installed.
4. Reconcile `build/server/config/` into `/config` selectively. Remove only the [three obsolete Explorify/Lite config files](configuration.md#structure-generation) from the active host configuration; their absence from `build/server/` does not remove existing host copies. Preserve generated Floodgate keys, host-owned secrets, other settings, backup/rollback copies, world snapshots and unrelated files. Do not replace the whole config tree or copy old settings into replacement namespaces.
5. Reconcile the reviewed `build/server/squaremap/` overrides into `/squaremap`, preserving host-specific settings and unrelated files.
6. Apply selected values from `server.properties.example`, including `online-mode=true` and `enforce-secure-profile=false`; preserve DatHost-managed ports and secrets. Recheck the [Geyser network arrangement](#geyser-networking) and squaremap web address against verified host allocations before startup.
7. Start once, preserving an existing Floodgate key; let Floodgate generate its key only for a new instance. Verify config migration, actual listeners and advertised addresses, then test real Java and Bedrock login and chat.
8. Run `/jeb next` and verify the configured schedules and backup directory.
9. Create and verify the initial full backup before admitting players.
10. Restart and run the acceptance tests, including Bedrock reconnects and separate-instance full and differential restore drills.

## Rollback

If startup fails, stop the server before making further changes. Restore the prior `/mods`, `/config`, `/squaremap`, and world snapshot together. Do not allow a failed version migration to keep writing into the only world copy.

## Backups

JEB remains the backup component in the 26.3 candidate. Its checked-in policy limits retained backups to 6 GB and preserves an 8 GB free-space reserve. Keep DatHost's daily backup enabled as an independent layer and download an off-host snapshot before every pack or loader update.

Previously inspected JEB versions reset automatic timers at startup and config reload; verify that behavior again for the updated pin. Coordinate explicit full backups with the host's restart schedule, and verify completion before each scheduled restart. Follow [`storage-and-recovery.md`](storage-and-recovery.md) for the operating procedure and required full and differential restore drills.

## Optional Ledger deployment

Do not upload Ledger or Ledger Databases at launch. If their activation gate is later approved, use the proposed bounded MySQL configuration in [`storage-and-recovery.md`](storage-and-recovery.md), inject credentials on DatHost, and complete the documented failure and recovery tests first.
