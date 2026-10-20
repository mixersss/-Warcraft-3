-- Execute all twelve custom effects; Channel itself has no native gameplay effect.
function RAbsBJ(x)return math.abs(x)end
local function near(a,b)assert(math.abs(a-b)<.002,'actual='..a..' expected='..b)end
local function prep(kind)
 reset();Seconds=100;CreateHero(0,46+kind)
 local h=Hero[0];h.x=0;h.y=0;h.hp=800;h.max=1000;h.mana=500;h.maxmana=1000
 for p=1,11 do Hero[p].x=5000;Hero[p].y=5000 end
 return h
end
local function enemy(x,y)
 local u=CreateUnit(3,FourCC('fm00'),x or 100,y or 0,0);u.hp=5000;u.max=5000;u.mana=500;u.maxmana=500;return u
end
local function cast(slot,rank,target,x,y,event)
 Dying=Hero[0];SpellId=HeroSkill[HeroKind[0]*4+slot];Hero[0].abilities[SpellId]=rank;SpellTarget=target;AimX=x or 0;AimY=y or 0
 SpellEvent=event or EVENT_PLAYER_UNIT_SPELL_EFFECT;OnCreativeSpell()
end
-- Bookmark returns only living heroes, caps recovery and cannot cross sectors.
local h=prep(0);cast(0,1,nil);h.x=400;h.hp=200;h.mana=100;Seconds=105;CreativeTick();near(h.hp,200)
Seconds=106;CreativeTick();near(h.x,0);near(h.hp,288);near(h.mana,132);assert(CreativeBookUntil[0]==0 and not CreativeArtA[0])
cast(0,200,nil);h.x=300;HeroSector[0]=2;Seconds=112;CreativeTick();near(h.x,300)
cast(0,1,nil);h.hp=0;Seconds=118;CreativeTick();near(h.hp,0);assert(CreativeBookUntil[0]==0)
-- Movement debt accounts bounded sampled travel, not teleporting/standing damage without cap.
h=prep(0);local e=enemy(100,0);cast(1,1,e)
for i=1,4 do e.x=e.x+100;Seconds=100+i;CreativeTick()end
near(e.hp,5000-(29+4*8.5));assert(not CreativeDebt[0]);Seconds=105;CreativeTick();near(e.hp,4937)
e=enemy();cast(1,1,e);Seconds=109;CreativeTick();near(e.hp,4971)
-- Three zone pulses; final multiplier requires the real caster inside its area.
h=prep(0);e=enemy(0,0);cast(2,1,nil,0,0)
for t=102,104 do Seconds=t;CreativeTick()end
near(e.hp,4932);assert(CreativeZoneTicks[0]==0)
h=prep(0);e=enemy(0,0);cast(3,1,nil)
for t=101,104 do Seconds=t;CreativeTick()end
near(e.hp,4720)
-- Thread comes from actual damage only, is bounded and healing spends exactly its pool.
h=prep(1);e=enemy();cast(0,1,e);near(e.hp,4951);near(CreativeBank[0],19.6)
e.magicimmune=true;cast(0,200,e);near(CreativeBank[0],19.6)
local before=h.hp;cast(2,200,nil);near(h.hp-before,19.6);near(CreativeBank[0],0)
local ally=Hero[1];ally.x=50;ally.y=0;ally.hero=true;ally.max=2000;ally.hp=200;h.hp=800
cast(1,200,ally);near(h.hp,1000/3);near(ally.hp,2000/3);near(h.hp+ally.hp,1000)
CreativeBank[0]=1000;e.magicimmune=false;local hp=e.hp;cast(3,1,nil);near(CreativeBank[0],670);near(e.hp,hp-253)
-- Segment and strict triangle tests exclude off-shape units, buildings and immunity.
h=prep(2);h.x=0;h.y=400;e=enemy(100,100);local outside=enemy(400,400)
cast(0,1,nil,0,0);cast(1,1,nil,400,0);local prior=e.hp;local out=outside.hp
cast(3,1,nil);near(e.hp,prior-138);near(outside.hp,out);assert(CreativeAUntil[0]==0 and CreativeBUntil[0]==0)
cast(0,1,nil,0,0);cast(1,1,nil,400,0);h.hp=100;cast(2,1,nil);near(h.hp,172);assert(CreativeAUntil[0]>Seconds and CreativeBUntil[0]==0)
cast(1,1,nil,400,0);Seconds=114;CreativeTick();assert(not CreativeArtA[0] and not CreativeArtB[0])
near(CreativeLineDistance(200,80,0,0,400,0),80);near(CreativeLineDistance(500,0,0,0,400,0),100)
-- Learn/cast UI shells have no unrelated native spell; combo-aware native bot orders.
for kind=46,48 do
 prep(kind-46);h=Hero[0];e=enemy();AllowedOrders={berserk=true,roar=true,taunt=true,howlofterror=true}
 for slot=0,3 do h.abilities[HeroSkill[kind*4+slot]]=1 end
 assert(TryBotSpell(0,e))
 if kind==48 then
  assert(h.order[1]=='berserk');cast(0,1,nil,-100,-100);assert(TryBotSpell(0,e) and h.order[1]=='roar')
  cast(1,1,nil,200,-100);assert(TryBotSpell(0,e) and h.order[1]=='howlofterror')
 elseif kind==47 then
  assert(h.order[1]=='berserk');CreativeBank[0]=200;h.hp=100;assert(TryBotSpell(0,e) and h.order[1]=='taunt')
 else assert(h.order[1]=='berserk')end
end
reset();ShowHeroGroups(0);assert(#Shop[0].buttons==12);ShowHeroes(0,9);assert(#Shop[0].buttons==6)
for kind=46,48 do reset();assert(SelectRosterHero(0,kind));assert(Hero[0].id==HeroType[kind])end
-- Repeated replacement removes retained art/targets/state; no new group per cast.
local created,destroyed=0,0;local addNative,removeNative=AddSpecialEffect,DestroyEffect
function AddSpecialEffect(...)created=created+1;return addNative(...)end
function DestroyEffect(e)destroyed=destroyed+1;return removeNative(e)end
for round=1,60 do
 h=prep(2);cast(0,1,nil,0,0);cast(1,1,nil,400,0);CreateHero(0,0)
 assert(not CreativeArtA[0] and not CreativeArtB[0] and CreativeBank[0]==0 and not CreativeDebt[0])
end
assert(created==destroyed,'All newly created persistent node art is released on replacement')
print('PASS: twelve original skill effects; capped rewind/travel damage, conditional zones, conserved HP/thread, exact line/triangle geometry, active expiry/death/swap cleanup, combo-aware bots and three gallery choices (mock natives).')
