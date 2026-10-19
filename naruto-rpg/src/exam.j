// New chapter implementation: shared bounded state, original scenery, no per-unit timers.
function ExamBroadcast takes string text returns nothing
    local integer t=0
    loop
        exitwhen t>=4
        if StoryMembers[t]>0 then
            call StorySay(t,text)
        endif
        set t=t+1
    endloop
endfunction
function ExamNear takes unit u, real x, real y, real radius returns boolean
    local real dx=GetUnitX(u)-x
    local real dy=GetUnitY(u)-y
    return dx*dx+dy*dy<=radius*radius
endfunction
function ExamHas takes integer t, integer raw returns boolean
    local integer p=t*3
    local integer k=0
    loop
        exitwhen p>=t*3+3
        if FoundationAlive(Hero[p]) then
            set k=0
            loop
                exitwhen k>=6
                if GetItemTypeId(UnitItemInSlot(Hero[p],k))==raw then
                    return true
                endif
                set k=k+1
            endloop
        endif
        set p=p+1
    endloop
    return false
endfunction
function ExamPair takes integer t returns boolean
    return ExamHas(t,'Eshe') and ExamHas(t,'Esea')
endfunction
function ExamNearest takes integer p returns unit
    local integer j=0
    local integer t=StoryTeam(p)
    local integer raw=0
    local real best=999999999.
    local real dx=0.
    local real dy=0.
    local real d=0.
    local unit result=null
    local boolean hasHeaven=ExamHas(t,'Eshe')
    local boolean hasEarth=ExamHas(t,'Esea')
    loop
        exitwhen j>=85
        set raw='Eshe'
        if ModuloInteger(j,2)==1 then
            set raw='Esea'
        endif
        if FoundationAlive(ExamEnemy[j]) and not IsUnitHidden(ExamEnemy[j]) and (ExamEnemy[j]!=ExamBotAvoidUnit[p] or TimeNow>=ExamBotAvoidUntil[p]) then
            set dx=GetUnitX(ExamEnemy[j])-GetUnitX(Hero[p])
            set dy=GetUnitY(ExamEnemy[j])-GetUnitY(Hero[p])
            set d=dx*dx+dy*dy
            // Prefer carriers of the missing scroll without ignoring nearby threats.
            if (raw=='Eshe' and not hasHeaven) or (raw=='Esea' and not hasEarth) then
                set d=d*.35
            endif
            if d<best then
                set best=d
                set result=ExamEnemy[j]
            endif
        endif
        set j=j+1
    endloop
    return result
endfunction
function ExamClearGate takes nothing returns nothing
    local destructable d=GetEnumDestructable()
    if GetDestructableTypeId(d)=='YTpb' then
        call RemoveDestructable(d)
    endif
    set d=null
endfunction
function ExamFinishTeam takes integer t, boolean passed returns nothing
    local integer p=t*3
    local integer k=0
    local item it=null
    if StoryStage[t]!=7 then
        return
    endif
    set StoryStage[t]=8
    if passed then
        loop
            exitwhen p>=t*3+3
            set k=0
            loop
                exitwhen k>=6
                set it=UnitItemInSlot(Hero[p],k)
                if GetItemTypeId(it)=='Eshe' or GetItemTypeId(it)=='Esea' then
                    call RemoveItem(it)
                endif
                set k=k+1
            endloop
            if Hero[p]!=null then
                call SetHeroLevel(Hero[p],IMinBJ(60,GetHeroLevel(Hero[p])+2),true)
            endif
            set p=p+1
        endloop
        call StoryReward(t,350,0)
        call StorySay(t,"Анко: Оба свитка доставлены! Отряд проходит испытание и получает каждому 2 уровня и 350 золота. Далее — предварительные бои.")
    else
        call StorySay(t,"Анко: Время истекло. Свитки не доставлены; награды нет. Экзамен завершён, ожидайте предварительных боёв.")
    endif
    set p=t*3
    loop
        exitwhen p>=t*3+3
        if FoundationAlive(Hero[p]) then
            call IssueImmediateOrder(Hero[p],"stop")
            call UnitAddAbility(Hero[p],'Avul')
            call PauseUnit(Hero[p],true)
        endif
        set p=p+1
    endloop
    set it=null
