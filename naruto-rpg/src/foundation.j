globals
    unit array LogActor
    real array LogActorUntil
    real array LogUntil
    real array LogReadyAt
    multiboard StageBoard=null
    timer PhaseClock=null
    timerdialog PhaseDialog=null
    integer HUDClockKey=0
    integer array HUDPreviousStage
    real array HUDStageAt
    integer ExamPhase=0
    real ExamReadyAt=0.
    real ExamNextAt=0.
    real ExamOpenAt=0.
    real ExamEndAt=0.
    boolean ExamTowerOpen=false
    integer ExamQuestion=0
    integer ExamAsked=0
    integer ExamPopulateCursor=0
    boolean array ExamUsed
    boolean array ExamAnswered
    integer array ExamScore
    real array ExamAnswerAt
    string array ExamQuestionText
    integer array ExamCorrect
    real array ExamSpawnX
    real array ExamSpawnY
    real array ExamEnemyX
    real array ExamEnemyY
    unit array ExamEnemy
    item array ExamScroll
    boolean array ExamDropped
    real array ExamEnemyCastAt
    real array ExamBotOrderAt
    unit ExamTower=null
    real ExamTowerX=-10096.
    real ExamTowerY=-10160.
    trigger ExamAnswers=null
    timer ExamClock=null
    timerdialog ExamDialog=null
    rect ExamRect=null
    unit array ShadowRoot
    boolean array ShadowBuffSeen
    real array ShadowGraceUntil
    real array ShadowDuration
    unit array VisualLiftUnit
    real array VisualLiftAge
    real array VisualLiftLife
    real array VisualLiftBase
    real array VisualLiftHeight
    integer array VisualVolleyLeft
    integer array VisualVolleyFired
    real array VisualVolleyDelay
    real array VisualVolleyX
    real array VisualVolleyY
    boolean array KibaFourLegs
    integer array SkillFormAnimation
    real array SkillFormPoseScale
    integer array SkillPoseAbility
    real array VisualPoseLife
    integer array VisualZoneIndex
    unit array VisualUnit
    integer array VisualOwner
    integer array VisualMode
    real array VisualSX
    real array VisualSY
    real array VisualTX
    real array VisualTY
    real array VisualHeight
    real array VisualEndHeight
    real array VisualElapsed
    real array VisualLife
    integer VisualCursor=0
    effect array VisualHand
    real array VisualHandLife
    integer array VisualPulseCount
    real array VisualChannelUntil
    integer array VisualChannelIndex
    real array SkillHold
    real array SkillPoseScale
    unit array ShadowSegment
    unit array ShadowTarget
    real array ShadowUntil
    real array VisionUntil
    real array VisionRadius
    real array VisionNext
    fogmodifier array VisionFog
    effect array VisionArt
    effect array SkillFlash
    real array SkillFlashUntil
    integer SkillFlashCursor=0
    boolean array SkillPoseQueued
    integer array SkillPoseIndex
    integer array SkillPoseType
    integer StoryPopulateCursor=0
    timer StoryPopulateClock=null
    real array EnemySpawnX
    real array EnemySpawnY
    integer array EnemyKind
    boolean array EnemyLootRolled
    integer array StoryLootType
    item array StoryLoot
    real array BotUseItemAt
    unit array JumpUnit
    destructable array JumpQueued
    real array JumpElapsed
    real array JumpReadyAt
    real array JumpSX
    real array JumpSY
    real array JumpTX
    real array JumpTY
    real array JumpBaseHeight
    unit array StoryBoss
    unit array StoryMentor
    string array StoryMentorName
    integer array StoryMentorType
    unit array BossClone
    real array EnemyBlinkAt
    real array EnemyPrisonAt
    boolean StoryMentorsReleased=false
    timer StoryMentorClock=null
    timerdialog StoryMentorDialog=null
    boolean array StoryStarted
    integer array StoryStage
    integer array StoryMembers
    boolean array StoryHasHuman
    boolean array StoryMarch
    boolean array StoryRetreat
    real array StoryAdvanceAt
    real array StoryX
    real array StoryY
    unit array StoryEnemy
    unit array StoryShop
    real array EnemyNext
    real array EnemyPending
    real array EnemyX
    real array EnemyY
    effect array EnemyMark
    boolean array EnemyPhase
    real array StoryRevive
    real array StoryBotOrderAt
    real array StoryBuyAt
    integer array StoryBought
    integer array StoryItem
    integer array StoryPrice
    unit array SandWave
    real array SandWaveUntil
    real array SandWaveDX
    real array SandWaveDY
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
    timer MusicClock=null
    integer MusicCursor=0
    integer MusicCount=9
    integer array PlaylistAudio
    real array PlaylistDuration
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
// TREE_RUNTIME
// SKILLS_RUNTIME
function FoundationMusicNext takes nothing returns nothing
    if MusicOn then
        call StopMusic(false)
        call PlayMusic(AudioPath[PlaylistAudio[MusicCursor]])
        call TimerStart(MusicClock,PlaylistDuration[MusicCursor],false,function FoundationMusicNext)
    endif
