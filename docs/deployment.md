# Deployment

These requirements apply to any selected host. Build and test a materialized server tree before upload; do not assume a provider imports packwiz or `.mrpack` files. Provider-specific offerings and account-verification questions belong in the [DatHost profile](providers/dathost.md), not in the pack configuration. See the [deployment report](verification.md#current-deployment). DatHost labels in `server.properties.example` and `squaremap/config.yml` are not verified allocations; apply the selected host's actual settings while preserving the security policy.

## Preflight

See the [deployment report](verification.md#current-deployment) and the [verification record](verification.md#current-263-evidence) for hosted native install/restart, selected config/permission-import evidence and outstanding checks. For subsequent installations or changes, use the preflight below and preserve the 26.2 pack and its world snapshot as a separate rollback line. Private installation on the owner's own server does not require a public redistribution-clearance record. Sharing or public distribution still requires the applicable exact-pin [distribution and source-delivery obligations](../README.md#ownership-and-licensing); archive integrity alone does not authorize sharing.

- Confirm Java 25 and Fabric 0.20.1 for Minecraft 26.3, or an equivalent supported installation path for those pinned versions.
- Confirm a suitable Geyser UDP allocation and signaling arrangement as described in [Geyser networking](#geyser-networking); UDP alone is insufficient for this build.
- Confirm an HTTP port or proxy arrangement for squaremap.
- Verify the actual filesystem quota, backup retention/restore scope and quota accounting. Keep an independent daily host/provider backup layer enabled; JEB does not replace it. See [storage and recovery](storage-and-recovery.md).
- Confirm at least 8,192 MB remains free after the world, squaremap tiles, logs, and current JEB backups are present, with additional headroom for temporary backup work. Do not infer capacity from an advertised plan.
- Verify authenticated file upload, server console and stop/start access, permission bootstrap, secret storage and a usable rollback/restore route before changing the installation.
- Before enabling SlashLoot on an existing world, complete the [ordinary and mixed-double storage, real Java and Bedrock, private-inventory restart and basic rollback checks](acceptance-tests.md#personal-loot). Generated loot containers can lose all players’ private items on source destruction/cleanup; this accepted lifecycle limitation is not an additional deployment hold. No all-player escrow or lossless-uninstall gate or historical migration is required for normal adoption. Reconcile an existing host-owned SlashLoot config deliberately; this pack ships no override.
- Disable automatic mod/server-version updates.
- Establish the [full-backup procedure across restarts](storage-and-recovery.md#create-full-backups-across-restarts) before enabling unattended restarts.
- Take a host-level backup before replacing an existing installation.

## Geyser networking

The pinned beta `2.12.1-b1281` follows build 1280's removal of RakNet-only transport. Its signaling configuration defaults to `BUILTIN`: NetherNet media uses UDP, while built-in signaling uses TCP on the Bedrock port. Verify reachability for both protocols and use a Bedrock port distinct from Java's TCP listener. Alternatively, retain suitable UDP reachability and explicitly configure and verify an external signaling service. Do not assume a provider supplies either arrangement or silently enable an external service; any such service needs explicit approval and must preserve the authentication/privacy policy.

Verification of the exact build's config migration, actual UDP/TCP listeners (or external signaling connection), allocated ports and advertised addresses remains outstanding on the designated test host. Confirm real Bedrock joins and reconnects through that arrangement; a UDP allocation or successful bind alone is not acceptance. See the [cross-play gates](acceptance-tests.md#clients-and-cross-play). The checked-in config remains a policy input, not a verified schema or live allocation. Exact-build references: [build 1280](https://download.geysermc.org/v2/projects/geyser/versions/2.12.1/builds/1280), [build 1281](https://download.geysermc.org/v2/projects/geyser/versions/2.12.1/builds/1281), and [signaling configuration source](https://github.com/GeyserMC/Geyser/blob/b9d535a67cb6ef75a38140db0bd5ac2ccbe1e9ba/core/src/main/java/org/geysermc/geyser/configuration/GeyserConfig.java#L129-L158).

## Build

Run server preparation on the designated Minecraft test host, not on a lightweight control machine:

```bash
make test
make validate
make server-zip
```

`make server-zip` first runs `make materialize`: it validates the `.mrpack`, downloads every original pinned mod and writes indexed configs/notices to a fresh `build/server/`. It then revalidates that folder and creates `build/cobbled-horizon-<pack-version>-server.zip`, using the version from `pack.toml`, with contents at the ZIP root, sorted names, fixed timestamps and 0644 file / 0755 directory modes. Preparation never starts Minecraft. Keep the folder quiescent while archiving. Neither an existing server directory nor an existing ZIP is overwritten; use a fresh owned `SERVER_DIR=build/server-inspect` if needed and move aside only a prior ZIP you own. `make materialize` remains available when only the folder is wanted.

The command reports actual ZIP bytes and warns above DatHost's 100 MB (100,000,000-byte) web-upload limit. Use the [Custom upload instructions](providers/dathost.md#modpack-import-options) for this local prepared ZIP, or authenticated FTP/file-manager transfer of the extracted contents for larger files; a browser file-manager upload is not necessarily exempt from the web limit. Do not rename a `.mrpack` into a ZIP. CI never builds, uploads or caches a real complete server ZIP, and the release plan never selects it. Private owner installation needs no public redistribution-clearance record; sharing binaries still requires the applicable permissions, notices and source-delivery obligations. The public pipeline publishes only the no-JAR `.mrpack` and its checksum. The hosted native job materializes that `.mrpack` before real first-install/restart without uploading JARs.

The generated server tree is `build/server/`. Inspect it before upload. It must contain all active project JARs selected in `collection.toml`, including Explorify v1.6.6 rather than Structory, and reviewed config overrides, but no staged/client-only JARs or credentials. For the current pack, verify the Epic override at `config/cristellib/mr_epic_structuresvillagesstandaloneedition/structure_placement_config.json5` is included with only `epic:villages` at spacing `80`, separation `22`, salt `50387312` and frequency `1.0`. Reconcile generated configs with the retained policy; distinguish the retired Lite file from the two legacy Explorify files awaiting schema review as described in [`configuration.md`](configuration.md#structure-generation).

For a downloaded release through `v26.3.0.1.4`, download `cobbled-horizon-<pack-version>.sha256` beside the `.mrpack`. This legacy checksum also lists the retired ZIP; downloading that ZIP is unnecessary. In the download directory, replace `<pack-version>` with the release's version and run:

```bash
MRPACK='cobbled-horizon-<pack-version>.mrpack'
sha256sum --check --ignore-missing cobbled-horizon-<pack-version>.sha256
```

Require the `.mrpack` line to say **OK**. The command ignores missing files; an absent `.mrpack` result is not verification.

Future releases from the mrpack-only pipeline instead provide `.mrpack.sha256`. Download it beside the `.mrpack`, set `MRPACK` to that release's filename as above, and run:

```bash
sha256sum --check "$MRPACK.sha256"
```

After verification, use the matching source revision, place the `.mrpack` under `dist/` and create the `build/` parent. Prepare the private folder and optional ZIP:

```bash
python3 scripts/server_folder.py materialize "dist/$MRPACK" build/server
python3 scripts/server_folder.py zip build/server build/cobbled-horizon-<pack-version>-server.zip
```

This validates all original pins, configs and recipient notices. `python3 scripts/server_folder.py validate build/server` checks the unmodified prepared folder before runtime provisioning. Provision Minecraft 26.3, Fabric 0.20.1 and Java 25 separately; preparation includes no runtime, launch scripts, EULA, world or host secrets.

Retain recipient credits/licenses/source directions. Complete stopped-server reconciliation; overlaying a fresh folder does not remove retired JARs or protect existing host configuration. Provider import limitations remain in the [provider profile](providers/dathost.md#modpack-import-options).

The current payload also includes the reviewed MSS/Hopo controls and the canonical/import-ready permission seed under `config/cobbled-horizon/`. Verify these exact bytes through the matching archive validator; do not copy a live LuckPerms directory into an export.

## Upload

This procedure covers an operator-authorized installation or update; live changes require separate authorization. With the target server stopped (paths below are relative to its server root):

1. Verify a completed host backup containing the current pack, configuration and matching world snapshot, with an off-host rollback copy. Preserve the 26.2 pack/world rollback line; do not alter backup copies during reconciliation. Before a provider's removal or Custom upload action, separately preserve world data, the generated Floodgate key and `mods/luckperms/` (backend, exports and private data). Confirm the panel's exact removal/extraction scope; if it cannot preserve host-owned data safely, use selective FTP/file-manager transfer instead.
2. Set the server type and version to Fabric / Minecraft 26.3 with the pinned loader.
3. Preserve the host-owned `mods/luckperms/` directory (including its configured backend, native exports and private data) separately from the mod JAR set. Reconcile or replace only the active `/mods` JAR set with the verified `build/server/mods/` payload, matching the projects selected in `collection.toml`. Remove interim Structory, retired Creeper No Break Blocks and DnT Stronghold Lite JARs, along with superseded versions (including older Explorify), from that active set before startup. Keep the selected Explorify v1.6.6 JAR and verify the set matches the payload with no staged or extra JARs. A simple upload overlay leaves obsolete JARs installed.
4. Reconcile `build/server/config/` into `/config` selectively. Remove the [retired Lite config](configuration.md#structure-generation) and set aside only the two named legacy Explorify active-host files, preserving rollback copies, before reviewing newly generated Explorify configs against packaged defaults. Their absence from `build/server/` does not reconcile existing host copies; Explorify is active, but the old schemas are unverified. Preserve generated Floodgate keys, host-owned secrets, other settings, backup/rollback copies, world snapshots and unrelated files. Do not replace the whole config tree or copy old settings into replacement namespaces. Preserve the Cristel/Towns and Towers policy; Nether Black Spiral generation/performance checks remain outstanding and are required before pre-generation.
   Reconcile only the reviewed MSS/Hopo placement/toggle files, preserving rollback copies of old and any `-had-error` files outside active config paths; do not blindly restore stale tree-set schemas. Confirm all eight MSS tree variants and both Hopo additions remain enabled and there is no missing-set recovery. Keep Moog rarity inputs unchanged.
   Include the reviewed Epic placement file at its exact owning-loader-ID path above; do not substitute an `epic/` directory or the BuiltInAPI filename. Review any existing host copy before replacing just that file, preserving rollback copies and generic Cristel settings. Confirm actual loading and the [fresh-chunk acceptance checks](acceptance-tests.md#world-generation) before pre-generation. The policy does not remove existing settlements or impose cross-mod clearance.
5. Reconcile the reviewed `build/server/squaremap/` overrides into `/squaremap`, preserving host-specific settings and unrelated files.
6. Apply selected values from `server.properties.example`, including `online-mode=true` and `enforce-secure-profile=false`; preserve host-managed ports and secrets. Recheck the [Geyser network arrangement](#geyser-networking) and squaremap web address against verified host allocations before startup.
7. Start once, preserving an existing Floodgate key; let Floodgate generate its key only for a new instance. Verify config migration, actual listeners and advertised addresses, then test real Java and Bedrock login and chat.
8. Apply the [one-time permission bootstrap](permissions.md) after its existing-data preflight and private backup; assign accounts/OP separately and verify effective role boundaries before admitting players. From console, run `jeb next` and `jeb list` to inspect schedules/archives. The schedule object, not the ignored legacy enable flag, controls this pin; neither listing proves a completed backup or restore.
9. Create and verify the initial full backup before admitting players.
10. Restart and run the acceptance tests, including Bedrock reconnects and separate-instance full and differential restore drills.

## Rollback

If startup fails, stop the server before making further changes. Restore the prior `/mods`, `/config`, `/squaremap`, and world snapshot together, including all dimensions, player inventories and identities and matching SlashLoot private state. Do not restore a loot ledger independently after rewards have moved into player inventories. Do not allow a failed version migration to keep writing into the only world copy.

If the one-time group import was applied, also restore or reconcile the LuckPerms backend from its private pre-import backup through the [separately approved recovery procedure](permissions.md#one-time-group-import). Restoring server files does not revert an external LuckPerms backend.

## Backups

JEB remains the backup component in this pack. Its checked-in policy limits retained backups to 6,144 MB per world and preserves an 8,192 MB free-space reserve. Keep the independently managed daily host/provider backup layer enabled, verify its scope and restore behavior, and download an off-host snapshot before every pack or loader update. A different advertised storage allocation is not a reason to retune JEB automatically.

Previously inspected JEB versions reset automatic timers at startup and config reload; verify that behavior again for the updated pin. Coordinate explicit full backups with the host's restart schedule, and verify completion before each scheduled restart. Follow [`storage-and-recovery.md`](storage-and-recovery.md) for the operating procedure and required full and differential restore drills.

## Optional Ledger deployment

Do not upload Ledger or Ledger Databases at launch. If their activation gate is later approved, use the proposed bounded MySQL configuration in [`storage-and-recovery.md`](storage-and-recovery.md), verify the selected database service and inject credentials only on the deployment host, and complete the documented failure and recovery tests first. An included database offer is not proof of compatibility, capacity or recovery.
