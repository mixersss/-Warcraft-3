// Independent continuation. Source functions, constants and differences: campaign-source.json.
function CampaignAlliances takes integer mode returns nothing
    local integer p=0
    local integer q=0
    local boolean allied=false
    loop
        exitwhen p>=12
        set q=0
        loop
            exitwhen q>=12
            set allied=mode==1 or StoryTeam(p)==StoryTeam(q)
            if mode==2 then
                set allied=(HeroRole[p]<9 and HeroRole[q]<9) or (HeroRole[p]>=9 and HeroRole[q]>=9)
            endif
            call SetPlayerAllianceStateAllyBJ(Player(p),Player(q),allied)
            call SetPlayerAllianceStateVisionBJ(Player(p),Player(q),allied and CampaignStage!=9 and CampaignStage!=11)
            set q=q+1
        endloop
        if mode==2 then
            call SetPlayerAllianceStateAllyBJ(Player(PLAYER_NEUTRAL_PASSIVE),Player(p),HeroRole[p]>=9)
            call SetPlayerAllianceStateAllyBJ(Player(p),Player(PLAYER_NEUTRAL_PASSIVE),HeroRole[p]>=9)
        else
            call SetPlayerAllianceStateAllyBJ(Player(PLAYER_NEUTRAL_PASSIVE),Player(p),true)
            call SetPlayerAllianceStateAllyBJ(Player(p),Player(PLAYER_NEUTRAL_PASSIVE),true)
        endif
        call SetPlayerAllianceStateAllyBJ(Player(14),Player(p),true)
        call SetPlayerAllianceStateAllyBJ(Player(p),Player(14),true)
        call SetPlayerAllianceStateVisionBJ(Player(14),Player(p),false)
        call SetPlayerAllianceStateVisionBJ(Player(p),Player(14),false)
        set p=p+1
    endloop
endfunction
function CampaignBindRoles takes nothing returns nothing
    local integer p=0
    set CampaignSasukePlayer=-1
    set CampaignNarutoPlayer=-1
    set CampaignAttackOwner=9
    set CampaignAttackerOwner[0]=9
    set CampaignAttackerOwner[1]=10
    set CampaignAttackerOwner[2]=11
    loop
        exitwhen p>=12
        if Hero[p]!=null then
            if HeroRole[p]>=9 then
                set CampaignAttackerOwner[HeroRole[p]-9]=p
            endif
            if HeroRole[p]==1 then
                set CampaignSasukePlayer=p
                set CampaignSasuke=Hero[p]
            elseif HeroRole[p]==9 then
                set CampaignAttackOwner=p
            elseif HeroRole[p]==0 then
                set CampaignNarutoPlayer=p
                set CampaignNaruto=Hero[p]
            endif
        endif
        set p=p+1
    endloop
    set p=0
    loop
        exitwhen p>=12
        if Hero[p]!=null and p!=CampaignSasukePlayer then
            set CampaignLeader=p
            exitwhen true
        endif
        set p=p+1
    endloop
    if CampaignNarutoPlayer>=0 then
        set CampaignLeader=CampaignNarutoPlayer
    endif
    if NPCSourceReady then
        call NPCSourceHeroes()
    endif
endfunction
function CampaignRogueAlliance takes nothing returns nothing
    local integer p=0
    if CampaignSasukePlayer<0 then
        return
    endif
    loop
        exitwhen p>=12
        if p!=CampaignSasukePlayer then
            call SetPlayerAllianceStateAllyBJ(Player(p),Player(CampaignSasukePlayer),false)
            call SetPlayerAllianceStateAllyBJ(Player(CampaignSasukePlayer),Player(p),false)
            call SetPlayerAllianceStateVisionBJ(Player(p),Player(CampaignSasukePlayer),false)
            call SetPlayerAllianceStateVisionBJ(Player(CampaignSasukePlayer),Player(p),false)
        endif
        set p=p+1
    endloop
endfunction
function CampaignEventClose takes integer slot returns nothing
    set CampaignEventDue[slot]=false
    if CampaignEventDialog[slot]!=null then
        call TimerDialogDisplay(CampaignEventDialog[slot],false)
        call DestroyTimerDialog(CampaignEventDialog[slot])
        set CampaignEventDialog[slot]=null
    endif
    if CampaignEventClock[slot]!=null then
        call PauseTimer(CampaignEventClock[slot])
        call DestroyTimer(CampaignEventClock[slot])
        set CampaignEventClock[slot]=null
    endif
endfunction
function CampaignEventsClose takes nothing returns nothing
    local integer j=0
    loop
        exitwhen j>=4
        call CampaignEventClose(j)
        set j=j+1
    endloop
endfunction
function CampaignEventWake takes nothing returns nothing
    local integer j=0
    loop
        exitwhen j>=4
        if CampaignEventClock[j]!=null and CampaignEventClock[j]==GetExpiredTimer() then
            set CampaignEventDue[j]=true
        endif
        set j=j+1
    endloop
    call ExecuteFunc("CampaignInvasionEvents")
endfunction
function CampaignEventOpen takes integer slot, string title, real deadline returns nothing
    call CampaignEventClose(slot)
    if deadline<=TimeNow then
        return
    endif
    set CampaignEventClock[slot]=CreateTimer()
    call TimerStart(CampaignEventClock[slot],deadline-TimeNow,false,function CampaignEventWake)
    set CampaignEventDialog[slot]=CreateTimerDialog(CampaignEventClock[slot])
    call TimerDialogSetTitle(CampaignEventDialog[slot],title)
    call TimerDialogDisplay(CampaignEventDialog[slot],true)
endfunction
function CampaignClear takes nothing returns nothing
    local integer j=0
    call CampaignEventsClose()
    if CampaignBountyActive then
        loop
            exitwhen j>=16
            call SetPlayerState(Player(j),PLAYER_STATE_GIVES_BOUNTY,CampaignBountyBefore[j])
            set j=j+1
        endloop
        set j=0
        set CampaignBountyActive=false
    endif
    if NPCSourceReady then
        loop
            exitwhen j>=6
            call NPCMedicStop(j)
            set OrigNPC_IF[j]=null
            set j=j+1
        endloop
        set j=0
    endif
    loop
        exitwhen j>=2048
        if CampaignActor[j]!=null then
            if NPCCooldowns!=null then
                call FlushChildHashtable(NPCCooldowns,GetHandleId(CampaignActor[j]))
                if NPCHiddenAbilities!=null then
                    call FlushChildHashtable(NPCHiddenAbilities,GetHandleId(CampaignActor[j]))
                endif
            endif
            call RemoveUnit(CampaignActor[j])
            set CampaignActor[j]=null
        endif
        if CampaignWatcher[j]!=null then
            call DestroyTrigger(CampaignWatcher[j])
            set CampaignWatcher[j]=null
        endif
        set CampaignActorType[j]=-1
        set CampaignCastAt[j]=0.
        set CampaignMoveAt[j]=0.
        set j=j+1
    endloop
    set CampaignCount=0
    set CampaignThinkCursor=0
endfunction
function CampaignAdopt takes unit u, integer kind returns integer
    local integer j=0
    loop
        exitwhen j>=2048 or CampaignActor[j]==null
        set j=j+1
    endloop
    if j>=2048 then
        return -1
    endif
    set CampaignActor[j]=u
    set CampaignActorType[j]=kind
    set CampaignActorRoute[j]=-1
    if j>=CampaignCount then
        set CampaignCount=j+1
    endif
    call NPCInitialize(u,kind)
    return j
endfunction
function CampaignSakonSplit takes nothing returns nothing
    local integer slot=0
    call OrigNPC_VGI()
    set slot=CampaignAdopt(OrigNPC_KI[1],39)
endfunction
function CampaignSoundGuard takes integer kind returns boolean
    return CampaignStage==12 and kind>=5 and kind<=9
endfunction
function CampaignAdd takes integer kind, integer owner, real x, real y returns integer
    local integer j=0
    loop
        exitwhen j>=2048 or CampaignActor[j]==null
        if not FoundationAlive(CampaignActor[j]) then
            if NPCCooldowns!=null then
                call FlushChildHashtable(NPCCooldowns,GetHandleId(CampaignActor[j]))
                if NPCHiddenAbilities!=null then
                    call FlushChildHashtable(NPCHiddenAbilities,GetHandleId(CampaignActor[j]))
                endif
            endif
            call RemoveUnit(CampaignActor[j])
            set CampaignActor[j]=null
            exitwhen true
        endif
        set j=j+1
    endloop
    if j>=2048 then
        return -1
    endif
    set CampaignActor[j]=CreateUnit(Player(owner),CampaignUnit[kind],x,y,180.)
    call NPCInitialize(CampaignActor[j],kind)
    if CampaignSoundGuard(kind) then
        call SetUnitPosition(CampaignActor[j],CampaignReserveX[kind],CampaignReserveY[kind])
    endif
    set CampaignMoveAt[j]=0.
    set CampaignPostX[j]=GetUnitX(CampaignActor[j])
    set CampaignPostY[j]=GetUnitY(CampaignActor[j])
    set CampaignPostFacing[j]=GetUnitFacing(CampaignActor[j])
    set CampaignWalkX[j]=GetUnitX(CampaignActor[j])
    set CampaignWalkY[j]=GetUnitY(CampaignActor[j])
    set CampaignWalkAt[j]=TimeNow+8.
    set CampaignWalkAttempt[j]=0
    if kind==7 or kind==9 then
        set CampaignWatcher[j]=CreateTrigger()
        if kind==7 then
            call TriggerRegisterUnitLifeEvent(CampaignWatcher[j],CampaignActor[j],LESS_THAN,15000.)
            call TriggerAddAction(CampaignWatcher[j],function CampaignSakonSplit)
        else
            call TriggerRegisterUnitLifeEvent(CampaignWatcher[j],CampaignActor[j],LESS_THAN,25000.)
            call TriggerAddAction(CampaignWatcher[j],function OrigNPC_ZMR)
        endif
    endif
    set CampaignActorType[j]=kind
    set CampaignActorRoute[j]=-1
    set CampaignCastAt[j]=TimeNow+3.
    call SetUnitCreepGuard(CampaignActor[j],false)
    call RemoveGuardPosition(CampaignActor[j])
    if CampaignTransition then
        call PauseUnit(CampaignActor[j],true)
    endif
    if j>=CampaignCount then
        set CampaignCount=j+1
    endif
    return j
endfunction
function CampaignAliveEnemies takes nothing returns integer
    local integer j=0
    local integer count=0
    loop
        exitwhen j>=CampaignCount
        if FoundationAlive(CampaignActor[j]) and IsUnitEnemy(CampaignActor[j],Player(CampaignLeader)) then
            set count=count+1
        endif
        set j=j+1
    endloop
    return count
