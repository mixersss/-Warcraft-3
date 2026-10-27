CampaignClear();CampaignStage=12;CampaignTransition=false;CampaignFinished=false
for p=0,11 do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;Controllers[p]='computer';SetPlayerHandicapXP(p,1+p*.01)end
HeroRole[0],HeroRole[10]=HeroRole[10],HeroRole[0]
CampaignStartPlay()
for p=0,11 do assert(math.abs(GetPlayerHandicapXP(p)-(1+p*.01)*1)<.00001,'No extra invasion multiplier on top of global XP')end
CampaignStartPlay();assert(math.abs(GetPlayerHandicapXP(10)-1.1)<.00001,'No repeated multiplicative boost')
CampaignClear()
for p=0,11 do assert(math.abs(GetPlayerHandicapXP(p)-(1+p*.01))<.00001,'Exact prior XP restored at scene clear')end
CampaignStage=13;Invasion48XPStart();assert(not Invasion48XPActive,'No boost outside invasion')
assert(CreateUnit(12,raw('c003'),0,0,0).maxLife==262500)
assert(CreateUnit(12,raw('c004'),0,0,0).maxLife==192500)
CampaignActor={};CampaignCount=0;CampaignStage=12
local a=CampaignAdd(13,15,0,0);assert(CampaignActor[a].type==raw('c00D')and CampaignActor[a].maxLife==100000,'Invasion Orochimaru unchanged')
CampaignClear();CampaignStage=28;CampaignActor={};CampaignCount=0
local b=CampaignAdd(13,12,0,0);assert(CampaignActor[b].type==raw('c048')and CampaignActor[b].maxLife==40000,'Only final Orochimaru gets40kHP')
assert(NPCSourceType(CampaignActor[b])==raw('c00D'),'Source-native Orochimaru spell conditions recognize final body')
assert(CampaignActorType[b]==13,'Original NPC spell/controller kind preserved')
CampaignClear()
for p=0,11 do SetPlayerHandicapXP(p,1)end
print('PASS: invasion XP restoration/idempotence without additional bonus; Akatsuki30% HP reduction; final Orochimaru40k separate from invasion body (native mocks)')
