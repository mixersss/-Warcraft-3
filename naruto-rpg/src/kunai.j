// One tracked homing kunai per caster; shared 0.05s clock, no cast timers/triggers.
function KunaiClear takes integer p returns nothing
    if KunaiMissile[p]!=null then
        call RemoveUnit(KunaiMissile[p])
    endif
    set KunaiMissile[p]=null
    set KunaiCaster[p]=null
    set KunaiTarget[p]=null
    set KunaiUntil[p]=0.
endfunction
function KunaiValid takes unit caster, unit target returns boolean
    return caster!=null and GetUnitTypeId(caster)!=0 and FoundationAlive(target) and not IsUnitHidden(target) and IsUnitEnemy(target,GetOwningPlayer(caster)) and not IsUnitType(target,UNIT_TYPE_STRUCTURE) and not IsUnitType(target,UNIT_TYPE_MAGIC_IMMUNE) and GetUnitAbilityLevel(target,'Avul')==0
endfunction
function KunaiLaunch takes integer p, integer rank, unit target returns nothing
    call KunaiClear(p)
    if not KunaiValid(Hero[p],target) then
        return
    endif
    set KunaiCaster[p]=Hero[p]
    set KunaiTarget[p]=target
    set KunaiDamage[p]=RosterPower[100+rank-1]
    set KunaiUntil[p]=TimeNow+2.
    set KunaiMissile[p]=CreateUnit(Player(p),'vkun',GetUnitX(Hero[p]),GetUnitY(Hero[p]),GetUnitFacing(Hero[p]))
    call SetUnitPathing(KunaiMissile[p],false)
    call SetUnitFlyHeight(KunaiMissile[p],100.,0.)
endfunction
function KunaiImpact takes integer p returns nothing
    local unit target=KunaiTarget[p]
    local unit dummy=null
    if KunaiValid(KunaiCaster[p],target) then
        if UnitDamageTarget(KunaiCaster[p],target,KunaiDamage[p],false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS) and FoundationAlive(target) then
            if StunDummy[StunCursor]!=null then
                call RemoveUnit(StunDummy[StunCursor])
            endif
            set dummy=CreateUnit(GetOwningPlayer(KunaiCaster[p]),'rdst',GetUnitX(target),GetUnitY(target),0.)
            call UnitRemoveAbility(dummy,'Rstn')
            call UnitAddAbility(dummy,'Rkst')
            set StunDummy[StunCursor]=dummy
            set StunExpires[StunCursor]=TimeNow+1.5
            set StunCursor=ModuloInteger(StunCursor+1,128)
            call IssueTargetOrder(dummy,"thunderbolt",target)
        endif
    endif
    call KunaiClear(p)
    set target=null
    set dummy=null
endfunction
function KunaiTick takes nothing returns nothing
    local integer p=0
    local real dx=0.
    local real dy=0.
    local real distance=0.
    loop
        exitwhen p>=12
        if KunaiMissile[p]!=null then
            if not KunaiValid(KunaiCaster[p],KunaiTarget[p]) or TimeNow>=KunaiUntil[p] then
                call KunaiClear(p)
            else
                set dx=GetUnitX(KunaiTarget[p])-GetUnitX(KunaiMissile[p])
                set dy=GetUnitY(KunaiTarget[p])-GetUnitY(KunaiMissile[p])
                set distance=SquareRoot(dx*dx+dy*dy)
                if distance<=75. then
                    call KunaiImpact(p)
                else
                    call SetUnitX(KunaiMissile[p],GetUnitX(KunaiMissile[p])+dx/distance*75.)
                    call SetUnitY(KunaiMissile[p],GetUnitY(KunaiMissile[p])+dy/distance*75.)
                    call SetUnitFacing(KunaiMissile[p],Atan2(dy,dx)*bj_RADTODEG)
                endif
            endif
        endif
        set p=p+1
    endloop
endfunction
