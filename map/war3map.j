// Four Fronts Frenzy. Plain JASS: Warcraft III TFT 1.26+.
// Balance globals and InitBalance are generated from balance.json.
globals
    integer array CreativeBuffUntil
    integer array CreativeBannerUntil
    integer array CreativeRainTicks
    integer array CreativeBladeTicks
    integer array CreativeVamp
    integer array CreativePetType
    real array CreativeRainX
    real array CreativeRainY
    real array CreativeRainPower
    real array CreativeBladePower
    real array CreativeRegen
    trigger array CreativeThread
    group CreativeOwnerGroup = null
    timer HeroQueueTimer = null
    integer HeroQueueCursor = 0
    boolean array HeroQueued
    boolean array HeroLearnQueued
    integer array ScheduledHero
    unit ReturnedUnit = null
    item ReturnedItem = null
    trigger array BotThinkTrigger
    group array CorpseRing
    unit array TeamFountain
    real array PreviousHeroX
    real array PreviousHeroY
    integer array HeroSector
    trigger SummonTrigger = null
    timer AutosaveTimer = null
    integer AutosaveCount = 0
    constant string AUTOSAVE_PATH = "save\\FFFAutosave.w3z"
    unit array HeroPicker
    integer array PickerPage
    unit array UtilityShop
    real array UtilityX
    real array UtilityY
    integer array WaveRanks
    integer array BastionUntil
    integer HostPlayer = -1
    boolean ModeDialogOpen = false
    boolean AllRandomMode = false
    trigger PickerTrainTrigger = null
    trigger PickerSpellTrigger = null
    trigger TransmuteTrigger = null
    unit array TransmuteTarget
    integer array TransmuteReward
    trigger BaseDefenseTrigger = null
    unit array Base
    unit array Hero
    unit array Bastion
    real array BastionX
    real array BastionY
    unit array Tower
    group array Army
    boolean array SlotActive
    boolean array Bot
    boolean array Lost
    boolean array TeamLost
    boolean array Defending
    integer array TierSavings
    boolean array AdvancedUnlocked
    integer array Tier
    integer array Attack
    integer array Armor
    integer array Vitality
    integer array Power
    integer array SpawnClock
    integer array Respawn
    integer array Kills
    integer array HeroKind
    integer array ArmyRace
    integer array CastUntil
    integer array RetreatUntil
    integer array Target
    real array HomeX
    real array HomeY
    real array TeamX
    real array TeamY
    real array RallyX
    real array RallyY
    dialog array Shop
    button array ShopButton
    integer array MenuAction
    integer Seconds = 0
    boolean Finished = false
    group Scan = null
    group Work = null
    multiboard Board = null
    trigger DeathTrigger = null
    trigger ChatTrigger = null
    trigger ShopTrigger = null
    trigger LeaveTrigger = null
    trigger ResearchTrigger = null
    trigger LevelTrigger = null
    integer array SkillLevel
    unit PotionShop = null
    unit array SupremeShop
    unit array BookShop
    unit array TeamBookShop
    integer array ShoppingUntil
    integer array SuperProgress
    unit EquipmentShop = null
    unit Fountain = null
    unit array FortressShop
    real array FortressX
    real array FortressY
    real array ShopX
    real array ShopY
    integer array GearProgress
    integer array GearSavings
    integer array BotTactic
    integer array BotStyle
    boolean array BotStyleReady
    real array BotAlliedPower
    real array BotEnemyPower
    integer array BotNearbyTroops
    integer array BotHurtTroops
    boolean array BotTowerDanger
    unit array TeamFocus
    integer array TeamFocusUntil
    integer array TeamPushUntil
    integer array TeamPushReady
    integer array TeamPlanAt
    integer array TeamOrder
    integer array TeamOrderUntil
    integer array TeamLeader
    unit array BotAttackTarget
    integer array BotSupplyAt
    integer array GearFraction
    integer array TierFraction
endglobals

function TeamOf takes integer p returns integer
    return R2I(I2R(p) / 3.0)
endfunction

function Alive takes unit u returns boolean
    return u != null and GetWidgetLife(u) > 0.405 and not IsUnitType(u, UNIT_TYPE_DEAD)
endfunction

function IsArmyUnit takes unit u returns boolean
    local integer id = GetUnitTypeId(u)
    return id >= 'fm00' and id <= 'fm34'
endfunction

function Tell takes integer p, string message returns nothing
    if not Bot[p] then
        call DisplayTimedTextToPlayer(Player(p), 0, 0, 12, message)
    endif
endfunction

function Say takes string message returns nothing
    call DisplayTimedTextToForce(bj_FORCE_ALL_PLAYERS, 12, message)
endfunction

function DistanceSq takes real ax, real ay, real bx, real by returns real
    return (ax-bx)*(ax-bx) + (ay-by)*(ay-by)
endfunction

function AddGold takes integer p, integer amount returns nothing
    local integer credit
    local integer whole = R2I(I2R(amount)/100.0)
    call SetPlayerState(Player(p), PLAYER_STATE_RESOURCE_GOLD, GetPlayerState(Player(p), PLAYER_STATE_RESOURCE_GOLD) + amount)
    if Bot[p] and Tier[p] < 4 and amount > 0 then
        set credit = ModuloInteger(amount,100)*BotTierBudget[BotTactic[p]]+TierFraction[p]
        set TierSavings[p] = TierSavings[p]+whole*BotTierBudget[BotTactic[p]]+R2I(I2R(credit)/100.0)
        set TierFraction[p] = ModuloInteger(credit,100)
    endif
    if Bot[p] and (GearProgress[p] < 18 or SuperProgress[p] < 6) and amount > 0 then
        set credit = ModuloInteger(amount,100)*BotGearBudget[BotTactic[p]]+GearFraction[p]
        set GearSavings[p] = GearSavings[p]+whole*BotGearBudget[BotTactic[p]]+R2I(I2R(credit)/100.0)
        set GearFraction[p] = ModuloInteger(credit,100)
    endif
endfunction

function ApplyBotHeroProfile takes integer p returns nothing
    if Bot[p] and BotStyleReady[p] then
        set BotTactic[p] = BotRoleTactic[HeroBotRole[HeroKind[p]]*3+BotStyle[p]]
        call SetPlayerName(Player(p),"Bot "+I2S(p+1)+" ["+BotRoleName[HeroBotRole[HeroKind[p]]]+" / "+BotTacticName[BotTactic[p]]+"]")
    endif
endfunction

function AssignBotTactic takes integer p returns nothing
    // Synchronized once per bot; never reroll on death, purchase or revival.
    set BotTactic[p] = GetRandomInt(0,2)
    set BotStyle[p] = BotTactic[p]
    set BotStyleReady[p] = true
endfunction

function EnemyNear takes integer p, real x, real y, real radius returns unit
    local unit u
    local unit best = null
    local real distance
    local real nearest = radius*radius + 1
    local integer owner
    call GroupEnumUnitsInRange(Scan, x, y, radius, null)
    loop
        set u = FirstOfGroup(Scan)
        exitwhen u == null
        call GroupRemoveUnit(Scan, u)
        set owner = GetPlayerId(GetOwningPlayer(u))
        if owner < 12 and TeamOf(owner) != TeamOf(p) and Alive(u) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) then
            set distance = DistanceSq(x, y, GetUnitX(u), GetUnitY(u))
            if distance < nearest then
                set nearest = distance
                set best = u
            endif
        endif
    endloop
    set u = null
    set ReturnedUnit = best
    set best = null
    return ReturnedUnit
endfunction

function UpdateBastion takes integer p returns nothing
    local unit threat = null
    if not Alive(Bastion[p]) or Seconds < WARMUP_SECONDS then
        return
    endif
    set threat = EnemyNear(p,HomeX[p],HomeY[p],900.)
    if threat == null then
        set threat = EnemyNear(p,BastionX[p],BastionY[p],650.)
    endif
    if threat != null then
        if Seconds >= BastionUntil[p] then
            call PauseUnit(Bastion[p],false)
            call IssueTargetOrder(Bastion[p],"attack",threat)
        endif
        set BastionUntil[p] = Seconds+6
    elseif Seconds >= BastionUntil[p] then
        call PauseUnit(Bastion[p],true)
    endif
    set threat = null
endfunction

function ChooseTarget takes integer team returns integer
    local integer p = 0
    local integer best = -1
    local real distance
    local real score = 999999999
    loop
        exitwhen p == 12
        if TeamOf(p) != team and Alive(Base[p]) then
            set distance = DistanceSq(TeamX[team], TeamY[team], HomeX[p], HomeY[p])
            // Attack a wounded base first, while avoiding diagonal travel.
            set distance = distance * (0.5 + GetWidgetLife(Base[p])/BASE_HP)
            if distance < score then
                set score = distance
                set best = p
            endif
        endif
        set p = p + 1
    endloop
    return best
endfunction

function UpdateRally takes integer team returns nothing
    local integer p = team*3
    local unit threat = null
    set Target[team] = ChooseTarget(team)
    set Defending[team] = false
    if Target[team] >= 0 then
        set RallyX[team] = HomeX[Target[team]]
        set RallyY[team] = HomeY[Target[team]]
    endif
    loop
        exitwhen p >= team*3+3
        if Alive(Base[p]) then
            set threat = EnemyNear(p, HomeX[p], HomeY[p], 1000)
            if threat != null then
                set Defending[team] = true
                set RallyX[team] = GetUnitX(threat)
                set RallyY[team] = GetUnitY(threat)
                set threat = null
                return
            endif
        endif
        set p = p + 1
    endloop
endfunction

function SyncArmyResearch takes integer p returns nothing
    local integer k = 0
    set Attack[p] = GetPlayerTechCount(Player(p), 'Rfat', true)+GetPlayerTechCount(Player(p), 'Rfa2', true)
    set Armor[p] = GetPlayerTechCount(Player(p), 'Rfar', true)+GetPlayerTechCount(Player(p), 'Rfr2', true)
    set Vitality[p] = GetPlayerTechCount(Player(p), 'Rfhp', true)+GetPlayerTechCount(Player(p), 'Rfh2', true)
    set Tier[p] = GetPlayerTechCount(Player(p), 'Rfti', true)
    set WaveRanks[p] = GetPlayerTechCount(Player(p), 'Rfwn', true)
    loop
        exitwhen k == 3
        if not AdvancedUnlocked[p*3+k] and GetPlayerTechCount(Player(p),ArmyResearch[k],true) >= RESEARCH_SOFT_CAP then
            call SetPlayerTechMaxAllowed(Player(p),AdvancedArmyResearch[k],UPGRADE_MAX-RESEARCH_SOFT_CAP)
            set AdvancedUnlocked[p*3+k] = true
        endif
        set k = k+1
    endloop
endfunction

function TroopResearchCost takes integer baseCost, integer stepCost, integer level returns integer
    if level >= RESEARCH_SOFT_CAP then
        return (baseCost+level*stepCost)*ADVANCED_RESEARCH_COST_MULTIPLIER
    endif
    return baseCost+level*stepCost
endfunction

