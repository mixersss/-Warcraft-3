// Shared native stores: one role item and situational supplies, paid from equipment income.
function ArenaItemIndex takes integer raw returns integer
    local integer k = 0
    loop
        exitwhen k == 8
        if ArenaItemId[k] == raw then
            return k
        endif
        set k = k+1
    endloop
    return -1
endfunction

function BotArenaShop takes integer p returns boolean
    local unit h = Hero[p]
    local integer choice
    local integer role = HeroBotRole[HeroKind[p]]
    local integer slot = 0
    local integer price
    local integer cheapest = 2147480000
    local integer reserve = 0
    local integer store
    local real x
    local item old = null
    local item candidate = null
    local boolean room = false
    if not Alive(h) or GearProgress[p] < 3 or Seconds < ArenaShopAt[p] or BotEnemyPower[p] > 0. or TeamPushUntil[TeamOf(p)] > Seconds or DistanceSq(GetUnitX(h),GetUnitY(h),0,0) > 4840000 then
        set h = null
        return false
    endif
    if not ArenaRelicBought[p] then
        set choice = 0
        if role == 0 then
            set choice = 3
        elseif role == 2 then
            set choice = 2
        elseif role == 3 then
            set choice = 1
        endif
        set store = 0
        set x = -720.
    else
        set choice = 6
        if role == 0 then
            set choice = 4+ModuloInteger(BotStyle[p],2)
        elseif role == 1 or role == 2 then
            set choice = 7
        endif
        set store = 1
        set x = 720.
        if GearProgress[p] < 18 then
            set reserve = IMinBJ(2000,GearCost[DesiredGear(p)]/3)
        elseif SuperProgress[p] < 6 then
            set reserve = 2000
        endif
    endif
    if HeroItem(h,ArenaItemId[choice]) != null then
        set h = null
        return false
    endif
    if GearSavings[p] < ArenaItemCost[choice]+reserve or GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)-BotTierReserve(p) < ArenaItemCost[choice]+reserve then
        set h = null
        return false
    endif
    loop
        exitwhen slot == 6
        set candidate = UnitItemInSlot(h,slot)
        if candidate == null then
            set room = true
        elseif store == 0 then
            set price = RegularGearCost(GetItemTypeId(candidate))
            if price > 0 and price < ArenaItemCost[choice] and price < cheapest then
                set old = candidate
                set cheapest = price
            endif
        endif
        set slot = slot+1
    endloop
    if not room and old == null then
        set h = null
        set candidate = null
        return false
    endif
    if DistanceSq(GetUnitX(h),GetUnitY(h),x,320.) > 160000 then
        call IssuePointOrder(h,"move",x,320.)
        set h = null
        set candidate = null
        set old = null
        return true
    endif
    if not room then
        set room = UnitDropItemTarget(h,old,ArenaStore[store])
    endif
    if room then
        call IssueNeutralTargetOrder(Player(p),ArenaStore[store],"neutralinteract",h)
        call IssueNeutralImmediateOrderById(Player(p),ArenaStore[store],ArenaItemId[choice])
        if HeroItem(h,ArenaItemId[choice]) != null then
            set GearSavings[p] = GearSavings[p]-ArenaItemCost[choice]
            if store == 0 then
                set ArenaRelicBought[p] = true
            endif
            set ArenaShopAt[p] = Seconds+180
        else
            set ArenaShopAt[p] = Seconds+15
        endif
    endif
    set candidate = null
    set old = null
    set h = null
    return room
endfunction
