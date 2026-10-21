-- Native permanent barracks choice, including late selection and paid progression.
for race=0,3 do
 reset();Seconds=WARMUP_SECONDS+100;Players[0].gold=100000
 for k=0,3 do UnitAddAbility(Base[0],FourCC('Fbr'..k))end
 SetPlayerTechMaxAllowed(0,FourCC('Rfti'),0)
 assert(not IssueImmediateOrderById(Base[0],FourCC('Rfti')),'Native development locked until branch choice')
 assert(purchase(0,0)and purchase(0,1)and purchase(0,2),'Troop stats available before branch choice')
 ArmyRace[0]=race;SpawnWave(0);assert(#Army[0]==4 and Army[0][1].id==ArmyType[race*5],'Shared footman tier0')
 local gold=Players[0].gold;Dying=Base[0];SpellId=FourCC('Fbr'..race);OnArmyBranchSpell()
 assert(ArmyBranchChosen[0] and ArmyRace[0]==race and Players[0].gold==gold,'Branch card is free and works after preparation')
 for k=0,3 do assert(GetUnitAbilityLevel(Base[0],FourCC('Fbr'..k))==0)end
 assert(not SelectArmyRace(0,(race+1)%4)and ArmyRace[0]==race,'Branch never rerolls')
 for tier=1,4 do
  local before=Players[0].gold;assert(purchase(0,3)and Tier[0]==tier)
  assert(Players[0].gold==before-TierCost[tier],'Only native development charges gold')
  GroupClear(Army[0]);SpawnWave(0);assert(#Army[0]==4 and Army[0][1].id==ArmyType[race*5+tier])
  assert(Attack[0]==1 and Armor[0]==1 and Vitality[0]==1,'Research survives troop replacement')
 end
end
-- The actual computer startup can choose every branch, but starts at tier0.
for race=0,3 do
 reset();Players[0].controller=MAP_CONTROL_COMPUTER;RngQueue={0,race,0};InitSlot(0)
 assert(Bot[0]and ArmyBranchChosen[0]and ArmyRace[0]==race and Tier[0]==0)
 SpawnWave(0);assert(#Army[0]==4 and Army[0][1].id==ArmyType[race*5])
 local selected=ArmyRace[0];Players[0].gold=1000000
 for turn=1,100 do BotBuy(0);FinishResearch(0);assert(ArmyRace[0]==selected)end
 assert(Tier[0]==4 and Attack[0]>0 and Armor[0]>0 and Vitality[0]>0,'Random branch develops with all troop stats')
end
-- Reject wrong caster, bot clicks, invalid rawcodes and inactive/dead bases.
reset();Dying=Hero[0];SpellId=FourCC('Fbr2');OnArmyBranchSpell();assert(not ArmyBranchChosen[0])
Dying=Base[0];SpellId=FourCC('Fbr4');OnArmyBranchSpell();assert(not ArmyBranchChosen[0])
Bot[0]=true;SpellId=FourCC('Fbr2');OnArmyBranchSpell();assert(not ArmyBranchChosen[0]);Bot[0]=false
SlotActive[0]=false;OnArmyBranchSpell();assert(not ArmyBranchChosen[0]);SlotActive[0]=true
Base[0].hp=0;OnArmyBranchSpell();assert(not ArmyBranchChosen[0])
reset();Players[0].controller=MAP_CONTROL_USER;InitSlot(0)
assert(not ArmyBranchChosen[0]and Players[0].techLimits[FourCC('Rfti')]==0,'Actual human startup waits for a card')
print('PASS: late native branch choice, same4-footman opening, all16 paid troop transitions, one gold debit, preserved research; all4 random bot branches reach tier4 without rerolls (mock natives).')