endfunction
function CampaignClonesSpawn takes nothing returns nothing
    local integer p=0
    local integer n=0
    loop
        exitwhen p>=12
        set n=0
        if HeroRole[p]==4 then
            set n=18
        elseif HeroRole[p]==3 then
            set n=19
        elseif HeroRole[p]==5 then
            set n=20
        elseif HeroRole[p]==7 then
            set n=21
        elseif HeroRole[p]==8 then
            set n=22
        elseif HeroRole[p]==9 then
            set n=23
        elseif HeroRole[p]==10 then
            set n=24
        elseif HeroRole[p]==11 then
            set n=25
        endif
        if Hero[p]!=null and n>0 and not CampaignPermanentDead[p] then
            set CampaignClone[p]=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),CampaignUnit[n+2],CampaignTX[n],CampaignTY[n],180.)
            call SetHeroLevel(CampaignClone[p],60,false)
            call NPCInitialize(CampaignClone[p],n+2)
            set CampaignCloneKind[p]=n+2
            set CampaignClonePending[p]=true
            call PauseUnit(CampaignClone[p],true)
            call SetUnitCreepGuard(CampaignClone[p],false)
            call RemoveGuardPosition(CampaignClone[p])
            call SetUnitPosition(Hero[p],CampaignX[n],CampaignY[n])
            set SpawnX[p]=GetUnitX(Hero[p])
            set SpawnY[p]=GetUnitY(Hero[p])
            call DisplayTimedTextToPlayer(Player(p),0.,0.,20.,"Ловушка создала вашего двойника. Победите его и присоединяйтесь к основной группе! Бои других героев идут одновременно.")
        endif
        set p=p+1
    endloop
endfunction
function CampaignClonesTick takes nothing returns nothing
    local integer p=0
    local unit clone=null
    local real dx=0.
    local real dy=0.
    loop
        exitwhen p>=12
        set clone=CampaignClone[p]
        if CampaignClonePending[p] then
            if not FoundationAlive(Hero[p]) then
                set CampaignPermanentDead[p]=true
                set CampaignClonePending[p]=false
                if clone!=null then
                    call RemoveUnit(clone)
                    set CampaignClone[p]=null
                endif
            elseif not FoundationAlive(clone) then
                set CampaignClonePending[p]=false
                if clone!=null then
                    call RemoveUnit(clone)
                    set CampaignClone[p]=null
                endif
                call SetUnitPosition(Hero[p],CampaignX[CampaignStage],CampaignY[CampaignStage])
                set SpawnX[p]=GetUnitX(Hero[p])
                set SpawnY[p]=GetUnitY(Hero[p])
                call PanCameraToTimedForPlayer(Player(p),SpawnX[p],SpawnY[p],1.)
                call DisplayTimedTextToPlayer(Player(p),0.,0.,12.,"Двойник побеждён! Вы присоединились к основной группе.")
            elseif not IsUnitPaused(clone) and not NPCBusy(clone) and TimeNow>=CampaignCloneCastAt[p] then
                if NPCTry(clone,CampaignCloneKind[p],Hero[p]) then
                    set CampaignCloneCastAt[p]=TimeNow+1.
                else
                    call IssueTargetOrder(clone,"attack",Hero[p])
                    set CampaignCloneCastAt[p]=TimeNow+2.
                endif
            endif
        endif
        set p=p+1
    endloop
    set clone=null
endfunction
function CampaignQueueBuild takes boolean winners returns nothing
    local integer p=0
    local integer n=0
    local integer other=0
    local integer value=0
    set CampaignQueueCount=0
    set CampaignQueueCursor=0
    if winners then
        loop
            exitwhen p>=CampaignWinnerCount
            set CampaignQueue[p]=CampaignWinner[p]
            set p=p+1
        endloop
        set CampaignQueueCount=CampaignWinnerCount
    else
        loop
            exitwhen p>=12
            if Hero[p]!=null and not CampaignPermanentDead[p] then
                set CampaignQueue[CampaignQueueCount]=p
                set CampaignQueueCount=CampaignQueueCount+1
            endif
            set p=p+1
        endloop
    endif
    set n=CampaignQueueCount-1
    loop
        exitwhen n<=0
        set other=GetRandomInt(0,n)
        set value=CampaignQueue[n]
        set CampaignQueue[n]=CampaignQueue[other]
        set CampaignQueue[other]=value
        set n=n-1
    endloop
    set CampaignWinnerCount=0
endfunction
function CampaignStand takes integer p returns nothing
    local integer seat=p
    if Hero[p]!=null then
        call RamenClearUnit(Hero[p])
        call CommonLogClear(p)
        call RosterResetEffects(p)
        if not FoundationAlive(Hero[p]) and not CampaignPermanentDead[p] then
            call ReviveHero(Hero[p],CampaignX[CampaignStage],CampaignY[CampaignStage],false)
        endif
        call UnitAddAbility(Hero[p],'Avul')
        call PauseUnit(Hero[p],true)
        call RosterSyncPets(p)
        call IssueImmediateOrder(Hero[p],"stop")
        if CampaignStage==11 then
            set seat=p+12
        endif
        call SetUnitPosition(Hero[p],ArenaSeatX[seat],ArenaSeatY[seat])
        call SetUnitFacing(Hero[p],Atan2(CampaignTY[CampaignStage]-GetUnitY(Hero[p]),CampaignTX[CampaignStage]-GetUnitX(Hero[p]))*bj_RADTODEG)
        call SetUnitAnimation(Hero[p],"stand")
    endif
endfunction
// The arena is public to every participant/spectator only during tournaments.
function CampaignFountainAuras takes integer stage returns nothing
    local integer j=0
    loop
        exitwhen j>=4
        if VillageFountain[j]!=null then
            if stage==9 or stage==11 then
                call UnitRemoveAbility(VillageFountain[j],'ACnr')
                call UnitRemoveAbility(VillageFountain[j],'Crg2')
                call UnitRemoveAbility(VillageFountain[j],'ANre')
            else
                if j==0 or j==2 then
                    call UnitAddAbility(VillageFountain[j],'Crg2')
                else
                    call UnitAddAbility(VillageFountain[j],'ACnr')
                endif
                call UnitAddAbility(VillageFountain[j],'ANre')
            endif
        endif
        set j=j+1
    endloop
endfunction
function CampaignArenaVisibility takes integer stage returns nothing
    local integer p=0
    call CampaignFountainAuras(stage)
    if stage==9 or stage==11 then
        if not CampaignArenaView then
            set CampaignSavedFog=IsFogEnabled()
            set CampaignSavedMask=IsFogMaskEnabled()
            set CampaignArenaView=true
        endif
        // Reveal terrain without global fog cheats or shared invisible-unit sight.
        call FogEnable(true)
        call FogMaskEnable(true)
        if CampaignArenaFogStage!=stage then
            loop
                exitwhen p>=12
                if CampaignArenaFog[p]!=null then
                    call FogModifierStop(CampaignArenaFog[p])
                    call DestroyFogModifier(CampaignArenaFog[p])
                endif
                set CampaignArenaFog[p]=CreateFogModifierRadius(Player(p),FOG_OF_WAR_VISIBLE,CampaignTX[stage],CampaignTY[stage],2600.,false,false)
                call FogModifierStart(CampaignArenaFog[p])
                set p=p+1
            endloop
            set CampaignArenaFogStage=stage
        endif
    elseif CampaignArenaView then
        loop
            exitwhen p>=12
            call FogModifierStop(CampaignArenaFog[p])
            call DestroyFogModifier(CampaignArenaFog[p])
            set CampaignArenaFog[p]=null
            set p=p+1
        endloop
        call FogEnable(CampaignSavedFog)
        call FogMaskEnable(CampaignSavedMask)
        set CampaignArenaView=false
        set CampaignArenaFogStage=0
    endif
endfunction
function CampaignArenaCamera takes nothing returns nothing
    local integer p=0
    loop
        exitwhen p>=12
        if Hero[p]!=null then
            call ResetToGameCameraForPlayer(Player(p),0.)
            call PanCameraToTimedForPlayer(Player(p),CampaignTX[CampaignStage],CampaignTY[CampaignStage],0.)
        endif
        set p=p+1
    endloop
endfunction
function CampaignResetFighter takes integer p returns nothing
    local integer k=0
    set LogArenaUsed[p]=false
    call UnitResetCooldown(Hero[p])
    loop
        exitwhen k>=5
        set BotReadyAt[p*5+k]=TimeNow
        set k=k+1
    endloop
    set k=0
    loop
        exitwhen k>=3
        set PetCastAt[p*3+k]=TimeNow
        if FoundationAlive(Companion[p*3+k]) then
            call UnitResetCooldown(Companion[p*3+k])
        endif
        set k=k+1
    endloop
    set BotNextCast[p]=TimeNow
    set BotUseItemAt[p]=TimeNow
    set StoryBotOrderAt[p]=TimeNow
    set LogReadyAt[p]=TimeNow
    set JumpReadyAt[p]=TimeNow
    set ComboLeft[p]=0
    set ComboTarget[p]=null
endfunction
function CampaignDuelNext takes nothing returns nothing
    local integer p=0
    call NoteClearAll()
    loop
        exitwhen p>=12
        call CampaignStand(p)
        set p=p+1
    endloop
    if CampaignQueueCursor>=CampaignQueueCount then
        set CampaignDuelA=-1
        set CampaignDuelB=-1
        return
    endif
    set CampaignDuelA=CampaignQueue[CampaignQueueCursor]
    set CampaignQueueCursor=CampaignQueueCursor+1
    if CampaignQueueCursor>=CampaignQueueCount then
        if CampaignStage==9 then
            set CampaignPrelimWinner[CampaignDuelA]=true
        endif
        set CampaignWinner[CampaignWinnerCount]=CampaignDuelA
        set CampaignWinnerCount=CampaignWinnerCount+1
        set CampaignDuelA=-1
        set CampaignDuelB=-1
        return
    endif
    set CampaignDuelB=CampaignQueue[CampaignQueueCursor]
    set CampaignQueueCursor=CampaignQueueCursor+1
    call SetPlayerAllianceStateAllyBJ(Player(CampaignDuelA),Player(CampaignDuelB),false)
    call SetPlayerAllianceStateAllyBJ(Player(CampaignDuelB),Player(CampaignDuelA),false)
    call SetPlayerAllianceStateVisionBJ(Player(CampaignDuelA),Player(CampaignDuelB),false)
    call SetPlayerAllianceStateVisionBJ(Player(CampaignDuelB),Player(CampaignDuelA),false)
    call SetUnitPosition(Hero[CampaignDuelA],CampaignTX[CampaignStage]-220.,CampaignTY[CampaignStage])
    call SetUnitPosition(Hero[CampaignDuelB],CampaignTX[CampaignStage]+220.,CampaignTY[CampaignStage])
    call CampaignResetFighter(CampaignDuelA)
    call CampaignResetFighter(CampaignDuelB)
    call SetWidgetLife(Hero[CampaignDuelA],GetUnitState(Hero[CampaignDuelA],UNIT_STATE_MAX_LIFE))
    call SetWidgetLife(Hero[CampaignDuelB],GetUnitState(Hero[CampaignDuelB],UNIT_STATE_MAX_LIFE))
    call SetUnitState(Hero[CampaignDuelA],UNIT_STATE_MANA,GetUnitState(Hero[CampaignDuelA],UNIT_STATE_MAX_MANA))
    call SetUnitState(Hero[CampaignDuelB],UNIT_STATE_MANA,GetUnitState(Hero[CampaignDuelB],UNIT_STATE_MAX_MANA))
    set p=0
    loop
        exitwhen p>=12
        if Hero[p]!=null then
            call PanCameraToTimedForPlayer(Player(p),CampaignTX[CampaignStage],CampaignTY[CampaignStage],1.)
        endif
        set p=p+1
    endloop
    call CampaignArenaCamera()
    set CampaignDuelAt=TimeNow+5.
    set CampaignDuelLive=false
    call ExamBroadcast("Экзаменатор: Команда "+I2S(StoryTeam(CampaignDuelA)+1)+" — "+HeroName[HeroRole[CampaignDuelA]]+" против "+HeroName[HeroRole[CampaignDuelB]]+"! Начало через 5 секунд. Поражение не удаляет героя из истории.")
