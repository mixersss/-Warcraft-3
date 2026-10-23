-- Verify real shipped scheduling rather than pretending to run the native cooldown engine.
for p=0,11 do RosterReset(p)end
TimeNow=5000000;World={};CampaignTransition=false
local victim=CreateUnit(12,123,400,0,0);local lee=Hero[3];lee.hp=10000;lee.x=0;lee.y=0;lee.paused=false
local position=SetUnitPosition;local effect=false
function SetUnitPosition(u,x,y)assert(not effect,'Never interrupt native Firebolt inside SPELL_EFFECT');position(u,x,y)end
effect=true;Source35Apply(3,16,1,victim);VisualApply(3,16,1,victim);effect=false
assert(lee.x==0 and Kick35Caster[3]==lee and Kick35Target[3]==victim)
TimeNow=TimeNow+.5;Source35Tick();assert(lee.x==320 and not Kick35Caster[3])
Source35Apply(3,16,1,victim);local at=lee.x;victim.hp=0;TimeNow=TimeNow+.5;Source35Tick();assert(lee.x==at and not Kick35Target[3]);victim.hp=10000
Source35Apply(3,16,1,victim);Source35Clear(3);assert(not Kick35Caster[3] and Kick35At[3]==0)
Source35Apply(3,16,1,victim);Hero[3]=CreateUnit(3,999,100,0,0);TimeNow=TimeNow+.5;Source35Tick();assert(Hero[3].x==100 and not Kick35Caster[3]);Hero[3]=lee
SetUnitPosition=position
-- Native powerup purchases consume real125 gold and apply+6 without needing inventory space.
CampaignStage=12;CampaignTransition=false;CampaignFinished=false;StoryShopsOpen();World={}
local expected={7,7,8,9,9,9,8,9,9,8,8,9}
for p=0,11 do
 HeroRole[p]=p;local h=Hero[p];h.hp=10000;h.maxLife=10000;h.paused=false;h.items={};h.x=StoryShop[0].x;h.y=StoryShop[0].y
 for slot=0,5 do h.items[slot]={type=raw('Nlca'),owned=true}end
 local first=h.items[0];StoryBuyAt[p]=0;StoryBought[p]=0;SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,250)
 assert(StoryChooseItem(p)==expected[p+1] and StoryCanCarryChoice(p,expected[p+1]))
 local stat=expected[p+1]==7 and 'str' or (expected[p+1]==8 and 'int' or 'agi');local before=h[stat]or 0
 StoryBuy(p);assert(GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==125 and StoryBought[p]==1 and h[stat]==before+6 and h.items[0]==first)
 StoryBuy(p);assert(GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==125,'Respect4s shopping interval')
 TimeNow=TimeNow+5;StoryBuy(p);assert(GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==0 and h[stat]==before+12)
 TimeNow=TimeNow+5;StoryBuy(p);assert(GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==0 and StoryBought[p]==2,'Never grant unaffordable powerups')
 h.items={};StoryBought[p]=3;assert(StoryChooseItem(p)==expected[p+1],'Every fourth successful purchase prioritizes main stat')
end
local p=3;local h=Hero[p];h.items={};for slot=0,5 do h.items[slot]={type=raw('Nlca'),owned=true}end
CampaignPermanentDead[p]=false;CampaignClonePending[p]=false;StoryMarch[1]=true;StoryRetreat[1]=false;StoryBuyAt[p]=0;StoryShopTripUntil[p]=0;SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,125)
CampaignBot(p,nil);assert(GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==0,'Full inventory must not suppress a bot shopping trip')
CampaignStage=9;StoryBuyAt[p]=0;SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,125);StoryBuy(p);assert(GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==125,'Arena still has no purchases')
StoryShopsClose()
print('PASS: delayed Lee kick without native-effect interruption/dead target/replacement/scene cleanup; all12 roles buy correct+6 stat scrolls with six carried items, real prices, cooldown, finite gold, native event accounting, full-inventory shopping trips and arena restriction (mock natives).')
