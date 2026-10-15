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
- Preserve 200 ranks each for attack/armor/HP, four base upgrades, 16-second waves, hero level 100 and basic/ultimate ability caps 20/7. Keep explicit per-rank ability data and the Tinker engineering variants consistent.
- Keep all 24 roster heroes selectable and available to synchronized bot RNG. Races and hero choice lock after preparation; test menu callbacks and every race/tier combination when changing them.
- Walls use static WPM collision and invulnerable destructables with no extra pathing texture. Preserve exactly one ground gate per team and run the WPM flood-fill check.
- Hero spell use, pathfinding, loading and multiplayer sync require real in-game validation. Record those separately from automated checks.
