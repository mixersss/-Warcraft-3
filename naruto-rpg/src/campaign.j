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
            call SetPlayerAllianceStateVisionBJ(Player(p),Player(q),allied)
            set q=q+1
        endloop
        if mode==2 then
            call SetPlayerAllianceStateAllyBJ(Player(PLAYER_NEUTRAL_PASSIVE),Player(p),HeroRole[p]>=9)
            call SetPlayerAllianceStateAllyBJ(Player(p),Player(PLAYER_NEUTRAL_PASSIVE),HeroRole[p]>=9)
        else
            call SetPlayerAllianceStateAllyBJ(Player(PLAYER_NEUTRAL_PASSIVE),Player(p),true)
            call SetPlayerAllianceStateAllyBJ(Player(p),Player(PLAYER_NEUTRAL_PASSIVE),true)
        endif
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
function CampaignClear takes nothing returns nothing
    local integer j=0
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
    if Hero[p]!=null then
        call CommonLogClear(p)
        call RosterReset(p)
        if not FoundationAlive(Hero[p]) and not CampaignPermanentDead[p] then
            call ReviveHero(Hero[p],CampaignX[CampaignStage],CampaignY[CampaignStage],false)
        endif
        call UnitAddAbility(Hero[p],'Avul')
        call PauseUnit(Hero[p],true)
        call IssueImmediateOrder(Hero[p],"stop")
        call SetUnitPosition(Hero[p],CampaignX[CampaignStage]+I2R(ModuloInteger(p,3))*64.,CampaignY[CampaignStage]+300.+I2R(StoryTeam(p))*64.)
    endif
