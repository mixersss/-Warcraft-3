-- New regressions use real emitted JASS. Native damage/stuns are checked as object data.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
local function nums()return setmetatable({},{__index=function()return 0 end})end
local function flags()return setmetatable({},{__index=function()return false end})end
local oldRandom=GetRandomInt
local rolls={}
function GetRandomInt(a,b)local n=table.remove(rolls,1)or b;assert(n>=a and n<=b);return n end
function GetRandomReal(a,b)return (a+b)/2 end
-- Exhaust all 100 first-forest rolls. No artificial guaranteed boss drops.
local totals={}
StoryEnemy[0]=CreateUnit(12,raw('re01'),0,0,0);EnemyKind[0]=1;EnemyLootRolled[0]=false
for roll=1,100 do
 StoryLoot[0]=nil;EnemyLootRolled[0]=false;rolls={roll};StoryDrop(0)
 local id=StoryLoot[0]and StoryLoot[0].type or 0;totals[id]=(totals[id]or 0)+1
end
assert(totals[raw('Nlra')]==10 and totals[raw('Nlpi')]==10 and totals[raw('Nlsh')]==7 and totals[raw('Nnot')]==8 and totals[raw('Nlku')]==8 and totals[raw('Nlga')]==2 and totals[raw('Nlne')]==10 and totals[0]==45)
EnemyKind[0]=3;StoryLoot[0]=nil;EnemyLootRolled[0]=false;StoryDrop(0);assert(not StoryLoot[0],'Haku has no invented guaranteed equipment table')
-- Exhaust original Z0X rolls using a genuine tracked death, not a parallel roll helper.
ExamEnemy={};ExamRespawnAt=nums();ExamEnemyCastAt=nums();ExamRespawnType=nums();ExamDropped=flags();ExamEngaged=flags();ExamScroll={};ExamGear={};ExamScrollCount=0;ExamGearCount=0
StoryStage={[0]=7,[1]=0,[2]=0,[3]=0};TimeNow=200000;ExamOpenAt=TimeNow+1200;ExamEndAt=TimeNow+1320;ExamTowerOpen=false;ExamPopulateCursor=85;ExamRepopulateAt=TimeNow+1000
for p=0,2 do Hero[p]=CreateUnit(p,raw('R000')+p,-5000,-5000,0)end
ExamEnemy[0]=CreateUnit(12,raw('re06'),-5000,-5000,0);ExamEnemy[0].hp=0
local sourceCounts={}
for roll=1,100 do
 ExamDropped[0]=false;local oldScroll=ExamScrollCount;local oldGear=ExamGearCount;rolls={roll,1};ExamForestTick()
 local it=nil;if ExamScrollCount>oldScroll then it=ExamScroll[ExamScrollCount-1]elseif ExamGearCount>oldGear then it=ExamGear[ExamGearCount-1]end
 local id=it and it.type or 0;sourceCounts[id]=(sourceCounts[id]or 0)+1
end
assert(sourceCounts[raw('Nlra')]==7 and sourceCounts[raw('Nlpi')]==5 and sourceCounts[raw('Nlsh')]==6 and sourceCounts[raw('Nnot')]==6 and sourceCounts[raw('Nlku')]==7 and sourceCounts[raw('Nlga')]==2 and sourceCounts[raw('Nlne')]==6 and sourceCounts[raw('Eshe')]==2 and sourceCounts[raw('Esea')]==2 and sourceCounts[raw('Nsch')]==2 and sourceCounts[raw('Nsht')]==2 and sourceCounts[raw('Nsta')]==2 and sourceCounts[0]==51)
-- Exact eight-unit source replenishment, repeating every eight seconds below <=25 live ninjas.
ExamEnemy={};ExamRespawnAt=nums();ExamDropped=flags();ExamRepopulateAt=TimeNow
ExamForestTick();for j=0,7 do assert(ExamRespawnAt[j]==TimeNow+1 and ExamRespawnType[j]==raw(j<3 and 're07'or're06'))end
assert(ExamRespawnAt[8]==0 and ExamRepopulateAt==TimeNow+8)
TimeNow=TimeNow+1;ExamForestTick();for j=0,7 do assert(FoundationAlive(ExamEnemy[j])and ExamEnemy[j].x<=-3776 and ExamEnemy[j].y<=-3296)end
-- Either full pool leaves the other functional; combat no longer cancels ramen.
local drinker=CreateUnit(0,raw('R000'),0,0,0);drinker.maxLife=1000;drinker.maxMana=1000;drinker.hp=500;drinker.mana=1000
local ramen={type=raw('Nlra')};function GetManipulatingUnit()return drinker end;function GetManipulatedItem()return ramen end
local create=CreateTrigger;local damageTriggers=0
function CreateTrigger()damageTriggers=damageTriggers+1;return create()end
TimeNow=300000;RamenUse();local active=RamenArt[0];TimeNow=TimeNow+10;RamenTick();assert(drinker.hp==700 and drinker.mana==1000,'Full mana must not block healing')
TimeNow=TimeNow+10;RamenTick();assert(drinker.hp==900 and not RamenUnit[0]and not active.alive)
drinker.hp=1000;drinker.mana=500;RamenUse();TimeNow=TimeNow+20;RamenTick();assert(drinker.hp==1000 and drinker.mana==900,'Full HP must not block mana regeneration')
drinker.hp=500;drinker.mana=500;RamenUse();TimeNow=TimeNow+5;RamenTick();assert(drinker.hp==600 and drinker.mana==600)
local attacker=CreateUnit(12,raw('re06'),100,0,0);UnitDamageTarget(attacker,drinker,90,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS)
TimeNow=TimeNow+5;RamenTick();assert(drinker.hp==610 and drinker.mana==700 and RamenUnit[0]==drinker,'Positive damage must not end ramen')
RamenUse();local first=RamenArt[0];RamenUse();assert(not first.alive and RamenUnit[0]==drinker and not RamenUnit[1],'Refresh instead of stacking regen/effects')
assert(damageTriggers==0,'Ramen must not create damage listeners')
drinker.hp=0;RamenTick();assert(not RamenUnit[0]and not RamenArt[0],'Death releases the effect')
CreateTrigger=create
-- The actual Kaiten and palm-combo paths issue native stun orders to the enemy.
Hero[4]=CreateUnit(4,raw('R004'),0,0,0);HeroRole[4]=4;Hero[4].level=60;Hero[4].hp=10000
local victim=CreateUnit(12,raw('re06'),100,0,0);victim.hp=10000;World={victim};local cursor=StunCursor
RosterRepel(4,1);local micro=StunDummy[cursor];assert(micro and GetUnitAbilityLevel(micro,raw('Rkt3'))==1,'Kaiten must issue the dedicated one-second stun ability')
for _,index in ipairs({22,23})do cursor=StunCursor;RosterApply(4,index,1,victim);assert(StunDummy[cursor]and GetUnitAbilityLevel(StunDummy[cursor],raw('Rstn'))==4,'Palm series must issue its actual native stun, capped at two seconds')end
GetRandomInt=oldRandom
print('PASS: exhaustive 100-roll source tables for both forests; eight-genin replenishment and random placements; ramen with either pool full, uninterrupted combat recovery, refresh and death cleanup (mock natives).')
