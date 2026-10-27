// Post-story shared defense. One bounded state machine on Foundation's existing heartbeat.
function Endless50Alliances takes nothing returns nothing
    local integer p=0
    call CampaignAlliances(1)
    loop
        exitwhen p>=12
        call SetPlayerAllianceStateAllyBJ(Player(15),Player(p),false)
        call SetPlayerAllianceStateAllyBJ(Player(p),Player(15),false)
        call SetPlayerAllianceStateVisionBJ(Player(15),Player(p),false)
        call SetPlayerAllianceStateVisionBJ(Player(p),Player(15),false)
        call SetPlayerAlliance(Player(13),Player(p),ALLIANCE_SHARED_CONTROL,false)
        call SetPlayerAlliance(Player(15),Player(p),ALLIANCE_SHARED_CONTROL,false)
        call SetPlayerAlliance(Player(13),Player(p),ALLIANCE_SHARED_ADVANCED_CONTROL,false)
        call SetPlayerAlliance(Player(15),Player(p),ALLIANCE_SHARED_ADVANCED_CONTROL,false)
        set p=p+1
    endloop
    call SetPlayerAllianceStateAllyBJ(Player(13),Player(15),false)
    call SetPlayerAllianceStateAllyBJ(Player(15),Player(13),false)
    call SetPlayerAllianceStateAllyBJ(Player(14),Player(15),false)
    call SetPlayerAllianceStateAllyBJ(Player(15),Player(14),false)
endfunction
function Endless50ReadyHero takes integer p returns nothing
    if Hero[p]==null or GetPlayerSlotState(Player(p))!=PLAYER_SLOT_STATE_PLAYING then
        return
    endif
    set CampaignPermanentDead[p]=false
    set CampaignClonePending[p]=false
    set StoryRevive[p]=0.
    set SpawnX[p]=CampaignDefenderX[p]
    set SpawnY[p]=CampaignDefenderY[p]
    if not FoundationAlive(Hero[p]) then
        if not ReviveHero(Hero[p],SpawnX[p],SpawnY[p],true) then
            set StoryRevive[p]=TimeNow+1.
            return
        endif
    endif
    call TreeJumpEnd(p)
    call RamenClearUnit(Hero[p])
    call RosterResetEffects(p)
    call CampaignResetFighter(p)
    call SkillsClearSharingan(p)
    call SetUnitInvulnerable(Hero[p],false)
    call UnitRemoveAbility(Hero[p],'Avul')
    call ShowUnit(Hero[p],false)
    call UnitRemoveAbility(Hero[p],'Aloc')
    call UnitRemoveAbility(Hero[p],'Apiv')
    call ShowUnit(Hero[p],true)
    call SetUnitVertexColor(Hero[p],255,255,255,255)
    call SetUnitTimeScale(Hero[p],1.)
    call SetUnitPathing(Hero[p],true)
    call SetUnitPosition(Hero[p],SpawnX[p],SpawnY[p])
    call PauseUnit(Hero[p],false)
    call SetWidgetLife(Hero[p],GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE))
    call SetUnitState(Hero[p],UNIT_STATE_MANA,GetUnitState(Hero[p],UNIT_STATE_MAX_MANA))
    call SetUnitAnimation(Hero[p],"stand")
    call RosterSyncPets(p)
    call ResetToGameCameraForPlayer(Player(p),0.)
    call PanCameraToTimedForPlayer(Player(p),SpawnX[p],SpawnY[p],1.)
    call SelectUnitForPlayerSingle(Hero[p],Player(p))
endfunction
function Endless50StopProducers takes nothing returns nothing
    local integer j=0
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
    if PhaseClock!=null then
        call PauseTimer(PhaseClock)
    endif
    if PhaseDialog!=null then
        call TimerDialogDisplay(PhaseDialog,false)
    endif
    loop
        exitwhen j>=85
        if j<72 then
            if StoryEnemy[j]!=null then
                call RemoveUnit(StoryEnemy[j])
                set StoryEnemy[j]=null
            endif
            if EnemyMark[j]!=null then
                call DestroyEffect(EnemyMark[j])
                set EnemyMark[j]=null
            endif
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
        set StoryStarted[j]=true
        set j=j+1
    endloop
