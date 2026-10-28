-- Actual stock sale + native post-event decrement; human clicks and bot bulk purchases.
CampaignStage=12;CampaignTransition=false;CampaignFinished=false;TimeNow=32000000
StoryShopsOpen();local beforeNative=IssueNeutralImmediateOrderById
function IssueNeutralImmediateOrderById(p,shop,id)
 local book=id==raw('Nsht')or id==raw('Nsta')or id==raw('Nsch')
 if book and(shop.stock[id]or 0)<=0 then return false end
 local ok=beforeNative(p,shop,id)
 -- Deliberately decrement AFTER the sale event: refilling in the event alone would fail.
 if ok and book then shop.stock[id]=shop.stock[id]-1 end
 return ok
end
local p=0;HeroRole[p]=0;Hero[p]=CreateUnit(p,raw('R000'),StoryShopX[0],StoryShopY[0],0)
Controllers[p]='human';StatBought50[p]=0;SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,125*200)
local allocated=CreatedTimers
for n=1,200 do
 local id=StoryItem[StoryChooseItem(p)];IssueNeutralTargetOrder(p,StoryShop[0],'neutralinteract',Hero[p]);assert(IssueNeutralImmediateOrderById(p,StoryShop[0],id))
 assert(StoryShop[0].stock[id]==0);assert(Scroll57Clock.callback==Scroll57Flush);Scroll57Clock.callback();assert(StoryShop[0].stock[id]==1)
end
assert(StatBought50[p]==200 and GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==0 and CreatedTimers<=allocated+1,'200 real paid human purchases, one shared refill timer')
SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,1000);StoryBuyAt[p]=0;StoryBuy(p);assert(GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==0 and StatBought50[p]==208,'Eight consecutive native purchases can refill after each completed order')
local shop=StoryShop[0];Scroll57Pending[0]=true;StoryShopsClose();Scroll57Flush();assert(StoryShop[0]==nil and shop.removed,'Pending refill cannot recreate a closed shop')
IssueNeutralImmediateOrderById=beforeNative
print('PASS: unlimited human/button and bot stock after native decrement,200+8 actual paid buys, one shared timer, closed-shop safety')
-- Companions receive independent orders even while their hero repeatedly casts.
CampaignStage=31;CampaignTransition=false;CampaignFinished=false;TimeNow=33000000;World={}
local oldNearest=CampaignNearest;local foe=CreateUnit(15,raw('c010'),100,0,0)
function CampaignNearest()return foe end
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;Controllers[p]='computer';StoryStage[StoryTeam(p)]=31;StoryRetreat[StoryTeam(p)]=false;Pet57OrderAt[p]=0;BotNextCast[p]=TimeNow+99
end
for _,p in ipairs({7,10})do
 for k=0,(p==10 and 2 or 0)do Companion[p*3+k]=CreateUnit(p,raw('ra01')+k,10,0,0);PetTrapVictim[p*3+k]=nil end
 Pet57Player=p;Companion57Player()
 for k=0,(p==10 and 2 or 0)do assert(Companion[p*3+k].last.target==foe and Companion[p*3+k].last.o=='attack')end
end
Hero[10].x=1200;TimeNow=TimeNow+1;Pet57Player=10;Companion57Player();for k=0,2 do assert(Companion[30+k].last.o=='follow'and Companion[30+k].last.target==Hero[10],'All three puppets regroup instead of being abandoned')end
Controllers[10]='human';local pet=Companion[30];pet.last={o='manual'};TimeNow=TimeNow+1;Companion57Player();assert(pet.last.o=='manual','Human pet orders are not overwritten')
Controllers[10]='computer';Hero[10].x=0;Hero[10].abilities[raw('RA01')]=1;Hero[10].abilities[raw('RA03')]=1;Hero[10].abilities[raw('RA04')]=1;Hero[10].mana=1000
Companion[30]=CreateUnit(10,raw('rk01'),0,0,0);Companion[31]=CreateUnit(10,raw('rk04'),0,0,0);Companion[32]=nil
Pet57OrderAt[10]=0;BotNextCast[10]=0;VisualChannelUntil[10]=0;JumpUnit[10]=nil;JumpQueued[10]=nil;TimeNow=TimeNow+2;Companion57Player();assert(Hero[10].last.o=='inferno','Missing learned Sansho is proactively cast as third puppet')
Hero[10].abilities[raw('RA04')]=nil;Hero[10].last={o='none'};Pet57OrderAt[10]=0;BotNextCast[10]=0;TimeNow=TimeNow+2;Companion57Player();assert(Hero[10].last.o=='none','No free third summon before learning its35-level skill')
HeroRole[2]=10;Pet57Player=2;Pet57OrderAt[2]=0;BotNextCast[2]=TimeNow+99
for k=0,2 do Companion[6+k]=CreateUnit(2,raw('rk01')+k,10,0,0);PetTrapVictim[6+k]=nil end
Companion57Player();for k=0,2 do assert(Companion[6+k].last.target==foe,'Companion control follows hero role after swapping player slots')end
CampaignNearest=oldNearest
print('PASS: Kiba and all3 Kankuro companions act while hero casts, regroup, respect human control, proactively summon learned third puppet with real mana')
-- Actual tournament -> invasion setup/deployment -> full1500s timer; simulate an aborted setup worker.
CampaignStage=11;CampaignTransition=false;CampaignFinished=false;CampaignFinalActive=false;CampaignBracket=false;CampaignQueueCount=0;CampaignQueueCursor=0;CampaignDuelA=-1;CampaignDuelB=-1;CampaignWinnerCount=0
for p=0,11 do HeroRole[p]=p;CampaignPermanentDead[p]=false;Hero[p].dead=false;Hero[p].hp=10000 end
CampaignDuelTick();assert(CampaignQueued==12 and CampaignTransition and not Village57Ready)
local nativeExecute=ExecuteFunc;local failScene=true
function ExecuteFunc(name)if name=='Scene57Build'and failScene then return end;nativeExecute(name)end
TimeNow=TimeNow+9;CampaignTick();assert(CampaignStage==12 and CampaignTransition and not Village57Ready,'Missing objective cannot be interpreted as a lost invasion')
TimeNow=TimeNow+1;CampaignTick();assert(CampaignStage==12 and CampaignTransition)
failScene=false
for n=1,100 do TimeNow=TimeNow+.5;CampaignTick();if not CampaignTransition then break end end
ExecuteFunc=nativeExecute
assert(CampaignStage==12 and not CampaignTransition and Village57Ready and FoundationAlive(CampaignActor[0])and CampaignActorType[0]==0 and CampaignDeployCursor>=242)
assert(not CampaignActor[0].invulnerable and CampaignEndAt==CampaignStartAt+1500,'Preparation immunity ends; full invasion timer starts only on actual readiness')
TimeNow=CampaignStartAt+5;CampaignTick();assert(CampaignStage==12 and not CampaignTransition and CampaignQueued==12,'Normal invasion is not skipped after arena')
CampaignActor[0].hp=0;CampaignActor[0].dead=true;CampaignTick();assert(CampaignQueued==13 and CampaignTransition,'Real death after battle starts still advances original story')
print('PASS: actual tournament->invasion even after interrupted scene build, full defenders/deployment/readiness1500s, no instant skip; real objective defeat still advances13')
