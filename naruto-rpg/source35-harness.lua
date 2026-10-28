-- Execute real shipped3.5 adaptation and invasion controllers; native combat remains an engine test.
for p=0,11 do RosterReset(p)end
CampaignStage=0;CampaignTransition=false;World={};TimeNow=4000000
for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);Hero[p].hp=100000;Hero[p].maxLife=100000;Hero[p].agi=30;HeroRole[p]=p;HeroType[p]=Hero[p].type;Controllers[p]='human'end
local target=CreateUnit(12,123,200,0,0);target.hp=1000000;target.hero=true
local randomNative=GetRandomInt
function GetRandomInt(a,b)return b end
-- Exact17s gates and8 random rolls coexist, with their own owner and exact cleanup.
Source35Apply(3,18,2,nil);assert(Hero[3].agi==130 and Gate35Agility[3]==100 and Hero[3].speed==5000)
assert(math.abs(Hero[3].hp-100000/1.35)<.001)
Source35Apply(4,18,1,nil);assert(Hero[4].agi==80)
Source35Apply(3,17,1,nil)
for n=0,7 do TimeNow=4000000+n;Source35Tick()end
assert(Drunk35Agility[3]==75 and Hero[3].agi==205,'Eight rolls, with special fifth roll at rank1')
TimeNow=4000008;Source35Tick();assert(Hero[3].agi==130 and Drunk35Agility[3]==0)
TimeNow=4000017;Source35Tick();assert(Hero[3].agi==30 and Hero[4].agi==30 and Hero[3].speed==300)
Source35Apply(3,18,3,nil);local previous=Hero[3];Hero[3]=CreateUnit(3,999,0,0,0);Source35Tick()
assert(previous.agi==30 and (Hero[3].agi or 20)==20,'Cleanup must touch captured old hero, never its replacement')
GetRandomInt=randomNative
-- Every Lotus rank deals the exact original total and releases both actors. No hidden caster.
for rank=1,3 do
 local p=3;target.hp=1000000;Hero[p].hp=100000;Hits={}
 Source35Apply(p,15,rank,target);assert(Hero[p].paused and target.paused and not Hero[p].hidden)
 for n=1,20 do TimeNow=TimeNow+.5;Source35Tick()end
 local damage=0;for _,hit in ipairs(Hits)do damage=damage+hit.damage end
 assert(damage==({900,1100,1500})[rank] and not Hero[p].paused and not target.paused and not Lotus35Target[p])
 assert(Hero[p].flyHeight==0 and target.flyHeight==0 and Hero[p].pathing)
