# Four Fronts Frenzy

- Target Warcraft III TFT Classic 1.26–1.28: plain JASS, 12 players, no Blz/Dz natives or runtime Lua.
- Use the existing isolated checkout. Do not create Git worktrees unless the user explicitly requests them.
- Build: `python3 tools/build.py`. Generated files are in ignored `build/`.
- Validate: `npm ci --cache /tmp/warcraft-npm-cache` then `npm test`.
- If available, run `pjass common.j Blizzard.j +shadow +checkglobalsinit +checkstringlength +nomodulooperator build/map/war3map.j` using legacy API declarations. Apply strict flags after stock libraries; do not suppress checks on map source. Never report the map as tested in Warcraft based on parser or native-mock checks.
- Never reuse JASS type names as identifiers (the `boolean force` parameter in 0.1.0 passed permissive parsing but failed `+shadow`; the user reported an empty 1.26 lobby). Run the lobby config test as well as binary metadata checks.
- Keep balance constants in `map/balance.json`; edit source JASS in `map/war3map.j` rather than generated JASS.
- Preserve classic binary versions and check object modification IDs and types against Warcraft metadata when adding fields.
- Army upgrades use the native research queue for humans and bots. `Buy` issues a research order for bots/chat; command-card clicks use the same W3Q prices and finish event. Never deduct research gold again in `OnResearch`; never give bots free resources or instant research.
- Preserve 200 ranks each for attack/armor/HP, four base upgrades, 16-second waves, hero level 500 and basic/ultimate ability caps 300/50. Award one extra skill point per gained level through the shared, idempotent hero-level handler. Keep explicit per-rank ability data and the Tinker engineering variants consistent.
- Keep all 24 roster heroes selectable and available to synchronized bot RNG. Races and hero choice lock after preparation; test menu callbacks and every race/tier combination when changing them.
- Walls use static WPM collision and invulnerable destructables with no extra pathing texture. Preserve exactly one ground gate per team and run the WPM flood-fill check.
- Hero spell use, pathfinding, loading and multiplayer sync require real in-game validation. Record those separately from automated checks.

- Waves contain one troop type per race/tier. Summon stats live in per-rank custom unit objects, not generic buffs based on the highest unrelated hero skill. Preserve rank 10/20/... summon count milestones.
- Research effects are cumulative base + increment * (rank - 1): ratx +3 damage, rarm armor, rhpo +10% troop HP, rhpx +3000 barracks HP. Never swap percent and flat HP effects or zero the incremental effect.
- Keep the 900-unit walled approach to each fortress; run tunnel side-wall and flood-fill tests. MPQ zlib compression must retain Classic format and independently round-trip every file.

- The user reported an SFile.cpp:898 out-of-memory crash when opening 0.4.0 in Classic 1.26. Never emit compressed SINGLE_UNIT MPQ files. Use standard 4096-byte sectors with offset tables and zlib masks; verify all sectors and every archived file independently. A successful modern MPQ parse does not prove Classic loading.

- Gates flare from half-width 560 to 920 over 900 units. Preserve wide cross-section, shop access and single-entry WPM tests.
- Sanctuary regeneration is 0.15% HP / 0.1% mana per second inside radius 2200, only for the circle owner team, living non-buildings. Do not reintroduce the old fast personal fountain.
- Each fortress has three shops. Equipment definitions and effects are in map/equipment.json and tools/equipment.py. Bots reserve real income, travel to shops, select their buyer, buy through native neutral orders and sell old tiers through UnitDropItemTarget. Never grant free items or gold or destroy unrelated inventory. Preserve six slots and native stock/prices.
