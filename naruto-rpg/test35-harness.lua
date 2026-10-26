-- Exercise actual chat, early-scene cleanup/transition and native invasion events.
for p=0,11 do RosterReset(p)end
CampaignClear();CampaignStage=0;CampaignQueued=0;CampaignTransition=false;CampaignFinished=false;CampaignFastTestQueued=false;CampaignFastTestActive=false
CampaignActor={};CampaignActorType={};CampaignCount=0;CampaignClone={};CampaignClonePending={};World={}
StoryEnemy={};ExamEnemy={};StoryMentor={};ExamFountain={};ExamTower=nil;ExamRect=nil
StoryPopulateClock=nil;StoryMentorClock=nil;StoryMentorDialog=nil;ExamAnswers=nil;ExamClock=nil;ExamDialog=nil;PhaseClock=nil;PhaseDialog=nil
SkillDataReady=true;SpawnClock=nil;StoryPopulateCursor=64;ExamPhase=0;TimeNow=9700000
for t=0,3 do StoryMembers[t]=3;StoryStage[t]=1;StoryStarted[t]=true;StoryAdvanceAt[t]=0 end
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);Hero[p].level=20;Hero[p].points=0;Hero[p].xp=1234;Hero[p].hp=10000;Hero[p].maxLife=10000;Hero[p].maxMana=2000;Hero[p].mana=2000
 HeroRole[p]=p;HeroType[p]=Hero[p].type;HeroTemplate[p]=p;CampaignPermanentDead[p]=false;Controllers[p]='computer';StoryRevive[p]=0
end
Controllers[0]='human'
local player,chat,slot=GetTriggerPlayer,GetEventPlayerChatString,GetPlayerSlotState
local sender=0;local message='-village fast'
function GetTriggerPlayer()return sender end
function GetEventPlayerChatString()return message end
function GetPlayerSlotState(p)return PLAYER_SLOT_STATE_PLAYING end
sender=3;FoundationChat();assert(not CampaignTransition and not CampaignFastTestQueued,'Only the first human can start the scenario')
sender=0;SkillDataReady=false;FoundationChat();assert(not CampaignTransition and not CampaignFastTestQueued,'Do not latch fast mode when hero creation is not ready')
SkillDataReady=true;FoundationChat();assert(CampaignTransition and CampaignQueued==12 and CampaignFastTestQueued,'Actual chat queues the existing village transition')
local start=CampaignIntroAt
TimeNow=start+1.5;CampaignTick();assert(CampaignStage==12 and CampaignPlaced and not CampaignFastTestActive,'Wait for scene deployment before releasing attackers')
local guard=0
while CampaignTransition and guard<30 do TimeNow=TimeNow+.5;CampaignTick();guard=guard+1 end
assert(not CampaignTransition and CampaignFastTestActive and not CampaignFastTestQueued and CampaignFastWaveCursor==8)
for p=0,11 do assert(Hero[p].level==(p<3 and 45 or 20),'Only all three first-team heroes get test level45')end
assert(CampaignDefenseOwner==13,'Leaf NPCs never belong to the red human')
for j=0,CampaignCount-1 do
 local k=CampaignActorType[j]
 if k==0 or k==1 or k==2 or k==17 or k==29 or k==30 or k==31 or k==32 or k==33 or k==34 then
  assert(CampaignActor[j].owner==13,'All Leaf defenders, medics and reinforcements stay autonomous')
 end
end
for p=0,11 do
 assert(not GetPlayerAlliance(13,p,ALLIANCE_SHARED_CONTROL) and not GetPlayerAlliance(13,p,ALLIANCE_SHARED_ADVANCED_CONTROL),'No human has NPC control')
 assert(IsUnitEnemy(CampaignActor[0],p)==(HeroRole[p]>=9),'NPC side allied to Leaf and hostile to Sand regardless player slot')
