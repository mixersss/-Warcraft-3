// Four straightforward kits. Native passives, timed creatures and bounded aura updates.
function PetKillGold takes unit dead returns integer
    local integer raw = GetUnitTypeId(dead)
    if IsArmyUnit(dead) or not IsUnitType(dead,UNIT_TYPE_SUMMONED) or IsUnitType(dead,UNIT_TYPE_HERO) or IsUnitType(dead,UNIT_TYPE_STRUCTURE) or IsUnitIllusion(dead) or GetUnitDefaultMoveSpeed(dead) <= 0. then
        return 0
    endif
    if raw >= 'k200' and raw <= 'k231' then
        return SUMMON_ULTIMATE_KILL_GOLD
    endif
    return SUMMON_KILL_GOLD
endfunction
function CreativeClear takes integer p returns nothing
    set CreativeBuffUntil[p] = 0
    set CreativeBannerUntil[p] = 0
    set CreativeRainTicks[p] = 0
    set CreativeBladeTicks[p] = 0
    if Hero[p] != null then
        call UnitRemoveAbility(Hero[p],'Csum')
        call UnitRemoveAbility(Hero[p],'Cuba')
        call UnitRemoveAbility(Hero[p],'Cubd')
        call UnitRemoveAbility(Hero[p],'Crag')
    endif
endfunction
function CreativeSoldier takes unit u returns boolean
    return Alive(u) and not IsUnitType(u,UNIT_TYPE_HERO) and not IsUnitType(u,UNIT_TYPE_STRUCTURE) and GetUnitDefaultMoveSpeed(u) > 0. and not IsUnitIllusion(u) and (IsArmyUnit(u) or IsUnitType(u,UNIT_TYPE_SUMMONED))
endfunction
function CreativeHealArmy takes integer p, real fraction, real cap returns nothing
    local unit u = null
    local real amount = 0.
    call GroupEnumUnitsInRange(ExpansionGroup,GetUnitX(Hero[p]),GetUnitY(Hero[p]),900.,null)
    loop
        set u = FirstOfGroup(ExpansionGroup)
        exitwhen u == null
        call GroupRemoveUnit(ExpansionGroup,u)
        if CreativeSoldier(u) and IsUnitAlly(u,Player(p)) then
            set amount = RMinBJ(cap,GetUnitState(u,UNIT_STATE_MAX_LIFE)*fraction)
            call SetUnitState(u,UNIT_STATE_LIFE,RMinBJ(GetUnitState(u,UNIT_STATE_MAX_LIFE),GetWidgetLife(u)+amount))
        endif
    endloop
    set u = null
endfunction
function CreativeSummon takes integer p, integer family, integer rank returns nothing
    local integer n = 0
    local integer count = 2
    local unit u = null
    local real x = 0.
    local real y = 0.
    local real duration = 35.
    if family == 2 then
        set count = 1
        set duration = 45.
    endif
    set count = count+R2I(I2R(rank)/10.)
    loop
        exitwhen n == count
        set x = GetUnitX(Hero[p])+80.+I2R(ModuloInteger(n,4))*64.
        set y = GetUnitY(Hero[p])-160.+I2R(R2I(I2R(n)/4.))*64.
        if IsTerrainPathable(x,y,PATHING_TYPE_WALKABILITY) then
            set x = GetUnitX(Hero[p])
            set y = GetUnitY(Hero[p])
        endif
        set u = CreateUnit(Player(p),CreativePetType[family*200+rank-1],x,y,270.)
        call SetUnitPosition(u,x,y)
        call UnitAddType(u,UNIT_TYPE_SUMMONED)
        call UnitApplyTimedLife(u,'BTLF',duration)
        call IssuePointOrder(u,"attack",GetUnitX(Hero[p]),GetUnitY(Hero[p]))
        set n = n+1
    endloop
    call ExpansionImpact(p,"Abilities\\Spells\\Orc\\FeralSpirit\\feralspiritdone.mdl",GetUnitX(Hero[p]),GetUnitY(Hero[p]))
    set u = null
