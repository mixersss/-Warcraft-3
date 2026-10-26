// Source SGV(3.5)/HLE(4.2i): left-hand lightning, 600units/s, rush/strike poses.
// Cast-local references use the existing visual clock. No pauses, hidden flags or sleeps.
function VisualChidoriEnd takes integer p returns nothing
    local integer n=p*4
    if FoundationAlive(Hero[p]) and not IsUnitPaused(Hero[p]) and not IsUnitHidden(Hero[p]) and GetUnitCurrentOrder(Hero[p])==0 then
        call SetUnitTimeScale(Hero[p],1.)
        call SetUnitAnimation(Hero[p],"stand")
    endif
    set VisualApproachCaster[p]=null
    set VisualApproachTarget[p]=null
    set VisualApproachAt[p]=0.
    set VisualApproachSkill[p]=0
    set VisualChidoriUntil[p]=0.
    loop
        exitwhen n>=p*4+2
        if VisualHand[n]!=null then
            call DestroyEffect(VisualHand[n])
            set VisualHand[n]=null
        endif
        set n=n+1
    endloop
endfunction
function VisualChidoriTick takes integer p returns nothing
    local unit u=VisualApproachCaster[p]
    local unit target=VisualApproachTarget[p]
    local real dx=0.
    local real dy=0.
    local real length=0.
    local real distance=0.
    local real x=0.
    local real y=0.
    local integer n=0
    if u!=Hero[p] or not FoundationAlive(u) or not FoundationAlive(target) or IsUnitPaused(u) or IsUnitHidden(u) or JumpUnit[p]!=null or not IsUnitEnemy(target,Player(p)) or TimeNow>VisualChidoriUntil[p] then
        call VisualChidoriEnd(p)
        set u=null
        set target=null
        return
    endif
    if TimeNow>=VisualApproachAt[p] then
        set dx=GetUnitX(target)-GetUnitX(u)
        set dy=GetUnitY(target)-GetUnitY(u)
        set length=SquareRoot(dx*dx+dy*dy)
        if length>650. then
            call VisualChidoriEnd(p)
        elseif length<=110. then
            call VisualChidoriEnd(p)
            call SetUnitTimeScale(u,1.)
            if GetUnitTypeId(u)==HeroType[p] then
                call SetUnitAnimationByIndex(u,11)
            else
                call SetUnitAnimationByIndex(u,2)
            endif
            set VisualPoseLife[p]=1.
            set x=GetUnitX(target)
            set y=GetUnitY(target)
            call SkillsFlashAt("Abilities\\Spells\\Human\\Thunderclap\\ThunderClapCaster.mdl",x,y)
            call SkillsFlashAt("Abilities\\Spells\\Other\\Stampede\\StampedeMissileDeath.mdl",x,y)
            loop
                exitwhen n>=3
                call VisualCreate(p,'vchi',x,y,x,y,100.,100.,2.,0)
                if n<2 then
                    call VisualField(p,'vcmf',x,y,2.)
                endif
                set n=n+1
            endloop
        else
            set distance=RMinBJ(30.,length-80.)
            set x=GetUnitX(u)+dx/length*distance
            set y=GetUnitY(u)+dy/length*distance
            if IsTerrainPathable(x,y,PATHING_TYPE_WALKABILITY) or GetTerrainCliffLevel(x,y)!=GetTerrainCliffLevel(GetUnitX(u),GetUnitY(u)) then
                call VisualChidoriEnd(p)
            else
                call SetUnitFacing(u,Atan2(dy,dx)*bj_RADTODEG)
                // Enter the native rush once; SetUnitX/Y keeps its animation playing.
                if VisualApproachAt[p]>0. then
                    if GetUnitTypeId(u)==HeroType[p] then
                        call SetUnitAnimationByIndex(u,10)
                    else
                        call SetUnitAnimationByIndex(u,5)
                    endif
                    set VisualApproachAt[p]=0.
                endif
                call SetUnitX(u,x)
                call SetUnitY(u,y)
            endif
        endif
    endif
    set u=null
    set target=null
endfunction
// Source MXV(3.5), RHX/OWX(4.2i): three hand chakra layers, accelerated pose,
// six target layers for three seconds and the original blue Naga impact actor.
function VisualRasenganEnd takes integer p returns nothing
    local integer n=0
    loop
        exitwhen n>=6
        if VisualRasenganArt[p*6+n]!=null then
            call DestroyEffect(VisualRasenganArt[p*6+n])
            set VisualRasenganArt[p*6+n]=null
        endif
        set n=n+1
    endloop
    if VisualRasenganCaster[p]==Hero[p] and FoundationAlive(Hero[p]) then
        call SetUnitTimeScale(Hero[p],1.)
    endif
    set VisualRasenganCaster[p]=null
    set VisualRasenganTarget[p]=null
    set VisualRasenganUntil[p]=0.
    set VisualRasenganPoseUntil[p]=0.
endfunction
function VisualRasenganStart takes integer p, unit target returns nothing
    local integer n=0
    call VisualRasenganEnd(p)
    if not FoundationAlive(Hero[p]) or target==null then
        return
    endif
    set VisualRasenganCaster[p]=Hero[p]
    set VisualRasenganTarget[p]=target
    set VisualRasenganUntil[p]=TimeNow+3.
    set VisualRasenganPoseUntil[p]=TimeNow+.5
    if GetUnitTypeId(Hero[p])==HeroType[p] then
        call SetUnitTimeScale(Hero[p],2.)
    endif
    loop
        exitwhen n>=3
        call VisualAttach(p,n,"Abilities\\Spells\\Items\\ClarityPotion\\ClarityTarget.mdl","hand right",.5)
        set VisualRasenganArt[p*6+n+3]=AddSpecialEffectTarget("Abilities\\Spells\\Items\\ClarityPotion\\ClarityTarget.mdl",target,"chest")
        set n=n+1
    endloop
    set VisualRasenganArt[p*6]=AddSpecialEffectTarget("Abilities\\Spells\\NightElf\\Blink\\BlinkCaster.mdl",target,"chest")
    set VisualRasenganArt[p*6+1]=AddSpecialEffectTarget("Abilities\\Spells\\NightElf\\Blink\\BlinkTarget.mdl",target,"chest")
    set VisualRasenganArt[p*6+2]=AddSpecialEffectTarget("Abilities\\Spells\\Other\\Charm\\CharmTarget.mdl",target,"chest")
endfunction
function VisualRasenganTick takes integer p returns nothing
    local unit target=VisualRasenganTarget[p]
    if VisualRasenganUntil[p]>0. then
        if VisualRasenganCaster[p]!=Hero[p] or not FoundationAlive(Hero[p]) or not FoundationAlive(target) then
            call VisualRasenganEnd(p)
        elseif TimeNow>=VisualRasenganUntil[p] then
            call VisualCreate(p,'vras',GetUnitX(target),GetUnitY(target),GetUnitX(target),GetUnitY(target),-100.,-100.,2.,0)
            call VisualRasenganEnd(p)
        elseif VisualRasenganPoseUntil[p]>0. and TimeNow>=VisualRasenganPoseUntil[p] then
            call SetUnitTimeScale(Hero[p],1.)
            set VisualRasenganPoseUntil[p]=0.
        endif
    endif
    set target=null
endfunction
