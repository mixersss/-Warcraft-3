// Three original kits. One static thread per player, no per-cast handles/groups/timers.
function CreativeRemoveNodes takes integer p returns nothing
    if CreativeArtA[p] != null then
        call DestroyEffect(CreativeArtA[p])
        set CreativeArtA[p] = null
    endif
    if CreativeArtB[p] != null then
        call DestroyEffect(CreativeArtB[p])
        set CreativeArtB[p] = null
    endif
    set CreativeAUntil[p] = 0
    set CreativeBUntil[p] = 0
endfunction
function CreativeClear takes integer p returns nothing
    call CreativeRemoveNodes(p)
    set CreativeBookUntil[p] = 0
    set CreativeDebt[p] = null
    set CreativeZoneTicks[p] = 0
    set CreativeBank[p] = 0.
endfunction
function CreativeHurt takes integer p, unit target, real power returns real
    local real before = 0.
    if not ExpansionEnemy(target,p) then
        return 0.
    endif
    set before = GetWidgetLife(target)
    call UnitDamageTarget(Hero[p],target,power,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS)
    return RMaxBJ(0.,before-RMaxBJ(0.,GetWidgetLife(target)))
endfunction
function CreativeLineDistance takes real x, real y, real ax, real ay, real bx, real by returns real
    local real dx = bx-ax
    local real dy = by-ay
    local real t = 0.
    if dx*dx+dy*dy < 1. then
        return SquareRoot((x-ax)*(x-ax)+(y-ay)*(y-ay))
    endif
    set t = RMaxBJ(0.,RMinBJ(1.,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy)))
    set dx = x-(ax+t*dx)
    set dy = y-(ay+t*dy)
    return SquareRoot(dx*dx+dy*dy)
endfunction
function CreativeGeometry takes integer p, integer rank, boolean triangle returns nothing
    local unit u = null
    local real ax = CreativeAX[p]
    local real ay = CreativeAY[p]
    local real bx = CreativeBX[p]
    local real by = CreativeBY[p]
    local real cx = GetUnitX(Hero[p])
    local real cy = GetUnitY(Hero[p])
    local real x = 0.
    local real y = 0.
    local real crossA = 0.
    local real crossB = 0.
    local real crossC = 0.
    local real ignored = 0.
    local boolean inside = false
    if triangle and RAbsBJ((bx-ax)*(cy-ay)-(by-ay)*(cx-ax)) < 100. then
        return
    endif
    call GroupEnumUnitsInRange(ExpansionGroup,ax,ay,1800.,null)
    loop
        set u = FirstOfGroup(ExpansionGroup)
        exitwhen u == null
        call GroupRemoveUnit(ExpansionGroup,u)
        if ExpansionEnemy(u,p) then
            set x = GetUnitX(u)
            set y = GetUnitY(u)
            if triangle then
                set crossA = (bx-ax)*(y-ay)-(by-ay)*(x-ax)
                set crossB = (cx-bx)*(y-by)-(cy-by)*(x-bx)
                set crossC = (ax-cx)*(y-cy)-(ay-cy)*(x-cx)
                set inside = (crossA > 0. and crossB > 0. and crossC > 0.) or (crossA < 0. and crossB < 0. and crossC < 0.)
                if inside then
                    set ignored = CreativeHurt(p,u,120.+18.*rank)
                endif
            elseif CreativeLineDistance(x,y,ax,ay,bx,by) <= 90. then
                set ignored = CreativeHurt(p,u,30.+4.*rank)
            endif
        endif
    endloop
    set u = null
endfunction
function CreativePatch takes integer p, integer rank returns nothing
    local unit u = null
    local real amount = 0.
    call GroupEnumUnitsInRange(ExpansionGroup,GetUnitX(Hero[p]),GetUnitY(Hero[p]),500.,null)
    loop
        set u = FirstOfGroup(ExpansionGroup)
        exitwhen u == null
        call GroupRemoveUnit(ExpansionGroup,u)
        if Alive(u) and IsUnitAlly(u,Player(p)) and not IsUnitType(u,UNIT_TYPE_STRUCTURE) and (IsArmyUnit(u) or IsUnitType(u,UNIT_TYPE_HERO)) then
            set amount = RMinBJ(CreativeBank[p],RMinBJ(60.+4.*rank,GetUnitState(u,UNIT_STATE_MAX_LIFE)-GetWidgetLife(u)))
            if amount > 0. then
                call SetUnitState(u,UNIT_STATE_LIFE,GetWidgetLife(u)+amount)
                set CreativeBank[p] = CreativeBank[p]-amount
            endif
        endif
    endloop
    set u = null
