globals
    integer SasukeRebuildSlot=-1
    unit array SasukeRebuildTarget
    integer array SasukeRebuildViewer
    real array SasukeRebuildAt
    real array SasukeRebuildNext
    integer array SasukeRebuildCount
    integer array SasukeRebuildRanks
    item array SasukeRebuildItems
    unit array Source40SmokeCaster
    real array Source40SmokeAt
    real array Source40SmokeX
    real array Source40SmokeY
    integer array Source40SmokeRank
    real Source40Now=0.
    group Source40Scratch=null
    group Source40Cleanup=null
    hashtable Source40Birth=null
    rect Source40TreeRect=null
    real Source40CutX=0.
    real Source40CutY=0.
    integer Source40Cursor=0
    group array Source40Helpers
    unit array Source40Ball
    unit array Source40BallCaster
    real array Source40BallPoseAt
    real array Source40BallAt
    real array Source40BallUntil
    real array Source40BallBudget
    real array Source40BallX
    real array Source40BallY
    real array Source40BallAngle
    boolean array Source40BallSteered
    unit array Source40AgiCaster
    real array Source40AgiUntil
    unit array Source40WindCaster
    real array Source40WindAt
    real array Source40WindX
    real array Source40WindY
    real array Source40WindAngle
    boolean CampaignFastTestQueued=false
    boolean CampaignFastTestActive=false
    integer CampaignFastWaveCursor=0
    integer array SasukeCorpseHealsBlocked
    integer array SasukeReviveFailures
    real array VisualWindPoseAt
    unit array VisualApproachCaster
    unit array VisualApproachTarget
    real array VisualApproachAt
    integer array VisualApproachSkill
    real array VisualChidoriUntil
    unit array VisualRasenganCaster
    unit array VisualRasenganTarget
    real array VisualRasenganUntil
    real array VisualRasenganPoseUntil
    effect array VisualRasenganArt
    trigger ExamKabutoDeathHook=null
    boolean ExamKabutoLootDropped=false
    unit ExamKabuto=null
    unit ExamKabutoTarget=null
    real ExamKabutoAt=0.
    real ExamKabutoWalkAt=0.
    real ExamKabutoX=0.
    real ExamKabutoY=0.
    real ExamKabutoHealAt=0.
    real ExamKabutoCrippleAt=0.
    // NPC_SOURCE_GLOBALS
    string array SasukeLastSource
    integer array SasukeBlockedRemove
    real array SasukeOutsideSince
    integer array SasukeLastType
    real array SasukeMorphRepairAt
    real array SasukeHiddenSince
    boolean array LogArenaUsed
    rect StatLootRect=null
    integer StatLootPlayer=0
    item StatLootBest=null
    real StatLootDistance=0.
    integer CampaignChampion=-1
    integer CampaignDefenseOwner=12
    real array StoryShopTripUntil
    trigger array CampaignWatcher
    group NPCFirstGroup=null
    boolean NPCSourceReady=false
    trigger NPCEndHook=null
    boolean array NPCChannelGuard
    hashtable NPCHiddenAbilities=null
    hashtable NPCCooldowns=null
    integer array NPCSpellCount
    integer array NPCSourceTypeDummy
    integer array NPCOrderId
    integer array NPCRank
    integer array NPCAbility
    string array NPCOrder
    integer array NPCTarget
    real array NPCRange
    real array NPCRadius
    real array NPCCost
    real array NPCCooldown
    real array NPCHold
    real array CampaignLeafX
    real array CampaignLeafY
    real array CampaignLeafFacing
    real array CampaignAnbuX
    real array CampaignAnbuY
    real array CampaignAnbuFacing
    real array CampaignMedicX
    real array CampaignMedicY
    real array CampaignSupportX
    real array CampaignSupportY
    integer CampaignDeployCursor=242
    unit array CampaignClone
    integer array CampaignCloneKind
    real array CampaignCloneCastAt
    boolean array CampaignClonePending
    item array ExamGear
    integer ExamGearCount=0
    boolean CampaignBountyActive=false
    integer array CampaignBountyBefore
    boolean CampaignKabutoAI=true
    boolean array CampaignEventDue
    group CampaignScratch=null
    integer CampaignThinkCursor=0
    integer array CampaignActorRoute
    integer array CampaignAttackerOwner
    integer array CampaignWaveOrigin
    integer array CampaignWaveDestination
    integer array CampaignWaveKind
    integer array CampaignWaveRole
    real array CampaignWavePeriod
    real array CampaignWaveDelay
    real array CampaignPostX
    real array CampaignPostY
    real array CampaignPostFacing
    integer array CampaignDefenseLane
    real array CampaignDefenderX
    real array CampaignDefenderY
    real array CampaignReserveX
    real array CampaignReserveY
    real array CampaignWaveSpawnX
    real array CampaignWaveSpawnY
    real array CampaignWalkX
    real array CampaignWalkY
    real array CampaignWalkAt
    integer array CampaignWalkAttempt
    real array CampaignWaveAt
    real array CampaignRouteX
    real array CampaignRouteY
    real array CampaignFiveX
    real array CampaignFiveY
    integer array CampaignFiveType
    boolean CampaignUkonSpawned=false
    camerasetup array CampaignCamera
    fogmodifier array CampaignArenaFog
    integer CampaignArenaFogStage=0
    boolean CampaignArenaView=false
    boolean CampaignSavedFog=true
    boolean CampaignSavedMask=true
    boolean CampaignCameraApplied=false
    integer array ExamEnemyType
    integer array ExamRespawnType
    real CampaignTrainingAt=0.
    integer CampaignAttackOwner=12
    integer ExamScrollCount=89
    real array ExamRespawnAt
    real ExamRepopulateAt=0.
    real CampaignJiraiyaAt=0.
    real CampaignKabutoAt=0.
    real CampaignSnakeAt=0.
    real CampaignOroAt=0.
    unit CampaignVillageKabuto=null
    unit CampaignVillageSnake=null
    unit CampaignVillageOro=null
    real CampaignSnakeGoneAt=0.
    boolean CampaignSasukeWon=false
    boolean array RoleChosen
    integer CampaignSasukePlayer=-1
    integer CampaignNarutoPlayer=-1
    unit CampaignSasuke=null
    unit CampaignNaruto=null
    real CampaignSasukeGrowAt=0.
    integer CampaignStage=0
    integer CampaignQueued=0
    real CampaignStartAt=0.
    real CampaignIntroAt=0.
    real CampaignEndAt=0.
    real CampaignNextNPC=0.
    real CampaignNextBot=0.
    boolean CampaignTransition=false
    boolean CampaignPlaced=false
    boolean CampaignFinished=false
    integer CampaignCount=0
    integer CampaignLeader=0
    integer CampaignJiraiya=0
    boolean CampaignFound=false
    unit array VillageFountain
    unit array CampaignActor
    integer array CampaignActorType
    real array CampaignCastAt
    real array CampaignMoveAt
    integer array CampaignUnit
    integer array CampaignAnimation
    string array CampaignName
    string array CampaignIntro
    integer array CampaignMusic
    real array CampaignLimit
    real array CampaignX
    real array CampaignY
    real array CampaignTX
    real array CampaignTY
    real array CampaignMinX
    real array CampaignMinY
    real array CampaignMaxX
    real array CampaignMaxY
    real array CampaignBarrelX
    real array CampaignBarrelY
    boolean array CampaignPermanentDead
    integer array CampaignQueue
    integer array CampaignWinner
    integer CampaignQueueCount=0
    integer CampaignQueueCursor=0
    integer CampaignWinnerCount=0
    boolean CampaignPrelimDone=false
    boolean array CampaignPrelimWinner
    real array PetCastAt
    real array PetTrapUntil
    unit array PetTrapVictim
    real array PetTrapDamage
    unit array PetTrapCaster
    unit array PetFog
    real array PetFogUntil
    real array ArenaAttackAt
    integer CampaignDuelA=-1
    integer CampaignDuelB=-1
    real CampaignDuelAt=0.
    boolean CampaignDuelLive=false
    boolean CampaignBracket=false
    boolean CampaignFinalActive=false
    integer array CampaignFinalPlayer
    boolean array CampaignEliminated
    timer array CampaignEventClock
    timerdialog array CampaignEventDialog
    timer CampaignClock=null
    timerdialog CampaignDialog=null
    unit array RamenUnit
    real array RamenUntil
    real array RamenLast
    real array ArenaSeatX
    real array ArenaSeatY
    unit array NoteActor
    real array NoteArmedAt
    real array NoteExpiresAt
    integer NoteCursor=0
    group NoteGroup=null
    fogmodifier array VillageLandmarkFog
    effect array RamenArt
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
    boolean array ExamEngaged
    boolean array ExamDropped
    real array ExamEnemyCastAt
    real array ExamBotOrderAt
    real array ExamBotProgressAt
    real array ExamBotLastX
    real array ExamBotLastY
    unit array ExamBotAvoidUnit
    item array ExamBotGoalItem
    real array ExamBotItemAvoidUntil
    item array ExamBotAvoidItem
    real array ExamBotAvoidUntil
    integer array ExamBotPatrol
    unit array ExamFountain
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
    unit array KibaRollTarget
    unit array KibaRollCaster
    real array KibaRollAge
    real array KibaRollWait
    integer array KibaRollHits
    real array KibaRollDamage
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
    boolexpr VisionHeroFilter=null
    integer array VisionMarkCount
    fogmodifier array VisionMarkFog
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
    unit StoryTargetResult=null
    unit array EnemyFocus
    unit array StoryEnemy
    trigger StoryShopSales=null
    real array StoryShopX
    real array StoryShopY
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
    integer array SandWaveSlot
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
    unit array KunaiCaster
    unit array KunaiTarget
    unit array KunaiMissile
    real array KunaiDamage
    real array KunaiUntil
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
    integer MusicCount=10
    integer MusicActiveChapter=-1
    integer MusicSong=0
    boolean MusicPlaying=false
    integer MusicPlayingTrack=-1
    integer array MusicChapterStart
    integer array MusicChapterCount
    string array MusicTrackPath
    real array MusicTrackSeconds
    integer array PlaylistAudio
    real array PlaylistDuration
    integer SpawnCursor=0
    timer SpawnClock=null
    integer Source35Player=0
    unit Source35Return=null
    real array Lee42KickElapsed
    real array Lee42KickAngle
    integer array Lee42KickStep
    unit array Lee42DrinkCaster
    real array Lee42DrinkElapsed
    integer array Lee42DrinkStep
    unit array Kick35Caster
    unit array Kick35Target
    real array Kick35At
    unit array Choke35Caster
    unit array Choke35Target
    unit array Choke35Helper
    real array Choke35Until
    unit array Source35Hero
    unit array Lotus35Caster
    unit array Lotus35Target
    integer array Lotus35Hits
    real array Lotus35Damage
    real array Lotus35Next
    effect array Lotus35Art
    real array Gate35Until
    real array Gate35Speed
    integer array Gate35Agility
    integer array Drunk35Agility
    integer array Drunk35Rank
    integer array Drunk35Left
    real array Drunk35Next
    integer array Clone35Rank
    real array Clone35At
    real array Clone35Retry
    group array Barrage35Shots
    group array Barrage35Mines
    real array Source35MineCheck
    group array Source35MineUnits
    integer array Barrage35Rank
    real array Barrage35At
    integer array Source35WireOwner
    lightning array Source35Wire
    real array Source35WireUntil
    integer Source35WireCursor=0
    real array SasukePauseSince
    real array SasukeAlphaSince
    real array SasukeSafeX
    real array SasukeSafeY
    boolean array SasukeSafeReady
    integer CampaignOroSlot=-1
    boolean CampaignOroStarted=false
    real CampaignOroWatchAt=0.
    real CampaignOroStaleAt=0.
    unit CampaignOroTarget=null
