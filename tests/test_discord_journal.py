"""Policy/archive regressions, not a Discord login or native Minecraft execution."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

import test_server_pack
import test_validation
from test_validation import ROOT, check_pack, load_script, permission_seed, validate_mrpack

journal = load_script("discord_journal")
native = load_script("native_acceptance")
PRIVATE = ("config/mc2discord.toml", "config/mc2discord.toml.bak",
           "config/mc2discord.toml.old", "config/backups/mc2discord.toml",
           "config/.mc2discord.toml", "m2d-linked-players.json", "m2d-hidden-players.json")


class DiscordJournalTests(unittest.TestCase):
    def test_authored_policy_and_exact_server_pin(self):
        config = tomllib.loads((ROOT / journal.TEMPLATE).read_text())
        self.assertEqual([], journal.policy_errors(config))
        pin = tomllib.loads((ROOT / "mods/mc2discord.pw.toml").read_text())
        self.assertEqual("server", pin["side"])
        self.assertIs(True, pin["pin"])
        self.assertEqual({"mod-id": "Cfbcv7uF", "version": "GaUQd96e"}, pin["update"]["modrinth"])
        self.assertEqual("mc2discord-fabric-26.3-4.4.0.jar", pin["filename"])

    def test_unsafe_subscriptions_grants_account_and_privacy_drift_are_rejected(self):
        changes = (
            (("General", "token"), "private canary"),
            (("Channels", "Channel"), []),
            (("Channels", "Channel", 0, "id"), 123),
            (("Channels", "Channel", 0, "mode"), "WEBHOOK"),
            (("Commands", "slash_command"), True),
            (("Commands", "Permission"), []),
            (("Commands", "Permission", 0, "permission_level"), 0),
            (("Commands", "Permission", 0, "commands"), ["stop"]),
            (("Features", "account_linking"), True),
            (("Features", "status_channels"), True),
            (("Account", "allow_private_messages"), True),
            (("Account", "rename_discord_member"), True),
            (("Account", "force_link"), True),
            (("Account", "Policy", 0, "roles_id_to_give"), [123]),
            (("Style", "Presence", "update"), 60),
            (("Misc", "broadcast_commands"), ["tell"]),
            (("Misc", "allowed_mention"), ["USER"]),
            (("Misc", "relay_bot_messages"), True),
        )
        changes += tuple((("Channels", "Channel", 0, "subscriptions"), [name])
                         for name in ("info", "chat", "discord", "minecraft", "command", "logs",
                                      "account_linking", "player_connect", "player_disconnect", "player_death"))
        for path, value in changes:
            config = copy.deepcopy(journal.POLICY)
            target = config
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.subTest(path=path, value=value):
                for normalized in (False, True):
                    errors = journal.policy_errors(config, normalized=normalized)
                    self.assertTrue(errors)
                    self.assertNotIn("private canary", str(errors))
        config = copy.deepcopy(journal.POLICY)
        config["fake_disable_flag"] = True
        self.assertTrue(journal.policy_errors(config))

    def test_normalization_allows_comments_and_disabled_account_omission_not_policy_loss(self):
        config = copy.deepcopy(journal.POLICY)
        config["Channels"]["Channel"][0]["comment"] = "native comment"
        config["lang"] = "en_us"
        del config["Account"]  # Upstream OnlyIf(Features.account_linking).
        self.assertEqual([], journal.policy_errors(config, normalized=True))
        config["Features"]["account_linking"] = True
        self.assertTrue(journal.policy_errors(config, normalized=True))
        config = copy.deepcopy(journal.POLICY)
        config["Commands"]["slash_command"] = 0  # bool/int equality is not enough.
        self.assertTrue(journal.policy_errors(config, normalized=True))

    def test_private_paths_are_rejected_even_when_indexed_into_all_three_contracts(self):
        mr = test_validation.MrpackTests()
        mr.setUp()
        fixture = test_server_pack.ServerPackTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        for relative in PRIVATE:
            with self.subTest(relative=relative):
                self.assertFalse(permission_seed.is_pack_override(relative))
                mr.assert_archive_rejected(mr.index, {**mr.overrides, "overrides/" + relative: b"private canary"},
                                           "unexpected archive entry")
                target = fixture.root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"private canary")
                original = (fixture.root / "index.toml").read_text()
                (fixture.root / "index.toml").write_text(original + f"[[files]]\nfile = {json.dumps(relative)}\n")
                fixture.fixture.files["overrides/" + relative] = b"private canary"
                self.assertIn("unexpected source override: " + relative, fixture.fixture.validate())
                fixture.write_server({**fixture.payload, relative: b"private canary"})
                self.assertIn("unexpected source override: " + relative,
                              test_server_pack.server_pack.validate_archive(fixture.output, fixture.root))
                # A source-index insertion must not turn the mrpack deny into an allow.
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    (root / "pack.toml").write_bytes((ROOT / "pack.toml").read_bytes())
                    (root / "collection.toml").write_text("selected = []\nresolved-dependency = []\n")
                    (root / "index.toml").write_text(f"[[files]]\nfile = {json.dumps(relative)}\n")
                    private = root / relative
                    private.parent.mkdir(parents=True, exist_ok=True)
                    private.write_bytes(b"private canary")
                    errors = []
                    validate_mrpack.validate_contract({**mr.index, "files": []},
                                                     {"overrides/" + relative: b"private canary"}, root, errors)
                    self.assertIn("unexpected source override: " + relative, errors)
                (fixture.root / "index.toml").write_text(original)
                del fixture.fixture.files["overrides/" + relative]
                target.unlink()

    def test_native_guard_rejects_missing_mod_guard_login_and_parser_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            server = Path(directory)
            (server / "config").mkdir()
            target = server / journal.RUNTIME
            template = (ROOT / journal.TEMPLATE).read_text()
            target.write_text(template)
            output = "- mc2discord 4.4.0\n[Mc2Discord]: Invalid Discord bot token\n"
            native.check_discord_dormant(server, output, normalized=True)
            for bad in (output.replace("mc2discord 4.4.0", "othermod"),
                        output.replace("Invalid Discord bot token", "not guarded"),
                        output + "Mc2Discord started as bot"):
                with self.subTest(output=bad), self.assertRaises(ValueError):
                    native.check_discord_dormant(server, bad, normalized=True)
            target.write_text(template.replace("slash_command = false", "slash_command = true"))
            with self.assertRaisesRegex(ValueError, "parser changed"):
                native.check_discord_dormant(server, output, normalized=True)
            with patch.object(check_pack, "ROOT", server):
                errors = []
                check_pack.validate_no_secrets(errors)
            self.assertIn("runtime state must not exist in the source tree: " + journal.RUNTIME, errors)


if __name__ == "__main__":
    unittest.main()
