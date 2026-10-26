-- New behavior is exercised through the shipped JASS and existing native mocks.
for p=0,11 do RosterReset(p)end
CampaignStage=0;CampaignFinished=false;CampaignTransition=false;ExamPhase=3;TimeNow=9000000;World={};CampaignAlliances(1)
for t=0,3 do StoryStage[t]=7;StoryMembers[t]=3 end
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+p,-10000+p*100,-10000,0);Hero[p].hp=10000;Hero[p].maxLife=10000;HeroRole[p]=p;HeroType[p]=Hero[p].type;CampaignPermanentDead[p]=false;CampaignClonePending[p]=false
end
ExamKabutoClear();ExamKabutoAt=TimeNow+540
local npc=NPCTry
function NPCTry()return false end
TimeNow=TimeNow+539.75;ExamKabutoTick();assert(not ExamKabuto,'No Kabuto before source nine-minute delay')
TimeNow=TimeNow+.25;ExamKabutoTick();local kabuto=ExamKabuto
assert(kabuto and kabuto.type==raw('c00B') and kabuto.owner==12 and ExamKabutoAt==0)
assert(GetUnitAbilityLevel(kabuto,raw('A018'))==3 and GetUnitAbilityLevel(kabuto,raw('A02D'))==3)
assert(GetUnitAbilityLevel(kabuto,raw('A028'))==1 and GetUnitAbilityLevel(kabuto,raw('ACcr'))==1 and GetUnitAbilityLevel(kabuto,raw('S02B'))==0)
TimeNow=TimeNow+2;kabuto.hp=10000;kabuto.mana=1500;ExamKabutoCrippleAt=TimeNow+1000
-- All four squads can be hunted, and invisible/finished participants are excluded.
for team=0,3 do
 for p=0,11 do Hero[p].x=kabuto.x+3000;Hero[p].y=kabuto.y end
 local h=Hero[team*3];h.x=kabuto.x+300;h.y=kabuto.y;ExamKabutoTarget=nil;kabuto.order=0
 ExamKabutoTick();assert(kabuto.last.o=='attack' and kabuto.last.target==h,'Hunt every squad, not only the human')
