-- Actual replacement handlers; native combat effects are checked in emitted object data.
function UnitAddType(u,t)u[t]=true;return true end
function UnitApplyTimedLife(u,buff,duration)u.timedlife=duration;u.timedbuff=buff end
local function near(a,b)assert(math.abs(a-b)<.002,'actual='..a..' expected='..b)end
local function prep(kind)
 reset();Seconds=100;CreateHero(0,46+kind)
 local h=Hero[0];h.x=0;h.y=0;h.hp=500;h.max=1000;h.mana=500;h.maxmana=1000
 for p=1,11 do Hero[p].x=5000;Hero[p].y=5000 end
 for slot=0,3 do h.abilities[HeroSkill[HeroKind[0]*4+slot]]=0 end
 return h
end
local function cast(slot,rank,x,y,event)
 local h=Hero[0];Dying=h;SpellId=HeroSkill[HeroKind[0]*4+slot];h.abilities[SpellId]=rank;AimX=x or 0;AimY=y or 0;SpellTarget=nil;SpellEvent=event or EVENT_PLAYER_UNIT_SPELL_EFFECT;OnCreativeSpell()
end
local function enemy(x,y)
 local u=CreateUnit(3,FourCC('fm00'),x or 100,y or 0,0);u.hp=5000;u.max=5000;return u