endfunction
function CreativeReturn takes integer p returns nothing
    local unit h = Hero[p]
    local real hp = GetWidgetLife(h)
    local real mp = GetUnitState(h,UNIT_STATE_MANA)
    if Alive(h) then
        if (HeroSector[p] == CreativeBookSector[p] or HeroSector[p] == -1 or CreativeBookSector[p] == -1) and not IsTerrainPathable(CreativeBookX[p],CreativeBookY[p],PATHING_TYPE_WALKABILITY) then
            call SetUnitPosition(h,CreativeBookX[p],CreativeBookY[p])
            set PreviousHeroX[p] = GetUnitX(h)
            set PreviousHeroY[p] = GetUnitY(h)
            set HeroSector[p] = CreativeBookSector[p]
        endif
        call SetUnitState(h,UNIT_STATE_LIFE,RMinBJ(GetUnitState(h,UNIT_STATE_MAX_LIFE),hp+RMaxBJ(0.,RMinBJ(CreativeBookHP[p]-hp,80.+8.*CreativeBookRank[p]))))
        call SetUnitState(h,UNIT_STATE_MANA,RMinBJ(GetUnitState(h,UNIT_STATE_MAX_MANA),mp+RMaxBJ(0.,RMinBJ(CreativeBookMP[p]-mp,30.+2.*CreativeBookRank[p]))))
        call ExpansionImpact(p,"Abilities\\Spells\\Human\\MassTeleport\\MassTeleportTarget.mdl",GetUnitX(h),GetUnitY(h))
    endif
    set CreativeBookUntil[p] = 0
    if CreativeArtA[p] != null then
        call DestroyEffect(CreativeArtA[p])
        set CreativeArtA[p] = null
    endif
    set h = null