endfunction
function Endless50Start takes nothing returns nothing
    local integer p=0
    if Endless50Active or Endless50Starting then
        return
    endif
    call Endless50StopProducers()
    call CampaignPrepare()
    call CampaignEventsClose()
    call NoteClearAll()
    call CampaignArenaVisibility(0)
    call CampaignClear()
    call StoryShopsClose()
    call CampaignVillageLandmarksClose()
    set CampaignFinished=false
    set CampaignStage=31
    set CampaignQueued=31
    set CampaignPlaced=true
    set CampaignTransition=true
    set CampaignIntroAt=TimeNow
    set CampaignEndAt=0.
    set CampaignDefenseOwner=13
    set CampaignKabutoAI=true
    set Endless50Starting=true
    set Endless50Cursor=0
    set Endless50BossRound=0
    set Endless50CleanupCursor=17
    call AbortCinematicFadeBJ()
    call DisplayCineFilter(false)
    if CampaignDialog!=null then
        call PauseTimer(CampaignClock)
        call TimerDialogDisplay(CampaignDialog,false)
    endif
    call Endless50Alliances()
    loop
        exitwhen p>=12
        if CampaignClone[p]!=null then
            call RemoveUnit(CampaignClone[p])
            set CampaignClone[p]=null
        endif
        set CampaignClonePending[p]=false
        set CampaignPermanentDead[p]=false
        set StoryRevive[p]=0.
        set StoryShopTripUntil[p]=0.
        set StoryBuyAt[p]=0.
        set CampaignDefenseLane[p]=3
        if ModuloInteger(p,3)==0 then
            set CampaignDefenseLane[p]=5
        endif
        if Hero[p]!=null then
            call PauseUnit(Hero[p],true)
            call RosterSyncPets(p)
        endif
        set p=p+1
    endloop
    set p=0
    loop
        exitwhen p>=4
        set StoryStage[p]=31
        set StoryRetreat[p]=false
        set StoryMarch[p]=true
        set StoryAdvanceAt[p]=0.
        set p=p+1
    endloop
    call EnumDestructablesInRect(bj_mapInitialPlayableArea,null,function CampaignOpenSourceGate)
    call StoryShopsOpen()
    call CampaignFountainsOpen()
    call CampaignVillageLandmarksOpen()
    call ExamBroadcast("Коноха: сюжет завершён. Все четыре команды объединяются! Подготовка общей обороны. Сарутоби — 300000 здоровья; герои возвращаются через20сек, его стража — через4мин. Поражение только при гибели Хокагэ.")
endfunction
function Endless50Guardian takes integer slot returns nothing
    local unit u=null
    local integer added=0
    if CampaignActor[slot]!=null then
        if NPCCooldowns!=null then
            call FlushChildHashtable(NPCCooldowns,GetHandleId(CampaignActor[slot]))
        endif
        if NPCHiddenAbilities!=null then
            call FlushChildHashtable(NPCHiddenAbilities,GetHandleId(CampaignActor[slot]))
        endif
        call RemoveUnit(CampaignActor[slot])
        set CampaignActor[slot]=null
    endif
    set added=CampaignAdd(Endless50Kind[slot],13,Endless50X[slot],Endless50Y[slot])
    if added>=0 then
        set u=CampaignActor[added]
        call UnitRemoveAbility(u,'Avul')
        call PauseUnit(u,false)
        set CampaignPostX[added]=Endless50X[slot]
        set CampaignPostY[added]=Endless50Y[slot]
        set Endless50ReviveAt[slot]=0.
    endif
    set u=null
endfunction
function Endless50BossSpawn takes integer kind, integer lane returns nothing
    local integer slot=CampaignAdd(kind,15,CampaignWaveSpawnX[lane*4],CampaignWaveSpawnY[lane*4])
    if slot>=0 then
        set CampaignActorRoute[slot]=CampaignWaveDestination[lane]
        call UnitRemoveAbility(CampaignActor[slot],'Avul')
        call PauseUnit(CampaignActor[slot],false)
        call IssuePointOrder(CampaignActor[slot],"attack",CampaignRouteX[CampaignActorRoute[slot]],CampaignRouteY[CampaignActorRoute[slot]])
    endif
endfunction
function Endless50Bosses takes nothing returns nothing
    set Endless50BossRound=Endless50BossRound+1
    if Endless50BossRound==1 then
        call Endless50BossSpawn(11,0)
        call Endless50BossSpawn(12,1)
        call ExamBroadcast("Разведка: Кабуто и гигантская змея идут на Коноху!")
    elseif Endless50BossRound==2 then
        call Endless50BossSpawn(4,2)
        call ExamBroadcast("Разведка: приближается Кисамэ!")
    elseif Endless50BossRound==3 then
        call Endless50BossSpawn(3,3)
        call ExamBroadcast("Разведка: Итачи начинает нападение!")
    elseif Endless50BossRound==4 then
        call Endless50BossSpawn(13,4)
        call Endless50BossSpawn(11,5)
        call Endless50BossSpawn(12,6)
        call Endless50BossSpawn(4,7)
        call ExamBroadcast("Разведка: Орочимару, Кабуто, змея и Кисамэ атакуют вместе!")
    elseif Endless50BossRound==5 then
        call Endless50BossSpawn(4,0)
        call Endless50BossSpawn(3,2)
        call ExamBroadcast("Разведка: Кисамэ и Итачи идут вместе!")
    else
        call Endless50BossSpawn(13,0)
        call Endless50BossSpawn(11,2)
        call Endless50BossSpawn(12,4)
        call Endless50BossSpawn(4,6)
        call Endless50BossSpawn(3,7)
        call ExamBroadcast("Разведка: все главные враги атакуют! Подкрепления будут повторяться каждые5минут.")
    endif
    set Endless50BossAt=TimeNow+300.
