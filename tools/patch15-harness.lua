-- Role assignment consumes only the existing synchronized style/race/hero draws.
for kind=0,HERO_COUNT-1 do
 for style=0,2 do
  reset();Players[0].controller=MAP_CONTROL_COMPUTER;RngQueue={style,0,kind};InitSlot(0)
  assert(#RngQueue==0 and BotStyle[0]==style)
  assert(HeroBotRole[kind]==EngineBotProfiles[kind].role)
  assert(BotTactic[0]==EngineBotProfiles[kind].tactics[style+1])
  if HeroBotRole[kind]==0 then assert(BotGearBudget[BotTactic[0]]<=25)end
  if HeroBotRole[kind]==1 then assert(BotGearBudget[BotTactic[0]]==75 and BotTierBudget[BotTactic[0]]==15)end
  local expected=BotTactic[0];ProcessHeroQueue();ProcessHeroQueue()
  assert(BotTactic[0]==expected and BotStyle[0]==style,'Creation and learning cannot reroll role strategy')
  local gear=BotGearBudget[BotTactic[0]]
  assert(gear>=15 and gear<=75 and 100-gear-BotTierBudget[BotTactic[0]]>=10,'Every profile retains troop, tier and gear income')
 end
end
-- A carry learns its damage skill first; a support starts with the relevant aura.
for _,example in ipairs({{4,0},{14,1},{6,1},{12,2}}) do
 reset();Bot[0]=true;CreateHero(0,example[1]);LearnHero(0)
 assert(GetUnitAbilityLevel(Hero[0],HeroSkill[example[1]*4+example[2]])==1)
end
-- Finite real income: every role develops ALL troop stats, tiers and equipment.
for _,kind in ipairs({0,4,11,9}) do
 for style=0,2 do
  reset();Players[0].controller=MAP_CONTROL_COMPUTER;RngQueue={style,0,kind};InitSlot(0);ProcessHeroQueue()
  for tick=1,2400 do
   Seconds=WARMUP_SECONDS+tick;AddGold(0,200);BotBuy(0)
   if Base[0].pending then FinishResearch(0)end
   local index=DesiredGear(0);local shopIndex=GearShop[index]or 0
   Hero[0].x,Hero[0].y=ShopX[shopIndex],ShopY[shopIndex]
   if GearProgress[0]>=18 then Hero[0].x,Hero[0].y=SuperX[0],SuperY[0]end
   BotShop(0)
  end
  assert(Attack[0]>10 and Armor[0]>10 and Vitality[0]>10 and Tier[0]==4 and GearProgress[0]>=6,'Each role continues every troop stat plus hero gear')
  assert(math.abs(Attack[0]-Armor[0])<=1 and math.abs(Armor[0]-Vitality[0])<=1)
 end
end
local function battle(kind)
 reset();Bot[0]=true;CreateHero(0,kind or 4);Seconds=WARMUP_SECONDS+300;AllowedOrders={}
 World={Hero[0]};Hero[0].x,Hero[0].y=0,0;Hero[0].hp,Hero[0].max=1000,1000
 for p=1,11 do Hero[p].hp=0 end
 RallyX[0],RallyY[0]=4000,-4000
end
local function bring(p,x,y,hp)
 CreateHero(p,p%HERO_COUNT)
 Hero[p].x,Hero[p].y=x,y;Hero[p].hp,Hero[p].max=hp or 1000,1000;return Hero[p]
end
battle();RunBotHero(0);assert(TeamPushUntil[0]==0 and Hero[0].order[2]==0,'Wait in center when both allies are dead')
battle();bring(1,200,0);RunBotHero(0)
assert(TeamPushUntil[0]>Seconds and Hero[0].order[2]==4000,'Two healthy heroes initiate a common push')
Bot[1]=true;RunBotHero(1);assert(Hero[1].order[2]==4000 and Hero[1].order[3]==-4000,'Teammates share the same attack window')
battle();bring(3,200,0);bring(4,400,0);bring(5,500,0);RunBotHero(0)
assert(Hero[0].order[1]=='move' and RetreatUntil[0]>Seconds,'Healthy lone hero retreats when outnumbered')
battle();bring(1,100,0);bring(2,-100,0);bring(3,200,0);local wounded=bring(4,400,0,200)
RunBotHero(0);assert(Hero[0].order[2]==wounded,'Healthy supported group focuses a wounded enemy hero')
Bot[1]=true;RunBotHero(1);assert(Hero[1].order[2]==wounded,'Nearby allies retain a shared focus target')
battle();local hidden=bring(3,200,0);hidden.hidden=true
assert(BotCombatScan(0)==nil and BotEnemyPower[0]==0,'Do not see enemies through fog')
hidden.hidden=false;hidden.invisible=true;assert(BotCombatScan(0)==nil,'Do not target an invisible enemy')
battle();Bastion[3].x,Bastion[3].y=1000,0;RunBotHero(0)
assert(BotTowerDanger[0] and Hero[0].order[1]=='move','Do not solo an enemy bastion')
battle();bring(3,100,0);bring(4,200,0);bring(5,300,0)
CastUntil[0]=Seconds+10;Hero[0].order={'channel'};local channel=Hero[0].order;RunBotHero(0)
assert(Hero[0].order==channel,'Danger checks cannot interrupt a healthy channel')
-- Team commands are scoped to teammates and yield to base defense/emergencies.
battle();Bot[0]=false;Hero[0].x,Hero[0].y=900,300;bring(1,500,0);Bot[1]=true
BotTeamCommand(0,1);RunBotHero(1);assert(Hero[1].order[2]==900 and Hero[1].order[3]==300,'Follow the human leader away from center')
assert(TeamOrder[1]==0);BotTeamCommand(3,3);assert(TeamOrder[0]==1,'Enemy cannot overwrite allied command')
Defending[0]=true;RunBotHero(1);assert(Hero[1].order[2]==4000,'Base defense overrides following')
Defending[0]=false;Hero[1].hp=100;RunBotHero(1);assert(Hero[1].order[1]=='move','Emergency retreat overrides command')
battle();Bot[0]=false;Hero[0].x,Hero[0].y=900,300;bring(1,500,0);Bot[1]=true
BotTeamCommand(0,1);Seconds=Seconds+BOT_COMMAND_SECONDS+1;TeamPushReady[0]=Seconds+100
RunBotHero(1);assert(Hero[1].order[2]==0 and Hero[1].order[3]==0,'Expired command returns to center')
-- Consumables are used via native items and bought with real gold from surplus.
battle();Hero[0].hp=400;Hero[0].inventory[0]={id=FourCC('fpH0')};RunBotHero(0)
assert(Hero[0].used==FourCC('fpH0') and Hero[0].inventory[0]==nil)
for _,distance in ipairs({100,950})do
 battle();bring(3,500,0);Hero[0].inventory[0]={id=FourCC('fsdm')}
 for n=1,5 do CreateUnit(0,ArmyType[0],distance,n*5,0)end
 RunBotHero(0)
 assert((Hero[0].used==FourCC('fsdm'))==(distance==100),'Buff scroll only when soldiers are inside its real700 range')
end
battle();Hero[0].inventory[0]={id=FourCC('fshl')}
for n=1,4 do local u=CreateUnit(0,ArmyType[0],100,n*5,0);u.hp=40 end
RunBotHero(0);assert(Hero[0].used==FourCC('fshl'),'Heal scroll supports injured troops even between fights')
battle(0);GearProgress[0]=2;GearSavings[0]=10000;Players[0].gold=10000
Hero[0].x,Hero[0].y=UtilityX[0],UtilityY[0]
UtilityShop[0]=CreateUnit(15,FourCC('futl'),UtilityX[0],UtilityY[0],0)
local gold=Players[0].gold;assert(BotBuySupplies(0))
assert(Players[0].gold==gold-800 and GearSavings[0]==9200 and HeroItem(Hero[0],FourCC('fshl')))
assert(not BotBuySupplies(0),'Do not repeatedly buy supplies')
BotSupplyAt[0]=0;Hero[0].inventory={};GearSavings[0]=GearCost[DesiredGear(0)]+799
assert(not BotBuySupplies(0),'Do not spend protected equipment or tier funds')
GearSavings[0]=10000;for slot=0,5 do Hero[0].inventory[slot]={id=9000+slot}end
assert(not BotBuySupplies(0) and Players[0].gold==gold-800,'Full inventory does not buy or destroy gear')
print('PASS: all50 role profiles and150 synchronized variants, skill priorities, finite-income all-parameter army/gear progression, group pushes, danger/tower retreat, visible shared focus, channel protection, allied commands, native consumables and paid surplus purchases (mock natives).')