endfunction
// No teleporting or collision changes: a stalled marching ninja gets a short
// clear-ground sidestep, then resumes the same source waypoint on the next order.
function CampaignWaveRecover takes integer slot returns boolean
    local unit u=CampaignActor[slot]
    local real dx=GetUnitX(u)-CampaignWalkX[slot]
    local real dy=GetUnitY(u)-CampaignWalkY[slot]
    local real x=0.
    local real y=0.
    local real angle=0.
    local integer k=0
    if TimeNow<CampaignWalkAt[slot] then
        set u=null
        return false
    endif
    set CampaignWalkAt[slot]=TimeNow+8.
    set CampaignWalkX[slot]=GetUnitX(u)
    set CampaignWalkY[slot]=GetUnitY(u)
    if dx*dx+dy*dy>=64.*64. then
        set CampaignWalkAttempt[slot]=0
        set u=null
        return false
    endif
    set CampaignWalkAttempt[slot]=CampaignWalkAttempt[slot]+1
    loop
        exitwhen k>=8
        set angle=I2R(ModuloInteger(slot+CampaignWalkAttempt[slot]+k,8))*45.*bj_DEGTORAD
        set x=GetUnitX(u)+Cos(angle)*(160.+I2R(ModuloInteger(CampaignWalkAttempt[slot],3))*64.)
        set y=GetUnitY(u)+Sin(angle)*(160.+I2R(ModuloInteger(CampaignWalkAttempt[slot],3))*64.)
        if RAbsBJ(x)<16224. and RAbsBJ(y)<16224. and not IsTerrainPathable(x,y,PATHING_TYPE_WALKABILITY) then
            call IssuePointOrder(u,"move",x,y)
            set CampaignMoveAt[slot]=TimeNow+2.
            set u=null
            return true
        endif
        set k=k+1
    endloop
    set u=null
    return false
endfunction
function CampaignInvasionWave takes integer lane returns nothing
    local integer n=0
    local integer slot=0
    local integer owner=CampaignAttackerOwner[CampaignWaveRole[lane]]
    local integer origin=CampaignWaveOrigin[lane]
    local integer destination=CampaignWaveDestination[lane]
    if CampaignStage!=12 or CampaignTransition then
        return
    endif
    loop
        exitwhen n>=3
        set slot=CampaignAdd(CampaignWaveKind[lane],owner,CampaignWaveSpawnX[lane*3+n],CampaignWaveSpawnY[lane*3+n])
        if slot>=0 then
            set CampaignActorRoute[slot]=destination
            call PauseUnit(CampaignActor[slot],false)
            call IssuePointOrder(CampaignActor[slot],"attack",CampaignRouteX[destination],CampaignRouteY[destination])
        endif
        set n=n+1
    endloop
endfunction
function CampaignMoveHeroes takes nothing returns nothing
    local integer p=0
    local integer t=0
    local real x=0.
    local real y=0.
    loop
        exitwhen p>=12
        if Hero[p]!=null and not CampaignPermanentDead[p] and not CampaignClonePending[p] then
            call TreeJumpEnd(p)
            call RosterResetEffects(p)
            call SkillsClearSharingan(p)
            set ComboLeft[p]=0
            set ComboTarget[p]=null
            set ResumeAt[p]=0.
            if not FoundationAlive(Hero[p]) then
                call ReviveHero(Hero[p],CampaignX[CampaignStage],CampaignY[CampaignStage],false)
            endif
            set x=CampaignX[CampaignStage]+I2R(ModuloInteger(p,3)-1)*48.
            set y=CampaignY[CampaignStage]+I2R(StoryTeam(p))*48.
            if CampaignStage==12 then
                if HeroRole[p]>=9 then
                    set x=-2336.
                    set y=-11840.+I2R(HeroRole[p]-10)*32.
                else
                    set x=CampaignDefenderX[HeroRole[p]]
                    set y=CampaignDefenderY[HeroRole[p]]
                endif
            endif
            call SetUnitPosition(Hero[p],x,y)
            set SpawnX[p]=GetUnitX(Hero[p])
            set SpawnY[p]=GetUnitY(Hero[p])
            call SetWidgetLife(Hero[p],GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE))
            call SetUnitState(Hero[p],UNIT_STATE_MANA,GetUnitState(Hero[p],UNIT_STATE_MAX_MANA))
            call UnitAddAbility(Hero[p],'Avul')
            call PauseUnit(Hero[p],true)
            call RosterSyncPets(p)
            call PanCameraToTimedForPlayer(Player(p),CampaignTX[CampaignStage],CampaignTY[CampaignStage],2.)
            set StoryStage[StoryTeam(p)]=CampaignStage
        endif
        set p=p+1
    endloop
    loop
        exitwhen t>=4
        if StoryMembers[t]>0 then
            set StoryStage[t]=CampaignStage
        endif
        set StoryRetreat[t]=false
        set StoryMarch[t]=true
        set t=t+1
    endloop
endfunction
function CampaignOpenSourceGate takes nothing returns nothing
    local destructable gate=GetEnumDestructable()
    if (GetDestructableTypeId(gate)=='LTe1' and RAbsBJ(GetDestructableX(gate)-5248.)<1. and RAbsBJ(GetDestructableY(gate)+3456.)<1.) or (GetDestructableTypeId(gate)=='LTe3' and RAbsBJ(GetDestructableX(gate)+1664.)<1. and RAbsBJ(GetDestructableY(gate)+11904.)<1.) then
        call ModifyGateBJ(1,gate)
    endif
    set gate=null
endfunction
// Original QAV positions and LTX owner. Persistent scenery, not disposable combat NPCs.
function CampaignFountainsOpen takes nothing returns nothing
    if VillageFountain[0]==null then
        set VillageFountain[0]=CreateUnit(Player(14),'rvf0',16128.,-15744.,270.)
    endif
    if VillageFountain[1]==null then
        set VillageFountain[1]=CreateUnit(Player(14),'rvf1',4672.,-12096.,270.)
    endif
    if VillageFountain[2]==null then
        set VillageFountain[2]=CreateUnit(Player(14),'rvf2',-2624.,-11840.,270.)
    endif
    if VillageFountain[3]==null then
        set VillageFountain[3]=CreateUnit(Player(14),'rvf3',5632.,-3008.,270.)
    endif
    call CampaignFountainAuras(CampaignStage)
endfunction
function CampaignVillageLandmarksClose takes nothing returns nothing
    local integer n=0
    loop
        exitwhen n>=96
        if VillageLandmarkFog[n]!=null then
            call FogModifierStop(VillageLandmarkFog[n])
            call DestroyFogModifier(VillageLandmarkFog[n])
            set VillageLandmarkFog[n]=null
        endif
        set n=n+1
    endloop
endfunction
function CampaignVillageLandmarksOpen takes nothing returns nothing
    local integer p=0
    local integer j=0
    local integer slot=0
    local unit landmark=null
    call CampaignVillageLandmarksClose()
    loop
        exitwhen p>=12
        if Hero[p]!=null then
            set j=0
            loop
                exitwhen j>=8
                if j<4 then
                    set landmark=StoryShop[j]
                else
                    set landmark=VillageFountain[j-4]
                endif
                if landmark!=null then
                    set slot=p*8+j
                    set VillageLandmarkFog[slot]=CreateFogModifierRadius(Player(p),FOG_OF_WAR_VISIBLE,GetUnitX(landmark),GetUnitY(landmark),320.,false,false)
                    call FogModifierStart(VillageLandmarkFog[slot])
                endif
                set j=j+1
            endloop
        endif
        set p=p+1
    endloop
    set landmark=null
endfunction
// Only computer-controlled Leaf heroes receive automatic lanes; humans stay free.
function CampaignAssignDefense takes nothing returns nothing
    local integer p=0
    local integer count=0
    local integer top=0
    loop
        exitwhen p>=12
        set CampaignDefenseLane[p]=3
        if Hero[p]!=null and HeroRole[p]<9 and not CampaignPermanentDead[p] and GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER then
            set count=count+1
        endif
        set p=p+1
    endloop
    set top=R2I(I2R(count)*.3+.5)
    set p=0
    loop
        exitwhen p>=12
        if top>0 and Hero[p]!=null and HeroRole[p]<9 and not CampaignPermanentDead[p] and GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER then
            set CampaignDefenseLane[p]=5
            set top=top-1
        endif
        set p=p+1
    endloop
endfunction
function CampaignDefenseAllows takes integer p, unit target returns boolean
    local real dx=GetUnitX(target)-GetUnitX(Hero[p])
    local real dy=GetUnitY(target)-GetUnitY(Hero[p])
    local real leftX=GetUnitX(target)-CampaignRouteX[3]
    local real leftY=GetUnitY(target)-CampaignRouteY[3]
    local real topX=GetUnitX(target)-CampaignRouteX[5]
    local real topY=GetUnitY(target)-CampaignRouteY[5]
    // Nearby self-defense and a breach at the Hokage remain emergencies for both groups.
    if dx*dx+dy*dy<=900.*900. or ExamNear(target,CampaignTX[12],CampaignTY[12],1400.) then
        return true
    endif
    if CampaignDefenseLane[p]==5 then
        return topX*topX+topY*topY<leftX*leftX+leftY*leftY
    endif
    return leftX*leftX+leftY*leftY<=topX*topX+topY*topY
