-- Actual shipped logic; native spell/powerup execution still requires Warcraft.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
TimeNow=2000000;CampaignStage=9;CampaignTransition=false;World={}
for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);Hero[p].level=40;HeroRole[p]=p;HeroType[p]=Hero[p].type;Hero[p].hp=10000;Hero[p].maxLife=10000;Hero[p].mana=1000;Hero[p].maxMana=1000 end
-- Smoke is now the source point projectile plus delayed native microstun helper.
Hero[7].x=0;Hero[7].y=0;RosterReset(7)
local foe=CreateUnit(12,0,100,0,0);local ally=CreateUnit(8,0,100,0,0);local far=CreateUnit(12,0,500,0,0)
World={foe,ally,far};AimX=100;AimY=0;cast(7,PlayableSkill[36],1,nil)
assert(Source40SmokeAt[7]==TimeNow+.9 and Source40SmokeX[7]==100)
TimeNow=TimeNow+.91;Source40Cursor=7;Source40PlayerTick()
local smoke=Source40Helpers[7][1];assert(smoke and smoke.type==raw('r40c')and smoke.last.o=='stomp'and GetUnitAbilityLevel(smoke,raw('R40c'))==1)
Source40Clear(7)
-- Arena: emergency only, once per bout, attack instead of repeat escape movement.
local h=Hero[0];h.abilities[raw('Rlog')]=1;h.hp=3000;LogReadyAt[0]=0;LogUntil[0]=0;LogArenaUsed[0]=false;VisualChannelUntil[0]=0;ComboLeft[0]=0
assert(not CommonLogBot(0,foe),'30% HP is not an arena emergency')
h.hp=1500;LogLastDamageAt[0]=TimeNow;LogBotNextAt[0]=0;assert(CommonLogBot(0,foe)and LogArenaUsed[0]and h.last.o=='windwalk')
CommonLogEffect(0);TimeNow=TimeNow+1;assert(CommonLogBot(0,foe)and h.last.o=='attack'and h.last.target==foe,'No repeated movement away under invisibility')
h.order=OrderId('attack');local ongoing=h.last;assert(CommonLogBot(0,foe)and h.last==ongoing,'Do not reset an ongoing attack');h.order=0
TimeNow=TimeNow+30;assert(not CommonLogBot(0,foe),'No second escape after cooldown')
CampaignResetFighter(0);LogLastDamageAt[0]=TimeNow;assert(not LogArenaUsed[0]and CommonLogBot(0,foe),'Next bout has its own emergency use')
CommonLogClear(0);CampaignStage=0;LogReadyAt[0]=0;h.hp=3000;assert(not CommonLogBot(0,foe),'30% HP alone no longer triggers escape outside arenas')
-- One native level per actual victory; neither loser nor next idle tick gets it.
CommonLogClear(0);CampaignStage=9;CampaignTransition=false;CampaignFinalActive=false;CampaignDuelLive=true;CampaignDuelA=0;CampaignDuelB=3;CampaignWinnerCount=0;CampaignBracket=false;CampaignQueueCount=0;CampaignQueueCursor=0
h.hp=10000;h.level=40;Hero[3].hp=0;Hero[3].level=40
CampaignDuelTick();assert(h.level==41 and Hero[3].level==40 and CampaignDuelA==-1)
CampaignDuelTick();assert(h.level==41,'No duplicate reward on next tick')
CampaignStage=11;CampaignTransition=false;CampaignFinalActive=true;CampaignDuelLive=true;h.hp=10000;Hero[3].hp=0;Hero[6].hp=0
for i,p in ipairs({0,3,6})do CampaignFinalPlayer[i-1]=p;CampaignEliminated[p]=false end
CampaignFinalTick();assert(h.level==42 and CampaignChampion==0 and not CampaignFinalActive,'Three-way champion gets one victory level')
h.level=60;CampaignArenaReward(0);assert(h.level==60,'Original level60 cap preserved')
-- Spatial item query sees actual ground powerups, including full inventories.
CampaignStage=0;CampaignTransition=false;StoryStage[0]=1;StoryRetreat[0]=false;ExamTowerOpen=false
h.x=-14000;h.y=14000;h.hp=10000;h.items={};for i=0,5 do h.items[i]={type=raw('Nlga'),owned=true}end
local function scroll(id,x,flags)local it={type=raw(id),x=h.x+x,y=h.y,hp=100,owned=false};for k,v in pairs(flags or{})do it[k]=v end;return it end
local str=scroll('Nsht',100);local agi=scroll('Nsta',200);local int=scroll('Nsch',300)
GroundStatItems={scroll('Eshe',1),scroll('Nsht',10,{hidden=true}),scroll('Nsta',20,{owned=true}),scroll('Nsch',900),str,agi,int}
assert(StoryStatLootBot(0,nil)and h.last.o=='smart'and h.last.target==str,'Pickup works with all6 slots occupied')
str.owned=true;assert(StoryStatLootBot(0,nil)and h.last.target==agi);agi.owned=true;assert(StoryStatLootBot(0,nil)and h.last.target==int)
local rect=StatLootRect;for n=1,100 do StoryStatLootBot(0,nil)end;assert(StatLootRect==rect,'One persistent rect, no per-scan handles')
VisualChannelUntil[0]=TimeNow+2;assert(not StoryStatLootBot(0,nil));VisualChannelUntil[0]=0;ComboLeft[0]=1;assert(not StoryStatLootBot(0,nil));ComboLeft[0]=0
foe.x=h.x+100;foe.y=h.y;foe.hp=10000;assert(not StoryStatLootBot(0,foe),'Combat wins over loot')
foe.x=h.x+2000;assert(StoryStatLootBot(0,foe),'A distant next objective does not suppress nearby pickup')
h.hp=2000;assert(not StoryStatLootBot(0,nil));h.hp=10000
CampaignStage=9;assert(not StoryStatLootBot(0,nil));CampaignStage=0
StoryStage[0]=7;ExamTowerOpen=true;assert(not StoryStatLootBot(0,nil),'Tower deadline wins over loot')
GroundStatItems={};StoryStage[0]=1;ExamTowerOpen=false
print('PASS: smoke microstun, arena emergency once per bout/no flee loop, one level per duel/final victory; visible nearby stat-scroll native pickup with6 slots, combat/quest priorities and one reused rect (mock natives).')
