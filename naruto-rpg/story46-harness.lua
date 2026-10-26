-- Exercise real transitions rather than just calling the scene helpers.
for p=0,11 do RosterReset(p)end
CampaignClear();CampaignStage=0;CampaignQueued=0;CampaignTransition=false;CampaignFinished=false;CampaignActor={};CampaignActorType={};CampaignCount=0;TimeNow=17000000;World={}
for p=0,11 do HeroRole[p]=p end
HeroRole[3]=0;HeroRole[0]=3;HeroRole[8]=1;HeroRole[1]=8
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+HeroRole[p],0,0,0);HeroType[p]=Hero[p].type;HeroTemplate[p]=HeroRole[p]
 Hero[p].level=25;Hero[p].hp=10000;Hero[p].maxLife=10000;Hero[p].mana=1000;Hero[p].maxMana=1000;Hero[p].points=0
 CampaignPermanentDead[p]=false;CampaignClonePending[p]=false;Controllers[p]='computer'
end
CampaignLeader=0;CampaignPrepare();assert(CampaignNarutoPlayer==3 and CampaignSasukePlayer==8)
CampaignQueueStage(13);TimeNow=TimeNow+1.6;CampaignTick()
assert(CampaignStage==13 and CampaignTransition)
for n=0,3 do assert(CampaignActor[n].paused,'All actors already paused through the cinematic')end
TimeNow=CampaignIntroAt+8.1;CampaignTick()
assert(not CampaignTransition and Story46AttackAt==TimeNow+10)
assert(CampaignActor[0].maxLife==100000 and CampaignActor[1].maxLife==100000)
assert(not CampaignActor[0].paused and not CampaignActor[1].paused and CampaignActor[2].paused and CampaignActor[3].paused)
assert(not Hero[0].paused,'Players get control during the preparation window')
local deadline=Story46AttackAt;TimeNow=deadline-.5;Story46Tick();assert(CampaignActor[2].paused)
local story=StoryTick;function StoryTick()error('simulated exhausted story budget')end
local ok,err=pcall(FoundationTick);StoryTick=story
assert(not ok and string.find(tostring(err),'simulated')and Story46AttackAt==0 and not CampaignActor[2].paused and not CampaignActor[3].paused,'Critical prefix releases both bosses even if later scene processing aborts')
assert(CampaignActor[2].last.target==CampaignActor[0] and CampaignActor[3].last.target==CampaignActor[1])
-- Mentors remain mortal; this still advances the original failed defense path.
CampaignActor[0].hp=0;CampaignNextBot=TimeNow+10;CampaignTick();assert(CampaignTransition and CampaignQueued==14)
-- Enter the Naruto/Sasuke story duel, with non-default player slots.
CampaignClear();CampaignStage=15;CampaignTransition=false;CampaignFinished=false
Hero[3].level=29;Hero[8].level=60;Hero[3].hp=250;Hero[3].mana=20
local item={type=raw('Nlca'),charges=0};Hero[3].items={[0]=item};Hero[3].abilities[raw('Rn04')]=2
local pet=CreateUnit(7,raw('ra03'),0,0,0);Companion[21]=pet
local camera=PanCameraToTimedForPlayer;local views={}
function PanCameraToTimedForPlayer(p,x,y,t)views[p]={x=x,y=y};camera(p,x,y,t)end
CampaignQueueStage(16);TimeNow=TimeNow+1.6;CampaignTick()
assert(CampaignNaruto==Hero[3] and CampaignNaruto.level==60 and Hero[8].level==60)
assert(Hero[3].hp==Hero[3].maxLife and Hero[3].mana==Hero[3].maxMana and Hero[3].items[0]==item and GetUnitAbilityLevel(Hero[3],raw('Rn04'))==2,'Level boost keeps gear/learned skills and fills new resource pools')
for p=0,11 do if p~=3 and p~=8 then
 local h=Hero[p];assert(h.paused and not h.hidden and (h.x-CampaignTX[16])^2+(h.y-CampaignTY[16])^2>2000^2,'Spectator models leave the actual battlefield without hide/remove')
end end
assert(pet.paused and (pet.x-CampaignTX[16])^2+(pet.y-CampaignTY[16])^2>2000^2)
assert(views[2].x==CampaignTX[16]and views[2].y==CampaignTY[16],'Intro camera follows the duel, not the old tournament arena')
TimeNow=CampaignIntroAt+8.1;CampaignTick()
assert(not Hero[3].paused and not Hero[8].paused and Hero[2].paused and pet.paused)
assert(views[2].x==CampaignTX[16]and views[2].y==CampaignTY[16],'Spectators retain a view of the duel after control starts')
PanCameraToTimedForPlayer=camera
-- Next scene uses the original normal placement/unpause; no spectator hidden-state persists.
CampaignStage=17;CampaignMoveHeroes();assert((Hero[2].x-CampaignX[17])^2+(Hero[2].y-CampaignY[17])^2<1000^2 and not Hero[2].hidden)
CampaignClear();CampaignStage=16;CampaignTransition=false;CampaignNarutoPlayer=-1;CampaignSasukePlayer=8
CampaignSpawnStage();assert(CampaignNaruto.type==raw('c01C') and CampaignNaruto.level==60,'Closed Naruto slot has a real hero fallback for native level60')
CampaignClear();CampaignStage=0;CampaignTransition=false
print('PASS: cinematic pause/stronger mentors/10s player-ready boss delay/critical release/mortal objectives; actual story duel elevates role-bound Naruto60, keeps gear/skills, moves spectators+pets off-field with correct camera and next-scene return, including NPC fallback (native mocks).')
