-- Real JASS continuation; native graphics/combat balance are separate engine checks.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
local alliances={};local vision={};
local shared={}
ALLIANCE_SHARED_CONTROL="control";ALLIANCE_SHARED_ADVANCED_CONTROL="advanced"
function SetPlayerAlliance(a,b,k,v)shared[a]=shared[a] or {};shared[a][b]=shared[a][b] or {};shared[a][b][k]=v end
local outcomes={};local fades={}
local fog=true;local mask=true;local filter=false;local pans={}
function IsFogEnabled()return fog end
function IsFogMaskEnabled()return mask end
function FogEnable(v)fog=v end
function FogMaskEnable(v)mask=v end
function AbortCinematicFadeBJ()end
function DisplayCineFilter(v)filter=v end
function PanCameraToTimedForPlayer(p,x,y,t)pans[p]={x=x,y=y}end
function GetPlayerAlliance(a,b,k)return shared[a] and shared[a][b] and shared[a][b][k] or false end
function SetPlayerAllianceStateAllyBJ(a,b,v)alliances[a]=alliances[a] or {};alliances[a][b]=v end
function SetPlayerAllianceStateVisionBJ(a,b,v)vision[a]=vision[a] or {};vision[a][b]=v end
function IsUnitEnemy(u,p)
 if not u or u.owner==p then return false end
 if alliances[u.owner] and alliances[u.owner][p]~=nil then return not alliances[u.owner][p]end
 return u.owner~=p and u.owner~=15
