// Combo-aware native orders; every purchase/skill cooldown/mana rule stays native.
function CreativeOrder takes integer p, integer slot, unit target, real x, real y returns boolean
    local integer raw = HeroSkill[HeroKind[p]*4+slot]
    local string order = "berserk"
    if GetUnitAbilityLevel(Hero[p],raw) == 0 then
        return false
    endif
    if slot == 1 then
        set order = "roar"
    elseif slot == 2 then
        set order = "taunt"
    elseif slot == 3 then
        set order = "howlofterror"
    endif
    if HeroKind[p] == 48 and slot < 2 or HeroKind[p] == 46 and slot == 2 then
        return IssuePointOrder(Hero[p],order,x,y)
    elseif HeroKind[p] == 46 and slot == 1 or HeroKind[p] == 47 and slot < 2 then
        return target != null and IssueTargetOrder(Hero[p],order,target)
    endif
    return IssueImmediateOrder(Hero[p],order)
endfunction
function TryCreativeBotSpell takes integer p, unit enemy returns boolean
    local integer kind = HeroKind[p]
    local unit h = Hero[p]
    local unit ally = null
    local boolean cast = false
    local real x = 0.
    local real y = 0.
    local real dx = 1.
    local real dy = 0.
    local real distance = 0.
    if enemy == null then
        set h = null
        return false
    endif
    set x = GetUnitX(enemy)
    set y = GetUnitY(enemy)
    if kind == 46 then
        if CreativeBookUntil[p] == 0 then
            set cast = CreativeOrder(p,0,null,0.,0.)
        endif
        if not cast and CreativeZoneTicks[p] == 0 then
            set cast = CreativeOrder(p,3,null,0.,0.)
        endif
        if not cast and CreativeDebt[p] == null then
            set cast = CreativeOrder(p,1,enemy,x,y)
        endif
        if not cast and CreativeZoneTicks[p] == 0 then
            set cast = CreativeOrder(p,2,null,x,y)
        endif
    elseif kind == 47 then
        if CreativeBank[p] > 0. and GetWidgetLife(h)/GetUnitState(h,UNIT_STATE_MAX_LIFE) < .65 then
            set cast = CreativeOrder(p,2,null,0.,0.)
        endif
        if not cast then
            set ally = FindBotAlly(p,3)
            if ally != null and GetWidgetLife(h)/GetUnitState(h,UNIT_STATE_MAX_LIFE) > .65 then
                set cast = CreativeOrder(p,1,ally,0.,0.)
            endif
        endif
        if not cast and CreativeBank[p] >= 100. and DistanceSq(GetUnitX(h),GetUnitY(h),x,y) < 250000. then
            set cast = CreativeOrder(p,3,null,0.,0.)
        endif
        if not cast then
            set cast = CreativeOrder(p,0,enemy,x,y)
        endif
    else
        set dx = x-GetUnitX(h)
        set dy = y-GetUnitY(h)
        set distance = SquareRoot(dx*dx+dy*dy)
        if distance > 1. then
            set dx = dx/distance
            set dy = dy/distance
        else
            set dx = 1.
            set dy = 0.
        endif
        if CreativeAUntil[p] <= Seconds then
            set cast = CreativeOrder(p,0,null,x+dx*160.-dy*160.,y+dy*160.+dx*160.)
        elseif CreativeBUntil[p] <= Seconds then
            set cast = CreativeOrder(p,1,null,x+dx*160.+dy*160.,y+dy*160.-dx*160.)
        else
            if DistanceSq(GetUnitX(h),GetUnitY(h),CreativeAX[p],CreativeAY[p]) <= 2560000. and RAbsBJ((CreativeBX[p]-CreativeAX[p])*(GetUnitY(h)-CreativeAY[p])-(CreativeBY[p]-CreativeAY[p])*(GetUnitX(h)-CreativeAX[p])) >= 100. then
                set cast = CreativeOrder(p,3,null,0.,0.)
            endif
            if not cast and GetWidgetLife(h)/GetUnitState(h,UNIT_STATE_MAX_LIFE) < .55 then
                set cast = CreativeOrder(p,2,null,0.,0.)
            endif
        endif
    endif
    if cast then
        set CastUntil[p] = Seconds+1
    endif
    set h = null
    set ally = null
    return cast
endfunction
