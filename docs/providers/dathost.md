# DatHost provider profile

See the [deployment report](../verification.md#current-deployment). Hosted native acceptance ran in disposable Docker containers on GitHub Actions runners, not on DatHost. See the [dated verification record](../verification.md#current-263-evidence). This profile retains provider-specific claims and unresolved account questions. The [deployment runbook](../deployment.md) remains authoritative for build, reconciliation, networking, security and rollback on any host; changing providers must not require changing the core pack or dropping those safeguards.

## Advertised offering, not verified entitlement

The [DatHost Minecraft hosting page](https://dathost.com/minecraft-server-hosting), retrieved **2026-11-11**, advertises **60 GB included NVMe storage**, daily backups and an included MySQL database. This supersedes the older 30 GB assumption in these runbooks; it is neither a measured account quota nor a new pack limit. Actual allocation, backup scope/retention/quota accounting, database access and TCP/UDP allocations remain unverified.

Do not increase JEB's checked-in **6,144 MB per-world retention cap** or reduce its **8,192 MB free-space reserve** based on that advertisement. Budget world growth, map tiles, logs, retained archives and temporary backup work against the selected account's verified usable capacity. Follow [storage and recovery](../storage-and-recovery.md), including its explicit-full-backup responsibility and real full/differential restore drills.

## Outstanding account checks

Record the actual answers for the selected account; a public feature listing is not acceptance:

- **Runtime and panel:** Can the account install Minecraft 26.3, Fabric Loader 0.20.1 and Java 25 without silently updating pins? Verify the supported installation path and disable automatic mod/server-version updates.
- **Upload and control:** Verify authenticated panel/file-transfer access to the actual server root, selective mods/config/squaremap upload, console commands, clean stop/start and rollback restoration. Check the documented [import choices](#modpack-import-options) against the actual account before using them. Otherwise upload the inspected server payload using the stopped-server [reconciliation procedure](../deployment.md#upload), not a manifest archive or an overlay alone. Preserve host-managed settings, secrets and Floodgate keys.
- **Game ports:** Obtain the actual Java TCP allocation and Geyser UDP/TCP allocation. Can the account support UDP media plus built-in TCP signaling on a Bedrock port distinct from Java's TCP listener? If not, is an explicitly approved external-signaling arrangement feasible with suitable UDP reachability? Apply the exact-build [Geyser networking checks](../deployment.md#geyser-networking); a generic Bedrock/UDP offer is insufficient.
- **Map endpoint:** Is a suitable HTTP allocation or supported proxy available? Verify its public address and intentionally public player-tracker exposure before publishing squaremap. A game port does not establish an HTTP endpoint or login boundary.
- **Storage:** What is the usable quota for this account, and do worlds, map tiles, logs, temporary work, JEB archives, provider snapshots or database storage share it? Verify headroom and failure alerts rather than treating advertised 60 GB as entitlement.
- **Daily backups:** Are backups enabled for this account? Confirm schedule, retention, quota accounting, world/config/mod/key scope, consistency, download/off-host access and restoration to a separate instance. Who detects failure and owns restoration? Keep this independent layer enabled; do not infer database coverage or a tested restore from the advertisement.
- **MySQL, future only:** If Ledger promotion is separately approved, verify compatible MySQL version, capacity/quota, credentials workflow, network reachability, access restrictions, latency and database-aware backup/restore. The advertised included service does not establish any of these. Use [Ledger's promotion gates](../storage-and-recovery.md#ledger-promotion-gates); do not upload or activate Ledger at launch.

## Modpack import options

DatHost's [Minecraft: Installing Modpacks](https://help.dathost.net/article/179-minecraft-mods-modpacks) guide, checked again **2026-11-19**, describes three methods. Its CurseForge URL importer under **Mods & Plugins → Mods & Modpacks** selects the **newest available server pack**, even when the copied link points to an older version. A URL therefore does not pin an older release. The guide says Modrinth URLs are not accepted by that CurseForge field. Methods 2 and 3 use a prepared server-pack ZIP under **Mods & Plugins → Custom upload**; a `.mrpack` is not that server-folder archive. This pack publishes no CurseForge listing or public server ZIP.

For a private installation on the owner's own server, prepare the exact selected payload on the designated Minecraft host:

```bash
make server-zip
```

This materializes and validates a fresh `build/server/`, then creates `build/cobbled-horizon-<pack-version>-server.zip`, using the version from `pack.toml`. Contents sit at the ZIP root: all selected pinned JARs in `mods/`, reviewed `config/` and `squaremap/` overrides, and recipient notices. It contains no Minecraft/Fabric runtime, world, Floodgate key or live LuckPerms data. Names, timestamps and permissions are normalized; existing folder and ZIP destinations are refused. Use a fresh owned `SERVER_DIR` if a preparation folder already exists, and move aside only a prior ZIP you own rather than expecting overwrite. See [build instructions](../deployment.md#build), including the matching-source route for a downloaded release.

After the stopped-server safeguards below, choose **Custom upload** and select this local `-server.zip`, not a renamed `.mrpack`. The command reports its actual byte size and warns above **100 MB** (100,000,000 bytes). DatHost's [file-upload reference](https://dathost.net/reference/post_game_server_files_item), checked **2026-11-19**, documents the 100 MB web limit and FTP for larger files. For a larger pack, or when safe Custom-upload preservation cannot be established, use authenticated FTP/file-manager transfer of the inspected extracted contents under the [selective reconciliation procedure](../deployment.md#upload); the same web limit may apply to a file manager's browser upload. Do not split, omit or replace pinned mods to fit the limit.

Before any replacement, **stop the instance** and verify a completed off-host backup of the current pack, configuration and matching **world data**, preserving the **Floodgate key** and **`mods/luckperms/`** backend/exports/private data separately. DatHost's guide calls for removing an installed modpack before Custom upload; verify that action's exact scope before using it. Never delete a world, key, host setting or LuckPerms directory as part of clearing the old mod JAR set. If the panel cannot preserve these safely, use selective transfer instead. Reconcile retired JARs and configs rather than overlaying blindly, then follow the remaining [upload, acceptance and rollback steps](../deployment.md#upload).

Private owner installation does not require a public redistribution-clearance record. This is not permission to publish the complete ZIP or share it with others: the applicable permissions, notices and source-delivery obligations still apply. `make server-zip` is local-only; CI never builds, uploads or caches a real complete server ZIP, and the release plan never selects it. Runtime provisioning/account compatibility and CurseForge moderation remain separate. Java clients remain vanilla; Bedrock joins retain the Geyser/Floodgate contract.

## Acceptance remains separate

No hosting account, port allocation, provider backup or MySQL service has been independently tested by this reconciliation. The successful hosted native run establishes bounded install/restart, config and synthetic permission-import behavior, not generation/performance, real Java/Bedrock joins and graves, live account permissions or backup restoration. The remaining [acceptance tests](../acceptance-tests.md) are outstanding evidence for this pack; see the [deployment report](../verification.md#current-deployment). Perform those checks on the designated Minecraft test host; any subsequent live changes, including the [permission bootstrap](../permissions.md), still need operator authorization and the runbook's backup/preservation safeguards.