end
function ShowUnit(u,v)u.hidden=not v end
function IsUnitAlly(u,p)return not IsUnitEnemy(u,p)end
function IsUnitHidden(u)return u and u.hidden or false end
function IsUnitPaused(u)return u and u.paused or false end
function CameraSetupApplyForPlayer(flag,c,p,t)assert(c and c.position);c.lastPlayer=p end
function CreateCameraSetup()return {}end
function CameraSetupSetField(c,k,v,t)c[k or 'field']=v end
function CameraSetupSetDestPosition(c,x,y,t)c.position={x,y}end
function ResetToGameCameraForPlayer()end
function CinematicFadeBJ(kind,seconds,mask,r,g,b,a)assert(seconds>0 and string.find(mask,'Black_mask',1,true));fades[#fades+1]={kind=kind,seconds=seconds};filter=true end
function CustomVictoryBJ(p,dialog,score)outcomes[p]='win'end
function CustomDefeatBJ(p,reason)assert(#reason>0);outcomes[p]='lose'end
function GetRandomReal(a,b)return (a+b)/2 end
function GetPlayerSlotState(p)return 'playing'end
bj_CINEFADETYPE_FADEOUT=1;bj_CINEFADETYPE_FADEIN=0
function KillUnit(u)u.hp=0 end
local newUnit=CreateUnit
function CreateUnit(p,id,x,y,f)
 local u=newUnit(p,id,x,y,f);local stats=CampaignTestStats[id]
 if stats then u.maxLife=stats.hp;u.hp=stats.hp;u.maxMana=3000;u.mana=3000 end
 return u
end
function PlayMusic(path)LastCampaignMusic=path end
function StopMusic()end
MusicOn=false
local function fresh()
 CampaignStage=0;CampaignQueued=0;CampaignTransition=false;CampaignPlaced=false;CampaignFinished=false;CampaignCount=0;CampaignFinalActive=false;CampaignPrelimDone=false;CampaignPrelimWinner={}
 CampaignClone={};CampaignClonePending={};CampaignCloneKind={};CampaignCloneCastAt=setmetatable({},{__index=function()return 0 end})
 CampaignActor={};CampaignActorType={};CampaignPermanentDead={};CampaignCastAt={};CampaignMoveAt={};CampaignActorRoute={}
 setmetatable(CampaignCastAt,{__index=function()return 0 end});setmetatable(CampaignMoveAt,{__index=function()return 0 end})
 Hero={};HeroRole={};HeroType={};HeroTemplate={};Companion={};Dummy={};World={};RoleChosen={};StoryShop={};StoryStage={};StoryMembers={};StoryStarted={};StoryMarch={};StoryRetreat={};StoryRevive={}
 for t=0,3 do StoryMembers[t]=3;StoryStage[t]=8;StoryStarted[t]=true;StoryMarch[t]=true;StoryRetreat[t]=false end
 for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);Hero[p].maxLife=10000;Hero[p].hp=10000;Hero[p].level=20;Hero[p].points=20;HeroRole[p]=p;HeroType[p]=Hero[p].type;HeroTemplate[p]=p;Controllers[p]='computer';StoryRevive[p]=0;LogUntil[p]=0;LogReadyAt[p]=0;ComboLeft[p]=0;BotNextCast[p]=0;VisualChannelUntil[p]=0 end
 Controllers[0]='human';Controllers[1]='human';ExamPhase=4;TimeNow=20000;outcomes={}
end
local function enter()
 assert(CampaignTransition);local start=CampaignIntroAt
 TimeNow=start+1.5;CampaignTick();assert(CampaignPlaced)
 for n=4,16 do TimeNow=start+n*.5;CampaignTick()end;assert(not CampaignTransition)
end
local function killEnemies()
 for j=0,CampaignCount-1 do local u=CampaignActor[j];if u and IsUnitEnemy(u,CampaignLeader)then u.hp=0 end end
end
local function doDuels(expected)
 local count=0
 local finals=0
 while not CampaignTransition do
  CampaignTick()
  if CampaignFinalActive then
   assert(CampaignStage==11 and CampaignDuelA<0)
   TimeNow=CampaignDuelAt;CampaignTick();assert(CampaignDuelLive)
   local a,b,c=CampaignFinalPlayer[0],CampaignFinalPlayer[1],CampaignFinalPlayer[2]
   assert(a~=b and b~=c and a~=c)
   for _,p in ipairs({a,b,c})do
    assert(not Hero[p].paused and not CampaignEliminated[p] and Hero[p].cooldownResets>0)
    for k=0,4 do assert(BotReadyAt[p*5+k]<=TimeNow)end
   end
   assert(IsUnitEnemy(Hero[a],b)and IsUnitEnemy(Hero[b],c)and IsUnitEnemy(Hero[c],a))
   for p=0,11 do if p~=a and p~=b and p~=c then assert(CampaignEliminated[p]and Hero[p].paused,'Eliminated heroes must not re-enter the final')end end
   Hero[a].hp=0;CampaignTick();assert(CampaignFinalActive and CampaignEliminated[a]and Hero[a].paused)
   assert(CampaignNearest(b)==Hero[c]and CampaignNearest(c)==Hero[b],'Final AI targets only surviving finalists')
   Hero[b].hp=0;CampaignTick();assert(not CampaignFinalActive and CampaignChampion==c and CampaignQueued==12)
   finals=finals+1
  elseif CampaignDuelA>=0 then
   TimeNow=CampaignDuelAt;CampaignTick();assert(CampaignDuelLive)
   local a,b=CampaignDuelA,CampaignDuelB
   assert(fog and mask and not filter,'Reveal only arena terrain without global fog disabling')
   for p=0,11 do assert(CampaignArenaFog[p]and CampaignArenaFog[p].active and CampaignArenaFog[p].radius==2600)end
   for p=0,11 do assert(pans[p].x==CampaignTX[CampaignStage] and pans[p].y==CampaignTY[CampaignStage],'Every spectator camera must look at the fight')end
   assert(not Hero[a].paused and not Hero[b].paused and IsUnitEnemy(Hero[a],b))
   assert(Hero[a].cooldownResets>0 and Hero[b].cooldownResets>0)
   assert(not vision[a][b]and not vision[b][a],'Fighters must not share invisible unit sight')
   for p=0,11 do for q=0,11 do assert(not vision[p][q],'Spectators must not relay sight to a fighter')end end
   if CampaignBracket then assert(CampaignPrelimWinner[a] and CampaignPrelimWinner[b],'Only preliminary winners enter the second arena');assert(not CampaignEliminated[a]and not CampaignEliminated[b],'Losers never re-enter elimination rounds')end
   for k=0,4 do assert(BotReadyAt[a*5+k]<=TimeNow and BotReadyAt[b*5+k]<=TimeNow,'Bot cooldown bookkeeping resets too')end
   Hero[b].invisible=true;assert(CampaignNearest(a)==nil,'No scripted target through invisibility')
   local oldDummy=Dummy[math.floor(a/3)];Dummy[math.floor(a/3)]=Hero[b];assert(not SkillsBot(a),'No targeted spells through invisibility');Dummy[math.floor(a/3)]=oldDummy
   Hero[b].detected=true;assert(CampaignNearest(a)==Hero[b],'Real detection still sees the opponent')
   Hero[b].invisible=false;Hero[b].detected=false
   for p=0,11 do if p~=a and p~=b then
    assert(Hero[p].paused,'Only two fighters are active')
    local seat=p+(CampaignStage==11 and 12 or 0)
    assert(Hero[p].x==ArenaSeatX[seat]and Hero[p].y==ArenaSeatY[seat],'Spectators wait on the original upper terraces')
   end end
   local ac,bc=Controllers[a],Controllers[b];Controllers[a]='human';Controllers[b]='human'
   local hp,mana=Hero[a].hp,Hero[a].mana;Hero[a].hp=500;Hero[a].mana=100
   SpawnX[a]=Hero[a].x;SpawnY[a]=Hero[a].y
   for tick=1,5 do TimeNow=TimeNow+.5;UnitDamageTarget(Hero[b],Hero[a],40,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS);StoryTick()end
   assert(Hero[a].hp==300 and Hero[a].mana==100,'Arena must not receive the camp HP/mana heartbeat')
   Hero[a].hp=hp;Hero[a].mana=mana;Controllers[a]=ac;Controllers[b]=bc
   Hero[a].hp=0;CampaignTick();count=count+1
   assert(Hero[a].hp>0 and Hero[a].paused,'Loser remains available for later story')
  end
  assert(count<30,'Duel bracket must terminate')
 end
 assert(count==expected,'Unexpected number of duels: '..count)
 assert(finals==(CampaignBracket and 1 or 0),'Exactly one three-way final after elimination rounds')
end
fresh();CampaignTick();assert(CampaignTransition and CampaignQueued==9)
enter();assert(fog and mask and not filter);for p=0,11 do assert(pans[p].x==CampaignTX[9] and pans[p].y==CampaignTY[9])end
assert(CampaignStage==9 and CampaignSasukePlayer==1 and CampaignNarutoPlayer==0)
doDuels(6);assert(CampaignQueued==10)
enter();assert(fog and mask and not filter and not CampaignArenaView,'Restore exploration after arena');assert(CampaignStage==10 and CampaignCount==20 and CampaignEndAt-TimeNow==150)
assert(vision[0][1]and StoryShop[0]and VillageFountain[0],'City restores shared vision and opens source supply')
assert(StoryShop[0].x==16192 and StoryShop[0].y==-16256 and VillageFountain[0].x==16128 and VillageFountain[0].y==-15744,'Source corner beside arena')
for p=0,11 do
 local target=CampaignNearest(p);assert(target and CampaignActorType[CampaignJiraiya]==18)
 CampaignBot(p,target);assert(Hero[p].last.o=='attack','Every bot participates in the barrel search')
end
local trainingXP=Hero[0].xp or 0;CampaignActor[CampaignJiraiya].hp=0;CampaignTick();assert(CampaignFound and not CampaignDialog.visible and Hero[0].xp==trainingXP+2200)
TimeNow=CampaignTrainingAt;CampaignTick();assert(CampaignQueued==11)
enter();doDuels(3);assert(CampaignQueued==12)
enter();assert(CampaignStage==12 and CampaignEndAt-TimeNow==1500)
local counts={};for j=0,CampaignCount-1 do local k=CampaignActorType[j];counts[k]=(counts[k]or 0)+1 end
assert(counts[17]==140 and counts[34]==102 and counts[32]==6,'All 248 source village ninja/medic placements must exist')
for t=0,3 do assert(StoryShop[t],'All four original village shops exist during invasion')end
local waveStart=TimeNow;local initial=CampaignCount
for _,p in ipairs({9,10,11})do assert(math.abs(Hero[p].x+2336)<1 and math.abs(Hero[p].y+11840)<=32,'Sand starts at the source enemy camp')end
TimeNow=waveStart+30;CampaignTick();assert(CampaignCount==initial+12,'Four immediate 30-second streams x three')
TimeNow=waveStart+45;CampaignTick();assert(CampaignCount==initial+18,'Sand first wave plus delayed Sound')
TimeNow=waveStart+60;CampaignTick();assert(CampaignCount==initial+33)
TimeNow=waveStart+75;CampaignTick();assert(CampaignCount==initial+39)
for j=initial,CampaignCount-1 do local u=CampaignActor[j];assert(not u.paused and u.last.o=='attack' and CampaignActorRoute[j]>=0,'Every invader is active and marching to its source waypoint')end
TimeNow=CampaignKabutoAt;CampaignTick();assert(CampaignVillageKabuto and CampaignVillageKabuto.owner==15)
TimeNow=CampaignJiraiyaAt;CampaignTick();local jiraiyaPresent=false;for j=0,CampaignCount-1 do if CampaignActorType[j]==33 then jiraiyaPresent=true end end;assert(jiraiyaPresent,'Jiraiya joins the village defense')
TimeNow=CampaignSnakeAt;CampaignTick();assert(CampaignVillageSnake and CampaignVillageSnake.owner==15 and CampaignSnakeGoneAt-TimeNow==300)
TimeNow=CampaignOroAt;CampaignTick();assert(CampaignVillageOro.owner==15 and not CampaignVillageOro.paused)
CampaignActor[0].hp=0;CampaignTick();assert(CampaignQueued==13)
enter();for t=0,3 do assert(not StoryShop[t],'Shops are removed after invasion')end;assert(CampaignStage==13 and CampaignEndAt-TimeNow==360 and CampaignActor[0].maxLife==100000 and CampaignActor[2].maxLife==318750)
TimeNow=CampaignEndAt;CampaignTick();assert(CampaignQueued==14)
enter();assert(CampaignStage==14 and CampaignEndAt-TimeNow==360 and Hero[1].hidden and Hero[1].paused)
assert(not CampaignNearest(0) or CampaignNearest(0)~=Hero[1],'Hidden sealed Sasuke cannot distract allies from Sound Five')
local sakonSlot=nil
for j=0,CampaignCount-1 do if CampaignActorType[j]==7 then sakonSlot=j end end
assert(sakonSlot and CampaignWatcher[sakonSlot].threshold==15000,'Original Sakon split threshold')
Caster=CampaignActor[sakonSlot];Caster.hp=14999;NativeCurrentTrigger=CampaignWatcher[sakonSlot]
local beforeSplit=CampaignCount;CampaignSakonSplit();assert(CampaignCount==beforeSplit+1 and CampaignActorType[CampaignCount-1]==39,'Source Ukon is adopted into objective and cleanup tracking')
killEnemies();CampaignTick();assert(CampaignQueued==15)
enter();assert(CampaignStage==15 and CampaignEndAt-TimeNow==240 and not Hero[1].hidden and not Hero[1].paused and IsUnitEnemy(Hero[0],1) and Hero[1].level==60)
assert(CampaignSasuke==Hero[1],'The selected human keeps Sasuke instead of being replaced by an NPC')
Hero[1].hp=0;CampaignTick();assert(CampaignQueued==16)
enter();assert(CampaignStage==16 and not Hero[0].paused and not Hero[1].paused and Hero[2].paused)
Hero[1].hp=0;CampaignTick();assert(CampaignQueued==17)
enter();assert(CampaignStage==17 and CampaignCount==22 and Hero[1].hidden)
-- Sakura's bot walks up to the obstacle and uses her real Okasho, never attacks invulnerability.
Hero[2].abilities[raw('R204')]=1
CampaignBot(2,nil);assert(Hero[2].last.o=='move')
Hero[2].abilities[raw('R204')]=nil;Hero[2].level=20;Hero[2].points=0
Hero[2].x=CampaignTX[17]-100;Hero[2].y=CampaignTY[17];CampaignBot(2,nil);assert(Hero[2].last.o=='attack','Low-level Sakura must break the entrance without an unlearnable ultimate')
-- Sakura's real existing Okasho spell destroys nearby protected boulders.
Caster=Hero[2];Spell=raw('R204');Target=nil;Hero[2].x=CampaignTX[17];Hero[2].y=CampaignTY[17];Hero[2].abilities[Spell]=1
SkillsEffect();assert(CampaignActor[0].hp==0 and CampaignActor[1].hp==0)
local cloneCount=0
for p=0,11 do if CampaignClonePending[p] then cloneCount=cloneCount+1;assert(CampaignClone[p].level==60,'Source clone level 60');assert(CampaignNearest(p)==CampaignClone[p]);CampaignBot(p,CampaignClone[p]);assert(Hero[p].last.target==CampaignClone[p])end end
assert(cloneCount==8,'Eight parallel clone rooms, no sequential teleport of every hero')
local cloneX,cloneY=Hero[3].x,Hero[3].y
killEnemies();CampaignTick();assert(not CampaignTransition and CampaignStage==17,'Keep the cave entrance open while individual clone fights continue')
assert(CampaignClonePending[3] and Hero[3].x==cloneX and Hero[3].y==cloneY,'Other clone fights are not interrupted')
for p=0,11 do if CampaignClonePending[p] then CampaignClone[p].hp=0 end end
CampaignClonesTick();for p=0,11 do assert(not CampaignClonePending[p]);assert(not CampaignClone[p])end
for p=0,11 do if p~=1 and Hero[p] and not CampaignPermanentDead[p] then assert(Hero[p].x==CampaignX[17] or p==0 or p==2 or p==6,'Clone winners return to cave entrance')end end
CampaignTick();assert(CampaignTransition and CampaignQueued==26);enter()
assert(CampaignStage==26 and CampaignActor[0].owner==1 and Hero[1].hidden,'Cave progression is preserved after regrouping; no boss is inserted into a clone duel')
StoryCommand(1,'-kabuto');StoryCommand(1,'-kabutooff');assert(not CampaignKabutoAI)
CampaignActor[0].hp=0;CampaignTick();assert(CampaignQueued==27)
enter();killEnemies();CampaignTick();assert(CampaignQueued==28)
enter();killEnemies();CampaignTick();assert(CampaignQueued==29)
enter();assert(CampaignStage==29 and CampaignSasuke==Hero[1] and not Hero[1].hidden)
Hero[1].hp=0;CampaignTick();assert(CampaignQueued==30)
enter();assert(CampaignStage==30)
TimeNow=CampaignStartAt+12;CampaignTick();assert(CampaignFinished and outcomes[0]=='win' and outcomes[1]=='lose')
-- The alternate final outcome preserves Sasuke's winning side.
fresh();CampaignBindRoles();CampaignClock=CreateTimer();CampaignDialog=CreateTimerDialog(CampaignClock);CampaignStage=29;CampaignSasuke=Hero[1];CampaignNaruto=Hero[0];Hero[0].hp=0
CampaignTick();assert(not CampaignFinished and CampaignPermanentDead[0] and Hero[0].hp==0,'Other survivors continue after Naruto dies')
for p=2,11 do Hero[p].hp=0 end
CampaignTick();assert(CampaignFinished and outcomes[1]=='win' and outcomes[0]=='lose','Defeat only after all allied survivors are dead')
-- Unique selectable story roles: swap a pending/default character, reject an already confirmed human role.
fresh();for t=0,3 do StoryStarted[t]=false end;Hero[0].xp=300;Hero[1].xp=300
SkillsChoose(0,1);assert(HeroRole[0]==1 and HeroRole[1]==0 and RoleChosen[0])
RoleChosen[1]=true;local before=HeroRole[0];SkillsChoose(0,0);assert(HeroRole[0]==before,'Cannot steal a confirmed human story role')
-- Public arena visibility restores the exact previous options, including a mixed fog/mask state.
CampaignArenaVisibility(0);fog=true;mask=false
CampaignArenaVisibility(9);assert(fog and mask)
CampaignArenaVisibility(9);CampaignArenaVisibility(11);assert(fog and mask)
CampaignArenaVisibility(10);assert(fog and not mask and not CampaignArenaView)
fog=true;mask=true
-- Exercise actual chat dispatch, safe startup/host gates, early-chapter cleanup and re-entry.
do
 fresh();CampaignArenaVisibility(0);fog=true;mask=true
 StoryPopulateCursor=64;SpawnClock=nil;SkillDataReady=true
 local timersPaused, timersDestroyed=PauseTimer,DestroyTimer
 function PauseTimer(t)t.paused=true end
 function DestroyTimer(t)t.destroyed=true end
 ChatPlayer=0;ChatText='-arena 3';FoundationChat();assert(not CampaignTransition,'Invalid suffix must not jump')
 ChatPlayer=1;ChatText='-arena 2';FoundationChat();assert(not CampaignTransition,'Only first occupied human may move the whole game')
 ChatPlayer=0;SpawnClock=CreateTimer();FoundationChat();assert(not CampaignTransition,'Wait for hero creation before testing')
 SpawnClock=nil
 StoryPopulateClock=CreateTimer();StoryMentorClock=CreateTimer();StoryMentorDialog=CreateTimerDialog(StoryMentorClock)
 ExamPhase=3;ExamClock=CreateTimer();ExamDialog=CreateTimerDialog(ExamClock);ExamRect=Rect(-1,-1,1,1);ExamAnswers={}
 PhaseClock=CreateTimer();PhaseDialog=CreateTimerDialog(PhaseClock)
 local producer,mentor,exam=StoryPopulateClock,StoryMentorClock,ExamClock
 local answer,region=ExamAnswers,ExamRect
 StoryEnemy[0]=CreateUnit(12,raw('re01'),0,0,0);ExamEnemy[0]=CreateUnit(12,raw('re06'),0,0,0)
 local firstEnemy,forestEnemy=StoryEnemy[0],ExamEnemy[0]
 local identity=Hero[0];local level=Hero[0].level;local gold=GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)
 ChatText='-arena 2';FoundationChat()
 assert(CampaignTransition and CampaignQueued==11 and ExamPhase==4)
 for t=0,3 do assert(StoryStage[t]==8 and StoryAdvanceAt[t]==0 and StoryStarted[t],'No skipped quest can complete during fade')end
 TimeNow=TimeNow+.5;StoryTick();assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==gold,'No reward during transition heartbeat')
 assert(producer.paused and producer.destroyed and mentor.paused and mentor.destroyed and exam.paused and exam.destroyed)
 assert(StoryPopulateClock==nil and StoryMentorClock==nil and StoryMentorDialog==nil and ExamClock==nil and ExamDialog==nil)
 assert(answer.destroyed and region.removed and firstEnemy.removed and forestEnemy.removed)
 assert(Hero[0]==identity and Hero[0].level==level and GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==gold,'No hero reroll or skipped quest reward')
 local clock,dialog,scratch=CampaignClock,CampaignDialog,CampaignScratch
 ChatText='-arena 1';FoundationChat();assert(CampaignQueued==11,'An in-progress transition cannot be overwritten')
 enter();assert(CampaignStage==11 and CampaignDuelA>=0 and fog and mask and not filter)
 ChatText='-arena';FoundationChat();assert(CampaignQueued==9 and CampaignTransition)
 assert(CampaignClock==clock and CampaignDialog==dialog and CampaignScratch==scratch,'Repeated shortcut reuses campaign handles')
 enter();assert(CampaignStage==9 and CampaignDuelA>=0)
 CampaignStage=12;ChatText='-arena 2';FoundationChat();assert(not CampaignTransition,'Do not rewind active invasion/source NPC timers')
 CampaignStage=9;Controllers[0]='computer';ChatPlayer=1;FoundationChat();assert(CampaignTransition and CampaignQueued==11,'Support non-red first human')
 enter();CampaignArenaVisibility(0);fog=true;mask=true
 fresh();StoryPopulateCursor=64;SpawnClock=nil;ChatPlayer=0;ChatText='-village';FoundationChat();assert(CampaignTransition and CampaignQueued==12)
 enter();assert(CampaignStage==12 and Hero[9].x==-2336 and StoryShop[0] and VillageFountain[0],'The real village shortcut builds the full invasion')
 PauseTimer,DestroyTimer=timersPaused,timersDestroyed
end

assert(#fades>0,'Every stage transition must include a real cinematic fade')
print('PASS: actual -arena chat dispatch, startup/host/transition guards, early-chapter producer cleanup, repeated and non-red host jumps; public arena fog/mask and spectator camera, transition filter release and exact exploration restoration; full continuation through 22 source-linked phases, six preliminary and three elimination duels and one three-way final, shared barrel search/training, exact chapter deadlines, invasion streams/secondary arrivals, human Sasuke betrayal/chase/Kabuto control/final outcomes, Sakura boulders, eight clone scenes, unique role selection and real transition calls (mock natives).')
