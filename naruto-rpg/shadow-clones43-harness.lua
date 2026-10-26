-- Shipped handlers, native APIs mocked. Actual playback and attack cycle require Warcraft.
for p=0,11 do RosterReset(p)end
TimeNow=12000000;CampaignTransition=false;CampaignStage=0;World={}
local shika=CreateUnit(6,raw('R006'),0,0,0);Hero[6]=shika;HeroType[6]=shika.type;HeroRole[6]=6
shika.abilities[raw('R601')]=4
local main=CreateUnit(12,123,600,0,0);main.hp=10000;main.hero=true
local nearTarget=CreateUnit(12,124,950,0,0);nearTarget.hp=10000
local nearCasterOnly=CreateUnit(12,125,-300,0,0);nearCasterOnly.hp=10000
World={main,nearTarget,nearCasterOnly}
Caster=shika;Spell=raw('R601');Target=main;AudioQueued={};SkillsEffect()
assert(SkillAudio[30]==29 and AudioQueued[29] and AudioQueued[5],'Both source voice and source impact are queued')
assert(ShadowTarget[6]==main and #Shadow43Helpers[6]==1,'Fourth rank expands around target, not caster')
local helper=Shadow43Helpers[6][1];assert(helper.x==600 and helper.last.o=='magicleash' and helper.last.target==nearTarget)
assert(StoryStatChoice(6)==9,'Agility-primary Shikamaru buys agility scrolls')
SkillsEndcast();assert(not ShadowTarget[6] and helper.removed and #Shadow43Helpers[6]==0,'Channel end removes only this caster helpers')
-- Actual summon callback registers only Naruto illusions, exactly once.
local oldCreate,oldAction=CreateTrigger,TriggerAddAction
function CreateTrigger()return {actions={}}end
function TriggerAddAction(t,f)t.actions[#t.actions+1]=f end
local oldRegistration=TriggerRegisterUnitEvent
function TriggerRegisterUnitEvent(t,u,event)t.unitEvents=t.unitEvents or{};t.unitEvents[#t.unitEvents+1]={unit=u,event=event}end
local oldSummoner,oldSummoned,oldTrigger,oldDamage=GetSummoningUnit,GetSummonedUnit,GetTriggerUnit,GetEventDamage
local image=CreateUnit(0,raw('R000'),0,0,0);image.illusion=true;image.hp=500
local summoner=Hero[0]
function GetSummoningUnit()return summoner end
function GetSummonedUnit()return image end
SkillsSummoned();local hook=LoadTriggerHandle(Clone43State,GetHandleId(image),0)
assert(hook and #hook.unitEvents==1 and hook.unitEvents[1].event==EVENT_UNIT_DAMAGED)
SkillsSummoned();assert(LoadTriggerHandle(Clone43State,GetHandleId(image),0)==hook and #hook.unitEvents==1)
-- Mere attack initiation and zero/missed damage leave the clone and attack cycle intact.
local eventDamage=0;function GetTriggerUnit()return image end;function GetEventDamage()return eventDamage end
SkillsFragileClone();assert(image.hp==500 and not hook.destroyed)
eventDamage=17;hook.actions[1]();assert(image.hp==0 and hook.destroyed and not IsUnitInGroup(image,Clone43Units))
assert(not LoadTriggerHandle(Clone43State,GetHandleId(image),0),'Release the registration and handle references immediately')
-- No attacker order, time-scale, movement or cooldown modifications in the handler.
local ordinary=CreateUnit(0,raw('R000'),0,0,0);Clone43Track(ordinary);assert(not IsUnitInGroup(ordinary,Clone43Units))
local other=CreateUnit(0,raw('R001'),0,0,0);other.illusion=true;Clone43Track(other);assert(not IsUnitInGroup(other,Clone43Units))
local hooks={};for i=1,40 do local c=CreateUnit(0,raw('Rnfm'),0,0,0);c.illusion=true;Clone43Track(c);hooks[i]={c,LoadTriggerHandle(Clone43State,GetHandleId(c),0)}end
for _,pair in ipairs(hooks)do pair[1].hp=0 end
Clone43Prune();for _,pair in ipairs(hooks)do assert(pair[2].destroyed and not IsUnitInGroup(pair[1],Clone43Units))end
-- Both Hyuuga heroes keep independent self-only attack bonuses, expiry and death cleanup.
for _,p in ipairs({4,8})do Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;HeroType[p]=Hero[p].type;RosterVision(p,2);assert(GetUnitAbilityLevel(Hero[p],raw('Rbv3'))==2)end
RosterClearVision(4);assert(GetUnitAbilityLevel(Hero[4],raw('Rbv3'))==0 and GetUnitAbilityLevel(Hero[8],raw('Rbv3'))==2)
TimeNow=TimeNow+16;RosterTick();assert(GetUnitAbilityLevel(Hero[8],raw('Rbv3'))==0)
RosterVision(4,1);Hero[4].hp=0;RosterTick();assert(GetUnitAbilityLevel(Hero[4],raw('Rbv3'))==0)
Hero[4].hp=10000;main.x=100;main.y=0;main.hp=10000;World={main};local cursor=StunCursor
RosterRepel(4,2);local stun=StunDummy[cursor];assert(stun and GetUnitAbilityLevel(stun,raw('Rkt3'))==1 and stun.last.target==main)
for _,index in ipairs({21,41})do local p=index==21 and 4 or 8;Hero[p].hp=10000;main.x=100;Hits={};World={main};RosterApply(p,index,1,nil);assert(Hits[1].damage==156)end
GetSummoningUnit,GetSummonedUnit,GetTriggerUnit,GetEventDamage=oldSummoner,oldSummoned,oldTrigger,oldDamage
TriggerRegisterUnitEvent=oldRegistration
CreateTrigger,TriggerAddAction=oldCreate,oldAction
for p=0,11 do RosterReset(p)end
print('PASS: source Shikamaru voice+impact/target-centered shadow/helper endcast and agility shopping; actual summon/damage hooks/no death on windup or zero damage/40-clone cleanup; independent Byakugan bonus expiry/death and enhanced Kaiten/dedicated stun (native mocks).')
