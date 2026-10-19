-- Execute the actual expansion event handlers and per-player trigger threads.
UNIT_TYPE_MAGIC_IMMUNE='magicimmune';UNIT_TYPE_FLYING='flying';PATHING_TYPE_WALKABILITY='walk'
local effects={};local groups=0;local groupNative=CreateGroup
function CreateGroup()groups=groups+1;return groupNative()end
function AddSpecialEffect(model,x,y)local e={model=model,x=x,y=y,alive=true};effects[#effects+1]=e;return e end
function AddSpecialEffectTarget(model,u,point)local e=AddSpecialEffect(model,u.x,u.y);e.target=u;e.point=point;return e end
function DestroyEffect(e)assert(e.alive,'Expansion effect destroyed twice');e.alive=false end
function UnitRemoveAbility(u,id)u.abilities[id]=nil;return true end
function UnitRemoveBuffs(u,positive,negative)assert(not positive and negative);u.cleansed=(u.cleansed or 0)+1 end
function RMaxBJ(a,b)return math.max(a,b)end
function SetUnitX(u,x)u.x=x end
function SetUnitY(u,y)u.y=y end
function GetSpellTargetX()return AimX or 0 end
function GetSpellTargetY()return AimY or 0 end
local blocked=false
function IsTerrainPathable(x,y,t)return blocked end
local function prepare(kind)
 reset();Seconds=100;CreateHero(0,36+kind)
 local h=Hero[0];h.x=0;h.y=0;h.hp=500;h.max=1000;h.mana=50;h.maxmana=1000;h.paused=false
 for p=1,11 do Hero[p].x=4000;Hero[p].y=4000 end
 return h
end
local function cast(slot,rank,target,event)
 SpellId=HeroSkill[HeroKind[0]*4+slot];Hero[0].abilities[SpellId]=rank;SpellTarget=target;Dying=Hero[0];SpellEvent=event or EVENT_PLAYER_UNIT_SPELL_EFFECT
 OnExpansionSpell()
end
local function enemy(x,y)
 local u=CreateUnit(3,FourCC('fm00'),x or 100,y or 0,0);u.hp=2000;u.max=2000;u.mana=200;u.maxmana=200;return u
end
local function near(a,b)assert(math.abs(a-b)<.001,'actual='..a..' expected='..b)end
-- Delayed ground impact stays at its original location and ignores allies/buildings/immunity.
local h=prepare(0);local e=enemy();local ally=CreateUnit(1,FourCC('fm00'),120,0,0)
local building=enemy();building.structure=true;local immune=enemy();immune.magicimmune=true
cast(0,10,e,EVENT_PLAYER_UNIT_SPELL_CAST);assert(ExpansionTicks[0]==0)
cast(0,10,e);assert(ExpansionTicks[0]==1 and ExpansionZoneArt[0].alive)
h.x=900;Seconds=101;ExpansionTick();near(e.hp,2000)
Seconds=102;ExpansionTick();near(e.hp,1975);near(ally.hp,100);near(building.hp,2000);near(immune.hp,2000)
assert(not ExpansionZoneArt[0] and ExpansionTicks[0]==0 and ExpansionCastArt[0].x==0,'Impact stays in the marked area, not at the moving caster')
-- Mana theft is a real bounded transfer, including depleted targets/full caster mana.
h=prepare(1);e=enemy();e.mana=5;cast(0,200,e);near(e.mana,0);near(h.mana,55)
h.mana=999;e.mana=200;cast(0,200,e);near(h.mana,1000);near(e.mana,28)
local friend=Hero[1];friend.x=100;friend.y=0;local before=friend.mana;cast(0,200,friend);near(friend.mana,before)
-- Blood pact costs actual HP; it heals allied soldiers only and respects mana/HP limits.
h=prepare(2);local soldier=CreateUnit(1,FourCC('fm00'),50,0,0);soldier.hp=100;soldier.max=1000;e=enemy()
Hero[1].x=100;Hero[1].y=0;Hero[1].hp=30
cast(3,5,e);near(h.hp,425);near(h.mana,190);near(soldier.hp,220);near(Hero[1].hp,30);near(e.hp,2000)
h.hp=1;cast(3,1,e);near(h.hp,1)
-- Hunt reward comes from the real OnDeath hook even if a teammate gets the kill.
h=prepare(3);e=enemy();cast(0,10,e);assert(ExpansionPrey[0]==e and ExpansionPreyArt[0].alive)
e.hp=0;Dying=e;Killer=Hero[1];local gold=Players[0].gold;OnDeath()
near(h.hp,720);near(h.mana,105);assert(not ExpansionPrey[0] and Players[0].gold==gold,'No invented gold reward')
ExpansionOnDeath(e,Killer);near(h.hp,720)
e=enemy();cast(0,10,e);Seconds=110;e.hp=0;ExpansionOnDeath(e,Hero[1]);near(h.hp,720);assert(not ExpansionPrey[0],'Expired prey cannot pay')
-- Fire field pulses four times and never follows the hero or doubles when refreshed.
h=prepare(4);e=enemy(100,0);AimX=100;AimY=0;cast(0,10,e);h.x=1500
for i=1,4 do Seconds=100+i;ExpansionTick();near(e.hp,2000-i*9)end
assert(ExpansionTicks[0]==0 and not ExpansionZoneArt[0]);Seconds=110;ExpansionTick();near(e.hp,1964)
-- Hydra regeneration/cleanse affects only the real caster, is capped and ignores other skills/items.
h=prepare(5);e=enemy();cast(1,1,e);near(h.hp,550);assert(h.cleansed==1)
h.max=100000;h.hp=100;cast(1,1,e);near(h.hp,153);cast(0,1,e);near(h.hp,153)
-- Warcry installs one real ranked aura, refreshes without stacking and is removed on time/death/swap.
h=prepare(6);e=enemy();cast(3,50,e);assert(GetUnitAbilityLevel(h,FourCC('Fxwr'))==50 and ExpansionWarcryUntil[0]==110)
Seconds=105;cast(3,1,e);assert(GetUnitAbilityLevel(h,FourCC('Fxwr'))==1 and ExpansionWarcryUntil[0]==115)
Seconds=114;ExpansionTick();assert(GetUnitAbilityLevel(h,FourCC('Fxwr'))==1)
Seconds=115;ExpansionTick();assert(GetUnitAbilityLevel(h,FourCC('Fxwr'))==0)
cast(3,10,e);h.hp=0;Dying=h;Killer=e;OnDeath();assert(GetUnitAbilityLevel(h,FourCC('Fxwr'))==0)
h.hp=500;cast(3,10,e);CreateHero(0,0);assert(GetUnitAbilityLevel(h,FourCC('Fxwr'))==0)
-- Overload only counts native hero abilities, procs once per three casts and expires.
h=prepare(7);e=enemy();cast(0,10,e);cast(1,10,e);near(e.hp,2000);assert(ExpansionCharges[0]==2)
Dying=h;SpellId=FourCC('Fatr');h.abilities[SpellId]=1;OnExpansionSpell();assert(ExpansionCharges[0]==2)
cast(3,10,e);near(e.hp,1965);assert(ExpansionCharges[0]==0 and string.find(ExpansionCastArt[0].model,'Monsoon'))
cast(0,10,e);Seconds=130;ExpansionTick();assert(ExpansionCharges[0]==0)
-- Pull is short, ground-only and respects terrain at both sampled positions.
h=prepare(8);e=enemy(200,0);local air=enemy(200,0);air.flying=true;building=enemy(200,0);building.structure=true
cast(0,1,e);near(e.x,136);near(air.x,200);near(building.x,200)
blocked=true;cast(0,1,e);near(e.x,136);blocked=false
-- Mana pulse is allied-hero-only and cannot exceed max mana or its 200-point cap.
h=prepare(9);e=enemy();Hero[1].x=100;Hero[1].y=0;Hero[1].mana=10;Hero[1].maxmana=1000
soldier=CreateUnit(1,FourCC('fm00'),100,0,0);soldier.mana=0;soldier.maxmana=1000
cast(3,50,e);near(h.mana,250);near(Hero[1].mana,210);near(soldier.mana,0);near(e.mana,200)
-- All active spell orders are exercised independently, including healing and close-range casting.
local orders=0
for kind=36,45 do
 for entry=0,3 do
  reset();CreateHero(0,kind);h=Hero[0];h.x=0;h.y=0;h.hp=30;h.max=100
  e=Hero[3];e.x=100;e.y=0;Hero[1].x=80;Hero[1].y=0;Hero[1].hp=20
  for slot=0,3 do h.abilities[HeroSkill[kind*4+slot]]=0 end
  local raw=SpellAbility[kind*4+entry]
  if raw~=0 then
   h.abilities[raw]=1;AllowedOrders={[SpellOrder[kind*4+entry]]=true};assert(TryBotSpell(0,e),'New active ability has no usable AI cast: '..kind..'/'..entry)
   assert(h.order[1]==SpellOrder[kind*4+entry]);orders=orders+1
  end
 end
end
assert(orders==29,'All new active spell orders must actually execute')
-- Nine fallback categories fit Classic twelve-button dialogs; new portraits occupy page 6/7.
reset();ShowHeroGroups(0);assert(#Shop[0].buttons==12)
for category=7,8 do
 ShowHeroes(0,category);assert(#Shop[0].buttons==8)
 local other=ShopButton[12];EventPlayer=0;Clicked=ShopButton[0];OnShop();assert(HeroKind[0]==(category==7 and 36 or 41));assert(ShopButton[12]==other)
end
for kind=36,45 do reset();assert(SelectRosterHero(0,kind));assert(Hero[0].id==HeroType[kind])end
-- Replacement, death and expiration clean every retained visual, even after repeated casts.
local groupStart=groups
for round=1,50 do
 for kind=0,9 do
  h=prepare(kind);e=enemy();AimX=100;AimY=0
  cast(kind==7 and 0 or ExpansionSlot[kind],1,e)
  CreateHero(0,0)
 end
end
Seconds=10000;ExpansionTick()
for _,effect in ipairs(effects)do assert(not effect.alive,'A replaced hero retained a visual handle')end
assert(groups==groupStart,'A single persistent group is reused; no per-cast group allocation')
print('PASS: ten actual expansion mechanics, damage/ally/structure/immunity filters, native death rewards, bounded mana/HP, delayed/static areas, buff refresh/death/replacement cleanup, charge expiry, wall-safe pull, all 29 active bot orders, 46 choices, twelve-button fallback and 500-cast visual cleanup (mock natives).')
