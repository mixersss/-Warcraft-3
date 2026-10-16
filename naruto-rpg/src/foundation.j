globals
    unit array Hero
    unit array Dummy
    integer array HeroType
    string array HeroName
    real array SpawnX
    real array SpawnY
    integer array AnimCount
    string array AnimName
    integer array AnimCursor
    integer array VoiceCount
    integer array VoiceIndex
    integer array VoiceCursor
    sound array AudioHandle
    integer array AudioDuration
    string array AudioEAX
    integer PendingAudio=-1
    timer AudioClock=null
    string array AudioPath
    string array SkillName
    integer array SkillCount
    real array ResumeAt
    real TimeNow=0.
    integer array AudioCursor
    boolean MusicOn=true
    integer SpawnCursor=0
    timer SpawnClock=null
endglobals
function FoundationAlive takes unit u returns boolean
    return u!=null and GetWidgetLife(u)>.405
endfunction
function FoundationPlayPending takes nothing returns nothing
    local integer index=PendingAudio
    set PendingAudio=-1
    if index>=0 and index<=174 then
        call StopSound(AudioHandle[index],false,false)
        call StartSound(AudioHandle[index])
    endif
endfunction
function FoundationSound takes integer index returns nothing
    if index<0 or index>174 then
        return
    endif
    if AudioHandle[index]==null then
        set AudioHandle[index]=CreateSound(AudioPath[index],false,false,false,10,10,AudioEAX[index])
        if index<174 then
            call SetSoundDuration(AudioHandle[index],AudioDuration[index])
        endif
        call SetSoundChannel(AudioHandle[index],0)
        call SetSoundVolume(AudioHandle[index],127)
        call SetSoundPitch(AudioHandle[index],1.)
    endif
    set PendingAudio=index
    call TimerStart(AudioClock,.2,false,function FoundationPlayPending)
endfunction
function FoundationChat takes nothing returns nothing
    local integer p=GetPlayerId(GetTriggerPlayer())
    local string msg=GetEventPlayerChatString()
    local integer k=0
    if p>=12 then
        return
    endif
    if msg=="-anim" or SubString(msg,0,6)=="-anim " then
        if not FoundationAlive(Hero[p]) then
            call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Герой ещё не создан или погиб.")
            return
        endif
        if msg=="-anim" then
            set k=ModuloInteger(AnimCursor[p],AnimCount[p])
        else
            set k=S2I(SubString(msg,6,StringLength(msg)))
        endif
        if k<0 or k>=AnimCount[p] then
            call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Индекс анимации: 0.."+I2S(AnimCount[p]-1))
            return
        endif
        call IssueImmediateOrder(Hero[p],"stop")
        call SetUnitTimeScale(Hero[p],1.)
        call SetUnitAnimationByIndex(Hero[p],k)
        set ResumeAt[p]=TimeNow+4.
        set AnimCursor[p]=ModuloInteger(k+1,AnimCount[p])
        call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Анимация "+I2S(k)+": "+AnimName[p*64+k])
    elseif msg=="-voice" and VoiceCount[p]>0 then
        set k=ModuloInteger(VoiceCursor[p],VoiceCount[p])
        call FoundationSound(VoiceIndex[p*64+k])
        set VoiceCursor[p]=k+1
        call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Озвучка: "+AudioPath[VoiceIndex[p*64+k]])
    elseif msg=="-sound" or SubString(msg,0,7)=="-sound " then
        if msg=="-sound" then
            set k=ModuloInteger(AudioCursor[p],174)
        else
            set k=S2I(SubString(msg,7,StringLength(msg)))
        endif
        if k<0 or k>=174 then
            call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Индекс звука: 0..173")
            return
        endif
        call FoundationSound(k)
        set AudioCursor[p]=k+1
        call DisplayTimedTextToPlayer(Player(p),0,0,8.,"Звук "+I2S(k)+": "+AudioPath[k])
    elseif msg=="-soundtest" then
        call FoundationSound(174)
        call DisplayTimedTextToPlayer(Player(p),0,0,8.,"Тест обычного звука Warcraft: сигнал нового задания.")
    elseif msg=="-music" then
        if MusicOn then
            call StopMusic(false)
        else
            call PlayMusic("war3mapImported\\Hero Beginning32br48hz.mp3")
        endif
        set MusicOn=not MusicOn
        call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Фоновая музыка переключена.")
    elseif msg=="-help" then
        call DisplayTimedTextToPlayer(Player(p),0,0,20.,"-anim / -anim N: анимация; -voice: голос героя; -sound / -sound N: звук; -music: переключить музыку; -skills: каталог. Во время анимации не отдавайте герою приказы.")
    elseif msg=="-skills" then
        call DisplayTimedTextToPlayer(Player(p),0,0,15.,"Каталог навыков: "+HeroName[p]+". Механики ещё не подключены в техническом тесте.")
        loop
            exitwhen k>=SkillCount[p]
            call DisplayTimedTextToPlayer(Player(p),0,0,15.,SkillName[p*5+k])
            set k=k+1
        endloop
    endif
