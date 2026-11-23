"""Authored dormant Mc2Discord policy, also checked after native TOML normalization."""

from __future__ import annotations

TEMPLATE = "config/mc2discord.example.toml"
RUNTIME = "config/mc2discord.toml"
# Exact SerdeKey names from upstream c4b1698. No real identities or grants.
POLICY = {
    "General": {"token": ""},
    "Channels": {"Channel": [{"id": 0, "subscriptions": ["player_advancement", "player_death",
                                                     "player_connect", "player_disconnect"],
                              "mode": "PLAIN_TEXT", "silent": True}]},
    "Commands": {"slash_command": False,
                 "Permission": [{"id": 0, "permission_level": -1, "commands": []}]},
    "Features": {"status_channels": False, "account_linking": False},
    "Account": {"guild_id": 0, "allow_private_messages": False,
                "rename_discord_member": False, "force_link": False,
                "Policy": [{"required_roles_id": [], "roles_id_to_give": []}]},
    "Style": {"Presence": {"message": "", "update": 0}},
    "Misc": {"relay_bot_messages": False, "allowed_mention": [],
             "broadcast_commands": [], "verbose_other_mods_messages": False},
}


def contains_policy(actual: object, expected: object) -> bool:
    """Native serialization adds defaults/comments; retain every policy leaf/list."""
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and contains_policy(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            contains_policy(item, value) for item, value in zip(actual, expected)
        )
    return type(actual) is type(expected) and actual == expected


def policy_errors(config: dict, *, normalized: bool = False) -> list[str]:
    """Never echo configuration values: accidental credentials stay private."""
    expected = POLICY
    if normalized:
        # Config4J OnlyIf may omit Account while linking is disabled. Its public
        # and DM handlers both return at the account_linking gate in that case.
        expected = {key: value for key, value in POLICY.items()
                    if key != "Account" or key in config}
        valid = contains_policy(config, expected)
    else:
        # Reject unknown fields too: misspelled keys and hidden credentials must
        # not turn a published template into an apparently safe activation file.
        valid = config == expected and contains_policy(config, expected)
    return [] if valid else ["Mc2Discord must retain the credential-free one-way activity policy"]