endfunction
function CampaignSpawnStage takes nothing returns nothing
    local integer n=CampaignStage
    local integer j=0
    local integer k=0
    local integer owner=PLAYER_NEUTRAL_AGGRESSIVE
    local integer unused=0
    local item reward=null
    local real x=CampaignTX[n]
    local real y=CampaignTY[n]
    if n>=10 and n<=12 then
        call StoryShopsOpen()
        call CampaignFountainsOpen()
        call CampaignVillageLandmarksOpen()
    endif
    if n>=14 then
        call CampaignRogueAlliance()
        if CampaignSasukePlayer>=0 then
            set CampaignSasuke=Hero[CampaignSasukePlayer]
            if not FoundationAlive(CampaignSasuke) then
                call ReviveHero(CampaignSasuke,x,y,false)
            endif
            call SetUnitPosition(CampaignSasuke,x,y)
            if n==14 or (n>=17 and n<=28) then
                call ShowUnit(CampaignSasuke,false)
                call PauseUnit(CampaignSasuke,true)
                call UnitAddAbility(CampaignSasuke,'Avul')
                call DisplayTimedTextToPlayer(Player(CampaignSasukePlayer),0.,0.,20.,"Саске: сюжетная роль сохраняется за вами. Пока раскрывается печать, ждите. В погоне избегайте преследователей. В убежище можете управлять Кабуто командой -kabuto.")
            else
                call ShowUnit(CampaignSasuke,true)
            endif
        endif
    endif
    if n==9 or n==11 then
        set CampaignBracket=n==11
        set CampaignFinalActive=false
        set j=0
        loop
            exitwhen j>=12
            set CampaignEliminated[j]=n==11 and CampaignPrelimDone and not CampaignPrelimWinner[j]
            if n==9 then
                set CampaignPrelimWinner[j]=false
            endif
            set j=j+1
        endloop
        if n==9 then
            set CampaignPrelimDone=false
        endif
        // Only direct -arena2 testing without prelim results seeds the full roster.
        if n==11 and CampaignPrelimDone then
            set CampaignWinnerCount=0
            set j=0
            loop
                exitwhen j>=12
                if CampaignPrelimWinner[j] and Hero[j]!=null and not CampaignPermanentDead[j] then
                    set CampaignWinner[CampaignWinnerCount]=j
                    set CampaignWinnerCount=CampaignWinnerCount+1
                endif
                set j=j+1
            endloop
            call CampaignQueueBuild(true)
        else
            call CampaignQueueBuild(false)
        endif
        call CampaignDuelNext()
    elseif n==10 then
        call ExamBroadcast("Коноха: Ичираку уже открыт. Магазин у арены: 16192, -16256; фонтан рядом: 16128, -15744. -shop / -fountain показывают ближайшую точку.")
        set CampaignJiraiya=GetRandomInt(0,19)
        set CampaignFound=false
        loop
            exitwhen j>=20
            set unused=CampaignAdd(18,PLAYER_NEUTRAL_AGGRESSIVE,CampaignBarrelX[j],CampaignBarrelY[j])
            set j=j+1
        endloop
        call ExamBroadcast("Наруто: Разбивайте бочки! У нас 150 секунд. -quest отмечает ближайшую; боты помогут искать, если дать -go.")
    elseif n==12 then
        call CampaignAssignDefense()
        set owner=CampaignLeader
        if HeroRole[owner]>=9 then
            set owner=PLAYER_NEUTRAL_AGGRESSIVE
        endif
        set CampaignDefenseOwner=owner
        set unused=CampaignAdd(0,owner,x,y)
        set CampaignDeployCursor=0
        call ExamBroadcast("Коноха: открыты четыре магазина Ичираку и четыре фонтана. Их места отмечены обзором: -shop — ближайший магазин, -fountain — ближайший фонтан.")
        if CampaignChampion>=0 then
            set reward=CreateItem('Nlca',GetUnitX(Hero[CampaignChampion]),GetUnitY(Hero[CampaignChampion]))
            if not UnitAddItem(Hero[CampaignChampion],reward) then
                call SetItemPosition(reward,GetUnitX(Hero[CampaignChampion]),GetUnitY(Hero[CampaignChampion]))
            endif
            set CampaignChampion=-1
            set reward=null
        endif
        call EnumDestructablesInRect(bj_mapInitialPlayableArea,null,function CampaignOpenSourceGate)
        set j=0
        loop
            exitwhen j>=8
            set CampaignWaveAt[j]=TimeNow+CampaignWavePeriod[j]+CampaignWaveDelay[j]
            set j=j+1
        endloop
        set unused=CampaignAdd(30,owner,CampaignSupportX[0],CampaignSupportY[0])
        set unused=CampaignAdd(29,owner,CampaignSupportX[1],CampaignSupportY[1])
        set unused=CampaignAdd(31,owner,CampaignSupportX[2],CampaignSupportY[2])
        set unused=CampaignAdd(35,PLAYER_NEUTRAL_PASSIVE,CampaignSupportX[3],CampaignSupportY[3])
        set unused=CampaignAdd(1,owner,x,y)
        set unused=CampaignAdd(2,owner,x,y)
        set j=0
        loop
            exitwhen j>=6
            set unused=CampaignAdd(32,owner,CampaignMedicX[j],CampaignMedicY[j])
            set OrigNPC_IF[j]=CampaignActor[unused]
            set j=j+1
        endloop
        set unused=CampaignAdd(5,PLAYER_NEUTRAL_PASSIVE,5407.0,-2754.7)
        call SetUnitFacing(CampaignActor[unused],270.0)
        set CampaignPostFacing[unused]=270.0
        set unused=CampaignAdd(6,PLAYER_NEUTRAL_PASSIVE,-2337.9,-12081.0)
        call SetUnitFacing(CampaignActor[unused],0.0)
        set CampaignPostFacing[unused]=0.0
        set unused=CampaignAdd(7,PLAYER_NEUTRAL_PASSIVE,5191.3,-2715.4)
        call SetUnitFacing(CampaignActor[unused],270.0)
        set CampaignPostFacing[unused]=270.0
        set unused=CampaignAdd(8,PLAYER_NEUTRAL_PASSIVE,4963.6,-2733.3)
        call SetUnitFacing(CampaignActor[unused],270.0)
        set CampaignPostFacing[unused]=270.0
        set unused=CampaignAdd(9,PLAYER_NEUTRAL_PASSIVE,-2340.7,-11625.9)
        call SetUnitFacing(CampaignActor[unused],0.0)
        set CampaignPostFacing[unused]=0.0
        set CampaignNextNPC=TimeNow+45.
        set CampaignJiraiyaAt=TimeNow+760.
        set CampaignKabutoAt=TimeNow+400.
        set CampaignSnakeAt=TimeNow+820.
        set CampaignOroAt=TimeNow+1160.
        set unused=CampaignAdd(13,PLAYER_NEUTRAL_PASSIVE,CampaignSupportX[4],CampaignSupportY[4])
        set CampaignVillageOro=CampaignActor[unused]
        call PauseUnit(CampaignVillageOro,true)
    elseif n==13 then
        set unused=CampaignAdd(37,CampaignLeader,x-100.,y)
        set unused=CampaignAdd(38,CampaignLeader,x+100.,y)
        set unused=CampaignAdd(3,PLAYER_NEUTRAL_AGGRESSIVE,x-300.,y+380.)
        set unused=CampaignAdd(4,PLAYER_NEUTRAL_AGGRESSIVE,x+300.,y+380.)
    elseif n==14 then
        loop
            exitwhen j>=5
            set unused=CampaignAdd(CampaignFiveType[j],PLAYER_NEUTRAL_AGGRESSIVE,CampaignFiveX[j],CampaignFiveY[j])
            set j=j+1
        endloop
    elseif n==15 or n==16 or n==29 then
        if CampaignSasukePlayer<0 then
            set unused=CampaignAdd(10,PLAYER_NEUTRAL_AGGRESSIVE,x,y)
            set CampaignSasuke=CampaignActor[unused]
        endif
        if n==16 then
            if CampaignNarutoPlayer>=0 then
                set CampaignNaruto=Hero[CampaignNarutoPlayer]
                call SetUnitPosition(CampaignNaruto,x-300.,y)
            else
                set unused=CampaignAdd(28,CampaignLeader,x-300.,y)
                set CampaignNaruto=CampaignActor[unused]
            endif
        endif
    elseif n==30 then
        set unused=CampaignAdd(3,PLAYER_NEUTRAL_PASSIVE,x-100.,y)
        set unused=CampaignAdd(4,PLAYER_NEUTRAL_PASSIVE,x+100.,y)
        set unused=CampaignAdd(11,PLAYER_NEUTRAL_PASSIVE,x,y-160.)
        call ExamBroadcast("Некоторое время спустя... |nИтачи: Он был здесь. |nКисамэ: Что будем делать? |nКабуто: Орочимару-сама... неужели вы мертвы?")
    elseif n==17 then
        set unused=CampaignAdd(19,PLAYER_NEUTRAL_AGGRESSIVE,x-100.,y)
        set unused=CampaignAdd(19,PLAYER_NEUTRAL_AGGRESSIVE,x+100.,y)
        call UnitAddAbility(CampaignActor[0],'Avul')
        call UnitAddAbility(CampaignActor[1],'Avul')
        loop
            exitwhen j>=20
            set unused=CampaignAdd(15,PLAYER_NEUTRAL_AGGRESSIVE,x+I2R(ModuloInteger(j,5)-2)*100.,y+I2R((j-ModuloInteger(j,5))/5)*100.+200.)
            set j=j+1
        endloop
    elseif n>=18 and n<=25 then
        set unused=CampaignAdd(n+2,PLAYER_NEUTRAL_AGGRESSIVE,x,y)
    elseif n>=26 and n<=28 then
        set owner=PLAYER_NEUTRAL_AGGRESSIVE
        if CampaignSasukePlayer>=0 and n==26 then
            set owner=CampaignSasukePlayer
        endif
        set unused=CampaignAdd(n-15,owner,x,y)
        if n==26 and CampaignSasukePlayer>=0 then
            call SelectUnitForPlayerSingle(CampaignActor[unused],Player(CampaignSasukePlayer))
        endif
    endif
endfunction
function CampaignQueueStage takes integer next returns nothing
    local integer p=0
    call CampaignEventsClose()
    call NoteClearAll()
    call CampaignVillageLandmarksClose()
    call StoryShopsClose()
    if NPCSourceReady and CampaignStage==12 then
        call DisableTrigger(OrigNPC_R2V)
        call DisableTrigger(OrigNPC_R3V)
    endif
    set CampaignQueued=next
    set CampaignTransition=true
    set CampaignPlaced=false
    set CampaignIntroAt=TimeNow
    loop
        exitwhen p>=12
        if FoundationAlive(Hero[p]) then
            call IssueImmediateOrder(Hero[p],"stop")
            call UnitAddAbility(Hero[p],'Avul')
            call PauseUnit(Hero[p],true)
            call RosterSyncPets(p)
        endif
        if CampaignClone[p]!=null then
            call PauseUnit(CampaignClone[p],true)
        endif
        set p=p+1
    endloop
    call CinematicFadeBJ(bj_CINEFADETYPE_FADEOUT,1.5,"ReplaceableTextures\\CameraMasks\\Black_mask.blp",0.,0.,0.,0.)
    if CampaignDialog!=null then
        call TimerDialogDisplay(CampaignDialog,false)
        call PauseTimer(CampaignClock)
    endif
endfunction
function CampaignPrepare takes nothing returns nothing
    call CampaignBindRoles()
    if CampaignCamera[0]==null then
        call CampaignCamerasInit()
    endif
    if CampaignScratch==null then
        set CampaignScratch=CreateGroup()
    endif
    if CampaignClock==null then
        set CampaignClock=CreateTimer()
        set CampaignDialog=CreateTimerDialog(CampaignClock)
    endif
