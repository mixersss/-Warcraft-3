-- Tests actual generated JASS; mocks cannot demonstrate native combat or rendering.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
function GetAttacker()return Attacker end
local oldRandom=GetRandomReal
function GetRandomReal(a,b)return (a+b)/2 end
CampaignStage=9;CampaignDuelLive=true;CampaignTransition=false;TimeNow=50000
Hero={};Companion={};Dummy={};World={}
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+p,100,100,0);Hero[p].maxLife=10000;Hero[p].hp=10000;Hero[p].maxMana=1000;Hero[p].mana=1000;Hero[p].level=40
 HeroRole[p]=p;HeroType[p]=Hero[p].type;VisionUntil[p]=0;ArenaAttackAt[p]=0
end
local enemy=CreateUnit(12,0,300,100,0);enemy.mana=1000;enemy.maxMana=1000
-- Arena cosmetics run for every ranged hero and release their bounded actors.
for _,p in ipairs({2,5,6,9,11})do
 Attacker=Hero[p];Caster=enemy
 local slot=VisualCursor;local hp=enemy.hp;SkillsRosterAttack()
 local actor=VisualUnit[slot];assert(actor and VisualMode[slot]==1 and enemy.hp==hp,'Projectile actor must add no damage')
 local expected=(p==9 and 'vsnd')or(p==11 and 'vwnd')or'vshu';assert(actor.type==raw(expected))
 for tick=1,35 do VisualTick()end
 assert(actor.removed,'Arena attack actors must not leak')
end
-- Source Hyuuga attacked-event mana burns require active Byakugan; not a permanent aura.
for _,p in ipairs({4,8})do
 local skill=raw(p==4 and 'R401'or'R801');Attacker=Hero[p];Caster=enemy
 for rank=1,4 do
  Hero[p].abilities[skill]=rank;VisionUntil[p]=TimeNow+10;enemy.mana=1000
  local hp=enemy.hp;SkillsRosterAttack();assert(enemy.mana==1000-(5*rank+5+10*rank)/2 and enemy.hp==hp)
 end
 VisionUntil[p]=TimeNow;enemy.mana=1000;SkillsRosterAttack();assert(enemy.mana==1000,'Expired detection gives no passive mana burn')
end
-- Living pets survive recasts, story cleanup and spectator seating; no timed life.
Hero[7].abilities[raw('R701')]=3;RosterSummon(7,35,3)
local dog=Companion[21];assert(dog and not dog.expire);RosterSummon(7,35,3);assert(Companion[21]==dog and not dog.removed)
dog.type=raw('rdgf');RosterSummon(7,35,3);assert(Companion[21]==dog,'A transformed dog must not be replaced')
RosterResetEffects(7);assert(Companion[21]==dog and not dog.removed)
Hero[7].paused=true;RosterSyncPets(7);assert(dog.paused and dog.abilities[raw('Avul')])
Hero[7].x=400;Hero[7].paused=false;RosterSyncPets(7);assert(not dog.paused and not dog.abilities[raw('Avul')])
Hero[10].abilities[raw('RA03')]=2;RosterSummon(10,52,2)
local puppet=Companion[31];puppet.abilities[raw('Rktr')]=1;puppet.mana=600
Dummy[3]=enemy;enemy.x=puppet.x+50;enemy.y=puppet.y
PetCastAt[31]=0;RosterPetThink(10);assert(puppet.last.o=='thunderbolt','Puppet AI uses its original trap order')
RosterPetSpell(puppet,enemy,raw('Rktr'));RosterResetEffects(10);assert(not PetTrapVictim[31] and Companion[31]==puppet,'Scene cleanup cancels old trap but keeps puppet')
RosterPetSpell(puppet,enemy,raw('Rktr'));local hp=enemy.hp
TimeNow=TimeNow+2.5;RosterPetThink(10);assert(enemy.hp==hp and puppet.hp>0)
TimeNow=TimeNow+.5;RosterPetThink(10);assert(enemy.hp==hp-600 and puppet.hp==0 and not PetTrapVictim[31],'Trap resolves once and sacrifices puppet')
TimeNow=TimeNow+1;RosterPetThink(10);assert(enemy.hp==hp-600)
-- Isolated smoke callback: at most three original fog units, bounded cleanup, no source-global sleeps.
RosterSummon(10,50,3);local karasu=Companion[30]
AimX=300;AimY=100;RosterPetSpell(karasu,nil,raw('Rpsm'));local fog=PetFog[30]
assert(fog and PetFog[31]and PetFog[32]);RosterPetSpell(karasu,nil,raw('Rpsm'));assert(fog.removed)
TimeNow=TimeNow+4;RosterPetThink(10);assert(not PetFog[30]and not PetFog[31]and not PetFog[32])
-- Ambient fountains disable all HP/mana auras in arenas and restore the exact source types afterward.
VillageFountain={};for j=0,3 do VillageFountain[j]=CreateUnit(14,0,0,0,0);UnitAddAbility(VillageFountain[j],raw('ACnr'));UnitAddAbility(VillageFountain[j],raw('ANre'))end
CampaignFountainAuras(11)
for j=0,3 do local a=VillageFountain[j].abilities;assert(not a[raw('ACnr')]and not a[raw('Crg2')]and not a[raw('ANre')])end
CampaignFountainAuras(12)
for j=0,3 do local a=VillageFountain[j].abilities;assert(a[raw((j==0 or j==2)and'Crg2'or'ACnr')]and a[raw('ANre')])end
GetRandomReal=oldRandom
print('PASS: Alpha22 arena projectile actor lifecycle/no extra damage, four Byakugan burn ranks for both Hyuugas/expiry, permanent/morphed companion recast and scene/spectator survival, pet trap AI/delayed sacrifice, bounded isolated smoke, arena fountain suppression and exact restoration (mock natives).')
