-- Animation playback itself requires Warcraft; these execute the actual shipped presentation JASS.
for p=0,11 do RosterReset(p) end
World={};Hero={};HeroType={};HeroRole={};TimeNow=5000;Orders={};Controllers={}
for p=0,11 do
 Hero[p]=CreateUnit(p,p,0,0,0);Hero[p].hp=100000000;Hero[p].maxLife=100000000;Hero[p].mana=1000000
 HeroType[p]=p;HeroRole[p]=p;Hero[p].points=0;Hero[p].level=60
end
local enemy=CreateUnit(12,123,400,100,0);enemy.hp=100000000;enemy.maxLife=100000000;enemy.mana=1000000
local oldTargetEffect=AddSpecialEffectTarget
local arts={}
function AddSpecialEffectTarget(model,u,point)
 local e=oldTargetEffect(model,u,point);e.model=model;e.unit=u;e.point=point;arts[#arts+1]=e;return e
end
local function step(seconds)
 for n=1,math.floor(seconds/.05+.5) do
  TimeNow=TimeNow+.05;VisualTick()
  if n%5==0 then SkillsTick() end
 end
end
local function clear(p)
 Caster=Hero[p];Spell=PlayableSkill[VisualChannelIndex[p] or 0] or 0;SkillsEndcast()
 RosterReset(p);ComboLeft[p]=0;ComboTarget[p]=nil;VisualChannelUntil[p]=0
end
local function countRaw(rawid)
 local count=0
 for i=0,255 do if VisualUnit[i] and VisualUnit[i].type==raw(rawid)then count=count+1 end end
 return count
end
-- Every active slot still emits a valid body pose; every temporary actor is cleaned.
local active=0;local baselineTimers=CreatedTimers
for index=0,59 do
 if PlayableSkill[index]~=0 and not SkillPassive[index] then
  local p=math.floor(index/5);Caster=Hero[p];Caster.abilities={};Caster.hp=Caster.maxLife;Caster.mana=1000000
  AimX=400;AimY=100;Dummy[math.floor(p/3)]=enemy;World={enemy}
  cast(p,PlayableSkill[index],1,SkillHeal[index] and Hero[p] or enemy)
  SkillsTick();assert(Caster.animationIndex==SkillAnimation[index],'Missing pose '..index)
  step(.5);clear(p)
  for n=0,255 do assert(not VisualUnit[n] or VisualOwner[n]~=p,'Visual actor retained after hero reset')end
  active=active+1
 end
end
assert(active==52 and CreatedTimers==baselineTimers,'No per-cast timers')
-- Both Kaiten spheres come from the complete spell-spin pose. They cannot be interrupted by AI.
for _,p in ipairs({4,8}) do
 World={};Hero[p].abilities={};Hero[p].mana=1000000;Hero[p].hp=100000000
 cast(p,PlayableSkill[p*5+1],2,nil);SkillsTick()
 local anim=Hero[p].animationIndex
 assert(anim==(p==4 and 2 or 3) and math.abs(Hero[p].timeScale-2.933/2)<.0001)
 assert(VisualChannelUntil[p]>TimeNow+1.9 and ZoneUntil[p]>TimeNow+1.9)
 BotNextCast[p]=0;local orders=#Orders;step(1)
 assert(not SkillsBot(p) and #Orders==orders and Hero[p].animationIndex==anim)
 Caster=Hero[p];Spell=PlayableSkill[p*5+1];SkillsEndcast()
 assert(Hero[p].timeScale==1 and ZoneUntil[p]==0 and VisualChannelUntil[p]==0 and Hero[p].animation=='stand')
end
-- Kunai flight is now native AHtb: do not overlay a second, non-damaging missile.
local p=5;Hero[p].x=0;Hero[p].y=0;AimX=600;AimY=0
local beforeKunai=countRaw('vkun');VisualApply(p,25,1,enemy);assert(countRaw('vkun')==beforeKunai,'Native kunai owns its projectile; avoid a duplicate cosmetic flight')
-- Both weapon barrages contain visible shuriken trajectories; the long one also includes notes.
VisualPulse(5,26,500,0);assert(countRaw('vshu')>0 and countRaw('vkun')>0)
clear(5);VisualPulse(5,28,500,0);assert(countRaw('vnot')>0 and countRaw('vshu')>0)
clear(5)
-- Wind and the electrical cyclone are different source models.
VisualApply(11,58,1,enemy);assert(countRaw('vtor')==3 and countRaw('vcyc')==0);clear(11)
VisualApply(11,57,1,enemy);assert(countRaw('vcyc')==1);clear(11)
VisualApply(11,59,1,enemy);assert(countRaw('vrac')==1 and countRaw('vkuc')==1);clear(11)
-- Rasengan / Chidori use the real left/right attachment names and source art, not a Farseer bolt.
VisualApply(0,3,1,enemy);assert(VisualHand[0].point=='hand right' and string.find(VisualHand[0].model,'ClarityTarget',1,true))
VisualApply(1,8,1,enemy);assert(VisualHand[4].point=='hand left' and string.find(VisualHand[5].model,'BoltImpact',1,true))
-- A native looping Chidori pose returns to idle instead of leaving a permanent charge animation.
cast(1,PlayableSkill[8],1,enemy);Hero[1].order=0;SkillsTick();step(2)
assert(Hero[1].animation=='stand')
-- Naruto alternate, cursed Sasuke and Shukaku use their own model's spell sequences.
for _,p in ipairs({0,1,9}) do
 local index=p*5+(p==0 and 1 or 0)
 Hero[p].type=9999;Caster=Hero[p];Hero[p].abilities={};Hero[p].hp=100000000
 cast(p,PlayableSkill[index],1,enemy);SkillsTick()
 assert(Hero[p].animationIndex==SkillFormAnimation[index] and SkillFormAnimation[index]>=0)
 Hero[p].type=HeroType[p];clear(p)
end
-- Stress replacement and death cleanup: the ring never exceeds 256 actors, no double remove.
for n=1,600 do VisualCreate(5,raw('vshu'),0,0,500,0,100,40,.65,1) end
local count=0;for n=0,255 do if VisualUnit[n] then count=count+1 end end;assert(count==256)
Hero[5].hp=0;VisualTick()
for n=0,255 do assert(not VisualUnit[n])end;Hero[5].hp=100000000
step(15)
for p=0,11 do RosterReset(p) end
for _,e in ipairs(arts)do assert(not e.alive,'Retained hand art')end
assert(CreatedTimers==baselineTimers)
print('PASS: all 52 visual cast paths, uninterrupted Kaiten pose/stop cleanup, travelling weapons, distinct wind/cyclone, real hand attachments, alternate form poses, finite looping poses and bounded 600-shot stress cleanup (mock natives).')

TimeNow=6000;Hero[7].type=HeroType[7];Hero[7].hp=100000000
cast(7,PlayableSkill[37],1,nil);assert(KibaFourLegs[7] and Hero[7].alternate)
VisualPose(7,38);assert(Hero[7].animationIndex==15)
Hero[7].type=raw('Rkfm');VisualPose(7,38);assert(Hero[7].animation=='attack','Stock wolf must never receive an out-of-range Kiba model index')
RosterClearBuff(7);assert(not KibaFourLegs[7] and not Hero[7].alternate)
Hero[7].type=HeroType[7]
