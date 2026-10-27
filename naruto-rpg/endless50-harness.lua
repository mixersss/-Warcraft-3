-- Execute the actual post-story state machine; engine combat, sound and renderer remain separate tests.
CampaignClear();Endless50Active=false;Endless50Starting=false;CampaignFinished=false;CampaignStage=30;CampaignTransition=false;World={};TimeNow=21000000
local keep={};local winners=0;local defeats=0
local win,lose=CustomVictoryBJ,CustomDefeatBJ
function CustomVictoryBJ()winners=winners+1 end
function CustomDefeatBJ()defeats=defeats+1 end
for t=0,3 do StoryMembers[t]=3;StoryStarted[t]=true;StoryStage[t]=30 end
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;HeroType[p]=Hero[p].type;HeroTemplate[p]=p;Controllers[p]='computer'
 Hero[p].level=60;Hero[p].xp=7890+p;Hero[p].abilities[raw('Rlog')]=1
 keep[p]={type=raw('Nlca'),charges=2,owned=true};Hero[p].items[0]=keep[p]
 CampaignPermanentDead[p]=true;Hero[p].hp=0;Hero[p].dead=true;Hero[p].paused=true;Hero[p].hidden=true
end
Controllers[0]='human';StoryPopulateCursor=64;SpawnCursor=12;CampaignSasukePlayer=1;CampaignNarutoPlayer=0
local timers=CreatedTimers
CampaignFinish(true);assert(CampaignStage==31 and Endless50Starting and not CampaignFinished and winners==0 and defeats==0)
for n=1,30 do TimeNow=TimeNow+.5;Endless50Tick()end
assert(Endless50Active and not Endless50Starting and not CampaignTransition and CampaignCount==17,'Exactly17 guardians, no ordinary defending ninjas')
assert(CampaignActor[0].type==raw('c050')and CampaignActor[0].maxLife==300000 and CampaignActor[0].x==CampaignTX[12]and CampaignActor[0].y==CampaignTY[12],'Hokage stays at original arena-side post')
local counts={}
for j=0,16 do local u=CampaignActor[j];counts[CampaignActorType[j]]=(counts[CampaignActorType[j]]or 0)+1;assert(u.owner==13 and not u.paused and not u.hidden and GetUnitAbilityLevel(u,raw('Avul'))==0)end
assert(counts[0]==1 and counts[1]==1 and counts[2]==1 and counts[33]==1 and counts[31]==1 and counts[30]==1 and counts[35]==1 and counts[34]==10)
for p=0,11 do
 local h=Hero[p];assert(FoundationAlive(h)and not h.paused and not h.hidden and not h.invulnerable and not CampaignPermanentDead[p],'Every real hero, including Sasuke/Sand and clone losers, restored')
 assert(h.level==60 and h.xp==7890+p and h.items[0]==keep[p]and keep[p].charges==2 and GetUnitAbilityLevel(h,raw('Rlog'))==1,'Levels/items/learned skills preserved')
 for q=0,11 do assert(not IsUnitEnemy(h,q),'All12 allied')end
 assert(IsUnitEnemy(CreateUnit(15,raw('c010'),0,0,0),p))
 assert(not GetPlayerAlliance(13,p,ALLIANCE_SHARED_CONTROL)and not GetPlayerAlliance(15,p,ALLIANCE_SHARED_CONTROL))
 assert(StoryShopFor(p)~=nil and SpawnX[p]==Endless50SpawnX[p] and SpawnY[p]==Endless50SpawnY[p] and h.x==SpawnX[p] and h.y==SpawnY[p] and h.x>15000 and h.y< -15000)