endfunction
function ExamClockEnd takes nothing returns nothing
    // Progression is handled by the shared heartbeat, including load/revival states.
endfunction
function ExamStartForest takes nothing returns nothing
    local integer t=0
    local integer p=0
    local integer k=0
    local unit u=null
    set ExamPhase=3
    if ExamAnswers!=null then
        call DestroyTrigger(ExamAnswers)
        set ExamAnswers=null
    endif
    set ExamOpenAt=TimeNow+1200.
    set ExamEndAt=TimeNow+1320.
    set ExamPopulateCursor=0
    set ExamRepopulateAt=TimeNow+8.
    set ExamFountain[0]=CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'refn',-4608.,-15232.,270.)
    set ExamFountain[1]=CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'refn',-15616.,-4224.,270.)
    set ExamRect=Rect(-16384.,-16384.,-3776.,-3296.)
    set ExamTower=CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'rean',ExamTowerX,ExamTowerY,270.)
    call PauseUnit(ExamTower,true)
    set MusicCursor=2
    call FoundationMusicStart()
    set ExamClock=CreateTimer()
    call TimerStart(ExamClock,1320.,false,function ExamClockEnd)
    set ExamDialog=CreateTimerDialog(ExamClock)
    call TimerDialogSetTitle(ExamDialog,"Лес смерти: до конца")
    call TimerDialogDisplay(ExamDialog,true)
    loop
        exitwhen t>=4
        if StoryMembers[t]>0 then
            set StoryStage[t]=7
            set StoryRetreat[t]=false
            set StoryMarch[t]=true
            call SetUnitPosition(StoryShop[t],ExamSpawnX[t]+128.,ExamSpawnY[t])
            set p=t*3
            loop
                exitwhen p>=t*3+3
                if Hero[p]!=null then
                    set ExamBotProgressAt[p]=TimeNow
                    set ExamBotAvoidUnit[p]=null
                    set ExamBotAvoidItem[p]=null
                    set ExamBotGoalItem[p]=null
                    set ExamBotItemAvoidUntil[p]=0.
                    set ExamBotAvoidUntil[p]=0.
                    set ExamBotPatrol[p]=0
                    call PauseUnit(Hero[p],false)
                    call UnitRemoveAbility(Hero[p],'Avul')
                    if not FoundationAlive(Hero[p]) then
                        call ReviveHero(Hero[p],ExamSpawnX[t],ExamSpawnY[t],false)
                    endif
                    call SetUnitPosition(Hero[p],ExamSpawnX[t],ExamSpawnY[t])
                    set SpawnX[p]=GetUnitX(Hero[p])
                    set SpawnY[p]=GetUnitY(Hero[p])
                    set ExamBotLastX[p]=SpawnX[p]
                    set ExamBotLastY[p]=SpawnY[p]
                    call SetWidgetLife(Hero[p],GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE))
                    call SetUnitState(Hero[p],UNIT_STATE_MANA,GetUnitState(Hero[p],UNIT_STATE_MAX_MANA))
                    call PanCameraToTimedForPlayer(Player(p),SpawnX[p],SpawnY[p],1.)
                    set k=0
                    loop
                        exitwhen k>=3
                        set u=Companion[p*3+k]
                        if FoundationAlive(u) then
                            call SetUnitPosition(u,SpawnX[p],SpawnY[p])
                        endif
                        set k=k+1
                    endloop
                endif
                set p=p+1
            endloop
            // Real quest item on the ground; inventory/ownership, not a checkpoint flag.
            if GetRandomInt(0,1)==0 then
                set ExamScroll[85+t]=CreateItem('Eshe',ExamSpawnX[t],ExamSpawnY[t])
            else
                set ExamScroll[85+t]=CreateItem('Esea',ExamSpawnX[t],ExamSpawnY[t])
            endif
        endif
        set t=t+1
    endloop
    call ExamBroadcast("Анко: Добро пожаловать в Лес смерти! У входа лежит свиток вашего отряда. Второй тип найдите у вражеских генинов. Нужны Небо и Земля. До конца 22 минуты; башня открывается на последние две. Свитки могут нести разные союзники, но оба должны подойти к башне. -quest: задача, -go/-follow: команды, -shop: снабжение.")
    set u=null
