// Four Fronts Frenzy. Plain JASS: Warcraft III TFT 1.26+.
// Balance globals and InitBalance are generated from balance.json.
globals
    unit array Base
    unit array Hero
    unit array Tower
    group array Army
    boolean array Bot
    boolean array Lost
    boolean array TeamLost
    boolean array Defending
    integer array Tier
    integer array Attack
    integer array Armor
    integer array Speed
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
    trigger MenuTrigger = null
endglobals

function TeamOf takes integer p returns integer
    return R2I(I2R(p) / 3.0)
endfunction

function Alive takes unit u returns boolean
    return u != null and GetWidgetLife(u) > 0.405 and not IsUnitType(u, UNIT_TYPE_DEAD)
endfunction

function IsArmyUnit takes unit u returns boolean
    local integer id = GetUnitTypeId(u)
    return (id >= 'fm00' and id <= 'fm34') or (id >= 'fr00' and id <= 'fr34')
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
    call SetPlayerState(Player(p), PLAYER_STATE_RESOURCE_GOLD, GetPlayerState(Player(p), PLAYER_STATE_RESOURCE_GOLD) + amount)
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
    return best
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

function UpgradeCost takes integer p, integer kind returns integer
    if kind == 0 and Attack[p] < UPGRADE_MAX then
        return ATTACK_COST + Attack[p]*ATTACK_COST_STEP
    elseif kind == 1 and Armor[p] < UPGRADE_MAX then
        return ARMOR_COST + Armor[p]*ARMOR_COST_STEP
    elseif kind == 2 and Tier[p] < 4 then
        return TierCost[Tier[p]+1]
    elseif kind == 3 and SPAWN_SECONDS-Speed[p] > SPAWN_MIN_SECONDS then
        return SPAWN_COST + Speed[p]*SPAWN_COST_STEP
    elseif kind == 4 and Power[p] < 10 then
        return HERO_POWER_COST + Power[p]*HERO_POWER_COST_STEP
    elseif kind == 5 then
        return 150
    endif
    return -1
endfunction

function UpgradeName takes integer kind returns string
    if kind == 0 then
        return "Атака армии +3"
    elseif kind == 1 then
        return "Броня армии +1"
    elseif kind == 2 then
        return "Следующая ступень армии"
    elseif kind == 3 then
        return "Интервал спавна -1 сек."
    elseif kind == 4 then
        return "Герою: +3 ко всем характеристикам"
    endif
    return "Лечение героя у своей базы"
endfunction

function Buy takes integer p, integer kind returns boolean
    local integer cost = UpgradeCost(p, kind)
    if Finished or Lost[p] or not Alive(Base[p]) then
        call Tell(p, "Your barracks are destroyed. You can still command surviving units.")
        return false
    endif
    if cost < 0 then
        call Tell(p, "Maximum level reached.")
        return false
    endif
    if kind >= 4 and not Alive(Hero[p]) then
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
    call AddGold(p, -cost)
    if kind == 0 then
        set Attack[p] = Attack[p]+1
        call SetPlayerTechResearched(Player(p), 'Rfat', Attack[p])
    elseif kind == 1 then
        set Armor[p] = Armor[p]+1
        call SetPlayerTechResearched(Player(p), 'Rfar', Armor[p])
    elseif kind == 2 then
        set Tier[p] = Tier[p]+1
        // Existing troops remain; new waves use the purchased tier.
    elseif kind == 3 then
        set Speed[p] = Speed[p]+1
    elseif kind == 4 then
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
    local integer k = 0
    local integer cost
    call ClearMenu(p, "АРМИЯ | " + RaceName[ArmyRace[p]] + " | Ступень " + I2S(Tier[p]+1) + " | Золото: " + I2S(GetPlayerState(Player(p), PLAYER_STATE_RESOURCE_GOLD)))
    loop
        exitwhen k == 6
        set cost = UpgradeCost(p, k)
        if cost >= 0 then
            call MenuButton(p, k, UpgradeName(k) + " [" + I2S(cost) + "]", k)
        endif
        set k = k+1
    endloop
    if Seconds < WARMUP_SECONDS then
        call MenuButton(p, 6, "Выбрать расу армии", 10)
        call MenuButton(p, 7, "Выбрать героя (24 героя)", 11)
    endif
    call MenuButton(p, 8, "Закрыть", 12)
    call DialogDisplay(Player(p), Shop[p], true)