endglobals
function FoundationAlive takes unit u returns boolean
    // Raising a corpse's HP never revives it in Classic. The engine death flag
    // remains authoritative even if an old heal callback writes positive HP.
    return u!=null and not IsUnitType(u,UNIT_TYPE_DEAD) and GetWidgetLife(u)>.405
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
        set MusicSong=ModuloInteger(MusicSong+1,MusicChapterCount[MusicCursor])
        set MusicPlaying=false
        call ExecuteFunc("FoundationMusicStart")
    endif
endfunction
function FoundationMusicStart takes nothing returns nothing
    local integer index=0
    if MusicCursor<0 or MusicCursor>=MusicCount then
        return
    endif
    if MusicActiveChapter!=MusicCursor then
        set MusicSong=0
        set MusicActiveChapter=MusicCursor
    endif
    if MusicOn then
        set index=MusicChapterStart[MusicCursor]+MusicSong
        if MusicPlaying and MusicPlayingTrack==index then
            return
        endif
        set MusicPlaying=true
        set MusicPlayingTrack=index
        call StopMusic(false)
        call PlayMusic(MusicTrackPath[index])
        call TimerStart(MusicClock,MusicTrackSeconds[index],false,function FoundationMusicNext)
    endif
endfunction
// STORY_RUNTIME
function FoundationMusicSetChapter takes integer chapter returns nothing
    if chapter<0 or chapter>=MusicCount then
        return
    endif
    set MusicCursor=chapter
    call FoundationMusicStart()
