# Verification record

## Initial 26.2 baseline

Date: 2026-09-10 UTC

The final checked-in configuration was exported with packwiz, materialized with `mrpack-install v0.16.10`, and run using Temurin Java `25.0.4.1`.

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

This verifies loader/mod resolution and lifecycle startup. It does not replace the Java/Bedrock gameplay, structure-generation, permissions, squaremap networking, or backup restore tests in `acceptance-tests.md`.
