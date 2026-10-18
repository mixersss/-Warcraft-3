-- Actual generated campaign code; terrain/collision, combat and animation natives are mocks.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
CampaignVillageLandmarksClose();StoryShopsClose()
TimeNow=980000;CampaignStage=12;CampaignTransition=true;CampaignCount=0;CampaignActor={};CampaignActorType={};CampaignActorRoute={};CampaignThinkCursor=0;World={}
CampaignLeader=0;CampaignChampion=-1;CampaignPermanentDead={};CampaignClonePending={}
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);Hero[p].hp=10000;Hero[p].maxLife=10000;HeroRole[p]=p;HeroType[p]=Hero[p].type
 StoryShopTripUntil[p]=0;StoryBuyAt[p]=TimeNow+100
end
CampaignBindRoles();CampaignAlliances(2);CampaignMoveHeroes()
for p=0,8 do
 assert(Hero[p].x==CampaignDefenderX[p] and Hero[p].y==CampaignDefenderY[p] and SpawnX[p]==Hero[p].x and SpawnY[p]==Hero[p].y,'All Leaf arrivals and revival anchors are at the corner fountain')
 assert((Hero[p].x-16128)^2+(Hero[p].y+15744)^2<800^2)
 for q=0,p-1 do assert((Hero[p].x-Hero[q].x)^2+(Hero[p].y-Hero[q].y)^2>=96^2)end
end
for p=9,11 do assert(Hero[p].x==-2336,'Sand stays at its own source camp')end
CampaignSpawnStage();while CampaignDeployCursor<242 do CampaignDeploy()end
CampaignStartPlay();local reserves={}
for j=0,CampaignCount-1 do
 local k=CampaignActorType[j];local u=CampaignActor[j]
 if k>=5 and k<=9 then
  reserves[#reserves+1]=u
  assert(u.x==CampaignReserveX[k] and u.y==CampaignReserveY[k] and u.paused and GetUnitAbilityLevel(u,raw('Avul'))>0,'Rear story reserves stay paused and protected after combat starts')
 end
end
assert(#reserves==5)
Hero[0].x=reserves[1].x+100;Hero[0].y=reserves[1].y;World={Hero[0]}
for _,u in ipairs(reserves)do u.last=nil end
for n=1,math.ceil(CampaignCount/24)+1 do CampaignNPCTick()end
for _,u in ipairs(reserves)do assert(u.last==nil and u.paused,'Camp elites never receive invasion attack orders')end
World={};local first=CampaignCount
for lane=0,7 do
 local start=CampaignCount;CampaignInvasionWave(lane);assert(CampaignCount==start+3)
 for n=0,2 do
  local u=CampaignActor[start+n];assert(u.x==CampaignWaveSpawnX[lane*3+n] and u.y==CampaignWaveSpawnY[lane*3+n])
  for m=0,n-1 do local v=CampaignActor[start+m];assert((u.x-v.x)^2+(u.y-v.y)^2>=96^2,'Wave spawn formation must not overlap')end
 end
end
-- Reset stale slot orders/watchdog state when the pool recycles a dead actor.
local old=CampaignActor[first];old.hp=0;CampaignMoveAt[first]=TimeNow+1000;CampaignWalkAt[first]=TimeNow+1000;CampaignWalkAttempt[first]=99
local reused=CampaignAdd(16,9,-2992,-11824);assert(reused==first and CampaignActor[first]~=old and CampaignMoveAt[first]==0 and CampaignWalkAt[first]==TimeNow+8 and CampaignWalkAttempt[first]==0)
CampaignActorRoute[first]=8
local u=CampaignActor[first];local x,y=u.x,u.y;local timerCount=CreatedTimers
TimeNow=TimeNow+9;CampaignThinkCursor=first;CampaignNPCTick()
assert(u.last.o=='move' and CampaignWalkAttempt[first]==1 and CampaignActorRoute[first]==8,'Stationary marcher gets a short recovery move, same route')
assert(u.x==x and u.y==y and (u.last.x-x)^2+(u.last.y-y)^2<=288^2,'Recovery must not teleport the unit')
TimeNow=TimeNow+3;CampaignThinkCursor=first;CampaignNPCTick();assert(u.last.o=='attack' and u.last.x==CampaignRouteX[8] and u.last.y==CampaignRouteY[8],'Normal source route resumes after recovery')
-- Real movement resets the stall counter. Melee-range/ranged combat is not mistaken for a jam.
u.x=x+128;TimeNow=TimeNow+9;CampaignThinkCursor=first;CampaignMoveAt[first]=0;CampaignNPCTick();assert(u.last.o=='attack' and CampaignWalkAttempt[first]==0)
Hero[0].x=u.x+200;Hero[0].y=u.y;World={Hero[0]};TimeNow=TimeNow+9;CampaignThinkCursor=first;CampaignMoveAt[first]=0;CampaignNPCTick()
assert(u.last.o=='attack' and u.last.target==Hero[0],'Do not sidestep away from normal combat')
-- A target beyond attack range across an obstacle must not pin the marcher forever.
Hero[0].x=u.x+800;TimeNow=TimeNow+9;CampaignThinkCursor=first;CampaignMoveAt[first]=0;CampaignWalkX[first]=u.x;CampaignWalkY[first]=u.y;CampaignNPCTick();assert(u.last.o=='move' and CampaignActorRoute[first]==8)
local last=u.last;u.paused=true;TimeNow=TimeNow+9;CampaignThinkCursor=first;CampaignNPCTick();assert(u.last==last and u.paused,'Do not remove pauses or crowd control to recover movement');u.paused=false
SaveReal(NPCCooldowns,GetHandleId(u),0,TimeNow+100);CampaignThinkCursor=first;CampaignNPCTick();assert(u.last==last,'Do not interrupt native busy/channel protection');SaveReal(NPCCooldowns,GetHandleId(u),0,0)
World={};local terrain=IsTerrainPathable;IsTerrainPathable=function()return true end
TimeNow=TimeNow+9;CampaignWalkAt[first]=0;assert(not CampaignWaveRecover(first) and u.last==last,'Never choose blocked recovery ground');IsTerrainPathable=terrain
assert(CreatedTimers==timerCount,'Recovery allocates no per-unit timers')
-- Character role, not slot number, controls the fountain spawn.
HeroRole[0]=9;HeroRole[9]=0;CampaignMoveHeroes();assert(Hero[0].x==-2336 and Hero[9].x==CampaignDefenderX[0] and Hero[9].y==CampaignDefenderY[0])
CampaignStage=15;CampaignTransition=false;local slot=CampaignAdd(5,15,100,200);assert(not CampaignActor[slot].paused and not CampaignReserveOnly(5),'Later story bosses remain active')
CampaignVillageLandmarksClose();StoryShopsClose()
print('PASS: nine spaced corner-fountain arrival/revival positions and role swaps, five protected stationary rear elites, all eight separated wave formations, recycled-slot reset, stalled and unreachable-target recovery without teleport/extra timers, route resumption, moving/combat/paused/busy safeguards and later story bosses preserved (mock natives).')
