-- Execute shipped trap/item/service decisions; not a renderer or native combat playtest.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
UNIT_TYPE_FLYING='flying';DAMAGE_TYPE_NORMAL='physical'
CampaignAlliances(0);NoteClearAll();TimeNow=500000
Caster=CreateUnit(0,raw('R000'),0,0,0);Spell=raw('Lexp');AimX=200;AimY=0
local timers=CreatedTimers;local hits=#Hits;NoteCast();local slot=(NoteCursor+127)%128;local actor=NoteActor[slot]
assert(actor and actor.owner==0 and actor.x==200 and actor.y==0 and CreatedTimers==timers,'Point cast places the real imported trap without a cast timer')
local center=CreateUnit(12,raw('re06'),250,0,0);local edge=CreateUnit(12,raw('re06'),450,0,0)
local ally=CreateUnit(0,raw('R000'),200,0,0);local flying=CreateUnit(12,raw('re06'),200,0,0);flying.flying=true
local invul=CreateUnit(12,raw('re06'),200,0,0);invul.abilities[raw('Avul')]=1
local hidden=CreateUnit(12,raw('re06'),200,0,0);hidden.hidden=true
World={center,edge,ally,flying,invul,hidden};local hp=center.hp;NoteTick();assert(center.hp==hp and NoteActor[slot]==actor,'Arming is not an immediate invisible hit')
TimeNow=TimeNow+1.5;NoteTick();assert(center.hp==hp-400 and edge.hp==hp-300 and ally.hp==hp and flying.hp==hp and invul.hp==hp and hidden.hp==hp)
assert(actor.removed and not NoteActor[slot] and #Hits==hits+2,'One explosion, enemies only, no native mine duplicate')
NoteTick();assert(#Hits==hits+2)
World={};NoteCast();slot=(NoteCursor+127)%128;actor=NoteActor[slot];TimeNow=TimeNow+181;NoteTick();assert(actor.removed and not NoteActor[slot],'Idle traps expire and release their unit')
NoteCast();slot=(NoteCursor+127)%128;actor=NoteActor[slot];actor.hp=0;NoteTick();assert(actor.removed and not NoteActor[slot],'Disarmed trap cannot explode later')
for n=1,260 do NoteCast()end
local active=0;for n=0,127 do if NoteActor[n]then active=active+1 end end;assert(active==128 and CreatedTimers==timers,'Trap state is bounded during repeated casts')
NoteClearAll();for n=0,127 do assert(not NoteActor[n])end
-- Bots place a trap between themselves and an enemy, within the 300 cast range.
Hero[0]=Caster;HeroRole[0]=0;Hero[0].hp=10000;Hero[0].mana=1000;Hero[0].items={[0]={type=raw('Nnot')}};BotUseItemAt[0]=0
center.x=500;center.y=0;assert(StoryLootBot(0,center));assert(Hero[0].usedPoint[1]==250 and Hero[0].usedPoint[2]==0)
-- The four original shops and fountains are visible to all occupied heroes in Konoha.
CampaignStage=12;CampaignTransition=false;Hero={};HeroRole={}
for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,6096,-8528,0);HeroRole[p]=p end
CampaignAlliances(2);StoryShopsOpen();CampaignFountainsOpen()
local before=FogCreated-FogDestroyed;CampaignVillageLandmarksOpen();assert(FogCreated-FogDestroyed==before+96)
for p=0,11 do for j=0,7 do assert(VillageLandmarkFog[p*8+j]and VillageLandmarkFog[p*8+j].active)end end
for j=0,3 do assert(StoryShop[j]and StoryShop[j].owner==14,'Supply stays neutral to defenders and attackers')end
StoryCommand(0,'-shop');assert(Selected==StoryShopFor(0))
StoryCommand(0,'-fountain');assert(Selected==StoryFountainFor(0))
StoryCommand(9,'-shop');assert(Selected==StoryShopFor(9),'Sand can also access supply')
StoryCommand(9,'-fountain');assert(Selected==StoryFountainFor(9))
CampaignVillageLandmarksOpen();assert(FogCreated-FogDestroyed==before+96,'Repeated setup replaces old fog handles')
CampaignVillageLandmarksClose();assert(FogCreated-FogDestroyed==before)
StoryShopsClose();CampaignStage=13;assert(not StoryShopFor(0)and not StoryFountainFor(0))
print('PASS: point-target exploding notes arm, damage enemies exactly once, spare allies/air/invulnerability, expire/disarm and remain bounded; bot point use; four neutral shops/fountains and 96 bounded village views, both sides and camera commands (mock natives).')
