// Per-cast helper cleanup, never the original global removal of another caster's units.
function Shadow43RemoveHelper takes nothing returns nothing
    call RemoveUnit(GetEnumUnit())
endfunction
// 1.26 has no global damaged event. Each actual clone owns one bounded registration,
// removed immediately after a hit or on the existing half-second cleanup heartbeat.
function Clone43Release takes unit u returns nothing
    local integer key=GetHandleId(u)
    local trigger hit=LoadTriggerHandle(Clone43State,key,0)
    if hit!=null then
        call DestroyTrigger(hit)
    endif
    call FlushChildHashtable(Clone43State,key)
    call GroupRemoveUnit(Clone43Units,u)
    set hit=null
endfunction
function SkillsFragileClone takes nothing returns nothing
    local unit u=GetTriggerUnit()
    // ATTACKED fires before the hit and cancelling its target bypasses the attack cycle.
    // A positive damage event is an actual impact, including spell hits in Classic.
    if GetEventDamage()>0. and IsUnitIllusion(u) and (GetUnitTypeId(u)=='R000' or GetUnitTypeId(u)=='Rnfm') then
        call Clone43Release(u)
        if FoundationAlive(u) then
            call DestroyEffect(AddSpecialEffect("Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl",GetUnitX(u),GetUnitY(u)))
            call KillUnit(u)
        endif
    endif
    set u=null
endfunction
function Clone43Track takes unit u returns nothing
    local trigger hit=null
    if not FoundationAlive(u) or not IsUnitIllusion(u) or (GetUnitTypeId(u)!='R000' and GetUnitTypeId(u)!='Rnfm') then
        return
    endif
    if Clone43Units==null then
        set Clone43Units=CreateGroup()
        set Clone43State=InitHashtable()
    endif
    if not IsUnitInGroup(u,Clone43Units) then
        set hit=CreateTrigger()
        call TriggerRegisterUnitEvent(hit,u,EVENT_UNIT_DAMAGED)
        call TriggerAddAction(hit,function SkillsFragileClone)
        call SaveTriggerHandle(Clone43State,GetHandleId(u),0,hit)
        call GroupAddUnit(Clone43Units,u)
    endif
    set hit=null
endfunction
function Clone43PruneOne takes nothing returns nothing
    local unit u=GetEnumUnit()
    if not FoundationAlive(u) or GetUnitTypeId(u)==0 then
        call Clone43Release(u)
    endif
    set u=null
endfunction
function Clone43Prune takes nothing returns nothing
    if Clone43Units!=null then
        call ForGroup(Clone43Units,function Clone43PruneOne)
    endif
endfunction