endfunction
// Fixed per-player progress state; no timers, random teleport or extra units.
function ExamBotProgress takes integer p, unit enemy returns nothing
    local real dx=GetUnitX(Hero[p])-ExamBotLastX[p]
    local real dy=GetUnitY(Hero[p])-ExamBotLastY[p]
    local item it=ExamBotGoalItem[p]
    if dx*dx+dy*dy>64.*64. then
        set ExamBotProgressAt[p]=TimeNow
        set ExamBotLastX[p]=GetUnitX(Hero[p])
        set ExamBotLastY[p]=GetUnitY(Hero[p])
    elseif TimeNow>=ExamBotProgressAt[p]+8. then
        // Do not interrupt a stationary melee/ranged battle or nearby item pickup.
        if it==null and enemy!=null and not ExamNear(enemy,GetUnitX(Hero[p]),GetUnitY(Hero[p]),700.) then
            set ExamBotAvoidUnit[p]=enemy
            set ExamBotAvoidUntil[p]=TimeNow+20.
        endif
        if it!=null and not IsItemOwned(it) and not ExamNear(Hero[p],GetItemX(it),GetItemY(it),160.) then
            set ExamBotAvoidItem[p]=it
            set ExamBotItemAvoidUntil[p]=TimeNow+20.
        else
            set ExamBotGoalItem[p]=null
        endif
        set ExamBotPatrol[p]=ModuloInteger(ExamBotPatrol[p]+1,85)
        set ExamBotProgressAt[p]=TimeNow
    endif
    set it=null
endfunction
function ExamBotPatrolOrder takes integer p returns nothing
    local integer tries=0
    local integer node=0
    loop
        set node=ModuloInteger(p*7+ExamBotPatrol[p]*11,85)
        exitwhen tries>=85 or (not IsTerrainPathable(ExamEnemyX[node],ExamEnemyY[node],PATHING_TYPE_WALKABILITY) and not ExamNear(Hero[p],ExamEnemyX[node],ExamEnemyY[node],200.))
        set ExamBotPatrol[p]=ModuloInteger(ExamBotPatrol[p]+1,85)
        set tries=tries+1
    endloop
    if tries<85 then
        call IssuePointOrder(Hero[p],"attack",ExamEnemyX[node],ExamEnemyY[node])
    endif