end
Source35Apply(3,15,3,target);target.hp=0;Source35Tick();assert(not Hero[3].paused and not target.paused and not Lotus35Target[3])
target.hp=1000000;Source35Apply(3,15,2,target);Source35Clear(3);assert(not Hero[3].paused and not target.paused)
-- Eight seeds schedule0/1/2/4 extra images each; every extra image copies the real Naruto.
local issueId=IssueTargetOrderById;local casts=0
function IssueTargetOrderById(u,id,t)assert(id==0xD0132 and GetUnitAbilityLevel(u,raw('R35i'))>0 and t==Hero[0] and not t.illusion);casts=casts+1;return true end
for rank=1,4 do
 World={};for n=1,8 do local c=CreateUnit(0,raw('R000'),n*10,0,0);c.illusion=true;World[#World+1]=c end
 local ally=CreateUnit(0,raw('R000'),0,0,0);World[#World+1]=ally
 local alien=CreateUnit(3,raw('R000'),0,0,0);alien.illusion=true;World[#World+1]=alien
 casts=0;Source35Apply(0,1,rank,nil);TimeNow=TimeNow+.5;Source35Tick()
 assert(casts==8*({0,1,2,4})[rank] and Clone35At[0]==0,'Exact8/16/24/40 totals')
 Source35Tick();assert(casts==8*({0,1,2,4})[rank],'No repeated multiplication next heartbeat')
end
IssueTargetOrderById=issueId
World={};Source35Apply(0,1,2,nil);TimeNow=TimeNow+.5;Source35Tick();assert(Clone35At[0]>0)
TimeNow=TimeNow+1;Source35Tick();assert(Clone35At[0]==0,'No leaked retry when native cast produces no seeds')
-- Helper-summoned bot images also receive an attack; retain one-attack fragile clone rule.
local getSummoner,getSummoned,attacked=GetSummoningUnit,GetSummonedUnit,GetTriggerUnit
local h=CreateUnit(0,raw('rdst'),0,0,0);h.abilities[raw('R35i')]=1
local image=CreateUnit(0,raw('R000'),0,0,0);image.illusion=true
function GetSummoningUnit()return h end;function GetSummonedUnit()return image end
Controllers[0]='computer';Dummy[0]=target;SkillsSummoned();assert(image.last and image.last.target==target)
function GetTriggerUnit()return image end;NativeEventDamage=1;SkillsFragileClone();NativeEventDamage=0;assert(image.hp==0)
GetSummoningUnit=getSummoner;GetSummonedUnit=getSummoned;GetTriggerUnit=attacked
-- Native shadow root follows the new Bmlt buff rather than disappearing after grace1s.
World={target};target.hp=1000000;target.abilities[raw('Bmlt')]=1
Source35Apply(6,30,1,target);assert(ShadowTarget[6]==target and ShadowDuration[6]==4)
TimeNow=TimeNow+1.5;RosterTick();assert(ShadowTarget[6]==target)
target.abilities[raw('Bmlt')]=nil;RosterTick();assert(not ShadowTarget[6])
-- Fourth skill uses a distinct native Channel order and an isolated real Amls helper.
for rank=1,3 do
 target.hero=true;target.hp=1000000
 Source35Apply(6,33,rank,target);local helper=Choke35Helper[6]
 assert(helper and GetUnitAbilityLevel(helper,raw('R35c'))==rank and helper.last.o=='magicleash')
 assert(Choke35Until[6]==TimeNow+3+rank and VisualChannelUntil[6]==Choke35Until[6])
 TimeNow=TimeNow+3+rank;Source35Tick();assert(helper.removed and not Choke35Helper[6])
 Source35Apply(6,33,rank,target);helper=Choke35Helper[6]
 Caster=Hero[6];Spell=raw('R604');SkillsEndcast();assert(helper.removed and not Choke35Target[6] and VisualChannelUntil[6]==0)
end
-- Barrage chunks crowded casts, preserves all targets, filters friends, creates1/1/2 native mines.
local oldTargetOrder=IssueTargetOrder;local darts=0
function IssueTargetOrder(u,o,t)if GetUnitAbilityLevel(u,raw('R35k'))>0 then assert(o=='thunderbolt');darts=darts+1 end;return oldTargetOrder(u,o,t)end
local function count(g)local n=0;for _,u in ipairs(g)do n=n+1 end;return n end
for rank=1,3 do
 Source35Clear(6);Hero[6].x=0;Hero[6].y=0;World={};AimX=100;AimY=0
 for n=1,25 do World[#World+1]=CreateUnit(12,123,100,n,0)end
 World[#World+1]=CreateUnit(6,123,100,0,0)
 darts=0;Source35Apply(6,32,rank,nil);Source35Tick();assert(darts==12 and count(Barrage35Shots[6])==14)
 Source35Tick();Source35Tick();assert(darts==25 and count(Barrage35Shots[6])==0)
 TimeNow=TimeNow+1;for i=1,3 do Source35Tick()end
 assert(count(Source35MineUnits[6])==25*({1,1,2})[rank])
 local mine=Source35MineUnits[6][1];mine.hp=0;Source35MineCheck[6]=0;Source35Tick();assert(mine.removed)
 Source35Clear(6);assert(count(Source35MineUnits[6])==0)
end
IssueTargetOrder=oldTargetOrder
-- Dedicated recovery handles visible transparent Sasuke and a stale pause, without disturbing a fresh lock.
CampaignStage=12;CampaignTransition=false;HeroRole[7]=1;HeroRole[1]=7;local sasuke=Hero[7]
sasuke.x=CampaignX[12];sasuke.y=CampaignY[12];sasuke.hidden=false;sasuke.paused=false;sasuke.alpha=255
NPCCooldowns=InitHashtable();InvasionHeroVisibility();assert(SasukeSafeReady[7])
function SetUnitVertexColorBJ(u,r,g,b,t)SetUnitVertexColor(u,math.floor(r*2.55),math.floor(g*2.55),math.floor(b*2.55),math.floor((100-t)*2.55+.5))end
InvasionSourceColor(sasuke,100,100,100,100);assert(sasuke.alpha==0)
TimeNow=TimeNow+9;InvasionHeroVisibility();assert(sasuke.alpha==0)
TimeNow=TimeNow+1;InvasionHeroVisibility();assert(sasuke.alpha==255)
sasuke.paused=true;InvasionHeroVisibility();TimeNow=TimeNow+14;InvasionHeroVisibility();assert(sasuke.paused)
TimeNow=TimeNow+1;InvasionHeroVisibility();assert(not sasuke.paused)
Source35Apply(9,15,3,sasuke);TimeNow=TimeNow+20;InvasionHeroVisibility();assert(sasuke.paused,'Never release a live cast-local Lotus victim');Source35Clear(9)
-- Critical recovery and timed boss attack execute before a deliberately aborted heavy story tick.
local originalStoryTick=StoryTick
function StoryTick()error('simulated Classic operation budget exhaustion')end
sasuke.hidden=true;InvasionHeroVisibility();TimeNow=TimeNow+10
local boss=CreateUnit(9,raw('c00D'),CampaignSupportX[4],CampaignSupportY[4],0)
boss.paused=true;boss.abilities[raw('Avul')]=1
CampaignVillageOro=boss;CampaignOroSlot=1;CampaignActor[1]=boss;CampaignActorType[1]=13
CampaignOroStarted=false;CampaignOroAt=TimeNow;CampaignEventDue[3]=true;CampaignAttackOwner=9;CampaignFinished=false
local countBefore=CampaignCount
local ok,err=pcall(FoundationTick);assert(not ok and string.find(tostring(err),'simulated') and not sasuke.hidden,'Guard ran before overloaded story')
assert(CampaignOroStarted and not boss.paused and GetUnitAbilityLevel(boss,raw('Avul'))==0 and boss.last.o=='attack','Boss releases before overloaded story')
assert(CampaignCount==countBefore,'Release existing boss once; never scan/resurrect extra bosses')
boss.hp=0;TimeNow=TimeNow+10;InvasionOroWatch();assert(CampaignVillageOro==boss and CampaignCount==countBefore)
StoryTick=originalStoryTick
for p=0,11 do RosterReset(p)end
for n=0,63 do assert(not Source35Wire[n],'Wire cleanup is bounded and complete')end
print('PASS: source3.5 Lee concurrent buffs/exact cleanup and Lotus3 ranks;8/16/24/40 illusion copying, retry/AI/one-hit rule; native shadow buff and crowded barrage/mine/wire cleanup; Sasuke alpha/pause recovery and early independent heartbeat (mock natives).')
