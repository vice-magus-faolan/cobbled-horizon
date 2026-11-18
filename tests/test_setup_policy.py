"""Native refresh and Git exclusion of private runtime state, without a seed."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import tempfile
import tomllib
import unittest

from pack_fixtures import ROOT


class RuntimePrivacyTests(unittest.TestCase):
    def test_native_refresh_indexes_pack_config_but_not_runtime_state(self) -> None:
        # Adapted from the 26.3 refresh regression: 26.2 has no authored seed.
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for name in ("pack.toml", ".packwizignore", ".gitignore"):
                shutil.copyfile(ROOT / name, root / name)
            (root / "index.toml").write_text('hash-format = "sha256"\n')
            ordinary = "config/ordinary.json"
            private = (
                "mods/luckperms/luckperms-h2.mv.db", "mods/luckperms/config.yml",
                "mods/luckperms/exports/private.json.gz", "config/luckperms/users.json",
                "config/floodgate/key.pem", "config/Geyser-Fabric/saved-refresh-tokens.json",
            )
            for relative in (ordinary, *private):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"owned fixture canary")
            result = subprocess.run(["packwiz", "refresh", "--build"], cwd=root,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            index = tomllib.loads((root / "index.toml").read_text())
            self.assertEqual({ordinary}, {entry["file"] for entry in index["files"]})
            # Own the fixture metadata; archived unit source need not be a Git checkout.
            result = subprocess.run(["git", "init", "--quiet", str(root)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            result = subprocess.run(["git", "-C", str(root), "check-ignore", "--no-index",
                                     *private[:3]], capture_output=True, text=True, timeout=10)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(set(private[:3]), set(result.stdout.splitlines()))
            result = subprocess.run(["git", "-C", str(root), "check-ignore", "--no-index", ordinary],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertEqual("", result.stdout)


if __name__ == "__main__":
    unittest.main()
