-- Execute the generated campaign decisions; native combat/pathfinding are not emulated.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
CampaignVillageLandmarksClose();StoryShopsClose()
TimeNow=950000;CampaignStage=12;CampaignTransition=false;CampaignCount=0;CampaignThinkCursor=0;CampaignActor={};CampaignActorRoute={};World={}
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+p,6096,-8528,0);Hero[p].hp=10000;Hero[p].maxLife=10000
 Controllers[p]='computer';HeroRole[p]=p;HeroType[p]=Hero[p].type;CampaignPermanentDead[p]=false;CampaignClonePending[p]=false
 SpawnX[p]=6096;SpawnY[p]=-8528;StoryBuyAt[p]=TimeNow;StoryShopTripUntil[p]=0
end
for t=0,3 do StoryMarch[t]=true;StoryRetreat[t]=false end
CampaignBindRoles();CampaignAlliances(2);CampaignAssignDefense()
-- All nine Leaf heroes cover two genuine approach points, 3 upper / 6 left, never the objective.
for p=0,8 do
 local lane=p<3 and 5 or 3
 assert(CampaignNearest(p)==nil)
 CampaignBot(p,nil);assert(Hero[p].last.o=='attack' and Hero[p].last.x==CampaignRouteX[lane] and Hero[p].last.y==CampaignRouteY[lane],'Idle defenders attack-move to an approach, not the Hokage')
end
-- Visible waves outside the old 1400 acquisition radius must draw defenders out.
CampaignInvasionWave(0);local wave=CampaignActor[0]
for j=1,2 do CampaignActor[j].hp=0 end
wave.x=GetUnitX(Hero[1])+3000;wave.y=GetUnitY(Hero[1]);World={wave}
assert(CampaignNearest(1)==wave,'Visible distant wave must be intercepted')
StoryMarch[0]=false;StoryShopTripUntil[1]=TimeNow+40
CampaignBot(1,wave);assert(Hero[1].last.o=='attack' and Hero[1].last.target==wave and StoryShopTripUntil[1]==0,'Combat overrides follow and shopping')
StoryMarch[0]=true
-- Invalid or unseen waves must not reveal themselves through scripted targeting.
for _,field in ipairs({'paused','hidden','invisible'})do
 wave[field]=true;assert(CampaignNearest(1)==nil,'Do not chase invalid/hidden/unseen wave: '..field);wave[field]=false
end
wave.hp=0;assert(CampaignNearest(1)==nil);wave.hp=10000
-- Nearby combat remains first priority; critical-health retreat still works.
local close=CreateUnit(10,raw('R00A'),Hero[1].x+100,Hero[1].y,0);World={wave,close}
assert(CampaignNearest(1)==close,'Do not abandon nearby enemies for distant waves')
Hero[1].hp=1900;CampaignBot(1,wave);assert(Hero[1].last.o=='move' and Hero[1].last.x==SpawnX[1] and Hero[1].last.y==SpawnY[1],'Critical retreat is preserved')
Hero[1].hp=10000;World={wave};Hero[1].x=CampaignRouteX[11];Hero[1].y=CampaignRouteY[11];wave.x=Hero[1].x-400;wave.y=Hero[1].y
assert(CampaignNearest(1)==wave);CampaignBot(1,wave);assert(Hero[1].last.target==wave,'Defenders also engage a wave which breaches the Hokage perimeter')
-- Purchases between waves and the attacking-side objective are unchanged.
wave.hp=0;World={};StoryShopsOpen();local shop=StoryShopFor(1)
Hero[1].x=shop.x-800;Hero[1].y=shop.y;StoryBuyAt[1]=TimeNow;StoryShopTripUntil[1]=TimeNow+40
CampaignBot(1,nil);assert(Hero[1].last.o=='move' and Hero[1].last.x==shop.x and Hero[1].last.y==shop.y,'Shopping is allowed between waves')
StoryBuyAt[9]=TimeNow+10;CampaignBot(9,nil);assert(Hero[9].last.o=='attack' and Hero[9].last.x==CampaignTX[12] and Hero[9].last.y==CampaignTY[12],'Sand keeps attacking the village objective')
StoryShopsClose()
print('PASS: nine Leaf heroes split 3 upper/6 left across two source approaches; visible distant waves intercepted before shopping/follow, nearby combat and low-health retreat preserved, hidden/dead/paused waves ignored, breached objective defended, between-wave shopping and Sand attack preserved (mock natives).')