function UpgradeCost takes integer p, integer kind returns integer
    if kind == 0 and Attack[p] < UPGRADE_MAX then
        return TroopResearchCost(ATTACK_COST,ATTACK_COST_STEP,Attack[p])
    elseif kind == 1 and Armor[p] < UPGRADE_MAX then
        return TroopResearchCost(ARMOR_COST,ARMOR_COST_STEP,Armor[p])
    elseif kind == 2 and Vitality[p] < UPGRADE_MAX then
        return HEALTH_COST+Vitality[p]*HEALTH_COST_STEP
    elseif kind == 3 and Tier[p] < 4 then
        return TierCost[Tier[p]+1]
    elseif kind == 4 and Power[p] < 10 then
        return HERO_POWER_COST + Power[p]*HERO_POWER_COST_STEP
    elseif kind == 6 and WaveRanks[p] < WAVE_UPGRADE_MAX then
        return WAVE_UPGRADE_COST + WaveRanks[p]*WAVE_UPGRADE_COST_STEP
    elseif kind == 5 then
        return 150
    endif
    return -1
endfunction

function UpgradeName takes integer kind returns string
    if kind == 0 then
        return "Атака армии +4"
    elseif kind == 1 then
        return "Броня армии +1,5"
    elseif kind == 2 then
        return "Здоровье армии +10%"
    elseif kind == 3 then
        return "Развитие казармы"
    elseif kind == 4 then
        return "Герою: +3 ко всем характеристикам"
    endif
    return "Лечение героя у своей базы"
endfunction

function Buy takes integer p, integer kind returns boolean
    local integer cost
    call SyncArmyResearch(p)
    set cost = UpgradeCost(p, kind)
    if Finished or Lost[p] or not Alive(Base[p]) then
        call Tell(p, "Your barracks are destroyed. You can still command surviving units.")
        return false
    endif
    if cost < 0 then
        call Tell(p, "Maximum level reached.")
        return false
    endif
    if (kind == 4 or kind == 5) and not Alive(Hero[p]) then
        call Tell(p, "Wait for your hero to revive.")
        return false
    endif
    if kind == 5 and (DistanceSq(GetUnitX(Hero[p]), GetUnitY(Hero[p]), HomeX[p], HomeY[p]) > 810000 or GetWidgetLife(Hero[p]) >= GetUnitState(Hero[p], UNIT_STATE_MAX_LIFE)*0.95) then
        call Tell(p, "Healing requires a wounded hero within 900 of your base.")
        return false
    endif
    if GetPlayerState(Player(p), PLAYER_STATE_RESOURCE_GOLD) < cost then
        call Tell(p, "Not enough gold: " + I2S(cost) + " required.")
        return false
    endif
    if kind < 4 or kind == 6 then
        if kind == 6 then
            return IssueImmediateOrderById(Base[p],'Rfwn')
        endif
        // The engine charges gold, queues research and updates existing/new units.
        // Human command-card clicks use exactly the same engine research path.
        if kind < 3 and GetPlayerTechCount(Player(p),ArmyResearch[kind],true) >= RESEARCH_SOFT_CAP then
            return IssueImmediateOrderById(Base[p],AdvancedArmyResearch[kind])
        endif
        return IssueImmediateOrderById(Base[p],ArmyResearch[kind])
    endif
    call AddGold(p, -cost)
    if kind == 4 then
        set Power[p] = Power[p]+1
        call SetHeroStr(Hero[p], GetHeroStr(Hero[p], false)+3, true)
        call SetHeroAgi(Hero[p], GetHeroAgi(Hero[p], false)+3, true)
        call SetHeroInt(Hero[p], GetHeroInt(Hero[p], false)+3, true)
    elseif kind == 5 then
        call SetUnitState(Hero[p], UNIT_STATE_LIFE, GetUnitState(Hero[p], UNIT_STATE_MAX_LIFE))
        call SetUnitState(Hero[p], UNIT_STATE_MANA, GetUnitState(Hero[p], UNIT_STATE_MAX_MANA))
    endif
    call Tell(p, UpgradeName(kind) + " purchased.")
    return true
endfunction

function MenuButton takes integer p, integer slot, string title, integer action returns nothing
    set ShopButton[p*12+slot] = DialogAddButton(Shop[p], title, 0)
    set MenuAction[p*12+slot] = action
endfunction

function ClearMenu takes integer p, string title returns nothing
    local integer k = 0
    call DialogClear(Shop[p])
    call DialogSetMessage(Shop[p], title)
    loop
        exitwhen k == 12
        set ShopButton[p*12+k] = null
        set MenuAction[p*12+k] = -1
        set k = k+1
    endloop
endfunction

function ShowShop takes integer p returns nothing
    if not Bot[p] and Alive(Base[p]) then
        call SelectUnitForPlayerSingle(Base[p], Player(p))
        call Tell(p, "В казарме пять улучшений: атака, броня, здоровье бойцов (до 200), развитие базы и численность волн (+1 воин). Цена указана на каждой кнопке.")
    endif
endfunction

function ResolvedSkill takes unit h, integer skill returns integer
    local integer engineering = GetUnitAbilityLevel(h, 'ANeg')
    if engineering > 3 then
        set engineering = 3
    endif
    if engineering > 0 then
        if skill == 'ANsy' then
            return 'ANs1'+engineering-1
        elseif skill == 'ANcs' then
            return 'ANc1'+engineering-1
        elseif skill == 'ANrg' then
            return 'ANg1'+engineering-1
        endif
    endif
    return skill
endfunction

function GrantHeroPoints takes integer p returns nothing
    local integer level = GetHeroLevel(Hero[p])
    if level > SkillLevel[p] then
        call UnitModifySkillPoints(Hero[p], level-SkillLevel[p])
        set SkillLevel[p] = level
    endif
endfunction

function OnHeroLevel takes nothing returns nothing
    local integer p = GetPlayerId(GetOwningPlayer(GetTriggerUnit()))
    if p < 12 and GetTriggerUnit() == Hero[p] then
        call GrantHeroPoints(p)
    endif
endfunction

function LearnHero takes integer p returns nothing
    local integer level = GetHeroLevel(Hero[p])
    local integer slot = 0
    local integer index = HeroKind[p]*4
    local integer learnSlot
    call GrantHeroPoints(p)
    if level >= 6 then
        call SelectHeroSkill(Hero[p], ResolvedSkill(Hero[p], HeroSkill[index+3]))
    endif
    loop
        exitwhen slot == 3
        set learnSlot = slot
        if Bot[p] then
            set learnSlot = HeroLearnOrder[HeroKind[p]*3+slot]
        endif
        call SelectHeroSkill(Hero[p], ResolvedSkill(Hero[p], HeroSkill[index+learnSlot]))
        set slot = slot+1
    endloop
    if GetUnitAbilityLevel(Hero[p], 'Fatr') < R2I(I2R(level)/12.0) or (GetUnitAbilityLevel(Hero[p],ResolvedSkill(Hero[p],HeroSkill[index])) >= BASIC_SKILL_MAX and GetUnitAbilityLevel(Hero[p],ResolvedSkill(Hero[p],HeroSkill[index+1])) >= BASIC_SKILL_MAX and GetUnitAbilityLevel(Hero[p],ResolvedSkill(Hero[p],HeroSkill[index+2])) >= BASIC_SKILL_MAX and GetUnitAbilityLevel(Hero[p],ResolvedSkill(Hero[p],HeroSkill[index+3])) >= ULTIMATE_SKILL_MAX) then
        call SelectHeroSkill(Hero[p], 'Fatr')
    endif
    if AutoSkill[HeroKind[p]] != 0 and GetUnitAbilityLevel(Hero[p], AutoSkill[HeroKind[p]]) > 0 then
        call IssueImmediateOrder(Hero[p], AutoOrder[HeroKind[p]])
    endif
endfunction

// EXPANSION_MODULE
// CREATIVE_MODULE
function CreateHero takes integer p, integer kind returns nothing
    call ExpansionClear(p)
    call CreativeClear(p)
    set HeroQueued[p] = false
    set HeroLearnQueued[p] = false
    set HeroKind[p] = kind
    call ApplyBotHeroProfile(p)
    set SkillLevel[p] = 1
    set Hero[p] = CreateUnit(Player(p), HeroType[kind], HomeX[p], HomeY[p]-240, 270)
    if Hero[p] == null then
        return
    endif
    set PreviousHeroX[p] = HomeX[p]
    set PreviousHeroY[p] = HomeY[p]-240
    set HeroSector[p] = TeamOf(p)
    call SetHeroLevel(Hero[p], 1, false)
    call PauseUnit(Hero[p], Seconds < WARMUP_SECONDS)
    if Bot[p] then
        set HeroLearnQueued[p] = true
    endif
endfunction

function QueueHero takes integer p, integer kind returns nothing
    set ScheduledHero[p] = kind
    set HeroKind[p] = kind
    call ApplyBotHeroProfile(p)
    set HeroQueued[p] = true
    set HeroLearnQueued[p] = false
endfunction

function ProcessHeroQueue takes nothing returns nothing
    local integer checked = 0
    local integer p
    loop
        exitwhen checked == 12
        set p = HeroQueueCursor
        set HeroQueueCursor = ModuloInteger(HeroQueueCursor+1,12)
        if not Lost[p] and SlotActive[p] and Alive(Base[p]) then
            if HeroQueued[p] then
                call CreateHero(p, ScheduledHero[p])
                if Hero[p] == null then
                    call QueueHero(p, GetRandomInt(0,23))
                endif
                return
            elseif HeroLearnQueued[p] then
                set HeroLearnQueued[p] = false
                if Bot[p] and Alive(Hero[p]) then
                    call LearnHero(p)
                endif
                return
            endif
        else
            set HeroQueued[p] = false
            set HeroLearnQueued[p] = false
        endif
        set checked = checked+1
    endloop
endfunction

function AssignBotChoices takes integer p returns nothing
    set ArmyRace[p] = GetRandomInt(0, 3)
    call CreateHero(p, GetRandomInt(0, HERO_COUNT-1))
endfunction

// Queue repairs, never reroll an existing or dead hero.
function EnsureBotHero takes integer p returns nothing
    if Bot[p] and SlotActive[p] and not Lost[p] and Alive(Base[p]) and not HeroQueued[p] then
        if Hero[p] == null or GetUnitTypeId(Hero[p]) == 0 then
            call QueueHero(p, GetRandomInt(0, HERO_COUNT-1))
        endif
    endif
endfunction

function SelectArmyRace takes integer p, integer choice returns boolean
    if AllRandomMode or Seconds >= WARMUP_SECONDS or choice < 0 or choice > 3 or Lost[p] then
        call Tell(p, "Расу армии можно выбрать только до первого спавна.")
        return false
    endif
    set ArmyRace[p] = choice
    call Tell(p, "Раса армии: " + RaceName[choice])
    return true
endfunction

function SelectRosterHero takes integer p, integer choice returns boolean
    if AllRandomMode or Seconds >= WARMUP_SECONDS or Power[p] > 0 or choice < 0 or choice >= HERO_COUNT or Lost[p] then
        call Tell(p, "Выбор героя закрыт после начала боя или покупки характеристик.")
        return false
    endif
    if Hero[p] != null then
        call RemoveUnit(Hero[p])
    endif
    call CreateHero(p, choice)
    call Tell(p, "Герой: " + HeroName[choice])
    return true
endfunction

