-- Run the actual synchronized assignment across all 12 occupied computer slots.
for seed=0,3 do
 reset()
 for p=0,11 do
  Players[p].controller=MAP_CONTROL_COMPUTER
  RngQueue={0,seed,HERO_COUNT-1};InitSlot(p)
  assert(ArmyBranchChosen[p]and Bot[p]and Tier[p]==0 and #RngQueue==0)
 end
 local counts={0,0,0,0}
 for team=0,3 do
  local used={}
  for p=team*3,team*3+2 do
   assert(not used[ArmyRace[p]],'No duplicate bot branches within a team')
   used[ArmyRace[p]]=true;counts[ArmyRace[p]+1]=counts[ArmyRace[p]+1]+1
   SpawnWave(p);assert(#Army[p]==6 and Army[p][1].id==ArmyType[ArmyRace[p]*5])
  end
 end
 for _,count in ipairs(counts)do assert(count==3,'All-computer match uses each branch exactly3 times')end
end
-- Human branch choice stays available after randomizing heroes and after warmup.
reset();ArmyRace[0]=2;CommitArmyBranch(1,1);local chosen=ArmyRace[1]
RngQueue={};for p=0,11 do table.insert(RngQueue,HERO_COUNT-1)end
SetAllRandom(0);assert(AllRandomMode and not ArmyBranchChosen[0] and ArmyRace[1]==chosen)
Seconds=WARMUP_SECONDS+2
assert(SelectArmyRace(0,3)and ArmyBranchChosen[0]and ArmyRace[0]==3)
-- Native spells: issued only to appropriate troop, in range, with valid enemies.
reset();local soldier=CreateUnit(0,ArmyType[7],0,0,0);local enemy=CreateUnit(3,ArmyType[0],100,0,0)
AllowedOrders={ensnare=true,devour=true,taunt=true}
UnitAddAbility(soldier,FourCC('Jtne'));assert(ArmyTraitCast(soldier,enemy)and soldier.order[1]=='ensnare'and soldier.order[2]==enemy)
enemy.x=700;assert(not ArmyTraitCast(soldier,enemy));enemy.x=100
UnitRemoveAbility(soldier,FourCC('Jtne'));UnitAddAbility(soldier,FourCC('Jtdv'));assert(ArmyTraitCast(soldier,enemy))
enemy.hero=true;assert(not ArmyTraitCast(soldier,enemy));enemy.hero=false;enemy.structure=true;assert(not ArmyTraitCast(soldier,enemy));enemy.structure=false
UnitRemoveAbility(soldier,FourCC('Jtdv'));UnitAddAbility(soldier,FourCC('Jtta'));assert(ArmyTraitCast(soldier,enemy)and soldier.order[1]=='taunt')
enemy.hp=0;assert(not ArmyTraitCast(soldier,enemy));AllowedOrders=nil
-- Only the requested wave size changes; paid wave ranks and hard cap still work.
reset();WaveRanks[0]=20;SpawnWave(0);assert(#Army[0]==26)
for n=1,5 do SpawnWave(0)end;assert(#Army[0]==85)
print('PASS:12 real bot startup assignments, unique allied branches, global3/3/3/3 spread, random heroes without randomizing armies,6..26 waves/cap85 and native troop cast targeting (mock natives).')

-- Exercise SpawnWave against the actual emitted troop ability lists.
local originalCreate=CreateUnit
local originalImmediate=IssueImmediateOrder
function CreateUnit(p,id,x,y,facing)
 local u=originalCreate(p,id,x,y,facing)
 for _,ability in ipairs(EngineTroopTraits[id]or{})do UnitAddAbility(u,ability)end
 return u
end
function IssueImmediateOrder(u,order)
 if order=='spellstealon'or order=='autodispelon'or order=='webon'then u.autoCast=order;return true end
 return originalImmediate(u,order)
end
for _,test in ipairs({{0,2,'spellstealon'},{3,3,'autodispelon'},{2,2,'webon'}})do
 reset();ArmyRace[0]=test[1];Tier[0]=test[2];SpawnWave(0)
 for _,u in ipairs(Army[0])do assert(u.autoCast==test[3],'New troops enable native autocast at creation')end
end
CreateUnit=originalCreate;IssueImmediateOrder=originalImmediate
print('PASS:actual W3U troop abilities enable native spell-steal/dispel/web autocast on every spawned soldier.')