end
local h=Hero[9];h.invisible=true;h.detected=false;ExamKabutoTarget=nil;kabuto.order=0
ExamKabutoTick();assert(ExamKabutoTarget~=h,'No pursuit of undetected invisibility');h.invisible=false
StoryStage[3]=8;ExamKabutoTarget=nil;ExamKabutoTick();assert(ExamKabutoTarget~=h,'Passed team is no longer hunted');StoryStage[3]=7
-- Kabuto steals real scrolls on his killing blow, preserving ordinary equipment.
local victim=Hero[0];victim.hp=0;victim.items={};kabuto.items={}
local sky=CreateItem(raw('Eshe'),0,0);local earth=CreateItem(raw('Esea'),0,0);local gear=CreateItem(raw('Nlku'),0,0)
UnitAddItem(victim,sky);UnitAddItem(victim,earth);UnitAddItem(victim,gear)
local killer=GetKillingUnit
function GetKillingUnit()return kabuto end
Caster=victim;StoryStage[0]=7;ExamKabutoKill()
assert(not CampaignPermanentDead[0] and StoryRevive[0]==TimeNow+20 and victim.items[2]==gear)
assert(kabuto.items[0]==sky and kabuto.items[1]==earth and not sky.removed and not earth.removed,'Actual scrolls move to Kabuto, no copies or lost equipment')
GetKillingUnit=killer;victim.hp=10000
-- Self healing is a real source drain order and preserves the full channel.
kabuto.hp=2500;ExamKabutoHealAt=0;ExamKabutoTick();assert(kabuto.last.o=='drain' and kabuto.last.target==kabuto)
local previous=kabuto.last;TimeNow=TimeNow+1;ExamKabutoTick();assert(kabuto.last==previous and NPCBusy(kabuto),'Do not cancel healing with a new attack')
TimeNow=TimeNow+20;kabuto.hp=0;ExamKabutoTick();assert(ExamKabuto==kabuto and ExamKabutoAt==0,'Kabuto never respawns after death')
assert(not sky.owned and not earth.owned and not kabuto.items[0] and not kabuto.items[1],'Defeated Kabuto drops the stolen scrolls for recovery')
ExamPhase=4;ExamKabutoTick();assert(not ExamKabuto and kabuto.removed,'Leaving forest cleans actor and state')
NPCTry=npc
-- Deferred melee approach cannot cancel native cooldown commitment or cross obstacles.
local p=1;local caster=Hero[p];caster.x=0;caster.y=0;caster.paused=false;caster.hidden=false;caster.hp=10000
local enemy=CreateUnit(12,123,400,0,0);enemy.hp=10000;World={enemy};AimX=400;AimY=0
local terrain=IsTerrainPathable;local cliff=GetTerrainCliffLevel
function IsTerrainPathable()return false end
function GetTerrainCliffLevel()return 0 end
VisualApply(p,8,1,enemy);assert(caster.x==0,'No SetUnitPosition inside SPELL_EFFECT')
TimeNow=TimeNow+.11;VisualApproachTick(p);assert(caster.x==30 and VisualApproachTarget[p]==enemy,'Source-speed rush starts after native cooldown commitment')
for k=1,12 do TimeNow=TimeNow+.05;VisualApproachTick(p)end
assert(caster.x>=290 and caster.x<=320 and not VisualApproachTarget[p] and caster.animationIndex==11,'Source rush finishes with a separate strike')
caster.x=0;VisualApply(p,8,1,enemy)
function IsTerrainPathable(x,y)return x>=120 and x<=250 end
TimeNow=TimeNow+.11
for k=1,10 do VisualApproachTick(p);TimeNow=TimeNow+.05 end
assert(caster.x<120 and not VisualApproachTarget[p],'Rush stops before a blocked route')
caster.x=0
function IsTerrainPathable()return false end
VisualApply(p,8,1,enemy);enemy.hp=0;TimeNow=TimeNow+.11;VisualApproachTick(p);assert(caster.x==0 and not VisualApproachCaster[p],'Death releases references without moving hero')
enemy.hp=10000;VisualApply(p,8,1,enemy);VisualClearHero(p);assert(not VisualApproachTarget[p] and VisualApproachAt[p]==0,'Scene reset cancels pending approach')
IsTerrainPathable=terrain;GetTerrainCliffLevel=cliff
-- Source40 native/controlled actors now own these paths; no duplicate cosmetic line.
for _,role in ipairs({5,11})do
 local hero=Hero[role];hero.x=0;hero.y=0;hero.hp=10000;hero.facing=0
 AimX=750;AimY=0;VisualApply(role,role==5 and 29 or 59,1,nil)
 for n=0,255 do if VisualUnit[n]and VisualOwner[n]==role then assert(VisualUnit[n].type~=raw('vbal')and VisualUnit[n].type~=raw('vrac'),'No old line adaptation over the original mechanics')end end
 VisualClearHero(role)
end
-- The big wind is native; a repeated body animation must not cancel its orders.
local hero=Hero[11];hero.hp=10000;VisualChannelIndex[11]=58;VisualChannelUntil[11]=TimeNow+8;VisualWindPoseAt[11]=TimeNow
VisualTick();assert(hero.animationIndex==SkillAnimation[58] and VisualWindPoseAt[11]==TimeNow+1)
VisualChannelUntil[11]=0;VisualClearHero(11)
-- A clone victim stays dead while another hero completes the end-game encounters.
CampaignStage=27;CampaignTransition=false;CampaignFinished=false;CampaignNarutoPlayer=0;CampaignSasukePlayer=1;CampaignCount=0
for p=0,11 do Hero[p].hp=0;CampaignPermanentDead[p]=false;CampaignClonePending[p]=false end
Hero[5].hp=10000;CampaignLateProgress();assert(CampaignTransition and CampaignQueued==28 and CampaignPermanentDead[0] and not CampaignPermanentDead[5])
CampaignStage=28;CampaignMoveHeroes();assert(Hero[0].hp==0 and CampaignPermanentDead[0],'Transition does not revive fallen Naruto')
CampaignTransition=false;CampaignStage=27;Hero[5].hp=0;CampaignLateProgress();assert(not CampaignTransition and CampaignSurvivors()==0,'No automatic recovery after the last survivor dies')
print('PASS: source-timed single forest Kabuto/all squads/invisibility/channel/death/cleanup; deferred Sasuke approach and obstacle/death/reset guards; matching Tenten/Temari line graphics; native wind pose loop; survivors continue without resurrecting victims (mock natives).')


