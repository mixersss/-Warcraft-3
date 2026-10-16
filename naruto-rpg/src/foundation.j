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
    string array AudioPath
    string array SkillName
    integer array SkillCount
    real array ResumeAt
    real TimeNow=0.
    integer SpawnCursor=0
    timer SpawnClock=null
endglobals
function FoundationAlive takes unit u returns boolean
    return u!=null and GetWidgetLife(u)>.405
endfunction
function FoundationSound takes integer index returns nothing
    local sound snd=null
    if index>=0 and index<174 then
        set snd=CreateSound(AudioPath[index],false,false,false,10,10,"DefaultEAXON")
        call StartSound(snd)
        call KillSoundWhenDone(snd)
    endif
    set snd=null
endfunction
function FoundationChat takes nothing returns nothing
    local integer p=GetPlayerId(GetTriggerPlayer())
    local string msg=GetEventPlayerChatString()
    local integer k=0
    if p>=12 or Hero[p]==null then
        return
    endif
    if msg=="-anim" and AnimCount[p]>0 then
        set k=ModuloInteger(AnimCursor[p],AnimCount[p])
        call PauseUnit(Hero[p],true)
        call SetUnitAnimation(Hero[p],AnimName[p*64+k])
        set ResumeAt[p]=TimeNow+4.
        set AnimCursor[p]=k+1
        call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Анимация: "+AnimName[p*64+k])
    elseif msg=="-voice" and VoiceCount[p]>0 then
        set k=ModuloInteger(VoiceCursor[p],VoiceCount[p])
        call FoundationSound(VoiceIndex[p*64+k])
        set VoiceCursor[p]=k+1
        call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Озвучка: "+AudioPath[VoiceIndex[p*64+k]])
    elseif SubString(msg,0,7)=="-sound " then
        set k=S2I(SubString(msg,7,StringLength(msg)))
        call FoundationSound(k)
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
                call PauseUnit(Hero[p],false)
                call SetUnitAnimation(Hero[p],"stand")
                set ResumeAt[p]=0.
            endif
            set team=(p-ModuloInteger(p,3))/3
            if GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER and not IsUnitPaused(Hero[p]) and FoundationAlive(Dummy[team]) and GetUnitCurrentOrder(Hero[p])==0 then
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
    call DisplayTimedTextToForce(bj_FORCE_ALL_PLAYERS,60.,"SHINOBI NEW FOUNDATION 01: новая основа, четыре команды по три. Техническая проверка моделей и озвучек, не готовая RPG. -anim: следующая анимация; -voice: озвучка героя; -sound 0..173: любой звук; -skills: полный список его навыков для воссоздания.")
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
