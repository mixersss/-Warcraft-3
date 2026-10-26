-- Execute the shipped death callback; native XP sharing is deliberately not mocked as proof of engine combat.
CampaignClear();CampaignStage=12;CampaignTransition=false;CampaignFinished=false;CampaignBountyActive=true
local oldXP,oldTrigger,oldKilling=AddHeroXP,GetTriggerUnit,GetKillingUnit
local grants={};local victim=nil;local killer=nil
function AddHeroXP(u,n,fx)grants[u]=(grants[u]or 0)+n end
function GetTriggerUnit()return victim end
function GetKillingUnit()return killer end
for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;Controllers[p]='computer';SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,0)end
-- Test role-based recipients outside original Sand slots.
HeroRole[2],HeroRole[9]=HeroRole[9],HeroRole[2]
HeroRole[5],HeroRole[10]=HeroRole[10],HeroRole[5]
HeroRole[8],HeroRole[11]=HeroRole[11],HeroRole[8]
CampaignAlliances(2)
killer=CreateUnit(15,raw('c010'),0,0,0)
for _,kind in ipairs({'c011','c022'})do victim=CreateUnit(13,raw(kind),0,0,0);Invasion44Death()end
for p=0,11 do
 assert((grants[Hero[p]]or 0)==((p==2 or p==5 or p==8)and 60 or 0),'Each Sand role gets30 per eligible death regardless of player slot')
 assert(GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==0,'Army still never transfers gold to heroes')
end
local function total()local sum=0;for _,v in pairs(grants)do sum=sum+v end;return sum end
local before=total()
for _,kind in ipairs({'c020','c010','c00F','c000','R000'})do victim=CreateUnit(13,raw(kind),0,0,0);Invasion44Death()end
victim=CreateUnit(15,raw('c011'),0,0,0);Invasion44Death()
victim=CreateUnit(13,raw('c011'),0,0,0);victim.illusion=true;Invasion44Death();victim.illusion=false
for _,state in ipairs({'transition','finished','otherstage','inactive'})do
 CampaignTransition=state=='transition';CampaignFinished=state=='finished';CampaignStage=state=='otherstage'and 13 or 12;CampaignBountyActive=state~='inactive'
 Invasion44Death()
end
assert(total()==before,'No XP for medics/attackers/heroes/illusions/wrong owner or inactive scene')
CampaignStage=12;CampaignTransition=false;CampaignFinished=false;CampaignBountyActive=true
-- A hero last hit pays existing gold exactly once, and XP is not duplicated by it.
killer=Hero[2];Invasion44Death();assert(grants[Hero[2]]==90 and grants[Hero[5]]==90 and grants[Hero[8]]==90)
assert(GetPlayerState(2,PLAYER_STATE_RESOURCE_GOLD)>=26 and GetPlayerState(2,PLAYER_STATE_RESOURCE_GOLD)<=38)
-- Missing/inactive heroes are skipped without blocking other teammates.
Hero[5]=nil;local slot=GetPlayerSlotState
function GetPlayerSlotState(p)if p==8 then return 'empty'end return PLAYER_SLOT_STATE_PLAYING end
killer=nil;Invasion44Death();assert(grants[Hero[2]]==120 and grants[Hero[8]]==90)
GetPlayerSlotState=slot
AddHeroXP,GetTriggerUnit,GetKillingUnit=oldXP,oldTrigger,oldKilling
CampaignClear()
print('PASS: original3.5 invasion30XP for each role-bound Sand hero per Leaf/ANBU death, no army gold, no extra last-hit XP or invalid-scene rewards')
