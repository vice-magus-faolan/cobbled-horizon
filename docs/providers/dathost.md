# DatHost provider profile

This profile records provider-specific claims and unresolved account checks for the 26.2 line. The [deployment runbook](../deployment.md) remains authoritative for build, reconciliation, security and rollback. Documentation and source checks are not deployment approval or live account acceptance.

## Advertised offering, not verified entitlement

The [DatHost Minecraft hosting page](https://dathost.com/minecraft-server-hosting), retrieved **2026-11-11**, advertises **60 GB included NVMe storage**, daily backups and an included MySQL database. This supersedes the older 30 GB assumption in these runbooks; it is neither a measured account quota nor a new pack limit. Actual allocation, backup scope/retention/quota accounting, database access and port allocations remain unverified.

Do not increase JEB's checked-in **6,144 MB per-world retention cap** or reduce its **8,192 MB free-space reserve** based on that advertisement. Budget world growth, map tiles, logs, retained archives and temporary backup work against the account's verified usable capacity. Follow [storage and recovery](../storage-and-recovery.md), including its explicit-full-backup responsibility and real full/differential restore drills.

## Account checks before deployment

Record the actual answers for the selected account; a public feature listing is not acceptance:

- **Runtime and panel:** Can the account install Minecraft 26.2, Fabric Loader 0.19.5 and Java 25 without silently updating pins? Verify the supported installation path and disable automatic mod/server-version updates.
- **Upload and control:** Verify authenticated panel/file-transfer access to the actual server root, selective mods/config/squaremap upload, console commands, clean stop/start and rollback restoration. Check the documented [import choices](#modpack-import-options) against the actual account before using them. Preserve host-managed settings, secrets and Floodgate keys.
- **Game ports:** Obtain the actual Java TCP and reachable Geyser UDP allocations. Verify real Java and Bedrock joins against this line's selected pins; a generic provider offer is insufficient.
- **Map endpoint:** Verify the squaremap HTTP allocation or proxy and intentionally public player-tracker exposure. A game port does not establish an HTTP endpoint or login boundary.
- **Storage:** Verify usable quota and whether worlds, map tiles, logs, temporary work, JEB archives, provider snapshots or database storage share it. Do not treat advertised 60 GB as entitlement.
- **Daily backups:** Confirm schedule, retention, quota accounting, world/config/mod/key scope, consistency, off-host access and separate-instance restoration. Assign responsibility for failure detection and recovery. Do not infer database coverage or a tested restore from the advertisement.
- **MySQL, future only:** If Ledger promotion is separately approved, verify compatible MySQL version, capacity/quota, credentials workflow, network reachability, access restrictions, latency and database-aware backup/restore. The advertised included service does not establish any of these. Use [Ledger's promotion gates](../storage-and-recovery.md#ledger-promotion-gates); do not upload or activate Ledger at launch.

## Modpack import options

For modpack import, ZIP preparation, upload limits, FTP transfer and stopped-server backups, follow the [deployment runbook](../deployment.md).

## Acceptance remains separate

No hosting account, port allocation, provider backup or MySQL service has been tested by this documentation change. Source checks and public claims do not establish clean boot, generation/performance, real Java/Bedrock joins and graves, permission boundaries or backup restoration. Complete the [acceptance tests](../acceptance-tests.md) on the designated Minecraft test host and obtain separate deployment approval before applying the [permission bootstrap](../permissions.md) and production runbook.
