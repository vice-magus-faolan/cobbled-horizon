# Deployment

These requirements apply to any selected host. Build and test a materialized server tree before upload; do not assume a provider imports packwiz or `.mrpack` files. Provider-specific offerings and account-verification questions belong in the [DatHost candidate profile](providers/dathost.md), not in the pack configuration. DatHost is a candidate, not a hosting decision. DatHost labels in `server.properties.example` and `squaremap/config.yml` are legacy provider comments, not requirements or verified allocations; apply the selected host's actual settings while preserving the security policy.

## Preflight

This 26.3 development candidate is not approved for deployment. Complete source/hosted review and the designated-host runtime acceptance first, including the Geyser beta and replacement structure gates. Preserve the 26.2 pack and its world snapshot as a separate rollback line.

- Confirm Java 25 and Fabric 0.20.1 for Minecraft 26.3, or an equivalent supported installation path for those pinned versions.
- Confirm a suitable Geyser UDP allocation and signaling arrangement as described in [Geyser networking](#geyser-networking); UDP alone is insufficient for this build.
- Confirm an HTTP port or proxy arrangement for squaremap.
- Verify the actual filesystem quota, backup retention/restore scope and quota accounting. Keep an independent daily host/provider backup layer enabled; JEB does not replace it. See [storage and recovery](storage-and-recovery.md).
- Confirm at least 8,192 MB remains free after the world, squaremap tiles, logs, and current JEB backups are present, with additional headroom for temporary backup work. Do not infer capacity from an advertised plan.
- Verify authenticated file upload, server console and stop/start access, permission bootstrap, secret storage and a usable rollback/restore route before changing the installation.
- Disable automatic mod/server-version updates.
- Establish the [full-backup procedure across restarts](storage-and-recovery.md#create-full-backups-across-restarts) before enabling unattended restarts.
- Take a host-level backup before replacing an existing installation.

## Geyser networking

The pinned beta `2.12.1-b1281` follows build 1280's removal of RakNet-only transport. Its signaling configuration defaults to `BUILTIN`: NetherNet media uses UDP, while built-in signaling uses TCP on the Bedrock port. Verify reachability for both protocols and use a Bedrock port distinct from Java's TCP listener. Alternatively, retain suitable UDP reachability and explicitly configure and verify an external signaling service. Do not assume a provider supplies either arrangement or silently enable an external service; any such service needs explicit approval and must preserve the authentication/privacy policy.

Before deployment, verify the exact build's config migration, actual UDP/TCP listeners (or external signaling connection), allocated ports and advertised addresses on the designated test host. Confirm real Bedrock joins and reconnects through that arrangement; a UDP allocation or successful bind alone is not acceptance. See the [cross-play gates](acceptance-tests.md#clients-and-cross-play). The checked-in config remains a policy input, not a verified schema or live allocation. Exact-build references: [build 1280](https://download.geysermc.org/v2/projects/geyser/versions/2.12.1/builds/1280), [build 1281](https://download.geysermc.org/v2/projects/geyser/versions/2.12.1/builds/1281), and [signaling configuration source](https://github.com/GeyserMC/Geyser/blob/b9d535a67cb6ef75a38140db0bd5ac2ccbe1e9ba/core/src/main/java/org/geysermc/geyser/configuration/GeyserConfig.java#L129-L158).

## Build

Run server materialization on the designated Minecraft test host, not on a lightweight control machine:

```bash
make test
make validate
make materialize
```

The generated server tree is `build/server/`. Inspect it before upload. It must contain the 32 active project JARs, including Explorify v1.6.6 rather than Structory, and reviewed config overrides, but no staged/client-only JARs or credentials. For pack `26.3.0.1.2`, verify the Epic override at `config/cristellib/mr_epic_structuresvillagesstandaloneedition/structure_placement_config.json5` is included with only `epic:villages` at spacing `80`, separation `22`, salt `50387312` and frequency `1.0`. Reconcile generated configs with the retained policy; distinguish the retired Lite file from the two legacy Explorify files awaiting schema review as described in [`configuration.md`](configuration.md#structure-generation).

## Upload

This procedure is operator guidance for a separately approved deployment, not permission to migrate or launch this candidate. With the target server stopped (paths below are relative to its server root):

1. Verify a completed host backup containing the current pack, configuration and matching world snapshot, with an off-host rollback copy. Preserve the 26.2 pack/world rollback line; do not alter backup copies during reconciliation.
2. Set the server type and version to Fabric / Minecraft 26.3 with the pinned loader.
3. Reconcile or replace only the active `/mods` set with the verified 32-project payload from `build/server/mods/`. Remove interim Structory, retired Creeper No Break Blocks and DnT Stronghold Lite JARs, along with superseded versions (including older Explorify), from that active set before startup. Keep the selected Explorify v1.6.6 JAR and verify the set matches the payload with no staged or extra JARs. A simple upload overlay leaves obsolete JARs installed.
4. Reconcile `build/server/config/` into `/config` selectively. Remove the [retired Lite config](configuration.md#structure-generation) and set aside only the two named legacy Explorify active-host files, preserving rollback copies, before reviewing newly generated Explorify configs against packaged defaults. Their absence from `build/server/` does not reconcile existing host copies; Explorify is active, but the old schemas are unverified. Preserve generated Floodgate keys, host-owned secrets, other settings, backup/rollback copies, world snapshots and unrelated files. Do not replace the whole config tree or copy old settings into replacement namespaces. Preserve the Cristel/Towns and Towers policy and complete Nether Black Spiral generation/performance acceptance before deployment.
   Include the reviewed Epic placement file at its exact owning-loader-ID path above; do not substitute an `epic/` directory or the BuiltInAPI filename. Review any existing host copy before replacing just that file, preserving rollback copies and generic Cristel settings. Confirm actual loading and the [fresh-chunk acceptance checks](acceptance-tests.md#world-generation) before pre-generation. The policy does not remove existing settlements or impose cross-mod clearance.
5. Reconcile the reviewed `build/server/squaremap/` overrides into `/squaremap`, preserving host-specific settings and unrelated files.
6. Apply selected values from `server.properties.example`, including `online-mode=true` and `enforce-secure-profile=false`; preserve host-managed ports and secrets. Recheck the [Geyser network arrangement](#geyser-networking) and squaremap web address against verified host allocations before startup.
7. Start once, preserving an existing Floodgate key; let Floodgate generate its key only for a new instance. Verify config migration, actual listeners and advertised addresses, then test real Java and Bedrock login and chat.
8. Run `/jeb next` and verify the configured schedules and backup directory.
9. Create and verify the initial full backup before admitting players.
10. Restart and run the acceptance tests, including Bedrock reconnects and separate-instance full and differential restore drills.

## Rollback

If startup fails, stop the server before making further changes. Restore the prior `/mods`, `/config`, `/squaremap`, and world snapshot together. Do not allow a failed version migration to keep writing into the only world copy.

## Backups

JEB remains the backup component in the 26.3 candidate. Its checked-in policy limits retained backups to 6,144 MB per world and preserves an 8,192 MB free-space reserve. Keep the independently managed daily host/provider backup layer enabled, verify its scope and restore behavior, and download an off-host snapshot before every pack or loader update. A different advertised storage allocation is not a reason to retune JEB automatically.

Previously inspected JEB versions reset automatic timers at startup and config reload; verify that behavior again for the updated pin. Coordinate explicit full backups with the host's restart schedule, and verify completion before each scheduled restart. Follow [`storage-and-recovery.md`](storage-and-recovery.md) for the operating procedure and required full and differential restore drills.

## Optional Ledger deployment

Do not upload Ledger or Ledger Databases at launch. If their activation gate is later approved, use the proposed bounded MySQL configuration in [`storage-and-recovery.md`](storage-and-recovery.md), verify the selected database service and inject credentials only on the deployment host, and complete the documented failure and recovery tests first. An included database offer is not proof of compatibility, capacity or recovery.