endfunction
function CampaignStartPlay takes nothing returns nothing
    local integer p=0
    local integer j=0
    set CampaignTransition=false
    // Explicitly release any completed/pending transition filter before combat.
    call AbortCinematicFadeBJ()
    call DisplayCineFilter(false)
    call CampaignArenaVisibility(CampaignStage)
    set CampaignStartAt=TimeNow
    if CampaignStage==9 or CampaignStage==11 then
        set CampaignDuelAt=TimeNow+5.
    endif
    if CampaignStage==12 then
        // Player-owned invasion troops otherwise never pay their native kill bounty.
        set p=0
        loop
            exitwhen p>=16
            if not CampaignBountyActive then
                set CampaignBountyBefore[p]=GetPlayerState(Player(p),PLAYER_STATE_GIVES_BOUNTY)
            endif
            call SetPlayerState(Player(p),PLAYER_STATE_GIVES_BOUNTY,1)
            set p=p+1
        endloop
        set CampaignBountyActive=true
        set p=0
        set j=0
        loop
            exitwhen j>=8
            set CampaignWaveAt[j]=TimeNow+CampaignWavePeriod[j]+CampaignWaveDelay[j]
            set j=j+1
        endloop
        set CampaignJiraiyaAt=TimeNow+760.
        set CampaignKabutoAt=TimeNow+400.
        set CampaignSnakeAt=TimeNow+820.
        set CampaignOroAt=TimeNow+1160.
        call CampaignEventOpen(0,"Кабуто: до атаки",CampaignKabutoAt)
        call CampaignEventOpen(1,"Джирайя: до подкрепления",CampaignJiraiyaAt)
        call CampaignEventOpen(2,"Змея: до появления",CampaignSnakeAt)
        call CampaignEventOpen(3,"Орочимару: до атаки",CampaignOroAt)
    else
        call CampaignEventsClose()
    endif
    set j=0
    loop
        exitwhen j>=CampaignCount
        if CampaignActor[j]!=null and not (CampaignStage==12 and CampaignActorType[j]==13) and CampaignStage!=30 then
            call PauseUnit(CampaignActor[j],false)
        endif
        set j=j+1
    endloop
    set CampaignEndAt=0.
    if CampaignLimit[CampaignStage]>0. then
        set CampaignEndAt=TimeNow+CampaignLimit[CampaignStage]
        call TimerStart(CampaignClock,CampaignLimit[CampaignStage],false,function HUDClockEnd)
        call TimerDialogSetTitle(CampaignDialog,CampaignName[CampaignStage])
        call TimerDialogDisplay(CampaignDialog,true)
    endif
    loop
        exitwhen p>=12
        if Hero[p]!=null and not CampaignPermanentDead[p] and CampaignStage!=9 and CampaignStage!=11 and CampaignStage!=30 then
            if p==CampaignSasukePlayer and (CampaignStage==14 or (CampaignStage>=17 and CampaignStage<=28)) then
                call PauseUnit(Hero[p],true)
                call RosterSyncPets(p)
            elseif CampaignStage==16 and p!=CampaignSasukePlayer and p!=CampaignNarutoPlayer then
                call PauseUnit(Hero[p],true)
                call RosterSyncPets(p)
            else
                call PauseUnit(Hero[p],false)
                call RosterSyncPets(p)
                call UnitRemoveAbility(Hero[p],'Avul')
            endif
            if p==CampaignSasukePlayer and CampaignStage==26 then
                call SelectUnitForPlayerSingle(CampaignActor[0],Player(p))
            else
                call SelectUnitForPlayerSingle(Hero[p],Player(p))
            endif
        endif
        set p=p+1
    endloop
    set p=0
    loop
        exitwhen p>=12
        if CampaignClone[p]!=null then
            call PauseUnit(CampaignClone[p],false)
        endif
        set p=p+1
    endloop
    if CampaignStage==15 and CampaignSasukePlayer>=0 then
        call SetHeroLevel(CampaignSasuke,60,false)
        if GetUnitAbilityLevel(CampaignSasuke,'Rs05')==0 and GetHeroSkillPoints(CampaignSasuke)>0 then
            call SelectHeroSkill(CampaignSasuke,'Rs05')
        endif
        set CampaignSasukeGrowAt=TimeNow+5.
    endif
    set p=0
    loop
        exitwhen p>=12
        if Hero[p]!=null then
            call ResetToGameCameraForPlayer(Player(p),1.)
            if CampaignStage==9 or CampaignStage==11 then
                call PanCameraToTimedForPlayer(Player(p),CampaignTX[CampaignStage],CampaignTY[CampaignStage],0.)
            else
                call PanCameraToTimedForPlayer(Player(p),GetUnitX(Hero[p]),GetUnitY(Hero[p]),1.)
            endif
        endif
        set p=p+1
    endloop
    if CampaignStage==30 then
        call ExamBroadcast("Миссия завершена. Вы прошли все подключённые сюжетные главы до финала. Спасибо за игру!")
    endif
endfunction
function CampaignFinish takes boolean victory returns nothing
    local integer p=0
    if CampaignFinished then
        return
    endif
    set CampaignFinished=true
    call NoteClearAll()
    call CampaignVillageLandmarksClose()
    call CampaignArenaVisibility(0)
    call AbortCinematicFadeBJ()
    call DisplayCineFilter(false)
    call PauseTimer(CampaignClock)
    call TimerDialogDisplay(CampaignDialog,false)
    call CampaignClear()
    loop
        exitwhen p>=12
        if CampaignClone[p]!=null then
            call RemoveUnit(CampaignClone[p])
            set CampaignClone[p]=null
            set CampaignClonePending[p]=false
        endif
        if Hero[p]!=null then
            if (victory and p!=CampaignSasukePlayer) or (not victory and p==CampaignSasukePlayer) then
                call CustomVictoryBJ(Player(p),true,true)
            else
                call CustomDefeatBJ(Player(p),"Отряд погиб в убежище. Миссия провалена.")
            endif
        endif
        set p=p+1
    endloop
endfunction
function CampaignFinalBegin takes nothing returns nothing
    local integer p=0
    local integer n=0
    local integer q=0
    call NoteClearAll()
    loop
        exitwhen p>=12
        call CampaignStand(p)
        set p=p+1
    endloop
    loop
        exitwhen n>=3
        set p=CampaignWinner[n]
        set CampaignFinalPlayer[n]=p
        set CampaignEliminated[p]=false
        call CampaignResetFighter(p)
        call SetWidgetLife(Hero[p],GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE))
        call SetUnitState(Hero[p],UNIT_STATE_MANA,GetUnitState(Hero[p],UNIT_STATE_MAX_MANA))
        if n==0 then
            call SetUnitPosition(Hero[p],CampaignTX[11]-260.,CampaignTY[11]-150.)
        elseif n==1 then
            call SetUnitPosition(Hero[p],CampaignTX[11]+260.,CampaignTY[11]-150.)
        else
            call SetUnitPosition(Hero[p],CampaignTX[11],CampaignTY[11]+240.)
        endif
        set n=n+1
    endloop
    set n=0
    loop
        exitwhen n>=3
        set q=0
        loop
            exitwhen q>=3
            if n!=q then
                call SetPlayerAllianceStateAllyBJ(Player(CampaignFinalPlayer[n]),Player(CampaignFinalPlayer[q]),false)
                call SetPlayerAllianceStateVisionBJ(Player(CampaignFinalPlayer[n]),Player(CampaignFinalPlayer[q]),false)
            endif
            set q=q+1
        endloop
        set n=n+1
    endloop
    set CampaignFinalActive=true
    set CampaignDuelA=-1
    set CampaignDuelB=-1
    set CampaignDuelLive=false
    set CampaignDuelAt=TimeNow+5.
    call CampaignArenaCamera()
    call ExamBroadcast("Экзаменатор: Остались трое! Финальный бой — каждый сам за себя. Проигравшие остаются на трибунах. Начало через 5 секунд.")
endfunction
function CampaignArenaReward takes integer p returns nothing
    if p>=0 and p<12 and FoundationAlive(Hero[p]) and GetHeroLevel(Hero[p])<60 then
        call SetHeroLevel(Hero[p],GetHeroLevel(Hero[p])+1,true)
        call DisplayTimedTextToPlayer(Player(p),0.,0.,6.,"Победа на арене: +1 уровень!")
    endif
endfunction
function CampaignFinalTick takes nothing returns nothing
    local integer n=0
    local integer p=0
    local integer alive=0
    local integer winner=-1
    if not CampaignDuelLive then
        if TimeNow>=CampaignDuelAt then
            set CampaignDuelLive=true
            loop
                exitwhen n>=3
                set p=CampaignFinalPlayer[n]
                call PauseUnit(Hero[p],false)
                call RosterSyncPets(p)
                call UnitRemoveAbility(Hero[p],'Avul')
                call IssuePointOrder(Hero[p],"attack",CampaignTX[11],CampaignTY[11])
                set n=n+1
            endloop
            call ExamBroadcast("Экзаменатор: Финал втроём — бой!")
        endif
        return
    endif
    loop
        exitwhen n>=3
        set p=CampaignFinalPlayer[n]
        if not CampaignEliminated[p] then
            if FoundationAlive(Hero[p]) then
                set alive=alive+1
                set winner=p
            else
                set CampaignEliminated[p]=true
                call CampaignStand(p)
            endif
        endif
        set n=n+1
    endloop
    if alive<=1 then
        set CampaignFinalActive=false
        set CampaignDuelLive=false
        if alive==1 then
            set CampaignChampion=winner
            call CampaignArenaReward(winner)
            call CampaignStand(winner)
            call ExamBroadcast("Экзаменатор: Чемпион — "+HeroName[HeroRole[winner]]+"! Коноха ждёт вас всех.")
        else
            set CampaignChampion=-1
            call ExamBroadcast("Экзаменатор: Все финалисты выбыли одновременно. Финал завершён вничью. Коноха ждёт вас всех.")
        endif
        call CampaignQueueStage(12)
    endif
endfunction
function CampaignDuelTick takes nothing returns nothing
    local integer winner=-1
    local integer loser=-1
    local item reward=null
    if CampaignFinalActive then
        call CampaignFinalTick()
        return
    endif
    if CampaignDuelA<0 then
        if CampaignQueueCursor<CampaignQueueCount then
            call CampaignDuelNext()
        elseif CampaignBracket and CampaignWinnerCount==3 then
            call CampaignFinalBegin()
        elseif CampaignBracket and CampaignWinnerCount>1 then
            call CampaignQueueBuild(true)
            call CampaignDuelNext()
        else
            if CampaignBracket and CampaignWinnerCount==1 then
                set winner=CampaignWinner[0]
                set CampaignChampion=winner
                call ExamBroadcast("Экзаменатор: Победитель — "+HeroName[HeroRole[winner]]+"! Снаряжение чунина выдадут в деревне.")
            endif
            if CampaignStage==9 then
                set CampaignPrelimDone=true
            endif
            call CampaignQueueStage(CampaignStage+1)
        endif
        set reward=null
        return
    endif
    if not CampaignDuelLive then
        if TimeNow>=CampaignDuelAt then
            set CampaignDuelLive=true
            call PauseUnit(Hero[CampaignDuelA],false)
            call RosterSyncPets(CampaignDuelA)
            call PauseUnit(Hero[CampaignDuelB],false)
            call RosterSyncPets(CampaignDuelB)
            call UnitRemoveAbility(Hero[CampaignDuelA],'Avul')
            call UnitRemoveAbility(Hero[CampaignDuelB],'Avul')
            call IssueTargetOrder(Hero[CampaignDuelA],"attack",Hero[CampaignDuelB])
            call IssueTargetOrder(Hero[CampaignDuelB],"attack",Hero[CampaignDuelA])
            call ExamBroadcast("Экзаменатор: Бой!")
        endif
        return
    endif
    if not FoundationAlive(Hero[CampaignDuelA]) then
        set winner=CampaignDuelB
        set loser=CampaignDuelA
    elseif not FoundationAlive(Hero[CampaignDuelB]) then
        set winner=CampaignDuelA
        set loser=CampaignDuelB
    endif
    if winner>=0 then
        call CampaignArenaReward(winner)
        if CampaignStage==9 then
            set CampaignPrelimWinner[winner]=true
        endif
        set CampaignWinner[CampaignWinnerCount]=winner
        set CampaignWinnerCount=CampaignWinnerCount+1
        if CampaignBracket then
            set CampaignEliminated[loser]=true
        endif
        call CampaignStand(winner)
        call CampaignStand(loser)
        call SetPlayerAllianceStateAllyBJ(Player(winner),Player(loser),true)
        call SetPlayerAllianceStateAllyBJ(Player(loser),Player(winner),true)
        call ExamBroadcast("Экзаменатор: Побеждает "+HeroName[HeroRole[winner]]+". Следующая пара!")
        set CampaignDuelA=-1
        set CampaignDuelB=-1
        set CampaignDuelLive=false
    endif