endfunction
function CampaignDuelNext takes nothing returns nothing
    local integer p=0
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
    call SetUnitPosition(Hero[CampaignDuelA],CampaignTX[CampaignStage]-220.,CampaignTY[CampaignStage])
    call SetUnitPosition(Hero[CampaignDuelB],CampaignTX[CampaignStage]+220.,CampaignTY[CampaignStage])
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
    set CampaignDuelAt=TimeNow+5.
    set CampaignDuelLive=false
    call ExamBroadcast("Экзаменатор: Команда "+I2S(StoryTeam(CampaignDuelA)+1)+" — "+HeroName[HeroRole[CampaignDuelA]]+" против "+HeroName[HeroRole[CampaignDuelB]]+"! Начало через 5 секунд. Поражение не удаляет героя из истории.")
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
            call RosterReset(p)
            call SkillsClearSharingan(p)
            set ComboLeft[p]=0
            set ComboTarget[p]=null
            set ResumeAt[p]=0.
            if not FoundationAlive(Hero[p]) then
                call ReviveHero(Hero[p],CampaignX[CampaignStage],CampaignY[CampaignStage],false)
            endif
            set x=CampaignX[CampaignStage]+I2R(ModuloInteger(p,3)-1)*48.
            set y=CampaignY[CampaignStage]+I2R(StoryTeam(p))*48.
            call SetUnitPosition(Hero[p],x,y)
            set SpawnX[p]=GetUnitX(Hero[p])
            set SpawnY[p]=GetUnitY(Hero[p])
            call SetWidgetLife(Hero[p],GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE))
            call SetUnitState(Hero[p],UNIT_STATE_MANA,GetUnitState(Hero[p],UNIT_STATE_MAX_MANA))
            call UnitAddAbility(Hero[p],'Avul')
            call PauseUnit(Hero[p],true)
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
function CampaignSpawnStage takes nothing returns nothing
    local integer n=CampaignStage
    local integer j=0
    local integer k=0
    local integer owner=PLAYER_NEUTRAL_AGGRESSIVE
    local integer unused=0
    local item reward=null
    local real x=CampaignTX[n]
    local real y=CampaignTY[n]
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
        call CampaignQueueBuild(false)
        call CampaignDuelNext()
    elseif n==10 then
        set CampaignJiraiya=GetRandomInt(0,19)
        set CampaignFound=false
        loop
            exitwhen j>=20
            set unused=CampaignAdd(18,PLAYER_NEUTRAL_AGGRESSIVE,CampaignBarrelX[j],CampaignBarrelY[j])
            set j=j+1
        endloop
        call ExamBroadcast("Наруто: Разбивайте бочки! У нас 150 секунд. -quest отмечает ближайшую; боты помогут искать, если дать -go.")
    elseif n==12 then
        set owner=CampaignLeader
        if HeroRole[owner]>=9 then
            set owner=PLAYER_NEUTRAL_AGGRESSIVE
        endif
        set CampaignDefenseOwner=owner
        set unused=CampaignAdd(0,owner,x,y)
        set CampaignDeployCursor=0
        call StoryShopsOpen()
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
            set CampaignWaveAt[j]=TimeNow+45.
            if j==1 or j==4 then
                set CampaignWaveAt[j]=CampaignWaveAt[j]+15.
            elseif j==2 then
                set CampaignWaveAt[j]=CampaignWaveAt[j]+30.
            endif
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
        set unused=CampaignAdd(6,PLAYER_NEUTRAL_PASSIVE,-2337.9,-12081.0)
        call SetUnitFacing(CampaignActor[unused],0.0)
        set unused=CampaignAdd(7,PLAYER_NEUTRAL_PASSIVE,5191.3,-2715.4)
        call SetUnitFacing(CampaignActor[unused],270.0)
        set unused=CampaignAdd(8,PLAYER_NEUTRAL_PASSIVE,4963.6,-2733.3)
        call SetUnitFacing(CampaignActor[unused],270.0)
        set unused=CampaignAdd(9,PLAYER_NEUTRAL_PASSIVE,-2340.7,-11625.9)
        call SetUnitFacing(CampaignActor[unused],0.0)
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
function CampaignStartPlay takes nothing returns nothing
    local integer p=0
    local integer j=0
    set CampaignTransition=false
    set CampaignStartAt=TimeNow
    if CampaignStage==9 or CampaignStage==11 then
        set CampaignDuelAt=TimeNow+5.
    endif
    if CampaignStage==12 then
        set j=0
        loop
            exitwhen j>=8
            set CampaignWaveAt[j]=TimeNow+45.
            if j==1 or j==4 then
                set CampaignWaveAt[j]=CampaignWaveAt[j]+15.
            elseif j==2 then
                set CampaignWaveAt[j]=CampaignWaveAt[j]+30.
            endif
            set j=j+1
        endloop
        set CampaignJiraiyaAt=TimeNow+760.
        set CampaignKabutoAt=TimeNow+400.
        set CampaignSnakeAt=TimeNow+820.
        set CampaignOroAt=TimeNow+1160.
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
            elseif CampaignStage==16 and p!=CampaignSasukePlayer and p!=CampaignNarutoPlayer then
                call PauseUnit(Hero[p],true)
            else
                call PauseUnit(Hero[p],false)
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
            call PanCameraToTimedForPlayer(Player(p),GetUnitX(Hero[p]),GetUnitY(Hero[p]),1.)
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
function CampaignDuelTick takes nothing returns nothing
    local integer winner=-1
    local integer loser=-1
    local item reward=null
    if CampaignDuelA<0 then
        if CampaignQueueCursor<CampaignQueueCount then
            call CampaignDuelNext()
        elseif CampaignBracket and CampaignWinnerCount>1 then
            call CampaignQueueBuild(true)
            call CampaignDuelNext()
        else
            if CampaignBracket and CampaignWinnerCount==1 then
                set winner=CampaignWinner[0]
                set CampaignChampion=winner
                call ExamBroadcast("Экзаменатор: Победитель — "+HeroName[HeroRole[winner]]+"! Снаряжение чунина выдадут в деревне.")
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
            call PauseUnit(Hero[CampaignDuelB],false)
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
        set CampaignWinner[CampaignWinnerCount]=winner
        set CampaignWinnerCount=CampaignWinnerCount+1
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
        if p==CampaignDuelA and CampaignDuelLive then
            return Hero[CampaignDuelB]
        elseif p==CampaignDuelB and CampaignDuelLive then
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
            if FoundationAlive(target) and GetUnitAbilityLevel(target,'Avul')==0 and not IsUnitPaused(target) and IsUnitEnemy(target,Player(p)) then
                set dx=GetUnitX(target)-GetUnitX(Hero[p])
                set dy=GetUnitY(target)-GetUnitY(Hero[p])
                if dx*dx+dy*dy<best then
                    set result=target
                    set best=dx*dx+dy*dy
                endif
            endif
        endloop
        if result==null and FoundationAlive(CampaignActor[0]) and IsUnitEnemy(CampaignActor[0],Player(p)) then
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
    if shop!=null and TimeNow>=StoryBuyAt[p] and StoryShopTripUntil[p]==0. and GetWidgetLife(Hero[p])>GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.45 then
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
    elseif not StoryMarch[t] and leader!=Hero[p] and leader!=null then
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
            set best=1100.*1100.
            call GroupEnumUnitsInRange(CampaignScratch,GetUnitX(u),GetUnitY(u),1100.,null)
            loop
                set candidate=FirstOfGroup(CampaignScratch)
                exitwhen candidate==null
                call GroupRemoveUnit(CampaignScratch,candidate)
                if FoundationAlive(candidate) and GetUnitAbilityLevel(candidate,'Avul')==0 and not IsUnitPaused(candidate) and not IsUnitHidden(candidate) and ((CampaignActorType[j]==32 and IsUnitAlly(candidate,GetOwningPlayer(u)) and GetWidgetLife(candidate)<GetUnitState(candidate,UNIT_STATE_MAX_LIFE)*.9) or (CampaignActorType[j]!=32 and IsUnitEnemy(candidate,GetOwningPlayer(u)))) then
                    set dx=GetUnitX(candidate)-GetUnitX(u)
                    set dy=GetUnitY(candidate)-GetUnitY(u)
                    if dx*dx+dy*dy<best then
                        set target=candidate
                        set best=dx*dx+dy*dy
                    endif
                endif
            endloop
            if target!=null then
                if NPCUseInventory(u,CampaignActorType[j],target) or NPCTry(u,CampaignActorType[j],target) then
                    set CampaignMoveAt[j]=TimeNow+1.
                elseif TimeNow>=CampaignMoveAt[j] then
                    if CampaignActorType[j]==32 then
                        call IssueTargetOrder(u,"follow",target)
                    else
                        call IssueTargetOrder(u,"attack",target)
                    endif
                    set CampaignMoveAt[j]=TimeNow+3.
                endif
            elseif CampaignStage==12 and CampaignActorRoute[j]>=0 and TimeNow>=CampaignMoveAt[j] then
                if ExamNear(u,CampaignRouteX[CampaignActorRoute[j]],CampaignRouteY[CampaignActorRoute[j]],220.) then
                    set CampaignActorRoute[j]=11
                endif
                call IssuePointOrder(u,"attack",CampaignRouteX[CampaignActorRoute[j]],CampaignRouteY[CampaignActorRoute[j]])
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
            call SetUnitColor(CampaignActor[slot],ConvertPlayerColor(12))
        else
            set j=j-140
            set slot=CampaignAdd(34,CampaignDefenseOwner,CampaignAnbuX[j],CampaignAnbuY[j])
            call SetUnitFacing(CampaignActor[slot],CampaignAnbuFacing[j])
            call SetUnitColor(CampaignActor[slot],ConvertPlayerColor(12))
        endif
        set CampaignDeployCursor=CampaignDeployCursor+1
        set processed=processed+1
    endloop
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
        loop
            exitwhen p>=12
            if Hero[p]!=null then
                set CampaignLeader=p
                exitwhen true
            endif
            set p=p+1
        endloop
        call CampaignBindRoles()
        call CampaignCamerasInit()
        set CampaignScratch=CreateGroup()
        set CampaignClock=CreateTimer()
        set CampaignDialog=CreateTimerDialog(CampaignClock)
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
    if TimeNow>=CampaignNextBot then
        call CampaignNPCTick()
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
        if CampaignJiraiyaAt>0. and TimeNow>=CampaignJiraiyaAt then
            set unused=CampaignAdd(33,CampaignLeader,CampaignSupportX[6],CampaignSupportY[6])
            set CampaignJiraiyaAt=0.
            call ExamBroadcast("Джирайя: Я здесь! Помогу защитить деревню.")
        endif
        if CampaignKabutoAt>0. and TimeNow>=CampaignKabutoAt then
            set owner=PLAYER_NEUTRAL_AGGRESSIVE
            set unused=CampaignAdd(11,CampaignAttackerOwner[1],CampaignSupportX[5],CampaignSupportY[5])
            set CampaignVillageKabuto=CampaignActor[unused]
            set CampaignKabutoAt=0.
            call ExamBroadcast("Канкуро: Кабуто прибыл на помощь нападающим!")
        endif
        if CampaignSnakeAt>0. and TimeNow>=CampaignSnakeAt then
            set unused=CampaignAdd(36,CampaignAttackerOwner[2],CampaignSupportX[5],CampaignSupportY[5])
            set CampaignVillageSnake=CampaignActor[unused]
            set CampaignSnakeGoneAt=TimeNow+300.
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
        if CampaignOroAt>0. and TimeNow>=CampaignOroAt then
            call SetUnitOwner(CampaignVillageOro,Player(CampaignAttackOwner),true)
            call PauseUnit(CampaignVillageOro,false)
            set CampaignOroAt=0.
            call ExamBroadcast("Орочимару: Теперь я лично разберусь с Хокагэ!")
        endif
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
                set origin=0
                set destination=1
                set waveKind=16
                if lane==1 then
                    set destination=2
                elseif lane==2 then
                    set destination=3
                elseif lane==3 or lane==4 then
                    set origin=4
                    set destination=5
                    set waveKind=15
                    if lane==4 then
                        set destination=6
                    endif
                elseif lane==5 then
                    set origin=7
                    set destination=8
                elseif lane==6 then
                    set origin=9
                    set destination=8
                    set waveKind=15
                elseif lane==7 then
                    set origin=10
                    set destination=8
                    set waveKind=15
                endif
                if lane==0 or lane==3 or lane==5 then
                    set owner=CampaignAttackerOwner[0]
                elseif lane==1 or lane==4 or lane==6 then
                    set owner=CampaignAttackerOwner[1]
                else
                    set owner=CampaignAttackerOwner[2]
                endif
                set k=0
                loop
                    exitwhen k>=3
                    set unused=CampaignAdd(waveKind,owner,CampaignRouteX[origin]+I2R(k)*24.,CampaignRouteY[origin])
                    if unused>=0 then
                        set CampaignActorRoute[unused]=destination
                        call IssuePointOrder(CampaignActor[unused],"attack",CampaignRouteX[destination],CampaignRouteY[destination])
                    endif
                    set k=k+1
                endloop
                set CampaignWaveAt[lane]=CampaignWaveAt[lane]+45.
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