endfunction
function ExamBot takes integer p, unit enemy returns nothing
    local integer t=StoryTeam(p)
    local integer j=0
    local integer k=0
    local integer free=0
    local integer raw=0
    local real best=999999999.
    local real dx=0.
    local real dy=0.
    local item found=null
    local item it=null
    local unit leader=StoryLeader(t)
    local boolean hasHeaven=ExamHas(t,'Eshe')
    local boolean hasEarth=ExamHas(t,'Esea')
    call ExamBotProgress(p,enemy)
    set ExamBotGoalItem[p]=null
    if enemy==ExamBotAvoidUnit[p] and TimeNow<ExamBotAvoidUntil[p] then
        set enemy=ExamNearest(p)
    endif
    if StoryRetreat[t] or GetWidgetLife(Hero[p])<GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.2 then
        call IssuePointOrder(Hero[p],"move",SpawnX[p],SpawnY[p])
        return
    endif
    if ExamTowerOpen and ExamPair(t) then
        call IssuePointOrder(Hero[p],"move",ExamTowerX,ExamTowerY)
        return
    endif
    loop
        exitwhen j>=ExamScrollCount
        set it=ExamScroll[j]
        set raw=GetItemTypeId(it)
        if it!=null and not IsItemOwned(it) and GetWidgetLife(it)>.405 and (it!=ExamBotAvoidItem[p] or TimeNow>=ExamBotItemAvoidUntil[p]) and ((raw=='Eshe' and not hasHeaven) or (raw=='Esea' and not hasEarth)) then
            set dx=GetItemX(it)-GetUnitX(Hero[p])
            set dy=GetItemY(it)-GetUnitY(Hero[p])
            if dx*dx+dy*dy<best then
                set best=dx*dx+dy*dy
                set found=it
            endif
        endif
        set j=j+1
    endloop
    if found!=null and (enemy==null or best<900.*900.) then
        set k=0
        loop
            exitwhen k>=6
            if UnitItemInSlot(Hero[p],k)==null then
                set free=free+1
            endif
            set k=k+1
        endloop
        if free==0 then
            // Make one slot by dropping non-quest gear, never destroy equipment.
            set k=5
            loop
                exitwhen k<0 or free>0
                set it=UnitItemInSlot(Hero[p],k)
                set raw=GetItemTypeId(it)
                if it!=null and raw!='Eshe' and raw!='Esea' then
                    call UnitRemoveItem(Hero[p],it)
                    call SetItemPosition(it,GetUnitX(Hero[p]),GetUnitY(Hero[p]))
                    set free=1
                endif
                set k=k-1
            endloop
        endif
        if free>0 then
            set ExamBotGoalItem[p]=found
            call IssueTargetOrder(Hero[p],"smart",found)
        elseif enemy!=null then
            call IssueTargetOrder(Hero[p],"attack",enemy)
        endif
    elseif StoryMarch[t] and ExamPair(t) and not ExamTowerOpen then
        set j=0
        set found=null
        set best=650.*650.
        loop
            exitwhen j>=ExamGearCount
            set it=ExamGear[j]
            if it!=null and GetItemTypeId(it)!=0 and not IsItemOwned(it) and (it!=ExamBotAvoidItem[p] or TimeNow>=ExamBotItemAvoidUntil[p]) then
                set dx=GetItemX(it)-GetUnitX(Hero[p])
                set dy=GetItemY(it)-GetUnitY(Hero[p])
                if dx*dx+dy*dy<best then
                    set best=dx*dx+dy*dy
                    set found=it
                endif
            endif
            set j=j+1
        endloop
        set k=0
        set free=0
        loop
            exitwhen k>=6
            if UnitItemInSlot(Hero[p],k)==null then
                set free=free+1
            endif
            set k=k+1
        endloop
        if found!=null and free>0 then
            set ExamBotGoalItem[p]=found
            call IssueTargetOrder(Hero[p],"smart",found)
        elseif enemy!=null then
            call IssueTargetOrder(Hero[p],"attack",enemy)
        else
            call ExamBotPatrolOrder(p)
        endif
    elseif not StoryMarch[t] and leader!=null and leader!=Hero[p] then
        if enemy!=null and ExamNear(enemy,GetUnitX(Hero[p]),GetUnitY(Hero[p]),700.) then
            call IssueTargetOrder(Hero[p],"attack",enemy)
        else
            call IssueTargetOrder(Hero[p],"follow",leader)
        endif
    elseif enemy!=null then
        call IssueTargetOrder(Hero[p],"attack",enemy)
    else
        call ExamBotPatrolOrder(p)
    endif
    set found=null
    set it=null
    set leader=null
