# DatHost candidate-provider profile

DatHost is under consideration, not selected or deployment-approved. This profile holds provider-specific claims and unresolved account questions. The [deployment runbook](../deployment.md) remains authoritative for build, reconciliation, networking, security and rollback on any host; changing providers must not require changing the core pack or dropping those safeguards.

## Advertised offering, not verified entitlement

The [DatHost Minecraft hosting page](https://dathost.com/minecraft-server-hosting), retrieved **2026-11-11**, advertises **60 GB included NVMe storage**, daily backups and an included MySQL database. This supersedes the older 30 GB assumption in these runbooks; it is neither a measured account quota nor a new pack limit. Actual allocation, backup scope/retention/quota accounting, database access and TCP/UDP allocations remain unverified.

Do not increase JEB's checked-in **6,144 MB per-world retention cap** or reduce its **8,192 MB free-space reserve** based on that advertisement. Budget world growth, map tiles, logs, retained archives and temporary backup work against the selected account's verified usable capacity. Follow [storage and recovery](../storage-and-recovery.md), including its explicit-full-backup responsibility and real full/differential restore drills.

## Account checks before selection or deployment

Record the actual answers for the selected account; a public feature listing is not acceptance:

- **Runtime and panel:** Can the account install Minecraft 26.3, Fabric Loader 0.20.1 and Java 25 without silently updating pins? Verify the supported installation path and disable automatic mod/server-version updates.
- **Upload and control:** Verify authenticated panel/file-transfer access to the actual server root, selective mods/config/squaremap upload, console commands, clean stop/start and rollback restoration. Check the documented [import choices](#modpack-import-options) against the actual account before using them. Otherwise upload the inspected server payload using the stopped-server [reconciliation procedure](../deployment.md#upload), not a manifest archive or an overlay alone. Preserve host-managed settings, secrets and Floodgate keys.
- **Game ports:** Obtain the actual Java TCP allocation and Geyser UDP/TCP allocation. Can the account support UDP media plus built-in TCP signaling on a Bedrock port distinct from Java's TCP listener? If not, is an explicitly approved external-signaling arrangement feasible with suitable UDP reachability? Apply the exact-build [Geyser networking checks](../deployment.md#geyser-networking); a generic Bedrock/UDP offer is insufficient.
- **Map endpoint:** Is a suitable HTTP allocation or supported proxy available? Verify its public address and intentionally public player-tracker exposure before publishing squaremap. A game port does not establish an HTTP endpoint or login boundary.
- **Storage:** What is the usable quota for this account, and do worlds, map tiles, logs, temporary work, JEB archives, provider snapshots or database storage share it? Verify headroom and failure alerts rather than treating advertised 60 GB as entitlement.
- **Daily backups:** Are backups enabled for this account? Confirm schedule, retention, quota accounting, world/config/mod/key scope, consistency, download/off-host access and restoration to a separate instance. Who detects failure and owns restoration? Keep this independent layer enabled; do not infer database coverage or a tested restore from the advertisement.
- **MySQL, future only:** If Ledger promotion is separately approved, verify compatible MySQL version, capacity/quota, credentials workflow, network reachability, access restrictions, latency and database-aware backup/restore. The advertised included service does not establish any of these. Use [Ledger's promotion gates](../storage-and-recovery.md#ledger-promotion-gates); do not upload or activate Ledger at launch.

## Modpack import options

DatHost's [Minecraft: Installing Modpacks](https://help.dathost.net/article/179-minecraft-mods-modpacks) guide, inspected **2026-11-13** (page updated November 3), documents CurseForge URL import under **Mods & Plugins → Mods & Modpacks**, and server-pack ZIP import under **Mods & Plugins → Custom upload**. Its URL importer selects the **newest available server pack**, even when the copied link points to an older version. A URL therefore does not pin an older release. The guide says Modrinth URLs are not accepted by that CurseForge field and a `.mrpack` is not a prepared server ZIP.

For a separately approved installation of an exact Cobbled Horizon version, use its checksum-verified additional `cobbled-horizon-<version>-server.zip`, not the main CurseForge manifest-format `.zip` or `.mrpack`. The standalone ZIP places `mods/`, `config/` and `squaremap/` at its root; runtime provisioning and account import compatibility still need verification. No CurseForge listing/upload is configured or implied. The provider's generic advice to install matching client mods does not apply to this server-only collection: Java clients remain vanilla.

Before any replacement, verify the account permissions, exact Minecraft/Fabric/Java pins, backups and rollback route in the [deployment preflight](../deployment.md#preflight). DatHost's guide calls for removing an installed modpack before Custom upload; do not apply that action to an existing world or host-owned files without verifying its scope and preserving keys/settings and a complete off-host backup. Use the stopped-server reconciliation procedure when safe selective preservation cannot be established. These are documented provider behaviors, not a tested account import or runtime success.

## Acceptance remains separate

No hosting account, port allocation, provider backup or MySQL service has been tested by this documentation change. Source checks and public claims do not establish clean boot, generation/performance, real Java/Bedrock joins and graves, permission boundaries or backup restoration. Complete the [acceptance tests](../acceptance-tests.md) on the designated Minecraft test host and obtain separate deployment approval before applying the [permission bootstrap](../permissions.md) and production runbook.
