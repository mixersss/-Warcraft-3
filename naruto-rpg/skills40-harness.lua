-- Execute actual source replacements; native numerical effects are independently audited in W3A.
for p=0,11 do RosterReset(p)end
TimeNow=10000000;CampaignStage=12;CampaignTransition=false;CampaignFinished=false;World={}
local inside,terrain,cliff=TreeJumpInside,IsTerrainPathable,GetTerrainCliffLevel
function TreeJumpInside()return true end
function IsTerrainPathable()return false end
function GetTerrainCliffLevel()return 0 end
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;HeroType[p]=Hero[p].type;Controllers[p]='computer'
 Hero[p].hp=10000;Hero[p].maxLife=10000;Hero[p].mana=10000;Hero[p].maxMana=10000;Hero[p].level=60;Hero[p].points=0
end
local enemy=CreateUnit(12,111,100,0,0);enemy.hp=10000;enemy.mana=500
local ally=Hero[3];World={enemy,ally};AimX=100;AimY=0;Controllers[5]='human'
local timerCount=CreatedTimers
cast(5,PlayableSkill[29],1,nil);local start=TimeNow
assert(Source40BallCaster[5]==Hero[5] and not Source40Ball[5] and VisualChannelUntil[5]==start+8.25,'Real spell event starts full native Channel')
TimeNow=start+.74;Source40Cursor=5;Source40PlayerTick();assert(not Source40Ball[5])
TimeNow=start+.76;Source40PlayerTick();local ball=Source40Ball[5]
assert(ball and ball.owner==5 and ball.type==raw('r40s')and Source40BallUntil[5]==TimeNow+7.5 and ball.flyHeight==200,'Owned selectable source ball after charge')
local hp,allyHP=enemy.hp,ally.hp;Source40BallPulse(5)
assert(enemy.hp==hp-24 and ally.hp==allyHP,'Source radius pulse24, no allied damage')
local getTrigger,getTarget,getX,getY=GetTriggerUnit,GetOrderTargetUnit,GetOrderPointX,GetOrderPointY
function GetTriggerUnit()return ball end
function GetOrderTargetUnit()return nil end
function GetOrderPointX()return ball.x end
function GetOrderPointY()return ball.y+1000 end
Source40Order();assert(Source40BallSteered[5]and math.abs(Source40BallAngle[5]-math.pi/2)<.001,'Actual order callback steers the ball')
GetTriggerUnit,GetOrderTargetUnit,GetOrderPointX,GetOrderPointY=getTrigger,getTarget,getX,getY
ball.x=100;ball.y=0;enemy.x=100;enemy.y=0;hp=enemy.hp;Source40BallPulse(5);assert(enemy.hp==hp-21,'Steered source damage21')
-- Concurrent copies are isolated, and normal spell-end cancels only its caster's ball.
HeroRole[4]=5;cast(4,PlayableSkill[29],1,nil);TimeNow=TimeNow+.76;Source40Cursor=4;Source40PlayerTick();local otherBall=Source40Ball[4]
Caster=Hero[5];Spell=PlayableSkill[29];SkillsEndcast()
assert(not Source40Ball[5]and ball.removed and Source40Ball[4]==otherBall and not otherBall.removed,'No global ball or cross-caster cleanup')
assert(Hero[5].timeScale==1 and not Hero[5].paused and not Hero[5].hidden,'No stuck/hidden caster on endcast')
Source40Clear(4);HeroRole[4]=4
Controllers[5]='computer';cast(5,PlayableSkill[29],1,nil);TimeNow=TimeNow+.76;Source40Cursor=5;Source40PlayerTick();ball=Source40Ball[5]
enemy.x=ball.x;enemy.y=ball.y+500;World={enemy};Source40BallPulse(5)
assert(Source40BallSteered[5]and Source40BallAngle[5]>1.,'Computer actively steers toward a visible enemy')
TimeNow=Source40BallUntil[5]+.01;Source40PlayerTick();assert(ball.removed and not Source40BallCaster[5])
-- Source point smoke: no old personal buff, delayed rank-specific native stomp.
AimX=300;AimY=400;cast(7,PlayableSkill[36],4,nil)
assert(RosterBuffUntil[7]==0 and Source40SmokeRank[7]==4)
TimeNow=Source40SmokeAt[7]+.01;Source40Cursor=7;Source40PlayerTick()
local smoke=Source40Helpers[7][1];assert(smoke.type==raw('r40c')and smoke.x==300 and smoke.y==400 and smoke.last.o=='stomp'and GetUnitAbilityLevel(smoke,raw('R40c'))==4)
Source40Clear(7);assert(smoke.removed)
-- Native morph + hidden attribute ability: exact duration, no stacking or persistence after death.
for rank=1,3 do
 cast(7,PlayableSkill[37],rank,nil);local due=Source40AgiUntil[7]
 assert(due-TimeNow==(rank==1 and 25 or 50)and GetUnitAbilityLevel(Hero[7],raw('R40a'))==rank)
 TimeNow=due+.01;Source40Cursor=7;Source40PlayerTick();assert(GetUnitAbilityLevel(Hero[7],raw('R40a'))==0 and not Source40AgiCaster[7])