endfunction
function OnCreativeSpell takes nothing returns nothing
    local unit h = GetTriggerUnit()
    local unit target = GetSpellTargetUnit()
    local integer p = GetPlayerId(GetOwningPlayer(h))
    local integer kind = 0
    local integer raw = GetSpellAbilityId()
    local integer slot = 0
    local integer rank = 0
    local real amount = 0.
    local real total = 0.
    local real maxTotal = 0.
    local real x = GetSpellTargetX()
    local real y = GetSpellTargetY()
    if Finished or GetTriggerEventId() != EVENT_PLAYER_UNIT_SPELL_EFFECT or p >= 12 or h != Hero[p] or not Alive(h) then
        set h = null
        set target = null
        return
    endif
    set kind = HeroKind[p]-46
    if kind < 0 or kind > 2 then
        set h = null
        set target = null
        return
    endif
    loop
        exitwhen slot == 4 or HeroSkill[HeroKind[p]*4+slot] == raw
        set slot = slot+1
    endloop
    set rank = GetUnitAbilityLevel(h,raw)
    if slot == 4 or rank == 0 then
        set h = null
        set target = null
        return
    endif
    if kind == 0 then
        if slot == 0 then
            call CreativeRemoveNodes(p)
            set CreativeBookX[p] = GetUnitX(h)
            set CreativeBookY[p] = GetUnitY(h)
            set CreativeBookHP[p] = GetWidgetLife(h)
            set CreativeBookMP[p] = GetUnitState(h,UNIT_STATE_MANA)
            set CreativeBookRank[p] = rank
            set CreativeBookSector[p] = HeroSector[p]
            set CreativeBookUntil[p] = Seconds+6
            set CreativeArtA[p] = AddSpecialEffect("Abilities\\Spells\\Human\\MassTeleport\\MassTeleportTarget.mdl",GetUnitX(h),GetUnitY(h))
        elseif slot == 1 and ExpansionEnemy(target,p) then
            set CreativeDebt[p] = target
            set CreativeDebtX[p] = GetUnitX(target)
            set CreativeDebtY[p] = GetUnitY(target)
            set CreativeDebtDistance[p] = 0.
            set CreativeDebtRank[p] = rank
            set CreativeDebtUntil[p] = Seconds+4
        elseif slot == 2 or slot == 3 then
            set CreativeZoneMode[p] = slot-2
            set CreativeZonePower[p] = 15.+2.*rank
            set CreativeZoneTicks[p] = 3
            set CreativeZoneAt[p] = Seconds+2
            set CreativeZoneX[p] = x
            set CreativeZoneY[p] = y
            if slot == 3 then
                set CreativeZoneX[p] = GetUnitX(h)
                set CreativeZoneY[p] = GetUnitY(h)
                set CreativeEchoX[p] = CreativeZoneX[p]
                set CreativeEchoY[p] = CreativeZoneY[p]
                if CreativeBookUntil[p] > Seconds then
                    set CreativeEchoX[p] = CreativeBookX[p]
                    set CreativeEchoY[p] = CreativeBookY[p]
                endif
                set CreativeZonePower[p] = 30.+5.*rank
                set CreativeZoneTicks[p] = 4
                set CreativeZoneAt[p] = Seconds+1
            endif
            call ExpansionImpact(p,"Abilities\\Spells\\Other\\Monsoon\\MonsoonBoltTarget.mdl",CreativeZoneX[p],CreativeZoneY[p])
        endif
    elseif kind == 1 then
        if slot == 0 then
            set amount = CreativeHurt(p,target,45.+4.*rank)
            set CreativeBank[p] = RMinBJ(200.+10.*GetHeroLevel(h),CreativeBank[p]+amount*.4)
        elseif slot == 1 and Alive(target) and IsUnitAlly(target,Player(p)) and IsUnitType(target,UNIT_TYPE_HERO) and DistanceSq(GetUnitX(h),GetUnitY(h),GetUnitX(target),GetUnitY(target)) <= 490000. then
            set total = GetWidgetLife(h)+GetWidgetLife(target)
            set maxTotal = GetUnitState(h,UNIT_STATE_MAX_LIFE)+GetUnitState(target,UNIT_STATE_MAX_LIFE)
            if target != h and maxTotal > 0. then
                set amount = RMaxBJ(1.,RMinBJ(GetUnitState(h,UNIT_STATE_MAX_LIFE),GetWidgetLife(h)+(total*GetUnitState(h,UNIT_STATE_MAX_LIFE)/maxTotal-GetWidgetLife(h))*RMinBJ(1.,.25+.00375*rank)))
                // Both participants are alive; preserve total HP and leave at least .406 to each.
                set amount = RMinBJ(amount,total-.406)
                call SetUnitState(h,UNIT_STATE_LIFE,amount)
                call SetUnitState(target,UNIT_STATE_LIFE,total-amount)
            endif
        elseif slot == 2 then
            call CreativePatch(p,rank)
        elseif slot == 3 then
            set amount = RMinBJ(CreativeBank[p],300.+30.*rank)
            set CreativeBank[p] = CreativeBank[p]-amount
            call ExpansionArea(p,GetUnitX(h),GetUnitY(h),500.,80.+8.*rank+amount*.5,0)
        endif
        call ExpansionImpact(p,"Abilities\\Spells\\Undead\\AnimateDead\\AnimateDeadTarget.mdl",GetUnitX(h),GetUnitY(h))
    else
        if slot == 0 then
            call CreativeRemoveNodes(p)
            set CreativeAX[p] = x
            set CreativeAY[p] = y
            set CreativeAUntil[p] = Seconds+14
            set CreativeArtA[p] = AddSpecialEffect("Abilities\\Spells\\Human\\MassTeleport\\MassTeleportTarget.mdl",x,y)
            call ExpansionArea(p,x,y,180.,20.+3.*rank,0)
        elseif slot == 1 and CreativeAUntil[p] > Seconds and DistanceSq(x,y,CreativeAX[p],CreativeAY[p]) <= 1960000. then
            if CreativeArtB[p] != null then
                call DestroyEffect(CreativeArtB[p])
            endif
            set CreativeBX[p] = x
            set CreativeBY[p] = y
            set CreativeBUntil[p] = Seconds+12
            set CreativeArtB[p] = AddSpecialEffect("Abilities\\Spells\\Other\\Drain\\DrainCaster.mdl",x,y)
            call CreativeGeometry(p,rank,false)
        elseif slot == 2 and CreativeAUntil[p] > Seconds and CreativeBUntil[p] > Seconds then
            set amount = 30.+2.*rank+RMinBJ(140.,SquareRoot(DistanceSq(CreativeAX[p],CreativeAY[p],CreativeBX[p],CreativeBY[p]))*.1)
            call SetUnitState(h,UNIT_STATE_LIFE,RMinBJ(GetUnitState(h,UNIT_STATE_MAX_LIFE),GetWidgetLife(h)+amount))
            call DestroyEffect(CreativeArtB[p])
            set CreativeArtB[p] = null
            set CreativeBUntil[p] = 0
        elseif slot == 3 and CreativeAUntil[p] > Seconds and CreativeBUntil[p] > Seconds and DistanceSq(GetUnitX(h),GetUnitY(h),CreativeAX[p],CreativeAY[p]) <= 2560000. then
            call CreativeGeometry(p,rank,true)
            call ExpansionImpact(p,"Abilities\\Spells\\Human\\Thunderclap\\ThunderClapCaster.mdl",GetUnitX(h),GetUnitY(h))
            call CreativeRemoveNodes(p)
        endif
    endif
    set h = null
    set target = null
