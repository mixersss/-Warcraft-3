-- Actual Alpha23 JASS paths; native rendering, pathfinding and bounty delivery need 1.26.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
local saved={}
local function mock(name,value)saved[#saved+1]={name,_G[name]};_G[name]=value end
local nativeOrder=OrderId
mock('OrderId',function(s)return ({drain=852487,drunkenhaze=852585,move=851986,attack=851983,stop=851972})[s] or nativeOrder(s)end)
local point,targetOrder,immediate=IssuePointOrder,IssueTargetOrder,IssueImmediateOrder
mock('GetSpellAbilityUnit',function()return Caster end)
mock('GetSpellTargetUnit',function()return Target end)
mock('IssuePointOrder',function(u,o,x,y)local ok=point(u,o,x,y);u.order=OrderId(o);return ok end)
mock('IssueImmediateOrder',function(u,o)local ok=immediate(u,o);u.order=OrderId(o);return ok end)
mock('IssueTargetOrder',function(u,o,t)
 local ok=targetOrder(u,o,t);u.order=OrderId(o)
 if o=='drain' then
  local c,tar,spell=Caster,Target,Spell;Caster=u;Target=t;Spell=raw('A02X');OrigNPC_GBO();Caster=c;Target=tar;Spell=spell
 end
 return ok
end)
CampaignClear();CampaignStage=12;CampaignTransition=false;CampaignFinished=false;CampaignLeader=0;CampaignScratch=CreateGroup();World={}
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);Hero[p].hp=10000;Hero[p].maxLife=10000;Hero[p].hero=true
 HeroRole[p]=p;HeroType[p]=Hero[p].type;Controllers[p]='computer';CampaignPermanentDead[p]=false
end
CampaignBindRoles();CampaignAlliances(2)
-- A stationary ANBU fights, then walks back to the captured original post.
TimeNow=1100000;local slot=CampaignAdd(34,0,5000,-6000);local guard=CampaignActor[slot]
guard.x=5500;local enemy=Hero[9];enemy.x=guard.x+100;enemy.y=guard.y;World={enemy}
CampaignNPCTick();assert(guard.last.o=='attack' and guard.last.target==enemy)
enemy.hp=0;World={};TimeNow=TimeNow+4;CampaignNPCTick()
assert(guard.last.o=='move' and guard.last.x==5000 and guard.last.y==-6000,'Idle defender returns on foot to original post')
local last=guard.last;guard.paused=true;TimeNow=TimeNow+4;CampaignNPCTick();assert(guard.last==last,'Never break a crowd-control pause');guard.paused=false
SaveReal(NPCCooldowns,GetHandleId(guard),0,TimeNow+20);TimeNow=TimeNow+4;CampaignNPCTick();assert(guard.last==last,'Do not interrupt a protected cast to return home')
SaveReal(NPCCooldowns,GetHandleId(guard),0,0);enemy.hp=10000;World={enemy};TimeNow=TimeNow+4;CampaignNPCTick();assert(guard.last.target==enemy,'Returning guards can re-engage')
CampaignClear();World={}
-- All five original camp posts are active, vulnerable, locally reactive, and retreat wounded.
for _,kind in ipairs({5,6,7,8,9})do
 slot=CampaignAdd(kind,15,0,0);guard=CampaignActor[slot];guard.hp=60000;guard.maxLife=60000
 assert(guard.x==CampaignReserveX[kind] and guard.y==CampaignReserveY[kind] and not guard.paused and GetUnitAbilityLevel(guard,raw('Avul'))==0)
 CampaignCount=slot+1;World={};TimeNow=TimeNow+20;CampaignNPCTick();assert(guard.last==nil,'Healthy Sound guard must stay at post')
 enemy=Hero[0];enemy.hp=10000;enemy.x=guard.x+100;enemy.y=guard.y;World={enemy};CampaignThinkCursor=slot;TimeNow=TimeNow+20;CampaignNPCTick()
 assert(guard.last,'Sound guard must react to a nearby enemy hero')
 SaveReal(NPCCooldowns,GetHandleId(guard),0,0);guard.hp=10000;CampaignThinkCursor=slot;TimeNow=TimeNow+20;CampaignNPCTick()
 local left=kind==6 or kind==9
 assert(guard.last.o=='move' and guard.last.x==(left and -2624 or 5632) and guard.last.y==(left and -11840 or -3008),'Source low-HP retreat selects the corresponding camp fountain')
 guard.hp=60000;World={};CampaignMoveAt[slot]=0;CampaignThinkCursor=slot;CampaignNPCTick()