end
assert(StoryShop[0]and StoryShop[3]and VillageFountain[0]and VillageFountain[3])
-- Hero death: one standard delay, same identity/items; repeated deaths do not end the shared game.
local h=Hero[9];h.hp=0;h.dead=true;h.hidden=true;h.paused=true
Endless50Tick();local deadline=StoryRevive[9];assert(deadline==TimeNow+20)
TimeNow=deadline-.5;Endless50Tick();assert(not FoundationAlive(h))
TimeNow=deadline;Endless50Tick();assert(FoundationAlive(h)and not h.hidden and not h.paused and h.items[0]==keep[9]and h.level==60 and StoryRevive[9]==0)
h.hp=0;h.dead=true;Endless50Tick();TimeNow=StoryRevive[9];Endless50Tick();assert(FoundationAlive(h)and not CampaignFinished)
-- Guardian slot remains reserved despite fresh waves, and resurrects at the exact post after240 seconds.
local guard=CampaignActor[1];guard.hp=0;guard.dead=true;Endless50Tick();local guardDue=Endless50ReviveAt[1]
assert(guardDue==TimeNow+240);CampaignInvasionWave(0);assert(CampaignActor[1]==guard)
TimeNow=guardDue-.5;Endless50Tick();assert(CampaignActor[1]==guard)
TimeNow=guardDue;Endless50Tick();assert(CampaignActor[1]~=guard and FoundationAlive(CampaignActor[1])and CampaignActor[1].x==Endless50X[1]and CampaignActor[1].y==Endless50Y[1])
-- Route and count are inherited, without a single Leaf infantry spawn.
for lane=0,7 do
 Invasion44Wave[lane]=0
 for round=1,3 do
  local before=CampaignCount;CampaignInvasionWave(lane)
  local amount=round==3 and 4 or 3;local found=0
  for j=before,CampaignCount-1 do assert(CampaignActor[j].owner==15 and CampaignActorRoute[j]>=0);found=found+1 end
  assert(found==amount)
 end
end
-- Test actual deadlines; later rounds repeat all five bosses every300 seconds.
local expected={{11,12},{4},{3},{13,11,12,4},{4,3},{13,11,12,4,3},{13,11,12,4,3},{13,11,12,4,3}}
Endless50BossRound=0;Endless50BossAt=TimeNow+300
for _,group in ipairs(expected)do
 for lane=0,7 do CampaignWaveAt[lane]=Endless50BossAt+600 end
 local before=CampaignCount;TimeNow=Endless50BossAt-.5;Endless50Tick();assert(CampaignCount==before,'No early bosses')
 TimeNow=Endless50BossAt;Endless50Tick();assert(CampaignCount==before+#group)
 for i,kind in ipairs(group)do local j=before+i-1;assert(CampaignActorType[j]==kind and CampaignActor[j].owner==15 and not CampaignActor[j].paused and CampaignActorRoute[j]>=0)end
 assert(Endless50BossAt==TimeNow+300)
end
-- All chapter tracks rotate sequentially; no new sound or timer for each song.
MusicOn=true;MusicCursor=0;MusicActiveChapter=-1;MusicSong=0;MusicPlaying=false;MusicClock=MusicClock or CreateTimer()
for i=0,11 do assert(type(MusicTrackPath[i])=='string'and #MusicTrackPath[i]>0 and MusicTrackSeconds[i]>0,'Actual generated soundtrack metadata')end
FoundationMusicStart()
for i=0,25 do assert(MusicPlayingTrack==i%12 and LastCampaignMusic==MusicTrackPath[i%12]);FoundationMusicNext()end
-- Clone defense removed at both object construction (verified separately) and native initialization.
for kind=20,27 do local c=CreateUnit(12,CampaignUnit[kind],0,0,0);UnitAddAbility(c,raw('S02D'));NPCInitialize(c,kind);assert(GetUnitAbilityLevel(c,raw('S02D'))==0)end
-- Real cash and event-based4+1 stat cadence, including six occupied inventory slots.
local primary={7,7,9,9,9,9,9,7,9,8,7,9}
for p=0,11 do
 StatBought50[p]=0;StoryBought[p]=0;StoryBuyAt[p]=0;Hero[p].hp=10000;Hero[p].maxLife=10000
 for k=0,5 do Hero[p].items[k]={type=raw('Nlca'),owned=true}end
 SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,625)
 local s,a,i=Hero[p].str or 0,Hero[p].agi or 0,Hero[p].int or 0
 StoryBuy(p);assert(GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)==0 and StatBought50[p]==5)
 if primary[p+1]==7 then assert(Hero[p].str==s+24 and Hero[p].agi==a+6)
 elseif primary[p+1]==8 then assert(Hero[p].int==i+24 and Hero[p].str==s+6)
 else assert(Hero[p].agi==a+24 and Hero[p].str==s+6)end