endfunction
function FoundationChat takes nothing returns nothing
    local integer p=GetPlayerId(GetTriggerPlayer())
    local string msg=GetEventPlayerChatString()
    local integer k=0
    local integer template=HeroTemplate[p]
    if p>=12 then
        return
    endif
    if msg=="-village fast" then
        call CampaignTestFast(p)
    elseif msg=="-sasuke-die" then
        call CampaignTestSasukeDeath(p)
    elseif msg=="-village" then
        call CampaignTestArena(p,3)
    elseif msg=="-arena" or SubString(msg,0,7)=="-arena " then
        if msg=="-arena" or msg=="-arena 1" then
            call CampaignTestArena(p,1)
        elseif msg=="-arena 2" then
            call CampaignTestArena(p,2)
        else
            call CampaignTestArena(p,0)
        endif
    elseif msg=="-go" or msg=="-follow" or msg=="-retreat" or msg=="-quest" or msg=="-shop" or msg=="-fountain" or msg=="-camera" or msg=="-kabuto" or msg=="-kabutooff" or msg=="-kabutoon" then
        call StoryCommand(p,msg)
    elseif msg=="-naruto" then
        call SkillsChoose(p,0)
    elseif msg=="-rebuildsasuke" or msg=="-fixsasuke hard" then
        call InvasionRebuildCommand(p)
    elseif msg=="-fixsasuke" then
        call InvasionFixSasuke(p)
    elseif msg=="-sasuke" then
        if CampaignStage==12 then
            call InvasionSasukeStatus(p)
        else
            call SkillsChoose(p,1)
        endif
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
    elseif msg=="-fixsasuke" then
        call InvasionFixSasuke(p)
    elseif msg=="-sasuke" then
        call InvasionSasukeStatus(p)
    elseif msg=="-music" then
        if MusicOn then
            set MusicOn=false
            set MusicPlaying=false
            call PauseTimer(MusicClock)
            call StopMusic(false)
        else
            set MusicOn=true
            call FoundationMusicStart()
        endif
        call DisplayTimedTextToPlayer(Player(p),0,0,5.,"Фоновая музыка переключена.")
    elseif msg=="-nextmusic" then
        call FoundationMusicNext()
        call DisplayTimedTextToPlayer(Player(p),0,0,8.,"Следующий трек текущего сюжетного этапа. -music: включить/выключить музыку.")
    elseif msg=="-help" then
        call DisplayTimedTextToPlayer(Player(p),0,0,20.,"-arena 1/2: тест арен; -village: тест вторжения; -village fast: все враги сразу; -sasuke-die: тест смерти Саске (первый игрок). -go: начать миссию / отряд к цели; -follow: прикрывать игрока; -retreat: отступить; -quest: задание и метка; -fixsasuke: мягкое восстановление; -rebuildsasuke: пересоздать Саске с навыками и вещами; -sasuke: состояние; -shop / -fountain: снабжение Конохи; -camera: герой. -hero 1..12: выбор до миссии; -heroes: список; -anim / -anim N: анимация; -voice: голос героя; -sound / -sound N: звук; -music: вкл/выкл; -nextmusic: следующий трек этапа; -skills: каталог. Во время анимации не отдавайте герою приказы.")
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
    call ExecuteFunc("InvasionRebuildTick")
    call ExecuteFunc("InvasionHeroVisibility")
    call ExecuteFunc("CommonLogTick")
    call ExecuteFunc("Source35Tick")
    call ExecuteFunc("InvasionOroWatch")
    call ExecuteFunc("CampaignLateProgress")
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
        call SetUnitState(Hero[p],UNIT_STATE_MANA,GetUnitState(Hero[p],UNIT_STATE_MAX_MANA))
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
    call FogMaskEnable(true)
    call FogEnable(true)
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