function ShowHeroPicker takes integer p, integer page returns nothing
    if AllRandomMode or Seconds >= WARMUP_SECONDS or Lost[p] or Bot[p] then
        call ShowShop(p)
        return
    endif
    call DialogDisplay(Player(p), Shop[p], false)
    if HeroPicker[p] != null then
        call RemoveUnit(HeroPicker[p])
    endif
    set PickerPage[p] = ModuloInteger(page+PICK_PAGE_COUNT, PICK_PAGE_COUNT)
    set HeroPicker[p] = CreateUnit(Player(p), 'fpk0'+PickerPage[p], HomeX[p]+350, HomeY[p]-350, 270)
    call SetUnitInvulnerable(HeroPicker[p], true)
    call SelectUnitForPlayerSingle(HeroPicker[p], Player(p))
    call PanCameraToTimedForPlayer(Player(p), HomeX[p], HomeY[p], 0.25)
    call Tell(p, "Выбери портрет героя. Внизу — страницы и случайный герой. 24 стандартных и 26 авторских героев.")
endfunction

function ShowModes takes integer p returns nothing
    if p != HostPlayer or Seconds > 15 or AllRandomMode then
        call Tell(p, "Режим выбирает первый игрок до 15-й секунды: -ar или -mode.")
        return
    endif
    set ModeDialogOpen = true
    call ClearMenu(p, "РЕЖИМ ИГРЫ — выбор до 15-й секунды")
    call MenuButton(p, 0, "Обычный: выбрать расу и героя", 500)
    call MenuButton(p, 1, "Всё наугад: расы и герои всем", 501)
    call DialogDisplay(Player(p), Shop[p], true)
endfunction

function ShowRaces takes integer p returns nothing
    local integer k = 0
    if AllRandomMode or Seconds >= WARMUP_SECONDS then
        call ShowShop(p)
        return
    endif
    call ClearMenu(p, "ВЫБОР РАСЫ АРМИИ (до начала боя)")
    loop
        exitwhen k == 4
        call MenuButton(p, k, RaceName[k], 100+k)
        set k = k+1
    endloop
    call MenuButton(p, 4, "Случайная раса", 104)
    call MenuButton(p, 5, "Меню армии", 13)
    call MenuButton(p, 6, "Закрыть", 12)
    call DialogDisplay(Player(p), Shop[p], true)
endfunction

function HeroCategory takes integer category returns string
    if category < 4 then
        return RaceName[category]
    endif
    if category == 9 then
        return "Новые механики"
    elseif category == 8 then
        return "Авторские герои IV"
    elseif category == 7 then
        return "Авторские герои III"
    elseif category == 6 then
        return "Авторские герои II"
    elseif category == 5 then
        return "Авторские герои I"
    endif
    return "Нейтральные герои"
endfunction

function ShowHeroGroups takes integer p returns nothing
    local integer k = 0
    if AllRandomMode or Seconds >= WARMUP_SECONDS then
        call ShowShop(p)
        return
    endif
    call ClearMenu(p, "ВЫБОР ГЕРОЯ: 50 героев")
    loop
        exitwhen k == 10
        call MenuButton(p, k, HeroCategory(k), 200+k)
        set k = k+1
    endloop
    call MenuButton(p, 10, "Случайный герой", 399)
    call MenuButton(p, 11, "Меню армии", 13)
    call DialogDisplay(Player(p), Shop[p], true)
endfunction

function ShowHeroes takes integer p, integer category returns nothing
    local integer k = 0
    local integer slot = 0
    if AllRandomMode or Seconds >= WARMUP_SECONDS then
        call ShowShop(p)
        return
    endif
    call ClearMenu(p, "ВЫБОР ГЕРОЯ: " + HeroCategory(category))
    loop
        exitwhen k == HERO_COUNT
        if HeroGroup[k] == category then
            call MenuButton(p, slot, HeroName[k], 300+k)
            set slot = slot+1
        endif
        set k = k+1
    endloop
    call MenuButton(p, slot, "Назад к расам героев", 11)
    call MenuButton(p, slot+1, "Случайный герой", 399)
    call MenuButton(p, slot+2, "Закрыть", 12)
    call DialogDisplay(Player(p), Shop[p], true)
endfunction

function SetAllRandom takes integer requester returns nothing
    local integer p = 0
    if requester != HostPlayer or Seconds > 15 or AllRandomMode then
        return
    endif
    loop
        exitwhen p == 12
        if Power[p] > 0 then
            call Tell(requester, "Режим уже нельзя менять после покупки характеристик героя.")
            return
        endif
        set p = p+1
    endloop
    set AllRandomMode = true
    set p = 0
    loop
        exitwhen p == 12
        if not Lost[p] then
            call RemoveUnit(Hero[p])
            set Hero[p] = null
            set ArmyRace[p] = GetRandomInt(0,3)
            call QueueHero(p, GetRandomInt(0,HERO_COUNT-1))
            if HeroPicker[p] != null then
                call RemoveUnit(HeroPicker[p])
                set HeroPicker[p] = null
            endif
            call DialogDisplay(Player(p), Shop[p], false)
            call Tell(p, "Всё наугад: " + RaceName[ArmyRace[p]] + " / " + HeroName[HeroKind[p]])
        endif
        set p = p+1
    endloop
    call Say("Режим ВСЁ НАУГАД: каждому случайная раса армии и герой, включая авторских.")
endfunction

function OnHeroPick takes nothing returns nothing
    local unit token = GetTrainedUnit()
    local integer p = GetPlayerId(GetOwningPlayer(GetTriggerUnit()))
    local integer k = 0
    if p < 12 and not Bot[p] and GetTriggerUnit() == HeroPicker[p] then
        loop
            exitwhen k == HERO_COUNT or GetUnitTypeId(token) == PickToken[k]
            set k = k+1
        endloop
        call RemoveUnit(token)
        if k < HERO_COUNT then
            call SelectRosterHero(p, k)
            call ShowShop(p)
        endif
    endif
    set token = null
endfunction

function OnPickerSpell takes nothing returns nothing
    local integer p = GetPlayerId(GetOwningPlayer(GetTriggerUnit()))
    local integer spell = GetSpellAbilityId()
    if p >= 12 or Bot[p] or GetTriggerUnit() != HeroPicker[p] then
        return
    endif
    if spell == 'Fprv' then
        call ShowHeroPicker(p, PickerPage[p]-1)
    elseif spell == 'Fnxt' then
        call ShowHeroPicker(p, PickerPage[p]+1)
    elseif spell == 'Frnd' then
        call SelectRosterHero(p, GetRandomInt(0, HERO_COUNT-1))
        call ShowShop(p)
    elseif spell == 'Fmod' then
        call ShowModes(p)
    endif
endfunction

function OnShop takes nothing returns nothing
    local integer p = GetPlayerId(GetTriggerPlayer())
    local integer k = 0
    local integer action = -1
    if p >= 12 or Finished or Bot[p] then
        return
    endif
    loop
        exitwhen k == 12
        if GetClickedButton() == ShopButton[p*12+k] then
            set action = MenuAction[p*12+k]
        endif
        set k = k+1
    endloop
    if action == 500 then
        set ModeDialogOpen = false
        call ShowRaces(p)
    elseif action == 501 then
        set ModeDialogOpen = false
        call SetAllRandom(p)
    elseif action == 10 then
        call ShowRaces(p)
    elseif action == 11 then
        call ShowHeroPicker(p, 0)
    elseif action == 13 then
        call ShowShop(p)
    elseif action >= 100 and action <= 104 then
        if action == 104 then
            set action = 100+GetRandomInt(0, 3)
        endif
        call SelectArmyRace(p, action-100)
        call ShowHeroPicker(p, 0)
    elseif action >= 200 and action < 210 then
        call ShowHeroes(p, action-200)
    elseif action == 399 then
        call SelectRosterHero(p, GetRandomInt(0, HERO_COUNT-1))
        call ShowShop(p)
    elseif action >= 300 and action < 300+HERO_COUNT then
        call SelectRosterHero(p, action-300)
        call ShowShop(p)
    endif
endfunction

function OnResearch takes nothing returns nothing
    local integer p = GetPlayerId(GetOwningPlayer(GetTriggerUnit()))
    local integer oldTier = Tier[p]
    if p < 12 and GetTriggerUnit() == Base[p] then
        call SyncArmyResearch(p)
        if Tier[p] > oldTier then
            set TierSavings[p] = IMaxBJ(0, TierSavings[p]-TierCost[Tier[p]])
        endif
        call Tell(p, "Исследование завершено: атака " + I2S(Attack[p]) + ", броня " + I2S(Armor[p]) + ", здоровье " + I2S(Vitality[p]) + ", ступень базы " + I2S(Tier[p]+1)+", бойцов в волне "+I2S(SPAWN_UNITS+WaveRanks[p]))
    endif
endfunction

function SpawnWave takes integer p returns nothing
    local integer n = 0
    local integer count = CountUnitsInGroup(Army[p])
    local real x
    local real y
    local real across
    local real forward
    local integer team = TeamOf(p)
    local integer id
    local unit u
    loop
        exitwhen n >= SPAWN_UNITS+WaveRanks[p] or count >= ARMY_CAP
        set id = ArmyType[ArmyRace[p]*5+Tier[p]]
        set across = I2R(ModuloInteger(n,3)-1)*90.
        set forward = 220.+I2R(n/3)*90.
        set x = across
        set y = forward
        if team == 1 then
            set x = -forward
            set y = across
        elseif team == 2 then
            set x = -across
            set y = -forward
        elseif team == 3 then
            set x = forward
            set y = -across
        endif
        set u = CreateUnit(Player(p), id, HomeX[p]+x, HomeY[p]+y, 270)
        // 11..15: advancing through center; 1..5: reached the center.
        call SetUnitUserData(u, Tier[p]+11)
        call GroupAddUnit(Army[p], u)
        if Defending[TeamOf(p)] then
            call IssuePointOrder(u, "attack", RallyX[TeamOf(p)], RallyY[TeamOf(p)])
        else
            call IssuePointOrder(u, "attack", 0, 0)
        endif
        set count = count+1
        set n = n+1
    endloop
    set u = null
endfunction

function CommandArmy takes integer p, boolean forceOrder returns nothing
    local unit u
    local integer t = TeamOf(p)
    local boolean arrived
    // Reconcile resurrected troops as well as newly summoned elementals.
    // Summons receive orders but do not occupy the trained-army cap.
    call GroupClear(Army[p])
    call GroupEnumUnitsOfPlayer(Work, Player(p), null)
    loop
        set u = FirstOfGroup(Work)
        exitwhen u == null
        call GroupRemoveUnit(Work, u)
        if Alive(u) and (IsArmyUnit(u) or IsUnitType(u, UNIT_TYPE_SUMMONED)) then
            if IsArmyUnit(u) then
                call GroupAddUnit(Army[p], u)
            endif
            set arrived = false
            if GetUnitUserData(u) > 10 and DistanceSq(GetUnitX(u), GetUnitY(u), 0, 0) < 2250000 then
                call SetUnitUserData(u, GetUnitUserData(u)-10)
                set arrived = true
            endif
            // Humans can override orders; -auto resumes automatic commands.
            if forceOrder or Bot[p] or AutoArmy[p] then
                // Do not reset a swing/cast when already fighting nearby.
                if forceOrder or arrived or Defending[t] or GetUnitCurrentOrder(u) == 0 then
                    if GetUnitUserData(u) > 10 and not Defending[t] then
                        call IssuePointOrder(u, "attack", 0, 0)
                    else
                        call IssuePointOrder(u, "attack", RallyX[t], RallyY[t])
                    endif
                endif
            endif
        else
            call GroupRemoveUnit(Army[p], u)
        endif
    endloop
    set u = null
