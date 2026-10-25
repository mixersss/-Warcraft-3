-- A corpse with positive HP is still engine-dead: reproduce the reported ghost.
for p=0,11 do RosterReset(p)end
CampaignStage=12;CampaignTransition=false;CampaignFinished=false;TimeNow=9500000;CampaignAlliances(2)
local p=7;HeroRole[p]=1;HeroRole[1]=7
local s=CreateUnit(p,raw('Rsfm'),CampaignX[12],CampaignY[12],0);Hero[p]=s;HeroType[p]=raw('R001')
s.hp=475;s.maxLife=2000;s.dead=true;s.paused=true;s.alpha=60;s.level=45;s.xp=9999;s.mana=300;s.maxMana=900
s.items={[0]={type=123,owned=true}};local item=s.items[0]
s.abilities[raw('Aloc')]=1;s.abilities[raw('Apiv')]=1;s.abilities[raw('Avul')]=1;s.abilities[raw('BOwk')]=1
CampaignPermanentDead[p]=false;StoryRevive[p]=0;NPCCooldowns=InitHashtable()
assert(not FoundationAlive(s),'Positive corpse HP must never imply alive')
InvasionHeroVisibility();local due=StoryRevive[p];assert(due==TimeNow+20 and s.dead and s.hp==475,'Queue the normal death timer, not a cosmetic corpse recovery')
TimeNow=TimeNow+5;InvasionHeroVisibility();InvasionFixSasuke(0);assert(StoryRevive[p]==due and s.dead and s.hp==475,'Repeated fix does not postpone or shortcut revival')
-- Source heal setters reject engine-dead units, including a transparent corpse.
local oldLife=SetWidgetLife
local writes=0
function SetWidgetLife(u,hp)writes=writes+1;u.hp=hp end
function SetUnitLifePercentBJ(u,percent)SetWidgetLife(u,u.maxLife*percent/100)end
InvasionSourceLife(s,1000,'late-heal');InvasionSourceLifePercent(s,80,'late-percent')
assert(writes==0 and s.hp==475 and SasukeCorpseHealsBlocked[p]==2)
local living=CreateUnit(7,123,s.x,s.y,0);living.hp=100;living.maxLife=1000
InvasionSourceLife(living,175,'normal');assert(living.hp==175 and writes==1)
InvasionSourceLifePercent(living,50,'normal-percent');assert(living.hp==500 and writes==2)
-- Source drain predicates must stop before spending mana/healing dead targets.
OrigNPC_OR[0]=living;OrigNPC_OR[1]=living;OrigNPC_RR[0]=s;OrigNPC_RR[1]=s
for _,fn in ipairs({OrigNPC_A2X,OrigNPC_A3X,OrigNPC_NBX,OrigNPC_NCX,OrigNPC_NHX,OrigNPC_NJX,OrigNPC_NPX,OrigNPC_NQX})do assert(not fn())end
SetWidgetLife=oldLife
-- The actual StoryTick branch verifies native revival and retries a failed call.
local campaignTick,chapterTick,hudTick,mentorThink=CampaignTick,NextChapterTick,HUDTick,StoryMentorThink
function CampaignTick()end
function NextChapterTick()end
function HUDTick()end
function StoryMentorThink()end
for t=0,3 do StoryMembers[t]=t==2 and 1 or 0;StoryStage[t]=12;StoryStarted[t]=true;StoryAdvanceAt[t]=0 end
Hero[6]=nil;Hero[8]=nil;Controllers[p]='human';StoryPopulateCursor=64;StoryEnemy={};EnemyPending=setmetatable({},{__index=function()return 0 end})
SpawnX[p]=CampaignX[12];SpawnY[p]=CampaignY[12]
local revive=ReviveHero;local calls=0
function ReviveHero(u,x,y,fx)
 calls=calls+1;assert(u==s)
 if calls==1 then return false end
 u.dead=false;u.hp=u.maxLife;u.x=x;u.y=y;return true
end
TimeNow=due-.25;StoryTick();assert(calls==0 and s.dead and StoryRevive[p]==due)
TimeNow=due;StoryTick();assert(calls==1 and s.dead and StoryRevive[p]==TimeNow+1 and SasukeReviveFailures[p]==1,'Do not erase the timer after a failed native revival')
TimeNow=TimeNow+1;StoryTick();assert(calls==2 and FoundationAlive(s) and StoryRevive[p]==0)
assert(not s.paused and not s.hidden and s.alpha==255 and s.pathing and s.flyHeight==0 and s.timeScale==1)
assert(not s.abilities[raw('Aloc')]and not s.abilities[raw('Apiv')]and not s.abilities[raw('Avul')]and not s.abilities[raw('BOwk')])
assert(Hero[p]==s and s.level==45 and s.xp==9999 and s.items[0]==item and s.hp==2000 and s.mana==900,'True revival retains the original hero, level, XP and items')
ReviveHero=revive
-- The short critical prefix also revives Sasuke if the heavy story callback aborts.
CampaignTick,NextChapterTick,HUDTick,StoryMentorThink=campaignTick,chapterTick,hudTick,mentorThink
s.dead=true;s.hp=475;StoryRevive[p]=0;InvasionHeroVisibility();local nextDue=StoryRevive[p]
local story=StoryTick;local reached=false
function StoryTick()reached=true;error('simulated overloaded story callback')end
TimeNow=nextDue-.5;local ok=pcall(FoundationTick)
assert(not ok and reached and FoundationAlive(s) and StoryRevive[p]==0,'Real native revival runs before the overloaded story callback')
StoryTick=story
-- Late clone losses remain final: native-dead/positive-HP never resurrects there.
CampaignStage=17;s.dead=true;s.hp=475;StoryRevive[p]=0;CampaignPermanentDead[p]=true
InvasionQueueCorpse(p);InvasionAfterRevive(p);assert(StoryRevive[p]==0 and s.dead)
CampaignTick,NextChapterTick,HUDTick,StoryMentorThink=campaignTick,chapterTick,hudTick,mentorThink
print('PASS: native-dead/positive-HP ghost reproduction, source corpse-heal rejection/drain stop, ordinary20s revival, failed native call retry, full control cleanup, preserved hero/XP/items and clone elimination (mock natives).')
