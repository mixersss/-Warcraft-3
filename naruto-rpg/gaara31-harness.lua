-- Actual generated Gaara area damage, wave animation and native shield scheduling.
for p=0,11 do RosterReset(p)end
CampaignStage=0;CampaignTransition=false;CampaignFinished=false;TimeNow=7000000;CampaignAlliances(1)
local p=9;Hero[p]=CreateUnit(p,raw('R009'),0,0,0);HeroType[p]=raw('R009');HeroRole[p]=9;Hero[p].hp=10000;Hero[p].mana=1000
local enemy=CreateUnit(12,123,750,0,0);enemy.hp=100000;local ally=CreateUnit(10,123,750,0,0)
local immune=CreateUnit(12,123,750,0,0);immune.immune=true
local building=CreateUnit(12,123,750,0,0);building.structure=true
local far=CreateUnit(12,123,1300,0,0)
for rank=1,3 do
 RosterReset(p);World={enemy,ally,immune,building,far};Hits={};enemy.hp=100000;AimX=750;AimY=0
 local start=TimeNow;cast(p,raw('R903'),rank,nil)
 assert(ZoneX[p]==750 and ZoneY[p]==0 and ZoneRadius[p]==380 and ZoneUntil[p]==start+4)
 assert(SandWave[27] and VisualTX[SandWaveSlot[28]]==750 and SandWave[28].animation=='birth')
 local slot=SandWaveSlot[28];local sx=VisualSX[slot]
 for n=1,15 do VisualTick()end
 assert(math.abs(SandWave[28].x-(sx+750)/2)<.01,'Smooth visual wave moves toward actual aim')
 for n=1,7 do TimeNow=start+n*.5;RosterTick()end
 assert(#Hits==8 and enemy.hp==100000-8*({65,100,135})[rank],'All8 actual damage pulses at all3 ranks')
 for _,hit in ipairs(Hits)do assert(hit.target==enemy,'Never damage ally/immune/building/out-of-area unit')end
 TimeNow=start+4;RosterTick();assert(ZoneUntil[p]==0 and not SandWave[27])
end
-- Ring reuse cannot let sand cleanup delete another player's new projectile.
RosterSand(p,750,0);local slot=SandWaveSlot[27];local removed=SandWave[27]
VisualCursor=slot;VisualCreate(0,raw('vkun'),0,0,100,0,0,0,1,1);local replacement=VisualUnit[slot]
RosterClearSand(p);assert(removed.removed and VisualUnit[slot]==replacement and not replacement.removed);VisualClearSlot(slot)
-- Native shield toggles on once; an active real Rgas buff must not be toggled off by bot AI.
enemy.x=600
local h=Hero[p];h.abilities={[raw('R902')]=2};h.level=60;h.points=0;Controllers[p]='computer';Dummy[3]=enemy;World={enemy};BotNextCast[p]=0;VisualChannelUntil[p]=0;ComboLeft[p]=0
for i=45,49 do BotReadyAt[i]=0 end
assert(SkillsBot(p)and h.last.o=='manashieldon')
h.abilities[raw('Rgas')]=1;TimeNow=TimeNow+10;BotNextCast[p]=0;BotReadyAt[46]=0;h.last=nil
assert(not SkillsBot(p)and not h.last,'Do not turn off an active native mana shield')
RosterReset(p)
print('PASS: Gaara tsunami3 ranks/8 pulses/filtering, target-aligned smooth Birth wave, safe visual ring reuse/cleanup and native shield bot toggle preservation (mock natives).')