endfunction

function GearFamily takes integer p, integer slot returns integer
    return HeroGear[HeroKind[p]*6+slot]
endfunction

function DesiredGear takes integer p returns integer
    return GearFamily(p, ModuloInteger(GearProgress[p], 6))*3+R2I(I2R(GearProgress[p])/6.0)
endfunction

function HeroItem takes unit h, integer id returns item
    local integer slot = 0
    local item it
    loop
        exitwhen slot == 6
        set it = UnitItemInSlot(h, slot)
        if it != null and GetItemTypeId(it) == id then
            set ReturnedItem = it
            set it = null
            return ReturnedItem
        endif
        set slot = slot+1
    endloop
    set it = null
    set ReturnedItem = null
    return null
endfunction

function DesiredSuper takes integer p returns integer
    local integer choice = SuperBuild[HeroKind[p]*6+SuperProgress[p]]
    // Do not waste the attack-speed purchase when agility already reaches the cap.
    if choice == 4 and GetHeroAgi(Hero[p],true) >= 200 then
        if HeroPrimary[HeroKind[p]] == 1 then
            return 2
        endif
        return 1
    endif
    return choice
endfunction

function RegularGearCost takes integer raw returns integer
    local integer k = 0
    loop
        exitwhen k == 36
        if GearId[k] == raw then
            return GearCost[k]
        endif
        set k = k+1
    endloop
    return 0
endfunction

function BotTierReserve takes integer p returns integer
    if Tier[p] < 4 then
        return IMinBJ(TierSavings[p],TierCost[Tier[p]+1])
    endif
    return 0
endfunction

function BotSupremeShop takes integer p returns boolean
    local integer choice
    local integer team = TeamOf(p)
    local integer slot = 0
    local integer price
    local integer cheapest = 2147480000
    local boolean room = false
    local unit h = Hero[p]
    local item old = null
    local item candidate = null
    if SuperProgress[p] >= 6 or not Alive(h) or UnitInventorySize(h) < 6 then
        set h = null
        return false
    endif
    set choice = DesiredSuper(p)
    if HeroItem(h, SuperId[choice]) != null then
        set SuperProgress[p] = SuperProgress[p]+1
        set GearSavings[p] = IMaxBJ(0, GearSavings[p]-SuperCost[choice])
        set h = null
        return false
    endif
    if GearSavings[p] < SuperCost[choice] or GetPlayerState(Player(p), PLAYER_STATE_RESOURCE_GOLD)-BotTierReserve(p) < SuperCost[choice] then
        set h = null
        return false
    endif
    if DistanceSq(GetUnitX(h),GetUnitY(h),SuperX[team],SuperY[team]) > 160000 then
        call IssuePointOrder(h,"move",SuperX[team],SuperY[team])
        set h = null
        return true
    endif
    loop
        exitwhen slot == 6
        set candidate = UnitItemInSlot(h,slot)
        if candidate == null then
            set room = true
        else
            set price = RegularGearCost(GetItemTypeId(candidate))
            if price > 0 and price < cheapest then
                set old = candidate
                set cheapest = price
            endif
        endif
        set slot = slot+1
    endloop
    if not room and old != null then
        set room = UnitDropItemTarget(h,old,SupremeShop[team])
    endif
    if room then
        call IssueNeutralTargetOrder(Player(p),SupremeShop[team],"neutralinteract",h)
        call IssueNeutralImmediateOrderById(Player(p),SupremeShop[team],SuperId[choice])
        if HeroItem(h,SuperId[choice]) != null then
            set SuperProgress[p] = SuperProgress[p]+1
            set GearSavings[p] = IMaxBJ(0,GearSavings[p]-SuperCost[choice])
        endif
    endif
    set candidate = null
    set old = null
    set h = null
    return room
endfunction

function BotShop takes integer p returns boolean
    local integer index
    local integer shopIndex
    local integer slot = 0
    local boolean room = false
    local item old = null
    local unit h = Hero[p]
    if GearProgress[p] >= 18 then
        set h = null
        return BotSupremeShop(p)
    endif
    if not Alive(h) or UnitInventorySize(h) < 6 then
        set h = null
        return false
    endif
    set index = DesiredGear(p)
    if HeroItem(h, GearId[index]) != null then
        set GearProgress[p] = GearProgress[p]+1
        set GearSavings[p] = IMaxBJ(0, GearSavings[p]-GearCost[index])
        set h = null
        return false
    endif
    if GearSavings[p] < GearCost[index] or GetPlayerState(Player(p), PLAYER_STATE_RESOURCE_GOLD)-BotTierReserve(p) < GearCost[index] then
        set h = null
        return false
    endif
    set shopIndex = TeamOf(p)*5+GearShop[index]
    if DistanceSq(GetUnitX(h), GetUnitY(h), ShopX[shopIndex], ShopY[shopIndex]) > 160000 then
        call IssuePointOrder(h, "move", ShopX[shopIndex], ShopY[shopIndex])
        set h = null
        return true
    endif
    loop
        exitwhen slot == 6
        if UnitItemInSlot(h, slot) == null then
            set room = true
        endif
        set slot = slot+1
    endloop
    if GearProgress[p] >= 6 then
        set old = HeroItem(h, GearId[index-1])
        if old != null then
            // Normal shop sale, including the native resale price.
            set room = UnitDropItemTarget(h, old, FortressShop[shopIndex])
        endif
    endif
    if room then
        call IssueNeutralTargetOrder(Player(p), FortressShop[shopIndex], "neutralinteract", h)
        // Native stock, gold price and item delivery also apply to bots.
        call IssueNeutralImmediateOrderById(Player(p), FortressShop[shopIndex], GearId[index])
        if HeroItem(h, GearId[index]) != null then
            set GearProgress[p] = GearProgress[p]+1
            set GearSavings[p] = IMaxBJ(0, GearSavings[p]-GearCost[index])
        endif
    endif
    set old = null
    set h = null
    return room
endfunction

function TryBotShopping takes integer p returns boolean
    local integer previousGear = GearProgress[p]
    local integer previousSuper = SuperProgress[p]
    if ModuloInteger(Seconds+p*3,90) >= 15 and ShoppingUntil[p] <= Seconds then
        return false
    endif
    if not BotShop(p) then
        set ShoppingUntil[p] = 0
        return false
    endif
    if GearProgress[p] != previousGear or SuperProgress[p] != previousSuper then
        set ShoppingUntil[p] = 0
    elseif ShoppingUntil[p] <= Seconds then
        set ShoppingUntil[p] = Seconds+45
    endif
    return true
endfunction

function BotResearch takes integer p, integer kind returns boolean
    local integer reserve = 0
    if GearProgress[p] < 18 then
        set reserve = IMinBJ(GearSavings[p], GearCost[DesiredGear(p)])
    elseif SuperProgress[p] < 6 then
        set reserve = IMinBJ(GearSavings[p], SuperCost[DesiredSuper(p)])
    endif
    if kind != 3 then
        // Protect partial savings too, otherwise frequent research drains them.
        set reserve = reserve+BotTierReserve(p)
    endif
    if GetPlayerState(Player(p), PLAYER_STATE_RESOURCE_GOLD)-UpgradeCost(p, kind) >= reserve then
        return Buy(p, kind)
    endif
    return false
endfunction

function BotBuy takes integer p returns nothing
    if GetUnitCurrentOrder(Base[p]) != 0 then
        return
    endif
    call SyncArmyResearch(p)
    // Develop the barracks early; balance all three troop stats afterwards.
    // No free gold or instant upgrades: use the native research queue.
    if Tier[p] < 4 and Attack[p] >= Tier[p]+1 and Armor[p] >= Tier[p]+1 and Vitality[p] >= Tier[p]+1 then
        if BotResearch(p, 3) then
            return
        endif
    endif
    if WaveRanks[p] < IMinBJ(WAVE_UPGRADE_MAX,(Attack[p]+Armor[p]+Vitality[p])/6) then
        if BotResearch(p,6) then
            return
        endif
    endif
    // Rotate all troop parameters; health may never fall behind damage/armor.
    if Vitality[p] < UPGRADE_MAX and (Vitality[p] < Attack[p] or Vitality[p] < Armor[p]) then
        call BotResearch(p,2)
    elseif Attack[p] < UPGRADE_MAX and Attack[p] <= Armor[p] then
        call BotResearch(p,0)
    elseif Armor[p] < UPGRADE_MAX then
        call BotResearch(p,1)
    elseif Vitality[p] < UPGRADE_MAX then
        call BotResearch(p,2)
    elseif Tier[p] < 4 then
        call BotResearch(p, 3)
    elseif Power[p] < 10 then
        call BotResearch(p, 4)
    endif
endfunction

// Heal targeting follows the unit's actual race, independently of army choice.
function FindBotAlly takes integer p, integer mode returns unit
    local unit u
    local unit best = null
    local real lowest = 0.75
    local real health
    call GroupEnumUnitsInRange(Scan, GetUnitX(Hero[p]), GetUnitY(Hero[p]), 650, null)
    loop
        set u = FirstOfGroup(Scan)
        exitwhen u == null
        call GroupRemoveUnit(Scan, u)
        if Alive(u) and IsUnitAlly(u, Player(p)) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) then
            if (mode != 3 or (u != Hero[p] and not IsUnitType(u, UNIT_TYPE_UNDEAD))) and (mode != 7 or (u != Hero[p] and IsUnitType(u, UNIT_TYPE_UNDEAD))) then
                set health = GetWidgetLife(u)/GetUnitState(u, UNIT_STATE_MAX_LIFE)
                if health < lowest then
                    set lowest = health
                    set best = u
                endif
            endif
        endif
    endloop
    set u = null
    set ReturnedUnit = best
    set best = null
    return ReturnedUnit
endfunction

