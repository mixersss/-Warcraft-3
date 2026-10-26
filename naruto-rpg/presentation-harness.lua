-- All 52 active slots must queue an existing normal-model cast animation, including native spells.
Hero={};HeroType={};HeroRole={};HeroTemplate={};World={};Controllers={};TimeNow=2000
for p=0,11 do Hero[p]=CreateUnit(p,p,SpawnX[p],SpawnY[p],0);HeroType[p]=p;HeroRole[p]=p;HeroTemplate[p]=p;Hero[p].level=60;Hero[p].points=60 end
local enemy=CreateUnit(12,123,100,0,0);enemy.hp=1000000;enemy.maxLife=1000000;enemy.mana=100000
local count=0
for index=0,59 do
 local p=math.floor(index/5)
 if PlayableSkill[index]~=0 and not SkillPassive[index] then
  Caster=Hero[p];Target=enemy;Spell=PlayableSkill[index];Caster.abilities[Spell]=1
  assert(SkillAnimation[index]>=0,'Unresolved animation')
  SkillsEffect()
  if index==8 then
   assert(not SkillPoseQueued[p] and VisualApproachSkill[p]==8 and VisualApproachCaster[p]==Caster,'Chidori runs source rush/impact sequence instead of queued looping charge')
   SkillsTick()
  else
   assert(SkillPoseQueued[p] and SkillPoseIndex[p]==SkillAnimation[index])
   SkillsTick();assert(not SkillPoseQueued[p] and Caster.animationIndex==((KibaFourLegs[p] and p==7 and index~=37 and index~=38) and 15 or SkillAnimation[index]),'Native spell must animate after instant cast ends '..index)
  end
  count=count+1
 end
end
assert(count==54)
-- Imported one-shot effects must survive creation, then be cleaned by the shared timer.
local fx=AddSpecialEffect('WindAttack.mdl',0,0);SkillsHoldFlash(fx);assert(fx.alive)
TimeNow=2001;SkillsTick();assert(fx.alive)
TimeNow=2001.5;SkillsTick();assert(not fx.alive)
-- Stage rewards must not add synthetic XP on top of source native kill XP.
Hero[0].xp=1234;StoryReward(0,0,99999);assert(Hero[0].xp==1234)
