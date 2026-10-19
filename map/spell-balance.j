// The native shared damage/heal values are zero. Preserve native mana, cooldown,
// targeting and art; resolve damage separately so healing/mana burn stay intact.
// No per-cast handles, timers, groups or local-player state.
function OnHybridSpell takes nothing returns nothing
    local unit caster=GetTriggerUnit()
    local unit target=GetSpellTargetUnit()
    local integer raw=GetSpellAbilityId()
    local integer kind=HybridSpellKind(raw)
    local integer rank=GetUnitAbilityLevel(caster,raw)
    local real power=0.
    if GetTriggerEventId()==EVENT_PLAYER_UNIT_SPELL_EFFECT and kind>=0 and rank>0 and rank<=200 and Alive(caster) and Alive(target) then
        set power=HybridPower[kind*200+rank-1]
        if kind==2 then
            set power=RMinBJ(power,GetUnitState(target,UNIT_STATE_MANA))
            call SetUnitState(target,UNIT_STATE_MANA,GetUnitState(target,UNIT_STATE_MANA)-power)
            if power>0. then
                call UnitDamageTarget(caster,target,power*SPELL_DAMAGE_MULTIPLIER,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS)
            endif
        elseif IsUnitEnemy(target,GetOwningPlayer(caster)) then
            call UnitDamageTarget(caster,target,power*.5*SPELL_DAMAGE_MULTIPLIER,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS)
        else
            call SetUnitState(target,UNIT_STATE_LIFE,RMinBJ(GetUnitState(target,UNIT_STATE_MAX_LIFE),GetWidgetLife(target)+power))
        endif
    endif
    set caster=null
    set target=null
endfunction