// CREATIVE_AI
function TryBotSpell takes integer p, unit enemy returns boolean
    local integer slot = 0
    local integer index
    local integer mode
    local unit ally = null
    local boolean cast = false
    local unit h = Hero[p]
    local real health = GetWidgetLife(h)/GetUnitState(h, UNIT_STATE_MAX_LIFE)
    if HeroKind[p] >= 46 then
        set h = null
        return TryCreativeBotSpell(p,enemy)
    endif
    loop
        exitwhen slot == 4
        set index = HeroKind[p]*4+slot
        set mode = SpellMode[index]
        if SpellAbility[index] != 0 and GetUnitAbilityLevel(h, ResolvedSkill(h, SpellAbility[index])) > 0 then
            if mode == 3 or mode == 6 or mode == 7 or mode == 10 then
                set ally = FindBotAlly(p, mode)
                if ally != null then
                    if mode == 10 then
                        set cast = IssuePointOrder(h, SpellOrder[index], GetUnitX(ally), GetUnitY(ally))
                    else
                        set cast = IssueTargetOrder(h, SpellOrder[index], ally)
                    endif
                endif
            elseif enemy != null then
                if (mode == 11 and GetUnitAbilityLevel(h, 'BEim') == 0 and GetUnitState(h, UNIT_STATE_MANA) > 30) or mode == 0 or (mode == 4 and health < 0.55) or (mode == 5 and DistanceSq(GetUnitX(h), GetUnitY(h), GetUnitX(enemy), GetUnitY(enemy)) < 160000) then
                    set cast = IssueImmediateOrder(h, SpellOrder[index])
                elseif mode == 1 or (mode == 8 and not IsUnitType(enemy, UNIT_TYPE_UNDEAD)) or (mode == 9 and not IsUnitType(enemy, UNIT_TYPE_HERO) and not IsUnitType(enemy, UNIT_TYPE_SUMMONED)) then
                    set cast = IssueTargetOrder(h, SpellOrder[index], enemy)
                elseif mode == 2 then
                    set cast = IssuePointOrder(h, SpellOrder[index], GetUnitX(enemy), GetUnitY(enemy))
                endif
            endif
            if cast then
                set CastUntil[p] = Seconds+SpellHold[index]
                set h = null
                set ally = null
                return true
            endif
        endif
        set slot = slot+1
    endloop
    set h = null
    set ally = null
    return false
endfunction

// BOT_AI_MODULE

function BotHero takes integer p returns nothing
    local unit h = Hero[p]
    local unit enemy = null
    local unit anchor = null
    local real health
    local integer team = TeamOf(p)
    local integer role = HeroBotRole[HeroKind[p]]
    local real threshold = BotRetreatHP[role]
    local boolean danger
    if not Alive(h) then
        set h = null
        return
    endif
    set health = GetWidgetLife(h)/GetUnitState(h,UNIT_STATE_MAX_LIFE)
    // Protect channelled spells; only a critical health emergency interrupts them.
    if CastUntil[p] > Seconds and health >= .20 then
        set h = null
        return
    endif
    call LearnHero(p)
    set enemy = BotCombatScan(p)
    call PlanBotTeam(team)
    if BotStyle[p] == 1 then
        set threshold = threshold+.04
    elseif BotStyle[p] == 2 then
        set threshold = threshold-.03
    endif
    set danger = BotEnemyPower[p] > BotAlliedPower[p]*BotDangerRatio[role] and BotEnemyPower[p] > 7.
    if BotUseSupplies(p) then
        set h = null
        set enemy = null
        return
    endif
    if health < threshold or (RetreatUntil[p] > Seconds and health < .85) or danger then
        set BotAttackTarget[p] = null
        set RetreatUntil[p] = Seconds+6
        set anchor = BotAllyAnchor(p)
        if HeroKind[p] == 0 then
            call IssueImmediateOrder(h,"divineshield")
        elseif HeroKind[p] == 4 then
            call IssueImmediateOrder(h,"windwalk")
        endif
        if health >= threshold+.15 and anchor != null and not BotTowerDanger[p] and (enemy == null or DistanceSq(GetUnitX(anchor),GetUnitY(anchor),GetUnitX(enemy),GetUnitY(enemy)) > DistanceSq(GetUnitX(h),GetUnitY(h),GetUnitX(enemy),GetUnitY(enemy))) then
            call IssuePointOrder(h,"move",GetUnitX(anchor),GetUnitY(anchor))
        elseif health >= threshold+.15 and BotTowerDanger[p] and DistanceSq(GetUnitX(h),GetUnitY(h),0,0) > 4840000 then
            call IssuePointOrder(h,"move",0,0)
        else
            call IssuePointOrder(h,"move",FortressX[team],FortressY[team])
        endif
        if Alive(Base[p]) and DistanceSq(GetUnitX(h),GetUnitY(h),HomeX[p],HomeY[p]) < 500000 and health < .5 then
            call Buy(p,5)
        endif
        set h = null
        set enemy = null
        set anchor = null
        return
    endif
    // A timed human instruction temporarily postpones shopping, not emergencies.
    if health >= .5 and TeamOrderUntil[team] <= Seconds and not Defending[team] and (BotBuySupplies(p) or TryBotShopping(p)) then
        set BotAttackTarget[p] = null
        set h = null
        set enemy = null
        return
    endif
    if TryBotSpell(p,enemy) then
        set h = null
        set enemy = null
        return
    endif
    if enemy != null then
        if BotAttackTarget[p] != enemy or GetUnitCurrentOrder(h) == 0 then
            call IssueTargetOrder(h,"attack",enemy)
            set BotAttackTarget[p] = enemy
        endif
    else
        set BotAttackTarget[p] = null
        if Defending[team] then
            call IssuePointOrder(h,"attack",RallyX[team],RallyY[team])
        elseif TeamOrderUntil[team] > Seconds then
            if TeamOrder[team] == 1 and Alive(Hero[TeamLeader[team]]) then
                call IssuePointOrder(h,"attack",GetUnitX(Hero[TeamLeader[team]]),GetUnitY(Hero[TeamLeader[team]]))
            elseif TeamOrder[team] == 2 then
                call IssuePointOrder(h,"attack",FortressX[team],FortressY[team])
            elseif TeamOrder[team] == 3 then
                call IssuePointOrder(h,"attack",RallyX[team],RallyY[team])
            else
                call IssuePointOrder(h,"attack",0,0)
            endif
        elseif TeamPushUntil[team] > Seconds then
            call IssuePointOrder(h,"attack",RallyX[team],RallyY[team])
        else
            call IssuePointOrder(h,"attack",0,0)
        endif
    endif
    set h = null
    set enemy = null
endfunction

// Separate static trigger threads keep large battles below Classic JASS op limits.
function BotThink takes nothing returns nothing
    local integer p = 0
    loop
        exitwhen p == 12
        if GetTriggeringTrigger() == BotThinkTrigger[p] then
            call BotHero(p)
            return
        endif
        set p = p+1
    endloop
endfunction

function FinishIfWon takes nothing returns nothing
    local integer t = 0
    local integer aliveTeams = 0
    local integer winner = -1
    local integer p
    loop
        exitwhen t == 4
        if not TeamLost[t] then
            set aliveTeams = aliveTeams+1
            set winner = t
        endif
        set t = t+1
    endloop
    if aliveTeams <= 1 then
        set Finished = true
        if winner >= 0 then
            call Say("Team " + I2S(winner+1) + " wins Four Fronts Frenzy!")
        else
            call Say("Draw: all barracks were destroyed.")
        endif
        set p = 0
        loop
            exitwhen p == 12
            call DialogDisplay(Player(p), Shop[p], false)
            if SlotActive[p] and not Bot[p] then
                if TeamOf(p) == winner then
                    call CustomVictoryBJ(Player(p), true, true)
                else
                    call CustomDefeatBJ(Player(p), "Your team's barracks were destroyed.")
                endif
            endif
            set p = p+1
        endloop
    endif
endfunction

function CheckTeam takes integer team returns nothing
    local integer p = team*3
    local boolean hasBase = false
    local unit u
    loop
        exitwhen p == team*3+3
        if Alive(Base[p]) then
            set hasBase = true
        endif
        set p = p+1
    endloop
    if not hasBase then
        set TeamLost[team] = true
        set p = team*3
        loop
            exitwhen p == team*3+3
            set Lost[p] = true
            call GroupEnumUnitsOfPlayer(Work, Player(p), null)
            loop
                set u = FirstOfGroup(Work)
                exitwhen u == null
                call GroupRemoveUnit(Work, u)
                call RemoveUnit(u)
            endloop
            set p = p+1
        endloop
        call Say("Team " + I2S(team+1) + " has been eliminated.")
    endif
    call FinishIfWon()
    set u = null
endfunction

function ShowGoldReward takes integer p, unit victim, integer amount returns nothing
    local texttag label
    if Bot[p] then
        return
    endif
    set label = CreateTextTag()
    call SetTextTagText(label, "+"+I2S(amount), 0.023)
    call SetTextTagPosUnit(label, victim, 35)
    call SetTextTagColor(label, 255, 220, 40, 255)
    call SetTextTagVelocity(label, 0, 0.04)
    call SetTextTagPermanent(label, false)
    call SetTextTagLifespan(label, 1.8)
    call SetTextTagFadepoint(label, 1.0)
    // Only visibility is local; creation and all gameplay remain synchronized.
    call SetTextTagVisibility(label, GetLocalPlayer() == Player(p))
    set label = null
endfunction

function OnDeath takes nothing returns nothing
    local unit dead = GetTriggerUnit()
    local unit killer = GetKillingUnit()
    local integer p = GetPlayerId(GetOwningPlayer(dead))
    local integer k = -1
    local integer reward = 0
    local integer goldReward = 0
    call ExpansionOnDeath(dead,killer)
    if IsUnitType(dead,UNIT_TYPE_HERO) and dead == Hero[GetPlayerId(GetOwningPlayer(dead))] then
        call CreativeClear(GetPlayerId(GetOwningPlayer(dead)))
    endif
    if Finished or p >= 12 then
        set dead = null
        set killer = null
        return
    endif
    if dead != Hero[p] and not IsUnitType(dead, UNIT_TYPE_STRUCTURE) then
        call GroupAddUnit(CorpseRing[ModuloInteger(Seconds+CORPSE_SECONDS, CORPSE_SECONDS+1)], dead)
    endif
    if killer != null then
        set k = GetPlayerId(GetOwningPlayer(killer))
    endif
    if dead == Base[p] then
        set reward = 300
        call Say(GetPlayerName(Player(p)) + " lost their barracks!")
    elseif dead == Hero[p] then
        set reward = 100 + 15*GetHeroLevel(dead)
        set Respawn[p] = HERO_RESPAWN_SECONDS
    elseif dead == Bastion[p] then
        set reward = 250
    elseif dead == Tower[p] then
        set reward = 80
    elseif IsArmyUnit(dead) then
        set reward = 6 + ModuloInteger(GetUnitUserData(dead), 10)*2
        call GroupRemoveUnit(Army[p], dead)
    endif
    if k >= 0 and k < 12 and TeamOf(k) != TeamOf(p) and reward > 0 then
        set goldReward = R2I(I2R(reward)*KILL_GOLD_MULTIPLIER)
        if dead == TransmuteTarget[k] then
            set goldReward = 0
        endif
        if goldReward > 0 then
            call AddGold(k, goldReward)
            call ShowGoldReward(k, dead, goldReward)
        endif
        set Kills[k] = Kills[k]+1
        // Nearby hero receives additional deterministic experience even above melee level 5.
        if Alive(Hero[k]) and DistanceSq(GetUnitX(Hero[k]), GetUnitY(Hero[k]), GetUnitX(dead), GetUnitY(dead)) < 1440000 then
            call AddHeroXP(Hero[k], R2I(I2R(reward)*2.0*EXPERIENCE_MULTIPLIER), true)
        endif
    endif
    // Pet gold is independent of ordinary bounty/XP and native Transmute rewards.
    if k >= 0 and k < 12 and TeamOf(k) != TeamOf(p) and dead != TransmuteTarget[k] then
        set goldReward = PetKillGold(dead)
        if goldReward > 0 then
            call AddGold(k,goldReward)
            call ShowGoldReward(k,dead,goldReward)
        endif
    endif
    if dead == Base[p] then
        call CheckTeam(TeamOf(p))
    endif
    set dead = null
    set killer = null
