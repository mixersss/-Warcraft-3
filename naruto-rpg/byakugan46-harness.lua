-- Actual player skill cast dispatch. Native % damage/UI need Warcraft validation.
for p=0,11 do RosterReset(p)end
CampaignStage=0;CampaignTransition=false;CampaignFinished=false;TimeNow=16000000;World={}
local timers=CreatedTimers
for _,p in ipairs({4,8})do
 Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;HeroType[p]=Hero[p].type
 Hero[p].str=45;Hero[p].agi=125;Hero[p].int=22
end
local function castVision(p,rank)
 Caster=Hero[p];Target=nil;Spell=PlayableSkill[p*5];Caster.abilities[Spell]=rank
 SkillsEffect()
 assert(GetUnitAbilityLevel(Caster,raw('Rbv3'))==rank,'The hidden percentage must follow the actual learned Byakugan rank')
 assert(GetUnitAbilityLevel(Caster,raw('Rbyg'))==rank,'Detection must still use its matching rank')
 assert(Caster.str==45 and Caster.agi==125 and Caster.int==22,'Damage bonus must never change hero attributes')
end
for rank=1,4 do
 for _,p in ipairs({4,8})do castVision(p,rank)end
 assert(GetUnitAbilityLevel(Hero[4],raw('Rbv3'))==rank and GetUnitAbilityLevel(Hero[8],raw('Rbv3'))==rank)
 TimeNow=TimeNow+15.1;RosterTick()
 for _,p in ipairs({4,8})do assert(GetUnitAbilityLevel(Hero[p],raw('Rbv3'))==0 and GetUnitAbilityLevel(Hero[p],raw('Rbyg'))==0)end
end
castVision(4,3);local art=VisionArt[4];TimeNow=TimeNow+2;castVision(8,2)
castVision(4,4);assert(not art.alive,'Recast replaces its prior bonus/art, never stacks')
TimeNow=TimeNow+1;RosterClearVision(4)
assert(GetUnitAbilityLevel(Hero[4],raw('Rbv3'))==0 and GetUnitAbilityLevel(Hero[8],raw('Rbv3'))==2,'Each hero owns only their own bonus')
Hero[8].hp=0;RosterTick();assert(GetUnitAbilityLevel(Hero[8],raw('Rbv3'))==0 and not VisionArt[8])
assert(CreatedTimers==timers,'Use existing vision expiry; no new timers')
for p=0,11 do RosterReset(p)end
print('PASS: both actual Byakugan cast dispatches propagate4 learned ranks, preserve STR/AGI/INT and detection, expire15s, replace recasts, isolate heroes and clear on death without new timers (native mocks).')
