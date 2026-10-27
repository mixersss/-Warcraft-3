CampaignClear();CampaignStage=0;CampaignFinished=false;CampaignTransition=false
for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;Controllers[p]='computer';SetPlayerHandicapXP(p,1)end
Experience49Applied=false;Experience49Init();Experience49Init()
for p=0,11 do assert(math.abs(GetPlayerHandicapXP(p)-1.7)<.00001,'Global70% XP for every player once')end
CampaignStage=12;CampaignStartPlay();CampaignClear()
for p=0,11 do assert(math.abs(GetPlayerHandicapXP(p)-1.7)<.00001,'No double invasion bonus and no removal of global rate on exit')end
-- Fresh actual damage is required, with danger assessment rather than just cooldown/low HP.
CampaignStage=12;TimeNow=19000000;local h=Hero[0];h.maxLife=10000;h.hp=10000;h.mana=1000;h.abilities[raw('Rlog')]=1
local foe=CreateUnit(15,raw('c010'),100,0,0);foe.hp=10000;foe.maxLife=10000
LogReadyAt[0]=0;LogBotNextAt[0]=0;LogUntil[0]=0;LogLastDamageAt[0]=0;VisualChannelUntil[0]=0;ComboLeft[0]=0
CommonLogTick();h.hp=2000;assert(not CommonLogBot(0,foe),'Low HP alone is not sufficient')
TimeNow=TimeNow+.5;CommonLogTick();assert(LogLastDamageAt[0]==TimeNow and CommonLogBot(0,foe),'Observed recent damage and strong close foe justify escape')
TimeNow=TimeNow+3;assert(not CommonLogBot(0,foe),'Old damage is not an emergency')
LogLastDamageAt[0]=TimeNow;foe.hp=100;assert(not CommonLogBot(0,foe),'Finish a weaker enemy instead of fleeing')
foe.hp=10000;CampaignStage=9;LogArenaUsed[0]=false;h.hp=1500;assert(CommonLogBot(0,foe),'Arena emergency still supported')
CommonLogEffect(0);assert(LogBotNextAt[0]==TimeNow+45 and LogReadyAt[0]==TimeNow+22,'Bot restraint never lengthens human/native cooldown')
CommonLogClear(0);TimeNow=TimeNow+23;LogLastDamageAt[0]=TimeNow;CampaignStage=12;assert(not CommonLogBot(0,foe),'No bot repeat every native cooldown')
local getLocal,color=GetLocalPlayer,SetUnitVertexColor;local writes=0
function SetUnitVertexColor(u,r,g,b,a)writes=writes+1;assert(u==h and a==255)end
CampaignStage=9;function GetLocalPlayer()return 1 end;CommonLogOwnerView(0);assert(writes==0,'Never color/reveal enemy on another client')
function GetLocalPlayer()return 0 end;CommonLogOwnerView(0);assert(writes==1,'Owner gets full source alpha; native invisibility remains')
GetLocalPlayer,SetUnitVertexColor=getLocal,color
-- Cash bonus belongs to a defending hero's personal/pet/technique last hit, never army or Sand.
CampaignStage=12;CampaignTransition=false;CampaignFinished=false;CampaignBountyActive=true;CampaignAlliances(2)
local trigger,killing,random=GetTriggerUnit,GetKillingUnit,GetRandomInt;local killer=Hero[0];local victim=CreateUnit(15,raw('c010'),0,0,0)
function GetTriggerUnit()return victim end;function GetKillingUnit()return killer end;function GetRandomInt(a,b)return 2 end
for p=0,11 do SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,0)end
Invasion44Death();assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==52,'32 original average+20 defending ninja bonus')
killer=CreateUnit(13,raw('c011'),0,0,0);Invasion44Death();assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==52,'Ordinary allied army earns no hero bonus')
killer=Hero[9];victim=CreateUnit(13,raw('c011'),0,0,0);Invasion44Death();assert(GetPlayerState(9,PLAYER_STATE_RESOURCE_GOLD)==32,'Sand bounty remains original')
GetTriggerUnit,GetKillingUnit,GetRandomInt=trigger,killing,random
for _,p in ipairs({0,1,2,9,10,11})do StatBought50[p]=0;StoryBought[p]=3;assert(StoryChooseItem(p)==StoryStatChoice(p));StoryBought[p]=5;assert(StoryChooseItem(p)==StoryStatChoice(p),'Every second purchase after initial gear is a stat scroll')end
local create,invul=CreateDestructable,SetDestructableInvulnerable;local walls={}
function CreateDestructable(kind,x,y,angle,scale,variation)local d={kind=kind,x=x,y=y};walls[#walls+1]=d;return d end
function SetDestructableInvulnerable(d,value)d.invulnerable=value end
Gates49Built=false;Gates49Init();Gates49Init();assert(#walls==7,'Seven persistent visible barricades created once')
for _,d in ipairs(walls)do assert(d.kind==raw('LTba')and d.invulnerable and d.y==-12800)end
CreateDestructable,SetDestructableInvulnerable=create,invul
CampaignClear()
print('PASS: global70% XP/no double invasion bonus, tactical invisibility and owner-only color, defender20gold without army transfer, frequent role-based scroll selection, idempotent visible invulnerable north barricades (native mocks)')