endfunction

// SPELL_BALANCE_MODULE
function OnTransmute takes nothing returns nothing
    local unit caster = GetTriggerUnit()
    local integer p = GetPlayerId(GetOwningPlayer(caster))
    local integer rank
    if p >= 12 or Finished or caster != Hero[p] or GetSpellAbilityId() != 'ANtm' then
        set caster = null
        return
    endif
    if GetTriggerEventId() == EVENT_PLAYER_UNIT_SPELL_CAST then
        // Capture before native resolution, even if removal/death precedes EFFECT.
        set TransmuteTarget[p] = GetSpellTargetUnit()
        set TransmuteReward[p] = 0
    elseif GetTriggerEventId() == EVENT_PLAYER_UNIT_SPELL_EFFECT then
        if TransmuteTarget[p] == null then
            set TransmuteTarget[p] = GetSpellTargetUnit()
        endif
        set rank = GetUnitAbilityLevel(caster,'ANtm')
        set TransmuteReward[p] = TRANSMUTE_GOLD_BASE+TRANSMUTE_GOLD_STEP*(rank-1)
    elseif GetTriggerEventId() == EVENT_PLAYER_UNIT_SPELL_FINISH then
        // Native Transmute removes its victim. No award for a live/invalid target.
        if TransmuteTarget[p] != null and (GetUnitTypeId(TransmuteTarget[p]) == 0 or not Alive(TransmuteTarget[p])) and TransmuteReward[p] > 0 then
            call AddGold(p,TransmuteReward[p])
            call ShowGoldReward(p,caster,TransmuteReward[p])
        endif
        set TransmuteTarget[p] = null
        set TransmuteReward[p] = 0
    else
        // ENDCAST also fires on interruption; release handles without a reward.
        set TransmuteTarget[p] = null
        set TransmuteReward[p] = 0
    endif
    set caster = null
endfunction

function OnLeave takes nothing returns nothing
    local integer p = GetPlayerId(GetTriggerPlayer())
    if p < 12 and not Lost[p] then
        if not Bot[p] then
            call AssignBotTactic(p)
        endif
        set Bot[p] = true
    call ApplyBotHeroProfile(p)
        set AutoArmy[p] = true
        call SetPlayerController(Player(p), MAP_CONTROL_COMPUTER)
        call Say(GetPlayerName(Player(p)) + ": bot has taken over.")
    endif
endfunction

function OnChat takes nothing returns nothing
    local integer p = GetPlayerId(GetTriggerPlayer())
    local string command = StringCase(GetEventPlayerChatString(), false)
    local integer kind = -1
    if p >= 12 or Finished then
        return
    endif
    if command == "-shop" then
        call ShowShop(p)
    elseif command == "-race" then
        call ShowRaces(p)
    elseif command == "-hero" then
        call ShowHeroPicker(p, 0)
    elseif command == "-herolist" then
        call ShowHeroGroups(p)
    elseif command == "-ar" then
        call SetAllRandom(p)
    elseif command == "-mode" then
        call ShowModes(p)
    elseif command == "-attack" then
        call Buy(p, 0)
    elseif command == "-armor" then
        call Buy(p, 1)
    elseif command == "-tier" then
        call Buy(p, 3)
    elseif command == "-hp" then
        call Buy(p, 2)
    elseif command == "-wave" then
        call Buy(p,6)
    elseif command == "-supplies" then
        call SelectUnitForPlayerSingle(UtilityShop[TeamOf(p)],Player(p))
        call PanCameraToTimedForPlayer(Player(p),UtilityX[TeamOf(p)],UtilityY[TeamOf(p)],.25)
    elseif command == "-spawn" then
        call Tell(p,"Волна: "+I2S(SPAWN_UNITS+WaveRanks[p])+" бойцов раз в "+I2S(SPAWN_SECONDS)+" секунд. -wave: улучшить численность.")
    elseif command == "-items" then
        call SelectUnitForPlayerSingle(EquipmentShop, Player(p))
        call PanCameraToTimedForPlayer(Player(p), 0, 640, 0.25)
    elseif command == "-supreme" then
        call SelectUnitForPlayerSingle(SupremeShop[TeamOf(p)],Player(p))
        call PanCameraToTimedForPlayer(Player(p),SuperX[TeamOf(p)],SuperY[TeamOf(p)],0.25)
    elseif command == "-potions" then
        call SelectUnitForPlayerSingle(PotionShop,Player(p))
        call PanCameraToTimedForPlayer(Player(p),0,-640,0.25)
    elseif command == "-books" then
        call SelectUnitForPlayerSingle(BookShop[p],Player(p))
        call PanCameraToTimedForPlayer(Player(p),BookX[p],BookY[p],0.25)
    elseif command == "-power" then
        call Buy(p, 4)
    elseif command == "-heal" then
        call Buy(p, 5)
    elseif command == "-auto" then
        set AutoArmy[p] = not AutoArmy[p]
        if AutoArmy[p] then
            call Tell(p, "Army auto-orders ON. Hero remains under your control.")
        else
            call Tell(p, "Army auto-orders OFF. New waves still rally to battle.")
        endif
    elseif command == "-follow" then
        call BotTeamCommand(p,1)
    elseif command == "-defend" then
        call BotTeamCommand(p,2)
    elseif command == "-push" then
        call BotTeamCommand(p,3)
    elseif command == "-regroup" then
        call BotTeamCommand(p,4)
    elseif command == "-free" then
        call BotTeamCommand(p,0)
        set TeamOrderUntil[TeamOf(p)] = 0
    elseif command == "-ai" then
        call Tell(p,"Союзные боты: -follow за мной | -defend защита | -push атака базы | -regroup сбор в центре | -free самостоятельная игра. Приказы на 90 секунд; экстренное отступление важнее.")
    elseif command == "-go" then
        call CommandArmy(p, true)
    elseif command == "-status" then
        call Tell(p, RaceName[ArmyRace[p]] + " | " + TierName[ArmyRace[p]*5+Tier[p]] + " | attack " + I2S(Attack[p]) + " | armor " + I2S(Armor[p]) + " | hp " + I2S(Vitality[p]) + " | wave size "+I2S(SPAWN_UNITS+WaveRanks[p])+" | spawn " + I2S(SPAWN_SECONDS) + "s | army " + I2S(CountUnitsInGroup(Army[p])) + "/" + I2S(ARMY_CAP))
    elseif SubString(command, 0, 6) == "-race " then
        if command == "-race random" then
            call SelectArmyRace(p, GetRandomInt(0, 3))
        else
            set kind = 0
            loop
                exitwhen kind == 4
                if command == "-race " + RaceAlias[kind] then
                    call SelectArmyRace(p, kind)
                    return
                endif
                set kind = kind+1
            endloop
        endif
    elseif SubString(command, 0, 6) == "-hero " then
        if command == "-hero random" then
            call SelectRosterHero(p, GetRandomInt(0, HERO_COUNT-1))
        else
            set kind = 0
            loop
                exitwhen kind == HERO_COUNT
                if command == "-hero " + HeroAlias[kind] then
                    call SelectRosterHero(p, kind)
                    return
                endif
                set kind = kind+1
            endloop
        endif
    elseif command == "-help" then
        call Tell(p, "Выдели казарму: 5 улучшений: атака, броня, HP, ступень и численность волн. -shop: выбрать казарму | -items: магазин | -race: 4 расы | -hero: 50 героев по портретам | -ar: всё наугад до 15 секунд | -status: армия | -auto: автоприказы | F9: правила. Выбор до 60 секунд.")
    endif
endfunction

function BoardCell takes integer row, integer col, string value returns nothing
    local multiboarditem cell = MultiboardGetItem(Board, row, col)
    call MultiboardSetItemValue(cell, value)
    call MultiboardReleaseItem(cell)
    set cell = null
endfunction

function UpdateBoard takes nothing returns nothing
    local integer p = 0
    call MultiboardSetTitleText(Board, "Four Fronts | " + I2S(Seconds/60) + ":" + SubString(I2S(100+ModuloInteger(Seconds, 60)), 1, 3))
    loop
        exitwhen p == 12
        call BoardCell(p+1, 0, "T" + I2S(TeamOf(p)+1) + " " + GetPlayerName(Player(p)))
        if not SlotActive[p] then
            call BoardCell(p+1, 1, "EMPTY")
        elseif Lost[p] then
            call BoardCell(p+1, 1, "OUT")
        elseif not Alive(Base[p]) then
            call BoardCell(p+1, 1, "NO BASE")
        else
            call BoardCell(p+1, 1, I2S(Tier[p]+1))
        endif
        call BoardCell(p+1, 2, I2S(Attack[p]) + "/" + I2S(Armor[p]) + "/" + I2S(Vitality[p]))
        call BoardCell(p+1, 3, I2S(CountUnitsInGroup(Army[p])) + " / " + I2S(Kills[p]))
        set p = p+1
    endloop
endfunction

function RegenerateFortresses takes nothing returns nothing
    local integer team = 0
    local integer p
    local unit u
    loop
        exitwhen team == 4
        if not TeamLost[team] then
            call GroupEnumUnitsInRange(Scan, FortressX[team], FortressY[team], 2200, null)
            loop
                set u = FirstOfGroup(Scan)
                exitwhen u == null
                call GroupRemoveUnit(Scan, u)
                set p = GetPlayerId(GetOwningPlayer(u))
                if p < 12 and TeamOf(p) == team and Alive(u) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and not IsUnitType(u, UNIT_TYPE_HERO) then
                    call SetUnitState(u, UNIT_STATE_LIFE, GetWidgetLife(u)+GetUnitState(u, UNIT_STATE_MAX_LIFE)*0.0015)
                    call SetUnitState(u, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MANA)+GetUnitState(u, UNIT_STATE_MAX_MANA)*0.001)
                endif
            endloop
        endif
        set team = team+1
    endloop
    set u = null
endfunction

function OnSummon takes nothing returns nothing
    local unit summoned = GetSummonedUnit()
    local integer p = GetPlayerId(GetOwningPlayer(summoned))
    if p < 12 and not Lost[p] and GetUnitUserData(summoned) == 0 then
        call SetUnitUserData(summoned, 11)
    endif
    set summoned = null
endfunction

function CleanCorpses takes nothing returns nothing
    local group batch = CorpseRing[ModuloInteger(Seconds, CORPSE_SECONDS+1)]
    local unit corpse
    loop
        set corpse = FirstOfGroup(batch)
        exitwhen corpse == null
        call GroupRemoveUnit(batch, corpse)
        if not Alive(corpse) then
            call RemoveUnit(corpse)
        endif
    endloop
    set corpse = null
    set batch = null
endfunction

function SectorAt takes real x, real y returns integer
    if x < 0 then
        if y < 0 then
            return 0
        endif
        return 3
    endif
    if y < 0 then
        return 1
    endif
    return 2
endfunction

