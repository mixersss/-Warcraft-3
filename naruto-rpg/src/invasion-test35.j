// Explicit host-only diagnostic scenario. Normal campaign timing is untouched.
function CampaignTestHost takes integer sender returns boolean
    local integer p=0
    loop
        exitwhen p>=12 or (GetPlayerSlotState(Player(p))==PLAYER_SLOT_STATE_PLAYING and GetPlayerController(Player(p))!=MAP_CONTROL_COMPUTER)
        set p=p+1
    endloop
    return p<12 and sender==p
endfunction
function CampaignFastWaveStep takes nothing returns nothing
    local integer lane=CampaignFastWaveCursor
    if not CampaignFastTestActive or CampaignStage!=12 or CampaignTransition or CampaignFinished or lane>=8 then
        return
    endif
    set CampaignFastWaveCursor=lane+1
    call CampaignInvasionWave(lane)
    set CampaignWaveAt[lane]=TimeNow+CampaignWavePeriod[lane]+CampaignWaveDelay[lane]
endfunction
function CampaignFastInvasion takes nothing returns nothing
    local integer lane=0
    if CampaignStage!=12 or CampaignTransition or CampaignFinished or CampaignFastTestActive then
        return
    endif
    set CampaignFastTestQueued=false
    set CampaignFastTestActive=true
    set CampaignFastWaveCursor=0
    // Only release scheduled events, never re-create already arrived/dead bosses.
    if CampaignKabutoAt>0. then
        set CampaignKabutoAt=TimeNow
        set CampaignEventDue[0]=true
    endif
    if CampaignJiraiyaAt>0. then
        set CampaignJiraiyaAt=TimeNow
        set CampaignEventDue[1]=true
    endif
    if CampaignSnakeAt>0. then
        set CampaignSnakeAt=TimeNow
        set CampaignEventDue[2]=true
    endif
    if CampaignOroAt>0. and not CampaignOroStarted then
        set CampaignOroAt=TimeNow
        set CampaignEventDue[3]=true
    endif
    call ExecuteFunc("CampaignInvasionEvents")
    loop
        exitwhen lane>=8
        // Each original lane has its own operation budget, no extra timer/loop.
        call ExecuteFunc("CampaignFastWaveStep")
        set lane=lane+1
    endloop
    call ExamBroadcast("ТЕСТ ВТОРЖЕНИЯ: волны всех направлений и запланированные подкрепления выпущены. -sasuke-die: обычная смерть Саске; -sasuke: диагностика. Возрождение через 20 секунд.")
endfunction
function CampaignTestFast takes integer sender returns nothing
    if not CampaignTestHost(sender) then
        call DisplayTimedTextToPlayer(Player(sender),0.,0.,12.,"Тест доступен первому игроку-человеку в списке слотов.")
        return
    endif
    if CampaignFinished or CampaignTransition or CampaignStage>12 then
        call DisplayTimedTextToPlayer(Player(sender),0.,0.,12.,"Для теста начните новую игру или дождитесь окончания перехода. Поздний сюжет не прерывается.")
        return
    endif
    if CampaignStage==12 then
        if CampaignFastTestActive then
            call DisplayTimedTextToPlayer(Player(sender),0.,0.,12.,"Быстрый тест уже запущен; дополнительные копии врагов не создаются.")
        else
            call CampaignFastInvasion()
        endif
    else
        call CampaignTestArena(sender,3)
        if CampaignTransition and CampaignQueued==12 then
            set CampaignFastTestQueued=true
        endif
    endif
endfunction
function CampaignTestSasukeDeath takes integer sender returns nothing
    local integer p=0
    local boolean found=false
    if not CampaignTestHost(sender) or not CampaignFastTestActive or CampaignStage!=12 or CampaignTransition or CampaignFinished then
        call DisplayTimedTextToPlayer(Player(sender),0.,0.,12.,"Сначала первый игрок должен запустить -village fast и дождаться начала вторжения.")
        return
    endif
    loop
        exitwhen p>=12
        if HeroRole[p]==1 and FoundationAlive(Hero[p]) then
            call KillUnit(Hero[p])
            set found=true
        endif
        set p=p+1
    endloop
    if found then
        call ExamBroadcast("ТЕСТ: Саске погиб обычной смертью. Подождите 20 секунд; -sasuke покажет состояние и срок возрождения.")
    else
        call DisplayTimedTextToPlayer(Player(sender),0.,0.,12.,"Живого Саске нет: он ещё не выбран или ожидает возрождения. -sasuke: диагностика.")
    endif
endfunction
