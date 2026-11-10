# Independent browser RTS

This folder is an independent game, not a Warcraft map. Keep Warcraft compatibility rules scoped to the existing map projects. Do not edit their sources or release binaries when working here.

- Plain ES modules and Canvas 2D, no mandatory CDN/runtime dependencies.
- Simulation belongs in src/engine.js, presentation in render.js and browser interaction in game.js.
- Keep the bot on the same paid finite worker economy as the player. No hidden AI income.
- Run node --test shinobi-strategy/test/engine.test.js after simulation changes.
- Build with python3 shinobi-strategy/build.py to regenerate the offline HTML; it embeds all 13 music tracks.
- Browser smoke uses system Chromium through Playwright and may need approved process permissions; do not disable managed browser file policies. The test fulfills source files without a listening server and tests the bundled HTML with all HTTP blocked.
- Never call the public Pages address live without verifying deployment. Keep prototype limitations in README accurate.