end
cast(7,PlayableSkill[37],3,nil);Hero[7].dead=true;Source40PlayerTick();assert(GetUnitAbilityLevel(Hero[7],raw('R40a'))==0);Hero[7].dead=false
-- Hinata: rank helpers per eligible enemy, no synthetic HP hit, real channel orders.
enemy.x=100;enemy.y=0;enemy.mana=500;enemy.hp=10000
local second=CreateUnit(12,112,200,0,0);second.mana=500;second.hp=10000
local dry=CreateUnit(12,113,110,0,0);dry.mana=0
local far=CreateUnit(12,114,900,0,0);far.mana=500
ally.x=100;ally.y=0;World={enemy,second,dry,far,ally};AimX=100;AimY=0;Hits={}
cast(8,PlayableSkill[42],2,nil);assert(#Source40Helpers[8]==4 and #Hits==0,'Two real drain casters per eligible enemy; no previous single-target damage')
for _,u in ipairs(Source40Helpers[8])do assert(u.last.o=='drain'and(u.last.target==enemy or u.last.target==second)and u.expire==TimeNow+4)end
local firstHelper=Source40Helpers[8][1];TimeNow=TimeNow+4.2;Source40Cursor=8;Source40PlayerTick();assert(#Source40Helpers[8]==0 and firstHelper.removed,'Helpers cannot leave corpses or references')
-- Native inferno summon event adopts its real unit, retaining other permanent puppets.
local old=CreateUnit(10,raw('rs01'),0,0,0);Companion[32]=old
Companion[30]=CreateUnit(10,raw('rc03'),0,0,0);Companion[31]=CreateUnit(10,raw('rk03'),0,0,0)
local karasu,kuroari=Companion[30],Companion[31]
local getSummoner,getSummoned=GetSummoningUnit,GetSummonedUnit
local sansho=CreateUnit(10,raw('rs03'),200,0,0)
function GetSummoningUnit()return Hero[10]end
function GetSummonedUnit()return sansho end
SkillsSummoned();assert(Companion[32]==sansho and old.removed and not sansho.expire and Companion[30]==karasu and Companion[31]==kuroari,'Native source summon is the tracked permanent companion')
GetSummoningUnit,GetSummonedUnit=getSummoner,getSummoned
-- Exactly six native bombs from each actual puppet, no instantaneous scripted damage.
World={enemy};Hits={};cast(10,PlayableSkill[54],1,nil)
assert(#Source40Helpers[10]==18 and #Hits==0)
for _,u in ipairs(Source40Helpers[10])do assert(u.type==raw('r40b')and u.owner==10 and u.last.o=='move'and u.expire==TimeNow+5)end
TimeNow=TimeNow+.2;Source40Cursor=10;Source40PlayerTick();assert(Source40Helpers[10][1].flyHeight>0)
local bombs={};for _,u in ipairs(Source40Helpers[10])do bombs[#bombs+1]=u end
Source40Clear(10);for _,u in ipairs(bombs)do assert(u.removed)end
for k=0,2 do Companion[30+k]=nil end
cast(10,PlayableSkill[54],1,nil);assert(#Source40Helpers[10]==0 and not Source40HasPuppet(10),'No fallback bombs or imaginary puppets')
-- Temari: native main shockwave, then two original native wind casters after half a second.
AimX=500;AimY=0;Hits={};cast(11,PlayableSkill[59],1,nil);assert(#Hits==0 and Source40WindAt[11]==TimeNow+.5,'No duplicate adapted line damage')
TimeNow=TimeNow+.51;Source40Cursor=11;Source40PlayerTick();assert(#Source40Helpers[11]==2)
for _,u in ipairs(Source40Helpers[11])do assert(u.type==raw('r40w')and u.last.o=='stampede')end
Source40Clear(11);assert(#Source40Helpers[11]==0 and not Source40WindCaster[11])
-- Sharingan uses source agility and exact three reachable durations; morph/death do not stack it.
for rank=1,3 do
 cast(1,PlayableSkill[6],rank,nil);assert(SharinganUntil[1]-TimeNow==6.5+2*rank and GetUnitAbilityLevel(Hero[1],raw('Rsag'))==rank)
 assert(GetUnitAbilityLevel(Hero[1],raw('Rsev'))==0 and GetUnitAbilityLevel(Hero[1],raw('Rscr'))==0)
 Hero[1].type=raw('Rsfm');TimeNow=SharinganUntil[1]+.01;SkillsTick();assert(GetUnitAbilityLevel(Hero[1],raw('Rsag'))==0 and not SharinganArt[1]);Hero[1].type=HeroType[1]
end
cast(1,PlayableSkill[6],3,nil);Hero[1].dead=true;SkillsTick();assert(SharinganUntil[1]==0 and GetUnitAbilityLevel(Hero[1],raw('Rsag'))==0 and not Hero[1].paused and not Hero[1].hidden);Hero[1].dead=false
-- Real Foundation time is coarse: .5s, while visual callbacks run every .05s.
local coarseStart=TimeNow+100
TimeNow=coarseStart;Source40Now=TimeNow;AimX=100;AimY=0;cast(5,PlayableSkill[29],1,nil)
for frame=1,166 do
 TimeNow=coarseStart+math.floor(frame/10)*.5
 Source40Tick()
 if frame==14 then assert(not Source40Ball[5],'No early ball with half-second Foundation time')end
 if frame==16 then assert(Source40Ball[5],'Sub-second charge is driven by actual visual callbacks')end
end
assert(not Source40Ball[5] and not Source40BallCaster[5],'7.5s ball expires with coarse story time too')
for p=0,11 do RosterReset(p)end
assert(CreatedTimers==timerCount,'No per-cast or extra periodic timer')
TreeJumpInside,IsTerrainPathable,GetTerrainCliffLevel=inside,terrain,cliff
print('PASS: source-controlled concurrent balls/steering/pulses/endcast/AI/expiry; delayed smoke; timed native morph agility/death; area chakra channels/cleanup; actual native summon adoption/permanent pets;18 real bombs/no fallback; delayed native wind/no duplicate damage; source Sharingan/morph/death; no extra timers (mock natives).')