endfunction
function CampaignNearest takes integer p returns unit
    local integer j=0
    local unit result=null
    local unit target=null
    local real best=999999999.
    local real dx=0.
    local real dy=0.
    local boolean allowed=true
    if CampaignClonePending[p] then
        return CampaignClone[p]
    endif
    if CampaignStage==9 or CampaignStage==11 then
        if CampaignFinalActive and CampaignDuelLive and not CampaignEliminated[p] then
            loop
                exitwhen j>=3
                if CampaignFinalPlayer[j]==p then
                    set allowed=false
                endif
                set j=j+1
            endloop
            if allowed then
                return null
            endif
            set j=0
            loop
                exitwhen j>=3
                set target=Hero[CampaignFinalPlayer[j]]
                if CampaignFinalPlayer[j]!=p and not CampaignEliminated[CampaignFinalPlayer[j]] and FoundationAlive(target) and SkillsCanSee(target,Player(p)) then
                    set dx=GetUnitX(target)-GetUnitX(Hero[p])
                    set dy=GetUnitY(target)-GetUnitY(Hero[p])
                    if dx*dx+dy*dy<best then
                        set best=dx*dx+dy*dy
                        set result=target
                    endif
                endif
                set j=j+1
            endloop
            set target=null
            return result
        elseif p==CampaignDuelA and CampaignDuelLive and SkillsCanSee(Hero[CampaignDuelB],Player(p)) then
            return Hero[CampaignDuelB]
        elseif p==CampaignDuelB and CampaignDuelLive and SkillsCanSee(Hero[CampaignDuelA],Player(p)) then
            return Hero[CampaignDuelA]
        endif
        return null
    endif
    if CampaignStage==12 then
        call GroupEnumUnitsInRange(CampaignScratch,GetUnitX(Hero[p]),GetUnitY(Hero[p]),1400.,null)
        loop
            set target=FirstOfGroup(CampaignScratch)
            exitwhen target==null
            call GroupRemoveUnit(CampaignScratch,target)
            if FoundationAlive(target) and GetUnitAbilityLevel(target,'Avul')==0 and not IsUnitPaused(target) and IsUnitEnemy(target,Player(p)) and (HeroRole[p]>=9 or CampaignDefenseAllows(p,target)) then
                set dx=GetUnitX(target)-GetUnitX(Hero[p])
                set dy=GetUnitY(target)-GetUnitY(Hero[p])
                if dx*dx+dy*dy<best then
                    set result=target
                    set best=dx*dx+dy*dy
                endif
            endif
        endloop
        // Leaf intercepts visible marching waves instead of rallying at the Hokage.
        // Ignore idle enemy camps, dead/hidden actors and units unseen by this team.
        if result==null and HeroRole[p]<9 then
            loop
                exitwhen j>=CampaignCount
                set target=CampaignActor[j]
                if CampaignActorRoute[j]>=0 and FoundationAlive(target) and not IsUnitPaused(target) and GetUnitAbilityLevel(target,'Avul')==0 and IsUnitEnemy(target,Player(p)) and SkillsCanSee(target,Player(p)) and CampaignDefenseAllows(p,target) then
                    set dx=GetUnitX(target)-GetUnitX(Hero[p])
                    set dy=GetUnitY(target)-GetUnitY(Hero[p])
                    if dx*dx+dy*dy<best then
                        set result=target
                        set best=dx*dx+dy*dy
                    endif
                endif
                set j=j+1
            endloop
        endif
        if result==null and HeroRole[p]>=9 and FoundationAlive(CampaignActor[0]) and IsUnitEnemy(CampaignActor[0],Player(p)) then
            set result=CampaignActor[0]
        endif
        set target=null
        return result
    endif
    loop
        exitwhen j>=CampaignCount+12
        if j<CampaignCount then
            set target=CampaignActor[j]
        else
            set target=Hero[j-CampaignCount]
        endif
        if FoundationAlive(target) and not IsUnitPaused(target) and not IsUnitHidden(target) and IsUnitEnemy(target,Player(p)) and not (CampaignStage==17 and j<2) then
            set dx=GetUnitX(target)-GetUnitX(Hero[p])
            set dy=GetUnitY(target)-GetUnitY(Hero[p])
            if dx*dx+dy*dy<best then
                set best=dx*dx+dy*dy
                set result=target
            endif
        endif
        set j=j+1
    endloop
    set target=null
    return result
endfunction
function CampaignBot takes integer p, unit enemy returns nothing
    local integer t=StoryTeam(p)
    local unit leader=StoryLeader(t)
    local unit shop=StoryShopFor(p)
    if CampaignTransition or CampaignPermanentDead[p] or IsUnitPaused(Hero[p]) then
        set leader=null
        return
    endif
    if shop!=null and (CampaignStage!=10 or ExamNear(Hero[p],GetUnitX(shop),GetUnitY(shop),650.)) and TimeNow>=StoryBuyAt[p] and StoryShopTripUntil[p]==0. and GetWidgetLife(Hero[p])>GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.45 then
        if GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)>=StoryPrice[StoryChooseItem(p)] and StoryHasItemSpace(p) then
            set StoryShopTripUntil[p]=TimeNow+45.
        else
            set StoryBuyAt[p]=TimeNow+10.
        endif
    endif
    if StoryShopTripUntil[p]>0. and TimeNow>=StoryShopTripUntil[p] then
        set StoryShopTripUntil[p]=0.
        set StoryBuyAt[p]=TimeNow+20.
    endif
    if CampaignClonePending[p] then
        if enemy!=null then
            call IssueTargetOrder(Hero[p],"attack",enemy)
        endif
    elseif CampaignStage==17 and HeroRole[p]==2 and (FoundationAlive(CampaignActor[0]) or FoundationAlive(CampaignActor[1])) then
        if FoundationAlive(CampaignActor[0]) then
            set leader=CampaignActor[0]
        else
            set leader=CampaignActor[1]
        endif
        if ExamNear(Hero[p],GetUnitX(leader),GetUnitY(leader),300.) then
            if GetUnitAbilityLevel(Hero[p],'R204')==0 and GetHeroSkillPoints(Hero[p])>0 then
                call SelectHeroSkill(Hero[p],'R204')
            endif
            call IssueImmediateOrder(Hero[p],"drunkenhaze")
        else
            call IssuePointOrder(Hero[p],"move",GetUnitX(leader),GetUnitY(leader))
        endif
    elseif CampaignStage==15 and p==CampaignSasukePlayer then
        if enemy!=null then
            call IssuePointOrder(Hero[p],"move",CampaignFiveX[GetRandomInt(0,4)],CampaignFiveY[GetRandomInt(0,4)])
        endif
    elseif CampaignStage==9 or CampaignStage==11 then
        if enemy!=null then
            call IssueTargetOrder(Hero[p],"attack",enemy)
        endif
    elseif StoryRetreat[t] or GetWidgetLife(Hero[p])<GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.2 then
        call IssuePointOrder(Hero[p],"move",SpawnX[p],SpawnY[p])
        if shop!=null and ExamNear(Hero[p],GetUnitX(shop),GetUnitY(shop),250.) then
            call StoryBuy(p)
        endif
    elseif CampaignStage==12 and HeroRole[p]<9 and enemy!=null then
        // Combat overrides shopping and following while a wave needs interception.
        set StoryShopTripUntil[p]=0.
        set StoryBuyAt[p]=TimeNow+10.
        call IssueTargetOrder(Hero[p],"attack",enemy)
    elseif not StoryMarch[t] and leader!=Hero[p] and leader!=null and not (CampaignStage==12 and HeroRole[p]<9) then
        if enemy!=null and ExamNear(enemy,GetUnitX(Hero[p]),GetUnitY(Hero[p]),700.) then
            call IssueTargetOrder(Hero[p],"attack",enemy)
        else
            call IssueTargetOrder(Hero[p],"follow",leader)
        endif
    elseif shop!=null and TimeNow>=StoryBuyAt[p] and StoryShopTripUntil[p]>TimeNow then
        if ExamNear(Hero[p],GetUnitX(shop),GetUnitY(shop),250.) then
            call StoryBuy(p)
            set StoryShopTripUntil[p]=0.
        else
            call IssuePointOrder(Hero[p],"move",GetUnitX(shop),GetUnitY(shop))
        endif
    elseif enemy!=null then
        call IssueTargetOrder(Hero[p],"attack",enemy)
    elseif CampaignStage==12 and HeroRole[p]<9 then
        // Fixed 30/70 allocation prevents every hero chasing the same northern wave.
        if CampaignDefenseLane[p]==5 then
            call IssuePointOrder(Hero[p],"attack",CampaignRouteX[5],CampaignRouteY[5])
        else
            call IssuePointOrder(Hero[p],"attack",CampaignRouteX[3],CampaignRouteY[3])
        endif
    elseif CampaignStage==12 or CampaignStage==13 then
        call IssuePointOrder(Hero[p],"attack",CampaignTX[CampaignStage],CampaignTY[CampaignStage])
    else
        call IssuePointOrder(Hero[p],"move",SpawnX[p],SpawnY[p])
        if shop!=null and ExamNear(Hero[p],GetUnitX(shop),GetUnitY(shop),250.) then
            call StoryBuy(p)
        endif
    endif
    set leader=null
    set shop=null
