// Straightforward native orders. Mana, cooldowns and costs remain native.
function CreativeOrder takes integer p, integer slot, unit target, real x, real y returns boolean
    local string order = "berserk"
    if GetUnitAbilityLevel(Hero[p],HeroSkill[HeroKind[p]*4+slot]) == 0 then
        return false
    endif
    if (HeroKind[p] == 47 and slot == 2) or (HeroKind[p] == 49 and slot == 1) then
        return IssueImmediateOrder(Hero[p],"windwalk")
    endif
    if slot == 1 then
        set order = "roar"
    elseif slot == 2 then
        set order = "taunt"
    elseif slot == 3 then
        set order = "howlofterror"
    endif
    if HeroKind[p] == 47 and slot == 3 then
        return IssuePointOrder(Hero[p],order,x,y)
    endif
    return IssueImmediateOrder(Hero[p],order)
endfunction
function TryCreativeBotSpell takes integer p, unit enemy returns boolean
    local integer kind = HeroKind[p]
    local real distance = 0.
    local real hp = GetWidgetLife(Hero[p])/GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)
    local boolean cast = false
    if enemy == null then
        return false
    endif
    set distance = DistanceSq(GetUnitX(Hero[p]),GetUnitY(Hero[p]),GetUnitX(enemy),GetUnitY(enemy))
    if kind == 46 then
        set cast = CreativeOrder(p,3,null,0.,0.)
        if not cast then
            set cast = CreativeOrder(p,0,null,0.,0.)
        endif
        if not cast then
            set cast = CreativeOrder(p,1,null,0.,0.)
        endif
        if not cast and CreativeBuffUntil[p] == 0 then
            set cast = CreativeOrder(p,2,null,0.,0.)
        endif
    elseif kind == 47 then
        if hp < .55 then
            set cast = CreativeOrder(p,2,null,0.,0.)
        endif
        if not cast and distance <= 490000. and CreativeRainTicks[p] == 0 then
            set cast = CreativeOrder(p,3,null,GetUnitX(enemy),GetUnitY(enemy))
        endif
    elseif kind == 48 then
        if distance < 1000000. and CreativeBannerUntil[p] == 0 then
            set cast = CreativeOrder(p,3,null,0.,0.)
        endif
    else
        if hp < .40 then
            set cast = CreativeOrder(p,1,null,0.,0.)
        endif
        if not cast and distance < 102400. and CreativeBladeTicks[p] == 0 then
            set cast = CreativeOrder(p,3,null,0.,0.)
        endif
    endif
    if cast then
        set CastUntil[p] = Seconds+1
    endif
    return cast
endfunction
