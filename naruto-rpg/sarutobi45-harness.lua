-- Reproduce a dead objective slot being reused before CampaignTick reaches its death test.
CampaignClear();CampaignActor={};CampaignActorType={};CampaignCount=0;CampaignStage=12;CampaignTransition=false;CampaignFinished=false;CampaignPlaced=true;TimeNow=15000000
CampaignPrepare();CampaignAlliances(2)
for p=0,11 do Hero[p].hp=10000;Hero[p].dead=false;Hero[p].hidden=false;CampaignPermanentDead[p]=false;StoryRevive[p]=0 end
local slot=CampaignAdd(0,13,CampaignX[12],CampaignY[12]);assert(slot==0)
local hokage=CampaignActor[0];hokage.hp=0
-- This is a real independent wave callback, not a direct invocation of the story advance.
Invasion44Wave[0]=0;CampaignInvasionWave(0)
assert(CampaignActor[0]==hokage and CampaignActorType[0]==0 and hokage.hp==0 and not hokage.removed,'New waves must never overwrite the fallen Sarutobi objective')
assert(CampaignCount==4 and CampaignActorType[1]==CampaignWaveKind[0],'Ordinary wave still creates all3 units')
-- Other corpse slots remain reusable, preserving the original bounded actor pool.
local old=CampaignActor[1];old.hp=0
local replacement=CampaignAdd(16,15,-2992,-11824)
assert(replacement==1 and CampaignActor[1]~=old and old.removed and CampaignActor[0]==hokage)
CampaignKabutoAt=TimeNow;CampaignInvasionEvents()
assert(CampaignVillageKabuto and CampaignActor[0]==hokage and not hokage.removed,'Real due reinforcement must not replace the dead objective either')
CampaignEndAt=TimeNow+1500;CampaignNextBot=TimeNow+100;CampaignNextNPC=TimeNow+100
CampaignKabutoAt=0;CampaignJiraiyaAt=0;CampaignSnakeAt=0;CampaignOroAt=0
for j=0,7 do CampaignWaveAt[j]=TimeNow+100 end
CampaignTick();assert(CampaignTransition and CampaignQueued==13,'Fallen Sarutobi queues the original next story scene')
TimeNow=TimeNow+1.6;CampaignTick()
assert(CampaignStage==13 and CampaignPlaced and hokage.removed and CampaignActor[0]~=hokage,'Cleanup removes the corpse and creates the next scene normally')
assert(CampaignActorType[0]==37 and CampaignActorType[1]==38,'Kakashi and Gai are restored as the original next objectives')
CampaignClear();CampaignTransition=false;CampaignStage=0
print('PASS: dead Sarutobi survives intervening wave/reinforcement allocation, other corpse slots still recycle, actual CampaignTick queues and deploys original stage13 (native mocks; engine crash cause unconfirmed).')