endfunction
function CampaignNPCTick takes nothing returns nothing
    local integer processed=0
    local integer j=0
    local unit target=null
    local unit u=null
    local unit candidate=null
    local real best=0.
    local real radius=1100.
    local real dx=0.
    local real dy=0.
    loop
        exitwhen processed>=24 or CampaignCount==0
        if CampaignThinkCursor>=CampaignCount then
            set CampaignThinkCursor=0
        endif
        set j=CampaignThinkCursor
        set CampaignThinkCursor=j+1
        set processed=processed+1
        set u=CampaignActor[j]
        if FoundationAlive(u) and not IsUnitPaused(u) and not NPCBusy(u) and CampaignActorType[j]!=18 and CampaignActorType[j]!=19 and CampaignActorType[j]!=14 and not (CampaignActorType[j]==11 and not CampaignKabutoAI) and not (CampaignStage==26 and CampaignSasukePlayer>=0 and GetPlayerController(Player(CampaignSasukePlayer))!=MAP_CONTROL_COMPUTER) and not (CampaignStage==12 and (CampaignActorType[j]==12 or CampaignActorType[j]==13) and GetPlayerController(GetOwningPlayer(u))!=MAP_CONTROL_COMPUTER and Hero[GetPlayerId(GetOwningPlayer(u))]!=null) then
            set target=null
            set radius=1100.
            if CampaignSoundGuard(CampaignActorType[j]) then
                if CampaignActorType[j]==5 then
                    set radius=250.
                elseif CampaignActorType[j]==6 then
                    set radius=700.
                elseif CampaignActorType[j]==8 then
                    set radius=800.
                else
                    set radius=400.
                endif
            endif
            set best=radius*radius
            call GroupEnumUnitsInRange(CampaignScratch,GetUnitX(u),GetUnitY(u),radius,null)
            loop
                set candidate=FirstOfGroup(CampaignScratch)
                exitwhen candidate==null
                call GroupRemoveUnit(CampaignScratch,candidate)
                if FoundationAlive(candidate) and GetUnitAbilityLevel(candidate,'Avul')==0 and not IsUnitPaused(candidate) and not IsUnitHidden(candidate) and SkillsCanSee(candidate,GetOwningPlayer(u)) and (not CampaignSoundGuard(CampaignActorType[j]) or IsUnitType(candidate,UNIT_TYPE_HERO)) and ((CampaignActorType[j]==32 and IsUnitAlly(candidate,GetOwningPlayer(u)) and GetWidgetLife(candidate)<GetUnitState(candidate,UNIT_STATE_MAX_LIFE)*.9) or (CampaignActorType[j]!=32 and IsUnitEnemy(candidate,GetOwningPlayer(u)))) then
                    set dx=GetUnitX(candidate)-GetUnitX(u)
                    set dy=GetUnitY(candidate)-GetUnitY(u)
                    if dx*dx+dy*dy<best then
                        set target=candidate
                        set best=dx*dx+dy*dy
                    endif
                endif
            endloop
            if CampaignSoundGuard(CampaignActorType[j]) and GetWidgetLife(u)<=10000. then
                // Original LFO: wounded camp elites seek their own camp fountain.
                if TimeNow>=CampaignMoveAt[j] then
                    if CampaignActorType[j]==6 or CampaignActorType[j]==9 then
                        call IssuePointOrder(u,"move",-2624.,-11840.)
                    else
                        call IssuePointOrder(u,"move",5632.,-3008.)
                    endif
                    set CampaignMoveAt[j]=TimeNow+3.
                endif
            elseif target!=null then
                if CampaignStage==12 and CampaignActorRoute[j]>=0 and best>650.*650. and TimeNow>=CampaignMoveAt[j] and CampaignWaveRecover(j) then
                    set CampaignMoveAt[j]=TimeNow+2.
                elseif NPCUseInventory(u,CampaignActorType[j],target) or NPCTry(u,CampaignActorType[j],target) then
                    set CampaignMoveAt[j]=TimeNow+1.
                elseif TimeNow>=CampaignMoveAt[j] then
                    if CampaignActorType[j]==32 then
                        call IssuePointOrder(u,"move",GetUnitX(target),GetUnitY(target))
                    else
                        call IssueTargetOrder(u,"attack",target)
                    endif
                    set CampaignMoveAt[j]=TimeNow+3.
                endif
            elseif CampaignStage==12 and CampaignActorRoute[j]>=0 and TimeNow>=CampaignMoveAt[j] then
                if ExamNear(u,CampaignRouteX[CampaignActorRoute[j]],CampaignRouteY[CampaignActorRoute[j]],220.) then
                    if CampaignActorRoute[j]==8 or CampaignActorRoute[j]==11 then
                        set CampaignActorRoute[j]=11
                    else
                        set CampaignActorRoute[j]=8
                    endif
                    set CampaignWalkAt[j]=TimeNow+8.
                    set CampaignWalkAttempt[j]=0
                endif
                if not CampaignWaveRecover(j) then
                    call IssuePointOrder(u,"attack",CampaignRouteX[CampaignActorRoute[j]],CampaignRouteY[CampaignActorRoute[j]])
                    set CampaignMoveAt[j]=TimeNow+3.
                endif
            elseif CampaignStage==12 and (CampaignSoundGuard(CampaignActorType[j]) or CampaignActorType[j]==1 or CampaignActorType[j]==2 or CampaignActorType[j]==17 or CampaignActorType[j]==34 or (CampaignActorType[j]>=29 and CampaignActorType[j]<=33)) and TimeNow>=CampaignMoveAt[j] then
                // Native creep guarding was disabled; explicitly return only stationary defenders.
                if not ExamNear(u,CampaignPostX[j],CampaignPostY[j],96.) then
                    call IssuePointOrder(u,"move",CampaignPostX[j],CampaignPostY[j])
                elseif GetUnitCurrentOrder(u)!=0 then
                    call IssueImmediateOrder(u,"stop")
                    call SetUnitFacing(u,CampaignPostFacing[j])
                endif
                set CampaignMoveAt[j]=TimeNow+3.
            endif
        endif
    endloop
    set target=null
    set candidate=null
    set u=null
endfunction
function CampaignDeploy takes nothing returns nothing
    local integer processed=0
    local integer j=0
    local integer slot=0
    loop
        exitwhen processed>=24 or CampaignDeployCursor>=242
        set j=CampaignDeployCursor
        if j<140 then
            set slot=CampaignAdd(17,CampaignDefenseOwner,CampaignLeafX[j],CampaignLeafY[j])
            call SetUnitFacing(CampaignActor[slot],CampaignLeafFacing[j])
            set CampaignPostFacing[slot]=CampaignLeafFacing[j]
            call SetUnitColor(CampaignActor[slot],ConvertPlayerColor(12))
        else
            set j=j-140
            set slot=CampaignAdd(34,CampaignDefenseOwner,CampaignAnbuX[j],CampaignAnbuY[j])
            call SetUnitFacing(CampaignActor[slot],CampaignAnbuFacing[j])
            set CampaignPostFacing[slot]=CampaignAnbuFacing[j]
            call SetUnitColor(CampaignActor[slot],ConvertPlayerColor(12))
        endif
        set CampaignDeployCursor=CampaignDeployCursor+1
        set processed=processed+1
    endloop
endfunction
// Explicit test shortcut, invoked synchronously by the first occupied human.
function CampaignTestArena takes integer sender, integer arena returns nothing
    local integer p=0
    local integer j=0
    if arena!=1 and arena!=2 and arena!=3 then
        call DisplayTimedTextToPlayer(Player(sender),0.,0.,12.,"Тест: -arena 1 — предварительные бои; -arena 2 — финальный турнир; -village — нападение на Коноху.")
        return
    endif
    loop
        exitwhen p>=12 or (GetPlayerSlotState(Player(p))==PLAYER_SLOT_STATE_PLAYING and GetPlayerController(Player(p))!=MAP_CONTROL_COMPUTER)
        set p=p+1
    endloop
    if sender!=p then
        call DisplayTimedTextToPlayer(Player(sender),0.,0.,10.,"Тестовые переходы доступны первому игроку-человеку в списке слотов.")
        return
    endif
    if CampaignFinished or CampaignStage>11 or CampaignTransition then
        call DisplayTimedTextToPlayer(Player(sender),0.,0.,12.,"Для теста начните новую игру или дождитесь окончания текущего перехода. Команда доступна до вторжения в Коноху.")
        return
    endif
    if not SkillDataReady or SpawnClock!=null or StoryPopulateCursor<64 then
        call DisplayTimedTextToPlayer(Player(sender),0.,0.,10.,"Герои ещё создаются. Повторите команду через несколько секунд.")
        return
    endif
    if CampaignStage==0 then
        // Stop early-chapter producers before leaving their maps; do not award skipped quests.
        set ExamPhase=4
        set StoryMentorsReleased=true
        if StoryMentorClock!=null then
            call PauseTimer(StoryMentorClock)
            call DestroyTimer(StoryMentorClock)
            set StoryMentorClock=null
        endif
        if StoryMentorDialog!=null then
            call DestroyTimerDialog(StoryMentorDialog)
            set StoryMentorDialog=null
        endif
        if StoryPopulateClock!=null then
            call PauseTimer(StoryPopulateClock)
            call DestroyTimer(StoryPopulateClock)
            set StoryPopulateClock=null
        endif
        if ExamAnswers!=null then
            call DestroyTrigger(ExamAnswers)
            set ExamAnswers=null
        endif
        if ExamClock!=null then
            call PauseTimer(ExamClock)
            call DestroyTimer(ExamClock)
            set ExamClock=null
        endif
        if ExamDialog!=null then
            call DestroyTimerDialog(ExamDialog)
            set ExamDialog=null
        endif
        if PhaseDialog!=null then
            call TimerDialogDisplay(PhaseDialog,false)
        endif
        if PhaseClock!=null then
            call PauseTimer(PhaseClock)
        endif
        loop
            exitwhen j>=85
            if j<72 and StoryEnemy[j]!=null then
                call RemoveUnit(StoryEnemy[j])
                set StoryEnemy[j]=null
            endif
            if j<72 and EnemyMark[j]!=null then
                call DestroyEffect(EnemyMark[j])
                set EnemyMark[j]=null
            endif
            if j<72 then
                set EnemyPending[j]=0.
                set EnemyFocus[j]=null
            endif
            if ExamEnemy[j]!=null then
                call RemoveUnit(ExamEnemy[j])
                set ExamEnemy[j]=null
            endif
            set j=j+1
        endloop
        set j=0
        loop
            exitwhen j>=4
            if StoryMentor[j]!=null then
                call RemoveUnit(StoryMentor[j])
                set StoryMentor[j]=null
            endif
            set StoryBoss[j]=null
            set StoryStage[j]=8
            set StoryStarted[j]=true
            set StoryAdvanceAt[j]=0.
            set StoryRetreat[j]=false
            set StoryMarch[j]=true
            if j<2 and ExamFountain[j]!=null then
                call RemoveUnit(ExamFountain[j])
                set ExamFountain[j]=null
            endif
            set j=j+1
        endloop
        if ExamTower!=null then
            call RemoveUnit(ExamTower)
            set ExamTower=null
        endif
        if ExamRect!=null then
            call RemoveRect(ExamRect)
            set ExamRect=null
        endif
    endif
    call CampaignPrepare()
    if arena==1 then
        call CampaignQueueStage(9)
    elseif arena==2 then
        call CampaignQueueStage(11)
    else
        call CampaignQueueStage(12)
    endif
    call ExamBroadcast("ТЕСТ ЭТАПА: предыдущие задания пропущены без наград. Навыки, уровень и снаряжение героев сохранены.")
