-- Exercise the shipped Transmute event handler, not a duplicate reward function.
EVENT_PLAYER_UNIT_SPELL_EFFECT='effect'
EVENT_PLAYER_UNIT_SPELL_CAST='cast'
EVENT_PLAYER_UNIT_SPELL_FINISH='finish'
EVENT_PLAYER_UNIT_SPELL_ENDCAST='endcast'
function GetTriggerEventId() return SpellEvent end
function GetSpellTargetUnit() return SpellTarget end
local function event(kind)
    Dying=Hero[0];SpellId=FourCC('ANtm');SpellEvent=kind;OnTransmute()
end
for _,bot in ipairs({false,true}) do
 for rank=1,50 do
    reset();Bot[0]=bot;CreateHero(0,23)
    Hero[0].abilities[FourCC('ANtm')]=rank
    SpawnWave(3);SpellTarget=Army[3][1]
    local gold=Players[0].gold
    event('cast');event('effect');assert(Players[0].gold==gold,'No award just for starting a cast')
    SpellTarget.removed=true
    event('finish')
    assert(Players[0].gold==gold+100+30*(rank-1),'Exact fixed reward for humans AND bots at every rank')
    assert(not TransmuteTarget[0] and TransmuteReward[0]==0,'Release target handles')
    event('finish');event('endcast');assert(Players[0].gold==gold+100+30*(rank-1),'No duplicate rewards')
    if bot then assert(GearSavings[0]>0 and TierSavings[0]>0,'Ordinary budget allocation')end
 end
end
reset();Hero[0].abilities[FourCC('ANtm')]=1
SpawnWave(3);SpellTarget=Army[3][1];local gold=Players[0].gold
event('effect');event('finish');assert(Players[0].gold==gold,'Live victim cannot pay gold')
event('effect');event('endcast');SpellTarget.removed=true
event('finish');assert(Players[0].gold==gold,'Interrupted cast cannot pay later')
SpellTarget=nil;event('effect');event('finish');assert(Players[0].gold==gold,'No target gives no reward')
-- If the native kill also emits a death event, suppress the ordinary gold bounty.
reset();Hero[0].abilities[FourCC('ANtm')]=2
SpawnWave(3);SpellTarget=Army[3][1];gold=Players[0].gold
event('effect');Dying=SpellTarget;Killer=Hero[0];Dying.hp=0;OnDeath()
assert(Players[0].gold==gold,'Transmute victim cannot pay a second kill bounty')
event('finish');assert(Players[0].gold==gold+130)
-- Also cover native removal/death BEFORE the effect callback.
reset();Hero[0].abilities[FourCC('ANtm')]=3
SpawnWave(3);SpellTarget=Army[3][1];gold=Players[0].gold
event('cast');Dying=SpellTarget;Killer=Hero[0];Dying.hp=0;OnDeath()
assert(Players[0].gold==gold);event('effect');event('finish')
assert(Players[0].gold==gold+160,'Early native kill still pays exactly once')
reset();Hero[0].abilities[FourCC('ANtm')]=1
SpawnWave(3);SpellTarget=Army[3][1];gold=Players[0].gold
event('cast');SpellTarget.removed=true;event('finish')
assert(Players[0].gold==gold,'Cast without effect cannot pay')
-- An unrelated kill during the cast retains its normal gold award.
reset();Hero[0].abilities[FourCC('ANtm')]=1
SpawnWave(3);SpellTarget=Army[3][1];gold=Players[0].gold
event('effect');Dying=Army[3][2];Killer=Hero[0];Dying.hp=0;OnDeath()
assert(Players[0].gold>gold,'Other kills still award gold')
event('endcast');assert(not TransmuteTarget[0])
print('PASS: exact Transmute gold at all 50 ranks for humans/bots, native removal/death paths, no extra bounty, no failed/interrupted/duplicate rewards and budget allocation (mock natives).')
