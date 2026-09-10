# Verification record

## Initial 26.2 baseline

Date: 2026-09-10 UTC

The final checked-in configuration was exported with packwiz, materialized with `mrpack-install v0.16.10`, and run using Temurin Java `25.0.4.1`.

Observed server result:

```text
Registered 199 custom block overrides.
Registered 7 custom blocks.
Started Geyser on UDP port 19132
Done (5.346s)! Run /geyser help for help!
```

The server then accepted `stop`, shut down Geyser and squaremap's Undertow web server, saved the Overworld, Nether, and End, and exited with status 0.

This verifies loader/mod resolution and lifecycle startup. It does not replace the Java/Bedrock gameplay, structure-generation, permissions, squaremap networking, or backup restore tests in `acceptance-tests.md`.