end
CampaignClear();World={}
-- Approach must reach the 150 casting range; native follow would stop too far away.
local medics={}
for j=0,5 do slot=CampaignAdd(32,13,CampaignMedicX[j],CampaignMedicY[j]);medics[j]=CampaignActor[slot];OrigNPC_IF[j]=medics[j] end
local injured=Hero[0];injured.hp=8500;injured.maxLife=10000;local medic=medics[0]
injured.x=medic.x+400;injured.y=medic.y;World={injured};TimeNow=TimeNow+20;CampaignThinkCursor=0;CampaignNPCTick()
assert(medic.last.o=='move' and medic.last.x==injured.x,'Medic approaches directly instead of following outside heal range')
local pulses={OrigNPC_GUO,OrigNPC_G_O,OrigNPC_G3O,OrigNPC_G7O,OrigNPC_HEO,OrigNPC_HIO}
for j=0,5 do
 medic=medics[j];medic.mana=1500;injured.hp=8500;injured.x=medic.x+100;injured.y=medic.y
 TimeNow=TimeNow+20;assert(NPCTry(medic,32,injured),'A patient at 85% HP is eligible; acquisition and cast thresholds agree')
 assert(OrigNPC_RR[j+2]==injured and NPCMedicClock(j).enabled and NPCBusy(medic))
 pulses[j+1]();assert(injured.hp==8575 and medic.mana==1475,'Each source pulse really restores 75 HP and spends 25 mana')
 pulses[j+1]();assert(injured.hp==8650 and medic.mana==1450)
 injured.hp=9990;pulses[j+1]();assert(injured.hp==10000,'Healing clamps to maximum HP')
 pulses[j+1]();assert(not NPCMedicClock(j).enabled and not OrigNPC_AF[j] and not OrigNPC_RR[j+2] and not NPCBusy(medic),'Full patient ends channel and releases effects')
 Caster=medic;OrigNPC_GPO();OrigNPC_GPO() -- repeated native FINISH/ENDCAST cleanup is safe.
