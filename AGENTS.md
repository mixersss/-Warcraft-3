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
- Preserve 200 ranks each for attack/armor/HP, four base upgrades, 12-second waves, hero level 500 and basic/ultimate ability caps 300/50. Award one extra skill point per gained level through the shared, idempotent hero-level handler. Keep explicit per-rank ability data and the Tinker engineering variants consistent.
- Keep all 28 roster heroes (24 stock plus four custom) selectable and available to synchronized bot RNG. Races and hero choice lock after preparation; test menu callbacks and every race/tier combination when changing them.
- Walls use static WPM collision and invulnerable destructables with no extra pathing texture. Preserve exactly one ground gate per team and run the WPM flood-fill check.
- Hero spell use, pathfinding, loading and multiplayer sync require real in-game validation. Record those separately from automated checks.

- Waves contain one troop type per race/tier. Summon stats live in per-rank custom unit objects, not generic buffs based on the highest unrelated hero skill. Preserve rank 10/20/... summon count milestones.
- Research effects are cumulative base + increment * (rank - 1): ratx +6 damage, rarm +2 armor through unit udup=2, rhpo +20% troop HP, rhpx +15000 barracks HP. Never swap percent and flat HP effects or zero the incremental effect.
- Keep the 1600-unit walled approach to each fortress; run tunnel side-wall and flood-fill tests. MPQ zlib compression must retain Classic format and independently round-trip every file.

- The user reported an SFile.cpp:898 out-of-memory crash when opening 0.4.0 in Classic 1.26. Never emit compressed SINGLE_UNIT MPQ files. Use standard 4096-byte sectors with offset tables and zlib masks; verify all sectors and every archived file independently. A successful modern MPQ parse does not prove Classic loading.

- Gates flare from half-width 560 to 1200 over 1600 units. Preserve wide cross-section, shop access and single-entry WPM tests.
- Sanctuary regeneration is 0.15% HP / 0.1% mana per second inside radius 2200, only for the circle owner team, living non-buildings. Do not reintroduce the old fast personal fountain.
- Each fortress has five shops. Equipment definitions and effects are in map/equipment.json and tools/equipment.py. Bots reserve real income, travel to shops, select their buyer, buy through native neutral orders and sell old tiers through UnitDropItemTarget. Never grant free items or gold or destroy unrelated inventory. Preserve six slots and native stock/prices.

- Combat structures have 30000 base HP and +15000 per tier; towers have 6000 HP. The central neutral fountain uses two native Classic regeneration auras: FfHP/ACnr and FfMP/ANre. Each restores 1.5% of max pool per second, radius 1000, heroes of every team, with no organic or alliance restriction. Do not reintroduce the removed trigger regeneration or double healing.
- Floating gold uses the actual OnDeath reward; create synchronized texttags and change only visibility with GetLocalPlayer. Never award a second bounty or show allied kills.
- Black Arrow targets include all enemy/neutral ground and air troop categories, including undead mechanical troops; do not reintroduce organic-only filtering. Preserve native skeleton data and test gameplay limits separately.

- Each barracks has an additional vulnerable, non-regenerating 60000 HP bastion (700 base damage, 24 armor, 1000 range, 0.75-second attacks). Preserve existing guard towers and test bastion footprint clearance. Bastions never respawn.
- Experience multiplier is 0.50: keep native creep factors, native hero grants/formula and supplemental OnDeath XP consistent. Waves are every 12 seconds.
- Every roster hero has six unique gear_families chosen for its gear_role. Do not add redundant critical strike to native crit heroes, lifesteal masks to Dreadlord or orb-arrow users, or force the same primary-stat loadout on every hero. Verify real purchases/upgrades for all 28 profiles.

- Open/closed/unoccupied slots must remain empty: only PLAYER_SLOT_STATE_PLAYING gets a base, hero, both towers and waves. Explicit computer slots run scripted AI; a departing human still transfers to AI. Test InitSlot with mixed slot states and non-red first human. All Random must skip inactive/Lost slots; mark wholly empty teams out before combat.
- Hero selection uses a temporary owned native training building: eight portrait cards/page plus four Channel controls, removed at combat start. The first occupied human chooses Normal or All Random in the first 15 seconds; All Random locks manual race/hero changes. Keep the text fallback. Custom heroes use isolated copies of stock spells with distinct learn/cast button positions. Import seeds using skill_sources for custom heroes.
- Bastions sit behind bases, initially paused. Enemy damage to the base or bastion wakes defense for six seconds. Extend the window without reissuing attack orders on every damage event; this prevents repeated hits from resetting attacks. Towers stay vulnerable and never regenerate/respawn.
- Bots check native research every second and do not reissue orders while busy. Develop a base tier after at least tier+1 ranks in each troop parameter. Gear savings accrue at roughly one third of real income; while the next item is unfunded, reserve at most a quarter of current gold for it; protect its full cost once funded. Keep native item purchases and real research prices.

- Computer heroes are assigned randomly by EnsureBotHero on the first game tick, independently of gallery input. Retry only missing/removed hero objects, never reroll dead heroes; preserve their revival identity. Native gallery callbacks reject computers.
