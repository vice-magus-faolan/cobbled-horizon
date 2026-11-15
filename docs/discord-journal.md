# Cooperative activity journal (private activation required)

Mc2Discord 4.4.0 is pinned for server-side Fabric 26.3. It is dormant without a
bot token. The pack ships **only** `config/mc2discord.example.toml`, never the
mutable `config/mc2discord.toml`. An ordinary unconfigured server is intended to
remain usable; an `Invalid Discord bot token` integration error is expected.
The exact pinned JAR must pass both boots in the hosted `native-acceptance` job
before PR acceptance. Source/config checks alone are not that runtime result.

## What the reviewed policy permits

Only announced player advancements go from Minecraft to the selected Discord
text channel (`subscriptions = ["player_advancement"]`). There are no rankings,
chat relays, private-message relays, console/log feeds or automated build detection.
Join, leave, death, startup and shutdown posts are off. Do not add `info`: it
subscribes to several of those event types. Do not empty the channel list:
upstream replaces an empty list with broad `info`, `chat` and `command` defaults.

The complete template disables slash commands, status channels, account linking,
private account messages, nickname changes, role grants, presence updates,
mentions and player-command broadcasts. It supplies an explicit permission rule
with level `-1` and no commands; ID `0` means everyone in this rule, **not** an
administrator. No channel subscribes to `command`, `chat`, `discord`, `minecraft`,
`logs` or `account_linking`. These controls deny inbound game actions even for
the Discord guild owner. The mod still receives gateway events; this is not a
network-level write-only client or a claim that Discord sends it no messages.

## Separately approved private setup

1. Obtain approval for bot provisioning, Discord/channel permissions, credentials,
   server configuration/restart and a live event test. None is performed by this
   pack PR. Agree with players on advancement/name disclosure and channel access.
2. Use a **dedicated** bot application. Grant only View Channel and Send Messages
   in one ordinary text channel; deny access elsewhere. `PLAIN_TEXT` needs no
   Administrator, Manage Webhooks, Manage Roles, Manage Nicknames, Manage Channels
   or Minecraft OP. Do not change the template to WEBHOOK or grant those rights
   to resolve an error. Do not grant remote console/whitelist authority.
3. Upstream requests all gateway intents except presences, including privileged
   Server Members and Message Content, even for this policy. It caches guild
   member/channel information and attempts to clear its own guild application
   commands even with slash commands off. These upstream limitations are why the
   app must be dedicated and access tightly scoped. If those reads/intents are
   unacceptable, **leave the bridge dormant**; do not silently broaden consent.
4. With the server stopped, retain any existing private configuration in a
   private rollback backup outside the checkout/export tree. Create or replace
   `config/mc2discord.toml` from the **complete reviewed example**, not from the
   broad upstream-generated defaults. Restrict file access to the server owner.
   Keep all case-sensitive table/field names intact. In a private editor only,
   replace the single `Channels.Channel.id = 0` value with the approved channel
   ID and set `General.token` last. Leave permission/account IDs at zero and all
   other controls unchanged. Never paste tokens, real IDs or private files into
   chat, Git, PRs, archives, logs or support bundles.
5. Restart only under that separate approval. Verify one announced advancement
   arrives as a bot text message. Contrast ordinary Minecraft chat, `/tell`,
   player commands, joins/deaths, Discord chat, `!stop`, slash commands and a DM
   containing `!code`: none may relay, execute game actions or link accounts.
   Confirm no roles, nicknames, whitelist or OP change. Check normal server use
   and a second restart. Record the actual result privately; a mocked event or
   credential-free boot is not a successful Discord-delivery test.

For a later deliberate event-policy change, obtain approval and review both the
subscription and privacy implications; joins/deaths remain off in this baseline.
To pause under an approved configuration change, empty the private token and
restart; retain the complete safe policy. Overlay updates ship only the example,
so they cannot replace a private token file. Git/packwiz exclude Mc2Discord-named
config copies/backups and `m2d-*` identity stores; all three archive validators
also reject them if accidentally indexed. Keep private backups outside the source
and export roots regardless of ignore rules. Rotate an exposed token promptly
through a separately authorized recovery action.

A voluntary `#builds`/screenshot channel and an approved Squaremap link can help
people catch up; these are suggestions for human posts, not created channels,
automated construction milestones or a new map endpoint. Squaremap player-tracker
visibility remains a separate existing disclosure policy.

## Evidence boundary

Configuration names and handler gates were inspected in upstream source snapshot
[`c4b169807bcf407fddf3dfeb4b43a8908b37977d`](https://github.com/DenisD3D/Mc2Discord/tree/c4b169807bcf407fddf3dfeb4b43a8908b37977d).
The pinned Modrinth artifact `Cfbcv7uF` / `GaUQd96e` has verified SHA-512 and
Fabric metadata, but no embedded source-commit stamp; that snapshot is not a
proven source-to-binary correspondence. The established hosted archive and native
jobs must validate the actual pinned payload and its normalized no-token policy.
Private activation, permissions and real event delivery remain separate gates.