endfunction
function ExamRespawn takes integer raw returns unit
    local integer attempts=0
    local integer point=0
    local real x=0.
    local real y=0.
    loop
        set x=GetRandomReal(-16352.,-3808.)
        set y=GetRandomReal(-16352.,-3328.)
        exitwhen not IsTerrainPathable(x,y,PATHING_TYPE_WALKABILITY) or attempts>=24
        set attempts=attempts+1
    endloop
    if attempts>=24 then
        set point=GetRandomInt(0,84)
        set x=ExamEnemyX[point]
        set y=ExamEnemyY[point]
    endif
    return CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),raw,x,y,GetRandomReal(0.,360.))
endfunction
function ExamForestTick takes nothing returns nothing
    local integer count=0
    local integer j=0
    local integer t=0
    local integer p=0
    local integer k=0
    local integer raw=0
    local boolean heaven=false
    local boolean earth=false
    local boolean active=false
    local item it=null
    local unit target=null
    local real best=0.
    local real dx=0.
    local real dy=0.
    // Stagger native unit creation: one actor per shared tick (85 actors total).
    if ExamPopulateCursor<85 then
        set j=ExamPopulateCursor
        set raw=ExamEnemyType[j]
        set ExamEnemy[j]=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),raw,ExamEnemyX[j],ExamEnemyY[j],180.)
        call SetUnitCreepGuard(ExamEnemy[j],false)
        call RemoveGuardPosition(ExamEnemy[j])
        set ExamPopulateCursor=j+1
    endif
    if not ExamTowerOpen and TimeNow>=ExamOpenAt then
        set ExamTowerOpen=true
        call EnumDestructablesInRect(ExamRect,null,function ExamClearGate)
        call ExamBroadcast("Анко: Башня открыта! Осталось две минуты. Принесите один комплект Небо + Земля на команду. Оба носителя должны быть рядом с башней. -quest: её отметка.")
    endif
    set j=0
    loop
        exitwhen j>=ExamPopulateCursor
        if FoundationAlive(ExamEnemy[j]) then
            set target=null
            set best=950.*950.
            set p=0
            loop
                exitwhen p>=12
                if StoryStage[StoryTeam(p)]==7 and FoundationAlive(Hero[p]) then
                    set dx=GetUnitX(Hero[p])-GetUnitX(ExamEnemy[j])
                    set dy=GetUnitY(Hero[p])-GetUnitY(ExamEnemy[j])
                    if dx*dx+dy*dy<best then
                        set best=dx*dx+dy*dy
                        set target=Hero[p]
                    endif
                endif
                set p=p+1
            endloop
            if target!=null then
                if not ExamEngaged[j] and best<600.*600. then
                    set ExamEngaged[j]=true
                    if ExamEnemyType[j]=='re06' and GetRandomInt(0,100)<=20 then
                        call UnitAddAbility(ExamEnemy[j],'Aens')
                    endif
                endif
                if TimeNow>=ExamEnemyCastAt[j] and best<600.*600. and GetUnitAbilityLevel(ExamEnemy[j],'Aens')>0 and GetUnitState(ExamEnemy[j],UNIT_STATE_MANA)>=75. then
                    if IssueTargetOrder(ExamEnemy[j],"ensnare",target) then
                        call SetUnitAnimationByIndex(ExamEnemy[j],4+ModuloInteger(j,2))
                        set ExamEnemyCastAt[j]=TimeNow+12.
                    endif
                elseif GetUnitCurrentOrder(ExamEnemy[j])==0 then
                    call IssueTargetOrder(ExamEnemy[j],"attack",target)
                endif
            endif
        elseif ExamEnemy[j]!=null and not ExamDropped[j] then
            set ExamDropped[j]=true
            // Source Z0X: 49% total loot; 2% Heaven + 2% Earth, no guaranteed scroll.
            set raw=GetRandomInt(1,100)
            if raw<=2 then
                set raw='Nsch'
            elseif raw<=4 then
                set raw='Nsht'
            elseif raw<=6 then
                set raw='Nsta'
            elseif raw<=11 or raw==25 then
                set raw='Nnot'
            elseif raw<=18 then
                set raw='Nlra'
            elseif raw<=24 then
                set raw='Nlsh'
            elseif raw<=32 then
                set raw='Nlku'
            elseif raw<=37 then
                set raw='Nlpi'
            elseif raw<=39 then
                set raw='Nlga'
            elseif raw<=41 then
                set raw='Eshe'
            elseif raw<=47 then
                set raw='Nlne'
            elseif raw<=49 then
                set raw='Esea'
            else
                set raw=0
            endif
            if raw!=0 then
                set it=CreateItem(raw,GetUnitX(ExamEnemy[j]),GetUnitY(ExamEnemy[j]))
                if (raw=='Eshe' or raw=='Esea') and ExamScrollCount<8191 then
                    set ExamScroll[ExamScrollCount]=it
                    set ExamScrollCount=ExamScrollCount+1
                elseif ExamGearCount<8191 then
                    set ExamGear[ExamGearCount]=it
                    set ExamGearCount=ExamGearCount+1
                endif
                set it=null
            endif
            if GetRandomInt(1,100)>32 then
                set ExamRespawnAt[j]=TimeNow+1.
            endif
        endif
        if ExamRespawnAt[j]>0. and TimeNow>=ExamRespawnAt[j] then
            if ExamEnemy[j]!=null then
                call RemoveUnit(ExamEnemy[j])
            endif
            if ExamRespawnType[j]!=0 then
                set ExamEnemyType[j]=ExamRespawnType[j]
                set ExamRespawnType[j]=0
            endif
            set ExamEnemy[j]=ExamRespawn(ExamEnemyType[j])
            call SetUnitCreepGuard(ExamEnemy[j],false)
            call RemoveGuardPosition(ExamEnemy[j])
            set ExamRespawnAt[j]=0.
            set ExamDropped[j]=false
            set ExamEngaged[j]=false
        endif
        set j=j+1
    endloop
    if TimeNow>=ExamRepopulateAt and ExamPopulateCursor>=85 then
        set count=0
        set j=0
        loop
            exitwhen j>=85
            if FoundationAlive(ExamEnemy[j]) then
                set count=count+1
            endif
            set j=j+1
        endloop
        if count<=25 then
            set j=0
            set k=0
            loop
                exitwhen j>=85 or k>=8
                if not FoundationAlive(ExamEnemy[j]) and ExamRespawnAt[j]==0. then
                    set ExamRespawnAt[j]=TimeNow+1.
                    set ExamRespawnType[j]='re06'
                    if k<3 then
                        set ExamRespawnType[j]='re07'
                    endif
                    set k=k+1
                endif
                set j=j+1
            endloop
        endif
        set ExamRepopulateAt=TimeNow+8.
    endif
    loop
        exitwhen t>=4
        if StoryStage[t]==7 then
            set active=true
            set heaven=false
            set earth=false
            set p=t*3
            loop
                exitwhen p>=t*3+3
                if FoundationAlive(Hero[p]) and ExamNear(Hero[p],ExamTowerX,ExamTowerY,600.) then
                    set k=0
                    loop
                        exitwhen k>=6
                        set it=UnitItemInSlot(Hero[p],k)
                        if GetItemTypeId(it)=='Eshe' then
                            set heaven=true
                        elseif GetItemTypeId(it)=='Esea' then
                            set earth=true
                        endif
                        set k=k+1
                    endloop
                endif
                set p=p+1
            endloop
            if ExamTowerOpen and heaven and earth then
                call ExamFinishTeam(t,true)
            elseif TimeNow>=ExamEndAt then
                call ExamFinishTeam(t,false)
            endif
        endif
        set t=t+1
    endloop
    if not active then
        call TimerDialogDisplay(ExamDialog,false)
        call DestroyTimerDialog(ExamDialog)
        call PauseTimer(ExamClock)
        call DestroyTimer(ExamClock)
        call RemoveRect(ExamRect)
        set ExamDialog=null
        set ExamClock=null
        set ExamRect=null
        set ExamPhase=4
        call ExamBroadcast("Ибики: Экзамен завершён. Следующая глава — предварительные поединки — будет добавлена следующим блоком.")
    endif
    set it=null
    set target=null
