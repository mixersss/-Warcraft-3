// Bounded scans in existing per-player trigger threads. No per-unit timers/groups.
function BotCanSee takes integer p, unit u returns boolean
    return Alive(u) and IsUnitVisible(u,Player(p)) and not IsUnitInvisible(u,Player(p))
endfunction

function BotAllyAnchor takes integer p returns unit
    local integer k = TeamOf(p)*3
    local unit best = null
    local real score = 99999999.
    local real distance
    loop
        exitwhen k == TeamOf(p)*3+3
        if k != p and SlotActive[k] and not Lost[k] and Alive(Hero[k]) and RetreatUntil[k] <= Seconds and GetWidgetLife(Hero[k])/GetUnitState(Hero[k],UNIT_STATE_MAX_LIFE) >= .5 then
            set distance = DistanceSq(GetUnitX(Hero[p]),GetUnitY(Hero[p]),GetUnitX(Hero[k]),GetUnitY(Hero[k]))
            if distance > 90000 and distance < 4840000 and distance < score then
                set score = distance
                set best = Hero[k]
            endif
        endif
        set k = k+1
    endloop
    set ReturnedUnit = best
    set best = null
    return ReturnedUnit
endfunction

function BotCombatScan takes integer p returns unit
    local unit u
    local unit best = null
    local integer owner
    local real weight
    local real health
    local real score
    local real bestScore = 999999.
    local integer k = 0
    local integer team = TeamOf(p)
    set BotAlliedPower[p] = 0
    set BotEnemyPower[p] = 0
    set BotNearbyTroops[p] = 0
    set BotHurtTroops[p] = 0
    set BotTowerDanger[p] = false
    call GroupEnumUnitsInRange(Scan,GetUnitX(Hero[p]),GetUnitY(Hero[p]),BOT_SCAN_RADIUS,null)
    loop
        set u = FirstOfGroup(Scan)
        exitwhen u == null
        call GroupRemoveUnit(Scan,u)
        set owner = GetPlayerId(GetOwningPlayer(u))
        if owner < 12 and BotCanSee(p,u) then
            set health = GetWidgetLife(u)/GetUnitState(u,UNIT_STATE_MAX_LIFE)
            if IsUnitType(u,UNIT_TYPE_HERO) then
                set weight = (6.+I2R(IMinBJ(12,GetHeroLevel(u)/30)))*health
            elseif IsUnitType(u,UNIT_TYPE_STRUCTURE) then
                set weight = 3.*health
                if GetUnitTypeId(u) == 'fbst' then
                    set weight = 0.
                endif
            else
                set weight = (1.+RMinBJ(7.,GetUnitState(u,UNIT_STATE_MAX_LIFE)/3000.))*health
            endif
            if TeamOf(owner) == team then
                set BotAlliedPower[p] = BotAlliedPower[p]+weight
                if not IsUnitType(u,UNIT_TYPE_HERO) and not IsUnitType(u,UNIT_TYPE_STRUCTURE) and DistanceSq(GetUnitX(Hero[p]),GetUnitY(Hero[p]),GetUnitX(u),GetUnitY(u)) <= 490000 then
                    set BotNearbyTroops[p] = BotNearbyTroops[p]+1
                    if health < .65 then
                        set BotHurtTroops[p] = BotHurtTroops[p]+1
                    endif
                endif
            else
                set BotEnemyPower[p] = BotEnemyPower[p]+weight
                if not IsUnitType(u,UNIT_TYPE_STRUCTURE) and DistanceSq(GetUnitX(Hero[p]),GetUnitY(Hero[p]),GetUnitX(u),GetUnitY(u)) <= 810000 then
                    set score = health*500.+SquareRoot(DistanceSq(GetUnitX(Hero[p]),GetUnitY(Hero[p]),GetUnitX(u),GetUnitY(u)))
                    if IsUnitType(u,UNIT_TYPE_HERO) then
                        set score = score-1500.
                    endif
                    if score < bestScore then
                        set bestScore = score
                        set best = u
                    endif
                endif
            endif
        endif
    endloop
    // Bastions are dangerous before the hero reaches the inner scan radius.
    loop
        exitwhen k == 12
        if TeamOf(k) != team and BotCanSee(p,Bastion[k]) and DistanceSq(GetUnitX(Hero[p]),GetUnitY(Hero[p]),GetUnitX(Bastion[k]),GetUnitY(Bastion[k])) < I2R(BOT_TOWER_RADIUS*BOT_TOWER_RADIUS) then
            set BotEnemyPower[p] = BotEnemyPower[p]+25.
            set BotTowerDanger[p] = true
        endif
        set k = k+1
    endloop
    if TeamFocusUntil[team] > Seconds and BotCanSee(p,TeamFocus[team]) and DistanceSq(GetUnitX(Hero[p]),GetUnitY(Hero[p]),GetUnitX(TeamFocus[team]),GetUnitY(TeamFocus[team])) <= 810000 then
        if best == null or not IsUnitType(best,UNIT_TYPE_HERO) or GetWidgetLife(TeamFocus[team])/GetUnitState(TeamFocus[team],UNIT_STATE_MAX_LIFE) <= GetWidgetLife(best)/GetUnitState(best,UNIT_STATE_MAX_LIFE)+.15 then
            set best = TeamFocus[team]
        endif
    endif
    if best != null and IsUnitType(best,UNIT_TYPE_HERO) then
        set TeamFocus[team] = best
        set TeamFocusUntil[team] = Seconds+5
    elseif TeamFocusUntil[team] <= Seconds then
        set TeamFocus[team] = null
    endif
    set u = null
    set ReturnedUnit = best
    set best = null
    return ReturnedUnit