endfunction
function CreativePlayerTick takes nothing returns nothing
    local integer p = 0
    local unit u = null
    local real distance = 0.
    local real power = 0.
    local real ignored = 0.
    loop
        exitwhen p == 12 or GetTriggeringTrigger() == CreativeThread[p]
        set p = p+1
    endloop
    if p == 12 then
        return
    endif
    if Finished or not Alive(Hero[p]) then
        call CreativeClear(p)
        return
    endif
    if CreativeBookUntil[p] > 0 and Seconds >= CreativeBookUntil[p] then
        call CreativeReturn(p)
    endif
    if CreativeDebt[p] != null then
        set u = CreativeDebt[p]
        if ExpansionEnemy(u,p) then
            set distance = SquareRoot(DistanceSq(CreativeDebtX[p],CreativeDebtY[p],GetUnitX(u),GetUnitY(u)))
            set CreativeDebtDistance[p] = RMinBJ(1200.,CreativeDebtDistance[p]+distance)
            set CreativeDebtX[p] = GetUnitX(u)
            set CreativeDebtY[p] = GetUnitY(u)
            if Seconds >= CreativeDebtUntil[p] then
                set ignored = CreativeHurt(p,u,25.+4.*CreativeDebtRank[p]+CreativeDebtDistance[p]*(8.+.5*CreativeDebtRank[p])/100.)
                set CreativeDebt[p] = null
            endif
        else
            set CreativeDebt[p] = null
        endif
    endif
    if CreativeZoneTicks[p] > 0 and Seconds >= CreativeZoneAt[p] then
        set power = CreativeZonePower[p]
        if CreativeZoneMode[p] == 0 then
            if CreativeZoneTicks[p] == 1 and DistanceSq(GetUnitX(Hero[p]),GetUnitY(Hero[p]),CreativeZoneX[p],CreativeZoneY[p]) <= 78400. then
                set power = power*2.
            endif
            call ExpansionArea(p,CreativeZoneX[p],CreativeZoneY[p],280.,power,0)
        else
            call ExpansionArea(p,CreativeZoneX[p],CreativeZoneY[p],300.,power,0)
            call ExpansionArea(p,CreativeEchoX[p],CreativeEchoY[p],300.,power,0)
        endif
        call ExpansionImpact(p,"Abilities\\Spells\\Other\\Monsoon\\MonsoonBoltTarget.mdl",CreativeZoneX[p],CreativeZoneY[p])
        set CreativeZoneTicks[p] = CreativeZoneTicks[p]-1
        set CreativeZoneAt[p] = Seconds+1
    endif
    if HeroKind[p] == 48 then
        if CreativeAUntil[p] > 0 and Seconds >= CreativeAUntil[p] then
            call CreativeRemoveNodes(p)
        elseif CreativeBUntil[p] > 0 and Seconds >= CreativeBUntil[p] then
            call DestroyEffect(CreativeArtB[p])
            set CreativeArtB[p] = null
            set CreativeBUntil[p] = 0
        endif
    endif
    set u = null
endfunction
function CreativeInit takes nothing returns nothing
    local integer p = 0
    if ExpansionGroup == null then
        set ExpansionGroup = CreateGroup()
    endif
    loop
        exitwhen p == 12
        set CreativeThread[p] = CreateTrigger()
        call TriggerAddAction(CreativeThread[p],function CreativePlayerTick)
        set p = p+1
    endloop
endfunction
function CreativeTick takes nothing returns nothing
    local integer p = 0
    loop
        exitwhen p == 12
        call TriggerExecute(CreativeThread[p])
        set p = p+1
    endloop
endfunction
