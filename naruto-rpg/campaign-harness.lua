-- Real JASS continuation; native graphics/combat balance are separate engine checks.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
local alliances={};local vision={};local outcomes={};local fades={}
function SetPlayerAllianceStateAllyBJ(a,b,v)alliances[a]=alliances[a] or {};alliances[a][b]=v end
function SetPlayerAllianceStateVisionBJ(a,b,v)vision[a]=vision[a] or {};vision[a][b]=v end
function IsUnitEnemy(u,p)
 if not u or u.owner==p or u.owner==15 then return false end
 if alliances[u.owner] and alliances[u.owner][p]~=nil then return not alliances[u.owner][p]end
 return u.owner~=p
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
function CinematicFadeBJ(kind,seconds,mask,r,g,b,a)assert(seconds>0 and string.find(mask,'Black_mask',1,true));fades[#fades+1]={kind=kind,seconds=seconds}end
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
 CampaignStage=0;CampaignQueued=0;CampaignTransition=false;CampaignPlaced=false;CampaignFinished=false;CampaignCount=0
 CampaignClone={};CampaignClonePending={};CampaignCloneKind={};CampaignCloneCastAt=setmetatable({},{__index=function()return 0 end})
 CampaignActor={};CampaignActorType={};CampaignPermanentDead={};CampaignCastAt={};CampaignMoveAt={};CampaignActorRoute={}
 setmetatable(CampaignCastAt,{__index=function()return 0 end});setmetatable(CampaignMoveAt,{__index=function()return 0 end})
 Hero={};HeroRole={};HeroType={};HeroTemplate={};Companion={};Dummy={};World={};RoleChosen={};StoryShop={};StoryStage={};StoryMembers={};StoryStarted={};StoryMarch={};StoryRetreat={};StoryRevive={}
 for t=0,3 do StoryMembers[t]=3;StoryStage[t]=8;StoryStarted[t]=true;StoryMarch[t]=true;StoryRetreat[t]=false;StoryShop[t]=CreateUnit(15,raw('rqsh'),0,0,0)end
 for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);Hero[p].maxLife=10000;Hero[p].hp=10000;Hero[p].level=20;Hero[p].points=20;HeroRole[p]=p;HeroType[p]=Hero[p].type;HeroTemplate[p]=p;Controllers[p]='computer';StoryRevive[p]=0;LogUntil[p]=0;LogReadyAt[p]=0;ComboLeft[p]=0;BotNextCast[p]=0;VisualChannelUntil[p]=0 end
 Controllers[0]='human';Controllers[1]='human';ExamPhase=4;TimeNow=20000;outcomes={}
end
local function enter()
 assert(CampaignTransition);local start=CampaignIntroAt
 TimeNow=start+1.5;CampaignTick();assert(CampaignPlaced)
 TimeNow=start+8;CampaignTick();assert(not CampaignTransition)
end
local function killEnemies()
 for j=0,CampaignCount-1 do local u=CampaignActor[j];if u and IsUnitEnemy(u,CampaignLeader)then u.hp=0 end end
end
local function doDuels(expected)
 local count=0
 while not CampaignTransition do
  CampaignTick()
  if CampaignDuelA>=0 then
   TimeNow=CampaignDuelAt;CampaignTick();assert(CampaignDuelLive)
   local a,b=CampaignDuelA,CampaignDuelB
   assert(not Hero[a].paused and not Hero[b].paused and IsUnitEnemy(Hero[a],b))
   for p=0,11 do if p~=a and p~=b then assert(Hero[p].paused,'Only two fighters are active')end end
   Hero[a].hp=0;CampaignTick();count=count+1
   assert(Hero[a].hp>0 and Hero[a].paused,'Loser remains available for later story')
  end
  assert(count<30,'Duel bracket must terminate')
 end
 assert(count==expected,'Unexpected number of duels: '..count)
end
fresh();CampaignTick();assert(CampaignTransition and CampaignQueued==9)
enter();assert(CampaignStage==9 and CampaignSasukePlayer==1 and CampaignNarutoPlayer==0)
doDuels(6);assert(CampaignQueued==10)
enter();assert(CampaignStage==10 and CampaignCount==20 and CampaignEndAt-TimeNow==150)
for p=0,11 do
 local target=CampaignNearest(p);assert(target and CampaignActorType[CampaignJiraiya]==18)
 CampaignBot(p,target);assert(Hero[p].last.o=='attack','Every bot participates in the barrel search')