endfunction

function PlanBotTeam takes integer team returns nothing
    local integer p = team*3
    local integer members = 0
    local integer ready = 0
    if TeamPlanAt[team] > Seconds then
        return
    endif
    set TeamPlanAt[team] = Seconds+BOT_PLAN_SECONDS
    loop
        exitwhen p == team*3+3
        if SlotActive[p] and not Lost[p] then
            set members = members+1
            if Alive(Hero[p]) and GetWidgetLife(Hero[p])/GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE) >= .55 and RetreatUntil[p] <= Seconds and ShoppingUntil[p] <= Seconds and CastUntil[p] <= Seconds and DistanceSq(GetUnitX(Hero[p]),GetUnitY(Hero[p]),0,0) < 4840000 then
                set ready = ready+1
            endif
        endif
        set p = p+1
    endloop
    if Defending[team] then
        set TeamPushUntil[team] = 0
    elseif Seconds > WARMUP_SECONDS+180 and Seconds >= TeamPushReady[team] and ready >= IMinBJ(2,members) and ready > 0 then
        set TeamPushUntil[team] = Seconds+BOT_PUSH_SECONDS
        set TeamPushReady[team] = Seconds+BOT_PUSH_COOLDOWN
    endif
endfunction

function BotTeamCommand takes integer p, integer kind returns nothing
    local integer team = TeamOf(p)
    local integer k = team*3
    if Bot[p] or Lost[p] or not SlotActive[p] then
        return
    endif
    set TeamLeader[team] = p
    set TeamOrder[team] = kind
    set TeamOrderUntil[team] = Seconds+BOT_COMMAND_SECONDS
    loop
        exitwhen k == team*3+3
        if Bot[k] then
            set ShoppingUntil[k] = 0
        endif
        set k = k+1
    endloop
    if kind == 0 then
        call Tell(p,"Союзные боты снова действуют самостоятельно.")
    else
        call Tell(p,"Приказ союзным ботам принят на 90 секунд. Опасность и защита базы имеют приоритет. -follow / -defend / -push / -regroup / -free")
    endif
endfunction

