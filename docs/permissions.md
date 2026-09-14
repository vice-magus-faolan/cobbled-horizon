# Permission bootstrap

Use the DatHost console after the first successful production boot. Replace placeholders literally; do not commit player UUIDs unless there is a clear reason.

These commands define a deployment procedure, not source-enforced security. Before applying them, inspect the current operator list, `ops.json`, LuckPerms groups, user memberships, and effective permissions. Remove stale authority deliberately; creating the intended groups does not revoke permissions inherited from old groups or direct user grants. Group-creation commands may report that a group already exists on repeat runs, after which the remaining parent, membership, and permission assignments should converge on the documented state.

## Roles

Only the owner is a Minecraft operator. The `helper` group inherits ordinary-player access and receives individual permission nodes only when a real support task requires them. It is not an operator-equivalent role.

```text
lp creategroup owner
lp group owner parent add default
lp user <OWNER_JAVA_USERNAME> parent set owner
op <OWNER_JAVA_USERNAME>

lp creategroup helper
lp group helper parent add default
lp user <HELPER_USERNAME> parent set helper
deop <HELPER_USERNAME>
```

Do not put ordinary administrators or helpers in `ops.json`. Operator status grants broad vanilla authority and mod commands such as Chunky world generation, configuration reloads, and JEB backup restoration. Use the DatHost console as the break-glass path if the owner account is unavailable.

## Waystone policy

The checked-in configuration charges two XP levels, applies a 30-second PvP/PvE combat lock, and limits each player to ten player-owned waystones. Server-owned waystones do not count against that per-player limit.

Players may create waystones, but only the owner may make them global or server-owned. A server-owned waystone is visible to everyone and cannot be broken by ordinary players.

```text
lp group default permission set sswaystones.create.place true
lp group default permission set sswaystones.create.global false
lp group default permission set sswaystones.create.team false
lp group default permission set sswaystones.create.server false
lp group default permission set sswaystones.command false
lp group default permission set sswaystones.manager false
lp group default permission set sswaystones.manager.bypass_limit false
lp group default permission set sswaystones.showall false

lp group owner permission set sswaystones.create.global true
lp group owner permission set sswaystones.create.server true
lp group owner permission set sswaystones.command true
lp group owner permission set sswaystones.manager true
lp group owner permission set sswaystones.manager.bypass_limit true
lp group owner permission set sswaystones.showall true
```

A newly placed player waystone is not globally listed. It is not strictly private, however: another player who physically finds and interacts with it discovers it and can then teleport to it. Server-Side Waystones 1.3.2 has no owner-only access flag.

The mod also has no true cross-dimension disable switch. The checked-in configuration uses the maximum signed integer XP cost to make cross-dimension travel infeasible for survival players. Creative players pay no XP and can still bypass this policy, so creative mode remains owner-only.

## Helper permissions

The baseline deliberately grants no additional helper permissions. Add narrowly scoped nodes only when a specific support duty exists, and record the reason here. Never grant `*`, `minecraft.*`, `luckperms.*`, `chunky.*`, `spark.*`, or destructive backup/restore authority for convenience.

JEB's checked-in `commandPermissionLevel` is `4`; use the owner account or DatHost console for backup and restore commands.

## Verification

```text
op list
lp listgroups
lp group default permission check sswaystones.create.place
lp group default permission check sswaystones.create.global
lp group default permission check sswaystones.create.team
lp group default permission check sswaystones.command
lp group owner permission check sswaystones.create.server
lp group owner permission check sswaystones.command
lp user <OWNER_JAVA_USERNAME> info
lp user <HELPER_USERNAME> info
lp user <ORDINARY_JAVA_USERNAME> info
lp user <FLOODGATE_USERNAME> info
```

Read `ops.json` on the deployed host and confirm it contains only the owner. Inspect each test account for unexpected direct grants or inherited groups, then test with an ordinary Java player, a helper, the owner, and an ordinary Floodgate player. Confirm that only the owner can create server/global waystones, use `/sswaystones`, enter creative mode, run Chunky operations, or invoke JEB. Floodgate identities may differ from Java usernames; prefer UUID-backed assignments after the player has joined.