endfunction
function OnCreativeSpell takes nothing returns nothing
    local unit h = GetTriggerUnit()
    local integer p = GetPlayerId(GetOwningPlayer(h))
    local integer kind = 0
    local integer slot = 0
    local integer raw = GetSpellAbilityId()
    local integer rank = 0
    if Finished or p >= 12 or h != Hero[p] or not Alive(h) or GetTriggerEventId() != EVENT_PLAYER_UNIT_SPELL_EFFECT then
        set h = null
        return
    endif
    set kind = HeroKind[p]-46
    if kind < 0 or kind > 3 then
        set h = null
        return
    endif
    loop
        exitwhen slot == 4 or HeroSkill[HeroKind[p]*4+slot] == raw
        set slot = slot+1
    endloop
    set rank = GetUnitAbilityLevel(h,raw)
    if slot == 4 or rank == 0 then
        set h = null
        return
    endif
    if kind == 0 then
        if slot < 2 then
            call CreativeSummon(p,slot,rank)
        elseif slot == 2 then
            call UnitAddAbility(h,'Csum')
            call SetUnitAbilityLevel(h,'Csum',rank)
            set CreativeBuffUntil[p] = Seconds+10
        else
            call CreativeSummon(p,2,rank)
        endif
    elseif kind == 1 then
        if slot == 2 then
            call SetUnitState(h,UNIT_STATE_LIFE,RMinBJ(GetUnitState(h,UNIT_STATE_MAX_LIFE),GetWidgetLife(h)+RMinBJ(GetUnitState(h,UNIT_STATE_MAX_LIFE)*.05,60.+3.*rank)))
        elseif slot == 3 then
            set CreativeRainX[p] = GetSpellTargetX()
            set CreativeRainY[p] = GetSpellTargetY()
            set CreativeRainPower[p] = 45.+6.*rank
            set CreativeRainTicks[p] = 4
        endif
    elseif kind == 2 and slot == 3 then
        call UnitAddAbility(h,'Cuba')
        call UnitAddAbility(h,'Cubd')
        call SetUnitAbilityLevel(h,'Cuba',rank)
        call SetUnitAbilityLevel(h,'Cubd',rank)
        set CreativeBannerUntil[p] = Seconds+10
        call CreativeHealArmy(p,.10,120.+12.*rank)
        call ExpansionImpact(p,"Abilities\\Spells\\Human\\Resurrect\\ResurrectTarget.mdl",GetUnitX(h),GetUnitY(h))
    elseif kind == 3 then
        if slot == 1 then
            call UnitRemoveBuffs(h,false,true)
        elseif slot == 3 then
            call UnitAddAbility(h,'Crag')
            call SetUnitAbilityLevel(h,'Crag',rank)
            set CreativeBladePower[p] = 30.+7.*rank
            set CreativeBladeTicks[p] = 6
        endif
    endif
    set h = null
endfunction
function CreativeCache takes nothing returns nothing
    local integer p = 0
    local integer slot = 0
    local integer rank = 0
    local real percent = 0.
    loop
        exitwhen p == 12
        set CreativeVamp[p] = 0
        set CreativeRegen[p] = 0.
        if Alive(Hero[p]) and not Lost[p] then
            set percent = 0.
            if HeroKind[p] == 48 then
                set rank = GetUnitAbilityLevel(Hero[p],HeroSkill[48*4])
                if rank > 0 then
                    set percent = .12+.20*I2R(rank-1)/199.
                endif
                if CreativeBannerUntil[p] > Seconds then
                    set percent = percent+.10
                endif
                set rank = GetUnitAbilityLevel(Hero[p],HeroSkill[48*4+2])
                if rank > 0 then
                    set CreativeRegen[p] = 1.+7.*I2R(rank-1)/199.
                endif
            endif
            set slot = 0
            loop
                exitwhen slot == 6
                if GetItemTypeId(UnitItemInSlot(Hero[p],slot)) == 'fvlm' then
                    set percent = RMaxBJ(percent,.15)
                endif
                set slot = slot+1
            endloop
            set CreativeVamp[p] = IMinBJ(420,R2I(percent*1000.+.5))
        endif
        set p = p+1
    endloop
