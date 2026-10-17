-- Actual generated chapter functions. Natives below model their contracts, not rendering/pathfinding.
local function numbers() return setmetatable({},{__index=function()return 0 end}) end
local function flags() return setmetatable({},{__index=function()return false end}) end
StoryStage=numbers();StoryMembers=numbers();StoryHasHuman=flags();StoryMarch=flags();StoryRetreat=flags()
StoryAdvanceAt=numbers();StoryEnemy={};StoryShop={};EnemyNext=numbers();EnemyPending=numbers();EnemyMark={};EnemyPhase=flags()
StoryRevive=numbers();StoryBotOrderAt=numbers();StoryBuyAt=numbers();StoryBought=numbers()
SandWave={};SandWaveUntil=numbers();SandWaveDX=numbers();SandWaveDY=numbers()
Hero={};Dummy={};Companion={};Controllers={};World={};Orders={};Effects=0;Destroyed=0;TimeNow=7
PLAYER_NEUTRAL_AGGRESSIVE=12;PLAYER_NEUTRAL_PASSIVE=15
PLAYER_STATE_RESOURCE_GOLD='gold';EVENT_UNIT_SELL_ITEM='sale'
local slots={[0]=true,[1]=true,[2]=true,[3]=true,[4]=true,[5]=true,[9]=true,[10]=true,[11]=true}
function GetPlayerSlotState(p)return slots[p] and 'playing' or 'open'end
local gold={};local xp={};local feedback={};local neutralBuyer={}
function GetPlayerState(p,s)return gold[p] or 0 end
function SetPlayerState(p,s,n)gold[p]=n end
function AddHeroXP(u,n,fx)u.xp=(u.xp or 0)+n end
function GetUnitCurrentOrder(u)return u.order or 0 end
function CreateQuest()return {}end
function QuestSetTitle(q,s)q.title=s end
function QuestSetDescription(q,s)q.desc=s end
function QuestSetRequired()end
function QuestSetDiscovered()end
function TriggerRegisterUnitEvent()end
function DisplayTimedTextToPlayer(p,x,y,d,s)feedback[#feedback+1]={p=p,text=s}end
function GetUnitState(u,s)return u[s] or 0 end
function SetUnitCreepGuard(u,b)assert(not b)end
function RemoveGuardPosition(u)end
function SetUnitFacing(u,a)u.facing=a end
function SetUnitVertexColor(u,r,g,b,a)u.alpha=a end
function PingMinimapEx()end
function SetUnitX(u,x)u.x=x end
function SetUnitY(u,y)u.y=y end
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
 for i=0,6 do if StoryItem[i]==id then price=StoryPrice[i] end end
 assert(price>0 and gold[p]>=price,'Purchase needs real gold')
 local given=false
 for slot=0,5 do if not buyer.items[slot] then buyer.items[slot]={type=id};given=true;break end end
 if given then gold[p]=gold[p]-price;boughtBy=buyer;StoryOnBuy();boughtBy=nil end
 return given
end
for p=0,11 do
 if slots[p] then
  Hero[p]=CreateUnit(p,p,SpawnX[p],SpawnY[p],0);Hero[p].level=3;Hero[p].points=2;HeroRole[p]=p;HeroTemplate[p]=p;HeroType[p]=p
  Controllers[p]=(p==0 or p==11) and 'human' or 'computer';gold[p]=500
 end
 BotNextCast[p]=0;StoryBotOrderAt[p]=0
end
StoryInit()
assert(StoryMembers[0]==3 and StoryMembers[1]==3 and StoryMembers[2]==0 and StoryMembers[3]==3)
assert(StoryHasHuman[0] and not StoryHasHuman[1] and StoryHasHuman[3])
assert(StoryShop[0] and StoryShop[1] and not StoryShop[2] and StoryShop[3],'Empty team must have no NPC/shop')
StoryCommand(0,'-go');assert(StoryStage[0]==1 and StoryMarch[0] and StoryStage[1]==0)
local old=Hero[0];SkillsChoose(0,1);assert(Hero[0]==old,'Cannot change hero during chapter')
Companion[3]=CreateUnit(1,123,GetUnitX(StoryEnemy[0]),GetUnitY(StoryEnemy[0]),0)
StoryTick();assert(Companion[3].last.o=='follow','Companion must stay with its distant owner')
assert(Hero[1].last.o=='attack' and Hero[1].last.target==StoryEnemy[0],'Bot must march to actual quest enemy')
StoryCommand(0,'-follow');TimeNow=10;Hero[0].x=Hero[0].x+1200;StoryTick()
assert(Hero[1].last.o=='move' and math.abs(Hero[1].last.x-Hero[0].x)<=80,'Bot must follow the human')
StoryCommand(0,'-retreat');TimeNow=13;StoryTick();assert(Hero[1].last.o=='move' and Hero[1].last.x==SpawnX[1])
StoryCommand(0,'-follow')
-- A death timer preserves hero identity and only revives after twenty seconds.
Hero[2].hp=0;TimeNow=14;StoryTick();assert(StoryRevive[2]==34)
TimeNow=33.5;StoryTick();assert(Hero[2].hp==0)
TimeNow=34;StoryTick();assert(Hero[2].revived and Hero[2].hp>0)
assert(StoryStage[1]==1 and StoryStage[3]==0,'Only computer-only teams auto-start')
-- Kill all three objective units; award once to all occupied teammates.
local before=gold[0]
for j=0,2 do StoryEnemy[j].hp=0 end
TimeNow=35;StoryTick();assert(gold[0]==before+250 and Hero[0].xp==900 and StoryAdvanceAt[0]==43)
StoryTick();assert(gold[0]==before+250,'No duplicate reward')
TimeNow=43;StoryTick();assert(StoryStage[0]==2)
for j=0,2 do StoryEnemy[j].hp=0 end
TimeNow=44;StoryTick();TimeNow=52;StoryTick();assert(StoryStage[0]==3)
-- Haku uses a sequence present in his model, a delayed visible strike and team-specific damage.
local haku=StoryEnemy[0]
Hero[0].x=GetUnitX(haku);Hero[0].y=GetUnitY(haku);Hero[1].x=GetUnitX(haku)+1000
StoryEnemyCast(0,Hero[0]);assert(haku.animationIndex==2 and EnemyMark[0] and EnemyPending[0]==53.5)
local hp=Hero[0].hp;local other=Hero[11].hp;TimeNow=53.5;StoryEnemyHit(0)
assert(Hero[0].hp==hp-120 and Hero[11].hp==other and not EnemyMark[0] and EnemyPending[0]==0)
StoryEnemy[0].hp=0;TimeNow=54;StoryTick();TimeNow=62;StoryTick();assert(StoryStage[0]==4)
local zabuza=StoryEnemy[0];zabuza.hp=4000
StoryEnemyCast(0,Hero[0]);assert(zabuza.animationIndex==5 and EnemyPhase[0] and EnemyNext[0]==67.5)
assert(StoryEnemy[1].alpha==155 and StoryEnemy[2].alpha==155)
zabuza.hp=0;StoryEnemy[1].hp=0;StoryEnemy[2].hp=0;TimeNow=64;StoryTick();assert(StoryStage[0]==5)
local finalGold=gold[0];TimeNow=65;StoryTick();assert(gold[0]==finalGold,'Final reward must be idempotent')
-- Real native purchases, armor and role stats, preserving six inventory slots.
Hero[1].items={};StoryBought[1]=0;gold[1]=500;StoryBuyAt[1]=0
for i=1,3 do TimeNow=100+i*5;StoryBuy(1)end
assert(gold[1]==70 and StoryBought[1]==3 and Hero[1].items[0].type==StoryItem[0] and Hero[1].items[1].type==StoryItem[4] and Hero[1].items[2].type==StoryItem[2])
for i=0,5 do Hero[1].items[i]={type=1}end
local saved=gold[1];TimeNow=130;StoryBuy(1);assert(gold[1]==saved,'Full inventory must not spend gold')
-- Gaara's sand crests really move, and expiry/recast/death remove their unit handles.
Hero[9].x=0;Hero[9].y=0;TimeNow=150
RosterSand(9,700,0);local crest=SandWave[27];local start=crest.x
RosterTick();assert(crest.x>start and crest.pathing==false)
local oldWave=SandWave[27];RosterSand(9,700,0);assert(oldWave.removed)
TimeNow=152;RosterTick();assert(not SandWave[27] and not SandWave[28] and not SandWave[29])
RosterSand(9,700,0);local dying=SandWave[27];Hero[9].hp=0;RosterTick();assert(dying.removed and not SandWave[27])
assert(#feedback>10,'Russian quest dialogue must be emitted')
