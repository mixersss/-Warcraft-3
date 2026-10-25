// One source Kabuto, existing forest heartbeat; no extra timers or respawning boss.
function ExamKabutoDropScrolls takes nothing returns nothing
    local integer k=0
    local item it=null
    loop
        exitwhen k>=6
        set it=UnitItemInSlot(ExamKabuto,k)
        if GetItemTypeId(it)=='Eshe' or GetItemTypeId(it)=='Esea' then
            call UnitRemoveItem(ExamKabuto,it)
            call SetItemPosition(it,GetUnitX(ExamKabuto),GetUnitY(ExamKabuto))
        endif
        set k=k+1
    endloop
    set it=null
endfunction
function ExamKabutoKill takes nothing returns nothing
    local unit victim=GetTriggerUnit()
    local integer p=GetPlayerId(GetOwningPlayer(victim))
    local integer k=0
    local item it=null
    if ExamPhase==3 and CampaignStage==0 and ExamKabuto!=null and GetKillingUnit()==ExamKabuto and p<12 and victim==Hero[p] and StoryStage[StoryTeam(p)]==7 then
        loop
            exitwhen k>=6
            set it=UnitItemInSlot(victim,k)
            if GetItemTypeId(it)=='Eshe' or GetItemTypeId(it)=='Esea' then
                // Transfer the actual quest item. A full thief inventory leaves it
                // on the ground at Kabuto, never deletes or duplicates a scroll.
                call UnitRemoveItem(victim,it)
                call SetItemPosition(it,GetUnitX(ExamKabuto),GetUnitY(ExamKabuto))
                call UnitAddItem(ExamKabuto,it)
            endif
            set k=k+1
        endloop
        set CampaignPermanentDead[p]=false
        set StoryRevive[p]=TimeNow+20.
        call DisplayTimedTextToPlayer(Player(p),0.,0.,12.,"Кабуто забрал ваши свитки. Возвращение в лагерь через 20 секунд; экзамен продолжается.")
    endif
    set it=null
    set victim=null
endfunction
function ExamKabutoSetup takes nothing returns nothing
    if ExamKabutoDeathHook==null then
        set ExamKabutoDeathHook=CreateTrigger()
        call TriggerRegisterAnyUnitEventBJ(ExamKabutoDeathHook,EVENT_PLAYER_UNIT_DEATH)
        call TriggerAddAction(ExamKabutoDeathHook,function ExamKabutoKill)
    endif
endfunction
function ExamKabutoClear takes nothing returns nothing
    if ExamKabuto!=null then
        call ExamKabutoDropScrolls()
        if NPCCooldowns!=null then
            call FlushChildHashtable(NPCCooldowns,GetHandleId(ExamKabuto))
        endif
        if NPCHiddenAbilities!=null then
            call FlushChildHashtable(NPCHiddenAbilities,GetHandleId(ExamKabuto))
        endif
        call RemoveUnit(ExamKabuto)
        set ExamKabuto=null
    endif
    set ExamKabutoTarget=null
    set ExamKabutoAt=0.