endfunction
function CreativePlayerTick takes nothing returns nothing
    local integer p = 0
    local integer source = 0
    local integer vamp = 0
    local real regen = 0.
    local unit u = null
    loop
        exitwhen p == 12 or GetTriggeringTrigger() == CreativeThread[p]
        set p = p+1
    endloop
    if p == 12 then
        return
    endif
    if not Alive(Hero[p]) then
        call CreativeClear(p)
    else
        if CreativeBuffUntil[p] > 0 and Seconds >= CreativeBuffUntil[p] then
            call UnitRemoveAbility(Hero[p],'Csum')
            set CreativeBuffUntil[p] = 0
        endif
        if CreativeBannerUntil[p] > 0 and Seconds >= CreativeBannerUntil[p] then
            call UnitRemoveAbility(Hero[p],'Cuba')
            call UnitRemoveAbility(Hero[p],'Cubd')
            set CreativeBannerUntil[p] = 0
        endif
        if CreativeRainTicks[p] > 0 then
            call ExpansionArea(p,CreativeRainX[p],CreativeRainY[p],400.,CreativeRainPower[p],0)
            call ExpansionImpact(p,"Abilities\\Spells\\NightElf\\Starfall\\StarfallTarget.mdl",CreativeRainX[p],CreativeRainY[p])
            set CreativeRainTicks[p] = CreativeRainTicks[p]-1
        endif
        if CreativeBladeTicks[p] > 0 then
            call ExpansionArea(p,GetUnitX(Hero[p]),GetUnitY(Hero[p]),280.,CreativeBladePower[p],0)
            call ExpansionImpact(p,"Abilities\\Spells\\Other\\Cleave\\CleaveDamageTarget.mdl",GetUnitX(Hero[p]),GetUnitY(Hero[p]))
            set CreativeBladeTicks[p] = CreativeBladeTicks[p]-1
            if CreativeBladeTicks[p] == 0 then
                call UnitRemoveAbility(Hero[p],'Crag')
            endif
        endif
    endif
    // Reuse one group. Re-evaluate every owned army unit to remove stale auras too.
    call GroupEnumUnitsOfPlayer(CreativeOwnerGroup,Player(p),null)
    loop
        set u = FirstOfGroup(CreativeOwnerGroup)
        exitwhen u == null
        call GroupRemoveUnit(CreativeOwnerGroup,u)
        set vamp = 0
        set regen = 0.
        if CreativeSoldier(u) then
            set source = 0
            loop
                exitwhen source == 12
                if (CreativeVamp[source] > 0 or CreativeRegen[source] > 0.) and Alive(Hero[source]) and IsUnitAlly(u,Player(source)) and DistanceSq(GetUnitX(u),GetUnitY(u),GetUnitX(Hero[source]),GetUnitY(Hero[source])) <= 810000. then
                    set vamp = IMaxBJ(vamp,CreativeVamp[source])
                    set regen = RMaxBJ(regen,CreativeRegen[source])
                endif
                set source = source+1
            endloop
            if regen > 0. then
                call SetUnitState(u,UNIT_STATE_LIFE,RMinBJ(GetUnitState(u,UNIT_STATE_MAX_LIFE),GetWidgetLife(u)+regen))
            endif
            if GetUnitTypeId(u) >= 'k000' and GetUnitTypeId(u) <= 'k231' and GetUnitCurrentOrder(u) == 0 and Alive(Hero[p]) then
                call IssuePointOrder(u,"attack",GetUnitX(Hero[p]),GetUnitY(Hero[p]))
            endif
        endif
        if vamp > 0 then
            if GetUnitAbilityLevel(u,'Clif') == 0 then
                call UnitAddAbility(u,'Clif')
            endif
            if GetUnitAbilityLevel(u,'Clif') != vamp then
                call SetUnitAbilityLevel(u,'Clif',vamp)
            endif
        elseif GetUnitAbilityLevel(u,'Clif') > 0 then
            call UnitRemoveAbility(u,'Clif')
        endif
    endloop
    set u = null
endfunction
function CreativeInit takes nothing returns nothing
    local integer p = 0
    if ExpansionGroup == null then
        set ExpansionGroup = CreateGroup()
    endif
    if CreativeOwnerGroup == null then
        set CreativeOwnerGroup = CreateGroup()
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
    call CreativeCache()
    loop
        exitwhen p == 12
        call TriggerExecute(CreativeThread[p])
        set p = p+1
    endloop
endfunction
