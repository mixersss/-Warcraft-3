-- No fake boss deaths: exercise the actual entrance and stage-transition predicates.
for p=0,11 do RosterReset(p)end
TimeNow=6000000;CampaignStage=17;CampaignFinished=false;CampaignTransition=false;World={};CampaignCount=2;CampaignNarutoPlayer=0;CampaignSasukePlayer=1;CampaignLeader=0
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+p,CampaignX[17],CampaignY[17],0);Hero[p].level=20;Hero[p].points=0;HeroRole[p]=p;HeroType[p]=Hero[p].type;CampaignPermanentDead[p]=false;CampaignClonePending[p]=false;CampaignClone[p]=nil;Controllers[p]='computer'
end
CampaignAlliances(1);CampaignRogueAlliance();Hero[1].hidden=true;Hero[1].paused=true
for j=0,1 do CampaignActor[j]=CreateUnit(12,raw('c013'),CampaignTX[17]+j*100,CampaignTY[17],0);CampaignActor[j].abilities[raw('Avul')]=1;CampaignActorType[j]=19 end
CampaignLateProgress();assert(not CampaignTransition and GetUnitAbilityLevel(CampaignActor[0],raw('Avul'))==1,'Distant Sakura does not magically remove entrance protection')
local sakura=Hero[2];sakura.x=CampaignTX[17];sakura.y=CampaignTY[17];StoryMarch[0]=true;StoryRetreat[0]=false
local learn=SelectHeroSkill
function SelectHeroSkill()error('Never force an unavailable skill or spend player points to unlock a quest')end
CampaignLateProgress();assert(not CampaignTransition and CampaignActor[0].hp>0 and GetUnitAbilityLevel(CampaignActor[0],raw('Avul'))==0,'Sakura opens vulnerability, not a free kill')
CampaignBot(2,nil);assert(sakura.last.o=='attack' and sakura.last.target==CampaignActor[0]);assert(sakura.level==20 and sakura.points==0 and GetUnitAbilityLevel(sakura,raw('R204'))==0)
assert(CampaignNearest(0)==CampaignActor[0]or CampaignNearest(0)==CampaignActor[1],'All allies can target opened boulders')
SelectHeroSkill=learn
-- If Sakura is absent/dead, the original fallback still requires clearing ordinary guards.
CampaignPermanentDead[2]=true;sakura.hp=0;CampaignCount=3;CampaignActor[2]=CreateUnit(12,raw('c00F'),CampaignTX[17],CampaignTY[17],0)
CampaignLateProgress();assert(not CampaignTransition and CampaignActor[0].hp>0)
CampaignActor[2].hp=0;CampaignLateProgress();assert(CampaignTransition and CampaignQueued==26 and CampaignActor[0].hp==0)
-- Every required late boss remains a gate until defeated; then the exact next stage is queued.
for _,stage in ipairs({26,27,28})do
 CampaignStage=stage;CampaignTransition=false;CampaignCount=1;CampaignActor[0]=CreateUnit(12,123,0,0,0)
 CampaignLateProgress();assert(not CampaignTransition,'Never bypass a living boss')
 CampaignActor[0].hp=0;CampaignLateProgress();assert(CampaignTransition and CampaignQueued==stage+1)
end
CampaignStage=29;CampaignTransition=false;CampaignSasuke=Hero[1];Hero[1].hp=10000
CampaignLateProgress();assert(not CampaignTransition,'Wait for actual Sasuke defeat')
Hero[1].hp=0;CampaignLateProgress();assert(CampaignTransition and CampaignQueued==30)
-- Alpha33: Naruto's death no longer defeats other living heroes or resurrects him.
CampaignStage=28;CampaignTransition=false;CampaignCount=0;Hero[0].hp=0
CampaignLateProgress();assert(CampaignTransition and CampaignQueued==29 and CampaignPermanentDead[0] and Hero[0].hp==0,'Survivors continue; Naruto remains permanently dead')
Hero[0].hp=10000;CampaignPermanentDead[0]=false;CampaignStage=27;CampaignTransition=false;CampaignCount=0
local story=StoryTick
function StoryTick()error('simulated overloaded scene processing')end
local ok=pcall(FoundationTick);assert(not ok and CampaignTransition and CampaignQueued==28,'Late transition executes before an exhausted story callback')
StoryTick=story
print('PASS: low-level Sakura entrance without free skill/level/stat/kill; allied boulder targeting; absent-Sakura guard requirement; cave progression and final enemy death gate; defeat priority and isolated progression before overloaded story (mock natives).')