endfunction

function ResolvedSkill takes unit h, integer skill returns integer
    local integer engineering = GetUnitAbilityLevel(h, 'ANeg')
    if engineering > 0 and engineering <= 3 then
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

function LearnHero takes integer p returns nothing
    local integer level = GetHeroLevel(Hero[p])
    local integer slot = 0
    local integer index = HeroKind[p]*4
    if level >= 6 then
        call SelectHeroSkill(Hero[p], ResolvedSkill(Hero[p], HeroSkill[index+3]))
    endif
    loop
        exitwhen slot == 3
        call SelectHeroSkill(Hero[p], ResolvedSkill(Hero[p], HeroSkill[index+slot]))
        set slot = slot+1
    endloop
    if AutoSkill[HeroKind[p]] != 0 and GetUnitAbilityLevel(Hero[p], AutoSkill[HeroKind[p]]) > 0 then
        call IssueImmediateOrder(Hero[p], AutoOrder[HeroKind[p]])
    endif
endfunction

function CreateHero takes integer p, integer kind returns nothing
    set HeroKind[p] = kind
    set Hero[p] = CreateUnit(Player(p), HeroType[kind], HomeX[p], HomeY[p]-240, 270)
    call SetHeroLevel(Hero[p], 1, false)
    call UnitAddAbility(Hero[p], 'Fmen')
    call UnitMakeAbilityPermanent(Hero[p], true, 'Fmen')
    call PauseUnit(Hero[p], Seconds < WARMUP_SECONDS)
    if Bot[p] then
        call LearnHero(p)
    endif
endfunction

function AssignBotChoices takes integer p returns nothing
    set ArmyRace[p] = GetRandomInt(0, 3)
    call CreateHero(p, GetRandomInt(0, HERO_COUNT-1))
endfunction

function SelectArmyRace takes integer p, integer choice returns boolean
    if Seconds >= WARMUP_SECONDS or choice < 0 or choice > 3 or Lost[p] then
        call Tell(p, "Расу армии можно выбрать только до первого спавна.")
        return false
    endif
    set ArmyRace[p] = choice
    call Tell(p, "Раса армии: " + RaceName[choice])
    return true
endfunction

function SelectRosterHero takes integer p, integer choice returns boolean
    if Seconds >= WARMUP_SECONDS or Power[p] > 0 or choice < 0 or choice >= HERO_COUNT or Lost[p] then
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

function ShowRaces takes integer p returns nothing
    local integer k = 0
    if Seconds >= WARMUP_SECONDS then
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
    return "Нейтральные герои"
endfunction

function ShowHeroGroups takes integer p returns nothing
    local integer k = 0
    if Seconds >= WARMUP_SECONDS then
        call ShowShop(p)
        return
    endif
    call ClearMenu(p, "ВЫБОР ГЕРОЯ: 24 стандартных героя")
    loop
        exitwhen k == 5
        call MenuButton(p, k, HeroCategory(k), 200+k)
        set k = k+1
    endloop
    call MenuButton(p, 5, "Случайный герой", 399)
    call MenuButton(p, 6, "Меню армии", 13)
    call MenuButton(p, 7, "Закрыть", 12)
    call DialogDisplay(Player(p), Shop[p], true)
endfunction

