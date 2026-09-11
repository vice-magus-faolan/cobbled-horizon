# Storage, backups, and optional event logging

Cobbled Horizon treats DatHost's 30 GB filesystem as a shared failure budget for the world, pregenerated chunks, squaremap tiles, logs, temporary backup work, and retained backups.[4]

## Launch policy

- **JEB is active in the 26.2 baseline.** It is configured conservatively, but it is not production-proven until the acceptance-test restore drill passes.
- **Ledger is not part of the launch baseline.** For a small allowlisted server, the operational cost and unbounded-growth risk are not justified until moderation history or surgical rollback is demonstrably needed.
- **DatHost's daily backup remains enabled.** JEB is an application-aware recovery layer, not a replacement for the provider's independent backup.[4]
- Keep an off-host copy before every pack, loader, world-generation, or configuration migration.

## JEB configuration

JEB supports full, partial, and differential schedules, dependency-aware retention, a per-world total-size cap, strict integrity checks, and a minimum-free-space preflight.[5][6]

The checked-in `config/justenoughbackups.json` applies this initial policy:

- full backup every 1,440 minutes;
- differential backup every 180 minutes;
- partial backups disabled;
- schedules pause when no player activity has occurred;
- server-start and server-stop backups disabled;
- two full backups and sixteen differential backups retained;
- 6,144 MB maximum JEB storage per world;
- 8,192 MB minimum free-space reserve;
- strict integrity mode and two worker threads.

The 6 GB cap limits retained archives; the 8 GB reserve protects operating headroom and can cause backups to fail early rather than fill the volume. JEB's preflight also accounts for the active world and temporary compression needs, so monitor failures and actual world, map, and backup sizes instead of assuming the caps guarantee capacity.[5][6]

### Operational checks

- Inspect `/jeb next` after startup and after `/jeb config reload`.
- Alert on backup failures, less than 8 GB free space, or unexpected growth in `world/`, `squaremap/`, or `backups/`.
- Confirm DatHost's backup retention, restore scope, and whether provider backups count against the 30 GB allocation before launch.
- Do not increase JEB retention without a storage-budget review.

### Required cold-restore drill

1. Create a named full backup with `/jeb create full pre-restore-test`.
2. Confirm it appears in `/jeb list` and that the backup archive is non-empty.
3. Stop the source server cleanly.
4. Materialize the exact same pack commit into a separate disposable server instance.
5. Copy the selected JEB backup into that instance's backup directory.
6. Start the disposable instance, select the copied backup with `/jeb restore <backup>`, and allow JEB to prepare the restore and stop the server.[6]
7. Start it again and require Minecraft's own `Done` readiness line.
8. Join with Java, inspect representative chunks and inventories, and stop cleanly.
9. Record the pack commit, backup name, restored world identity, and result in `docs/verification.md`.

Do not treat archive creation as proof of recovery. If this drill fails, JEB remains installed for investigation but production launch is blocked until it is fixed or replaced.

## Proposed Ledger deployment

Ledger logs server-side world changes for inspection, search, and rollback.[1] Its default `autoPurgeDays = -1` means actions are never purged automatically, which is unacceptable on this storage-constrained deployment.[2]

Ledger may be promoted only after its gate in `candidates.toml` passes. The preferred architecture is Ledger plus Ledger Databases using DatHost's included MySQL service, keeping the event store off the 30 GB game filesystem.[3][4] A separate database VM is a fallback only if DatHost's MySQL capacity, latency, backup, or connectivity is insufficient.

Proposed `config/ledger.toml` additions, using runtime-injected values rather than committed credentials:

```toml
[database]
autoPurgeDays = 30
queueTimeoutMin = 5
queueCheckDelaySec = 10
batchSize = 1000
batchDelay = 10
logSQL = false
updateSchema = false

[database_extensions]
database = "MYSQL"
url = "<MYSQL_HOST>:<MYSQL_PORT>/<MYSQL_DATABASE>"
username = "<MYSQL_USERNAME>"
password = "<MYSQL_PASSWORD>"
properties = []
maxPoolSize = 5
connectionTimeout = 10000
```

Ledger Databases documents the MySQL URL, username, password, pool-size, and connection-timeout fields and requires the database name in the URL.[3]

### Ledger promotion gates

- Confirm DatHost's MySQL quota, backups, network path, and credentials workflow.
- Keep `autoPurgeDays` finite; begin at 30 days and review measured growth after one week and one month.
- Limit inspect/search to administrators and grant purge/rollback separately using LuckPerms.
- Filter high-volume environmental events only after measuring them; retain player-caused block and container activity needed for investigations.
- Monitor queue depth, database size, purge execution, query latency, and failed inserts.
- Test database latency, connection loss, server shutdown with queued writes, purge, inspect, and rollback on a disposable world.
- Back up MySQL with a database-aware mechanism; do not copy a live file-backed database and assume it is consistent.
- Keep secrets out of Git, packwiz exports, logs, and support bundles.

If Ledger's database fails, gameplay availability and bounded queue behavior matter more than preserving every audit event. Do not promote it until that failure mode is observed and accepted.

## Sources

[1] https://modrinth.com/mod/ledger — Ledger — Modrinth
[2] https://quiltservertools.github.io/Ledger/latest/config — Ledger configuration
[3] https://modrinth.com/mod/ledger-databases — Ledger Databases — Modrinth
[4] https://dathost.com/minecraft-server-hosting — DatHost Minecraft hosting
[5] https://modrinth.com/mod/justenoughbackups-jeb — Just Enough Backups — Modrinth
[6] https://github.com/frandm16/JustEnoughBackups — Just Enough Backups — source
