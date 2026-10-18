-- Native timer dialogs from actual generated JASS; real rendering needs Warcraft.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
CampaignClear();CampaignVillageLandmarksClose();StoryShopsClose()
TimeNow=990000;CampaignStage=12;CampaignTransition=true;CampaignFinished=false;CampaignLeader=0;CampaignChampion=-1;World={}
CampaignPermanentDead={};CampaignClonePending={}
for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);Hero[p].hp=10000;Hero[p].maxLife=10000;HeroRole[p]=p;HeroType[p]=Hero[p].type end
CampaignBindRoles();CampaignAlliances(2);CampaignMoveHeroes();CampaignSpawnStage()
while CampaignDeployCursor<242 do CampaignDeploy()end
local allocated=CreatedTimers;CampaignStartPlay();local start=TimeNow;local clocks,dialogs={},{}
assert(CreatedTimers==allocated+4,'Exactly four event countdowns, not timers per wave or heartbeat')
local labels={'Кабуто: до атаки','Джирайя: до подкрепления','Змея: до появления','Орочимару: до атаки'}
for j,seconds in ipairs({400,760,820,1160})do
 local i=j-1;clocks[i]=CampaignEventClock[i];dialogs[i]=CampaignEventDialog[i]
 assert(clocks[i] and clocks[i].delay==seconds and not clocks[i].repeating and dialogs[i].timer==clocks[i] and dialogs[i].visible and dialogs[i].title==labels[j],'Visible one-shot clock at its actual source deadline')
end
for n=1,10 do TimeNow=start+n;CampaignTick()end
assert(CreatedTimers==allocated+4,'Heartbeats must not allocate or restart event clocks')
for i=0,3 do assert(CampaignEventClock[i]==clocks[i] and CampaignEventDialog[i]==dialogs[i] and not clocks[i].destroyed)end
for _,e in ipairs({{400,0},{760,1},{820,2},{1160,3}})do
 TimeNow=start+e[1];CampaignTick();local i=e[2]
 assert(CampaignEventClock[i]==nil and CampaignEventDialog[i]==nil and clocks[i].destroyed and clocks[i].paused and dialogs[i].destroyed and not dialogs[i].visible,'Close the real timer/dialog when its NPC event happens')
end
assert(CampaignVillageKabuto and not CampaignVillageOro.paused and CampaignDialog.visible,'Actual events and overall invasion clock remain active')
allocated=CreatedTimers;CampaignEventOpen(0,'already expired',TimeNow);assert(CreatedTimers==allocated and CampaignEventClock[0]==nil)
-- Early stage exit must immediately hide/destroy countdowns, including cancelled attacks.
CampaignStartPlay();local earlyC,earlyD={},{}
for i=0,3 do earlyC[i]=CampaignEventClock[i];earlyD[i]=CampaignEventDialog[i]end
CampaignQueueStage(13)
for i=0,3 do assert(earlyC[i].destroyed and earlyD[i].destroyed and CampaignEventClock[i]==nil and CampaignEventDialog[i]==nil)end
-- Repeated start replaces old handles instead of leaving duplicates; finish also cleans up.
CampaignStartPlay();local replacedC,replacedD={},{}
for i=0,3 do replacedC[i]=CampaignEventClock[i];replacedD[i]=CampaignEventDialog[i]end
CampaignStartPlay()
for i=0,3 do assert(replacedC[i].destroyed and replacedD[i].destroyed and CampaignEventClock[i]~=replacedC[i])end
local lastC,lastD={},{};for i=0,3 do lastC[i]=CampaignEventClock[i];lastD[i]=CampaignEventDialog[i]end
CampaignFinish(true)
for i=0,3 do assert(lastC[i].destroyed and lastD[i].destroyed and CampaignEventClock[i]==nil and CampaignEventDialog[i]==nil)end
print('PASS: four visible source-deadline event countdowns (Kabuto/Jiraiya/Snake/Orochimaru), stable handles across heartbeats, close on each actual arrival, immediate early-exit cancellation, expired-clock guard, repeated-start replacement and finish cleanup (mock natives).')
