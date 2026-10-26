-- Real shipped handlers; native missile damage/cooldown needs Warcraft validation.
for p=0,11 do RosterReset(p)end
CampaignTransition=false;CampaignStage=0;TimeNow=9900000;World={}
local inside,terrain,cliff=TreeJumpInside,IsTerrainPathable,GetTerrainCliffLevel
function TreeJumpInside(p,x,y)return true end
function GetTerrainCliffLevel(x,y)return 0 end
function IsTerrainPathable(x,y,t)return false end
local lee=CreateUnit(3,raw('R003'),0,0,0);Hero[3]=lee;HeroType[3]=lee.type;HeroRole[3]=3
local enemy=CreateUnit(12,123,90,0,0);enemy.hp=10000
local hitCount=#Hits
Source35Apply(3,16,1,enemy);VisualApply(3,16,1,enemy)
assert(lee.x==0 and lee.flyHeight==100 and not SkillPoseQueued[3])
for f=1,6 do Lee42Tick()end
assert(lee.x==0 and lee.timeScale==2)
Lee42Tick();assert(lee.x==50 and lee.animationIndex==3 and lee.timeScale==1)
for f=8,25 do Lee42Tick()end
assert(math.abs(enemy.x-294)<.001 and lee.flyHeight==0 and not Kick35Caster[3])
assert(#Hits==hitCount,'Native Firebolt alone owns HP damage, no duplicate script hit')
-- Obstructed or cross-scene paths never teleport/push through walls.
lee.x=0;enemy.x=90
function IsTerrainPathable(x,y,t)return true end
Source35Apply(3,16,1,enemy);for f=1,25 do Lee42Tick()end
assert(lee.x==0 and enemy.x==90)
function IsTerrainPathable(x,y,t)return false end
Source35Apply(3,16,1,enemy);lee.dead=true;Lee42Tick();assert(not Kick35Caster[3] and lee.flyHeight==0);lee.dead=false
-- Original Suiken9 ->6/6/6 at1.5x, then restore; randomness already tested by source35-harness.
lee.agi=30;Source35Apply(3,17,1,nil);VisualApply(3,17,1,nil)
assert(lee.animationIndex==9 and not SkillPoseQueued[3])
for f=1,6 do Lee42Tick()end
assert(lee.animationIndex==6 and lee.timeScale==1.5)
for f=7,24 do Lee42Tick()end
assert(lee.timeScale==1 and lee.animation=='stand' and not Lee42DrinkCaster[3] and Drunk35Left[3]==8)
Source35Clear(3);assert(lee.agi==30)
Source35Apply(3,17,1,nil);lee.paused=true;Lee42Tick();assert(not Lee42DrinkCaster[3] and lee.timeScale==1);lee.paused=false
-- Actual bot dispatch prioritizes Sharingan; an accepted order isn't a native spell effect.
local sasuke=CreateUnit(1,raw('R001'),0,0,0);Hero[1]=sasuke;HeroType[1]=sasuke.type;HeroRole[1]=1
sasuke.mana=2000;sasuke.points=0;sasuke.abilities[raw('Rs02')]=2
Dummy[0]=enemy;enemy.x=100;enemy.hidden=false;enemy.invisible=false
BotNextCast[1]=0;BotReadyAt[6]=0;SharinganUntil[1]=0;VisualChannelUntil[1]=0;ComboLeft[1]=0;SkillDataReady=true
local nativeOrder=IssueImmediateOrder;local n=0
function IssueImmediateOrder(u,o)n=n+1;assert(u==sasuke and o=='stomp');return false end
assert(not SkillsBot(1) and BotReadyAt[6]==0 and n==1,'Rejected order cannot spend the sixty-second cooldown')
function IssueImmediateOrder(u,o)n=n+1;assert(u==sasuke and o=='stomp');return true end
assert(SkillsBot(1) and BotReadyAt[6]==0,'Accepted order alone still cannot consume the real cooldown')
Caster=sasuke;Spell=raw('Rs02');Target=nil;SkillsEffect()
assert(SharinganUntil[1]==TimeNow+10.5 and GetUnitAbilityLevel(sasuke,raw('Rsag'))==2)
assert(BotReadyAt[6]==TimeNow+62 and not sasuke.paused and not sasuke.hidden)
TimeNow=TimeNow+3;local oldCount=n;assert(not SkillsBot(1) and n==oldCount,'Do not reissue while already active')
TimeNow=SharinganUntil[1]+.5;SkillsTick();assert(GetUnitAbilityLevel(sasuke,raw('Rsag'))==0)
TimeNow=BotReadyAt[6]+.5;assert(SkillsBot(1),'Bot uses Sharingan again after its real cooldown')
IssueImmediateOrder=nativeOrder;TreeJumpInside,IsTerrainPathable,GetTerrainCliffLevel=inside,terrain,cliff
for p=0,11 do RosterReset(p)end
print('PASS: source Lee melee kick/17 safe pushes/fine-clock poses/no duplicate damage; Suiken source pose cleanup; actual Sharingan bot priority/rejected and interrupted orders/effect cooldown/reuse (native mocks).')