function CheckHeroRoute takes integer p returns nothing
    local real x
    local real y
    local integer sector
    if not Alive(Hero[p]) then
        return
    endif
    set x = GetUnitX(Hero[p])
    set y = GetUnitY(Hero[p])
    if x*x+y*y <= 1960000 then
        set HeroSector[p] = -1
    else
        set sector = SectorAt(x,y)
        if HeroSector[p] >= 0 and HeroSector[p] != sector then
            // Also prevent Blink/teleport/flying forms from bypassing the arena.
            call SetUnitPosition(Hero[p], PreviousHeroX[p], PreviousHeroY[p])
            call IssueImmediateOrder(Hero[p], "stop")
            call Tell(p, "Переход между территориями — через центральную площадь.")
            return
        endif
        set HeroSector[p] = sector
    endif
    set PreviousHeroX[p] = x
    set PreviousHeroY[p] = y
endfunction

function AutoSave takes nothing returns nothing
    if not Finished then
        set AutosaveCount = AutosaveCount+1
        // Full native save, synchronized on all clients, always the same path.
        call SyncSelections()
        call SaveGame(AUTOSAVE_PATH)
        // File availability is local: only UI may depend on it, never gameplay.
        if SaveGameExists(AUTOSAVE_PATH) then
            call DisplayTimedTextToPlayer(GetLocalPlayer(),0,0,5,"Файл автосохранения найден: Save\\FFFAutosave.w3z. Следующая запись через 2 минуты.")
        else
            call DisplayTimedTextToPlayer(GetLocalPlayer(),0,0,12,"Автосохранение: файл Save\\FFFAutosave.w3z не найден после попытки записи. Проверь доступ игры к папке Save.")
        endif
    endif
endfunction

function Tick takes nothing returns nothing
    local integer p = 0
    local integer t = 0
    if Finished then
        return
    endif
    set Seconds = Seconds+1
    call ExpansionTick()
    call CreativeTick()
    call CleanCorpses()
    call RegenerateFortresses()
    if Seconds == 16 and HostPlayer >= 0 and ModeDialogOpen then
        set ModeDialogOpen = false
        call ShowRaces(HostPlayer)
    endif
    if Seconds == 1 then
        loop
            exitwhen p == 12
            if not Lost[p] and not Bot[p] then
                if p == HostPlayer then
                    call ShowModes(p)
                else
                    call ShowRaces(p)
                endif
            endif
            set p = p+1
        endloop
        set p = 0
    endif
    if ModuloInteger(Seconds, 6) == 0 then
        loop
            exitwhen t == 4
            if not TeamLost[t] then
                call UpdateRally(t)
            endif
            set t = t+1
        endloop
    endif
    loop
        exitwhen p == 12
        call UpdateBastion(p)
        if not Lost[p] then
            if Alive(Base[p]) then
                call EnsureBotHero(p)
                call CheckHeroRoute(p)
                if Seconds > WARMUP_SECONDS then
                    call AddGold(p, INCOME_PER_SECOND)
                    set SpawnClock[p] = SpawnClock[p]+1
                    if SpawnClock[p] >= SPAWN_SECONDS then
                        set SpawnClock[p] = 0
                        call SpawnWave(p)
                    endif
                endif
                if Hero[p] != null and not Alive(Hero[p]) then
                    set Respawn[p] = Respawn[p]-1
                    if Respawn[p] <= 0 then
                        call ReviveHero(Hero[p], HomeX[p], HomeY[p]-240, true)
                        set HeroSector[p] = TeamOf(p)
                        set PreviousHeroX[p] = HomeX[p]
                        set PreviousHeroY[p] = HomeY[p]-240
                        call SetUnitState(Hero[p], UNIT_STATE_MANA, GetUnitState(Hero[p], UNIT_STATE_MAX_MANA))
                    endif
                endif
                if Bot[p] and Seconds >= WARMUP_SECONDS then
                    call BotBuy(p)
                endif
            endif
            if Seconds >= WARMUP_SECONDS then
                if ModuloInteger(Seconds+p, 6) == 0 then
                    call CommandArmy(p, false)
                endif
                if Bot[p] and ModuloInteger(Seconds+p, 2) == 0 then
                    call TriggerExecute(BotThinkTrigger[p])
                endif
            endif
        endif
        set p = p+1
    endloop
    if Seconds == WARMUP_SECONDS then
        call Say("Бой начался! Исследования: четыре кнопки в казарме. Магазин экипировки находится в центре арены; в каждой крепости ещё пять обычных магазинов и Сокровищница титанов (-supreme). Зелья: -potions. В центре — общий фонтан жизни и маны.")
        set p = 0
        loop
            exitwhen p == 12
            if Alive(Base[p]) then
                if Hero[p] != null then
                    call PauseUnit(Hero[p], false)
                endif
                if HeroPicker[p] != null then
                    call RemoveUnit(HeroPicker[p])
                    set HeroPicker[p] = null
                endif
                call DialogDisplay(Player(p), Shop[p], false)
                call SpawnWave(p)
            endif
            set p = p+1
        endloop
    endif
    if ModuloInteger(Seconds, 3) == 0 then
        call UpdateBoard()
    endif
endfunction

function CreateRules takes nothing returns nothing
    local quest q = CreateQuest()
    call QuestSetTitle(q, "Four Fronts: rules")
    call QuestSetDescription(q, "4 teams of 3. Choose race and hero before 60 seconds. Barracks have five command-card research buttons: attack, armor, troop HP (200 ranks each), barracks tier (four upgrades), and wave size (+1 troop, starting at 2000 gold). Research affects existing and future troops; attack/armor/HP prices are 50% lower than 0.16.0. Attack research adds 4 damage and armor adds 1.5 per rank. HP research adds 10% of base HP per rank. Attack, armor and troop HP keep their normal linear prices at all ranks; no rank-11 surcharge. Barracks tiers strengthen future waves and give +25350 HP to the barracks. " + "Every barracks tier moderately strengthens future troops; models and collision are smaller. Waves: three plus wave-size research troops of the current army tier every 18 seconds. Destroy all occupied barracks to eliminate a team. One wide, flared tunnel per fortress. Inside each fortress allied nonhero troops regenerate 0.15% HP and 0.1% mana each second. " + "Five regular shops, a supreme shop and an allied hero fountain (0.5% HP/mana, radius 1200) per fortress. Shared fountain: native health/mana auras restore 1.5% per second to all heroes of every team within 1000, including undead. " + "Each barracks has a destructible 156000 HP bastion tower behind its base: 1750 damage, 24 armor, attacks every 0.2s; activates near the base or when damaged, retaining a six-second defense window, range 1400. Experience rate: 50%. Bots randomly choose balanced, equipment or army spending priorities for the whole match.")
    call QuestSetRequired(q, true)
    call QuestSetDiscovered(q, true)
    set q = CreateQuest()
    call QuestSetTitle(q, "Commands and heroes")
    call QuestSetDescription(q, "-shop selects your barracks. -items selects the equipment shop near the arena center; bring your hero into range to buy items. -race / -hero: portrait selection before 60 seconds. 50 heroes including twenty-six custom. -mode / -ar: first occupied human chooses mode before 15s. Open slots stay empty. -attack / -armor / -hp / -tier / -wave queue research. -supplies selects your fortress supplies. Q/W/E/R cast hero skills. Hero max level: 500. Three normal skills: 200 ranks each, one rank per hero level. Ultimate: 50 ranks, from level 6 every 10 hero levels. Each level grants two skill points. Strength gives 30 HP and intelligence 18 mana. A single fortress market row sells weapons, armor, magic, speed and special effects. Summons grow in HP, damage and size; one extra summon every 10 skill ranks. -status: army stats. -auto: army orders. -go: rally.")
    call QuestSetRequired(q, false)
    call QuestSetDiscovered(q, true)
    set q = CreateQuest()
    call QuestSetTitle(q, "Attributes, routes and autosave")
    call QuestSetDescription(q, "All heroes have a fifth + skill: spend one skill point for +2 strength, agility and intelligence per rank, up to 500 ranks. All inter-team routes pass through center, including hero Blink/teleport. Allied base fountains heal heroes. Passive income and kill gold are reduced by 25% versus 0.13.1. Ultimate damage/healing/bonuses and summoned creatures are stronger; secondary summon effects scale with their rank. -supreme selects high-end equipment; -potions selects central consumables; -books selects the shared team book shop. Full native autosave every 120 seconds, same file: Save/FFFAutosave.w3z. Load it through the saved-game menu. Saving may briefly pause the engine. Three plus wave-size research troops per wave, now every 18 seconds; army cap 85; summon counts preserved. 24 stock plus 26 custom creature heroes.")
    call QuestSetRequired(q, false)
    call QuestSetDiscovered(q, true)
    set q = null
endfunction

function OnBaseDefense takes nothing returns nothing
    local unit target = GetTriggerUnit()
    local unit attacker = GetEventDamageSource()
    local integer p = GetPlayerId(GetOwningPlayer(target))
    if p < 12 and GetEventDamage() > 0 and Alive(attacker) and Alive(Bastion[p]) then
        if IsUnitEnemy(attacker, Player(p)) then
            if Seconds >= BastionUntil[p] then
                call PauseUnit(Bastion[p], false)
                call IssueTargetOrder(Bastion[p], "attack", attacker)
            endif
            set BastionUntil[p] = Seconds+6
        endif
    endif
    set target = null
    set attacker = null
endfunction

