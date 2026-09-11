# Acceptance tests

Run these against a disposable world before production and again after every mod or loader update.

All Minecraft server startup, world-generation, and gameplay tests must run on the designated, adequately resourced Minecraft test host. A control/orchestration machine may perform static validation and export only.

## Automated gates

```bash
make test
make validate
make export
python3 scripts/validate_mrpack.py dist/cobbled-horizon-0.1.0+mc26.2.mrpack --minecraft 26.2
```

## Server lifecycle

- [ ] Clean server reaches `Done` with no missing dependency or wrong-version error.
- [ ] A second boot succeeds using the generated world and configs.
- [ ] `stop` exits cleanly and saves all dimensions.
- [ ] No private key, refresh token, player database, world, or log enters Git.

## Clients and cross-play

- [ ] Unmodded Java 26.2 client joins successfully.
- [ ] Bedrock client joins through the assigned Geyser UDP port.
- [ ] Floodgate player reconnects with the same identity and inventory.
- [ ] Java and Bedrock chat, inventory, doors, boats, and combat behave acceptably.

## Quality of life

- [ ] Default players cannot create global waystones.
- [ ] Local waystones work for Java and Bedrock players.
- [ ] Cross-dimensional waystone behavior is recorded honestly; version 1.3.2 has no verified disable switch.
- [ ] Java and Bedrock players can see, open, and completely recover a grave.
- [ ] Grave XP recovery and real-time expiry match policy.
- [ ] Creepers damage entities without breaking blocks; unrelated mob behavior remains normal.

## World generation

Use disposable seeds and `/locate structure` where available.

- [ ] Inspect several Towns and Towers structures.
- [ ] Inspect several Explorify structures, including campsite-like structures.
- [ ] Inspect Hopo mineshafts at different depths.
- [ ] Locate and enter a DnT Lite stronghold; verify portal and loot progression.
- [ ] Inspect several Moog floating structures and confirm rarity feels intentional.
- [ ] If ScalableLux is promoted, generate chunks under load and inspect lighting and relighting behavior.

Do not run final Chunky pre-generation until this section passes and the seed is accepted.

## Operations

- [ ] spark profile captures idle and active baselines.
- [ ] squaremap renders only the Overworld and uses the assigned HTTP endpoint.
- [ ] LuckPerms contains only the intended default/admin model.
- [ ] A backup is restored into a separate test instance successfully.