end
-- Every count milestone uses the real spell handler, with compact terrain-safe spawns.
local h=prep(0);local first=0
for _,slot in ipairs({0,1,3}) do
 local family=slot==3 and 2 or slot
 local cap=slot==3 and 50 or 200
 for _,rank in ipairs({1,9,10,19,20,49,50,99,100,199,200}) do
  if rank<=cap then
   first=#World;cast(slot,rank)
   local count=(slot==3 and 1 or 2)+math.floor(rank/10)
   assert(#World==first+count,'Rank milestone must add one actual pet every10 ranks')
   local raw=FourCC(string.format('k%d%02x',family,rank-1))
   for i=first+1,#World do local u=World[i]
    assert(u.id==raw and u.summoned and u.owner==0 and u.timedlife==(slot==3 and 45 or 35))
    assert(math.abs(u.x-h.x)<=300 and math.abs(u.y-h.y)<=200,'Compact formation')
   end
  end
 end
end
cast(2,200);assert(GetUnitAbilityLevel(h,FourCC('Csum'))==200 and CreativeBuffUntil[0]==110)
Seconds=109;CreativeTick();assert(GetUnitAbilityLevel(h,FourCC('Csum'))==200)
Seconds=110;CreativeTick();assert(GetUnitAbilityLevel(h,FourCC('Csum'))==0)
-- Ranged/melee, undead/mechanical troops and pets all get the SAME native lifesteal.
h=prep(2);h.abilities[HeroSkill[48*4]]=200
local melee=CreateUnit(1,FourCC('fm00'),100,0,0);local ranged=CreateUnit(1,FourCC('fm01'),120,0,0);ranged.ranged=true
local mechanical=CreateUnit(1,FourCC('fm02'),140,0,0);mechanical.mechanical=true;mechanical.undead=true
local pet=CreateUnit(1,FourCC('k000'),160,0,0);pet.summoned=true
local illusion=CreateUnit(1,FourCC('k000'),180,0,0);illusion.summoned=true;illusion.illusion=true
local ward=CreateUnit(1,FourCC('oeye'),200,0,0);ward.summoned=true;ward.defaultspeed=0
local foe=enemy();CreativeTick()
for _,u in ipairs({melee,ranged,mechanical,pet})do assert(GetUnitAbilityLevel(u,FourCC('Clif'))==380,'All real troops have38% native attack lifesteal')end
assert(GetUnitAbilityLevel(foe,FourCC('Clif'))==0 and GetUnitAbilityLevel(illusion,FourCC('Clif'))==0 and GetUnitAbilityLevel(ward,FourCC('Clif'))==0)
cast(3,50);CreativeTick();assert(GetUnitAbilityLevel(ranged,FourCC('Clif'))==480,'Banner raises total to capped48%')
Seconds=110;CreativeTick();assert(GetUnitAbilityLevel(ranged,FourCC('Clif'))==380 and GetUnitAbilityLevel(h,FourCC('Cuba'))==0)
h.x=2000;CreativeTick();assert(GetUnitAbilityLevel(ranged,FourCC('Clif'))==0,'Leaving the aura removes its native helper')
h.x=0;CreativeTick();h.hp=0;CreativeTick();assert(GetUnitAbilityLevel(ranged,FourCC('Clif'))==0,'Dead sources do not heal or leave permanent lifesteal')
-- Flat army regen and burst heal respect alliance, hero/building exclusions and max HP.
h=prep(2);h.abilities[HeroSkill[48*4+2]]=200
local soldier=CreateUnit(1,FourCC('fm00'),100,0,0);soldier.max=1000;soldier.hp=500;foe=enemy()
Hero[1].x=100;Hero[1].y=0;Hero[1].hp=20;Hero[1].max=1000
CreativeTick();near(soldier.hp,510);near(Hero[1].hp,20);near(foe.hp,5000)
cast(3,1);near(soldier.hp,610);near(Hero[1].hp,20)
-- Archer heal fires only on EFFECT, rain has exactly4 bounded enemy-only pulses.
h=prep(1);cast(2,200,nil,nil,EVENT_PLAYER_UNIT_SPELL_CAST);near(h.hp,500)
cast(2,200);near(h.hp,550)
foe=enemy(100,0);local structure=enemy(100,0);structure.structure=true
cast(3,1,100,0);for n=1,4 do Seconds=100+n;CreativeTick()end
near(foe.hp,5000-4*51);near(structure.hp,5000);assert(CreativeRainTicks[0]==0)
Seconds=105;CreativeTick();near(foe.hp,4796)
-- Rogue cleanses only negative buffs, six moving pulses, expiry/removal of attack boost.
h=prep(3);cast(1,1);assert(h.cleansed==1)
foe=enemy(100,0);cast(3,1);assert(GetUnitAbilityLevel(h,FourCC('Crag'))==1)
for n=1,6 do Seconds=100+n;CreativeTick()end
near(foe.hp,5000-6*37);assert(GetUnitAbilityLevel(h,FourCC('Crag'))==0)
cast(3,50);h.hp=0;CreativeTick();assert(CreativeBladeTicks[0]==0 and GetUnitAbilityLevel(h,FourCC('Crag'))==0)
-- New items are paid native neutral purchases; item aura follows the wearer/inventory.
h=prep(0);local shop=CreateUnit(15,FourCC('futl'),0,0,0);shop.structure=true;Players[0].selection=h;Players[0].gold=3680
assert(IssueNeutralTargetOrder(0,shop,'neutralinteract',h))
assert(IssueNeutralImmediateOrderById(0,shop,FourCC('fvlm')));assert(Players[0].gold==480)
assert(IssueNeutralImmediateOrderById(0,shop,FourCC('ftot')));assert(Players[0].gold==0)
soldier=CreateUnit(1,FourCC('fm00'),100,0,0);CreativeTick();assert(GetUnitAbilityLevel(soldier,FourCC('Clif'))==150,'Item aura is exactly15%')
h.inventory[0]=nil;CreativeTick();assert(GetUnitAbilityLevel(soldier,FourCC('Clif'))==0,'Dropping the source removes the army aura')
-- Pet kill gold is real income, not native bounty duplication, and does not grant extra scripted XP.
h=prep(0);local function death(raw,killer,flags)
 local u=CreateUnit(3,FourCC(raw),0,0,0);u.summoned=true;u.hp=0
 for k,v in pairs(flags or{})do u[k]=v end
 Dying=u;Killer=killer;OnDeath();return u
end
local gold=Players[0].gold;local xp=h.xp or 0
death('k000',h);assert(Players[0].gold==gold+12);assert((h.xp or 0)==xp)
death('k231',h);assert(Players[0].gold==gold+72)
death('s000',h);assert(Players[0].gold==gold+84,'Pre-existing native summoned pets also give gold')
gold=Players[0].gold;death('k000',nil);death('k000',Hero[3]);death('k000',h,{illusion=true});death('oeye',h,{defaultspeed=0});assert(Players[0].gold==gold)
local transmuted=CreateUnit(3,FourCC('k000'),0,0,0);transmuted.summoned=true;transmuted.hp=0;TransmuteTarget[0]=transmuted;Dying=transmuted;Killer=h;OnDeath();assert(Players[0].gold==gold,'Transmute never gets a second pet bounty')
-- Every active spell has an executable native bot order, including retreat abilities.
local orders=0
for kind=46,49 do
 for slot=0,3 do
  prep(kind-46);h=Hero[0];foe=enemy();h.hp=30;AllowedOrders={berserk=true,roar=true,taunt=true,howlofterror=true,windwalk=true}
  local raw=HeroSkill[kind*4+slot]
  if (kind==46)or(kind==47 and slot>=2)or(kind==48 and slot==3)or(kind==49 and(slot==1 or slot==3))then
   h.abilities[raw]=1;assert(TryBotSpell(0,foe),'Missing native AI order');orders=orders+1
  end
 end
end
assert(orders==9)
reset();ShowHeroGroups(0);assert(#Shop[0].buttons==12);ShowHeroes(0,9);assert(#Shop[0].buttons==7)
for kind=46,49 do reset();assert(SelectRosterHero(0,kind));assert(Hero[0].id==HeroType[kind])end
print('PASS: four hero choices,450 ranked pet types via native timed summons; allies-only ranged/melee lifesteal and expiry, burst/regen bounds,4 rain/6 blade pulses, native paid aura/totem purchases, all9 active bot orders, pet kill gold without ally/timer/illusion/ward/Transmute rewards or extra XP (mock natives).')
