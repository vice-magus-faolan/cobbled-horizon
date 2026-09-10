# Permission bootstrap

Use the DatHost console after the first successful production boot. Replace placeholders literally; do not commit player UUIDs unless there is a clear reason.

## Minimal groups

```text
lp creategroup admin
lp group admin parent add default
lp user <JAVA_USERNAME> parent set admin
op <JAVA_USERNAME>
```

Minecraft operator status remains the administrative boundary for vanilla commands. The LuckPerms `admin` group provides a simple place for explicit mod permissions without granting an opaque wildcard.

## Waystone policy

Server-Side Waystones permits global waystone creation by default. Deny it explicitly:

```text
lp group default permission set sswaystones.create.global false
lp group admin permission set sswaystones.create.global false
```

Ordinary player-created waystones remain allowed. Server-owned waystone management remains operator-controlled by the mod's defaults.

## Verification

```text
lp group default permission check sswaystones.create.global
lp group admin permission check sswaystones.create.global
lp user <JAVA_USERNAME> info
```

Test permissions with both a Java player and a Floodgate player. Floodgate identities may differ from Java usernames; prefer UUID-backed assignments after the player has joined.

Do not grant `*` to the admin group merely for convenience. Add explicit permission nodes when a real administrative need appears.
