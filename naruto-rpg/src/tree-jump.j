// Native Eat Tree provides smart/right-click targeting only. Its 10s cast point
// gives the shared timer time to cancel it before any native tree consumption.
function TreeJumpTree takes destructable target returns boolean
    local integer raw=0
    if target==null then
        return false
    endif
    set raw=GetDestructableTypeId(target)
    return target!=null and GetWidgetLife(target)>.405 and (raw=='LTlt' or raw=='CTtc' or raw=='ATtr' or raw=='BTtw' or raw=='NTtw')
endfunction
function TreeJumpInside takes integer p, real x, real y returns boolean
    local integer t=(p-ModuloInteger(p,3))/3
    local real ox=0.
    local real oy=0.
    if ModuloInteger(t,2)==1 then
        set ox=8192.
    endif
    if t>=2 then
        set oy=-4864.
    endif
    return x>-16352.+ox and x<-8320.+ox and y>11808.+oy and y<16352.+oy
endfunction
function TreeJumpEnd takes integer p returns nothing
    local unit u=JumpUnit[p]
    if u!=null and GetUnitTypeId(u)!=0 then
        call SetUnitPathing(u,true)
        call SetUnitFlyHeight(u,JumpBaseHeight[p],0.)
        if FoundationAlive(u) then
            call SetUnitPosition(u,JumpTX[p],JumpTY[p])
            if not TreeJumpInside(p,GetUnitX(u),GetUnitY(u)) then
                call SetUnitPosition(u,JumpSX[p],JumpSY[p])
            endif
            call SetUnitAnimation(u,"stand")
        endif
    endif
    set JumpUnit[p]=null
    set JumpQueued[p]=null
    set JumpElapsed[p]=0.
    set u=null
endfunction
function TreeJumpQueue takes integer p, destructable target returns nothing
    if TreeJumpTree(target) then
        set JumpQueued[p]=target
    endif
endfunction
function TreeJumpOrder takes nothing returns nothing
    local unit u=GetOrderedUnit()
    local integer p=GetPlayerId(GetOwningPlayer(u))
    local integer order=GetIssuedOrderId()
    if p<12 and u==Hero[p] and (order==OrderId("smart") or order==OrderId("eattree")) then
        call TreeJumpQueue(p,GetOrderTargetDestructable())
    endif
    set u=null
endfunction
function TreeJumpChannel takes nothing returns nothing
    local integer p=GetPlayerId(GetOwningPlayer(GetTriggerUnit()))
    if p<12 and GetTriggerUnit()==Hero[p] and GetSpellAbilityId()=='Rjtr' then
        call TreeJumpQueue(p,GetSpellTargetDestructable())
    endif
