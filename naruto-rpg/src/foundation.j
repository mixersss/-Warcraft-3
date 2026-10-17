globals
    integer array RosterMechanic
    real array RosterPower
    real array RosterBurn
    real array RosterRadius
    real array RosterDuration
    string array RosterVisual
    integer array RosterProfile
    integer array RosterPetType
    integer array RosterPetSlot
    integer array RosterBonus
    boolean array SkillPassive
    boolean array SkillMorph
    boolean array SkillToggle
    boolean array SkillHeal
    integer array SkillAnimation
    boolean SkillDataReady=false
    integer SkillDataCursor=0
    timer SkillDataClock=null
    real array RosterBuffUntil
    real array RosterBuffDrain
    effect array RosterBuffArt
    real array ZoneUntil
    real array ZoneNext
    real array ZoneX
    real array ZoneY
    real array ZoneRadius
    real array ZonePower
    real array ZoneBurn
    boolean array ZoneFollow
    effect array ZoneArt
    real array RosterNextSecond
    unit RosterAlly=null
    unit array Companion
    unit array StunDummy
    real array StunExpires
    integer StunCursor=0
    real array ComboBurn
    integer array HeroTemplate
    integer array HeroRole
    integer array PlayableSkill
    integer array SkillRanks
    integer array SkillRequired
    integer array SkillSkip
    integer array SkillAudio
    integer array SkillTarget
    string array SkillOrder
    real array SkillCooldown
    real array SkillMana
    real array BotReadyAt
    real array BotNextCast
    real array SharinganUntil
    real array BurstUntil
    effect array SharinganArt
    effect array BurstArt
    unit array ComboTarget
    integer array ComboLeft
    real array ComboDamage
    group SkillScratch=null
    unit array Hero
    real array DummyRespawnAt
    unit array Dummy
    integer array RosterHeroType
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
    boolean array AudioQueued
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
    local integer index=0
    set PendingAudio=-1
    loop
        exitwhen index>174
        if AudioQueued[index] then
            set AudioQueued[index]=false
            call StopSound(AudioHandle[index],false,false)
            call StartSound(AudioHandle[index])
        endif
        set index=index+1
    endloop
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
    set AudioQueued[index]=true
    set PendingAudio=index
    call TimerStart(AudioClock,.2,false,function FoundationPlayPending)
endfunction
// SKILLS_RUNTIME
function FoundationChat takes nothing returns nothing
    local integer p=GetPlayerId(GetTriggerPlayer())
    local string msg=GetEventPlayerChatString()
    local integer k=0
    local integer template=HeroTemplate[p]
    if p>=12 then
        return
    endif
    if msg=="-naruto" then
        call SkillsChoose(p,0)
    elseif msg=="-sasuke" then
        call SkillsChoose(p,1)
    elseif SubString(msg,0,6)=="-hero " then
        set k=S2I(SubString(msg,6,StringLength(msg)))-1
        if k>=0 and k<12 then
            call SkillsChoose(p,k)
        endif
    elseif msg=="-heroes" then
        set k=0
        loop
            exitwhen k>=12
            call DisplayTimedTextToPlayer(Player(p),0,0,30.,I2S(k+1)+" — "+HeroName[k])
            set k=k+1
        endloop
    elseif msg=="-wound" and FoundationAlive(Hero[p]) then
        call SetWidgetLife(Hero[p],GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.5)
        call DisplayTimedTextToPlayer(Player(p),0,0,8.,"Тренировочная проверка лечения: здоровье героя снижено до половины.")
    elseif msg=="-practice" and HeroRole[p]>=0 and FoundationAlive(Hero[p]) then
        call SetHeroLevel(Hero[p],30,false)
        call SetUnitState(Hero[p],UNIT_STATE_MANA,GetUnitState(Hero[p],UNIT_STATE_MAX_MANA))
        call DisplayTimedTextToPlayer(Player(p),0,0,12.,"Тренировочный режим: 30-й уровень. Изучи техники кнопкой +. Мана восстановлена; перезарядки сохраняются.")
    elseif msg=="-anim" or SubString(msg,0,6)=="-anim " then
        if not FoundationAlive(Hero[p]) then
            call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Герой ещё не создан или погиб.")
            return
        endif
        if GetUnitTypeId(Hero[p])!=HeroType[p] then
            call DisplayTimedTextToPlayer(Player(p),0,0,8.,"Просмотр анимаций доступен в обычной форме героя.")
            return
        endif
        if msg=="-anim" then
            set k=ModuloInteger(AnimCursor[p],AnimCount[template])
        else
            set k=S2I(SubString(msg,6,StringLength(msg)))
        endif
        if k<0 or k>=AnimCount[template] then
            call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Индекс анимации: 0.."+I2S(AnimCount[template]-1))
            return
        endif
        call IssueImmediateOrder(Hero[p],"stop")
        call SetUnitTimeScale(Hero[p],1.)
        call SetUnitAnimationByIndex(Hero[p],k)
        set ResumeAt[p]=TimeNow+4.
        set AnimCursor[p]=ModuloInteger(k+1,AnimCount[template])
        call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Анимация "+I2S(k)+": "+AnimName[template*64+k])
    elseif msg=="-voice" and VoiceCount[template]>0 then
        set k=ModuloInteger(VoiceCursor[p],VoiceCount[template])
        call FoundationSound(VoiceIndex[template*64+k])
        set VoiceCursor[p]=k+1
        call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Озвучка: "+AudioPath[VoiceIndex[template*64+k]])
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
        call DisplayTimedTextToPlayer(Player(p),0,0,20.,"-hero 1..12: выбрать героя; -heroes: список; -practice: 30-й уровень; -wound: проверить лечение; -anim / -anim N: анимация; -voice: голос героя; -sound / -sound N: звук; -music: переключить музыку; -skills: каталог. Во время анимации не отдавайте герою приказы.")
    elseif msg=="-skills" then
        call DisplayTimedTextToPlayer(Player(p),0,0,15.,"Навыки персонажа: "+HeroName[template]+". У всех двенадцати персонажей подключены техники; изучай их кнопкой +.")
        loop
            exitwhen k>=SkillCount[template]
            call DisplayTimedTextToPlayer(Player(p),0,0,15.,SkillName[template*5+k])
            set k=k+1
        endloop
    endif