function ShowHeroes takes integer p, integer category returns nothing
    local integer k = 0
    local integer slot = 0
    if Seconds >= WARMUP_SECONDS then
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
    if action >= 0 and action < 6 then
        call Buy(p, action)
        call ShowShop(p)
    elseif action == 10 then
        call ShowRaces(p)
    elseif action == 11 then
        call ShowHeroGroups(p)
    elseif action == 13 then
        call ShowShop(p)
    elseif action >= 100 and action <= 104 then
        if action == 104 then
            set action = 100+GetRandomInt(0, 3)
        endif
        call SelectArmyRace(p, action-100)
        call ShowHeroGroups(p)
    elseif action >= 200 and action < 205 then
        call ShowHeroes(p, action-200)
    elseif action == 399 then
        call SelectRosterHero(p, GetRandomInt(0, HERO_COUNT-1))
        call ShowShop(p)
    elseif action >= 300 and action < 300+HERO_COUNT then
        call SelectRosterHero(p, action-300)
        call ShowShop(p)
    endif
endfunction

function OnArmyMenu takes nothing returns nothing
    local integer p = GetPlayerId(GetOwningPlayer(GetTriggerUnit()))
    if GetSpellAbilityId() == 'Fmen' and p < 12 and not Bot[p] and not Finished then
        call ShowShop(p)
    endif
endfunction

function SpawnWave takes integer p returns nothing
    local integer n = 0
    local integer count = CountUnitsInGroup(Army[p])
    local integer id
    local unit u
    loop
        exitwhen n >= SPAWN_UNITS or count >= ARMY_CAP
        if n == SPAWN_UNITS-1 then
            set id = RangedType[ArmyRace[p]*5+Tier[p]]
        else
            set id = MeleeType[ArmyRace[p]*5+Tier[p]]
        endif
        set u = CreateUnit(Player(p), id, HomeX[p] + I2R(n-1)*90, HomeY[p] + 220, 270)
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
            if GetUnitUserData(u) > 10 and DistanceSq(GetUnitX(u), GetUnitY(u), 0, 0) < 2250000 then
                call SetUnitUserData(u, GetUnitUserData(u)-10)
            endif
            // Humans can override orders; -auto resumes automatic commands.
            if forceOrder or Bot[p] or AutoArmy[p] then
                // Do not reset a swing/cast when already fighting nearby.
                if forceOrder or GetUnitCurrentOrder(u) == 0 or EnemyNear(p, GetUnitX(u), GetUnitY(u), 650) == null then
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

function BotBuy takes integer p returns nothing
    local integer cash = GetPlayerState(Player(p), PLAYER_STATE_RESOURCE_GOLD)
    // Save for a tier after a balanced number of inexpensive upgrades.
    // Purchase exclusively through Buy(), with the same prices as humans.
    if Tier[p] < 4 and Attack[p] >= (Tier[p]+1)*2 and Armor[p] >= Tier[p]+1 then
        if cash >= UpgradeCost(p, 2) then
            call Buy(p, 2)
        endif
    elseif Attack[p] < UPGRADE_MAX and Attack[p] <= Armor[p]*2 then
        call Buy(p, 0)
    elseif Armor[p] < UPGRADE_MAX then
        call Buy(p, 1)
    elseif Tier[p] < 4 then
        call Buy(p, 2)
    elseif Speed[p] < SPAWN_SECONDS-SPAWN_MIN_SECONDS then
        call Buy(p, 3)
    elseif Power[p] < 10 then
        call Buy(p, 4)
    endif
    // Extra purchases never consume the tier savings above.
    if Tier[p] >= 2 and Speed[p] < Tier[p]-1 and cash > 2*UpgradeCost(p, 3) then
        call Buy(p, 3)
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
    return best
endfunction

function TryBotSpell takes integer p, unit enemy returns boolean
    local integer slot = 0
    local integer index
    local integer mode
    local unit ally = null
    local boolean cast = false
    local unit h = Hero[p]
    local real health = GetWidgetLife(h)/GetUnitState(h, UNIT_STATE_MAX_LIFE)
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
                if mode == 0 or (mode == 4 and health < 0.55) or (mode == 5 and DistanceSq(GetUnitX(h), GetUnitY(h), GetUnitX(enemy), GetUnitY(enemy)) < 160000) then
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

