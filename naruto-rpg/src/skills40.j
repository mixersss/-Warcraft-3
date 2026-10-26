// Source mechanics with independent per-player state; one existing visual heartbeat.
// Foundation TimeNow advances in half-second steps; keep presentation deadlines on .05s.
function Source40SyncTime takes nothing returns nothing
    if Source40Now<TimeNow or Source40Now>TimeNow+.55 then
        set Source40Now=TimeNow
    endif
endfunction
function Source40Enemy takes unit u, integer p returns boolean
    return FoundationAlive(u) and IsUnitEnemy(u,Player(p)) and not IsUnitType(u,UNIT_TYPE_STRUCTURE) and GetUnitAbilityLevel(u,'Avul')==0
endfunction
function Source40HasPuppet takes integer p returns boolean
    return FoundationAlive(Companion[p*3]) or FoundationAlive(Companion[p*3+1]) or FoundationAlive(Companion[p*3+2])
endfunction
function Source40BallEnd takes integer p returns nothing
    if Source40Ball[p]!=null then
        call RemoveUnit(Source40Ball[p])
        set Source40Ball[p]=null
        if GetPlayerController(Player(p))!=MAP_CONTROL_COMPUTER and FoundationAlive(Hero[p]) then
            call SelectUnitForPlayerSingle(Hero[p],Player(p))
        endif
    endif
    if Source40BallCaster[p]==Hero[p] and FoundationAlive(Hero[p]) then
        call SetUnitTimeScale(Hero[p],1.)
        call SetUnitAnimation(Hero[p],"stand")
    endif
    set Source40BallCaster[p]=null
    set Source40BallAt[p]=0.
    set Source40BallUntil[p]=0.
    set Source40BallBudget[p]=0.
    set Source40BallPoseAt[p]=0.
    if VisualChannelIndex[p]==29 then
        set VisualChannelIndex[p]=-1
        set VisualChannelUntil[p]=0.
        set SkillPoseQueued[p]=false
    endif
endfunction
function Source40Clear takes integer p returns nothing
    local unit u=null
    call Source40BallEnd(p)
    set Source40WindCaster[p]=null
    set Source40WindAt[p]=0.
    set Source40SmokeAt[p]=0.
    set Source40SmokeCaster[p]=null
    set Source40AgiUntil[p]=0.
    set Source40AgiCaster[p]=null
    if Hero[p]!=null then
        call UnitRemoveAbility(Hero[p],'R40a')
    endif
    if Source40Helpers[p]!=null then
        loop
            set u=FirstOfGroup(Source40Helpers[p])
            exitwhen u==null
            call GroupRemoveUnit(Source40Helpers[p],u)
            call FlushChildHashtable(Source40Birth,GetHandleId(u))
            call RemoveUnit(u)
        endloop
    endif
    set u=null
endfunction
function Source40Adopt takes integer p, unit u returns nothing
    local integer raw=GetUnitTypeId(u)
    if HeroRole[p]==10 and (raw=='rs01' or raw=='rs02' or raw=='rs03') then
        if Companion[p*3+2]!=null and Companion[p*3+2]!=u then
            call RemoveUnit(Companion[p*3+2])
        endif
        set Companion[p*3+2]=u
    endif
endfunction
function Source40Order takes nothing returns nothing
    local integer p=0
    local unit u=GetTriggerUnit()
    local unit target=GetOrderTargetUnit()
    local real x=GetOrderPointX()
    local real y=GetOrderPointY()
    loop
        exitwhen p>=12
        if u==Source40Ball[p] and u!=null then
            if target!=null then
                set x=GetUnitX(target)
                set y=GetUnitY(target)
            endif
            set Source40BallAngle[p]=Atan2(y-GetUnitY(u),x-GetUnitX(u))
            set Source40BallSteered[p]=true
            exitwhen true
        endif
        set p=p+1
    endloop
    set u=null
    set target=null
endfunction
function Source40CutTree takes nothing returns nothing
    local destructable tree=GetEnumDestructable()
    local real dx=GetDestructableX(tree)-Source40CutX
    local real dy=GetDestructableY(tree)-Source40CutY
    if dx*dx+dy*dy<=250000. and TreeJumpTree(tree) then
        call KillDestructable(tree)
    endif
    set tree=null
