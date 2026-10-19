// Ten creature heroes. State is bounded by 12 player slots and one shared group.
// No per-cast timers, triggers, locations, free items or permanent unit bonuses.
function ExpansionClearPrey takes integer p returns nothing
    set ExpansionPrey[p] = null
    set ExpansionPreyUntil[p] = 0
    if ExpansionPreyArt[p] != null then
        call DestroyEffect(ExpansionPreyArt[p])
        set ExpansionPreyArt[p] = null
    endif
endfunction
function ExpansionClear takes integer p returns nothing
    call ExpansionClearPrey(p)
    if ExpansionZoneArt[p] != null then
        call DestroyEffect(ExpansionZoneArt[p])
        set ExpansionZoneArt[p] = null
    endif
    if ExpansionCastArt[p] != null then
        call DestroyEffect(ExpansionCastArt[p])
        set ExpansionCastArt[p] = null
    endif
    if Hero[p] != null and ExpansionWarcryUntil[p] > 0 then
        call UnitRemoveAbility(Hero[p],'Fxwr')
    endif
    set ExpansionTicks[p] = 0
    set ExpansionCharges[p] = 0
    set ExpansionChargeUntil[p] = 0
    set ExpansionWarcryUntil[p] = 0
endfunction
function ExpansionFlash takes integer p, integer kind returns nothing
    if ExpansionCastArt[p] != null then
        call DestroyEffect(ExpansionCastArt[p])
    endif
    set ExpansionCastArt[p] = AddSpecialEffectTarget(ExpansionEffect[kind],Hero[p],"origin")
    set ExpansionCastUntil[p] = Seconds+1
endfunction
function ExpansionImpact takes integer p, string model, real x, real y returns nothing
    if ExpansionCastArt[p] != null then
        call DestroyEffect(ExpansionCastArt[p])
    endif
    set ExpansionCastArt[p] = AddSpecialEffect(model,x,y)
    set ExpansionCastUntil[p] = Seconds+1
endfunction
function ExpansionEnemy takes unit u, integer p returns boolean
    return Alive(u) and IsUnitEnemy(u,Player(p)) and not IsUnitType(u,UNIT_TYPE_STRUCTURE) and not IsUnitType(u,UNIT_TYPE_MAGIC_IMMUNE) and GetUnitAbilityLevel(u,'Avul') == 0
endfunction
// mode 0 damage, 1 heal soldiers, 2 pull ground enemies, 3 restore hero mana.
function ExpansionArea takes integer p, real x, real y, real radius, real power, integer mode returns nothing
    local unit u = null
    local real dx = 0.
    local real dy = 0.
    local real distance = 0.
    local real tx = 0.
    local real ty = 0.
    if ExpansionGroup == null then
        set ExpansionGroup = CreateGroup()
    endif
    call GroupEnumUnitsInRange(ExpansionGroup,x,y,radius,null)
    loop
        set u = FirstOfGroup(ExpansionGroup)
        exitwhen u == null
        call GroupRemoveUnit(ExpansionGroup,u)
        if mode == 0 and ExpansionEnemy(u,p) then
            call UnitDamageTarget(Hero[p],u,power,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS)
        elseif mode == 1 and Alive(u) and IsArmyUnit(u) and IsUnitAlly(u,Player(p)) then
            call SetUnitState(u,UNIT_STATE_LIFE,RMinBJ(GetUnitState(u,UNIT_STATE_MAX_LIFE),GetWidgetLife(u)+power))
        elseif mode == 2 and ExpansionEnemy(u,p) and not IsUnitType(u,UNIT_TYPE_FLYING) then
            set dx = x-GetUnitX(u)
            set dy = y-GetUnitY(u)
            set distance = SquareRoot(dx*dx+dy*dy)
            if distance > XH_PULL_MIN_DISTANCE then
                set tx = GetUnitX(u)+dx/distance*XH_PULL_DISTANCE
                set ty = GetUnitY(u)+dy/distance*XH_PULL_DISTANCE
                if not IsTerrainPathable(tx,ty,PATHING_TYPE_WALKABILITY) and not IsTerrainPathable((tx+GetUnitX(u))*.5,(ty+GetUnitY(u))*.5,PATHING_TYPE_WALKABILITY) then
                    call SetUnitX(u,tx)
                    call SetUnitY(u,ty)
                endif
            endif
        elseif mode == 3 and Alive(u) and IsUnitType(u,UNIT_TYPE_HERO) and IsUnitAlly(u,Player(p)) then
            call SetUnitState(u,UNIT_STATE_MANA,RMinBJ(GetUnitState(u,UNIT_STATE_MAX_MANA),GetUnitState(u,UNIT_STATE_MANA)+power))
        endif
    endloop
    set u = null