endfunction
function ExamAnswer takes integer p, integer choice returns nothing
    if ExamPhase!=2 or ExamAsked<1 or StoryStage[StoryTeam(p)]!=6 or ExamAnswered[p] or TimeNow>=ExamNextAt or choice<1 or choice>4 or Hero[p]==null then
        return
    endif
    set ExamAnswered[p]=true
    if choice==ExamCorrect[ExamQuestion] then
        set ExamScore[p]=ExamScore[p]+1
        call AddHeroXP(Hero[p],120,false)
        call DisplayTimedTextToPlayer(Player(p),0.,0.,5.,"Ответ принят. Верно: +120 опыта.")
    else
        call DisplayTimedTextToPlayer(Player(p),0.,0.,5.,"Ответ принят. Неверно; следующая попытка — на следующем вопросе.")
    endif
endfunction
function ExamChat takes nothing returns nothing
    local integer p=GetPlayerId(GetTriggerPlayer())
    local string text=GetEventPlayerChatString()
    if p>=12 or GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER then
        return
    endif
    if SubString(text,0,8)=="-answer " then
        set text=SubString(text,8,StringLength(text))
    endif
    if text=="1" or text=="2" or text=="3" or text=="4" then
        call ExamAnswer(p,S2I(text))
    endif
endfunction
function ExamAsk takes nothing returns nothing
    local integer pick=GetRandomInt(0,15)
    local integer p=0
    loop
        exitwhen not ExamUsed[pick]
        set pick=ModuloInteger(pick+1,16)
    endloop
    set ExamQuestion=pick
    set ExamUsed[pick]=true
    set ExamAsked=ExamAsked+1
    set ExamNextAt=TimeNow+15.
    loop
        exitwhen p>=12
        set ExamAnswered[p]=false
        set ExamAnswerAt[p]=TimeNow+I2R(GetRandomInt(3,10))
        set p=p+1
    endloop
    call ExamBroadcast("Ибики: Вопрос "+I2S(ExamAsked)+"/5. "+ExamQuestionText[pick]+" |nОтвет: 1, 2, 3 или 4 в чат (либо -answer 1..4). Одна попытка, 15 секунд.")
