-- Regression for reported 08 bugs, using actual built JASS with native mocks.
for p=0,11 do RosterReset(p) end
World={};Hero={};HeroType={};HeroRole={};TimeNow=7000;Controllers={}
for p=0,11 do Hero[p]=CreateUnit(p,p,-15000,14000,0);HeroType[p]=p;HeroRole[p]=p;Hero[p].points=0;Hero[p].level=60;Hero[p].hp=100000000 end
local function step(seconds)
 for i=1,math.floor(seconds/.05+.5) do TimeNow=TimeNow+.05;VisualTick();if i%5==0 then SkillsTick()end end
end
-- Byakugan chooses Stand Ready, never the generic Spell tag which also matched Spell Spin.
for _,p in ipairs({4,8})do
 cast(p,PlayableSkill[p*5],1,nil);SkillsTick()
 assert(SkillAnimation[p*5]==0 and Hero[p].animationIndex==0 and VisionUntil[p]>TimeNow)
 assert(ZoneUntil[p]==0,'Detection alone must not start Kaiten damage')
 RosterReset(p)
end
-- All three Tobidogu ranks emit their volleys around the actual caster, not world origin.
local originalCreate=CreateUnit;local created=0
function CreateUnit(p,id,x,y,f)
 if id==raw('vshu') or id==raw('vkun') or id==raw('vnot') or id==raw('vfan') then created=created+1 end
 return originalCreate(p,id,x,y,f)
end
for rank=1,3 do
 local p=5;Hero[p].flyHeight=0;Hero[p].pathing=true;created=0;AimX=0;AimY=0
 cast(p,PlayableSkill[26],rank,nil)
 assert(VisualLiftUnit[p]==Hero[p] and VisualVolleyLeft[p]==rank)
 step(.25);assert(Hero[p].flyHeight>0 and created==6)
 for n=0,255 do
  if VisualUnit[n] and VisualOwner[n]==p then
   assert(math.abs(VisualTX[n]-Hero[p].x)<300 and math.abs(VisualTY[n]-Hero[p].y)<300,'Tobidogu must not shoot toward map center')
  end
 end
 step(.70);assert(created==6*rank,'Each learned rank must emit its actual repeated volley')
 step(.15);assert(not VisualLiftUnit[p] and math.abs(Hero[p].flyHeight)<.001 and Hero[p].pathing)
 Caster=Hero[p];Spell=PlayableSkill[26];SkillsEndcast();RosterReset(p)
end
-- Soshoryu: aerial pose and weapons; stop and death restore the original height.
Hero[5].flyHeight=17;AimX=Hero[5].x+350;AimY=Hero[5].y
cast(5,PlayableSkill[28],1,nil);step(.25);assert(Hero[5].flyHeight>17)
Caster=Hero[5];Spell=PlayableSkill[28];SkillsEndcast()
assert(not VisualLiftUnit[5] and Hero[5].flyHeight==17)
RosterReset(5);cast(5,PlayableSkill[28],1,nil);step(.25);Hero[5].hp=0;VisualTick()
assert(not VisualLiftUnit[5] and Hero[5].flyHeight==17);Hero[5].hp=100000000;RosterReset(5)
-- Kaiten takes two seconds at both heroes, with original-size MDX and preserved full-cast damage.
for _,p in ipairs({4,8})do
 Hero[p].x=0;Hero[p].y=0
 local enemy=CreateUnit(12,123,0,0,0);enemy.hp=100000000;World={enemy}
 cast(p,PlayableSkill[p*5+1],1,nil);SkillsTick();assert(math.abs(Hero[p].timeScale-2.933/2)<.0001)
 local started=TimeNow
 step(2.05)
 assert(ZoneUntil[p]==0 and math.abs(enemy.hp-(100000000-100))<.01,'Kaiten must apply source rank-one damage once before push')
 assert(TimeNow-started<2.1)
 Caster=Hero[p];Spell=PlayableSkill[p*5+1];SkillsEndcast();RosterReset(p)
end
print('PASS: neutral Byakugan without spin, Tenten ranks/volley destinations/aerial lifecycle and two-second Kaiten with source instant damage (mock natives).')