endfunction
function FoundationTick takes nothing returns nothing
    local integer p=0
    local integer team=0
    set TimeNow=TimeNow+.5
    loop
        exitwhen p>=12
        if FoundationAlive(Hero[p]) then
            if ResumeAt[p]>0. and TimeNow>=ResumeAt[p] then
                call SetUnitAnimation(Hero[p],"stand")
                set ResumeAt[p]=0.
            endif
            set team=(p-ModuloInteger(p,3))/3
            if GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER and ResumeAt[p]==0. and FoundationAlive(Dummy[team]) and GetUnitCurrentOrder(Hero[p])==0 then
                call IssueTargetOrder(Hero[p],"attack",Dummy[team])
            endif
        endif
        set p=p+1
    endloop
endfunction
function FoundationSpawn takes nothing returns nothing
    local integer p=SpawnCursor
    if p>=12 then
        call PauseTimer(SpawnClock)
        call DestroyTimer(SpawnClock)
        set SpawnClock=null
        return
    endif
    if GetPlayerSlotState(Player(p))==PLAYER_SLOT_STATE_PLAYING then
        set Hero[p]=CreateUnit(Player(p),HeroType[p],SpawnX[p],SpawnY[p],90.)
        call SetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD,500)
        call SelectUnitForPlayerSingle(Hero[p],Player(p))
        call PanCameraToTimedForPlayer(Player(p),SpawnX[p],SpawnY[p],0.)
        call SetCameraFieldForPlayer(Player(p),CAMERA_FIELD_ZOFFSET,350.,0.)
    endif
    set SpawnCursor=p+1
endfunction
function FoundationInit takes nothing returns nothing
    local integer p=0
    local trigger chat=CreateTrigger()
    local timer clock=CreateTimer()
// GENERATED_DATA
    set AudioClock=CreateTimer()
    set AudioPath[174]="Sound\\Interface\\QuestNew.wav"
    set AudioEAX[174]=""
    set Dummy[0]=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),'rdum',-3400.,-3400.,225.)
    set Dummy[1]=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),'rdum',3400.,-3400.,315.)
    set Dummy[2]=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),'rdum',3400.,3400.,45.)
    set Dummy[3]=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),'rdum',-3400.,3400.,135.)
    loop
        exitwhen p>=12
        call TriggerRegisterPlayerChatEvent(chat,Player(p),"-",false)
        set p=p+1
    endloop
    call TriggerAddAction(chat,function FoundationChat)
    call FogMaskEnable(false)
    call FogEnable(false)
    call SetTimeOfDay(12.)
    call SetTimeOfDayScale(0.)
    call PlayMusic("war3mapImported\\Hero Beginning32br48hz.mp3")
    call DisplayTimedTextToForce(bj_FORCE_ALL_PLAYERS,60.,"SHINOBI NEW FOUNDATION 04: новая основа, четыре команды по три. Техническая проверка моделей и озвучек, не готовая RPG. -help: команды теста; -anim 5: анимация; -voice: голос; -sound: следующий звук; -music: выключить/включить музыку. Навыки пока не подключены.")
    set SpawnClock=CreateTimer()
    call TimerStart(SpawnClock,.35,true,function FoundationSpawn)
    call TimerStart(clock,.5,true,function FoundationTick)
    set chat=null
    set clock=null
endfunction
function main takes nothing returns nothing
    call SetCameraBounds(-5888.,-5888.,5888.,5888.,-5888.,5888.,5888.,-5888.)
    call SetDayNightModels("Environment\\DNC\\DNCLordaeron\\DNCLordaeronTerrain\\DNCLordaeronTerrain.mdl","Environment\\DNC\\DNCLordaeron\\DNCLordaeronUnit\\DNCLordaeronUnit.mdl")
    call NewSoundEnvironment("Default")
    call SetAmbientDaySound("LordaeronSummerDay")
    call SetAmbientNightSound("LordaeronSummerNight")
    call InitBlizzard()
    call FoundationInit()
endfunction