function InitSlot takes integer p returns nothing
    local integer t
    local integer j
    local fogmodifier fog
    set t = TeamOf(p)
    set SlotActive[p] = GetPlayerSlotState(Player(p)) == PLAYER_SLOT_STATE_PLAYING
    set Lost[p] = not SlotActive[p]
    set Army[p] = CreateGroup()
    set Shop[p] = DialogCreate()
    if not SlotActive[p] then
        set Bot[p] = false
        return
    endif
    set Bot[p] = GetPlayerController(Player(p)) != MAP_CONTROL_USER
    if Bot[p] then
        call AssignBotTactic(p)
    endif
    if not Bot[p] and HostPlayer == -1 then
        set HostPlayer = p
    endif
    set BotThinkTrigger[p] = CreateTrigger()
    call TriggerAddAction(BotThinkTrigger[p], function BotThink)
    set AutoArmy[p] = true
    if Bot[p] then
        call SetPlayerController(Player(p), MAP_CONTROL_COMPUTER)
        call SetPlayerName(Player(p), "Bot " + I2S(p+1) + " [" + BotTacticName[BotTactic[p]] + "]")
    endif
    call SetPlayerState(Player(p), PLAYER_STATE_RESOURCE_GOLD, STARTING_GOLD)
    call SetPlayerState(Player(p), PLAYER_STATE_RESOURCE_LUMBER, 0)
    call SetPlayerState(Player(p), PLAYER_STATE_RESOURCE_FOOD_CAP, 300)
    call SetPlayerState(Player(p), PLAYER_STATE_GIVES_BOUNTY, 0)
    call SetPlayerState(Player(p), PLAYER_STATE_FOOD_CAP_CEILING, 300)
    set j = 0
    loop
        exitwhen j == 12
        call SetPlayerAllianceStateAllyBJ(Player(p), Player(j), TeamOf(j) == t)
        call SetPlayerAlliance(Player(p), Player(j), ALLIANCE_SHARED_VISION, TeamOf(j) == t)
        set j = j+1
    endloop
    set fog = CreateFogModifierRadius(Player(p), FOG_OF_WAR_VISIBLE, HomeX[p], HomeY[p], 1200, true, false)
    call FogModifierStart(fog)
    set fog = CreateFogModifierRadius(Player(p), FOG_OF_WAR_VISIBLE, 0, 640, 700, true, false)
    call FogModifierStart(fog)
    set fog = CreateFogModifierRadius(Player(p),FOG_OF_WAR_VISIBLE,SuperX[t],SuperY[t],500,true,false)
    call FogModifierStart(fog)
    set fog = CreateFogModifierRadius(Player(p),FOG_OF_WAR_VISIBLE,0,-640,500,true,false)
    call FogModifierStart(fog)
    set j = 0
    loop
        exitwhen j == 5
        set fog = CreateFogModifierRadius(Player(p), FOG_OF_WAR_VISIBLE, ShopX[t*5+j], ShopY[t*5+j], 500, true, false)
        call FogModifierStart(fog)
        set j = j+1
    endloop
    set Base[p] = CreateUnit(Player(p), 'fbax', HomeX[p], HomeY[p], 270)
    if TeamBookShop[t] == null then
        set TeamBookShop[t] = CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'fbks',BookX[p],BookY[p],270)
        call SetUnitInvulnerable(TeamBookShop[t],true)
    endif
    set BookShop[p] = TeamBookShop[t]
    set Tower[p] = CreateUnit(Player(p), 'ftow', HomeX[p]*0.82, HomeY[p]*0.82, 270)
    set Bastion[p] = CreateUnit(Player(p), 'fbst', BastionX[p], BastionY[p], 270)
    call PauseUnit(Bastion[p], true)
    call SetPlayerTechMaxAllowed(Player(p),'Rfwn',WAVE_UPGRADE_MAX)
    call TriggerRegisterUnitEvent(BaseDefenseTrigger, Base[p], EVENT_UNIT_DAMAGED)
    call TriggerRegisterUnitEvent(BaseDefenseTrigger, Bastion[p], EVENT_UNIT_DAMAGED)
    if Bot[p] then
        set ArmyRace[p] = GetRandomInt(0, 3)
        call QueueHero(p, GetRandomInt(0,HERO_COUNT-1))
    else
        call CreateHero(p, 0)
    endif
    call TriggerRegisterDialogEvent(ShopTrigger, Shop[p])
    call TriggerRegisterPlayerUnitEvent(SummonTrigger, Player(p), EVENT_PLAYER_UNIT_SUMMON, null)
    call TriggerRegisterPlayerUnitEvent(ResearchTrigger, Player(p), EVENT_PLAYER_UNIT_RESEARCH_FINISH, null)
    call TriggerRegisterPlayerUnitEvent(PickerTrainTrigger, Player(p), EVENT_PLAYER_UNIT_TRAIN_FINISH, null)
    call TriggerRegisterPlayerUnitEvent(PickerSpellTrigger, Player(p), EVENT_PLAYER_UNIT_SPELL_EFFECT, null)
    call TriggerRegisterPlayerUnitEvent(TransmuteTrigger, Player(p), EVENT_PLAYER_UNIT_SPELL_EFFECT, null)
    call TriggerRegisterPlayerUnitEvent(TransmuteTrigger, Player(p), EVENT_PLAYER_UNIT_SPELL_CAST, null)
    call TriggerRegisterPlayerUnitEvent(TransmuteTrigger, Player(p), EVENT_PLAYER_UNIT_SPELL_FINISH, null)
    call TriggerRegisterPlayerUnitEvent(TransmuteTrigger, Player(p), EVENT_PLAYER_UNIT_SPELL_ENDCAST, null)
    call TriggerRegisterPlayerUnitEvent(LevelTrigger, Player(p), EVENT_PLAYER_HERO_LEVEL, null)
    set j = 0
    loop
        exitwhen j == 4
        if j == 3 then
            call SetPlayerTechMaxAllowed(Player(p), ArmyResearch[j], 4)
        else
            call SetPlayerTechMaxAllowed(Player(p),ArmyResearch[j],RESEARCH_SOFT_CAP)
            call SetPlayerTechMaxAllowed(Player(p),AdvancedArmyResearch[j],0)
        endif
        set j = j+1
    endloop
    call TriggerRegisterPlayerUnitEvent(DeathTrigger, Player(p), EVENT_PLAYER_UNIT_DEATH, null)
    call TriggerRegisterPlayerChatEvent(ChatTrigger, Player(p), "-", false)
    call TriggerRegisterPlayerEvent(LeaveTrigger, Player(p), EVENT_PLAYER_LEAVE)
    if not Bot[p] then
        call PanCameraToTimedForPlayer(Player(p), HomeX[p], HomeY[p], 0)
    endif
    set fog = null
endfunction

function InitGame takes nothing returns nothing
    local integer p = 0
    local integer t
    local multiboarditem cell
    local timer clock = CreateTimer()
    set Scan = CreateGroup()
    set Work = CreateGroup()
    set DeathTrigger = CreateTrigger()
    set ChatTrigger = CreateTrigger()
    set LeaveTrigger = CreateTrigger()
    set ShopTrigger = CreateTrigger()
    set ResearchTrigger = CreateTrigger()
    set LevelTrigger = CreateTrigger()
    set SummonTrigger = CreateTrigger()
    set PickerTrainTrigger = CreateTrigger()
    set PickerSpellTrigger = CreateTrigger()
    set TransmuteTrigger = CreateTrigger()
    set BaseDefenseTrigger = CreateTrigger()
    call InitBalance()
    loop
        exitwhen p > CORPSE_SECONDS
        set CorpseRing[p] = CreateGroup()
        set p = p+1
    endloop
    call InitWalls()
    set Fountain = CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE), 'ffnt', 0, 0, 270)
    call SetUnitInvulnerable(Fountain, true)
    set EquipmentShop = CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE), 'fshp', 0, 640, 270)
    call SetUnitInvulnerable(EquipmentShop, true)
    set p = 0
    loop
        exitwhen p == 20
        set FortressShop[p] = CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE), 'fs0p'+ModuloInteger(p, 5)*256, ShopX[p], ShopY[p], 270)
        call SetUnitInvulnerable(FortressShop[p], true)
        set p = p+1
    endloop
    set p = 0
    loop
        exitwhen p == 4
        set UtilityShop[p] = CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'futl',UtilityX[p],UtilityY[p],270)
        call SetUnitInvulnerable(UtilityShop[p],true)
        set SupremeShop[p] = CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'fsup',SuperX[p],SuperY[p],270)
        call SetUnitInvulnerable(SupremeShop[p],true)
        set p = p+1
    endloop
    set PotionShop = CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'fpot',0,-640,270)
    call SetUnitInvulnerable(PotionShop,true)
    set p = 0
    call SetTimeOfDay(12)
    call SetTimeOfDayScale(0)
    call SetMapFlag(MAP_FOG_HIDE_TERRAIN, false)
    call SetMapFlag(MAP_FOG_MAP_EXPLORED, true)
    call FogMaskEnable(false)
    call FogEnable(true)
    loop
        exitwhen p == 12
        call InitSlot(p)
        set p = p+1
    endloop
    call ExpansionInit()
    call CreativeInit()
    call TriggerAddAction(SummonTrigger, function OnSummon)
    call TriggerAddAction(DeathTrigger, function OnDeath)
    call TriggerAddAction(ChatTrigger, function OnChat)
    call TriggerAddAction(ShopTrigger, function OnShop)
    call TriggerAddAction(ResearchTrigger, function OnResearch)
    call TriggerAddAction(LevelTrigger, function OnHeroLevel)
    call TriggerAddAction(PickerTrainTrigger, function OnHeroPick)
    call TriggerAddAction(PickerSpellTrigger, function OnPickerSpell)
    call TriggerAddAction(TransmuteTrigger, function OnTransmute)
    call TriggerAddAction(TransmuteTrigger, function OnHybridSpell)
    call TriggerAddAction(TransmuteTrigger, function OnExpansionSpell)
    call TriggerAddAction(TransmuteTrigger, function OnCreativeSpell)
    call TriggerAddAction(BaseDefenseTrigger, function OnBaseDefense)
    call TriggerAddAction(LeaveTrigger, function OnLeave)
    set t = 0
    loop
        exitwhen t == 4
        set TeamLost[t] = not Alive(Base[t*3]) and not Alive(Base[t*3+1]) and not Alive(Base[t*3+2])
        if not TeamLost[t] then
            set p = t*3
            loop
                exitwhen SlotActive[p]
                set p = p+1
            endloop
            set TeamFountain[t] = CreateUnit(Player(p), 'fbfn', FortressX[t], FortressY[t], 270)
            call SetUnitInvulnerable(TeamFountain[t], true)
            call UpdateRally(t)
        endif
        set t = t+1
    endloop
    set Board = CreateMultiboard()
    call MultiboardSetRowCount(Board, 13)
    call MultiboardSetColumnCount(Board, 4)
    call MultiboardSetItemsStyle(Board, true, false)
    call MultiboardSetItemsWidth(Board, 0.065)
    set p = 0
    loop
        exitwhen p == 13
        set cell = MultiboardGetItem(Board, p, 0)
        call MultiboardSetItemWidth(cell, 0.13)
        call MultiboardReleaseItem(cell)
        set p = p+1
    endloop
    call BoardCell(0, 0, "Team / Player")
    call BoardCell(0, 1, "Tier")
    call BoardCell(0, 2, "Atk / Def / HP")
    call BoardCell(0, 3, "Army / Kills")
    call UpdateBoard()
    call MultiboardDisplay(Board, true)
    call CreateRules()
    call Say("Four Fronts Frenzy | 4 команды по 3 | Выбери расу и героя по портретам (50 героев). Первый игрок: -mode или -ar до 15-й секунды. Подготовка 60 секунд: герои компьютеров загружаются по очереди. Улучшения: 4 кнопки в казарме. Экипировка: магазин в центре (-items). Герой до 500, навыки до 200/50. За каждый уровень героя — два очка навыков. Автосохранение каждые 2 минуты: Save\\FFFAutosave.w3z.")
    set HeroQueueTimer = CreateTimer()
    call TimerStart(HeroQueueTimer, 0.5, true, function ProcessHeroQueue)
    call TimerStart(clock, 1, true, function Tick)
    set AutosaveTimer = CreateTimer()
    call TimerStart(AutosaveTimer, I2R(AUTOSAVE_SECONDS), true, function AutoSave)
    set clock = null
    set cell = null
endfunction

function main takes nothing returns nothing
    call SetCameraBounds(-5888, -5888, 5888, 5888, -5888, 5888, 5888, -5888)
    call SetDayNightModels("Environment\\DNC\\DNCLordaeron\\DNCLordaeronTerrain\\DNCLordaeronTerrain.mdl", "Environment\\DNC\\DNCLordaeron\\DNCLordaeronUnit\\DNCLordaeronUnit.mdl")
    call NewSoundEnvironment("Default")
    call SetAmbientDaySound("LordaeronSummerDay")
    call SetAmbientNightSound("LordaeronSummerNight")
    call InitBlizzard()
    call InitGame()
endfunction

// config() is generated with the same positions as map metadata.