endfunction
function TreeJumpBegin takes integer p, destructable target returns nothing
    local unit u=Hero[p]
    local real tx=GetDestructableX(target)
    local real ty=GetDestructableY(target)
    local real dx=tx-GetUnitX(u)
    local real dy=ty-GetUnitY(u)
    local real angle=Atan2(dy,dx)
    local real x=0.
    local real y=0.
    local real a=0.
    local integer n=0
    local boolean found=false
    call IssueImmediateOrder(u,"stop")
    if not FoundationAlive(u) or JumpUnit[p]!=null or IsUnitPaused(u) or IsUnitType(u,UNIT_TYPE_SNARED) or IsUnitType(u,UNIT_TYPE_STUNNED) then
        set u=null
        return
    endif
    if TimeNow<JumpReadyAt[p] or GetUnitState(u,UNIT_STATE_MANA)<50. then
        call DisplayTimedTextToPlayer(Player(p),0.,0.,3.,"Прыжок: нужно 50 чакры; перезарядка 3 секунды.")
        set u=null
        return
    endif
    if not TreeJumpTree(target) or GetUnitTypeId(u)!=HeroType[p] or dx*dx+dy*dy>1000.*1000. or not TreeJumpInside(p,tx,ty) then
        call DisplayTimedTextToPlayer(Player(p),0.,0.,3.,"Прыжок доступен в обычной форме, на живое дерево своего леса в радиусе 1000.")
        set u=null
        return
    endif
    // Land on a clear branch-side patch, then let native collision settle the unit.
    loop
        exitwhen n>=24 or found
        set a=angle+(ModuloInteger(n,8))*bj_PI/4.
        set x=tx+Cos(a)*(144.+I2R((n-ModuloInteger(n,8))/8)*64.)
        set y=ty+Sin(a)*(144.+I2R((n-ModuloInteger(n,8))/8)*64.)
        if TreeJumpInside(p,x,y) and not IsTerrainPathable(x,y,PATHING_TYPE_WALKABILITY) then
            set found=true
        endif
        set n=n+1
    endloop
    if not found then
        call DisplayTimedTextToPlayer(Player(p),0.,0.,3.,"У этого дерева нет свободного места для приземления.")
        set u=null
        return
    endif
    set JumpSX[p]=GetUnitX(u)
    set JumpSY[p]=GetUnitY(u)
    set JumpTX[p]=x
    set JumpTY[p]=y
    set JumpBaseHeight[p]=GetUnitFlyHeight(u)
    set JumpElapsed[p]=0.
    set JumpUnit[p]=u
    set JumpReadyAt[p]=TimeNow+3.
    call SetUnitState(u,UNIT_STATE_MANA,GetUnitState(u,UNIT_STATE_MANA)-50.)
    call UnitAddAbility(u,'Amrf')
    call UnitRemoveAbility(u,'Amrf')
    call SetUnitPathing(u,false)
    call SetUnitFacing(u,bj_RADTODEG*angle)
    call SetUnitAnimation(u,"walk")
    call DestroyEffect(AddSpecialEffect("Abilities\\Spells\\Human\\FlakCannons\\FlakTarget.mdl",JumpSX[p],JumpSY[p]))
    call FoundationSound(9)
    set u=null
endfunction
function TreeJumpTick takes nothing returns nothing
    local integer p=0
    local real progress=0.
    local destructable target=null
    loop
        exitwhen p>=12
        if JumpQueued[p]!=null then
            set target=JumpQueued[p]
            set JumpQueued[p]=null
            call TreeJumpBegin(p,target)
        endif
        if JumpUnit[p]!=null then
            if not FoundationAlive(JumpUnit[p]) or JumpUnit[p]!=Hero[p] then
                call TreeJumpEnd(p)
            else
                set JumpElapsed[p]=JumpElapsed[p]+.03125
                set progress=JumpElapsed[p]/.625
                if progress>=1. then
                    call TreeJumpEnd(p)
                else
                    call SetUnitX(JumpUnit[p],JumpSX[p]+(JumpTX[p]-JumpSX[p])*progress)
                    call SetUnitY(JumpUnit[p],JumpSY[p]+(JumpTY[p]-JumpSY[p])*progress)
                    call SetUnitFlyHeight(JumpUnit[p],JumpBaseHeight[p]+1440.*progress*(1.-progress),0.)
                endif
            endif
        endif
        set p=p+1
    endloop
    set target=null
endfunction
function TreeJumpInit takes nothing returns nothing
    local integer p=0
    local trigger orders=CreateTrigger()
    local trigger channels=CreateTrigger()
    local timer clock=CreateTimer()
    loop
        exitwhen p>=12
        call TriggerRegisterPlayerUnitEvent(orders,Player(p),EVENT_PLAYER_UNIT_ISSUED_TARGET_ORDER,null)
        call TriggerRegisterPlayerUnitEvent(channels,Player(p),EVENT_PLAYER_UNIT_SPELL_CHANNEL,null)
        set p=p+1
    endloop
    call TriggerAddAction(orders,function TreeJumpOrder)
    call TriggerAddAction(channels,function TreeJumpChannel)
    call TimerStart(clock,.03125,true,function TreeJumpTick)
    set orders=null
    set channels=null
    set clock=null
endfunction
