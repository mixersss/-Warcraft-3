# Independent Canvas fighting game

This folder is separate from all Warcraft maps and the browser RTS. Preserve those projects.
- 16 roster profiles with4 moves each in src/roster.js; BASICS defines16 ordinary attack profiles.
- Combat simulation in combat.js: no DOM. Keep costs, finite stun/lifetimes, genuine projectile travel, best-of-three and symmetric rules.
- Art in art.js is procedural Canvas2D; do not claim imported Warcraft models, exact source animation or professional sprite assets.
- Run node shinobi-fighter/test/combat.test.js after mechanics changes. Browser smoke uses system Chromium/Playwright, requires process permission in the environment; never disable managed browser file policies.
- Rebuild python3 shinobi-fighter/build.py after source changes. It embeds all13 existing user MP3s in a standalone HTML andZIP.
- Pages hosts RTS atroot and this game at/fighter/. Do not replace the root strategy. Do not announce a live public URL without verifying deployment.