endfunction
function ExpansionOnDeath takes unit dead, unit killer returns nothing
    local integer p = 0
    if Finished then
        return
    endif
    loop
        exitwhen p == 12
        if dead == Hero[p] then
            call ExpansionClear(p)
        elseif dead == ExpansionPrey[p] then
            if ExpansionPreyUntil[p] > Seconds and Alive(Hero[p]) and killer != null and IsUnitAlly(killer,Player(p)) and IsUnitEnemy(dead,Player(p)) then
                call SetUnitState(Hero[p],UNIT_STATE_LIFE,RMinBJ(GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE),GetWidgetLife(Hero[p])+XH_HUNT_HP_BASE+XH_HUNT_HP_STEP*ExpansionPreyRank[p]))
                call SetUnitState(Hero[p],UNIT_STATE_MANA,RMinBJ(GetUnitState(Hero[p],UNIT_STATE_MAX_MANA),GetUnitState(Hero[p],UNIT_STATE_MANA)+XH_HUNT_MANA_BASE+XH_HUNT_MANA_STEP*ExpansionPreyRank[p]))
                call ExpansionFlash(p,3)
            endif
            call ExpansionClearPrey(p)
        endif
        set p = p+1
    endloop
endfunction
function OnExpansionSpell takes nothing returns nothing
    local unit caster = GetTriggerUnit()
    local unit target = GetSpellTargetUnit()
    local integer p = GetPlayerId(GetOwningPlayer(caster))
    local integer raw = GetSpellAbilityId()
    local integer kind = 0
    local integer rank = 0
    local integer slot = 0
    local real amount = 0.
    local boolean known = false
    if Finished or GetTriggerEventId() != EVENT_PLAYER_UNIT_SPELL_EFFECT or p >= 12 or caster != Hero[p] or not Alive(caster) then
        set caster = null
        set target = null
        return
    endif
    set kind = HeroKind[p]-EXPANSION_FIRST_HERO
    if kind < 0 or kind >= 10 then
        set caster = null
        set target = null
        return
    endif
    set rank = GetUnitAbilityLevel(caster,raw)
    if rank < 1 then
        set caster = null
        set target = null
        return
    endif
    if kind == 7 then
        loop
            exitwhen slot == 4
            if raw == HeroSkill[HeroKind[p]*4+slot] then
                set known = true
            endif
            set slot = slot+1
        endloop
        if known then
            if Seconds >= ExpansionChargeUntil[p] then
                set ExpansionCharges[p] = 0
            endif
            set ExpansionCharges[p] = ExpansionCharges[p]+1
            set ExpansionChargeUntil[p] = Seconds+XH_OVERLOAD_SECONDS
            call ExpansionFlash(p,kind)
            if ExpansionCharges[p] >= XH_OVERLOAD_CASTS then
                set ExpansionCharges[p] = 0
                call ExpansionImpact(p,"Abilities\\Spells\\Other\\Monsoon\\MonsoonBoltTarget.mdl",GetUnitX(caster),GetUnitY(caster))
                call ExpansionArea(p,GetUnitX(caster),GetUnitY(caster),XH_OVERLOAD_RADIUS,XH_OVERLOAD_DAMAGE_BASE+XH_OVERLOAD_DAMAGE_STEP*rank,0)
            endif
        endif
    elseif raw == HeroSkill[HeroKind[p]*4+ExpansionSlot[kind]] then
        if kind == 0 or kind == 4 then
            if ExpansionZoneArt[p] != null then
                call DestroyEffect(ExpansionZoneArt[p])
            endif
            if kind == 0 then
                set ExpansionX[p] = GetUnitX(caster)
                set ExpansionY[p] = GetUnitY(caster)
                set ExpansionTicks[p] = 1
                set ExpansionZoneAt[p] = Seconds+XH_AFTERSHOCK_DELAY_SECONDS
                set ExpansionDamage[p] = XH_AFTERSHOCK_DAMAGE_BASE+XH_AFTERSHOCK_DAMAGE_STEP*rank
            else
                set ExpansionX[p] = GetSpellTargetX()
                set ExpansionY[p] = GetSpellTargetY()
                set ExpansionTicks[p] = XH_EMBERS_SECONDS
                set ExpansionZoneAt[p] = Seconds+1
                set ExpansionDamage[p] = XH_EMBERS_DAMAGE_BASE+XH_EMBERS_DAMAGE_STEP*rank
            endif
            if kind == 0 then
                set ExpansionZoneArt[p] = AddSpecialEffect("Abilities\\Spells\\Orc\\EarthQuake\\EarthQuakeTarget.mdl",ExpansionX[p],ExpansionY[p])
            else
                set ExpansionZoneArt[p] = AddSpecialEffect(ExpansionEffect[kind],ExpansionX[p],ExpansionY[p])
            endif
        elseif kind == 1 and ExpansionEnemy(target,p) then
            set amount = RMinBJ(GetUnitState(target,UNIT_STATE_MANA),XH_MANASTEAL_BASE+XH_MANASTEAL_STEP*rank)
            call SetUnitState(target,UNIT_STATE_MANA,GetUnitState(target,UNIT_STATE_MANA)-amount)
            call SetUnitState(caster,UNIT_STATE_MANA,RMinBJ(GetUnitState(caster,UNIT_STATE_MAX_MANA),GetUnitState(caster,UNIT_STATE_MANA)+amount))
            call ExpansionFlash(p,kind)
        elseif kind == 2 then
            call SetUnitState(caster,UNIT_STATE_LIFE,RMaxBJ(1.,GetWidgetLife(caster)*(1.-XH_BLOODPACT_HP_FRACTION)))
            call SetUnitState(caster,UNIT_STATE_MANA,RMinBJ(GetUnitState(caster,UNIT_STATE_MAX_MANA),GetUnitState(caster,UNIT_STATE_MANA)+XH_BLOODPACT_MANA_BASE+XH_BLOODPACT_MANA_STEP*rank))
            call ExpansionArea(p,GetUnitX(caster),GetUnitY(caster),XH_BLOODPACT_RADIUS,XH_BLOODPACT_HEAL_BASE+XH_BLOODPACT_HEAL_STEP*rank,1)
            call ExpansionFlash(p,kind)
        elseif kind == 3 and ExpansionEnemy(target,p) then
            call ExpansionClearPrey(p)
            set ExpansionPrey[p] = target
            set ExpansionPreyUntil[p] = Seconds+XH_HUNT_SECONDS
            set ExpansionPreyRank[p] = rank
            set ExpansionPreyArt[p] = AddSpecialEffectTarget(ExpansionEffect[kind],target,"overhead")
        elseif kind == 5 then
            call UnitRemoveBuffs(caster,false,true)
            call SetUnitState(caster,UNIT_STATE_LIFE,RMinBJ(GetUnitState(caster,UNIT_STATE_MAX_LIFE),GetWidgetLife(caster)+RMinBJ(GetUnitState(caster,UNIT_STATE_MAX_LIFE)*XH_CLEANSE_HP_FRACTION,XH_CLEANSE_CAP_BASE+XH_CLEANSE_CAP_STEP*rank)))
            call ExpansionFlash(p,kind)
        elseif kind == 6 then
            call UnitAddAbility(caster,'Fxwr')
            call SetUnitAbilityLevel(caster,'Fxwr',IMinBJ(XH_WARCRY_MAX_RANK,rank))
            set ExpansionWarcryUntil[p] = Seconds+XH_WARCRY_SECONDS
            call ExpansionFlash(p,kind)
        elseif kind == 8 then
            call ExpansionArea(p,GetUnitX(caster),GetUnitY(caster),XH_PULL_RADIUS,0.,2)
            call ExpansionFlash(p,kind)
        elseif kind == 9 then
            call ExpansionArea(p,GetUnitX(caster),GetUnitY(caster),XH_MANAPULSE_RADIUS,RMinBJ(XH_MANAPULSE_CAP,XH_MANAPULSE_BASE+XH_MANAPULSE_STEP*rank),3)
            call ExpansionFlash(p,kind)
        endif
    endif
    set caster = null
    set target = null