end
-- Cancellation/stage cleanup releases all six target/effect references and clocks.
medic=medics[0];injured.hp=5000;injured.x=medic.x+100;injured.y=medic.y;TimeNow=TimeNow+20;assert(NPCTry(medic,32,injured))
local effect=OrigNPC_AF[0];CampaignClear();assert(not effect.alive)
for j=0,5 do assert(not NPCMedicClock(j).enabled and not OrigNPC_IF[j] and not OrigNPC_RR[j+2] and not OrigNPC_AF[j])end
-- Each countdown performs its real arrival even when the story heartbeat is not called.
World={};CampaignStage=12;CampaignTransition=true;CampaignFinished=false;CampaignLeader=0
CampaignSpawnStage();while CampaignDeployCursor<242 do CampaignDeploy()end
local gold=GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD);CampaignStartPlay()
assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==gold,'Enabling bounty cannot change balances')
for p=0,15 do assert(GetPlayerState(p,PLAYER_STATE_GIVES_BOUNTY)==((p==13 or p==15)and 0 or 1),'NPC victims use explicit checked rewards; hero-owned victims retain native bounty')end
local clocks={};for j=0,3 do clocks[j]=CampaignEventClock[j] end
local expired=nil;mock('GetExpiredTimer',function()return expired end)
for _,j in ipairs({0,1,2,3})do expired=clocks[j];assert(expired.callback==CampaignEventWake);expired.callback();assert(CampaignEventClock[j]==nil and expired.destroyed)end
assert(CampaignVillageKabuto and CampaignVillageSnake and CampaignVillageOro and not CampaignVillageOro.paused,'All four real timer callbacks run without CampaignTick')
assert(CampaignVillageKabuto.last.o=='attack' and CampaignVillageKabuto.last.x==CampaignRouteX[3])
assert(CampaignVillageSnake.last.o=='attack' and CampaignVillageSnake.last.x==CampaignRouteX[3])
local count=CampaignCount;expired.callback();assert(CampaignCount==count,'Expired callback is idempotent')
CampaignClear();assert(not CampaignBountyActive and GetPlayerState(0,PLAYER_STATE_GIVES_BOUNTY)==0,'Restore prior bounty flags after the invasion')
-- Tsuga is the source targeted approach and five hits, not an instantaneous line spell.
CampaignStage=0;StoryStage[2]=1;CampaignClonePending[7]=false;World={};TimeNow=1200000
local kiba=Hero[7];kiba.hp=10000;kiba.hidden=false;kiba.paused=false;kiba.type=HeroType[7];KibaFourLegs[7]=false
local victim=CreateUnit(12,raw('re01'),0,0,0);victim.maxLife=100000;victim.hp=100000
mock('IsTerrainPathable',function()return false end)
for rank=1,3 do
 kiba.x=-14500;kiba.y=10000;victim.x=kiba.x+600;victim.y=kiba.y;victim.hp=100000;victim.hidden=false
 Caster=kiba;Target=victim;Spell=raw('R704');kiba.abilities[Spell]=rank;kiba.order=OrderId('drunkenhaze');Hits={}
 SkillsEffect();assert(KibaRollTarget[7]==victim and SkillTarget[38]==1)
 local start=kiba.x;KibaRollTick();assert(kiba.x>start and #Hits==0,'Real approach occurs before impacts')
 for n=1,60 do KibaRollTick()end
 assert(#Hits==5 and victim.hp==100000-5*(120+60*rank),'Exactly five source-rank impacts')
 assert(not KibaRollTarget[7] and not KibaRollCaster[7] and not kiba.paused and kiba.timeScale==1 and VisualChannelUntil[7]==0)
end
kiba.x=-14500;victim.x=kiba.x+600;Hits={};KibaRollStart(7,1,victim)
mock('IsTerrainPathable',function(x,y)return x>-14480 end)
KibaRollTick();assert(not KibaRollTarget[7] and kiba.x==-14500 and #Hits==0,'Blocked path cancels without teleporting through terrain')
KibaRollStart(7,1,victim);Caster=kiba;Spell=raw('R704');VisualChannelIndex[7]=38;VisualChannelUntil[7]=TimeNow+3;SkillsEndcast();assert(not KibaRollTarget[7],'Native cancellation stops the combo')
KibaRollStart(7,1,victim);victim.hp=0;KibaRollTick();assert(not KibaRollTarget[7],'Target death releases cast-local references')
victim.hp=100000;KibaRollStart(7,1,victim);RosterResetEffects(7);assert(not KibaRollTarget[7],'Scene changes clear the movement')
KibaFourLegs[7]=true;VisualPose(7,38);assert(kiba.animationIndex==SkillAnimation[38]);KibaFourLegs[7]=false
for n=#saved,1,-1 do local v=saved[n];_G[v[1]]=v[2]end
print('PASS: Alpha23 defender posts, five active source Sound guards and fountain retreat, six real source medic healing/cost/cleanup paths, invasion native bounty flags, all four actual reinforcement timer callbacks without story heartbeat, marching Kabuto/snake and targeted five-hit Tsuga ranks/movement/obstacles/cancellation/death/scene cleanup (mock natives).')