endfunction
function ExamKabutoTick takes nothing returns nothing
    local integer p=0
    local integer point=0
    local unit target=null
    local real best=999999999.
    local real dx=0.
    local real dy=0.
    local real distance=0.
    if ExamPhase!=3 or CampaignStage!=0 then
        call ExamKabutoClear()
        return
    endif
    if ExamKabutoAt>0. and TimeNow>=ExamKabutoAt then
        set ExamKabutoAt=0.
        set ExamKabuto=ExamRespawn('c00B')
        set ExamKabutoLootDropped=false
        call NPCInitialize(ExamKabuto,11)
        // Source forest set, rather than the late-game Kabuto's sleeping technique.
        call UnitRemoveAbility(ExamKabuto,'S02B')
        call UnitAddAbility(ExamKabuto,'A018')
        call SetUnitAbilityLevel(ExamKabuto,'A018',3)
        call UnitAddAbility(ExamKabuto,'ACcr')
        call UnitRemoveAbility(ExamKabuto,'S023')
        call SetUnitCreepGuard(ExamKabuto,false)
        call RemoveGuardPosition(ExamKabuto)
        set ExamKabutoWalkAt=TimeNow
        set ExamKabutoX=GetUnitX(ExamKabuto)
        set ExamKabutoY=GetUnitY(ExamKabuto)
        call ExamBroadcast("Анко: В Лесу смерти появился Кабуто! Он охотится на участников всех отрядов. Будьте осторожны.")
    endif
    if ExamKabuto!=null and not FoundationAlive(ExamKabuto) and not ExamKabutoLootDropped then
        call ExamKabutoDropScrolls()
        set ExamKabutoLootDropped=true
    endif
    if not FoundationAlive(ExamKabuto) or IsUnitPaused(ExamKabuto) or NPCBusy(ExamKabuto) then
        return
    endif
    loop
        exitwhen p>=12
        if StoryStage[StoryTeam(p)]==7 and FoundationAlive(Hero[p]) and not IsUnitHidden(Hero[p]) and not IsUnitPaused(Hero[p]) and SkillsCanSee(Hero[p],GetOwningPlayer(ExamKabuto)) and IsUnitEnemy(Hero[p],GetOwningPlayer(ExamKabuto)) then
            set dx=GetUnitX(Hero[p])-GetUnitX(ExamKabuto)
            set dy=GetUnitY(Hero[p])-GetUnitY(ExamKabuto)
            set distance=dx*dx+dy*dy
            if distance<best then
                set best=distance
                set target=Hero[p]
            endif
        endif
        set p=p+1
    endloop
    if target!=null then
        if GetWidgetLife(ExamKabuto)<=3000. and GetUnitState(ExamKabuto,UNIT_STATE_MANA)>=75. and TimeNow>=ExamKabutoHealAt then
            if IssueTargetOrder(ExamKabuto,"drain",ExamKabuto) then
                set ExamKabutoHealAt=TimeNow+20.
                if NPCCooldowns==null then
                    set NPCCooldowns=InitHashtable()
                endif
                call SaveReal(NPCCooldowns,GetHandleId(ExamKabuto),0,TimeNow+10.)
                call SaveInteger(NPCCooldowns,GetHandleId(ExamKabuto),-3,'A02D')
                set target=null
                return
            endif
        endif
        // Source cripple, drain and explosive volley; real native cooldowns/mana.
        if best<=600.*600. and TimeNow>=ExamKabutoCrippleAt and GetUnitState(ExamKabuto,UNIT_STATE_MANA)>=175. then
            if IssueTargetOrder(ExamKabuto,"cripple",target) then
                set ExamKabutoCrippleAt=TimeNow+10.
                if NPCCooldowns==null then
                    set NPCCooldowns=InitHashtable()
                endif
                call SaveReal(NPCCooldowns,GetHandleId(ExamKabuto),0,TimeNow+1.)
                set target=null
                return
            endif
        endif
        if best<=900.*900. and NPCTry(ExamKabuto,11,target) then
            set target=null
            return
        endif
        if target!=ExamKabutoTarget or GetUnitCurrentOrder(ExamKabuto)==0 then
            call IssueTargetOrder(ExamKabuto,"attack",target)
        endif
        set ExamKabutoTarget=target
        if TimeNow>=ExamKabutoWalkAt then
            set dx=GetUnitX(ExamKabuto)-ExamKabutoX
            set dy=GetUnitY(ExamKabuto)-ExamKabutoY
            if best>350.*350. and dx*dx+dy*dy<32.*32. then
                call IssuePointOrder(ExamKabuto,"attack",GetUnitX(target),GetUnitY(target))
            endif
            set ExamKabutoX=GetUnitX(ExamKabuto)
            set ExamKabutoY=GetUnitY(ExamKabuto)
            set ExamKabutoWalkAt=TimeNow+6.
        endif
    elseif TimeNow>=ExamKabutoWalkAt then
        set point=GetRandomInt(0,84)
        call IssuePointOrder(ExamKabuto,"attack",ExamEnemyX[point],ExamEnemyY[point])
        set ExamKabutoWalkAt=TimeNow+6.
        set ExamKabutoTarget=null
    endif
    set target=null
endfunction
