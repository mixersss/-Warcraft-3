-- Execute actual new JASS; native invisibility rendering still needs a Warcraft test.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
local savedTarget=GetSpellTargetUnit
function GetSpellTargetUnit()return Target end
TimeNow=1000000;CampaignStage=9;CampaignTransition=false
for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;HeroType[p]=Hero[p].type;VisionUntil[p]=0 end
local sasuke=Hero[1];sasuke.abilities[raw('Rlog')]=1;UnitAddAbility(sasuke,raw('BOwk'))
CommonLogEffect(1);assert(GetUnitAbilityLevel(sasuke,raw('BOwk'))==1,'Do not remove the newly applied native buff on SPELL_EFFECT')
assert(LogReadyAt[1]==TimeNow+22 and LogUntil[1]==TimeNow+3)
TimeNow=1000002.5;CommonLogTick();assert(GetUnitAbilityLevel(sasuke,raw('BOwk'))==1)
sasuke.paused=true;TimeNow=1000003;CommonLogTick();assert(GetUnitAbilityLevel(sasuke,raw('BOwk'))==0 and sasuke.paused,'Expiration must clear a paused arena hero without releasing him')
UnitAddAbility(sasuke,raw('BOwk'));LogUntil[1]=0;CommonLogTick();assert(GetUnitAbilityLevel(sasuke,raw('BOwk'))==0,'An orphan native buff is also removed')
sasuke.hidden=true;CommonLogClear(1);assert(sasuke.hidden and sasuke.paused,'Never cancel intentional story hiding/pausing')
sasuke.hidden=false;sasuke.paused=false;UnitAddAbility(sasuke,raw('BOwk'));CommonLogEffect(1)
Caster=sasuke;Target=nil;Spell=raw('Rs05');sasuke.abilities[Spell]=1;SkillsEffect()
assert(GetUnitAbilityLevel(sasuke,raw('BOwk'))==0 and LogUntil[1]==0 and LogReadyAt[1]==TimeNow+22,'Form changes clean Wind Walk without shortening its cooldown')
UnitAddAbility(sasuke,raw('BOwk'));CommonLogEffect(1);CampaignStage=9;CampaignStand(1)
assert(GetUnitAbilityLevel(sasuke,raw('BOwk'))==0 and sasuke.paused and not sasuke.hidden,'Arena seating clears buff and preserves the visible hero')
-- A second NPC cast overwrites the old shared state during the final hide/sleep.
-- The original target/caster must still be shown, lowered, unpaused and released.
local saved={}
local function mock(name,value)saved[name]=_G[name];_G[name]=value end
mock('ShowUnitHide',function(u)ShowUnit(u,false)end);mock('ShowUnitShow',function(u)ShowUnit(u,true)end)
mock('SetUnitTimeScalePercent',function(u,n)SetUnitTimeScale(u,n/100)end)
mock('SetUnitPositionLoc',function(u,l)SetUnitPosition(u,l.x,l.y)end)
mock('AddSpecialEffectTargetUnitBJ',function(point,u,model)bj_lastCreatedEffect=AddSpecialEffectTarget(model,u,point)end)
mock('AddSpecialEffectLocBJ',function(l,model)bj_lastCreatedEffect=AddSpecialEffect(model,l.x,l.y)end)
mock('GetUnitAbilityLevelSwapped',function(id,u)return GetUnitAbilityLevel(u,id)end)
mock('UnitDamageTargetBJ',function()end);mock('PlaySoundBJ',function()end);mock('TriggerExecute',function()end)
local npc=CreateUnit(12,raw('C015'),100,0,0);npc.abilities[raw('A01T')]=1
local otherCaster=CreateUnit(12,0,200,0,0);local otherTarget=CreateUnit(3,0,300,0,0)
local otherOrigin={x=900,y=900};local otherFlash=AddSpecialEffect('test',0,0);local overwritten=false
Caster=npc;Target=sasuke;sasuke.paused=false
mock('TriggerSleepAction',function(seconds)
 if npc.hidden and sasuke.hidden then
  OrigNPC_UN=otherCaster;OrigNPC_WN=otherTarget;OrigNPC_VB=otherOrigin;OrigNPC_ZN=otherFlash;overwritten=true
 end
end)
OrigNPC_K3X()
assert(overwritten and not sasuke.hidden and not npc.hidden,'Show the original pair even after globals are overwritten')
assert(not sasuke.paused and not npc.paused and sasuke.flyHeight==0 and npc.flyHeight==0,'Restore original control and height')
assert(sasuke.pathing and npc.pathing and otherFlash.alive and not otherOrigin.removed,'Do not clean the other cast resources')
DestroyEffect(otherFlash)
for name,value in pairs(saved)do _G[name]=value end
GetSpellTargetUnit=savedTarget
-- Automatic defense distribution respects controllers/roles/empty slots and rounds to whole bots.
for p=0,11 do HeroRole[p]=p;Controllers[p]='computer';CampaignPermanentDead[p]=false end
CampaignAssignDefense();local top,left=0,0
for p=0,8 do if CampaignDefenseLane[p]==5 then top=top+1 else left=left+1 end end
assert(top==3 and left==6)
Controllers[0]='human';CampaignAssignDefense();top=0;left=0
for p=1,8 do if CampaignDefenseLane[p]==5 then top=top+1 else left=left+1 end end
assert(top==2 and left==6,'Eight bots round to 2 upper and 6 left; human control remains free')
local upper,leftDef=1,3
local north=CreateUnit(12,0,CampaignRouteX[5],CampaignRouteY[5],0)
local west=CreateUnit(12,0,CampaignRouteX[3],CampaignRouteY[3],0)
for _,p in ipairs({upper,leftDef})do Hero[p].x=6096;Hero[p].y=-8528 end
assert(CampaignDefenseAllows(upper,north) and not CampaignDefenseAllows(leftDef,north))
assert(CampaignDefenseAllows(leftDef,west) and not CampaignDefenseAllows(upper,west),'Left group must not all chase the same northern wave')
north.x=Hero[leftDef].x+100;north.y=Hero[leftDef].y;assert(CampaignDefenseAllows(leftDef,north),'Keep immediate self-defense')
north.x=CampaignTX[12];north.y=CampaignTY[12];assert(CampaignDefenseAllows(leftDef,north) and CampaignDefenseAllows(upper,north),'A breached Hokage remains an emergency')
Hero[2]=nil;CampaignAssignDefense();assert(CampaignDefenseLane[2]==3,'Empty slots cannot consume the upper quota')
print('PASS: Alpha23 native Wind Walk lifetime/22s cooldown, fresh buff preservation, paused arena expiry/orphan recovery, morph/seating cleanup and intentional story hiding; actual NPC sleep/global overwrite visibility/control cleanup; 30/70 defender allocation, human/empty-slot handling, lane targeting and emergencies (mock natives).')
