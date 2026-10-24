-- Real generated JASS; native mocks cannot establish renderer/pathfinding compatibility.
local function numbers() return setmetatable({},{__index=function()return 0 end}) end
local function flags() return setmetatable({},{__index=function()return false end}) end
StoryStage=numbers();StoryStarted=flags();StoryMembers=numbers();StoryHasHuman=flags();StoryMarch=flags();StoryRetreat=flags()
StoryAdvanceAt=numbers();StoryEnemy={};StoryShop={};EnemyNext=numbers();EnemyPending=numbers();EnemyMark={};EnemyPhase=flags()
EnemyLootRolled=flags();StoryLoot={};BotUseItemAt=numbers();EnemyBlinkAt=numbers();EnemyPrisonAt=numbers()
StoryRevive=numbers();StoryBotOrderAt=numbers();StoryBuyAt=numbers();StoryBought=numbers()
SandWave={};SandWaveUntil=numbers();SandWaveDX=numbers();SandWaveDY=numbers()
Hero={};Dummy={};Companion={};Controllers={};World={};Orders={};Effects=0;Destroyed=0;TimeNow=7
PLAYER_NEUTRAL_AGGRESSIVE=12;PLAYER_NEUTRAL_PASSIVE=15
PLAYER_STATE_GIVES_BOUNTY='bounty';PLAYER_STATE_RESOURCE_GOLD='gold';EVENT_UNIT_SELL_ITEM='sale'
local slots={[0]=true,[1]=true,[2]=true,[3]=true,[4]=true,[5]=true,[9]=true,[10]=true,[11]=true}
function GetPlayerSlotState(p)return slots[p] and 'playing' or 'open'end
local gold={};local bounty={};local feedback={};local neutralBuyer={}
function GetPlayerState(p,s)if s==PLAYER_STATE_GIVES_BOUNTY then return bounty[p] or 0 end;return gold[p] or 0 end
function SetPlayerState(p,s,n)if s==PLAYER_STATE_GIVES_BOUNTY then bounty[p]=n else gold[p]=n end end
function AddHeroXP(u,n,fx)u.xp=(u.xp or 0)+n end
function GetUnitCurrentOrder(u)return u.order or 0 end
function CreateQuest()return {}end
function QuestSetTitle(q,s)q.title=s end
function QuestSetDescription(q,s)q.desc=s end
function QuestSetRequired()end
function QuestSetDiscovered()end
function TriggerRegisterUnitEvent()end
function DestroyTrigger(t)if t then t.destroyed=true end end
function DisplayTimedTextToPlayer(p,x,y,d,s)feedback[#feedback+1]={p=p,text=s}end
function GetUnitState(u,s)return u[s] or 0 end
function SetUnitCreepGuard(u,b)assert(not b)end
function RemoveGuardPosition(u)end
function SetUnitFacing(u,a)u.facing=a end
function SetUnitVertexColor(u,r,g,b,a)u.alpha=a end
function PingMinimapEx()end
function SetUnitX(u,x)u.x=x end
function SetUnitY(u,y)u.y=y end
function PauseUnit(u,pause)u.paused=pause end
function SetUnitOwner(u,p,flag)u.owner=p end
function CreateTimerDialog(t)return {timer=t}end
function TimerDialogSetTitle(d,s)d.title=s end
function TimerDialogDisplay(d,flag)d.visible=flag end
function DestroyTimerDialog(d)d.destroyed=true end
function ReviveHero(u,x,y,fx)u.hp=u.maxLife;u.x=x;u.y=y;u.revived=true;return true end
local nativeCreate=CreateUnit
function CreateUnit(p,id,x,y,facing)
 local u=nativeCreate(p,id,x,y,facing)
 u.maxLife=10000;u.hp=10000;u.maxMana=1000;u.mana=1000;u.items={};u.abilities={};u.order=0
 return u
end
function IssuePointOrder(u,o,x,y)u.last={o=o,x=x,y=y};return true end
function IssueTargetOrder(u,o,target)u.last={o=o,target=target};return true end
function IssueImmediateOrder(u,o)u.last={o=o};return true end
function IssueNeutralTargetOrder(p,shop,o,buyer)assert(o=='neutralinteract');neutralBuyer[p]=buyer;return true end
local boughtBy=nil
function GetBuyingUnit()return boughtBy end
function IssueNeutralImmediateOrderById(p,shop,id)
 local buyer=neutralBuyer[p];assert(buyer==Hero[p],'Native shop buyer was not selected')
 local price=0
 for i=0,10 do if StoryItem[i]==id then price=StoryPrice[i] end end
 assert(price>0 and gold[p]>=price,'Purchase needs real gold')
 local given=false
 if id==raw('Nsht') or id==raw('Nsta') or id==raw('Nsch') then
  local stat=id==raw('Nsht') and 'str' or (id==raw('Nsta') and 'agi' or 'int')
  buyer[stat]=(buyer[stat]or 0)+6;given=true
 else
  for slot=0,5 do if not buyer.items[slot] then buyer.items[slot]={type=id,owned=true};given=true;break end end
 end
 if given then gold[p]=gold[p]-price;boughtBy=buyer;StoryOnBuy();boughtBy=nil end
 return given
end
GroundStatItems={}
function SetRect(r,a,b,c,d)r[1]=a;r[2]=b;r[3]=c;r[4]=d end
function EnumItemsInRect(r,filter,callback)
 for _,it in ipairs(GroundStatItems)do if it.x>=r[1]and it.x<=r[3]and it.y>=r[2]and it.y<=r[4]then EnumStatItem=it;callback()end end
 EnumStatItem=nil
end
function GetEnumItem()return EnumStatItem end
function IsItemVisible(i)return not i.hidden end
function IsVisibleToPlayer(x,y,p)return true end
function GetItemTypeId(i)return i and i.type or 0 end
function GetItemX(i)return i.x end
function GetItemY(i)return i.y end
function IsItemOwned(i)return i.owned or false end
local random={}
function GetRandomInt(a,b)local v=table.remove(random,1) or b;assert(v>=a and v<=b);return v end
function CreateItem(id,x,y)return {type=id,x=x,y=y,owned=false}end
function UnitUseItem(u,i)u.used=i;return true end
function UnitUseItemPoint(u,i,x,y)u.used=i;u.usedPoint={x,y};return true end
function UnitUseItemTarget(u,i,target)u.used=i;u.usedTarget=target;return true end
for p=0,11 do
 if slots[p] then
  Hero[p]=CreateUnit(p,p,SpawnX[p],SpawnY[p],0);Hero[p].level=3;Hero[p].points=2;HeroRole[p]=p;HeroTemplate[p]=p;HeroType[p]=p
  Controllers[p]=(p==0 or p==3 or p==11) and 'human' or 'computer';gold[p]=500
 end
 BotNextCast[p]=0;StoryBotOrderAt[p]=0
end
StoryInit()
assert(StoryMembers[0]==3 and StoryMembers[1]==3 and StoryMembers[2]==0 and StoryMembers[3]==3)
assert(StoryHasHuman[0] and StoryHasHuman[1] and StoryHasHuman[3])
for t=0,3 do assert(not StoryShop[t],'No shops exist before village invasion')end
assert(StoryMentorClock.delay==330 and StoryMentorClock.callback==StoryReleaseMentors and StoryMentorDialog==nil)
HUDTick();assert(StoryMentorDialog.visible,'Opening clock is shown from a real game heartbeat')
local populator=StoryPopulateClock
for i=0,64 do populator.callback()end
assert(populator.destroyed)
for t=0,3 do
 local count=0
 for n=0,17 do
  local u=StoryEnemy[t*18+n]
  if u then count=count+1;assert(u.x==EnemySpawnX[t*18+n] and u.y==EnemySpawnY[t*18+n])end
 end
 assert(count==(t==2 and 0 or 16),'Exactly fourteen ninjas, Haku and Zabuza per occupied forest')
end
local boss=StoryBoss[1];assert(boss==StoryEnemy[33] and boss.hp>0,'Rock Lee team boss must exist before any -go')
StoryTick();assert(StoryStage[1]==1 and not StoryStarted[1],'Enemies must exist while human selection stays open')
-- Computer-only timer and the human 30s boundary do not depend on the red slot.
Controllers[11]='computer';StoryHasHuman[3]=false
TimeNow=19.5;StoryTick();assert(not StoryStarted[3] and not StoryStarted[1])
TimeNow=20;StoryTick();assert(StoryStarted[3] and StoryMarch[3] and not StoryStarted[1])
TimeNow=29.5;StoryTick();assert(not StoryStarted[1])
-- Human Rock Lee team needs no chat command: depart automatically at 30s.
TimeNow=30;StoryTick();assert(StoryStarted[1] and StoryMarch[1])
assert(Hero[4].last.o=='attack' and Hero[4].last.target~=nil,'Neji bot must attack a real forest enemy')
assert(Hero[5].last.o=='attack' and StoryBoss[1]==boss)
-- Explicit commands and natural early departure preserve cooperative play.
StoryCommand(0,'-go');assert(StoryStarted[0] and StoryMarch[0])
local old=Hero[0];SkillsChoose(0,1);assert(Hero[0]==old,'No character changes after departure')
StoryCommand(0,'-follow');TimeNow=33;Hero[0].x=Hero[0].x+1200;StoryTick()
assert(Hero[1].last.o=='move','Follow must issue movement toward the human')
StoryCommand(0,'-retreat');TimeNow=36;StoryTick();assert(Hero[1].last.x==SpawnX[1])
StoryCommand(0,'-go')
-- Native revival is twenty seconds, including the non-red first human case.
Hero[2].hp=0;TimeNow=37;StoryTick();assert(StoryRevive[2]==57)
TimeNow=56.5;StoryTick();assert(Hero[2].hp==0)
TimeNow=57;StoryTick();assert(Hero[2].revived and Hero[2].hp>0)
-- Seven kills advance training; remaining actors retain identity, counts and orders.
local before=gold[0];local survivor=StoryEnemy[10]
for j=0,6 do StoryEnemy[j].hp=0 end
TimeNow=60;StoryTick();assert(gold[0]==before+250 and StoryAdvanceAt[0]==68)
StoryTick();assert(gold[0]==before+250)
TimeNow=68;StoryTick();assert(StoryStage[0]==2 and StoryEnemy[10]==survivor and StoryMarch[0],'Stage transition must not reset march')
for j=7,13 do StoryEnemy[j].hp=0 end
TimeNow=69;StoryTick();TimeNow=77;StoryTick();assert(StoryStage[0]==3)
local haku=StoryEnemy[14];Hero[0].x=haku.x;Hero[0].y=haku.y;Hero[1].x=haku.x+1000
StoryEnemyCast(14,Hero[0]);assert(haku.last.o=='attack' and not EnemyMark[14],'No invented ice splash')
haku.hp=0;TimeNow=79;StoryTick();TimeNow=87;StoryTick();assert(StoryStage[0]==4 and StoryEnemy[15]==StoryBoss[0],'Never recreate Zabuza')
local zabuza=StoryEnemy[15];zabuza.hp=4000;StoryEnemyCast(15,Hero[0]);assert(not StoryEnemy[16] and not StoryEnemy[17],'No invented water clones')
Hero[0].x=zabuza.x+600;Hero[0].y=zabuza.y;EnemyBlinkAt[15]=0;TimeNow=91;EnemyNext[15]=0;StoryTick();assert(zabuza.last.o=='blink' and EnemyBlinkAt[15]==96,'Source five-second blink')
-- Original mentor delay releases the stored four different mentors, not a new boss.
local dialog=StoryMentorDialog;local deadline=StoryMentorClock
TimeNow=330;deadline.callback();assert(dialog.destroyed and StoryMentorClock==nil and StoryMentorsReleased)
assert(StoryMentor[1].paused==false and StoryMentor[1].owner==3 and StoryMentor[1].last.o=='attack')
assert(StoryBoss[1]==boss)
zabuza.hp=0;StoryTick();assert(StoryStage[0]==5)
local finalGold=gold[0];StoryTick();assert(gold[0]==finalGold)
-- Loot chance boundaries and one drop per real actor (never clones).
local j=18;EnemyKind[j]=1;EnemyLootRolled[j]=false;random={56};StoryDrop(j);assert(StoryLoot[j]==nil)
EnemyLootRolled[j]=false;random={10};StoryDrop(j);assert(StoryLoot[j].type==raw('Nlra'));local dropped=StoryLoot[j]
random={1};StoryDrop(j);assert(StoryLoot[j]==dropped,'Never reroll a dead unit')
EnemyLootRolled[j]=false;random={44};StoryDrop(j);assert(StoryLoot[j].type==raw('Nlga'),'Source genin armor chance, no invented chuunin drop')
-- Bots pick up nearby drops with free inventory; full inventory never discards equipment.
Hero[4].items={};Hero[4].x=StoryLoot[j].x;Hero[4].y=StoryLoot[j].y;BotUseItemAt[4]=0
assert(StoryLootBot(4,nil) and Hero[4].last.o=='smart')
for slot=0,5 do Hero[4].items[slot]={type=1}end
assert(not StoryLootBot(4,nil))
Hero[4].items[0]={type=raw('Nlsh')};BotUseItemAt[4]=0;boss.x=Hero[4].x+100;boss.y=Hero[4].y
assert(StoryLootBot(4,boss) and Hero[4].used==Hero[4].items[0] and Hero[4].usedTarget==boss)
-- No purchases or human selection of a hidden/remote shop outside invasion.
Hero[1].items={};StoryBought[1]=0;gold[1]=500;StoryBuyAt[1]=0
StoryStarted[0]=false;TimeNow=400;StoryBuy(1)
assert(gold[1]==500 and StoryBought[1]==0,'No purchases during hero selection')
StoryStarted[0]=true;StoryStage[0]=1;TimeNow=30;StoryBuy(1)
assert(gold[1]==500 and StoryBought[1]==0,'No immediate opening purchases')
for stage=0,11 do if stage~=10 then CampaignStage=stage;TimeNow=400;StoryBuy(1);assert(gold[1]==500 and StoryBought[1]==0);assert(not StoryShopFor(1))end end
CampaignStage=12;CampaignTransition=false;StoryShopsOpen();assert(StoryShop[0] and StoryShop[1] and StoryShop[2] and StoryShop[3])
for i=1,3 do TimeNow=400+i*5;StoryBuy(1)end
assert(gold[1]==165 and StoryBought[1]==3)
StoryShopsClose();CampaignStage=13;StoryBuy(1);assert(gold[1]==165 and StoryBought[1]==3);for t=0,3 do assert(not StoryShop[t])end
CampaignStage=0
-- Sand crest cleanup remains bounded.
Hero[9].x=0;Hero[9].y=0;TimeNow=450
RosterSand(9,700,0);local crest=SandWave[27];local start=crest.x;VisualTick();assert(crest.x>start)
TimeNow=452;RosterTick();assert(not SandWave[27])
assert(#feedback>10)
