// Source KWX: approach at 950/s and five target impacts, 0.35s apart.
// Fixed per-player state; no shared target, sleeps or per-cast timers.
function KibaRollEnd takes integer p returns nothing
    local unit caster=KibaRollCaster[p]
    set KibaRollTarget[p]=null
    set KibaRollCaster[p]=null
    set KibaRollHits[p]=0
    if caster!=null then
        if VisualChannelIndex[p]==38 then
            set VisualChannelUntil[p]=0.
            set VisualChannelIndex[p]=-1
            set SkillPoseQueued[p]=false
            set VisualPoseLife[p]=0.
        endif
        call SetUnitTimeScale(caster,1.)
        if FoundationAlive(caster) and not IsUnitPaused(caster) then
            if GetUnitCurrentOrder(caster)==OrderId("drunkenhaze") then
                call IssueImmediateOrder(caster,"stop")
            endif
            if KibaFourLegs[p] and GetUnitTypeId(caster)==HeroType[p] then
                call SetUnitAnimationByIndex(caster,15)
            else
                call SetUnitAnimation(caster,"stand")
            endif
        endif
    endif
    set caster=null
endfunction
function KibaRollMove takes integer p, real x, real y returns boolean
    local unit caster=KibaRollCaster[p]
    local real sx=GetUnitX(caster)
    local real sy=GetUnitY(caster)
    local real distance=SquareRoot((x-sx)*(x-sx)+(y-sy)*(y-sy))
    local integer steps=R2I(distance/32.)+1
    local integer j=1
    local real tx=0.
    local real ty=0.
    if steps>40 then
        set caster=null
        return false
    endif
    loop
        exitwhen j>steps
        set tx=sx+(x-sx)*j/steps
        set ty=sy+(y-sy)*j/steps
        if not TreeJumpInside(p,tx,ty) or IsTerrainPathable(tx,ty,PATHING_TYPE_WALKABILITY) then
            set caster=null
            return false
        endif
        set j=j+1
    endloop
    call SetUnitX(caster,x)
    call SetUnitY(caster,y)
    set caster=null
    return true
endfunction
function KibaRollPose takes integer p returns nothing
    if GetUnitTypeId(KibaRollCaster[p])==HeroType[p] then
        call SetUnitAnimationByIndex(KibaRollCaster[p],SkillAnimation[38])
    else
        call SetUnitAnimation(KibaRollCaster[p],"attack")
    endif
endfunction
function KibaRollStart takes integer p, integer rank, unit target returns nothing
    call KibaRollEnd(p)
    if not FoundationAlive(target) or not IsUnitEnemy(target,Player(p)) then
        return
    endif
    set KibaRollCaster[p]=Hero[p]
    set KibaRollTarget[p]=target
    set KibaRollAge[p]=0.
    set KibaRollWait[p]=0.
    set KibaRollHits[p]=0
    set KibaRollDamage[p]=120.+60.*rank
    call KibaRollPose(p)
endfunction
function KibaRollTick takes nothing returns nothing
    local integer p=0
    local unit caster=null
    local unit target=null
    local real dx=0.
    local real dy=0.
    local real distance=0.
    loop
        exitwhen p>=12
        set caster=KibaRollCaster[p]
        set target=KibaRollTarget[p]
        if caster!=null then
            set KibaRollAge[p]=KibaRollAge[p]+.05
            if caster!=Hero[p] or not FoundationAlive(caster) or not FoundationAlive(target) or IsUnitPaused(caster) or IsUnitHidden(target) or IsUnitInvisible(target,Player(p)) or not IsUnitEnemy(target,Player(p)) or GetUnitAbilityLevel(target,'Avul')>0 or KibaRollAge[p]>3. then
                call KibaRollEnd(p)
            else
                set dx=GetUnitX(target)-GetUnitX(caster)
                set dy=GetUnitY(target)-GetUnitY(caster)
                set distance=SquareRoot(dx*dx+dy*dy)
                if KibaRollHits[p]==0 and distance>220. then
                    if not KibaRollMove(p,GetUnitX(caster)+dx/distance*47.5,GetUnitY(caster)+dy/distance*47.5) then
                        call KibaRollEnd(p)
                    endif
                else
                    set KibaRollWait[p]=KibaRollWait[p]-.05
                    if KibaRollWait[p]<=0. then
                        if distance<1. then
                            set dx=Cos(GetUnitFacing(caster)*bj_DEGTORAD)
                            set dy=Sin(GetUnitFacing(caster)*bj_DEGTORAD)
                            set distance=1.
                        endif
                        if distance>450. or not KibaRollMove(p,GetUnitX(target)+dx/distance*200.,GetUnitY(target)+dy/distance*200.) then
                            call KibaRollEnd(p)
                        else
                            call SetUnitFacing(caster,bj_RADTODEG*Atan2(-dy,-dx))
                            call SkillsFlashAt("Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl",GetUnitX(target),GetUnitY(target))
                            set KibaRollHits[p]=KibaRollHits[p]+1
                            set KibaRollWait[p]=.35
                            call UnitDamageTarget(caster,target,KibaRollDamage[p],false,false,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL,WEAPON_TYPE_WHOKNOWS)
                            if KibaRollHits[p]>=5 then
                                call KibaRollEnd(p)
                            endif
                        endif
                    endif
                endif
            endif
        endif
        set p=p+1
    endloop
    set caster=null
    set target=null
endfunction
