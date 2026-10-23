-- Regression scenarios execute shipped JASS with mocked Classic natives.
for p=0,11 do RosterReset(p) end
Hero={};HeroType={};HeroRole={};World={};Controllers={};StoryStarted={};TimeNow=3000
for p=0,11 do
 Hero[p]=CreateUnit(p,p,0,0,0);HeroType[p]=p;HeroRole[p]=p
 Hero[p].level=60;Hero[p].points=4;Hero[p].abilities={}
end
--3.5 fourth skills are learned active techniques, never free reincarnations.
RosterGrantInnate(6);assert(GetUnitAbilityLevel(Hero[6],raw('R604'))==0 and Hero[6].points==4)
RosterGrantInnate(3);assert(GetUnitAbilityLevel(Hero[3],raw('R301'))==0)
Controllers[0]='human';Hero[0].xp=0;Hero[0].points=1;SkillsChoose(0,6)
assert(GetUnitAbilityLevel(Hero[0],raw('R604'))==0 and Hero[0].points==1)
Hero[0].level=50;Caster=Hero[0];SkillsLevel();assert(GetUnitAbilityLevel(Hero[0],raw('R604'))==0,'Active choking must be learned manually')
function PingMinimapEx(x,y,d,r,g,b,extra)Pings[#Pings+1]={x=x,y=y}end
-- Both Hyuuga: source 400/600/800/1000 radius; allies/structures/outside enemies not marked.
local near=CreateUnit(12,111,350,0,0)
local far=CreateUnit(12,111,1100,0,0)
local ally=CreateUnit(3,111,100,0,0)
local shop=CreateUnit(12,111,50,0,0);shop.structure=true
World={near,far,ally,shop};LocalPlayer=4
for _,p in ipairs({4,8}) do
 ally.owner=p
 near.x=350;near.y=0
 for rank=1,4 do
  near.x=350;near.y=0
  Pings={};LocalPlayer=p;cast(p,PlayableSkill[p*5],rank,nil)
  assert(VisionRadius[p]==200+200*rank and VisionFog[p].radius==VisionRadius[p])
  assert(GetUnitAbilityLevel(Hero[p],raw('Rbyg'))==rank and #Pings==1 and Pings[1].x==350)
  local fog=VisionFog[p]
  cast(p,PlayableSkill[p*5+1],1,nil)
  assert(VisionUntil[p]>TimeNow and not fog.destroyed and GetUnitAbilityLevel(Hero[p],raw('Rbyg'))==rank,'Kaiten must not cancel sight')
  LocalPlayer=(p+3)%12;Pings={};TimeNow=TimeNow+2;RosterTick();assert(#Pings==0,'Enemy clients must not receive Byakugan pings')
  RosterReset(p);assert(fog.destroyed and not VisionFog[p] and not VisionArt[p] and GetUnitAbilityLevel(Hero[p],raw('Rbyg'))==0)
 end
end
TimeNow=3100;RosterVision(4,2);local fog=VisionFog[4];TimeNow=3115;RosterTick()
assert(VisionUntil[4]==0 and fog.destroyed)
RosterVision(4,1);Hero[4].hp=0;RosterTick();assert(not VisionFog[4] and not VisionArt[4]);Hero[4].hp=10000
assert(FogCreated==FogDestroyed,'Sight handles must be cleaned on replacement, death, expiry and hero change')
-- Ground shadow uses bounded pathless visual units. Dispel/death/recast clean every segment.
TimeNow=3200;near.x=600;near.abilities[raw('Rsmb')]=1
cast(6,raw('R601'),2,near);local first=ShadowSegment[96]
assert(first and first.type==raw('rshd') and first.pathing==false and ShadowTarget[6]==near)
local count=0;for n=0,15 do if ShadowSegment[96+n] then count=count+1 end end;assert(count==12)
near.y=100;RosterTick();assert(ShadowSegment[96].y>0)
near.abilities[raw('Rsmb')]=nil;RosterTick();assert(first.removed and not ShadowTarget[6])
for n=0,15 do assert(not ShadowSegment[96+n])end
near.abilities[raw('Rsmb')]=1;cast(6,raw('R601'),1,near);first=ShadowSegment[96]
cast(6,raw('R601'),4,near);assert(first.removed)
TimeNow=3209;RosterTick();assert(not ShadowTarget[6])
cast(6,raw('R601'),1,near);Hero[6].hp=0;RosterTick();assert(not ShadowTarget[6]);Hero[6].hp=10000
function IssueImmediateOrder(u,o)Orders[#Orders+1]={unit=u,order=o};return true end
-- Self-centered attacks cannot spend a cooldown at 700 range: Kaiten for both heroes + Hinata guard.
for _,index in ipairs({21,41,43,13}) do
 local p=math.floor(index/5);local slot=index%5
 Hero[p].hp=10000;Hero[p].x=0;Hero[p].y=0;Hero[p].mana=1000;HeroRole[p]=p;ComboLeft[p]=0
 Hero[p].abilities={};Hero[p].points=0;Hero[p].abilities[PlayableSkill[index]]=1
 for k=0,4 do BotReadyAt[p*5+k]=999999 end
 BotReadyAt[p*5+slot]=0;BotNextCast[p]=0;TimeNow=3300
 near.x=700;near.y=0;Dummy[math.floor(p/3)]=near
 local orders=#Orders
 assert(not SkillsBot(p) and #Orders==orders and BotReadyAt[p*5+slot]==0)
 near.x=RosterRadius[index]+1;assert(not SkillsBot(p))
 near.x=RosterRadius[index]-1;assert(SkillsBot(p) and #Orders==orders+1)
end
print('Technique audit: source3.5 active fourth skill; sight ranges/team privacy/lifecycle; shadow lifecycle; close-range AI boundaries')

-- Kaiten has independent sight state in both cast orders and repels only enemies.
TimeNow=3500;LocalPlayer=4;World={near,ally,shop};ally.owner=4;near.x=100;near.y=0;ally.x=100
function IsTerrainPathable(x,y,t)return false end
function GetTerrainCliffLevel(x,y)return 0 end
for _,p in ipairs({4,8}) do
 ally.owner=p;near.x=100;near.y=0
 cast(p,PlayableSkill[p*5+1],1,nil)
 assert(near.x==220 and ally.x==100,'Rank-one Kaiten must repel enemies 120 without moving allies')
 local zone=ZoneArt[p];local untilTime=ZoneUntil[p]
 cast(p,PlayableSkill[p*5],1,nil)
 assert(ZoneArt[p]==zone and ZoneUntil[p]==untilTime and (not zone or not zone.destroyed),'Activating sight must preserve Kaiten')
 RosterClearZone(p);RosterClearBuff(p);RosterClearVision(p)
end
-- A blocked passage and a cliff stop knockback before the obstacle.
near.x=100;near.y=0;World={near}
function IsTerrainPathable(x,y,t)return x>=160 end
RosterRepel(4,3);assert(near.x==140)
near.x=100
function IsTerrainPathable(x,y,t)return false end
function GetTerrainCliffLevel(x,y)return x>=160 and 1 or 0 end
RosterRepel(4,3);assert(near.x==140)