endfunction
function FoundationRefreshTargets takes nothing returns nothing
    local integer team=0
    local real x=-3400.
    local real y=-3400.
    loop
        exitwhen team>=4
        if not FoundationAlive(Dummy[team]) then
            if DummyRespawnAt[team]==0. then
                set DummyRespawnAt[team]=TimeNow+5.
            elseif TimeNow>=DummyRespawnAt[team] then
                call RemoveUnit(Dummy[team])
                if team==1 or team==2 then
                    set x=3400.
                else
                    set x=-3400.
                endif
                if team==2 or team==3 then
                    set y=3400.
                else
                    set y=-3400.
                endif
                set Dummy[team]=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),'rdum',x,y,0.)
                set DummyRespawnAt[team]=0.
            endif
        endif
        set team=team+1
    endloop
endfunction
function FoundationTick takes nothing returns nothing
    local integer p=0
    local integer team=0
    local boolean casting=false
    set TimeNow=TimeNow+.5
    call FoundationRefreshTargets()
    loop
        exitwhen p>=12
        if FoundationAlive(Hero[p]) then
            if ResumeAt[p]>0. and TimeNow>=ResumeAt[p] then
                call SetUnitAnimation(Hero[p],"stand")
                set ResumeAt[p]=0.
            endif
            set team=(p-ModuloInteger(p,3))/3
            if GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER and ResumeAt[p]==0. and FoundationAlive(Dummy[team]) then
                set casting=SkillsBot(p)
                if not casting and TimeNow>=BotNextCast[p] and GetUnitCurrentOrder(Hero[p])==0 then
                    call IssueTargetOrder(Hero[p],"attack",Dummy[team])
                endif
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
        if HeroRole[p]>=0 then
            call SetHeroLevel(Hero[p],10,false)
            if GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER then
                call SkillsLearnBot(p)
            endif
        endif
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
    call SkillsInit()
    set AudioClock=CreateTimer()
    set AudioPath[174]="Sound\\Interface\\QuestNew.wav"
    set AudioEAX[174]=""
    set Dummy[0]=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),'rdum',-3400.,-3400.,225.)
    set Dummy[1]=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),'rdum',3400.,-3400.,315.)
    set Dummy[2]=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),'rdum',3400.,3400.,45.)
    set Dummy[3]=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),'rdum',-3400.,3400.,135.)
    loop
        exitwhen p>=12
        set HeroTemplate[p]=p
        call TriggerRegisterPlayerChatEvent(chat,Player(p),"-",false)
        set p=p+1
    endloop
    call TriggerAddAction(chat,function FoundationChat)
    call FogMaskEnable(false)
    call FogEnable(false)
    call SetTimeOfDay(12.)
    call SetTimeOfDayScale(0.)
    call PlayMusic("war3mapImported\\Hero Beginning32br48hz.mp3")
    call DisplayTimedTextToForce(bj_FORCE_ALL_PLAYERS,60.,"SHINOBI ROSTER ALPHA 06: техники всех 12 героев. -heroes: список; -hero 1..12: выбор; кнопка +: изучить навыки; -practice: 30-й уровень для проверки. Боты изучают и применяют техники. Сюжет ещё не подключён.")
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
    call SetAmbientDaySound("")
    call SetAmbientNightSound("")
    call InitBlizzard()
    call FoundationInit()
endfunction