end
assert(FoundationAlive(CampaignVillageKabuto) and FoundationAlive(CampaignVillageSnake) and FoundationAlive(CampaignVillageOro) and CampaignOroStarted)
assert(CampaignVillageKabuto.owner==15 and CampaignVillageSnake.owner==15 and CampaignVillageOro.owner==15,'All attacker bosses are autonomous')
for j=0,CampaignCount-1 do
 if CampaignActorRoute[j]>=0 then assert(CampaignActor[j].owner==15,'Every attack stream stays outside human slots')end
end
for p=0,11 do
 assert(not GetPlayerAlliance(15,p,ALLIANCE_SHARED_CONTROL) and not GetPlayerAlliance(15,p,ALLIANCE_SHARED_ADVANCED_CONTROL),'Temari and all others have no enemy army control')
 assert(IsUnitEnemy(CampaignVillageKabuto,p)==(HeroRole[p]<9),'Attacker NPCs remain allied to Sand heroes and hostile to Leaf')
end
assert(IsUnitEnemy(CampaignVillageKabuto,13) and IsUnitEnemy(CampaignActor[0],15),'Both autonomous armies must fight each other')
assert(not CampaignVillageOro.paused and GetUnitAbilityLevel(CampaignVillageOro,raw('Avul'))==0 and CampaignVillageOro.last.o=='attack','Orochimaru really starts marching')
for j=0,3 do assert(CampaignEventClock[j]==nil and CampaignEventDialog[j]==nil,'Early arrivals close their original countdowns')end
local waveCount=0;for j=0,CampaignCount-1 do if CampaignActorRoute[j]>=0 and CampaignActorType[j]~=11 and CampaignActorType[j]~=13 and CampaignActorType[j]~=36 then waveCount=waveCount+1 end end
assert(waveCount==32,'Eight immediate waves have exactly four ninjas each')
for lane=0,7 do assert(CampaignWaveAt[lane]>TimeNow,'Normal repeated waves retain their real next deadlines')end
Hero[0].level=46
local before=CampaignCount;FoundationChat();assert(Hero[0].level==46,'Repeated command never lowers levels');assert(CampaignCount==before and CampaignFastWaveCursor==8,'Repeated command never duplicates waves or bosses')
-- The test death is native KillUnit, with the ordinary Alpha34 death/revival flow.
local kill=KillUnit;local calls=0
function KillUnit(u)calls=calls+1;kill(u);u.dead=true end
local sasuke=Hero[1];sasuke.items={[0]={type=123,owned=true}};local kept=sasuke.items[0]
message='-sasuke-die';sender=3;FoundationChat();assert(calls==0 and FoundationAlive(sasuke),'Non-host cannot kill the test hero')
sender=0;FoundationChat();assert(calls==1 and not FoundationAlive(sasuke) and Hero[1]==sasuke)
InvasionHeroVisibility();local deadline=StoryRevive[1];assert(deadline==TimeNow+20)
FoundationChat();assert(calls==1 and StoryRevive[1]==deadline,'Repeated death command leaves corpse and deadline unchanged')
TimeNow=deadline;InvasionHeroVisibility();assert(FoundationAlive(sasuke) and not sasuke.paused and sasuke.alpha==255 and Hero[1]==sasuke and sasuke.items[0]==kept and sasuke.level==45 and sasuke.xp==1234)
KillUnit=kill
CampaignFastTestActive=false;FoundationChat();assert(calls==1 and FoundationAlive(sasuke),'Death shortcut is disabled outside explicitly started test mode')
CampaignStage=17;CampaignTransition=false;message='-village fast';FoundationChat();assert(CampaignStage==17 and not CampaignTransition,'Never interrupt the late story/clone elimination')
CampaignSasukePlayer=1;CampaignRogueAlliance()
assert(IsUnitEnemy(CampaignActor[0],1),'Independent Leaf NPCs remain hostile to rogue Sasuke in late story')
GetTriggerPlayer,GetEventPlayerChatString,GetPlayerSlotState=player,chat,slot
print('PASS: real -village fast chat/host/readiness/early cleanup/deployment, eight original wave lanes and all timed bosses/closed countdowns/idempotency; -sasuke-die host/test gating and ordinary20s same-hero revival; late story preserved (mock natives).')