endfunction
function Source40BallPulse takes integer p returns nothing
    local unit ball=Source40Ball[p]
    local unit target=null
    local unit best=null
    local real nearest=1500.*1500.
    local real dx=0.
    local real dy=0.
    local real distance=0.
    local real x=GetUnitX(ball)
    local real y=GetUnitY(ball)
    local real nx=0.
    local real ny=0.
    local real damage=24.
    call GroupEnumUnitsInRange(Source40Scratch,x,y,1500.,null)
    loop
        set target=FirstOfGroup(Source40Scratch)
        exitwhen target==null
        call GroupRemoveUnit(Source40Scratch,target)
        if Source40Enemy(target,p) and IsUnitVisible(target,Player(p)) and (not IsUnitInvisible(target,Player(p)) or IsUnitDetected(target,Player(p))) then
            set dx=GetUnitX(target)-x
            set dy=GetUnitY(target)-y
            set distance=dx*dx+dy*dy
            if distance<nearest then
                set best=target
                set nearest=distance
            endif
            if distance<=550.*550. then
                if Source40BallSteered[p] then
                    set damage=21.
                endif
                call UnitDamageTarget(Hero[p],target,damage,false,false,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL,WEAPON_TYPE_WHOKNOWS)
                if distance<500.*500. and FoundationAlive(target) then
                    set distance=SquareRoot(distance)
                    if distance>1. then
                        set nx=GetUnitX(target)+dx/distance*30.
                        set ny=GetUnitY(target)+dy/distance*30.
                        if not IsTerrainPathable(nx,ny,PATHING_TYPE_WALKABILITY) and GetTerrainCliffLevel(nx,ny)==GetTerrainCliffLevel(GetUnitX(target),GetUnitY(target)) then
                            call SetUnitPosition(target,nx,ny)
                        endif
                    endif
                endif
            endif
        endif
    endloop
    if GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER and best!=null then
        set Source40BallAngle[p]=Atan2(GetUnitY(best)-y,GetUnitX(best)-x)
        set Source40BallSteered[p]=true
    endif
    set nx=x+30.*Cos(Source40BallAngle[p])
    set ny=y+30.*Sin(Source40BallAngle[p])
    if TreeJumpInside(p,nx,ny) then
        call SetUnitX(ball,nx)
        call SetUnitY(ball,ny)
    endif
    call SetUnitFacing(ball,GetUnitFacing(ball)+67.5)
    set Source40CutX=GetUnitX(ball)
    set Source40CutY=GetUnitY(ball)
    call SetRect(Source40TreeRect,Source40CutX-500.,Source40CutY-500.,Source40CutX+500.,Source40CutY+500.)
    call EnumDestructablesInRect(Source40TreeRect,null,function Source40CutTree)
    set target=null
    set best=null
    set ball=null
endfunction
function Source40Apply takes integer p, integer index, integer rank returns boolean
    local integer n=0
    local integer k=0
    local integer slot=0
    local unit target=null
    local unit helper=null
    local unit pet=null
    local real x=GetSpellTargetX()
    local real y=GetSpellTargetY()
    local real angle=0.
    local real distance=0.
    call Source40SyncTime()
    if index==29 then
        call Source40BallEnd(p)
        call SetUnitAnimationByIndex(Hero[p],SkillAnimation[29])
        set Source40BallCaster[p]=Hero[p]
        set Source40BallAt[p]=Source40Now+.75
        set Source40BallX[p]=x
        set Source40BallY[p]=y
        set Source40BallAngle[p]=Atan2(y-GetUnitY(Hero[p]),x-GetUnitX(Hero[p]))
        set Source40BallSteered[p]=false
        return true
    elseif index==36 then
        set Source40SmokeCaster[p]=Hero[p]
        set Source40SmokeAt[p]=Source40Now+.9
        set Source40SmokeX[p]=x
        set Source40SmokeY[p]=y
        set Source40SmokeRank[p]=rank
        return true
    elseif index==37 then
        call UnitAddAbility(Hero[p],'R40a')
        call SetUnitAbilityLevel(Hero[p],'R40a',rank)
        call UnitMakeAbilityPermanent(Hero[p],true,'R40a')
        set Source40AgiCaster[p]=Hero[p]
        set Source40AgiUntil[p]=Source40Now+25.
        if rank>1 then
            set Source40AgiUntil[p]=Source40Now+50.
        endif
        return true
    elseif index==42 then
        if Source40Helpers[p]==null then
            set Source40Helpers[p]=CreateGroup()
        endif
        call GroupEnumUnitsInRange(Source40Scratch,x,y,125.+75.*rank,null)
        loop
            set target=FirstOfGroup(Source40Scratch)
            exitwhen target==null
            call GroupRemoveUnit(Source40Scratch,target)
            if Source40Enemy(target,p) and GetUnitState(target,UNIT_STATE_MANA)>0. then
                set n=0
                loop
                    exitwhen n>=rank
                    set helper=CreateUnit(Player(p),'r40d',GetUnitX(Hero[p]),GetUnitY(Hero[p]),0.)
                    call IssueTargetOrder(helper,"drain",target)
                    call UnitApplyTimedLife(helper,'BTLF',4.)
                    call GroupAddUnit(Source40Helpers[p],helper)
                    call SaveReal(Source40Birth,GetHandleId(helper),0,Source40Now)
                    set n=n+1
                endloop
            endif
        endloop
    elseif index==53 then
        // Native AUin creates, lands, damages and raises EVENT_PLAYER_UNIT_SUMMON.
    elseif index==54 then
        call SetUnitAnimationByIndex(Hero[p],SkillAnimation[54])
        if Source40Helpers[p]==null then
            set Source40Helpers[p]=CreateGroup()
        endif
        loop
            exitwhen k>=3
            set pet=Companion[p*3+k]
            if FoundationAlive(pet) then
                set n=0
                loop
                    exitwhen n>=6
                    set angle=GetRandomReal(0.,2.*bj_PI)
                    set distance=GetRandomReal(200.,600.)
                    set helper=CreateUnit(Player(p),'r40b',GetUnitX(pet),GetUnitY(pet),angle*bj_RADTODEG)
                    call IssuePointOrder(helper,"move",GetUnitX(pet)+distance*Cos(angle),GetUnitY(pet)+distance*Sin(angle))
                    call UnitApplyTimedLife(helper,'BTLF',5.)
                    call GroupAddUnit(Source40Helpers[p],helper)
                    call SaveReal(Source40Birth,GetHandleId(helper),0,Source40Now)
                    set n=n+1
                endloop
            endif
            set k=k+1
        endloop
    elseif index==59 then
        // Native shockwave remains authoritative; original3.5 helper wind follows.
        set Source40WindCaster[p]=Hero[p]
        set Source40WindAt[p]=Source40Now+.5
        set Source40WindX[p]=x
        set Source40WindY[p]=y
        set Source40WindAngle[p]=Atan2(y-GetUnitY(Hero[p]),x-GetUnitX(Hero[p]))
    else
        return false
    endif
    set target=null
    set helper=null
    set pet=null
    return true
