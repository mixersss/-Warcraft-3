-- Real new JASS, with native invisibility/cooldown data checked separately in W3A.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
function I2S(n)return tostring(math.floor(n))end
function IssueImmediateOrder(u,o)u.last={o=o};return true end
TimeNow=10000;Hero={};HeroRole={};HeroType={};StoryStage={[0]=1,[1]=1,[2]=1,[3]=1}
for p=0,11 do Hero[p]=CreateUnit(p,p,-14000,14000,0);Hero[p].abilities[raw('Rlog')]=1;HeroRole[p]=p;HeroType[p]=p;LogReadyAt[p]=0;LogUntil[p]=0 end
local enemy=CreateUnit(12,0,-13800,14000,0)
Hero[0].hp=3000;Hero[0].mana=150;ComboLeft[0]=0;VisualChannelUntil[0]=0
assert(CommonLogBot(0,enemy) and Hero[0].last.o=='windwalk','Wounded bot casts the real native order')
Caster=Hero[0];Spell=raw('Rlog');Target=nil
local timers=CreatedTimers;SkillsEffect();local log=LogActor[0]
assert(log and LogUntil[0]==10003 and LogReadyAt[0]==10008 and CreatedTimers==timers,'One bounded log actor without a cast timer')
TimeNow=10001;assert(CommonLogBot(0,enemy) and Hero[0].last.o=='move','Do not immediately break invisibility with an attack')
TimeNow=10001.5;CommonLogTick();assert(not LogActor[0] and log.removed,'Log removed after 1.5 seconds')
TimeNow=10003;assert(not CommonLogBot(0,enemy),'Respect the eight-second cooldown')
TimeNow=10008;Hero[0].mana=149;assert(not CommonLogBot(0,enemy),'No cast without 150 mana')
Hero[0].mana=150;Hero[0].hp=9000;assert(not CommonLogBot(0,enemy),'Healthy bots keep fighting')
Hero[0].hp=3000;assert(CommonLogBot(0,enemy))
CommonLogEffect(0);local nextLog=LogActor[0];Hero[0].hp=0;CommonLogTick();assert(not LogActor[0] and nextLog.removed and LogUntil[0]==0,'Death cleanup')
Hero[0].hp=3000;CommonLogEffect(0);nextLog=LogActor[0];RosterReset(0);assert(not LogActor[0] and nextLog.removed,'Reselection/chapter cleanup')
assert(CreatedTimers==timers)
-- Timers for preparation, unbounded battle elapsed time, transitions, quiz and both forest deadlines.
assert(HUDTime(65.9)=='1:05' and HUDTime(-1)=='0:00')
StageBoard=nil;HUDClockKey=0;HUDInit();local clock=PhaseClock;local dialog=PhaseDialog
StoryMembers={[0]=3,[1]=3,[2]=0,[3]=3};StoryStarted={[0]=false,[1]=true,[2]=false,[3]=true};StoryAdvanceAt={[0]=0,[1]=0,[2]=0,[3]=0}
TimeNow=10;ExamPhase=0;StoryStage[0]=1;StoryStage[1]=3;HUDTick();assert(StageBoard.cells[5]=='0:20 до выхода' and StageBoard.cells[8]=='0:00 прошло' and StageBoard.cells[10]=='Пустые слоты')
TimeNow=15;HUDTick();assert(StageBoard.cells[8]=='0:05 прошло')
StoryAdvanceAt[1]=23;HUDTick();assert(StageBoard.cells[8]=='0:08 до перехода')
ExamPhase=1;ExamReadyAt=35;HUDTick();assert(clock.delay==20 and dialog.visible)
ExamPhase=2;ExamAsked=0;ExamNextAt=25;HUDTick();assert(clock.delay==10)
ExamAsked=1;ExamNextAt=30;HUDTick();assert(clock.delay==15 and dialog.title=='Ибики: вопрос 1/5')
TimeNow=16;HUDTick();assert(clock.delay==15,'HUD must not restart a clock each heartbeat')
ExamPhase=3;ExamOpenAt=1216;ExamEndAt=1336;ExamTowerOpen=false;HUDTick();assert(not dialog.visible and StageBoard.cells[17]=='20:00')
TimeNow=1216;ExamTowerOpen=true;HUDTick();assert(StageBoard.cells[16]=='Башня открыта' and StageBoard.cells[17]=='2:00 до конца')
assert(HUDItemsAcquired==HUDItemsReleased,'Every temporary multiboard item handle must be released')
print('PASS: native log cast/order, wounded-bot escape, mana/cooldown, bounded actors and death/reset cleanup; stage UI times, per-question clock, no repeated restarts, tower deadline and balanced UI handle releases (mock natives).')