endfunction
function CampaignInvasionEvents takes nothing returns nothing
    local integer unused=0
    if CampaignFinished or CampaignTransition or CampaignStage!=12 then
        return
    endif
    if CampaignJiraiyaAt>0. and (CampaignEventDue[1] or TimeNow>=CampaignJiraiyaAt) then
        set unused=CampaignAdd(33,CampaignDefenseOwner,CampaignSupportX[6],CampaignSupportY[6])
        call CampaignEventClose(1)
        set CampaignJiraiyaAt=0.
        call ExamBroadcast("Джирайя: Я здесь! Помогу защитить деревню.")
    endif
    if CampaignKabutoAt>0. and (CampaignEventDue[0] or TimeNow>=CampaignKabutoAt) then
        set unused=CampaignAdd(11,CampaignAttackerOwner[1],CampaignSupportX[5],CampaignSupportY[5])
        set CampaignVillageKabuto=CampaignActor[unused]
        set CampaignActorRoute[unused]=3
        call IssuePointOrder(CampaignVillageKabuto,"attack",CampaignRouteX[3],CampaignRouteY[3])
        call CampaignEventClose(0)
        set CampaignKabutoAt=0.
        call ExamBroadcast("Канкуро: Кабуто прибыл на помощь нападающим!")
    endif
    if CampaignSnakeAt>0. and (CampaignEventDue[2] or TimeNow>=CampaignSnakeAt) then
        set unused=CampaignAdd(36,CampaignAttackerOwner[2],CampaignSupportX[5],CampaignSupportY[5])
        set CampaignVillageSnake=CampaignActor[unused]
        set CampaignActorRoute[unused]=3
        call IssuePointOrder(CampaignVillageSnake,"attack",CampaignRouteX[3],CampaignRouteY[3])
        set CampaignSnakeGoneAt=TimeNow+300.
        call CampaignEventClose(2)
        set CampaignSnakeAt=0.
        call ExamBroadcast("Темари: Призвана огромная змея! Она останется на поле пять минут.")
    endif
    if CampaignSnakeGoneAt>0. and TimeNow>=CampaignSnakeGoneAt then
        if CampaignVillageSnake!=null then
            call RemoveUnit(CampaignVillageSnake)
            set CampaignVillageSnake=null
        endif
        set CampaignSnakeGoneAt=0.
    endif
    if CampaignOroAt>0. and (CampaignEventDue[3] or TimeNow>=CampaignOroAt) then
        call SetUnitOwner(CampaignVillageOro,Player(CampaignAttackOwner),true)
        call PauseUnit(CampaignVillageOro,false)
        call CampaignEventClose(3)
        set CampaignOroAt=0.
        call ExamBroadcast("Орочимару: Теперь я лично разберусь с Хокагэ!")
    endif
endfunction
function CampaignTick takes nothing returns nothing
    local integer n=CampaignStage
    local integer p=0
    local integer j=0
    local integer alive=0
    local integer unused=0
    local integer owner=PLAYER_NEUTRAL_AGGRESSIVE
    local boolean ready=true
    local integer k=0
    local integer lane=0
    local integer waveKind=16
    local integer origin=0
    local integer destination=1
    local item growth=null
    local integer camera=0
    if CampaignFinished then
        return
    endif
    if CampaignStage==0 and not CampaignTransition then
        if ExamPhase!=4 then
            return
        endif
        call CampaignPrepare()
        call CampaignQueueStage(9)
        return
    endif
    if CampaignTransition then
        if CampaignStage==12 and CampaignPlaced then
            call CampaignDeploy()
        endif
        if not CampaignPlaced and TimeNow>=CampaignIntroAt+1.5 then
            call CampaignClear()
            set CampaignStage=CampaignQueued
            call CampaignArenaVisibility(CampaignStage)
            set CampaignPlaced=true
            set n=CampaignStage
            call CampaignAlliances(1)
            if n==12 then
                call CampaignAlliances(2)
            endif
            call CampaignMoveHeroes()
            if CampaignMusic[n]<0 then
                call StopMusic(false)
                call PauseTimer(MusicClock)
            else
                set MusicCursor=CampaignMusic[n]
                call FoundationMusicStart()
            endif
            if n==12 then
                set MusicCursor=6
                call FoundationMusicStart()
            endif
            call CampaignSpawnStage()
            if n==17 then
                call CampaignClonesSpawn()
            endif
            set camera=0
            if n==10 then
                set camera=2
            elseif n==11 then
                set camera=4
            elseif n==12 then
                set camera=6
            elseif n==13 then
                set camera=7
            elseif n==14 or n==15 then
                set camera=9
            elseif n>=17 then
                set camera=10
            endif
            set p=0
            loop
                exitwhen p>=12
                if Hero[p]!=null then
                    if n>=17 then
                        call PanCameraToTimedForPlayer(Player(p),GetUnitX(Hero[p]),GetUnitY(Hero[p]),0.)
                    else
                        call CameraSetupApplyForPlayer(true,CampaignCamera[camera],Player(p),0.)
                    endif
                    if n==9 or n==10 or n==13 then
                        call CameraSetupApplyForPlayer(true,CampaignCamera[camera+1],Player(p),5.)
                    endif
                endif
                set p=p+1
            endloop
            call ExamBroadcast(CampaignIntro[n])
            call CinematicFadeBJ(bj_CINEFADETYPE_FADEIN,1.5,"ReplaceableTextures\\CameraMasks\\Black_mask.blp",0.,0.,0.,0.)
        endif
        if CampaignPlaced and TimeNow>=CampaignIntroAt+8. and (CampaignStage!=12 or CampaignDeployCursor>=242) then
            call CampaignStartPlay()
            if CampaignStage==12 then
                set MusicCursor=7
                call FoundationMusicStart()
            endif
        endif
        return
    endif
    if CampaignStage==9 or CampaignStage==11 then
        call CampaignDuelTick()
        return
    endif
    if CampaignStage>=17 and CampaignStage<30 then
        call CampaignClonesTick()
        set p=0
        loop
            exitwhen p>=12
            if Hero[p]!=null then
                if FoundationAlive(Hero[p]) and p!=CampaignSasukePlayer then
                    set alive=alive+1
                elseif p!=CampaignSasukePlayer then
                    set CampaignPermanentDead[p]=true
                endif
            endif
            set p=p+1
        endloop
        if alive==0 or (CampaignNarutoPlayer>=0 and not FoundationAlive(Hero[CampaignNarutoPlayer])) then
            call CampaignFinish(false)
            return
        endif
    endif
    if CampaignStage==12 then
        call ExecuteFunc("CampaignInvasionEvents")
    endif
    if TimeNow>=CampaignNextBot then
        // A crowded NPC scan must not exhaust the parent story/event thread.
        call ExecuteFunc("CampaignNPCTick")
        set CampaignNextBot=TimeNow+.5
    endif
    if CampaignStage==10 then
        if not CampaignFound and CampaignActor[CampaignJiraiya]!=null and not FoundationAlive(CampaignActor[CampaignJiraiya]) then
            set CampaignFound=true
            set CampaignTrainingAt=TimeNow+7.
            call PauseTimer(CampaignClock)
            call TimerDialogDisplay(CampaignDialog,false)
            set unused=CampaignAdd(14,PLAYER_NEUTRAL_PASSIVE,GetUnitX(CampaignActor[CampaignJiraiya]),GetUnitY(CampaignActor[CampaignJiraiya]))
            call ExamBroadcast("Джирайя: Ладно, вы меня нашли! Проведём тренировку. Каждый получает 2200 опыта. Затем возвращаемся на турнир.")
            set p=0
            loop
                exitwhen p>=12
                if Hero[p]!=null then
                    call AddHeroXP(Hero[p],2200,false)
                    call PauseUnit(Hero[p],true)
                    call RosterSyncPets(p)
                    call UnitAddAbility(Hero[p],'Avul')
                    call PanCameraToTimedForPlayer(Player(p),GetUnitX(CampaignActor[unused]),GetUnitY(CampaignActor[unused]),2.)
                endif
                set p=p+1
            endloop
        endif
        if (CampaignFound and TimeNow>=CampaignTrainingAt) or (not CampaignFound and TimeNow>=CampaignEndAt) then
            call CampaignQueueStage(11)
        endif
    elseif CampaignStage==12 then
        if not FoundationAlive(CampaignActor[0]) then
            call ExamBroadcast("Какаши: Третий Хокагэ пал... Вторжение окончено, но опасность ещё не миновала.")
            call CampaignQueueStage(13)
        elseif TimeNow>=CampaignEndAt then
            call ExamBroadcast("Какаши: Хокагэ выстоял! Отряды Листа получают награду. Теперь защитим наставников от Акацуки.")
            set p=0
            loop
                exitwhen p>=9
                if Hero[p]!=null then
                    call SetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)+1000)
                endif
                set p=p+1
            endloop
            call CampaignQueueStage(13)
        endif
        set lane=0
        loop
            exitwhen lane>=8 or CampaignTransition
            if TimeNow>=CampaignWaveAt[lane] then
                call CampaignInvasionWave(lane)
                set CampaignWaveAt[lane]=CampaignWaveAt[lane]+CampaignWavePeriod[lane]
            endif
            set lane=lane+1
        endloop
    elseif CampaignStage==13 then
        if not FoundationAlive(CampaignActor[0]) or not FoundationAlive(CampaignActor[1]) then
            call ExamBroadcast("Гай: Наставник пал. Испытание провалено, подкрепление оттесняет врага. Продолжаем миссию, но без награды.")
            call CampaignQueueStage(14)
        elseif TimeNow>=CampaignEndAt or (not FoundationAlive(CampaignActor[2]) and not FoundationAlive(CampaignActor[3])) then
            call ExamBroadcast("Кисамэ: Мы ещё вернёмся за Девятихвостым. |nГай: Они отступают! АНБУ прибыло вовремя.")
            call CampaignQueueStage(14)
        endif
    elseif CampaignStage==14 then
        if CampaignAliveEnemies()==0 or TimeNow>=CampaignEndAt then
            call ExamBroadcast("Шикамару: Саске освободился! За ним, времени мало!")
            call CampaignQueueStage(15)
        endif
    elseif CampaignStage==15 then
        if CampaignSasukePlayer>=0 and FoundationAlive(CampaignSasuke) and TimeNow>=CampaignSasukeGrowAt then
            set growth=CreateItem('Nsht',GetUnitX(CampaignSasuke),GetUnitY(CampaignSasuke))
            if not UnitAddItem(CampaignSasuke,growth) then
                call RemoveItem(growth)
            endif
            set CampaignSasukeGrowAt=TimeNow+5.
            set growth=null
        endif
        if not FoundationAlive(CampaignSasuke) then
            call ExamBroadcast("Наруто: Я догнал тебя, Саске. Нам нужно поговорить!")
            call CampaignQueueStage(16)
        elseif TimeNow>=CampaignEndAt then
            call ExamBroadcast("Шикамару: Он ушёл к Орочимару... Наруто отправляется за ним.")
            call CampaignQueueStage(16)
        endif
    elseif CampaignStage==16 then
        if not FoundationAlive(CampaignSasuke) or not FoundationAlive(CampaignNaruto) then
            call CampaignQueueStage(17)
        endif
    elseif CampaignStage==17 then
        set ready=false
        set j=0
        loop
            exitwhen j>=12
            if FoundationAlive(Hero[j]) and HeroRole[j]==2 then
                set ready=true
            endif
            set j=j+1
        endloop
        if not ready and CampaignAliveEnemies()<=2 then
            set j=0
            loop
                exitwhen j>=2
                if FoundationAlive(CampaignActor[j]) then
                    call UnitRemoveAbility(CampaignActor[j],'Avul')
                    call KillUnit(CampaignActor[j])
                endif
                set j=j+1
            endloop
        endif
        if CampaignAliveEnemies()==0 then
            call CampaignQueueStage(26)
        endif
    elseif CampaignStage==29 then
        if not FoundationAlive(CampaignSasuke) then
            call CampaignQueueStage(30)
        endif
    elseif CampaignStage==30 then
        if TimeNow>=CampaignStartAt+12. then
            call CampaignFinish(true)
        endif
    elseif CampaignAliveEnemies()==0 then
        call CampaignQueueStage(CampaignStage+1)
    endif
endfunction
