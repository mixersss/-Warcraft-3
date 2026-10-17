function HUDTime takes real seconds returns string
    local integer n=R2I(RMaxBJ(0.,seconds))
    local integer m=(n-ModuloInteger(n,60))/60
    local integer s=ModuloInteger(n,60)
    if s<10 then
        return I2S(m)+":0"+I2S(s)
    endif
    return I2S(m)+":"+I2S(s)
endfunction
function HUDCell takes integer row, integer col, string text returns nothing
    local multiboarditem cell=MultiboardGetItem(StageBoard,row,col)
    call MultiboardSetItemValue(cell,text)
    call MultiboardReleaseItem(cell)
    set cell=null
endfunction
function HUDClockEnd takes nothing returns nothing
endfunction
function HUDInit takes nothing returns nothing
    set StageBoard=CreateMultiboard()
    call MultiboardSetTitleText(StageBoard,"Миссия и время отрядов")
    call MultiboardSetRowCount(StageBoard,6)
    call MultiboardSetColumnCount(StageBoard,3)
    call MultiboardSetItemsStyle(StageBoard,true,false)
    call MultiboardSetItemsWidth(StageBoard,.14)
    call HUDCell(0,0,"Отряд")
    call HUDCell(0,1,"Этап")
    call HUDCell(0,2,"Время")
    call MultiboardDisplay(StageBoard,true)
    call MultiboardMinimize(StageBoard,false)
    set PhaseClock=CreateTimer()
    set PhaseDialog=CreateTimerDialog(PhaseClock)
    call TimerDialogDisplay(PhaseDialog,false)
endfunction
function HUDTick takes nothing returns nothing
    local integer t=0
    local integer stage=0
    local integer key=0
    local string phase=""
    local string timing=""
    local real remaining=0.
    if StageBoard==null then
        return
    endif
    loop
        exitwhen t>=4
        set stage=StoryStage[t]
        if HUDPreviousStage[t]!=stage then
            set HUDPreviousStage[t]=stage
            set HUDStageAt[t]=TimeNow
        endif
        set timing=HUDTime(TimeNow-HUDStageAt[t])+" прошло"
        if StoryMembers[t]==0 then
            set phase="Пустые слоты"
            set timing="—"
        elseif not StoryStarted[t] then
            set phase="Подготовка"
            set timing=HUDTime(30.-TimeNow)+" до выхода"
        elseif stage==1 then
            set phase="Лес: первый дозор"
        elseif stage==2 then
            set phase="Лес: зачистка"
        elseif stage==3 then
            set phase="Бой с Хаку"
        elseif stage==4 then
            set phase="Бой с Забузой"
        elseif stage==5 then
            set phase="Ждём отряды"
            if ExamPhase==1 then
                set timing=HUDTime(ExamReadyAt-TimeNow)+" до экзамена"
            endif
        elseif stage==6 then
            set phase="Ибики: вопрос "+I2S(ExamAsked)+"/5"
            if ExamAsked==0 then
                set phase="Ибики: правила"
            endif
            set timing=HUDTime(ExamNextAt-TimeNow)+" осталось"
        elseif stage==7 then
            set phase="Лес смерти"
            set timing=HUDTime(ExamEndAt-TimeNow)+" до конца"
        else
            set phase="Этап завершён"
            set timing="Ожидание арен"
        endif
        if StoryAdvanceAt[t]>TimeNow and stage<5 then
            set timing=HUDTime(StoryAdvanceAt[t]-TimeNow)+" до перехода"
        endif
        call HUDCell(t+1,0,"Команда "+I2S(t+1))
        call HUDCell(t+1,1,phase)
        call HUDCell(t+1,2,timing)
        set t=t+1
    endloop
    call HUDCell(5,0,"Общий этап")
    if ExamPhase==0 then
        if StoryMentorsReleased then
            call HUDCell(5,1,"Наставники в бою")
            call HUDCell(5,2,"—")
        else
            call HUDCell(5,1,"Выход наставников")
            call HUDCell(5,2,HUDTime(330.-TimeNow))
        endif
    elseif ExamPhase==1 then
        call HUDCell(5,1,"До вопросов Ибики")
        call HUDCell(5,2,HUDTime(ExamReadyAt-TimeNow))
        set key=1
        set remaining=ExamReadyAt-TimeNow
    elseif ExamPhase==2 then
        call HUDCell(5,1,"До следующего вопроса")
        call HUDCell(5,2,HUDTime(ExamNextAt-TimeNow))
        set key=10+ExamAsked
        set remaining=ExamNextAt-TimeNow
    elseif ExamPhase==3 then
        if ExamTowerOpen then
            call HUDCell(5,1,"Башня открыта")
            call HUDCell(5,2,HUDTime(ExamEndAt-TimeNow)+" до конца")
        else
            call HUDCell(5,1,"До открытия башни")
            call HUDCell(5,2,HUDTime(ExamOpenAt-TimeNow))
        endif
    else
        call HUDCell(5,1,"Экзамен завершён")
        call HUDCell(5,2,"—")
    endif
    if key!=HUDClockKey then
        set HUDClockKey=key
        if key>0 then
            call TimerStart(PhaseClock,RMaxBJ(.01,remaining),false,function HUDClockEnd)
            if key==1 then
                call TimerDialogSetTitle(PhaseDialog,"До вопросов Ибики")
            elseif ExamAsked==0 then
                call TimerDialogSetTitle(PhaseDialog,"Ибики: до первого вопроса")
            else
                call TimerDialogSetTitle(PhaseDialog,"Ибики: вопрос "+I2S(ExamAsked)+"/5")
            endif
            call TimerDialogDisplay(PhaseDialog,true)
        else
            call PauseTimer(PhaseClock)
            call TimerDialogDisplay(PhaseDialog,false)
        endif
    endif
endfunction
