"""Public offline delta CLI regressions using owned local Git repositories."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/branch_delta.py"


def mod(identity: str, version: str = "Version1", hash_digit: str = "a", name: str = "Same display") -> str:
    return (
        f'name = "{name}"\nfilename = "unchanged.jar"\nside = "server"\npin = true\n'
        f'[download]\nurl = "https://example.invalid/{identity}.jar"\nhash-format = "sha512"\nhash = "{hash_digit * 128}"\n'
        f'[update.modrinth]\nmod-id = "{identity}"\nversion = "{version}"\n'
    )


class BranchDeltaTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="branch-delta-")
        self.addCleanup(temporary.cleanup)
        self.repo = pathlib.Path(temporary.name)
        self.git("init", "--quiet", "--initial-branch=fixture")
        (self.repo / "mods").mkdir()
        self.write_target("26.2")
        self.write_collection(["Alpha001", "Bravo002", "Gone0004"], ["Same0003"], target="26.2")
        for identity in ("Alpha001", "Bravo002", "Same0003", "Gone0004"):
            (self.repo / "mods" / f"{identity}.pw.toml").write_text(mod(identity))
        self.before = self.commit()
        self.write_target("26.3")
        self.write_collection(["Alpha001", "Bravo002", "Fresh005"], ["Same0003"])
        (self.repo / "mods/Gone0004.pw.toml").unlink()
        (self.repo / "mods/Alpha001.pw.toml").rename(self.repo / "mods/renamed.pw.toml")
        (self.repo / "mods/renamed.pw.toml").write_text(mod("Alpha001", name="New display"))
        (self.repo / "mods/Bravo002.pw.toml").write_text(mod("Bravo002", version="Version2"))
        (self.repo / "mods/Same0003.pw.toml").write_text(mod("Same0003", hash_digit="b"))
        (self.repo / "mods/Fresh005.pw.toml").write_text(mod("Fresh005"))
        # Deliberately invalid out-of-scope content must not enter the active comparison.
        (self.repo / "staged/mods").mkdir(parents=True)
        (self.repo / "staged/mods/bad.pw.toml").write_text("not valid TOML")
        (self.repo / "candidates.toml").write_text("not valid TOML")
        self.after = self.commit()

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", *args],
            check=True, capture_output=True, text=True,
        )
        return result.stdout.strip()

    def commit(self) -> str:
        self.git("add", "--all")
        self.git("commit", "--quiet", "--no-gpg-sign", "-m", "fixture")
        return self.git("rev-parse", "HEAD")

    def write_target(self, target: str) -> None:
        (self.repo / "pack.toml").write_text(
            f'version = "{target}.0.1.0"\n[versions]\nminecraft = "{target}"\nfabric = "0.20.1"\n'
        )

    def write_collection(self, selected: list[str], resolved: list[str], target: str = "26.3") -> None:
        text = f'schema = 1\nminecraft = "{target}"\nloader = "fabric"\n'
        for section, identities in (("selected", selected), ("resolved-dependency", resolved)):
            for identity in identities:
                text += f'[[{section}]]\nproject-id = "{identity}"\n'
        (self.repo / "collection.toml").write_text(text)

    def invoke(self, before: str, after: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repository", str(self.repo), before, after],
            capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def files(self) -> dict[str, bytes]:
        return {path.relative_to(self.repo).as_posix(): path.read_bytes() for path in self.repo.rglob("*") if path.is_file()}

    def test_complete_identity_groups_exact_pins_and_determinism_without_writes(self) -> None:
        # Dirty/untracked working-tree content is deliberately different from the frozen inputs.
        (self.repo / "mods/renamed.pw.toml").write_text("uncommitted invalid TOML")
        (self.repo / "untracked.txt").write_text("preserve me")
        files, refs = self.files(), self.git("show-ref")
        result = self.invoke(self.before, "HEAD")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual({"REMOVED": 1, "ADDED": 1, "UPDATED": 2, "UNCHANGED": 1}, data["counts"])
        expected = {"REMOVED": ["Gone0004"], "ADDED": ["Fresh005"], "UPDATED": ["Bravo002", "Same0003"], "UNCHANGED": ["Alpha001"]}
        for group, identities in expected.items():
            entries = data["groups"][group]
            self.assertEqual(identities, [entry["project_id"] for entry in entries])
            self.assertEqual(len(entries), data["counts"][group])
        self.assertEqual(self.before, data["before"]["commit"])
        self.assertEqual(self.after, data["after"]["commit"])
        self.assertEqual("26.2", data["before"]["minecraft"])
        self.assertEqual("26.3", data["after"]["minecraft"])
        self.assertEqual("0.20.1", data["after"]["fabric"])
        renamed = data["groups"]["UNCHANGED"][0]
        self.assertNotEqual(renamed["before"]["metadata"], renamed["after"]["metadata"])
        self.assertNotEqual(renamed["before"]["name"], renamed["after"]["name"])
        self.assertEqual(renamed["before"]["pin"], renamed["after"]["pin"])
        for entry in data["groups"]["UPDATED"]:
            self.assertEqual(entry["before"]["pin"]["filename"], entry["after"]["pin"]["filename"])
        self.assertEqual(result.stdout, self.invoke(self.before, self.after).stdout)
        self.assertEqual(refs, self.git("show-ref"))
        self.assertEqual(files, self.files())

    def assert_rejected(self, before: str, after: str) -> None:
        files, refs = self.files(), self.git("show-ref")
        result = self.invoke(before, after)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("error:", result.stderr)
        self.assertEqual(refs, self.git("show-ref"))
        self.assertEqual(files, self.files())

    def test_invalid_and_option_like_refs_are_rejected_without_output_or_writes(self) -> None:
        for ref in ("does-not-exist", "--all", "-n", "HEAD:pack.toml"):
            with self.subTest(ref=ref):
                self.assert_rejected(self.before, ref)
        self.assert_rejected("missing-before", self.after)

    def test_malformed_missing_and_duplicate_pin_identities_are_rejected(self) -> None:
        path = self.repo / "mods/Bravo002.pw.toml"
        for text in ("not TOML", mod("bad"), mod("Alpha001"), mod("Bravo002").replace('mod-id = "Bravo002"\n', ""), mod("Bravo002", version="bad")):
            with self.subTest(text=text):
                path.write_text(text)
                self.assert_rejected(self.before, self.commit())

    def test_missing_extra_and_duplicate_collection_members_are_rejected(self) -> None:
        for selected in (["Alpha001", "Fresh005"], ["Alpha001", "Bravo002", "Fresh005", "Absent06"], ["Alpha001", "Bravo002", "Fresh005", "Alpha001"]):
            with self.subTest(selected=selected):
                self.write_collection(selected, ["Same0003"])
                self.assert_rejected(self.before, self.commit())

    def test_malformed_pack_and_collection_targets_are_rejected(self) -> None:
        for path, text in (("pack.toml", 'version = "26.3.0.1.0"\n[versions]\nminecraft = "26.x"\nfabric = "0.20.1"\n'), ("collection.toml", 'schema = 1\nminecraft = "26.2"\nloader = "fabric"\n')):
            with self.subTest(path=path):
                self.write_target("26.3")
                (self.repo / path).write_text(text)
                self.assert_rejected(self.before, self.commit())


if __name__ == "__main__":
    unittest.main()
