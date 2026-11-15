# Owner-only game tools

The owner explicitly requested exactly two newly created one-handed level35 Assassin
Swords1397, fused into Crimson Thunder apparel5002, for the ordinary character **buba**.
They chose the valid full +27 configuration: Rage/type12 rank9, Black Dragon Eye/type13
rank9, Fiery/type1 rank9, with native apparel strengthening15. This personal grant is
an explicit exception to the no-free-items policy for autonomous bots; never give it
to the bot population or modify the character's earned level/profession/stats.

`buba-swords` copies only our explicit GM dofile script. It does not patch NPCs/SDK,
automatically execute grants, edit SQL inventories or grant GM. Owner currently has
no GM; manual guarded SQL scripts temporarily set0->99 and restore99->0 for the one
account found through buba. Preserve the runtime `owner-buba-swords-01.state` ledger;
pending means manual inspection, never automatic deletion/retry. Preserve all existing
items; consume only the two temporary bases created by this invocation.

Recipe audited against owner ItemInfo/forge.lua/variable.lua and public native
CharScript.cpp (MakeItem/FusionItem/GetPlayerByName). Six local Lua-model/copy checks
pass; live owner GameServer API availability and actual grant remain unverified.
Only derived facts and our tools may be published, never account data or raw resources.
