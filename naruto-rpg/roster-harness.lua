function SetUnitPathing(u,flag)u.pathing=flag end
function SetUnitFacing(u,a)u.facing=a end
function Atan2(y,x)return math.atan(y,x)end
function SetUnitX(u,x)u.x=x end
function SetUnitY(u,y)u.y=y end
bj_RADTODEG=180/math.pi
-- Run the generated initializer in twelve independent callbacks, as the engine does.
function raw(s)local n=0;for i=1,#s do n=n*256+string.byte(s,i)end;return n end
function SetUnitAnimationByIndex(u,n)assert(n>=0);u.animationIndex=n end
CreatedTimers=0
function CreateTimer()CreatedTimers=CreatedTimers+1;return {}end
function CreateGroup()return {}end
function CreateTrigger()return {}end
function TriggerRegisterPlayerUnitEvent(t,p,event,filter)end
function TriggerAddAction(t,callback)end
function TimerStart(t,delay,repeating,callback)t.callback=callback;t.delay=delay;t.repeating=repeating end
function PauseTimer(t)t.paused=true end
function DestroyTimer(t)t.destroyed=true end
PlayableSkill=setmetatable({},{__index=function()return 0 end})
SkillDataReady=false;SkillDataCursor=0
SkillsInit()
local loader=SkillDataClock
assert(loader.delay==.05 and loader.repeating and not SkillDataReady)
loader.callback();assert(PlayableSkill[0]~=0 and PlayableSkill[59]==0 and not SkillDataReady)
for i=2,12 do loader.callback()end
assert(SkillDataReady and loader.destroyed and SkillDataClock==nil and PlayableSkill[59]~=0)
AudioClock=CreateTimer()
local baselineTimers=CreatedTimers
TimeNow=200
Hero={};Companion={};World={};Hits={};Orders={};Effects=0;Destroyed=0
for p=0,11 do
 Hero[p]=make(p,0,0);Hero[p].abilities={};Hero[p].level=10;Hero[p].points=10;HeroType[p]=0;HeroTemplate[p]=p;HeroRole[p]=p
 SkillsLearnBot(p)
 for j=p*5,p*5+4 do
  if SkillRanks[j]>0 then assert((GetUnitAbilityLevel(Hero[p],PlayableSkill[j])>=1)==(SkillRequired[j]<=10),'Each slot must respect its source unlock level')end
 end
 Hero[p].level=60;Hero[p].points=60
 SkillsLearnBot(p)
 for j=p*5,p*5+4 do if SkillRanks[j]>0 then assert(GetUnitAbilityLevel(Hero[p],PlayableSkill[j])==math.min(SkillRanks[j],1+math.floor((60-SkillRequired[j])/SkillSkip[j])),'Bot did not learn the source-eligible ranks')end end
end
Dummy[0]=make(12,100,0);Dummy[1]=make(12,100,0);Dummy[2]=make(12,100,0);Dummy[3]=make(12,100,0)
function resetHits()Hits={}end
local seen={}
function technique(p,index,rank,target)
 seen[RosterMechanic[index]]=true
 cast(p,PlayableSkill[index],rank,target)
