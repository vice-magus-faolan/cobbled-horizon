# Staged projects

This directory retains pinned metadata and reviewed configuration for projects that are intentionally excluded from the active baseline.

Packwiz ignores this directory. A normal `packwiz refresh` or export cannot install these files.

Promotion is deliberate:

1. Satisfy the project's activation gate in `../candidates.toml`.
2. Create an update branch.
3. Move the selected `.pw.toml` file into `../mods/`.
4. Move any associated configuration into `../config/`.
5. Move the project record into `../collection.toml`; move its staged dependencies too.
6. Run static validation and all applicable server acceptance tests on the designated Minecraft test host.
7. Review and merge only after the measurements and compatibility evidence justify the added surface.

Current staged set:

- Krypton
- Fast Noise and its ZConfig dependency
- ScalableLux
