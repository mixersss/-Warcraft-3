-- Actual shipped JASS; native rendering, auras and stun duration still require Warcraft.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
local function numbers()return setmetatable({},{__index=function()return 0 end})end
function GetSpellTargetUnit()return Target end
-- Tenten: damage and an independent native stun are requested at impact, exactly once.
Hero[5]=CreateUnit(5,raw('R005'),0,0,0);Hero[5].hp=10000;HeroRole[5]=5;HeroType[5]=raw('R005')
local target=CreateUnit(12,raw('re06'),600,0,0);target.hp=10000;target.maxLife=10000
TimeNow=400000;Hits={};local timers=CreatedTimers;local cursor=StunCursor
cast(5,PlayableSkill[25],1,target);local missile=KunaiMissile[5]
assert(missile and target.hp==10000 and #Hits==0,'No invisible instant damage/stun before the flying kunai arrives')
KunaiTick();assert(missile.x==75 and target.hp==10000)
target.x=650;for i=1,10 do KunaiTick()end
assert(target.hp==9870 and #Hits==1 and missile.removed and not KunaiMissile[5]and not KunaiTarget[5])
assert(GetUnitAbilityLevel(StunDummy[cursor],raw('Rkst'))==1,'Impact must issue the separate stun ability')
assert(StunDummy[cursor].last.o=='thunderbolt'and StunDummy[cursor].last.target==target)
KunaiTick();assert(#Hits==1,'No duplicate native/script damage')
cast(5,PlayableSkill[25],4,target);local second=KunaiMissile[5];target.hp=0;KunaiTick();assert(second.removed and #Hits==1)
target.hp=10000;target.immune=true;cast(5,PlayableSkill[25],4,target);assert(not KunaiMissile[5]and #Hits==1);target.immune=false
cast(5,PlayableSkill[25],4,target);TimeNow=TimeNow+3;KunaiTick();assert(not KunaiMissile[5]and #Hits==1,'Expiry releases a chasing missile without hitting a stale target')
cast(5,PlayableSkill[25],2,target);RosterReset(5);assert(not KunaiMissile[5]and not KunaiCaster[5]);assert(CreatedTimers==timers)
-- Original source fountain positions, owner, persistence and duplicate protection.
VillageFountain={};CampaignFountainsOpen();local fountains={}
local positions={{16128,-15744},{4672,-12096},{-2624,-11840},{5632,-3008}}
for j=0,3 do local u=VillageFountain[j];fountains[j]=u;assert(u and u.owner==14 and u.x==positions[j+1][1]and u.y==positions[j+1][2])end
CampaignFountainsOpen();for j=0,3 do assert(VillageFountain[j]==fountains[j])end
CampaignClear();for j=0,3 do assert(VillageFountain[j]==fountains[j]and not fountains[j].removed,'Chapter combat cleanup must preserve these source fountains')end
-- Byakugan marks a distant enemy hero for allied clients, never for enemy clients.
Hero[4]=CreateUnit(4,raw('R004'),0,0,0);Hero[4].hp=10000;HeroRole[4]=4;HeroType[4]=raw('R004')
local far=CreateUnit(12,raw('C014'),9000,9000,0);far.hero=true
local other=CreateUnit(0,raw('R000'),-9000,-9000,0);other.hero=true
local ally=CreateUnit(3,raw('R003'),5000,5000,0);ally.hero=true
local dead=CreateUnit(12,raw('C015'),4000,4000,0);dead.hero=true;dead.hp=0
local illusion=CreateUnit(12,raw('C014'),3000,3000,0);illusion.hero=true;illusion.illusion=true
local hidden=CreateUnit(12,raw('C014'),2000,2000,0);hidden.hero=true;hidden.hidden=true
local creep=CreateUnit(12,raw('re06'),4000,4000,0)
CampaignAlliances(0)
World={far,other,ally,dead,illusion,hidden,creep};TimeNow=500000;Pings={};LocalPlayer=4
RosterVision(4,1);assert(#Pings==2 and VisionMarkCount[4]==2 and VisionRadius[4]==400,'Rank one must also mark heroes beyond the local vision radius')
local f0=VisionMarkFog[4*128];assert(f0.active and f0.radius==192)
LocalPlayer=3;Pings={};RosterVisionPulse(4);assert(#Pings==2 and f0.destroyed,'An allied human receives a computer ally Byakugan; old marks are released')
LocalPlayer=0;Pings={};RosterVisionPulse(4);assert(#Pings==0 and VisionMarkCount[4]==2,'Fog handle creation stays synchronized even on enemy clients')
RosterClearVision(4);assert(VisionMarkCount[4]==0 and not VisionFog[4]and not VisionMarkFog[4*128])
-- All three teammates participate in enemy target selection, not just the human leader.
Hero={};Companion={};StoryMentor={};World={};TimeNow=600000
for p=0,2 do Hero[p]=CreateUnit(p,raw('R000')+p,500-p*200,0,0)end
Hero[1].x=100;Hero[2].x=300;Controllers[0]='human';Controllers[1]='computer';Controllers[2]='computer'
local enemy=CreateUnit(12,raw('re01'),0,0,0);StoryMentorsReleased=false
assert(StoryEnemyTarget(0,enemy,Hero[0])==Hero[1],'Nearest allied bot must get aggro')
Hero[1].hp=0;assert(StoryEnemyTarget(0,enemy,Hero[0])==Hero[2],'Second bot can also take aggro')
Hero[2].abilities[raw('Avul')]=1;assert(StoryEnemyTarget(0,enemy,Hero[0])==Hero[0],'Invalid invulnerable targets are excluded')
Hero[1].hp=10000;Hero[2].abilities={}
StoryEnemy={};StoryEnemy[0]=enemy;EnemyKind[0]=1;EnemyNext[0]=TimeNow+999;EnemyPending[0]=0;EnemyFocus[0]=Hero[0];enemy.order=852000
StoryMembers={[0]=3,[1]=0,[2]=0,[3]=0};StoryStage=numbers();StoryStage[0]=1;StoryStarted={[0]=true};StoryPopulateCursor=64;StoryAdvanceAt=numbers();StoryMarch={[0]=false};ExamPhase=0;CampaignStage=0;CampaignTransition=false;StoryMentorClock=nil
local issue=IssueTargetOrder;local attacks=0
function IssueTargetOrder(u,o,t)if u==enemy then attacks=attacks+1 end;return issue(u,o,t)end
StoryTick();assert(enemy.last.target==Hero[1]and EnemyFocus[0]==Hero[1]and attacks==1,'An ongoing human attack must retarget the closer bot without waiting for a spell cooldown')
StoryTick();assert(attacks==1,'A stable target must not have its attack repeatedly reset')
IssueTargetOrder=issue
-- Opening timer UI is created after loading, shown again if hidden, and not restarted.
StageBoard=nil;PhaseClock=nil;PhaseDialog=nil;StoryMentorDialog=nil;HUDClockKey=0;TimeNow=0;ExamPhase=0;CampaignStage=0;StoryMentorsReleased=false
StoryMentorClock=CreateTimer();TimerStart(StoryMentorClock,330,false,StoryReleaseMentors)
HUDTick();assert(not StageBoard and not PhaseDialog,'Do not attempt to show the native timer during map initialization')
TimeNow=.5;HUDTick();assert(StageBoard and PhaseDialog.visible and StoryMentorDialog.visible)
assert(PhaseClock.delay==419.5 and StoryMentorClock.delay==330)
local firstClock=PhaseClock;PhaseDialog.visible=false;StoryMentorDialog.visible=false;TimeNow=1;HUDTick()
assert(PhaseDialog.visible and StoryMentorDialog.visible and PhaseClock==firstClock and PhaseClock.delay==419.5,'Re-show an existing clock; never restart the countdown each heartbeat')
print('PASS: exact persistent village fountains; global team-only Byakugan marks/cleanup; homing kunai impact damage plus native stun; both allied bots take aggro without attack resets; first real heartbeat shows opening countdown (mock natives).')
