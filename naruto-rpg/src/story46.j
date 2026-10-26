// Bounded story timing/duel preparation on the existing Foundation heartbeat.
function Story46Clear takes nothing returns nothing
    set Story46AttackAt=0.
    set Story46Boss[0]=null
    set Story46Boss[1]=null
endfunction
function Story46MentorsStart takes nothing returns nothing
    local integer j=0
    if CampaignStage!=13 then
        return
    endif
    call Story46Clear()
    set Story46AttackAt=TimeNow+10.
    loop
        exitwhen j>=2
        set Story46Boss[j]=CampaignActor[j+2]
        if FoundationAlive(Story46Boss[j]) then
            call PauseUnit(Story46Boss[j],true)
        endif
        set j=j+1
    endloop
    call ExamBroadcast("Гай: Итачи и Кисамэ начнут атаку через10секунд. Соберитесь возле наставников!")
endfunction
function Story46Tick takes nothing returns nothing
    local integer j=0
    local unit boss=null
    local unit target=null
    if Story46AttackAt<=0. then
        return
    endif
    if CampaignStage!=13 or CampaignTransition or CampaignFinished then
        call Story46Clear()
        return
    endif
    if TimeNow<Story46AttackAt then
        return
    endif
    set Story46AttackAt=0.
    loop
        exitwhen j>=2
        set boss=Story46Boss[j]
        set target=CampaignActor[j]
        if FoundationAlive(boss) then
            call PauseUnit(boss,false)
            if FoundationAlive(target) and IsUnitEnemy(target,GetOwningPlayer(boss)) then
                call IssueTargetOrder(boss,"attack",target)
            endif
        endif
        set Story46Boss[j]=null
        set j=j+1
    endloop
    set boss=null
    set target=null
endfunction
function Story46PrepareDuel takes nothing returns nothing
    local integer p=0
    local real x=0.
    local real y=0.
    if CampaignStage!=16 then
        return
    endif
    if FoundationAlive(CampaignNaruto) then
        if GetHeroLevel(CampaignNaruto)<60 then
            call SetHeroLevel(CampaignNaruto,60,false)
        endif
        call SetWidgetLife(CampaignNaruto,GetUnitState(CampaignNaruto,UNIT_STATE_MAX_LIFE))
        call SetUnitState(CampaignNaruto,UNIT_STATE_MANA,GetUnitState(CampaignNaruto,UNIT_STATE_MAX_MANA))
    endif
    // Move spectators and their real pets out of the valley. Never hide/delete a hero.
    loop
        exitwhen p>=12
        if Hero[p]!=null and p!=CampaignNarutoPlayer and p!=CampaignSasukePlayer and not CampaignPermanentDead[p] then
            set x=CampaignX[10]+I2R(ModuloInteger(p,4)-1)*96.
            set y=CampaignY[10]+I2R((p-ModuloInteger(p,4))/4-1)*96.
            call PauseUnit(Hero[p],true)
            call UnitAddAbility(Hero[p],'Avul')
            call SetUnitPosition(Hero[p],x,y)
            call RosterSyncPets(p)
        endif
        set p=p+1
    endloop
endfunction