function BotUseSupplies takes integer p returns boolean
    local integer slot = 0
    local integer id
    local item it
    local unit h = Hero[p]
    local real health = GetWidgetLife(h)/GetUnitState(h,UNIT_STATE_MAX_LIFE)
    loop
        exitwhen slot == 6
        set it = UnitItemInSlot(h,slot)
        if it != null then
            set id = GetItemTypeId(it)
            if (id == 'friv' and health < .28 and BotEnemyPower[p] > 0.) or (id == 'frrs' and (health < .60 or (GetUnitState(h,UNIT_STATE_MAX_MANA) > 0 and GetUnitState(h,UNIT_STATE_MANA) < GetUnitState(h,UNIT_STATE_MAX_MANA)*.25) or BotHurtTroops[p] >= 4)) or ((id == 'frat' or id == 'frdf') and BotNearbyTroops[p] >= 5 and BotEnemyPower[p] > 3.) or (id == 'fpH0' and health < .55) or (id == 'fpM0' and GetUnitState(h,UNIT_STATE_MAX_MANA) > 0 and GetUnitState(h,UNIT_STATE_MANA) < GetUnitState(h,UNIT_STATE_MAX_MANA)*.25) or (id == 'fshl' and BotHurtTroops[p] >= 4) or ((id == 'fsdm' or id == 'fsar') and BotNearbyTroops[p] >= 5 and BotEnemyPower[p] > 3.) then
                if UnitUseItem(h,it) then
                    set it = null
                    set h = null
                    return true
                endif
            endif
        endif
        set slot = slot+1
    endloop
    set it = null
    set h = null
    return false
endfunction

function BotBuySupplies takes integer p returns boolean
    local integer supply = 0
    local integer id
    local integer cost
    local integer reserve
    local integer slot = 0
    local boolean room = false
    local integer team = TeamOf(p)
    if Seconds < BotSupplyAt[p] or GearProgress[p] < 2 or TeamOrderUntil[team] > Seconds or TeamPushUntil[team] > Seconds or BotEnemyPower[p] > 0. or DistanceSq(GetUnitX(Hero[p]),GetUnitY(Hero[p]),FortressX[team],FortressY[team]) > 4840000 then
        return false
    endif
    if HeroBotRole[HeroKind[p]] == 0 then
        set supply = 2
        if BotStyle[p] == 1 then
            set supply = 3
        elseif BotStyle[p] == 2 then
            set supply = 4
        endif
    elseif HeroBotRole[HeroKind[p]] == 3 then
        set supply = 1
    endif
    set id = BotSupplyId[supply]
    set cost = BotSupplyCost[supply]
    if HeroItem(Hero[p],id) != null then
        return false
    endif
    if GearProgress[p] < 18 then
        set reserve = GearCost[DesiredGear(p)]
    elseif SuperProgress[p] < 6 then
        set reserve = SuperCost[DesiredSuper(p)]
    else
        set reserve = 0
    endif
    if GearSavings[p] < reserve+cost or GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)-BotTierReserve(p) < reserve+cost then
        return false
    endif
    loop
        exitwhen slot == 6
        if UnitItemInSlot(Hero[p],slot) == null then
            set room = true
        endif
        set slot = slot+1
    endloop
    if not room then
        return false
    endif
    if DistanceSq(GetUnitX(Hero[p]),GetUnitY(Hero[p]),UtilityX[team],UtilityY[team]) > 160000 then
        call IssuePointOrder(Hero[p],"move",UtilityX[team],UtilityY[team])
        return true
    endif
    call IssueNeutralTargetOrder(Player(p),UtilityShop[team],"neutralinteract",Hero[p])
    call IssueNeutralImmediateOrderById(Player(p),UtilityShop[team],id)
    if HeroItem(Hero[p],id) != null then
        set GearSavings[p] = GearSavings[p]-cost
        set BotSupplyAt[p] = Seconds+90
    else
        set BotSupplyAt[p] = Seconds+10
    endif
    return true
endfunction
