// Original3.5 EFE/EKE/EME and CHE presentation, using the existing .05s clock.
// No sleeps/shared source actors, no synthetic damage or extra timers.
function Lee42Clear takes integer p returns nothing
    local unit u=Kick35Caster[p]
    if u!=null then
        call SetUnitFlyHeight(u,0.,600.)
        call SetUnitTimeScale(u,1.)
    endif
    set Kick35Caster[p]=null
    set Kick35Target[p]=null
    set Kick35At[p]=0.
    set Lee42KickStep[p]=0
    set u=Lee42DrinkCaster[p]
    if u!=null then
        call SetUnitTimeScale(u,1.)
        if FoundationAlive(u) then
            call SetUnitAnimation(u,"stand")
        endif
    endif
    set Lee42DrinkCaster[p]=null
    set Lee42DrinkStep[p]=0
    set u=null
endfunction
function Lee42KickStart takes integer p, unit target returns nothing
    call Lee42Clear(p)
    set Kick35Caster[p]=Hero[p]
    set Kick35Target[p]=target
    set Lee42KickElapsed[p]=0.
    set Lee42KickStep[p]=0
    set Lee42KickAngle[p]=Atan2(GetUnitY(target)-GetUnitY(Hero[p]),GetUnitX(target)-GetUnitX(Hero[p]))
    call UnitAddAbility(Hero[p],'Amrf')
    call UnitRemoveAbility(Hero[p],'Amrf')
    call SetUnitFlyHeight(Hero[p],100.,200.)
    // Do not move or issue orders in SPELL_EFFECT: preserve native mana/cooldown.
endfunction
function Lee42DrinkStart takes integer p returns nothing
    call Lee42Clear(p)
    set Lee42DrinkCaster[p]=Hero[p]
    set Lee42DrinkElapsed[p]=0.
    set Lee42DrinkStep[p]=0
    call SetUnitAnimationByIndex(Hero[p],9)
endfunction
function Lee42Tick takes nothing returns nothing
    local integer p=0
    local integer step=0
    local unit u=null
    local unit t=null
    local real elapsed=0.
    local real x=0.
    local real y=0.
    loop
        exitwhen p>=12
        set u=Kick35Caster[p]
        set t=Kick35Target[p]
        if u!=null then
            if u!=Hero[p] or not FoundationAlive(u) or not FoundationAlive(t) or not IsUnitEnemy(t,Player(p)) or IsUnitPaused(u) or IsUnitHidden(u) or CampaignTransition then
                call Lee42Clear(p)
            else
                set elapsed=Lee42KickElapsed[p]+.05
                set Lee42KickElapsed[p]=elapsed
                if elapsed<.31 then
                    call SetUnitTimeScale(u,2.)
                elseif Lee42KickStep[p]==0 then
                    call SetUnitTimeScale(u,1.)
                    call SetUnitAnimationByIndex(u,3)
                    // Source teleports onto the already melee-range target. Keep safe
                    // ground positioning and never cross a scene boundary or cliff.
                    set x=GetUnitX(t)-40.*Cos(Lee42KickAngle[p])
                    set y=GetUnitY(t)-40.*Sin(Lee42KickAngle[p])
                    if TreeJumpInside(p,x,y) and not IsTerrainPathable(x,y,PATHING_TYPE_WALKABILITY) and GetTerrainCliffLevel(x,y)==GetTerrainCliffLevel(GetUnitX(u),GetUnitY(u)) then
                        call SetUnitPosition(u,x,y)
                    endif
                    set Lee42KickStep[p]=1
                endif
                // Original12 units/.04s over .7sec; fixed17 pulses (204 units).
                set step=Lee42KickStep[p]
                loop
                    exitwhen step==0 or step>17 or elapsed<.35+.04*step
                    set x=GetUnitX(t)+12.*Cos(Lee42KickAngle[p])
                    set y=GetUnitY(t)+12.*Sin(Lee42KickAngle[p])
                    if TreeJumpInside(p,x,y) and not IsTerrainPathable(x,y,PATHING_TYPE_WALKABILITY) and GetTerrainCliffLevel(x,y)==GetTerrainCliffLevel(GetUnitX(t),GetUnitY(t)) and not IsUnitType(t,UNIT_TYPE_STRUCTURE) then
                        call SetUnitPosition(t,x,y)
                        call DestroyEffect(AddSpecialEffectTarget("Abilities\\Weapons\\TreantMissile\\TreantMissile.mdl",t,"origin"))
                    endif
                    set step=step+1
                    set Lee42KickStep[p]=step
                endloop
                if elapsed>=1.2 then
                    call Lee42Clear(p)
                endif
            endif
        endif
        set u=Lee42DrinkCaster[p]
        if u!=null then
            if u!=Hero[p] or not FoundationAlive(u) or IsUnitPaused(u) or IsUnitHidden(u) or CampaignTransition then
                call Lee42Clear(p)
            else
                set elapsed=Lee42DrinkElapsed[p]+.05
                set Lee42DrinkElapsed[p]=elapsed
                if Lee42DrinkStep[p]<3 and elapsed>=.26+.25*Lee42DrinkStep[p] then
                    call SetUnitTimeScale(u,1.5)
                    call SetUnitAnimationByIndex(u,6)
                    set Lee42DrinkStep[p]=Lee42DrinkStep[p]+1
                endif
                if elapsed>=1.11 then
                    call SetUnitTimeScale(u,1.)
                    call SetUnitAnimation(u,"stand")
                    set Lee42DrinkCaster[p]=null
                endif
            endif
        endif
        set p=p+1
    endloop
    set u=null
    set t=null
endfunction