endfunction
function FoundationMusicStart takes nothing returns nothing
    if MusicOn then
        call StopMusic(false)
        call PlayMusic(AudioPath[PlaylistAudio[MusicCursor]])
        call TimerStart(MusicClock,PlaylistDuration[MusicCursor],false,function FoundationMusicNext)
    endif
endfunction
// STORY_RUNTIME
function FoundationMusicSetChapter takes integer chapter returns nothing
    if chapter<0 or chapter>=MusicCount then
        return
    endif
    set MusicCursor=chapter
    if MusicOn then
        call FoundationMusicStart()
    endif
endfunction
function FoundationChat takes nothing returns nothing
    local integer p=GetPlayerId(GetTriggerPlayer())
    local string msg=GetEventPlayerChatString()
    local integer k=0
    local integer template=HeroTemplate[p]
    if p>=12 then
        return
    endif
    if msg=="-go" or msg=="-follow" or msg=="-retreat" or msg=="-quest" or msg=="-shop" or msg=="-camera" then
        call StoryCommand(p,msg)
    elseif msg=="-naruto" then
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
    elseif not StoryStarted[(p-ModuloInteger(p,3))/3] and msg=="-wound" and FoundationAlive(Hero[p]) then
        call SetWidgetLife(Hero[p],GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.5)
        call DisplayTimedTextToPlayer(Player(p),0,0,8.,"Проверка лечения до начала миссии: здоровье героя снижено до половины.")
    elseif not StoryStarted[(p-ModuloInteger(p,3))/3] and msg=="-practice" and HeroRole[p]>=0 and FoundationAlive(Hero[p]) then
        call SetHeroLevel(Hero[p],30,false)
        call SetUnitState(Hero[p],UNIT_STATE_MANA,GetUnitState(Hero[p],UNIT_STATE_MAX_MANA))
        call DisplayTimedTextToPlayer(Player(p),0,0,12.,"Проверка техник перед миссией: 30-й уровень. Изучи техники кнопкой +. Мана восстановлена; перезарядки сохраняются.")
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
            set MusicOn=false
            call PauseTimer(MusicClock)
            call StopMusic(false)
        else
            set MusicOn=true
            call FoundationMusicStart()
        endif
        call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Фоновая музыка переключена.")
    elseif msg=="-nextmusic" then
        call FoundationMusicNext()
        call DisplayTimedTextToPlayer(Player(p),0,0,8.,"Музыка текущего сюжетного этапа начата заново. -music: включить/выключить музыку.")
    elseif msg=="-help" then
        call DisplayTimedTextToPlayer(Player(p),0,0,20.,"-go: начать миссию / отряд к цели; -follow: прикрывать игрока; -retreat: отступить; -quest: задание и метка; -shop: магазин; -camera: герой. -hero 1..12: выбор до миссии; -heroes: список; -anim / -anim N: анимация; -voice: голос героя; -sound / -sound N: звук; -music: вкл/выкл; -nextmusic: заново музыку этапа; -skills: каталог. Во время анимации не отдавайте герою приказы.")
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
    call StoryTick()
    loop
        exitwhen p>=12
        if FoundationAlive(Hero[p]) and ResumeAt[p]>0. and TimeNow>=ResumeAt[p] then
            call SetUnitAnimation(Hero[p],"stand")
            set ResumeAt[p]=0.
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
            call VisualPrepareHero(p)
            call SetHeroLevel(Hero[p],1,false)
            call RosterGrantInnate(p)
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
    loop
        exitwhen p>=12
        set HeroTemplate[p]=p
        call TriggerRegisterPlayerChatEvent(chat,Player(p),"-",false)
        set p=p+1
    endloop
    call TriggerAddAction(chat,function FoundationChat)
    call TreeJumpInit()
    call StoryInit()
    call FogMaskEnable(false)
    call FogEnable(false)
    call SetTimeOfDay(12.)
    call SetTimeOfDayScale(0.)
    set MusicClock=CreateTimer()
    call FoundationMusicStart()
    call DisplayTimedTextToForce(bj_FORCE_ALL_PLAYERS,60.,"Глава I — Страна Волн. -heroes: список; -hero 1..12: выбор до выхода; +: изучить техники. -go: начать раньше; начало автоматически через 30 секунд; ПКМ по дереву: прыжок за 50 чакры. -follow: боты прикрывают вас; -quest: цель; -shop: снабжение. Гибель: возвращение через 20 секунд.")
    set SpawnClock=CreateTimer()
    call TimerStart(SpawnClock,.35,true,function FoundationSpawn)
    call TimerStart(clock,.5,true,function FoundationTick)
    set chat=null
    set clock=null
endfunction
function main takes nothing returns nothing
    call SetCameraBounds(-16320.,-16320.,16320.,16320.,-16320.,16320.,16320.,-16320.)
    call SetDayNightModels("Environment\\DNC\\DNCLordaeron\\DNCLordaeronTerrain\\DNCLordaeronTerrain.mdl","Environment\\DNC\\DNCLordaeron\\DNCLordaeronUnit\\DNCLordaeronUnit.mdl")
    call NewSoundEnvironment("Default")
    call SetAmbientDaySound("")
    call SetAmbientNightSound("")
    call InitBlizzard()
    call FoundationInit()
endfunction
