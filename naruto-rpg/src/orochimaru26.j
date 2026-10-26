// Dedicated existing-heartbeat boss controller; independent of the crowded24-NPC scan.
function InvasionOroWatch takes nothing returns nothing
    local unit u=CampaignVillageOro
    local unit target=null
    local unit candidate=null
    local integer slot=CampaignOroSlot
    local integer route=3
    local real best=1100.*1100.
    local real dx=0.
    local real dy=0.
    if CampaignFinished or CampaignTransition or CampaignStage!=12 then
        set u=null
        return
    endif
    if not CampaignOroStarted then
        if CampaignOroAt<=0. or (not CampaignEventDue[3] and TimeNow<CampaignOroAt) then
            set u=null
            return
        endif
        if not FoundationAlive(u) then
            set slot=CampaignAdd(13,PLAYER_NEUTRAL_PASSIVE,CampaignSupportX[4],CampaignSupportY[4])
            if slot<0 then
                set u=null
                return
            endif
            set CampaignOroSlot=slot
            set CampaignVillageOro=CampaignActor[slot]
            set u=CampaignVillageOro
        endif
        call SetUnitOwner(u,Player(PLAYER_NEUTRAL_PASSIVE),true)
        call PauseUnit(u,false)
        call UnitRemoveAbility(u,'Avul')
        call ShowUnit(u,true)
        call SetUnitPathing(u,true)
        call SetUnitVertexColor(u,255,255,255,255)
        if slot>=0 and CampaignActor[slot]==u then
            set CampaignActorRoute[slot]=3
            set CampaignMoveAt[slot]=TimeNow+2.
            set CampaignWalkAt[slot]=TimeNow+8.
            set CampaignWalkX[slot]=GetUnitX(u)
            set CampaignWalkY[slot]=GetUnitY(u)
        endif
        call IssuePointOrder(u,"attack",CampaignRouteX[3],CampaignRouteY[3])
        set CampaignOroStarted=true
        set CampaignOroAt=0.
        set CampaignOroWatchAt=TimeNow+1.
        call CampaignEventClose(3)
        call ExamBroadcast("Орочимару: Теперь я лично разберусь с Хокагэ!")
        set u=null
        return
    endif
    if not FoundationAlive(u) or TimeNow<CampaignOroWatchAt then
        set u=null
        return
    endif
    set CampaignOroWatchAt=TimeNow+1.
    if NPCBusy(u) then
        set u=null
        return
    endif
    if IsUnitPaused(u) or IsUnitHidden(u) then
        if CampaignOroStaleAt==0. then
            set CampaignOroStaleAt=TimeNow+15.
        elseif TimeNow>=CampaignOroStaleAt then
            call PauseUnit(u,false)
            call ShowUnit(u,true)
            call SetUnitPathing(u,true)
            call SetUnitTimeScale(u,1.)
            set CampaignOroStaleAt=0.
        endif
        set u=null
        return
    endif
    set CampaignOroStaleAt=0.
    call GroupEnumUnitsInRange(CampaignScratch,GetUnitX(u),GetUnitY(u),1100.,null)
    loop
        set candidate=FirstOfGroup(CampaignScratch)
        exitwhen candidate==null
        call GroupRemoveUnit(CampaignScratch,candidate)
        if FoundationAlive(candidate) and not IsUnitHidden(candidate) and GetUnitAbilityLevel(candidate,'Avul')==0 and IsUnitEnemy(candidate,GetOwningPlayer(u)) and SkillsCanSee(candidate,GetOwningPlayer(u)) then
            set dx=GetUnitX(candidate)-GetUnitX(u)
            set dy=GetUnitY(candidate)-GetUnitY(u)
            if dx*dx+dy*dy<best then
                set best=dx*dx+dy*dy
                set target=candidate
            endif
        endif
    endloop
    if target!=null then
        if NPCUseInventory(u,13,target) or NPCTry(u,13,target) then
            set CampaignOroTarget=null
        elseif CampaignOroTarget!=target or GetUnitCurrentOrder(u)==0 then
            call IssueTargetOrder(u,"attack",target)
            set CampaignOroTarget=target
        endif
    elseif slot>=0 and CampaignActor[slot]==u then
        set route=CampaignActorRoute[slot]
        if route<0 then
            set route=3
        endif
        if ExamNear(u,CampaignRouteX[route],CampaignRouteY[route],220.) then
            if route==3 then
                set route=8
            else
                set route=11
            endif
            set CampaignActorRoute[slot]=route
        endif
        if not CampaignWaveRecover(slot) and (CampaignOroTarget!=null or GetUnitCurrentOrder(u)==0 or TimeNow>=CampaignMoveAt[slot]) then
            call IssuePointOrder(u,"attack",CampaignRouteX[route],CampaignRouteY[route])
            set CampaignMoveAt[slot]=TimeNow+4.
        endif
        set CampaignOroTarget=null
    endif
    set candidate=null
    set target=null
    set u=null
endfunction
