-- Verify shipped handlers. Native payouts/attribution are replaced for NPC victims only.
for p=0,11 do RosterReset(p)end
CampaignClear();CampaignStage=12;CampaignTransition=false;CampaignFinished=false;TimeNow=14000000;World={}
for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;HeroType[p]=Hero[p].type;Hero[p].hp=10000;Controllers[p]='computer';SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,0)end
CampaignAlliances(2)
local register,addAction,create,oldKilling,oldTrigger,randomNative=TriggerRegisterPlayerUnitEvent,TriggerAddAction,CreateTrigger,GetKillingUnit,GetTriggerUnit,GetRandomInt
local calls=0
function CreateTrigger()calls=calls+1;return {actions={},registrations={}}end
function TriggerAddAction(t,fn)t.actions[#t.actions+1]=fn end
function TriggerRegisterPlayerUnitEvent(t,p,event,filter)t.registrations[#t.registrations+1]={p=p,event=event}end
Invasion44DeathHook=nil;Invasion44Init();local hook=Invasion44DeathHook
assert(#hook.registrations==2 and hook.registrations[1].p==13 and hook.registrations[2].p==15 and #hook.actions==1)
Invasion44Init();assert(Invasion44DeathHook==hook and calls==1,'One persistent death hook; no duplicate rewards from repeated init')
assert(LoadInteger(Invasion44Bounty,raw('c022'),0)==20 and LoadInteger(Invasion44Bounty,raw('c022'),1)==6 and LoadInteger(Invasion44Bounty,raw('c022'),2)==3)
local killer,victim=nil,CreateUnit(13,raw('c022'),0,0,0)
function GetKillingUnit()return killer end;function GetTriggerUnit()return victim end
function GetRandomInt(a,b)return 2 end
function CreateTextTag()return {}end
function SetTextTagText(t,s,size)t.text=s end
function SetTextTagPosUnit()end;function SetTextTagColor()end;function SetTextTagVelocity()end;function SetTextTagPermanent()end;function SetTextTagLifespan()end;function SetTextTagFadepoint()end;function SetTextTagVisibility()end
-- Activate the real stage: NPC victims never give native bounty, hero-owned victims unchanged.
CampaignLeader=0;CampaignStartPlay();assert(CampaignBountyActive)
for p=0,15 do assert(GetPlayerState(p,PLAYER_STATE_GIVES_BOUNTY)==((p==13 or p==15)and 0 or 1))end
killer=CreateUnit(15,raw('c010'),0,0,0)
for n=1,100 do hook.actions[1]()end
for p=0,11 do assert(GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==0 and Invasion44Earned[p]==0,'Army kills must never enrich any hero')end
-- Even an ordinary ninja accidentally owned by a hero must not qualify.
killer=CreateUnit(9,raw('c010'),0,0,0);hook.actions[1]();assert(GetPlayerState(9,PLAYER_STATE_RESOURCE_GOLD)==0)
killer=Hero[9];hook.actions[1]();assert(GetPlayerState(9,PLAYER_STATE_RESOURCE_GOLD)==32 and Invasion44Kills[9]==1)
for _,p in ipairs({10,11})do killer=Hero[p];hook.actions[1]();assert(GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==32)end
-- Pets, clones and actual technical spell casters still credit the real owner.
local pet=CreateUnit(10,raw('rc01'),0,0,0);Companion[30]=pet;killer=pet;hook.actions[1]();assert(GetPlayerState(10,PLAYER_STATE_RESOURCE_GOLD)==64)
local clone=CreateUnit(9,raw('R009'),0,0,0);clone.illusion=true;killer=clone;hook.actions[1]();assert(GetPlayerState(9,PLAYER_STATE_RESOURCE_GOLD)==64)
killer=CreateUnit(11,raw('r40w'),0,0,0);hook.actions[1]();assert(GetPlayerState(11,PLAYER_STATE_RESOURCE_GOLD)==64)
-- Symmetric Leaf behavior, no allied kill/illusion payout, no work outside active invasion.
victim=CreateUnit(15,raw('c010'),0,0,0);killer=Hero[0];hook.actions[1]();assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==32)
killer=CreateUnit(13,raw('c022'),0,0,0);hook.actions[1]();assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==32)
killer=Hero[9];local sandGold=GetPlayerState(9,PLAYER_STATE_RESOURCE_GOLD);hook.actions[1]();assert(GetPlayerState(9,PLAYER_STATE_RESOURCE_GOLD)==sandGold,'Friendly kills cannot pay')
killer=Hero[0];victim.illusion=true;hook.actions[1]();victim.illusion=false;assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==32)
for _,guard in ipairs({'transition','finished','otherstage'})do
 CampaignTransition=guard=='transition';CampaignFinished=guard=='finished';CampaignStage=guard=='otherstage'and 13 or 12
 hook.actions[1]();assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==32)