end
-- At most8 purchases/call, no unbounded loop with a large balance.
StatBought50[0]=0;SetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD,2000);StoryBuyAt[0]=0;StoryBuy(0);assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==1000 and StatBought50[0]==8)
TimeNow=TimeNow+1;StoryBuy(0);assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==0 and StatBought50[0]==16)
-- Idle heroes rally at the arena entrance; they still fight and make genuine shop trips.
for p=0,11 do
 local h=Hero[p];h.hp=h.maxLife;h.dead=false;h.paused=false;h.x=15500;h.y=-15600
 StoryRetreat[StoryTeam(p)]=false;StoryShopTripUntil[p]=0;StoryBuyAt[p]=TimeNow+100
 CampaignBot(p,nil);assert(h.last.o=='attack'and h.last.x==15932 and h.last.y==-13600,'All12 rally by Sarutobi, not lane corners')
 h.x=15932;h.y=-13600;CampaignBot(p,nil);assert(h.last.o=='holdposition','Idle heroes hold the entrance')
 local target=CreateUnit(15,raw('c010'),15800,-13700,0);CampaignBot(p,target);assert(h.last.o=='attack'and h.last.target==target,'Visible enemies override hold')
end
-- Only corpses expire; living units are never culled. Objective cannot be recycled on death.
local living=CampaignActor[17];local corpse=CampaignActor[18];corpse.hp=0;corpse.dead=true;Endless50CleanupCursor=18;Endless50Cleanup();TimeNow=TimeNow+120;Endless50CleanupCursor=18;Endless50Cleanup();assert(corpse.removed and CampaignActor[18]==nil and not living.removed)
local sasuke=Hero[1];InvasionSourceRemove(sasuke,'endless-test');assert(Hero[1]==sasuke and not sasuke.removed,'Preserve real Sasuke from NPC cleanup in endless mode')
assert(CreatedTimers<=timers+1,'No timer per guardian, wave, revive or raid')
local objective=CampaignActor[0];objective.hp=0;objective.dead=true;CampaignInvasionWave(0);assert(CampaignActor[0]==objective)
Endless50Tick();assert(CampaignFinished and not Endless50Active and defeats==12 and winners==0,'All players lose only when Sarutobi dies')
CustomVictoryBJ,CustomDefeatBJ=win,lose
print('PASS: actual31 startup/all12 restoration/retained gear and levels/allied Sand/no NPC control/17 correct posts/shops/fountains; repeated20s hero and240s guardian revival; original waves; eight300s boss groups including repeated finale;12-track loop; native4+1 scroll purchases/full inventory/bounded bank spending; corpse-only cleanup and common Hokage defeat (native mocks)')

CampaignStage=12;CampaignFinished=false;CampaignTransition=false;TimeNow=26000000
local u=Hero[0];u.hp=10000;u.dead=false;u.hidden=false;u.paused=false
InvasionSourcePause(u,true,'test-mass-control');local cap=Control50Until[0];assert(cap==TimeNow+20)
TimeNow=TimeNow+10;InvasionSourcePause(u,true,'overlapping-control');assert(Control50Until[0]==cap,'Repeated source pause cannot postpone timeout forever')
TimeNow=cap-.5;Control50Tick();assert(u.paused)
TimeNow=cap;Control50Tick();assert(not u.paused and Control50Until[0]==0,'A stuck source pause releases after20s')
InvasionSourcePause(u,true,'normal');InvasionSourcePause(u,false,'normal-end');assert(Control50Until[0]==0 and not u.paused)
InvasionSourcePause(u,true,'cinematic');CampaignTransition=true;TimeNow=TimeNow+30;Control50Tick();assert(u.paused,'Do not unpause during a scene transition')
PauseUnit(u,false);CampaignTransition=false;CampaignStage=9;InvasionSourcePause(u,true,'arena');assert(Control50Until[0]==0,'Arena/source story timing is untouched');PauseUnit(u,false)
print('PASS: finite source-pause safety lease, overlap cannot extend indefinitely, normal end clears, cinematics/arena untouched')
