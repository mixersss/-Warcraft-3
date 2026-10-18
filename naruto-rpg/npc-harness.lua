-- Execute NPC order scheduling and source action semantics with native mocks.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
local u=CreateUnit(12,raw('c003'),0,0,0);local target=CreateUnit(0,raw('R000'),200,0,0)
u.mana=10000;TimeNow=30000;NPCCooldowns=InitHashtable();NPCInitialize(u,3)
assert(GetUnitAbilityLevel(u,raw('A01B'))==4 and GetUnitAbilityLevel(u,raw('A01K'))==1,'Itachi has source fire and Mangekyou ranks')
assert(NPCTry(u,3,target));assert(u.last.o~='stomp' and u.last.o~='shockwave','Source skill orders replace generic bolt/wave/stomp')
assert(NPCBusy(u));TimeNow=30020;assert(not NPCBusy(u))
local medic=CreateUnit(0,raw('c020'),0,0,0);NPCInitialize(medic,32);local hurt=CreateUnit(0,raw('R000'),100,0,0);hurt.hp=100;hurt.maxLife=10000;medic.mana=10000
assert(NPCTry(medic,32,hurt) and medic.last.o=='drain','Medics use source healing channel, not a priest spell')
-- The native Tsukuyomi action really holds a target for the original 14 seconds.
local sleeping={};function GetSpellTargetUnit()return target end
function TriggerSleepAction(n)sleeping[#sleeping+1]=n end
OrigNPC_KIX();assert(sleeping[1]==14 and not target.paused and target.animation=='Death')
print('PASS: source Itachi ranks, distinct native NPC orders/cooldowns/channel protection, medic source healing order and original 14-second Tsukuyomi action (mock natives).')

local tayuya=CreateUnit(12,raw('c008'),0,0,0);NPCInitialize(tayuya,8);assert(GetUnitAbilityLevel(tayuya,raw('S02B'))==0,'Tayuya cannot sleep before original phase')
tayuya.hp=4999;tayuya.mana=10000;TimeNow=40000;NPCTry(tayuya,8,target);assert(GetUnitAbilityLevel(tayuya,raw('S02B'))==1,'Source Tayuya sleep unlocks below 5000 HP')
local gate=nil;function GetEnumDestructable()return gate end
function ModifyGateBJ(op,d)assert(op==1);d.open=true end
gate={type=raw('LTe1'),x=5248,y=-3456};CampaignOpenSourceGate();assert(gate.open)
gate={type=raw('LTe3'),x=-1664,y=-11904};CampaignOpenSourceGate();assert(gate.open)
gate={type=raw('LTe3'),x=0,y=0};CampaignOpenSourceGate();assert(not gate.open,'Unrelated gates remain unchanged')

local neji=CreateUnit(0,raw('R004'),0,0,0);local clone=CreateUnit(12,raw('C014'),100,0,0);NPCInitialize(clone,20)
assert(NPCSourceType(clone)==raw('R004'),'Source type guards recognize an enemy clone')
World={neji,clone};local sameType=OrigNPC_PBV(raw('R004'));assert(#sameType==2,'Source type groups include both player and clone, as in the original')
assert(GetUnitAbilityLevel(clone,raw('A034'))==4 and GetUnitAbilityLevel(clone,raw('A006'))==4 and GetUnitAbilityLevel(clone,raw('A02L'))==3,'Original Neji clone skill ranks')

Caster=clone;Spell=raw('A02L');SaveInteger(NPCCooldowns,GetHandleId(clone),-3,Spell);SaveReal(NPCCooldowns,GetHandleId(clone),0,TimeNow+99)
assert(NPCBusy(clone));NPCLongChannelEnd();assert(not NPCBusy(clone),'Source technical 99-second follow-through must release AI when the original combo ends')

local lee=CreateUnit(12,raw('C015'),0,0,0);NPCInitialize(lee,21);lee.mana=10000;target.x=50;target.y=0;TimeNow=50000
assert(NPCTry(lee,21,target));assert(GetUnitAbilityLevel(lee,raw('A00E'))==4 and GetUnitAbilityLevel(lee,raw('A01T'))==0,'Lee chooses the correct source spell despite a shared native order')
TimeNow=50010;SaveReal(NPCCooldowns,GetHandleId(lee),raw('A00E'),51000);SaveReal(NPCCooldowns,GetHandleId(lee),raw('A029'),51000)
assert(NPCTry(lee,21,target));assert(GetUnitAbilityLevel(lee,raw('A01T'))==2,'Original Ura Renge rank survives native order switching')