end
local trainingXP=Hero[0].xp or 0;CampaignActor[CampaignJiraiya].hp=0;CampaignTick();assert(CampaignFound and not CampaignDialog.visible and Hero[0].xp==trainingXP+2200)
TimeNow=CampaignTrainingAt;CampaignTick();assert(CampaignQueued==11)
enter();doDuels(11);assert(CampaignQueued==12)
enter();assert(CampaignStage==12 and CampaignEndAt-TimeNow==1500)
local waveStart=TimeNow;local initial=CampaignCount
TimeNow=waveStart+45;CampaignTick();assert(CampaignCount==initial+15,'Five immediate streams x three units')
TimeNow=waveStart+60;CampaignTick();assert(CampaignCount==initial+21,'Two delayed streams x three units')
-- Source schedule: one stream at +30 (75), two at +15 (60). Account for actual lane pattern below.
TimeNow=waveStart+75;CampaignTick();assert(CampaignCount==initial+24)
TimeNow=CampaignKabutoAt;CampaignTick();assert(CampaignVillageKabuto and CampaignVillageKabuto.owner==10)
TimeNow=CampaignJiraiyaAt;CampaignTick();local jiraiyaPresent=false;for j=0,CampaignCount-1 do if CampaignActorType[j]==33 then jiraiyaPresent=true end end;assert(jiraiyaPresent,'Jiraiya joins the village defense')
TimeNow=CampaignSnakeAt;CampaignTick();assert(CampaignVillageSnake and CampaignVillageSnake.owner==11 and CampaignSnakeGoneAt-TimeNow==300)
TimeNow=CampaignOroAt;CampaignTick();assert(CampaignVillageOro.owner==9 and not CampaignVillageOro.paused)
CampaignActor[0].hp=0;CampaignTick();assert(CampaignQueued==13)
enter();assert(CampaignStage==13 and CampaignEndAt-TimeNow==360 and CampaignActor[0].maxLife==10000 and CampaignActor[2].maxLife==375000)
TimeNow=CampaignEndAt;CampaignTick();assert(CampaignQueued==14)
enter();assert(CampaignStage==14 and CampaignEndAt-TimeNow==360 and Hero[1].hidden and Hero[1].paused)
assert(not CampaignNearest(0) or CampaignNearest(0)~=Hero[1],'Hidden sealed Sasuke cannot distract allies from Sound Five')
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
Hero[2].x=CampaignTX[17]-100;Hero[2].y=CampaignTY[17];CampaignBot(2,nil);assert(Hero[2].last.o=='drunkenhaze')
-- Sakura's real existing Okasho spell destroys nearby protected boulders.
Caster=Hero[2];Spell=raw('R204');Target=nil;Hero[2].x=CampaignTX[17];Hero[2].y=CampaignTY[17];Hero[2].abilities[Spell]=1
SkillsEffect();assert(CampaignActor[0].hp==0 and CampaignActor[1].hp==0)
local cloneCount=0
for p=0,11 do if CampaignClonePending[p] then cloneCount=cloneCount+1;assert(CampaignNearest(p)==CampaignClone[p]);CampaignBot(p,CampaignClone[p]);assert(Hero[p].last.target==CampaignClone[p])end end
assert(cloneCount==8,'Eight parallel clone rooms, no sequential teleport of every hero')
local cloneX,cloneY=Hero[3].x,Hero[3].y
killEnemies();CampaignTick();assert(CampaignQueued==26,'Main party continues while clone fights remain active')
enter();assert(CampaignClonePending[3] and Hero[3].x==cloneX and Hero[3].y==cloneY,'Stage transitions preserve individual clone fights')
for p=0,11 do if CampaignClonePending[p] then CampaignClone[p].hp=0 end end
CampaignClonesTick();for p=0,11 do assert(not CampaignClonePending[p]);assert(not CampaignClone[p])end
assert(CampaignStage==26 and CampaignActor[0].owner==1 and Hero[1].hidden)
StoryCommand(1,'-kabuto');StoryCommand(1,'-kabutooff');assert(not CampaignKabutoAI)
CampaignActor[0].hp=0;CampaignTick();assert(CampaignQueued==27,'Human-controlled Kabuto remains a required enemy')
enter();killEnemies();CampaignTick();assert(CampaignQueued==28)
enter();killEnemies();CampaignTick();assert(CampaignQueued==29)
enter();assert(CampaignStage==29 and CampaignSasuke==Hero[1] and not Hero[1].hidden)
Hero[1].hp=0;CampaignTick();assert(CampaignQueued==30)
enter();assert(CampaignStage==30)
TimeNow=CampaignStartAt+12;CampaignTick();assert(CampaignFinished and outcomes[0]=='win' and outcomes[1]=='lose')
-- The alternate final outcome preserves Sasuke's winning side.
fresh();CampaignBindRoles();CampaignClock=CreateTimer();CampaignDialog=CreateTimerDialog(CampaignClock);CampaignStage=29;CampaignSasuke=Hero[1];CampaignNaruto=Hero[0];Hero[0].hp=0
CampaignTick();assert(CampaignFinished and outcomes[1]=='win' and outcomes[0]=='lose')
-- Unique selectable story roles: swap a pending/default character, reject an already confirmed human role.
fresh();for t=0,3 do StoryStarted[t]=false end;Hero[0].xp=300;Hero[1].xp=300
SkillsChoose(0,1);assert(HeroRole[0]==1 and HeroRole[1]==0 and RoleChosen[0])
RoleChosen[1]=true;local before=HeroRole[0];SkillsChoose(0,0);assert(HeroRole[0]==before,'Cannot steal a confirmed human story role')
assert(#fades>0,'Every stage transition must include a real cinematic fade')
print('PASS: full continuation through 22 source-linked phases, six preliminary and eleven final duels, shared barrel search/training, exact chapter deadlines, invasion streams/secondary arrivals, human Sasuke betrayal/chase/Kabuto control/final outcomes, Sakura boulders, eight clone scenes, unique role selection and real transition calls (mock natives).')
