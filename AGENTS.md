# Four Fronts Frenzy

- Target Warcraft III TFT Classic 1.26–1.28: plain JASS, 12 players, no Blz/Dz natives or runtime Lua.
- Use the existing isolated checkout. Do not create Git worktrees unless the user explicitly requests them.
- Build: `python3 tools/build.py`. Generated files are in ignored `build/`.
- Validate: `npm ci --cache /tmp/warcraft-npm-cache` then `npm test`.
- If available, run `pjass common.j Blizzard.j +shadow +checkglobalsinit +checkstringlength +nomodulooperator build/map/war3map.j` using legacy API declarations. Apply strict flags after stock libraries; do not suppress checks on map source. Never report the map as tested in Warcraft based on parser or native-mock checks.
- Never reuse JASS type names as identifiers (the `boolean force` parameter in 0.1.0 passed permissive parsing but failed `+shadow`; the user reported an empty 1.26 lobby). Run the lobby config test as well as binary metadata checks.
- Keep balance constants in `map/balance.json`; edit source JASS in `map/war3map.j` rather than generated JASS.
- Preserve classic binary versions and check object modification IDs and types against Warcraft metadata when adding fields.
- Human and bot purchases must use the same `Buy` function. Do not give bots hidden resources or bypass upgrade caps.
- Hero spell use, pathfinding, loading and multiplayer sync require real in-game validation. Record those separately from automated checks.