function BotHero takes integer p returns nothing
    local unit h = Hero[p]
    local unit enemy
    local real health
    local integer team = TeamOf(p)
    if not Alive(h) then
        set h = null
        return
    endif
    if CastUntil[p] <= Seconds then
        call LearnHero(p)
    endif
    set health = GetWidgetLife(h) / GetUnitState(h, UNIT_STATE_MAX_LIFE)
    set enemy = EnemyNear(p, GetUnitX(h), GetUnitY(h), 750)
    if Alive(Base[p]) and (health < 0.28 or (RetreatUntil[p] > Seconds and health < 0.85)) then
        set RetreatUntil[p] = Seconds+8
        if HeroKind[p] == 0 then
            call IssueImmediateOrder(h, "divineshield")
        elseif HeroKind[p] == 4 then
            call IssueImmediateOrder(h, "windwalk")
        endif
        call IssuePointOrder(h, "move", HomeX[p], HomeY[p]-260)
        if DistanceSq(GetUnitX(h), GetUnitY(h), HomeX[p], HomeY[p]) < 500000 and health < 0.5 then
            call Buy(p, 5)
        endif
        set h = null
        set enemy = null
        return
    endif
    if CastUntil[p] > Seconds then
        set h = null
        set enemy = null
        return
    endif
    if TryBotSpell(p, enemy) then
        set h = null
        set enemy = null
        return
    endif
    if enemy == null then
        call IssuePointOrder(h, "attack", RallyX[team], RallyY[team])
    elseif GetUnitCurrentOrder(h) == 0 then
        call IssueTargetOrder(h, "attack", enemy)
    endif
    set h = null
    set enemy = null
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
            if not Bot[p] then
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

function OnDeath takes nothing returns nothing
    local unit dead = GetTriggerUnit()
    local unit killer = GetKillingUnit()
    local integer p = GetPlayerId(GetOwningPlayer(dead))
    local integer k = -1
    local integer reward = 0
    if Finished or p >= 12 then
        set dead = null
        set killer = null
        return
    endif
    if killer != null then
        set k = GetPlayerId(GetOwningPlayer(killer))
    endif
    if dead == Base[p] then
        set reward = 300
        call Say(GetPlayerName(Player(p)) + " lost their barracks!")
    elseif dead == Hero[p] then
        set reward = 100 + 15*GetHeroLevel(dead)
        set Respawn[p] = 15 + GetHeroLevel(dead)*3
    elseif dead == Tower[p] then
        set reward = 80
    elseif IsArmyUnit(dead) then
        set reward = 6 + ModuloInteger(GetUnitUserData(dead), 10)*2
        call GroupRemoveUnit(Army[p], dead)
    endif
    if k >= 0 and k < 12 and TeamOf(k) != TeamOf(p) and reward > 0 then
        call AddGold(k, reward)
        set Kills[k] = Kills[k]+1
        // Nearby hero receives additional deterministic experience even above melee level 5.
        if Alive(Hero[k]) and DistanceSq(GetUnitX(Hero[k]), GetUnitY(Hero[k]), GetUnitX(dead), GetUnitY(dead)) < 1440000 then
            call AddHeroXP(Hero[k], reward*2, true)
        endif
    endif
    if dead == Base[p] then
        call CheckTeam(TeamOf(p))
    endif
    set dead = null
    set killer = null
endfunction

function OnLeave takes nothing returns nothing
    local integer p = GetPlayerId(GetTriggerPlayer())
    if p < 12 and not Lost[p] then
        set Bot[p] = true
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
        call ShowHeroGroups(p)
    elseif command == "-attack" then
        call Buy(p, 0)
    elseif command == "-armor" then
        call Buy(p, 1)
    elseif command == "-tier" then
        call Buy(p, 2)
    elseif command == "-spawn" then
        call Buy(p, 3)
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
    elseif command == "-go" then
        call CommandArmy(p, true)
    elseif command == "-status" then
        call Tell(p, RaceName[ArmyRace[p]] + " | " + TierName[ArmyRace[p]*5+Tier[p]] + " | attack " + I2S(Attack[p]) + " | armor " + I2S(Armor[p]) + " | spawn " + I2S(SPAWN_SECONDS-Speed[p]) + "s | army " + I2S(CountUnitsInGroup(Army[p])) + "/" + I2S(ARMY_CAP))
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
        call Tell(p, "Кнопка [U] на казарме или герое: улучшения армии. -shop: меню | -race: 4 расы | -hero: 24 героя | -status: армия | -auto: автоприказы | F9: правила. Выбор до 60 секунд.")
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
        if Lost[p] then
            call BoardCell(p+1, 1, "OUT")
        elseif not Alive(Base[p]) then
            call BoardCell(p+1, 1, "NO BASE")
        else
            call BoardCell(p+1, 1, I2S(Tier[p]+1))
        endif
        call BoardCell(p+1, 2, I2S(Attack[p]) + "/" + I2S(Armor[p]))
        call BoardCell(p+1, 3, I2S(CountUnitsInGroup(Army[p])) + " / " + I2S(Kills[p]))
        set p = p+1
    endloop