endfunction
function ExamStartQuiz takes nothing returns nothing
    local integer p=0
    local integer t=0
    local integer k=0
    local integer j=0
    local trigger answers=CreateTrigger()
    set ExamAnswers=answers
    if StoryMentorDialog!=null then
        call TimerDialogDisplay(StoryMentorDialog,false)
        call DestroyTimerDialog(StoryMentorDialog)
        set StoryMentorDialog=null
    endif
    if StoryMentorClock!=null then
        call PauseTimer(StoryMentorClock)
        call DestroyTimer(StoryMentorClock)
        set StoryMentorClock=null
    endif
    set ExamPhase=2
    set ExamAsked=0
    set ExamNextAt=TimeNow+10.
    set MusicCursor=1
    call FoundationMusicStart()
    loop
        exitwhen p>=12
        if Hero[p]!=null then
            call TreeJumpEnd(p)
            call RosterReset(p)
            call SkillsClearSharingan(p)
            set ComboLeft[p]=0
            set ComboTarget[p]=null
            set ComboBurn[p]=0.
            set ResumeAt[p]=0.
            if BurstArt[p]!=null then
                call DestroyEffect(BurstArt[p])
                set BurstArt[p]=null
            endif
            call IssueImmediateOrder(Hero[p],"stop")
            if not FoundationAlive(Hero[p]) then
                call ReviveHero(Hero[p],SpawnX[p],SpawnY[p],false)
            endif
            call UnitAddAbility(Hero[p],'Avul')
            call PauseUnit(Hero[p],true)
            // Classroom from original FJ; each row is one team.
            call SetUnitPosition(Hero[p],-15744.+I2R(ModuloInteger(p,3))*240.,-700.-I2R(StoryTeam(p))*320.)
            call PanCameraToTimedForPlayer(Player(p),GetUnitX(Hero[p]),GetUnitY(Hero[p]),1.)
            call TriggerRegisterPlayerChatEvent(answers,Player(p),"",false)
        endif
        set p=p+1
    endloop
    loop
        exitwhen j>=72
        if EnemyMark[j]!=null then
            call DestroyEffect(EnemyMark[j])
            set EnemyMark[j]=null
        endif
        set EnemyPending[j]=0.
        if StoryEnemy[j]!=null then
            call RemoveUnit(StoryEnemy[j])
            set StoryEnemy[j]=null
        endif
        set j=j+1
    endloop
    loop
        exitwhen t>=4
        if StoryMembers[t]>0 then
            set StoryStage[t]=6
        endif
        set t=t+1
    endloop
    call TriggerAddAction(answers,function ExamChat)
    set answers=null
    call ExamBroadcast("Ибики: Первый этап экзамена на чунина — вопросы. Пять случайных вопросов, 15 секунд на каждый. Первый ответ окончательный. За верный ответ — 120 опыта. Боты отвечают самостоятельно; их ответы не заменяют ваши. Затем все отряды отправятся в Лес смерти.")
