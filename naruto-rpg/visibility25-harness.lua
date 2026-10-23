local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
-- Recover only the real Sasuke, after a stale ShowUnit(false) in active invasion.
TimeNow=3000000;CampaignStage=12;CampaignTransition=false;World={}
for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;HeroType[p]=Hero[p].type;SasukeHiddenSince[p]=0 end
HeroRole[7]=1;HeroRole[1]=7;local sasuke=Hero[7]
sasuke.hidden=true;sasuke.paused=true;sasuke.pathing=false;sasuke.flyHeight=500;sasuke.alpha=0
InvasionHeroVisibility();TimeNow=TimeNow+9;InvasionHeroVisibility();assert(sasuke.hidden,'Preserve a normal short NPC technique')
TimeNow=TimeNow+1;InvasionHeroVisibility();assert(not sasuke.hidden and not sasuke.paused and sasuke.pathing and sasuke.flyHeight==0 and sasuke.alpha==255,'Stale hide releases actual character after10s')
sasuke.paused=true;InvasionHeroVisibility();assert(sasuke.paused,'Never release unrelated stuns on visible heroes');sasuke.paused=false
sasuke.abilities[raw('BOwk')]=1;InvasionHeroVisibility();assert(GetUnitAbilityLevel(sasuke,raw('BOwk'))==1,'Native Wind Walk is not ShowUnit(false)')
for _,stage in ipairs({14,17,26,28})do CampaignStage=stage;sasuke.hidden=true;sasuke.paused=true;TimeNow=TimeNow+20;InvasionHeroVisibility();TimeNow=TimeNow+20;InvasionHeroVisibility();assert(sasuke.hidden and sasuke.paused,'Preserve plot-bound hiding')end
CampaignStage=12;CampaignTransition=true;InvasionHeroVisibility();TimeNow=TimeNow+20;InvasionHeroVisibility();assert(sasuke.hidden,'No recovery during cinematic transition')
CampaignTransition=false;sasuke.hidden=false;InvasionHeroVisibility();Hero[2].hidden=true;TimeNow=TimeNow+20;InvasionHeroVisibility();assert(Hero[2].hidden,'Do not alter other hidden characters')
-- Actual invasion setup/event: autonomous Orochimaru even with a human Sand owner.
CampaignClear();CampaignVillageLandmarksClose();StoryShopsClose();World={};CampaignStage=12;CampaignTransition=true;CampaignFinished=false;CampaignLeader=0
for p=0,11 do HeroRole[p]=p;Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroType[p]=Hero[p].type;CampaignPermanentDead[p]=false end
CampaignBindRoles();CampaignAlliances(2);CampaignMoveHeroes();CampaignSpawnStage()
local oro=CampaignVillageOro;assert(oro.paused and GetUnitAbilityLevel(oro,raw('Avul'))==1,'Cannot kill the scheduled boss before his entrance')
while CampaignDeployCursor<242 do CampaignDeploy()end
CampaignStartPlay();Controllers[9]='human';CampaignAttackOwner=9;TimeNow=CampaignOroAt
CampaignInvasionEvents();assert(oro.owner==9 and not oro.paused and GetUnitAbilityLevel(oro,raw('Avul'))==0 and not oro.hidden)
assert(oro.last.o=='attack'and oro.last.x==CampaignRouteX[3]and oro.last.y==CampaignRouteY[3],'Timer actually starts the village march')
local slot=-1;for j=0,CampaignCount-1 do if CampaignActor[j]==oro then slot=j end end
assert(slot>=0 and CampaignActorRoute[slot]==3)
local count=CampaignCount;CampaignInvasionEvents();assert(CampaignCount==count and CampaignOroAt==0,'No repeated event spawn')
NPCCooldowns=InitHashtable();Hero[0].x=oro.x+100;Hero[0].y=oro.y;Hero[0].hp=10000;oro.last=nil;World={Hero[0]};CampaignThinkCursor=slot
TimeNow=TimeNow+1;InvasionOroWatch();assert(oro.last,'Human ownership must not disable the story boss AI')
SaveReal(NPCCooldowns,GetHandleId(oro),0,0);World={};TimeNow=TimeNow+5;CampaignMoveAt[slot]=0;CampaignWalkAt[slot]=TimeNow+100;CampaignThinkCursor=slot;oro.last=nil
InvasionOroWatch();assert(oro.last and oro.last.o=='attack','Keep marching when no nearby target is present')
print('PASS: character-bound stale hide recovery with pose/control/pathing reset, native/plot invisibility preserved; protected scheduled Orochimaru, actual timed attack route and autonomous human-owner AI (mock natives).')
-- Reproduce a second cast overwriting the old shared caster during the first sleep.
local saved={};local function mock(name,f)saved[name]=_G[name];_G[name]=f end
local actor=Hero[7];local victim=Hero[0];local stranger=Hero[8];local otherTarget=Hero[6]
actor.hidden=false;actor.paused=false;victim.paused=false;stranger.hidden=true;local overwritten=false
Caster=actor;Target=victim
mock('ShowUnitHide',function(u)ShowUnit(u,false)end);mock('ShowUnitShow',function(u)ShowUnit(u,true)end)
mock('PlaySoundOnUnitBJ',function()end);mock('UnitDamageTargetBJ',function()end)
mock('AngleBetweenPoints',function(a,b)return math.atan(b.y-a.y,b.x-a.x)*180/math.pi end)
mock('GetUnitLoc',function(u)return {x=u.x,y=u.y}end);mock('RemoveLocation',function()end)
local function spawn(count,id,owner,l,face)bj_lastCreatedUnit=CreateUnit(owner,id,l.x,l.y,0)end
mock('CreateNUnitsAtLoc',spawn);mock('CreateNUnitsAtLocFacingLocBJ',spawn)
mock('OrigNPC_M3V',function(l,d,a)return {x=l.x+d,y=l.y}end)
mock('SetUnitPositionLocFacingLocBJ',function(u,l,f)SetUnitPosition(u,l.x,l.y)end)
mock('SetUnitTimeScalePercent',function(u,n)SetUnitTimeScale(u,n/100)end)
mock('AddSpecialEffectTargetUnitBJ',function(point,u,model)bj_lastCreatedEffect=AddSpecialEffectTarget(model,u,point)end)
mock('SetUnitColor',function()end);mock('ConvertPlayerColor',function(x)return x end)
mock('IssueTargetOrderById',function()return true end);mock('IssuePointOrderByIdLoc',function()return true end)
mock('UnitApplyTimedLifeBJ',function()end);mock('EnableTrigger',function()end);mock('DisableTrigger',function()end)
mock('TriggerSleepAction',function(seconds)
 if actor.hidden and not overwritten then OrigNPC_QC=stranger;OrigNPC_PC=otherTarget;overwritten=true end
end)
OrigNPC_MLE()
assert(overwritten and not actor.hidden and not actor.paused and not victim.paused,'Resume the real participants after a shared-global overwrite')
assert(stranger.hidden,'Never reveal an unrelated caster from the second cast')
for name,f in pairs(saved)do _G[name]=f end
print('PASS: actual source combo resumes its cast-local Sasuke/target after concurrent global overwrite (mock natives).')
