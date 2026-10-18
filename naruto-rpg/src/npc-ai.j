function NPCBusy takes unit u returns boolean
    if NPCCooldowns==null then
        return false
    endif
    return LoadReal(NPCCooldowns,GetHandleId(u),0)>TimeNow
endfunction
function NPCUseInventory takes unit u, integer kind, unit target returns boolean
    local integer j=0
    local integer raw=0
    local integer hid=GetHandleId(u)
    local item it=null
    local boolean used=false
    if kind!=11 and kind!=13 then
        return false
    endif
    if NPCCooldowns==null then
        set NPCCooldowns=InitHashtable()
    endif
    if kind==13 and CampaignStage==28 and GetWidgetLife(u)<=35000. and not LoadBoolean(NPCCooldowns,hid,-2) then
        call SaveBoolean(NPCCooldowns,hid,-2,true)
        call UnitAddAbility(u,'AInv')
        loop
            exitwhen j>=4
            call UnitAddItemByIdSwapped('Nlra',u)
            set j=j+1
        endloop
        set j=0
    endif
    if TimeNow<LoadReal(NPCCooldowns,hid,-1) then
        return false
    endif
    loop
        exitwhen j>=6
        set it=UnitItemInSlot(u,j)
        set raw=GetItemTypeId(it)
        if raw=='Nlra' and GetWidgetLife(u)<GetUnitState(u,UNIT_STATE_MAX_LIFE)*.85 then
            set used=UnitUseItemTarget(u,it,u)
        elseif raw=='Nlku' or raw=='Nlsh' then
            set used=UnitUseItemTarget(u,it,target)
        elseif raw=='Nnot' then
            set used=UnitUseItemPoint(u,it,GetUnitX(target),GetUnitY(target))
        endif
        if used then
            call SaveReal(NPCCooldowns,hid,-1,TimeNow+6.)
            call SaveReal(NPCCooldowns,hid,0,TimeNow+1.)
            set it=null
            return true
        endif
        set j=j+1
    endloop
    set it=null
    return false
endfunction
function NPCLongChannelEnd takes nothing returns nothing
    local integer hid=GetHandleId(GetTriggerUnit())
    if NPCCooldowns!=null and LoadInteger(NPCCooldowns,hid,-3)!=0 and LoadInteger(NPCCooldowns,hid,-3)==GetSpellAbilityId() then
        call SaveReal(NPCCooldowns,hid,0,TimeNow)
        call SaveInteger(NPCCooldowns,hid,-3,0)
    endif
endfunction
function NPCTry takes unit u, integer kind, unit target returns boolean
    local integer k=0
    local integer i=0
    local integer other=0
    local integer hid=GetHandleId(u)
    local real dx=GetUnitX(target)-GetUnitX(u)
    local real dy=GetUnitY(target)-GetUnitY(u)
    local real distance=SquareRoot(dx*dx+dy*dy)
    local boolean issued=false
    if NPCCooldowns==null then
        set NPCCooldowns=InitHashtable()
    endif
    if kind==8 and GetWidgetLife(u)<5000. and GetUnitAbilityLevel(u,'S02B')==0 then
        call UnitAddAbility(u,'S02B')
    endif
    if NPCHiddenAbilities==null then
        set NPCHiddenAbilities=InitHashtable()
    endif
    if NPCEndHook==null then
        set NPCEndHook=CreateTrigger()
        call TriggerRegisterAnyUnitEventBJ(NPCEndHook,EVENT_PLAYER_UNIT_SPELL_ENDCAST)
        call TriggerRegisterAnyUnitEventBJ(NPCEndHook,EVENT_PLAYER_UNIT_SPELL_FINISH)
        call TriggerAddAction(NPCEndHook,function NPCLongChannelEnd)
    endif
    loop
        exitwhen k>=NPCSpellCount[kind]
        set i=kind*8+k
        if TimeNow>=LoadReal(NPCCooldowns,hid,NPCAbility[i]) and GetUnitState(u,UNIT_STATE_MANA)>=NPCCost[i] and (GetUnitAbilityLevel(u,NPCAbility[i])>0 or LoadBoolean(NPCHiddenAbilities,hid,NPCAbility[i])) then
            if NPCOrder[i]!="" then
                set other=0
                loop
                    exitwhen other>=NPCSpellCount[kind]
                    if kind*8+other!=i and NPCOrder[kind*8+other]==NPCOrder[i] and GetUnitAbilityLevel(u,NPCAbility[kind*8+other])>0 then
                        call SaveBoolean(NPCHiddenAbilities,hid,NPCAbility[kind*8+other],true)
                        call UnitRemoveAbility(u,NPCAbility[kind*8+other])
                    endif
                    set other=other+1
                endloop
                if GetUnitAbilityLevel(u,NPCAbility[i])==0 then
                    call UnitAddAbility(u,NPCAbility[i])
                    call SetUnitAbilityLevel(u,NPCAbility[i],NPCRank[i])
                endif
                call SaveBoolean(NPCHiddenAbilities,hid,NPCAbility[i],false)
            endif
            if NPCTarget[i]==4 then
                if GetWidgetLife(u)<=3000. then
                    set issued=IssueTargetOrder(u,NPCOrder[i],u)
                elseif distance<=NPCRange[i] then
                    set issued=IssueTargetOrder(u,NPCOrder[i],target)
                endif
            elseif NPCTarget[i]==0 and distance<=RMaxBJ(300.,NPCRadius[i]) then
                if NPCOrderId[i]>0 then
                    set issued=IssueImmediateOrderById(u,NPCOrderId[i])
                else
                    set issued=IssueImmediateOrder(u,NPCOrder[i])
                endif
            elseif NPCTarget[i]==1 and distance<=NPCRange[i] and IsUnitEnemy(target,GetOwningPlayer(u)) then
                set issued=IssueTargetOrder(u,NPCOrder[i],target)
            elseif NPCTarget[i]==2 and distance<=NPCRange[i] and IsUnitEnemy(target,GetOwningPlayer(u)) then
                set issued=IssuePointOrder(u,NPCOrder[i],GetUnitX(target),GetUnitY(target))
            elseif NPCTarget[i]==3 and distance<=NPCRange[i] and IsUnitAlly(target,GetOwningPlayer(u)) and GetWidgetLife(target)<GetUnitState(target,UNIT_STATE_MAX_LIFE)*.8 then
                set issued=IssueTargetOrder(u,NPCOrder[i],target)
            endif
            if issued then
                call SaveReal(NPCCooldowns,hid,NPCAbility[i],TimeNow+NPCCooldown[i])
                call SaveReal(NPCCooldowns,hid,0,TimeNow+NPCHold[i])
                if NPCChannelGuard[i] then
                    call SaveInteger(NPCCooldowns,hid,-3,NPCAbility[i])
                else
                    call SaveInteger(NPCCooldowns,hid,-3,0)
                endif
                return true
            endif
        endif
        set k=k+1
    endloop
    return false
endfunction