endfunction
function Source40PlayerTick takes nothing returns nothing
    local integer p=Source40Cursor
    local unit helper=null
    local integer n=0
    local integer artSlot=0
    local real age=0.
    local real angle=0.
    call Source40SyncTime()
    if Source40BallCaster[p]!=null then
        if Source40BallCaster[p]!=Hero[p] or not FoundationAlive(Hero[p]) or IsUnitHidden(Hero[p]) or IsUnitPaused(Hero[p]) then
            call Source40BallEnd(p)
        elseif Source40Ball[p]==null and Source40Now>=Source40BallAt[p] then
            set Source40Ball[p]=CreateUnit(Player(p),'r40s',Source40BallX[p],Source40BallY[p],0.)
            set Source40BallUntil[p]=Source40Now+7.5
            set Source40BallPoseAt[p]=Source40Now
            call SetUnitTimeScale(Hero[p],4.)
            call SetUnitPathing(Source40Ball[p],false)
            call SetUnitFlyHeight(Source40Ball[p],200.,0.)
            if GetPlayerController(Player(p))!=MAP_CONTROL_COMPUTER then
                call SelectUnitForPlayerSingle(Source40Ball[p],Player(p))
                call DisplayTimedTextToPlayer(Player(p),0.,0.,8.,"Железный шар: направляй его правой кнопкой мыши. Остановка Тен-Тен прерывает технику.")
            endif
        elseif Source40Ball[p]!=null then
            if not FoundationAlive(Source40Ball[p]) or Source40Now>=Source40BallUntil[p] then
                call Source40BallEnd(p)
            else
                if Source40Now>=Source40BallPoseAt[p] then
                    // Source attack-alternate resolves to Attack in this imported model.
                    call SetUnitAnimationByIndex(Hero[p],3)
                    set Source40BallPoseAt[p]=Source40Now+.25
                endif
                set Source40BallBudget[p]=Source40BallBudget[p]+.05
                loop
                    exitwhen Source40BallBudget[p]<.03
                    set Source40BallBudget[p]=Source40BallBudget[p]-.03
                    call Source40BallPulse(p)
                endloop
            endif
        endif
    endif
    if Source40AgiUntil[p]>0. then
        if Source40AgiCaster[p]!=Hero[p] or not FoundationAlive(Hero[p]) or Source40Now>=Source40AgiUntil[p] then
            if Source40AgiCaster[p]!=null then
                call UnitRemoveAbility(Source40AgiCaster[p],'R40a')
            endif
            set Source40AgiCaster[p]=null
            set Source40AgiUntil[p]=0.
        endif
    endif
    if Source40SmokeAt[p]>0. and Source40Now>=Source40SmokeAt[p] then
        if Source40SmokeCaster[p]==Hero[p] and FoundationAlive(Hero[p]) then
            if Source40Helpers[p]==null then
                set Source40Helpers[p]=CreateGroup()
            endif
            set helper=CreateUnit(Player(p),'r40c',Source40SmokeX[p],Source40SmokeY[p],0.)
            call ExecuteFunc("VisualSource40Smoke")
            call SetUnitAbilityLevel(helper,'R40c',Source40SmokeRank[p])
            call IssueImmediateOrder(helper,"stomp")
            call UnitApplyTimedLife(helper,'BTLF',10.)
            call GroupAddUnit(Source40Helpers[p],helper)
            call SaveReal(Source40Birth,GetHandleId(helper),0,Source40Now)
        endif
        set Source40SmokeCaster[p]=null
        set Source40SmokeAt[p]=0.
    endif
    if Source40WindAt[p]>0. and Source40Now>=Source40WindAt[p] then
        if Source40WindCaster[p]==Hero[p] and FoundationAlive(Hero[p]) then
            if Source40Helpers[p]==null then
                set Source40Helpers[p]=CreateGroup()
            endif
            set n=0
            loop
                exitwhen n>=2
                set angle=Source40WindAngle[p]
                set helper=CreateUnit(Player(p),'r40w',Source40WindX[p],Source40WindY[p],angle*bj_RADTODEG)
                if n==0 then
                    call UnitRemoveAbility(helper,'R40t')
                else
                    call UnitRemoveAbility(helper,'R40w')
                endif
                call IssuePointOrder(helper,"stampede",Source40WindX[p]+150.*Cos(angle),Source40WindY[p]+150.*Sin(angle))
                call UnitApplyTimedLife(helper,'BTLF',1.5+1.5*n)
                call GroupAddUnit(Source40Helpers[p],helper)
                call SaveReal(Source40Birth,GetHandleId(helper),0,Source40Now)
                set n=n+1
            endloop
        endif
        set Source40WindCaster[p]=null
        set Source40WindAt[p]=0.
    endif
    // Groups persist, but every helper is removed after its actual cast/death/expiry.
    if Source40Helpers[p]!=null then
        call GroupAddGroup(Source40Helpers[p],Source40Cleanup)
        loop
            set helper=FirstOfGroup(Source40Cleanup)
            exitwhen helper==null
            call GroupRemoveUnit(Source40Cleanup,helper)
            set age=Source40Now-LoadReal(Source40Birth,GetHandleId(helper),0)
            if not FoundationAlive(helper) or age>10.1 or (GetUnitTypeId(helper)!='r40c' and age>5.1) or (GetUnitTypeId(helper)=='r40d' and age>4.1) or (GetUnitTypeId(helper)=='r40w' and age>3.1) then
                call GroupRemoveUnit(Source40Helpers[p],helper)
                if GetUnitTypeId(helper)=='r40b' and not FoundationAlive(helper) then
                    call DestroyEffect(AddSpecialEffect("Note.MDX",GetUnitX(helper),GetUnitY(helper)))
                    set artSlot=SkillFlashCursor
                    call SkillsHoldFlash(AddSpecialEffect("Doodads\\Cinematic\\TownBurningFireEmitter\\TownBurningFireEmitter.mdl",GetUnitX(helper),GetUnitY(helper)))
                    set SkillFlashUntil[artSlot]=TimeNow+.5
                endif
                call FlushChildHashtable(Source40Birth,GetHandleId(helper))
                call RemoveUnit(helper)
            elseif GetUnitTypeId(helper)=='r40b' then
                if age<=.35 then
                    call SetUnitFlyHeight(helper,RMinBJ(350.,age*1600.),0.)
                else
                    call SetUnitFlyHeight(helper,RMaxBJ(0.,350.-(age-.35)*1000.),0.)
                endif
            endif
        endloop
    endif
    set helper=null
endfunction
function Source40Tick takes nothing returns nothing
    local integer p=0
    set Source40Now=Source40Now+.05
    call Source40SyncTime()
    loop
        exitwhen p>=12
        set Source40Cursor=p
        call ExecuteFunc("Source40PlayerTick")
        set p=p+1
    endloop
endfunction
function Source40Init takes nothing returns nothing
    local trigger orders=null
    local integer p=0
    if Source40Scratch!=null then
        set orders=null
        return
    endif
    set Source40Now=TimeNow
    set orders=CreateTrigger()
    set Source40Scratch=CreateGroup()
    set Source40Cleanup=CreateGroup()
    set Source40Birth=InitHashtable()
    set Source40TreeRect=Rect(0.,0.,1.,1.)
    loop
        exitwhen p>=12
        call TriggerRegisterPlayerUnitEvent(orders,Player(p),EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER,null)
        call TriggerRegisterPlayerUnitEvent(orders,Player(p),EVENT_PLAYER_UNIT_ISSUED_TARGET_ORDER,null)
        set p=p+1
    endloop
    call TriggerAddAction(orders,function Source40Order)
    set orders=null
endfunction
