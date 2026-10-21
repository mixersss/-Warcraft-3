-- Real jump state machine, valid/invalid trees, range/mana/cooldown and cleanup.
local function num()return setmetatable({},{__index=function()return 0 end})end
JumpUnit={};JumpQueued={};JumpElapsed=num();JumpReadyAt=num();JumpSX=num();JumpSY=num();JumpTX=num();JumpTY=num();JumpBaseHeight=num()
function IsUnitPaused(u)return u.paused or false end
UNIT_TYPE_SNARED='snared';UNIT_TYPE_STUNNED='stunned'
local p=3
Hero[p]=CreateUnit(p,HeroType[p],SpawnX[p],SpawnY[p],0);Hero[p].hp=10000;Hero[p].mana=1000
local unit=Hero[p]
function GetDestructableTypeId(d)return d and d.type or 0 end
local widgetLife=GetWidgetLife
function GetWidgetLife(u)return u and u.hp or 0 end
function GetDestructableX(d)return d.x end
function GetDestructableY(d)return d.y end
function GetUnitFlyHeight(u)return u.flyHeight or 0 end
function SetUnitFlyHeight(u,h,speed)u.flyHeight=h end
function SetUnitPosition(u,x,y)u.x=x;u.y=y end
function IsTerrainPathable(x,y,p)return BlockAllLandings or false end
function I2R(n)return n end
function OrderId(s)return ({smart=851971,eattree=852146,attack=851983})[s] or 0 end
function GetOrderedUnit()return OrderedUnit end
function GetIssuedOrderId()return IssuedOrder end
function GetOrderTargetDestructable()return ClickTree end
function GetSpellTargetDestructable()return ClickTree end
bj_PI=math.pi
local tree={type=raw('LTlt'),x=unit.x+600,y=unit.y,hp=2500}
TimeNow=500
OrderedUnit=unit;IssuedOrder=OrderId('smart');ClickTree=tree
TreeJumpOrder();assert(JumpQueued[p]==tree and not JumpUnit[p],'Right click must queue actual tree')
TreeJumpTick();assert(JumpUnit[p]==unit and unit.pathing==false and unit.flyHeight>0 and unit.mana==950)
assert(tree.hp==2500,'Jump must not damage/consume tree')
local x=unit.x
TreeJumpTick();assert(unit.x>x,'Leap must animate movement rather than teleport only')
for i=1,20 do TreeJumpTick()end
assert(JumpUnit[p]==nil and unit.pathing and unit.flyHeight==0 and unit.last.o=='stop')
assert(TreeJumpInside(p,unit.x,unit.y) and tree.hp==2500)
local mana=unit.mana
TreeJumpQueue(p,tree);TreeJumpTick();assert(not JumpUnit[p] and unit.mana==mana,'Cooldown must not charge twice')
TimeNow=504;unit.mana=49;TreeJumpQueue(p,tree);TreeJumpTick();assert(not JumpUnit[p] and unit.mana==49)
unit.mana=1000;unit.snared=true;TreeJumpQueue(p,tree);TreeJumpTick();assert(not JumpUnit[p] and unit.mana==1000);unit.snared=false
unit.stunned=true;TreeJumpQueue(p,tree);TreeJumpTick();assert(not JumpUnit[p]);unit.stunned=false
local far={type=raw('LTlt'),x=unit.x+1200,y=unit.y,hp=2000};TreeJumpQueue(p,far);TreeJumpTick();assert(not JumpUnit[p] and unit.mana==1000)
local rock={type=raw('LRrk'),x=unit.x+100,y=unit.y,hp=1000};TreeJumpQueue(p,rock);assert(JumpQueued[p]==nil)
local dead={type=raw('LTlt'),x=unit.x+100,y=unit.y,hp=0};TreeJumpQueue(p,dead);assert(JumpQueued[p]==nil)
local foreign={type=raw('LTlt'),x=-8500,y=unit.y,hp=2000};TreeJumpQueue(p,foreign);TreeJumpTick();assert(not JumpUnit[p])
BlockAllLandings=true;TreeJumpQueue(p,tree);TreeJumpTick();assert(not JumpUnit[p] and unit.mana==1000);BlockAllLandings=false
TreeJumpQueue(p,tree);TreeJumpTick();assert(JumpUnit[p]);unit.hp=0;TreeJumpTick();assert(not JumpUnit[p] and unit.pathing and unit.flyHeight==0,'Death restores movement state')
unit.hp=10000;TimeNow=508;tree.x=unit.x+200;TreeJumpQueue(p,tree);TreeJumpTick();assert(JumpUnit[p])
local old=unit;Hero[p]=CreateUnit(p,HeroType[p],SpawnX[p],SpawnY[p],0);TreeJumpTick();assert(not JumpUnit[p] and old.pathing and old.flyHeight==0,'Hero replacement must clean original handle')
-- All four teams use their own forest, including lower-left / lower-right lanes.
for player=0,11 do assert(TreeJumpInside(player,SpawnX[player],SpawnY[player]))end
