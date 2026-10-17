-- Regression for user-visible missing Tobidogu/shadow effects. Native rendering is a separate check.
for p=0,11 do RosterReset(p)end
Hero={};HeroRole={};HeroType={};TimeNow=8500;World={}
for p=0,11 do Hero[p]=CreateUnit(p,p,0,0,0);HeroRole[p]=p;HeroType[p]=p;Hero[p].hp=1000000;Hero[p].mana=100000;Hero[p].points=0 end
local function step(t)
 for n=1,math.floor(t/.05+.5)do TimeNow=TimeNow+.05;VisualTick();if n%5==0 then SkillsTick()end end
end
local function emptyShadow(p)
 assert(not ShadowRoot[p] and not ShadowTarget[p])
 for n=0,15 do assert(not ShadowSegment[p*16+n])end
end
-- No flying-form ability changes are allowed during a live cast; these can interfere with Channel.
local add,remove=UnitAddAbility,UnitRemoveAbility
local during=false;local prepares=0
local nativePose=SetUnitAnimationByIndex;local throwPoses=0
function SetUnitAnimationByIndex(u,index)
 if u==Hero[5] and index==1 then throwPoses=throwPoses+1 end
 return nativePose(u,index)
end
function UnitAddAbility(u,id)
 if u==Hero[5] and id==raw('Amrf')then assert(not during,'Adding Amrf during Tobidogu');prepares=prepares+1 end
 return add(u,id)
end
function UnitRemoveAbility(u,id)
 if u==Hero[5] and id==raw('Amrf')then assert(not during,'Removing Amrf during Tobidogu')end
 return remove(u,id)
end
VisualPrepareHero(5);assert(prepares==1)
during=true;cast(5,PlayableSkill[26],3,nil);during=false
assert(prepares==1 and VisualVolleyLeft[5]==3)
step(.25);assert(Hero[5].flyHeight>0 and Hero[5].flyHeight<=350 and Hero[5].animationIndex==1)
local knives=0
for n=0,255 do if VisualUnit[n] and VisualUnit[n].type==raw('vfan')then knives=knives+1 end end
assert(knives==2,'First volley must contain two native Fan of Knives missiles')
step(.6);assert(VisualVolleyFired[5]==3 and throwPoses==2,'Later volleys must not restart the body pose before its visible weapon frames')
Caster=Hero[5];Spell=PlayableSkill[26];SkillsEndcast();assert(VisualLiftUnit[5]==nil and VisualVolleyLeft[5]==0 and Hero[5].flyHeight==0)
RosterReset(5)
-- AEer native buff may arrive after SPELL_EFFECT. Never erase the effect on the first empty check.
local enemy=CreateUnit(12,123,600,0,0);enemy.hp=1000000;enemy.abilities={}
cast(6,PlayableSkill[30],1,enemy);local root=ShadowRoot[6]
assert(root and root.type==raw('rshk') and root.animation=='birth' and ShadowSegment[96])
TimeNow=8500.5;RosterTick();assert(ShadowRoot[6]==root and not root.removed and not ShadowBuffSeen[6])
enemy.abilities[raw('Rsmb')]=1;TimeNow=8500.75;RosterTick()
assert(ShadowBuffSeen[6] and ShadowUntil[6]==8502.75 and not root.removed)
enemy.x=500;enemy.y=100;RosterTick();assert(root.x==500 and root.y==100)
-- Every strip is above terrain, near black, explicitly Stand, and points toward the target.
local strip=ShadowSegment[96];assert(strip and strip.animation=='stand' and strip.flyHeight==6 and strip.alpha==245)
-- Replacement, actual dispel, death and rejected/missing native buff all release the bounded actors.
cast(6,PlayableSkill[30],2,enemy);assert(root.removed);root=ShadowRoot[6]
enemy.abilities[raw('Rsmb')]=nil;RosterTick();emptyShadow(6);assert(root.removed)
TimeNow=8510;cast(6,PlayableSkill[30],1,enemy);root=ShadowRoot[6];TimeNow=8510.5;RosterTick();assert(not root.removed)
TimeNow=8511.1;RosterTick();emptyShadow(6);assert(root.removed)
enemy.abilities[raw('Rsmb')]=1;TimeNow=8520;cast(6,PlayableSkill[30],1,enemy);root=ShadowRoot[6]
Hero[6].hp=0;RosterTick();emptyShadow(6);assert(root.removed);Hero[6].hp=1000000
cast(6,PlayableSkill[30],1,enemy);root=ShadowRoot[6];enemy.hp=0;RosterTick();emptyShadow(6);assert(root.removed)
UnitAddAbility=add;UnitRemoveAbility=remove;SetUnitAnimationByIndex=nativePose
print('PASS: Tobidogu flight prepared outside Channel, visible native missiles/throw pose, delayed shadow buff, original Birth actor, solid ground strips and replacement/dispel/death/rejection cleanup (mock natives).')