endfunction

function Tick takes nothing returns nothing
    local integer p = 0
    local integer t = 0
    local real life
    if Finished then
        return
    endif
    set Seconds = Seconds+1
    if Seconds == 1 then
        loop
            exitwhen p == 12
            if not Bot[p] then
                call ShowRaces(p)
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
        if not Lost[p] then
            if Alive(Base[p]) then
                if Seconds > WARMUP_SECONDS then
                    call AddGold(p, INCOME_PER_SECOND)
                    set SpawnClock[p] = SpawnClock[p]+1
                    if SpawnClock[p] >= SPAWN_SECONDS-Speed[p] then
                        set SpawnClock[p] = 0
                        call SpawnWave(p)
                    endif
                endif
                if not Alive(Hero[p]) then
                    set Respawn[p] = Respawn[p]-1
                    if Respawn[p] <= 0 then
                        call ReviveHero(Hero[p], HomeX[p], HomeY[p]-240, true)
                        call SetUnitState(Hero[p], UNIT_STATE_MANA, GetUnitState(Hero[p], UNIT_STATE_MAX_MANA))
                    endif
                elseif DistanceSq(GetUnitX(Hero[p]), GetUnitY(Hero[p]), HomeX[p], HomeY[p]) < 360000 then
                    // Fountain regeneration pauses under enemy pressure.
                    if EnemyNear(p, HomeX[p], HomeY[p], 850) == null then
                        set life = GetUnitState(Hero[p], UNIT_STATE_MAX_LIFE)
                        call SetUnitState(Hero[p], UNIT_STATE_LIFE, GetWidgetLife(Hero[p])+life*0.035)
                        call SetUnitState(Hero[p], UNIT_STATE_MANA, GetUnitState(Hero[p], UNIT_STATE_MANA)+8)
                    endif
                endif
                if Bot[p] and Seconds >= WARMUP_SECONDS and ModuloInteger(Seconds+p, 5) == 0 then
                    call BotBuy(p)
                endif
            endif
            if Seconds >= WARMUP_SECONDS then
                if ModuloInteger(Seconds, 6) == 0 then
                    call CommandArmy(p, false)
                endif
                if Bot[p] and ModuloInteger(Seconds, 2) == 0 then
                    call BotHero(p)
                endif
            endif
        endif
        set p = p+1
    endloop
    if Seconds == WARMUP_SECONDS then
        call Say("Бой начался! Кнопка [U] на казарме или герое открывает улучшения армии.")
        set p = 0
        loop
            exitwhen p == 12
            if Alive(Base[p]) then
                call PauseUnit(Hero[p], false)
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
    call QuestSetDescription(q, "4 teams of 3. Each team's fortress has one gate facing the arena. Choose army race and hero during the first 60 seconds. Barracks produce two melee and one ranged soldier every 8 seconds. Army Menu [U] on barracks and heroes opens upgrades. Attack and armor affect existing troops; tiers affect future waves. Destroy all three barracks to eliminate a team. Last surviving team wins. Bots randomly choose any of 24 heroes and one of 4 races. Heroes revive while their own barracks survive.")
    call QuestSetRequired(q, true)
    call QuestSetDiscovered(q, true)
    set q = CreateQuest()
    call QuestSetTitle(q, "Commands and heroes")
    call QuestSetDescription(q, "-shop: upgrade menu, also available as Army Menu [U] on barracks and heroes. -race: army race menu. -hero: hero roster (16 racial + 8 neutral heroes). -hero random / -race random: random choice. Race and hero lock at 60 seconds. -attack / -armor / -tier / -spawn / -power / -heal: direct purchases. -status: army stats. -auto: toggle army orders. -go: rally. Human heroes remain manually controlled after preparation.")
    call QuestSetRequired(q, false)
    call QuestSetDiscovered(q, true)
    set q = null
