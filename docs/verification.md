# Verification record

## Superseded full-stack smoke test

Date: 2026-09-10 UTC

The original 27-project test candidate was exported with packwiz, materialized with `mrpack-install v0.16.10`, and run using Temurin Java `25.0.4.1`. It included Krypton, Fast Noise, ZConfig, and ScalableLux, which are now staged outside the baseline.

This initial smoke test was run on the control host before the test-host boundary was established. That was an operational mistake. Future Minecraft server execution belongs exclusively on the designated Minecraft test host; the control host is limited to static pack validation and export.

Observed server result:

```text
Minecraft server: Done (30.553s)! For help, type "help"
Registered 199 custom block overrides.
Registered 7 custom blocks.
Started Geyser on UDP port 19132
Geyser: Done (5.346s)! Run /geyser help for help!
```

The two `Done` lines are separate readiness events: `30.553s` is the Minecraft server startup, while `5.346s` is Geyser's own initialization message.

The server then accepted `stop`, shut down Geyser and squaremap's Undertow web server, saved the Overworld, Nether, and End, and exited with status 0.

This historical result verifies the superseded full-stack candidate only. It does not prove the current conservative baseline.

## Initial 26.2 baseline export

Date: 2026-09-11 UTC

The active pack now contains 24 projects, including JEB 1.2.0.6+26.2. Local static verification completed with:

```text
make test
-> 5 tests passed

make validate
-> PASS: baseline 20 selected + 4 dependencies; staged 3 selected + 1 dependency; 5 future candidates; 51 indexed pack files

make export
python3 scripts/validate_mrpack.py dist/cobbled-horizon-0.1.0+mc26.2.mrpack --minecraft 26.2
-> PASS: 24 required server file(s); metadata and hashes are valid
```

Export SHA-256:

```text
4314cf40aa0a545392688a61e4e0f92689b94bc526321db9ab00b5511304cc94  dist/cobbled-horizon-0.1.0+mc26.2.mrpack
```

The exported JEB entry is server-required and pinned to Modrinth version `n1Jc09sK`; the checked-in JEB config is present in overrides, and the staged tree is absent. A runtime smoke test and JEB cold restore have not yet been performed on the designated Minecraft test host; complete both before treating this baseline as production-ready.

## Configuration and export validation changes

Date: 2026-09-11 UTC

The server-properties template now disables secure-profile enforcement for Bedrock chat while retaining online authentication. The backup procedure requires an initial full backup, daily full backups coordinated with host restarts, and full and differential restore drills. JEB's configured intervals remain unchanged.

`make test validate` passed with 14 tests and 51 indexed pack files. Archive regression tests cover missing and changed configs, missing and extra mods, changed pins, invalid client/server flags, duplicate archive paths, and manifest-only validation attempts.

A fresh export passed using packwiz revision `ef87d964f8cbd52b3b13ea42453ef322290e2b9e`, the revision pinned in CI. The local build used a temporary packwiz binary and download cache through the Makefile's `PACKWIZ` override. Refresh left the committed pack and index hashes unchanged.

```text
PASS: 24 required server file(s); pins and configuration overrides match source
```

All 27 configuration overrides matched the source files. Two consecutive local exports produced different archive SHA-256 values while both passed the exact-content validator; packwiz does not normalize all ZIP metadata. Treat the artifact uploaded by a specific CI run as immutable, rather than using a source-committed archive hash as a reproducibility claim.

No host configuration or scheduler was changed. Minecraft was not started. Java and Bedrock chat, backup completion across restarts, and both restore drills remain required on the designated test host.