endfunction
function Endless50Lose takes nothing returns nothing
    local integer p=0
    set Endless50Active=false
    set Endless50Starting=false
    set CampaignFinished=true
    call CampaignClear()
    call NoteClearAll()
    call StoryShopsClose()
    call CampaignVillageLandmarksClose()
    call ExamBroadcast("Сарутоби пал. Бесконечная оборона Конохи завершена.")
    loop
        exitwhen p>=12
        if Hero[p]!=null and GetPlayerSlotState(Player(p))==PLAYER_SLOT_STATE_PLAYING then
            call CustomDefeatBJ(Player(p),"Сарутоби погиб. Коноха пала.")
        endif
        set p=p+1
    endloop
endfunction
function Endless50Cleanup takes nothing returns nothing
    local integer n=0
    local integer j=0
    loop
        exitwhen n>=16
        if Endless50CleanupCursor>=CampaignCount then
            set Endless50CleanupCursor=17
        endif
        exitwhen Endless50CleanupCursor>=CampaignCount
        set j=Endless50CleanupCursor
        set Endless50CleanupCursor=j+1
        if CampaignActor[j]!=null and not FoundationAlive(CampaignActor[j]) then
            if Endless50DeadSince[j]==0. then
                set Endless50DeadSince[j]=TimeNow
            elseif TimeNow>=Endless50DeadSince[j]+120. then
                if NPCCooldowns!=null then
                    call FlushChildHashtable(NPCCooldowns,GetHandleId(CampaignActor[j]))
                endif
                if NPCHiddenAbilities!=null then
                    call FlushChildHashtable(NPCHiddenAbilities,GetHandleId(CampaignActor[j]))
                endif
                call RemoveUnit(CampaignActor[j])
                set CampaignActor[j]=null
                set Endless50DeadSince[j]=0.
            endif
        else
            set Endless50DeadSince[j]=0.
        endif
        set n=n+1
    endloop
endfunction
function Endless50Heroes takes nothing returns nothing
    local integer p=0
    loop
        exitwhen p>=12
        if Hero[p]!=null and GetPlayerSlotState(Player(p))==PLAYER_SLOT_STATE_PLAYING then
            if not FoundationAlive(Hero[p]) then
                if StoryRevive[p]==0. then
                    set StoryRevive[p]=TimeNow+20.
                elseif TimeNow>=StoryRevive[p] then
                    call Endless50ReadyHero(p)
                endif
            endif
        endif
        set p=p+1
    endloop
endfunction
function Endless50Tick takes nothing returns nothing
    local integer j=0
    if CampaignStage!=31 or CampaignFinished then
        return
    endif
    if Endless50Starting then
        if Endless50Cursor<17 then
            call Endless50Guardian(Endless50Cursor)
        elseif Endless50Cursor<29 then
            call Endless50ReadyHero(Endless50Cursor-17)
        else
            set Endless50Starting=false
            set Endless50Active=true
            set CampaignTransition=false
            set CampaignStartAt=TimeNow
            set Endless50BossAt=TimeNow+300.
            set CampaignBountyActive=true
            loop
                exitwhen j>=16
                set CampaignBountyBefore[j]=GetPlayerState(Player(j),PLAYER_STATE_GIVES_BOUNTY)
                if j==13 or j==15 then
                    call SetPlayerState(Player(j),PLAYER_STATE_GIVES_BOUNTY,0)
                endif
                set j=j+1
            endloop
            set j=0
            loop
                exitwhen j>=8
                set Invasion44Wave[j]=0
                set CampaignWaveAt[j]=TimeNow+CampaignWavePeriod[j]+CampaignWaveDelay[j]
                set j=j+1
            endloop
            set MusicCursor=0
            set MusicSong=0
            set MusicPlaying=false
            set MusicActiveChapter=-1
            call ExecuteFunc("FoundationMusicStart")
            call ExamBroadcast("Все на защиту Конохи! Волны идут непрерывно. До первого выхода боссов —5минут. Все главы музыки играют по очереди.")
        endif
        set Endless50Cursor=Endless50Cursor+1
        return
    endif
    if not Endless50Active then
        return
    endif
    if not FoundationAlive(CampaignActor[0]) then
        call Endless50Lose()
        return
    endif
    call Endless50Heroes()
    set j=1
    loop
        exitwhen j>=17
        if not FoundationAlive(CampaignActor[j]) then
            if Endless50ReviveAt[j]==0. then
                set Endless50ReviveAt[j]=TimeNow+240.
            elseif TimeNow>=Endless50ReviveAt[j] then
                call Endless50Guardian(j)
            endif
        endif
        set j=j+1
    endloop
    set j=0
    loop
        exitwhen j>=8
        if TimeNow>=CampaignWaveAt[j] then
            set CampaignWaveAt[j]=TimeNow+CampaignWavePeriod[j]
            call CampaignInvasionWave(j)
        endif
        set j=j+1
    endloop
    if TimeNow>=Endless50BossAt then
        call Endless50Bosses()
    endif
    call Endless50Cleanup()
    if TimeNow>=Endless50ThinkAt then
        set Endless50ThinkAt=TimeNow+.5
        call ExecuteFunc("CampaignNPCTick")
    endif
endfunction
