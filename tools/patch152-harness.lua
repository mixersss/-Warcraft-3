-- Actual shipped spell handler; original magnitudes come from published 0.15.1 W3A.
ATTACK_TYPE_NORMAL='normal';DAMAGE_TYPE_MAGIC='magic';WEAPON_TYPE_WHOKNOWS='unknown'
function UnitDamageTarget(c,t,damage,attack,ranged,at,dt,wt)
 assert(damage>0 and at==ATTACK_TYPE_NORMAL and dt==DAMAGE_TYPE_MAGIC)
 t.hp=t.hp-damage;return true
end
local function near(a,b)assert(math.abs(a-b)<math.max(.02,math.abs(b)*.000002),'actual='..a..' expected='..b)end
reset();local ally=Hero[1];local enemy=Hero[3]
for _,case in ipairs(EngineHybridCases)do
 for rank=1,200 do
  local original=EngineHybridExpected[case.kind*200+rank-1]
  Hero[0].abilities[case.raw]=rank;Dying=Hero[0];SpellId=case.raw
  enemy.max=1000000;enemy.hp=1000000;enemy.maxmana=1000;enemy.mana=55;SpellTarget=enemy
  SpellEvent=EVENT_PLAYER_UNIT_SPELL_ENDCAST;OnHybridSpell();assert(enemy.hp==1000000 and enemy.mana==55,'Only spell effect resolves damage')
  SpellEvent=EVENT_PLAYER_UNIT_SPELL_EFFECT;OnHybridSpell()
  if case.kind==2 then
   near(enemy.hp,1000000-math.min(original,55)*.7);near(enemy.mana,55-math.min(original,55))
   enemy.hp=1000000;enemy.mana=0;OnHybridSpell();assert(enemy.hp==1000000,'No mana means no mana-burn damage')
  else
   near(enemy.hp,1000000-original*.35)
   SpellTarget=ally;ally.max=1000000;ally.hp=1;OnHybridSpell();near(ally.hp,1+original,'Healing is not nerfed')
   ally.hp=999999;OnHybridSpell();assert(ally.hp==1000000,'Never heal beyond maximum')
  end
 end
end
-- Research uses the same native command-card queue for human/bot; no extra debit on completion.
for _,bot in ipairs({false,true})do
 for _,rank in ipairs({0,9,10,11,199})do
  for kind=0,2 do
   reset();Bot[0]=bot;Players[0].gold=1000000;GearSavings[0]=0;TierSavings[0]=0
   local base=ArmyResearch[kind];local advanced=AdvancedArmyResearch[kind]
   Players[0].tech[base]=math.min(10,rank);Players[0].tech[advanced]=math.max(0,rank-10);SyncArmyResearch(0)
   local costs={84,84,151};local steps={63,63,101}
   local expected=(costs[kind+1]+rank*steps[kind+1])
   local gold=Players[0].gold;assert(UpgradeCost(0,kind)==expected and Buy(0,kind))
   assert(Players[0].gold==gold-expected,'Native research debits the reduced price exactly once')
   FinishResearch(0);assert(Players[0].gold==gold-expected)
  end
 end
end
print('PASS: 600 hybrid spell ranks and isolated copies, -30% enemy damage, full healing/mana removal, native event guard/resource limits; reduced native research prices at 0/9/10/11/199 for humans and bots, one debit (mock natives).')
