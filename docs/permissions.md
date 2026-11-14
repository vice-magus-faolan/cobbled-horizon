# Permission bootstrap

Use the selected host's authenticated server console after the first successful, separately approved boot, before admitting ordinary players. Rehearse this procedure on the disposable acceptance instance first; console/panel and file access are [deployment prerequisites](deployment.md#preflight). All paths below are relative to the server root. Replace account placeholders only on the deployed host; never commit identities, memberships or OP entries.

## One-time group import

`config/cobbled-horizon/luckperms-groups.json` is the readable, authored group-only policy, not a captured native export. `make refresh` derives the import-ready `luckperms-groups.json.gz` beside it; `make validate` checks that decompression reproduces the canonical bytes. Both encodings are indexed and included in all three release formats. Neither contains users, UUIDs, memberships, export metadata, credentials or a database. Nothing applies the policy at startup.

1. Inspect the host's operator-management list and `ops.json`, then `lp listgroups`, the three target groups' existing nodes/parents and all relevant users' memberships, direct grants and effective permissions. Stop and reconcile conflicting authority deliberately; importing a baseline does not revoke stale OP, direct grants or inherited/custom permissions.
2. Run `lp export first-server-before` from the authenticated console, wait for completion and retain that private native backup off-host together with a consistent host/storage backup. It includes identities and must never enter the pack or Git. Keep the current storage backend; importing is not a backend migration.
3. Using the host's file manager/SFTP, **copy** the supplied `config/cobbled-horizon/luckperms-groups.json.gz` to `mods/luckperms/luckperms-groups.json.gz`. This is the pinned Fabric LuckPerms 5.5.85 data folder, not `config/luckperms/` or a nested `exports/` folder. No OS shell, gzip utility or online upload is required. Leave the canonical pack files in place and never overwrite `mods/luckperms/` wholesale.
4. From the authenticated console run exactly:

   ```text
   lp import luckperms-groups.json.gz
   ```

   Wait for native import completion and inspect the readbacks below before assigning accounts. Do **not** add `--replace` or `--upload`.
5. Record that this one-time bootstrap was applied, its pack version and verification results. Repeat only as a deliberate reconciliation, never on every restart. Retain the private pre-import backup for rollback.

The default native import merges nodes into the named groups. It preserves unrelated groups/users and does not assign any account or OP; it is not a transaction or universal reset of existing authority. Matching existing nodes can change, while unrelated/contextual nodes and existing parents/direct user grants can survive and affect effective permissions. Repeating this same seed does not intentionally duplicate its nodes, but it also does not remove custom grants added since the first import. Review conflicts on a disposable copy first and verify actual effective results; do not promise harmless convergence on an arbitrary existing server. If interrupted or rejected, keep players out, inspect state and restore/reconcile from the private backup through a separately approved recovery action rather than blindly rerunning with replacement.

## Roles and account assignment

The seed gives `owner` and `helper` inheritance from `default`. Only the owner is a Minecraft operator; helper has **no additional permission nodes**. Membership and OP changes below are separate, deployment-specific owner decisions, not part of importing the pack:

```text
lp user <OWNER_JAVA_USERNAME> parent add owner
op <OWNER_JAVA_USERNAME>
lp user <HELPER_USERNAME> parent add helper
deop <HELPER_USERNAME>
```

Inspect existing memberships before these additions: they preserve other parents, including potentially stale authority. Revoke unwanted parents/direct grants deliberately instead of replacing every user's group list. Do not make helpers operators for convenience. Operator status grants broad vanilla and mod authority, including Chunky generation and JEB restoration. Restrict console access and retain it as the break-glass route if the owner account is unavailable. Floodgate identities may differ from Java usernames; prefer UUID-backed assignments after the player has joined, recording them only in private host state.

## Waystone policy

The canonical seed allows ordinary personal waystone placement and explicitly denies global/team/server creation, administration, manager/bypass and show-all controls for `default`. `owner` overrides the global/server and administrative denies, but not the team deny. Helper inherits the ordinary baseline. Add a narrow helper node only when a real support duty exists; never grant `*`, `minecraft.*`, `luckperms.*`, `chunky.*`, `spark.*` or destructive backup/restore authority.

The checked-in mod configuration charges two XP levels, applies a 30-second PvP/PvE combat lock and limits each player to ten player-owned waystones. Server-owned waystones do not count against that limit. A newly placed player waystone is not globally listed, but a player who finds and interacts with it discovers it; Server-Side Waystones 1.3.2 has no owner-only access flag. Only the owner may make global/server-owned waystones; ordinary players cannot break server-owned ones.

There is no true cross-dimension disable switch: the maximum signed-integer XP cost is infeasible for survival players, but creative players bypass it. Creative mode remains owner-only. JEB's `commandPermissionLevel` remains `4`; use the owner or authenticated console for backup/restore, not helpers.

## Verification

Use the host's operator-management list or read `ops.json` and confirm only the intended owner is present. `op list` is not a read-only listing command and must not be used. From the authenticated console:

```text
lp listgroups
lp group default permission info
lp group owner permission info
lp group helper permission info
lp group owner parent info
lp group helper parent info
lp group default permission check sswaystones.create.place
lp group default permission check sswaystones.create.global
lp group default permission check sswaystones.create.team
lp group owner permission check sswaystones.create.server
lp group helper permission check sswaystones.command
lp user <OWNER_JAVA_USERNAME> info
lp user <HELPER_USERNAME> info
lp user <ORDINARY_JAVA_USERNAME> info
lp user <FLOODGATE_USERNAME> info
lp user <HELPER_USERNAME> permission check sswaystones.command
lp user <ORDINARY_JAVA_USERNAME> permission check sswaystones.create.server
```

Inspect each account's direct grants, inherited groups and effective permissions in its actual contexts. Test an ordinary Java player, helper, owner and ordinary Floodgate player: only the owner can create server/global waystones, use `/sswaystones`, enter creative mode, run Chunky or invoke JEB. A successful import or a group-node listing alone does not prove these runtime boundaries. Complete the [operations acceptance matrix](acceptance-tests.md#operations) before deployment.
