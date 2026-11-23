"""Policy/archive regressions, not a Discord login or native Minecraft execution."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from pack_fixtures import ROOT, load_script
import check_pack
import permission_seed
import server_folder
import test_server_folder
import test_validation
import validate_mrpack

journal = load_script("discord_journal")
native = load_script("native_acceptance")
PRIVATE = ("config/mc2discord.toml", "config/mc2discord.toml.bak",
           "config/mc2discord.toml.old", "config/backups/mc2discord.toml",
           "config/.mc2discord.toml", "m2d-linked-players.json", "m2d-hidden-players.json")


class DiscordJournalTests(unittest.TestCase):
    def test_authored_policy_and_exact_server_pin(self):
        config = tomllib.loads((ROOT / journal.TEMPLATE).read_text())
        self.assertEqual(
            ["player_advancement", "player_death", "player_connect", "player_disconnect"],
            config["Channels"]["Channel"][0]["subscriptions"],
        )
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
        changes += tuple((("Channels", "Channel", 0, "subscriptions"),
                          ["player_advancement", "player_death", "player_connect", "player_disconnect", name])
                         for name in ("info", "chat", "discord", "minecraft", "command", "logs",
                                      "account_linking", "*"))
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

    def test_incomplete_activity_subscriptions_are_rejected(self):
        requested = ["player_advancement", "player_death", "player_connect", "player_disconnect"]
        for omitted in requested:
            config = copy.deepcopy(journal.POLICY)
            config["Channels"]["Channel"][0]["subscriptions"] = [
                event for event in requested if event != omitted
            ]
            for normalized in (False, True):
                with self.subTest(omitted=omitted, normalized=normalized):
                    self.assertTrue(journal.policy_errors(config, normalized=normalized))

    def test_normalization_allows_comments_and_disabled_account_omission_not_policy_loss(self):
        config = copy.deepcopy(journal.POLICY)
        # Independent human-requested contract, not a positive derived from POLICY.
        config["Channels"]["Channel"][0]["subscriptions"] = [
            "player_advancement", "player_death", "player_connect", "player_disconnect"
        ]
        config["Channels"]["Channel"][0]["comment"] = "native comment"
        config["lang"] = "en_us"
        del config["Account"]  # Upstream OnlyIf(Features.account_linking).
        self.assertEqual([], journal.policy_errors(config, normalized=True))
        config["Features"]["account_linking"] = True
        self.assertTrue(journal.policy_errors(config, normalized=True))
        config = copy.deepcopy(journal.POLICY)
        config["Commands"]["slash_command"] = 0  # bool/int equality is not enough.
        self.assertTrue(journal.policy_errors(config, normalized=True))

    def test_private_paths_are_rejected_by_mrpack_folder_and_private_zip_even_when_indexed(self):
        mr = test_validation.MrpackTests()
        mr.setUp()
        for relative in PRIVATE:
            with self.subTest(relative=relative):
                fixture = test_server_folder.ServerFolderTests()
                fixture.setUp()
                self.addCleanup(fixture.doCleanups)
                fixture.materialize()
                self.assertFalse(permission_seed.is_pack_override(relative))
                mr.assert_archive_rejected(mr.index, {**mr.overrides, "overrides/" + relative: b"private canary"},
                                           "unexpected archive entry")
                private = fixture.output / relative
                private.parent.mkdir(parents=True, exist_ok=True)
                private.write_bytes(b"private canary")
                self.assertIn("unexpected server entry: " + relative,
                              server_folder.validate_directory(fixture.output, fixture.root))
                archive = fixture.root / "private.zip"
                with self.assertRaisesRegex(ValueError, "unexpected server entry: " + relative):
                    server_folder.server_zip(fixture.output, archive, fixture.root)
                self.assertFalse(archive.exists())
                target = fixture.root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"private canary")
                original = (fixture.root / "index.toml").read_text()
                (fixture.root / "index.toml").write_text(original + f"[[files]]\nfile = {json.dumps(relative)}\n")
                fixture.write_mrpack({**fixture.contents, "overrides/" + relative: b"private canary"})
                destination = fixture.root / "refused"
                with patch.object(server_folder.urllib.request, "urlopen") as download:
                    with self.assertRaisesRegex(ValueError, "unexpected source override: " + relative):
                        server_folder.materialize(fixture.source, destination, fixture.root)
                download.assert_not_called()
                self.assertFalse(destination.exists())
                self.assertIn("unexpected source override: " + relative,
                              server_folder.validate_directory(fixture.output, fixture.root))
                with self.assertRaisesRegex(ValueError, "unexpected source override: " + relative):
                    server_folder.server_zip(fixture.output, archive, fixture.root)
                self.assertFalse(archive.exists())
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
            for drift in (template.replace("slash_command = false", "slash_command = true"),
                          template.replace('"player_disconnect"', '"player_disconnect", "chat"')):
                target.write_text(drift)
                with self.subTest(drift=drift), self.assertRaisesRegex(ValueError, "parser changed"):
                    native.check_discord_dormant(server, output, normalized=True)
            with patch.object(check_pack, "ROOT", server):
                errors = []
                check_pack.validate_no_secrets(errors)
            self.assertIn("runtime state must not exist in the source tree: " + journal.RUNTIME, errors)


if __name__ == "__main__":
    unittest.main()
