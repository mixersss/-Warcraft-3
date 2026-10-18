// Real point-target inventory cast, native charges; one bounded shared trap heartbeat.
function NoteClear takes integer slot returns nothing
    if NoteActor[slot]!=null then
        call RemoveUnit(NoteActor[slot])
    endif
    set NoteActor[slot]=null
    set NoteArmedAt[slot]=0.
    set NoteExpiresAt[slot]=0.
endfunction
function NoteClearAll takes nothing returns nothing
    local integer slot=0
    loop
        exitwhen slot>=128
        call NoteClear(slot)
        set slot=slot+1
    endloop
endfunction
function NoteCast takes nothing returns nothing
    local unit caster=GetTriggerUnit()
    local integer slot=NoteCursor
    if GetSpellAbilityId()!='Lexp' or not FoundationAlive(caster) then
        set caster=null
        return
    endif
    if NoteGroup==null then
        set NoteGroup=CreateGroup()
    endif
    call NoteClear(slot)
    set NoteActor[slot]=CreateUnit(GetOwningPlayer(caster),'rnnt',GetSpellTargetX(),GetSpellTargetY(),0.)
    call SetUnitPathing(NoteActor[slot],false)
    set NoteArmedAt[slot]=TimeNow+1.5
    set NoteExpiresAt[slot]=TimeNow+180.
    set NoteCursor=ModuloInteger(slot+1,128)
    set caster=null
endfunction
function NoteEnemy takes unit target, unit actor returns boolean
    return FoundationAlive(target) and target!=actor and IsUnitEnemy(target,GetOwningPlayer(actor)) and not IsUnitHidden(target) and not IsUnitType(target,UNIT_TYPE_FLYING) and GetUnitAbilityLevel(target,'Avul')==0
endfunction
function NoteTick takes nothing returns nothing
    local integer slot=0
    local unit target=null
    local unit actor=null
    local real dx=0.
    local real dy=0.
    local boolean exploded=false
    loop
        exitwhen slot>=128
        set actor=NoteActor[slot]
        if actor!=null then
            if not FoundationAlive(actor) or TimeNow>=NoteExpiresAt[slot] then
                call NoteClear(slot)
            elseif TimeNow>=NoteArmedAt[slot] then
                set exploded=false
                call GroupEnumUnitsInRange(NoteGroup,GetUnitX(actor),GetUnitY(actor),300.,null)
                loop
                    set target=FirstOfGroup(NoteGroup)
                    exitwhen target==null
                    call GroupRemoveUnit(NoteGroup,target)
                    if NoteEnemy(target,actor) then
                        set exploded=true
                        set dx=GetUnitX(target)-GetUnitX(actor)
                        set dy=GetUnitY(target)-GetUnitY(actor)
                        if dx*dx+dy*dy<=100.*100. then
                            call UnitDamageTarget(actor,target,400.,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_NORMAL,WEAPON_TYPE_WHOKNOWS)
                        else
                            call UnitDamageTarget(actor,target,300.,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_NORMAL,WEAPON_TYPE_WHOKNOWS)
                        endif
                    endif
                endloop
                if exploded then
                    call DestroyEffect(AddSpecialEffect("Objects\\Spawnmodels\\Other\\NeutralBuildingExplosion\\NeutralBuildingExplosion.mdl",GetUnitX(actor),GetUnitY(actor)))
                    call NoteClear(slot)
                endif
            endif
        endif
        set slot=slot+1
    endloop
    set target=null
    set actor=null
endfunction