endfunction

function InitGame takes nothing returns nothing
    local integer p = 0
    local integer j
    local integer t
    local multiboarditem cell
    local fogmodifier fog
    local timer clock = CreateTimer()
    set Scan = CreateGroup()
    set Work = CreateGroup()
    set DeathTrigger = CreateTrigger()
    set ChatTrigger = CreateTrigger()
    set LeaveTrigger = CreateTrigger()
    set ShopTrigger = CreateTrigger()
    set MenuTrigger = CreateTrigger()
    call InitBalance()
    call InitWalls()
    call SetTimeOfDay(12)
    call SetTimeOfDayScale(0)
    call SetMapFlag(MAP_FOG_HIDE_TERRAIN, false)
    call SetMapFlag(MAP_FOG_MAP_EXPLORED, true)
    call FogMaskEnable(false)
    call FogEnable(true)
    loop
        exitwhen p == 12
        set t = TeamOf(p)
        set Bot[p] = GetPlayerController(Player(p)) != MAP_CONTROL_USER or GetPlayerSlotState(Player(p)) != PLAYER_SLOT_STATE_PLAYING
        set AutoArmy[p] = true
        if Bot[p] then
            call SetPlayerController(Player(p), MAP_CONTROL_COMPUTER)
            call SetPlayerName(Player(p), "Bot " + I2S(p+1))
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
        set Army[p] = CreateGroup()
        set Base[p] = CreateUnit(Player(p), 'fbax', HomeX[p], HomeY[p], 270)
        set Tower[p] = CreateUnit(Player(p), 'ftow', HomeX[p]*0.82, HomeY[p]*0.82, 270)
        if Bot[p] then
            call AssignBotChoices(p)
        else
            call CreateHero(p, 0)
        endif
        set Shop[p] = DialogCreate()
        call TriggerRegisterDialogEvent(ShopTrigger, Shop[p])
        call TriggerRegisterPlayerUnitEvent(MenuTrigger, Player(p), EVENT_PLAYER_UNIT_SPELL_EFFECT, null)
        call TriggerRegisterPlayerUnitEvent(DeathTrigger, Player(p), EVENT_PLAYER_UNIT_DEATH, null)
        call TriggerRegisterPlayerChatEvent(ChatTrigger, Player(p), "-", false)
        call TriggerRegisterPlayerEvent(LeaveTrigger, Player(p), EVENT_PLAYER_LEAVE)
        if not Bot[p] then
            call PanCameraToTimedForPlayer(Player(p), HomeX[p], HomeY[p], 0)
        endif
        set p = p+1
    endloop
    call TriggerAddAction(DeathTrigger, function OnDeath)
    call TriggerAddAction(ChatTrigger, function OnChat)
    call TriggerAddAction(ShopTrigger, function OnShop)
    call TriggerAddAction(MenuTrigger, function OnArmyMenu)
    call TriggerAddAction(LeaveTrigger, function OnLeave)
    set t = 0
    loop
        exitwhen t == 4
        call UpdateRally(t)
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
    call BoardCell(0, 2, "Atk / Def")
    call BoardCell(0, 3, "Army / Kills")
    call UpdateBoard()
    call MultiboardDisplay(Board, true)
    call CreateRules()
    call Say("Four Fronts Frenzy | 4 команды по 3 | Выбери расу армии и героя. Бой начнётся через 60 секунд. Меню улучшений: кнопка [U] на казарме/герое или -shop.")
    call TimerStart(clock, 1, true, function Tick)
    set clock = null
    set cell = null
    set fog = null
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