end
-- Healing accepts friends/self, clamps at maximum and rejects enemies.
local enemy=make(12,100,0);enemy.mana=500
Hero[0].hp=7000
technique(2,12,3,Hero[0]);assert(Hero[0].hp==7620)
Hero[2].hp=9900;technique(2,12,1,Hero[2]);assert(Hero[2].hp==10000)
enemy.hp=5000;technique(2,12,3,enemy);assert(enemy.hp==5000)
-- Hinata now uses the original area chakra-drain helpers, not a single HP hit.
World={enemy,Hero[7]};AimX=100;AimY=0;resetHits()
technique(8,42,2,enemy);assert(#Hits==0 and #Source40Helpers[8]==2)
for _,u in ipairs(Source40Helpers[8])do assert(u.type==raw('r40d')and u.expire==TimeNow+4)end
Source40Clear(8)
-- Unchanged poison hit still exercises the legacy single-target family.
World={enemy};technique(10,51,1,enemy);assert(#Hits==1);resetHits()
-- Four/eight/six sub-combos have exact totals and stop on lost targets.
enemy.hp=10000;enemy.mana=500;resetHits()
technique(4,22,1,enemy);for i=1,4 do SkillsTick()end
assert(#Hits==4 and enemy.hp==9740 and enemy.mana==420 and not ComboTarget[4])
technique(4,23,2,enemy);for i=1,8 do SkillsTick()end
assert(#Hits==12 and ComboLeft[4]==0 and not ComboTarget[4])
technique(8,44,1,enemy);for i=1,6 do SkillsTick()end
assert(#Hits==18 and not ComboTarget[8])
technique(4,22,1,enemy);enemy.immune=true;SkillsTick();assert(#Hits==18 and not ComboTarget[4]);enemy.immune=false
--3.5 Lee has cast-local agility buffs, covered in source35-harness.
technique(4,20,2,nil);assert(GetUnitAbilityLevel(Hero[4],raw('Rbyg'))==2)
Hero[4].hp=0;RosterTick();assert(GetUnitAbilityLevel(Hero[4],raw('Rbyg'))==0);Hero[4].hp=10000
-- Fixed areas pulse eight times; allies/immune/structures outside valid targets survive.
TimeNow=220;AimX=200;AimY=0;enemy.hp=10000;enemy.x=200
local ally=make(1,200,0);local immune=make(12,200,0);immune.immune=true
local building=make(12,200,0);building.structure=true
World={enemy,Hero[5],immune,building};resetHits()
technique(5,28,1,nil)
Hero[5].x=1200
for i=1,8 do TimeNow=220+i*.5;RosterTick()end
assert(#Hits==0 and enemy.hp==10000 and immune.hp==10000 and building.hp==10000 and ZoneUntil[5]==0 and not ZoneArt[5],'Native rockets own their damage; the JASS layer must not add duplicate phantom pulses')
-- Following area moves with the caster; the fixed one above did not.
Hero[4].x=0;enemy.x=0;World={enemy};TimeNow=230;resetHits()
technique(4,21,1,nil);Hero[4].x=1000;TimeNow=230.5;RosterTick();assert(#Hits==1 and ZoneX[4]==1000)
Hero[4].hp=0;RosterTick();assert(ZoneUntil[4]==0 and not ZoneArt[4]);Hero[4].hp=10000;Hero[4].x=0
-- Directional hits must exclude behind, too far, off-axis, allies and immunity.
TimeNow=240;AimX=900;AimY=0
local ahead=make(12,500,0);local behind=make(12,-20,0);local far=make(12,930,0);local edge=make(12,500,200)
local friend=make(3,500,0);World={ahead,behind,far,edge,friend};resetHits()
technique(4,24,1,nil);assert(#Hits==1 and Hits[1].target==ahead and Hits[1].damage==550)
-- Real summoned types/ranks, one of each kind, safe replacement and timed-life cleanup.
TimeNow=250;Hero[10].x=0
technique(10,50,2,nil);local first=Companion[30];assert(first.type==raw('rc02') and first.expire==nil)
technique(10,50,3,nil);assert(first.removed and Companion[30].type==raw('rc03'))
technique(10,52,2,nil);technique(10,53,1,nil)
Source40Adopt(10,CreateUnit(10,raw('rs01'),100,0,0))
assert(Companion[31].type==raw('rk02') and Companion[32].type==raw('rs01'))
World={enemy};enemy.x=100;enemy.hp=10000;resetHits();technique(10,54,1,nil);assert(#Hits==0 and #Source40Helpers[10]==18 and enemy.hp==10000,'Native bombs fly and detonate, no instant duplicate area hit')
local old=Companion[31];old.hp=0;RosterTick();assert(old.removed and Companion[31]==nil)
RosterReset(10);assert(not Companion[30] and not Companion[32])
World={enemy};resetHits();technique(10,54,1,nil);assert(#Hits==0 and #Source40Helpers[10]==0,'No imaginary bombs without actual puppets')
-- Shizune only heals living allied heroes within 600, not enemies or far allies.
Hero[2].x=0;Hero[0].x=0;Hero[0].hp=5000;Hero[1].x=1500;Hero[1].hp=5000;Hero[3].x=0;Hero[3].hp=5000
TimeNow=260;RosterNextSecond[2]=0;technique(2,14,1,nil);RosterTick()
assert(Hero[0].hp==5035 and Hero[1].hp==5000 and Hero[3].hp==5000)
-- A ground blast has the same friend/immune filter and creates no ally stun.
TimeNow=270;Hero[2].x=0;AimX=100;AimY=0;enemy.x=100;World={enemy,Hero[0],immune};resetHits()
technique(2,11,2,nil);assert(#Hits==1 and Hits[1].damage==220)
-- Every active skill has an AI order; every passive is deliberately skipped.
local issued=0
for p=0,11 do
 Hero[p].hp=10000;Hero[p].x=0;Hero[p].y=0;Hero[p].mana=1000;Hero[p].type=0;ComboLeft[p]=0
 for slot=0,4 do
  local index=p*5+slot
  if RosterMechanic[index]==7 then Companion[p*3+RosterPetSlot[index]]=nil end
  if SkillRanks[index]>0 and not SkillPassive[index] then
   TimeNow=300+p*10+slot;BotNextCast[p]=0
   for s=0,4 do BotReadyAt[p*5+s]=999999 end
   BotReadyAt[index]=0
   if index==6 then SharinganUntil[p]=0 end
   if SkillHeal[index] then Hero[0].hp=1000;Hero[0].x=0;Hero[0].y=0 end
   if index==54 then Companion[30]=make(10,0,0)end
   local before=#Orders
   assert(SkillsBot(p),'AI refused active ability '..index)
   assert(#Orders==before+1 and Orders[#Orders].order==SkillOrder[index] and SkillOrder[index]~='')
   if SkillHeal[index] then assert(Orders[#Orders].target==Hero[0]);Hero[0].hp=10000 end
   issued=issued+1
  end
 end
end
assert(issued==54,'Both reincarnations are replaced by active source3.5 skills')
-- Healing skips healthy friends, reserves mana, then selects an injured ally.
TimeNow=500;BotNextCast[2]=0;for s=0,4 do BotReadyAt[10+s]=999999 end;BotReadyAt[12]=0
Hero[0].hp=10000;Hero[1].hp=10000;Hero[2].hp=10000
assert(not SkillsBot(2))
Hero[1].x=0;Hero[1].hp=5000;assert(SkillsBot(2) and Orders[#Orders].target==Hero[1])
TimeNow=510;Hero[2].mana=0;assert(not SkillsBot(2));Hero[2].mana=1000
-- Every current roster entry can be selected without losing carried items or XP.
Controllers[7]='human';Hero[7].xp=1900;Hero[7].items={[0]={name='kept'}}
for role=0,11 do
 RosterHeroType[role]=raw('R'..string.format('%03X',role))
 SkillsChoose(7,role)
 assert(HeroRole[7]==role and HeroTemplate[7]==role and HeroType[7]==RosterHeroType[role])
 assert(Hero[7].xp==1900 and Hero[7].items[0].name=='kept' and GetHeroLevel(Hero[7])==20)
end
-- Training enemies are replaced only after five seconds, with the same team positions.
PLAYER_NEUTRAL_AGGRESSIVE=12
TimeNow=600;local oldDummy=Dummy[0];oldDummy.hp=0
FoundationRefreshTargets();assert(Dummy[0]==oldDummy and DummyRespawnAt[0]==605)
TimeNow=604.5;FoundationRefreshTargets();assert(Dummy[0]==oldDummy)
TimeNow=605;FoundationRefreshTargets();assert(Dummy[0]~=oldDummy and oldDummy.removed and Dummy[0].x==-3400 and Dummy[0].y==-3400)
-- Timers are reused; buffs, zones, summons, combo references and dummy ring are bounded.
for p=0,11 do RosterReset(p)end
TimeNow=1000;SkillsTick()
assert(CreatedTimers==baselineTimers,'No per-cast timer allocation is allowed')
assert(Effects==Destroyed,'A temporary visual was retained')
technique(9,47,1,nil);assert(ZoneUntil[9]>TimeNow,'The fixed area mechanic remains exercised independently of native Soshoryu');RosterReset(9)
for n=1,9 do assert(seen[n],'Missing mechanic test '..n)end