-- A defeated clone advances its actual hero; a losing hero is eliminated permanently.
CampaignStage=17;CampaignTransition=false;CampaignFinished=false;CampaignCount=0;CampaignActor[0]=nil;CampaignActor[1]=nil
for p=0,11 do Hero[p].hp=0;CampaignPermanentDead[p]=p~=1;CampaignClonePending[p]=false;CampaignClone[p]=nil end
Hero[5].hp=10000;CampaignPermanentDead[5]=false;CampaignClonePending[5]=true;CampaignClone[5]=CreateUnit(12,123,0,0,0);CampaignClone[5].hp=0
CampaignClonePending[4]=true;CampaignPermanentDead[4]=false;CampaignClone[4]=CreateUnit(12,123,0,0,0)
CampaignClonesTick();assert(Hero[5].x==CampaignX[17] and Hero[5].y==CampaignY[17],'Winner returns to Naruto and Sakura at cave entrance');assert(not CampaignClonePending[5] and not CampaignPermanentDead[5] and CampaignPermanentDead[4] and not CampaignClone[4])
CampaignLateProgress();assert(CampaignTransition and CampaignQueued==26,'Resume the existing cave story after regrouping, without skipping its stages')
CampaignStage=29;CampaignMoveHeroes();assert(Hero[5].hp>0 and Hero[4].hp==0 and Hero[0].hp==0,'Winners advance, victims never revive')
print('PASS: clone winners return to the cave entrance, losers remain eliminated; existing subsequent cave stages preserved, with no resurrection checkpoint.')
-- Real StoryTick revival branch: a forest death remains a twenty-second respawn.
CampaignStage=0;CampaignTransition=false;CampaignFinished=false;ExamPhase=3;TimeNow=9100000
local campaignTick,chapterTick,hudTick,mentorThink=CampaignTick,NextChapterTick,HUDTick,StoryMentorThink
function CampaignTick()end
function NextChapterTick()end
function HUDTick()end
function StoryMentorThink()end
for t=0,3 do StoryMembers[t]=t==0 and 1 or 0;StoryStage[t]=7;StoryStarted[t]=true;StoryAdvanceAt[t]=0 end
StoryPopulateCursor=64;StoryEnemy={};EnemyPending=setmetatable({},{__index=function()return 0 end})
Hero[0]=CreateUnit(0,raw('R000'),10,20,0);Hero[0].hp=0;Hero[0].mana=0;Hero[1]=nil;Hero[2]=nil;Controllers[0]='human'
SpawnX[0]=123;SpawnY[0]=456;CampaignPermanentDead[0]=false;StoryRevive[0]=TimeNow+20
local fallen=Hero[0]
TimeNow=TimeNow+19.75;StoryTick();assert(fallen.hp==0,'No early forest resurrection')
TimeNow=TimeNow+.25;StoryTick();assert(fallen.hp>0 and Hero[0]==fallen and fallen.x==123 and fallen.y==456 and StoryRevive[0]==0,'Same hero respawns in forest camp at20s')
CampaignTick,NextChapterTick,HUDTick,StoryMentorThink=campaignTick,chapterTick,hudTick,mentorThink
print('PASS: actual StoryTick respawns the original forest hero at20seconds, independent of Kabuto death, without permanent elimination.')