endfunction
function ExpansionPlayerTick takes nothing returns nothing
    local integer p = 0
    local real radius = 0.
    loop
        exitwhen p == 12 or GetTriggeringTrigger() == ExpansionThinkTrigger[p]
        set p = p+1
    endloop
    if p == 12 then
        return
    endif
        if not Alive(Hero[p]) then
            call ExpansionClear(p)
        else
            if ExpansionCastArt[p] != null and Seconds >= ExpansionCastUntil[p] then
                call DestroyEffect(ExpansionCastArt[p])
                set ExpansionCastArt[p] = null
            endif
            if ExpansionPrey[p] != null and (Seconds >= ExpansionPreyUntil[p] or not Alive(ExpansionPrey[p])) then
                call ExpansionClearPrey(p)
            endif
            if ExpansionWarcryUntil[p] > 0 and Seconds >= ExpansionWarcryUntil[p] then
                call UnitRemoveAbility(Hero[p],'Fxwr')
                set ExpansionWarcryUntil[p] = 0
            endif
            if ExpansionCharges[p] > 0 and Seconds >= ExpansionChargeUntil[p] then
                set ExpansionCharges[p] = 0
            endif
            if ExpansionTicks[p] > 0 and Seconds >= ExpansionZoneAt[p] then
                if HeroKind[p] == EXPANSION_FIRST_HERO then
                    set radius = XH_AFTERSHOCK_RADIUS
                    call ExpansionImpact(p,ExpansionEffect[0],ExpansionX[p],ExpansionY[p])
                else
                    set radius = XH_EMBERS_RADIUS
                endif
                call ExpansionArea(p,ExpansionX[p],ExpansionY[p],radius,ExpansionDamage[p],0)
                set ExpansionTicks[p] = ExpansionTicks[p]-1
                set ExpansionZoneAt[p] = Seconds+1
                if ExpansionTicks[p] == 0 and ExpansionZoneArt[p] != null then
                    call DestroyEffect(ExpansionZoneArt[p])
                    set ExpansionZoneArt[p] = null
                endif
            endif
        endif
endfunction
function ExpansionInit takes nothing returns nothing
    local integer p = 0
    loop
        exitwhen p == 12
        set ExpansionThinkTrigger[p] = CreateTrigger()
        call TriggerAddAction(ExpansionThinkTrigger[p],function ExpansionPlayerTick)
        set p = p+1
    endloop
endfunction
function ExpansionTick takes nothing returns nothing
    local integer p = 0
    loop
        exitwhen p == 12
        call TriggerExecute(ExpansionThinkTrigger[p])
        set p = p+1
    endloop
endfunction