endfunction
function NextChapterTick takes nothing returns nothing
    local integer t=0
    local integer p=0
    local integer choice=0
    local boolean ready=true
    local boolean occupied=false
    if ExamPhase==0 then
        loop
            exitwhen t>=4
            if StoryMembers[t]>0 then
                set occupied=true
                if StoryStage[t]!=5 then
                    set ready=false
                endif
            endif
            set t=t+1
        endloop
        if occupied and (ready or TimeNow>=420.) then
            set ExamPhase=1
            set ExamReadyAt=RMaxBJ(TimeNow,420.)
            call ExamBroadcast("Какаши: Все отряды вернулись с моста. Готовьтесь к экзамену с вопросами. Он начнётся по общему исходному таймеру 7 минут. Пополните снаряжение.")
        endif
    elseif ExamPhase==1 and TimeNow>=ExamReadyAt then
        call ExamStartQuiz()
    elseif ExamPhase==2 then
        if TimeNow>=ExamNextAt then
            if ExamAsked>0 then
                call ExamBroadcast("Ибики: Время. Правильный вариант: "+I2S(ExamCorrect[ExamQuestion])+".")
            endif
            if ExamAsked>=5 then
                loop
                    exitwhen p>=12
                    if Hero[p]!=null then
                        call DisplayTimedTextToPlayer(Player(p),0.,0.,12.,"Ибики: Верных ответов: "+I2S(ExamScore[p])+" из 5. Переходим к испытанию со свитками.")
                    endif
                    set p=p+1
                endloop
                call ExamStartForest()
            else
                call ExamAsk()
            endif
        elseif ExamAsked>0 then
            loop
                exitwhen p>=12
                if Hero[p]!=null and GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER and not ExamAnswered[p] and TimeNow>=ExamAnswerAt[p] then
                    set choice=ExamCorrect[ExamQuestion]
                    if GetRandomInt(1,100)>75 then
                        set choice=ModuloInteger(choice,4)+1
                    endif
                    call ExamAnswer(p,choice)
                endif
                set p=p+1
            endloop
        endif
    elseif ExamPhase==3 then
        call ExamForestTick()
    endif
endfunction
