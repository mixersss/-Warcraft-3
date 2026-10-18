// Original AIpr totals (400 HP + 400 mana / 20 s), without its full-pool gate.
// One shared heartbeat. Damage does not cancel recovery; refresh never stacks.
function RamenClear takes integer slot returns nothing
    if RamenArt[slot]!=null then
        call DestroyEffect(RamenArt[slot])
        set RamenArt[slot]=null
    endif
    set RamenUnit[slot]=null
    set RamenUntil[slot]=0.
endfunction
function RamenClearUnit takes unit u returns nothing
    local integer slot=0
    loop
        exitwhen slot>=64
        if RamenUnit[slot]==u then
            call RamenClear(slot)
        endif
        set slot=slot+1
    endloop
endfunction
function RamenUse takes nothing returns nothing
    local unit u=GetManipulatingUnit()
    local integer slot=0
    local integer free=-1
    if GetItemTypeId(GetManipulatedItem())!='Nlra' or not FoundationAlive(u) then
        set u=null
        return
    endif
    loop
        exitwhen slot>=64
        if RamenUnit[slot]==u then
            set free=slot
            exitwhen true
        elseif RamenUnit[slot]==null and free<0 then
            set free=slot
        endif
        set slot=slot+1
    endloop
    if free>=0 then
        call RamenClear(free)
        set RamenUnit[free]=u
        set RamenUntil[free]=TimeNow+20.
        set RamenLast[free]=TimeNow
        set RamenArt[free]=AddSpecialEffectTarget("Abilities\\Spells\\Items\\ReplenishHealth\\ReplenishHealthCaster.mdl",u,"origin")
    endif
    set u=null
endfunction
function RamenTick takes nothing returns nothing
    local integer slot=0
    local unit u=null
    local real amount=0.
    loop
        exitwhen slot>=64
        set u=RamenUnit[slot]
        if u!=null then
            if not FoundationAlive(u) or GetUnitTypeId(u)==0 then
                call RamenClear(slot)
            else
                set amount=RMaxBJ(0.,RMinBJ(TimeNow,RamenUntil[slot])-RamenLast[slot])*20.
                call SetWidgetLife(u,RMinBJ(GetUnitState(u,UNIT_STATE_MAX_LIFE),GetWidgetLife(u)+amount))
                call SetUnitState(u,UNIT_STATE_MANA,RMinBJ(GetUnitState(u,UNIT_STATE_MAX_MANA),GetUnitState(u,UNIT_STATE_MANA)+amount))
                set RamenLast[slot]=TimeNow
                if TimeNow>=RamenUntil[slot] then
                    call RamenClear(slot)
                endif
            endif
        endif
        set slot=slot+1
    endloop
    set u=null
endfunction