end
CampaignStage=12;CampaignFinished=false;CampaignTransition=false
-- Exactly preserve six individual d3 draws:26 minimum and38 maximum.
function GetRandomInt(a,b)return a end;hook.actions[1]();assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==58)
function GetRandomInt(a,b)return b end;hook.actions[1]();assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==96)
-- Exercise the real host-only diagnostic chat dispatch without changing balances.
local playerChat,messageChat,unitName,displayText=GetTriggerPlayer,GetEventPlayerChatString,GetUnitName,DisplayTimedTextToPlayer
local sender=0;local lines=0
function GetTriggerPlayer()return sender end
function GetEventPlayerChatString()return '-goldcheck' end
function GetUnitName(u)return 'Hero '..tostring(u.owner)end
function DisplayTimedTextToPlayer(p,x,y,d,text)lines=lines+1 end
Controllers[0]='human';local beforeInspect=GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)
FoundationChat();assert(lines==13 and GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==beforeInspect,'Real diagnostic is read-only and reports12 heroes')
sender=9;lines=0;FoundationChat();assert(lines==1,'Only first human can inspect enemy balances')
GetTriggerPlayer,GetEventPlayerChatString,GetUnitName,DisplayTimedTextToPlayer=playerChat,messageChat,unitName,displayText
CampaignClear();assert(not CampaignBountyActive and GetPlayerState(13,PLAYER_STATE_GIVES_BOUNTY)==0 and GetPlayerState(15,PLAYER_STATE_GIVES_BOUNTY)==0)
-- Each lane independently repeats3,3,4; the fourth reserved formation slot stays clear.
CampaignStage=12;CampaignTransition=false;CampaignFinished=false;CampaignActor={};CampaignActorType={};CampaignCount=0
for lane=0,7 do Invasion44Wave[lane]=0 end
for wave=1,6 do
 for lane=0,7 do
  local n=CampaignCount;CampaignInvasionWave(lane);local expected=wave%3==0 and 4 or 3
  assert(CampaignCount==n+expected and Invasion44Wave[lane]==wave)
  for k=0,expected-1 do local u=CampaignActor[n+k];assert(u.owner==15 and u.x==CampaignWaveSpawnX[lane*4+k] and u.y==CampaignWaveSpawnY[lane*4+k])end
 end
end
local w=Invasion44Wave[0];CampaignTransition=true;CampaignInvasionWave(0);assert(Invasion44Wave[0]==w)
TriggerRegisterPlayerUnitEvent,TriggerAddAction,CreateTrigger,GetKillingUnit,GetTriggerUnit,GetRandomInt=register,addAction,create,oldKilling,oldTrigger,randomNative
CampaignClear();CampaignTransition=false;CampaignStage=0
print('PASS: real NPC-only death hook/no native double bounty/100 army kills pay no hero; all three Sand heroes/Leaf/pets/clones/skills paid real source dice26..38; phase/illusion/ownership guards; independent six-cycle3/3/4 waves and safe spawn positions (native mocks).')
