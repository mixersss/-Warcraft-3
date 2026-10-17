// Independent source-based presentation. One shared 0.05s clock, 256 visual units,
// 48 attachment handles. Visual actors never attack, block paths or award experience.
function VisualPose takes integer p, integer index returns nothing
    if KibaFourLegs[p] and HeroRole[p]==7 and GetUnitTypeId(Hero[p])==HeroType[p] then
        call SetUnitAnimationByIndex(Hero[p],15)
    elseif GetUnitTypeId(Hero[p])==HeroType[p] and SkillAnimation[index]>=0 then
        call SetUnitAnimationByIndex(Hero[p],SkillAnimation[index])
    elseif SkillFormAnimation[index]>=0 then
        call SetUnitAnimationByIndex(Hero[p],SkillFormAnimation[index])
    else
        call SetUnitAnimation(Hero[p],"attack")
    endif
endfunction
function VisualClearSlot takes integer slot returns nothing
    if VisualUnit[slot]!=null then
        call RemoveUnit(VisualUnit[slot])
        set VisualUnit[slot]=null
    endif
endfunction
function VisualLiftEnd takes integer p returns nothing
    if VisualLiftUnit[p]!=null then
        call SetUnitFlyHeight(VisualLiftUnit[p],VisualLiftBase[p],0.)
        set VisualLiftUnit[p]=null
    endif
    set VisualVolleyLeft[p]=0
endfunction
function VisualLiftStart takes integer p, real height, real lifetime returns nothing
    call VisualLiftEnd(p)
    if JumpUnit[p]!=null or not FoundationAlive(Hero[p]) then
        return
    endif
    set VisualLiftUnit[p]=Hero[p]
    set VisualLiftAge[p]=0.
    set VisualLiftLife[p]=lifetime
    set VisualLiftBase[p]=GetUnitFlyHeight(Hero[p])
    set VisualLiftHeight[p]=height
    call UnitAddAbility(Hero[p],'Amrf')
    call UnitRemoveAbility(Hero[p],'Amrf')
endfunction
function VisualClearHero takes integer p returns nothing
    local integer n=0
    call VisualLiftEnd(p)
    loop
        exitwhen n>=256
        if VisualUnit[n]!=null and VisualOwner[n]==p then
            call VisualClearSlot(n)
        endif
        set n=n+1
    endloop
    set n=p*4
    loop
        exitwhen n>=p*4+4
        if VisualHand[n]!=null then
            call DestroyEffect(VisualHand[n])
            set VisualHand[n]=null
        endif
        set n=n+1
    endloop
    if Hero[p]!=null then
        call SetUnitTimeScale(Hero[p],1.)
    endif
    set VisualPoseLife[p]=0.
    set VisualChannelUntil[p]=0.
    set VisualChannelIndex[p]=-1
endfunction
function VisualAttach takes integer p, integer hand, string model, string attachment, real lifetime returns nothing
    local integer n=p*4+hand
    if VisualHand[n]!=null then
        call DestroyEffect(VisualHand[n])
    endif
    set VisualHand[n]=AddSpecialEffectTarget(model,Hero[p],attachment)
    set VisualHandLife[n]=lifetime
endfunction
function VisualCreate takes integer p, integer raw, real sx, real sy, real tx, real ty, real height, real endheight, real lifetime, integer mode returns nothing
    local integer n=VisualCursor
    call VisualClearSlot(n)
    set VisualCursor=ModuloInteger(n+1,256)
    set VisualUnit[n]=CreateUnit(Player(p),raw,sx,sy,Atan2(ty-sy,tx-sx)*bj_RADTODEG)
    set VisualOwner[n]=p
    set VisualSX[n]=sx
    set VisualSY[n]=sy
    set VisualTX[n]=tx
    set VisualTY[n]=ty
    set VisualHeight[n]=height
    set VisualEndHeight[n]=endheight
    set VisualElapsed[n]=0.
    set VisualLife[n]=lifetime
    set VisualMode[n]=mode
    call SetUnitPathing(VisualUnit[n],false)
    call SetUnitFlyHeight(VisualUnit[n],height,0.)
    if raw=='vkuc' or raw=='vfog' then
        call SetUnitAnimation(VisualUnit[n],"birth")
        call QueueUnitAnimation(VisualUnit[n],"stand")
    elseif raw=='vsnd' or raw=='vsan' or raw=='vexp' then
        call SetUnitAnimation(VisualUnit[n],"birth")
    elseif raw=='vrac' then
        call SetUnitAnimation(VisualUnit[n],"walk")
    else
        call SetUnitAnimation(VisualUnit[n],"stand")
    endif
endfunction
function VisualField takes integer p, integer raw, real x, real y, real lifetime returns nothing
    call VisualCreate(p,raw,x,y,x,y,0.,0.,lifetime,0)
endfunction
function VisualFan takes integer p, integer raw, real x, real y, real height, integer count, real width returns nothing
    local integer n=0
    local real sx=GetUnitX(Hero[p])
    local real sy=GetUnitY(Hero[p])
    local real dx=x-sx
    local real dy=y-sy
    local real length=SquareRoot(dx*dx+dy*dy)
    local real offset=0.
    if length<1. then
        set dx=Cos(GetUnitFacing(Hero[p])*bj_DEGTORAD)
        set dy=Sin(GetUnitFacing(Hero[p])*bj_DEGTORAD)
        set length=1.
        set x=sx+dx*700.
        set y=sy+dy*700.
    endif
    loop
        exitwhen n>=count
        set offset=(n-(count-1)*.5)*width
        call VisualCreate(p,raw,sx,sy,x-dy/length*offset,y+dx/length*offset,height,40.,.65,1)
        set n=n+1
    endloop
endfunction
function VisualPulse takes integer p, integer index, real x, real y returns nothing
    local integer n=0
    local integer raw='vshu'
    local real angle=0.
    if index==26 or index==28 or index==32 then
        loop
            exitwhen n>=6
            set angle=(n*60.+VisualPulseCount[p]*25.)*bj_DEGTORAD
            if index==32 then
                if ModuloInteger(n,2)==0 then
                    set raw='vnot'
                else
                    set raw='vkun'
                endif
            elseif ModuloInteger(n,3)==1 then
                set raw='vkun'
            elseif ModuloInteger(n,3)==2 and index==28 then
                set raw='vnot'
            else
                set raw='vshu'
            endif
            call VisualCreate(p,raw,GetUnitX(Hero[p]),GetUnitY(Hero[p]),x+Cos(angle)*220.,y+Sin(angle)*220.,GetUnitFlyHeight(Hero[p])+150.,40.,.65,1)
            set n=n+1
        endloop
        set VisualPulseCount[p]=VisualPulseCount[p]+1
    elseif index==47 then
        call VisualField(p,'vsnd',x,y,.65)
    elseif index==58 then
        call VisualFan(p,'vtor',x,y,60.,3,160.)
    endif
endfunction
function VisualApply takes integer p, integer index, integer rank, unit target returns nothing
    local real x=GetSpellTargetX()
    local real y=GetSpellTargetY()
    local real sx=GetUnitX(Hero[p])
    local real sy=GetUnitY(Hero[p])
    local integer n=0
    local integer count=0
    local real angle=0.
    if target!=null then
        set x=GetUnitX(target)
        set y=GetUnitY(target)
    elseif SkillTarget[index]==0 then
        // No-target spells have no world aim point. Never launch toward map coordinate (0,0).
        set x=sx
        set y=sy
    endif
    if index==1 then
        call SkillsFlashAt("Abilities\\Spells\\Orc\\MirrorImage\\MirrorImageCaster.mdl",sx,sy)
    elseif index==2 or index==14 or index==35 or index==50 or index==52 or index==53 then
        call VisualField(p,'vkuc',sx,sy,1.5)
        if index==14 then
            call VisualCreate(p,'vscr',sx,sy,sx+100.,sy,100.,30.,.6,1)
        endif
    elseif index==3 then
        call VisualAttach(p,0,"Abilities\\Spells\\Items\\ClarityPotion\\ClarityTarget.mdl","hand right",1.5)
        call SkillsFlashTarget("Abilities\\Spells\\Other\\Charm\\CharmTarget.mdl",target)
    elseif index==4 then
        call SkillsFlashAt("Abilities\\Spells\\Human\\MarkOfChaos\\MarkOfChaosTarget.mdl",sx,sy)
    elseif index==5 then
        call VisualField(p,'vfir',x,y,1.5)
    elseif index==7 then
        call SkillsFlashTarget("Abilities\\Spells\\Human\\FlakCannons\\FlakTarget.mdl",target)
    elseif index==8 then
        call VisualAttach(p,0,"Abilities\\Spells\\Orc\\Purge\\PurgeBuffTarget.mdl","hand left",1.5)
        call VisualAttach(p,1,"Abilities\\Weapons\\Bolt\\BoltImpact.mdl","hand left",1.5)
        call SkillsFlashTarget("Abilities\\Weapons\\Bolt\\BoltImpact.mdl",target)
    elseif index==9 then
        call SkillsFlashAt("Abilities\\Spells\\Undead\\CarrionSwarm\\CarrionSwarmDamage.mdl",sx,sy)
    elseif index==10 or index==25 then
        call VisualFan(p,'vkun',x,y,100.,1,0.)
    elseif index==11 then
        call VisualFan(p,'vnot',x,y,100.,1,0.)
    elseif index==12 then
        call VisualAttach(p,0,"Abilities\\Spells\\Other\\Parasite\\ParasiteMissile.mdl","hand left",1.)
        call VisualAttach(p,1,"Abilities\\Spells\\Other\\Parasite\\ParasiteMissile.mdl","hand right",1.)
    elseif index==13 then
        call SkillsFlashAt("Abilities\\Spells\\Orc\\EarthQuake\\EarthQuakeTarget.mdl",sx,sy)
        call SkillsFlashAt("Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl",sx,sy)
    elseif index==16 then
        call SkillsFlashTarget("Abilities\\Weapons\\TreantMissile\\TreantMissile.mdl",target)
    elseif index==18 then
        call VisualAttach(p,0,"Abilities\\Spells\\Undead\\DarkSummoning\\DarkSummonMissile.mdl","hand right",12.)
        call VisualAttach(p,1,"Abilities\\Spells\\Undead\\DarkSummoning\\DarkSummonMissile.mdl","foot right",12.)
    elseif index==21 or index==41 then
        call SkillsFlashAt("Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl",sx,sy)
    elseif index==22 or index==23 or index==44 then
        call VisualField(p,'vhak',sx,sy,2.5)
        call VisualAttach(p,0,"Abilities\\Weapons\\ZigguratFrostMissile\\ZigguratFrostMissile.mdl","hand left",2.5)
        call VisualAttach(p,1,"Abilities\\Weapons\\ZigguratFrostMissile\\ZigguratFrostMissile.mdl","hand right",2.5)
        if index==23 then
            call VisualField(p,'vcyc',x,y,1.)
        endif
    elseif index==24 then
        call VisualFan(p,'vcyc',x,y,80.,1,0.)
    elseif index==26 then
        call VisualLiftStart(p,700.,SkillHold[index])
        set VisualVolleyLeft[p]=rank
        set VisualVolleyDelay[p]=.2
        set VisualVolleyX[p]=sx
        set VisualVolleyY[p]=sy
    elseif index==28 or index==32 or index==58 then
        if index==28 then
            call VisualLiftStart(p,1000.,SkillHold[index])
            call SkillsFlashAt("Abilities\\Spells\\Orc\\FeralSpirit\\feralspirittarget.mdl",sx,sy)
        endif
        call VisualPulse(p,index,x,y)
    elseif index==29 then
        call VisualField(p,'vkuc',sx,sy,1.5)
        call SkillsFlashAt("Abilities\\Spells\\Orc\\FeralSpirit\\feralspirittarget.mdl",sx,sy)
        call VisualFan(p,'vbal',x,y,80.,1,0.)
    elseif index==36 then
        call VisualField(p,'vfog',sx,sy,8.)
    elseif index==38 then
        call SkillsFlashAt("Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl",sx,sy)
    elseif index==42 then
        call SkillsFlashTarget("Abilities\\Weapons\\SpiritOfVengeanceMissile\\SpiritOfVengeanceMissile.mdl",target)
    elseif index==43 then
        call VisualAttach(p,0,"Abilities\\Weapons\\SpiritOfVengeanceMissile\\SpiritOfVengeanceMissile.mdl","hand left",4.)
        call VisualAttach(p,1,"Abilities\\Weapons\\SpiritOfVengeanceMissile\\SpiritOfVengeanceMissile.mdl","hand right",4.)
    elseif index==49 then
        if ZoneUntil[p]>TimeNow then
            set x=ZoneX[p]
            set y=ZoneY[p]
        else
            set x=sx
            set y=sy
        endif
        call VisualField(p,'vsnd',x,y,1.5)
        call SkillsFlashAt("Objects\\Spawnmodels\\Human\\HumanBlood\\BloodElfSpellThiefBlood.mdl",x,y)
    elseif index==51 then
        call VisualFan(p,'vkun',x,y,100.,1,0.)
    elseif index==54 then
        loop
            exitwhen n>=3
            if FoundationAlive(Companion[p*3+n]) then
                set x=GetUnitX(Companion[p*3+n])
                set y=GetUnitY(Companion[p*3+n])
                call VisualCreate(p,'vbom',x,y,x,y,300.,0.,.65,1)
                set count=count+1
            endif
            set n=n+1
        endloop
        if count==0 then
            call VisualCreate(p,'vbom',sx,sy,sx,sy,300.,0.,.65,1)
        endif
    elseif index==57 then
        call VisualField(p,'vcyc',x,y,3.)
        call SkillsFlashAt("Abilities\\Spells\\Other\\Tornado\\TornadoElementalSmall.mdl",x,y)
    elseif index==59 then
        call VisualField(p,'vkuc',sx,sy,1.5)
        loop
            exitwhen n>=8
            set angle=n*45.*bj_DEGTORAD
            call SkillsFlashAt("Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl",sx+Cos(angle)*125.,sy+Sin(angle)*125.)
            set n=n+1
        endloop
        call VisualFan(p,'vrac',x,y,70.,1,0.)
        call VisualFan(p,'vtor',x,y,50.,3,130.)
    endif
endfunction
function VisualTick takes nothing returns nothing
    local integer n=0
    local integer p=0
    local real f=0.
    loop
        exitwhen n>=256
        if VisualUnit[n]!=null then
            set p=VisualOwner[n]
            set VisualElapsed[n]=VisualElapsed[n]+.05
            if VisualElapsed[n]>=VisualLife[n] or not FoundationAlive(Hero[p]) then
                if VisualElapsed[n]>=VisualLife[n] and FoundationAlive(Hero[p]) and (GetUnitTypeId(VisualUnit[n])=='vnot' or GetUnitTypeId(VisualUnit[n])=='vbom') then
                    call SkillsFlashAt("Objects\\Spawnmodels\\Other\\NeutralBuildingExplosion\\NeutralBuildingExplosion.mdl",VisualTX[n],VisualTY[n])
                endif
                call VisualClearSlot(n)
            elseif VisualMode[n]==1 then
                set f=VisualElapsed[n]/VisualLife[n]
                call SetUnitX(VisualUnit[n],VisualSX[n]+(VisualTX[n]-VisualSX[n])*f)
                call SetUnitY(VisualUnit[n],VisualSY[n]+(VisualTY[n]-VisualSY[n])*f)
                call SetUnitFlyHeight(VisualUnit[n],VisualHeight[n]+(VisualEndHeight[n]-VisualHeight[n])*f,0.)
            endif
        endif
        set n=n+1
    endloop
    set p=0
    loop
        exitwhen p>=12
        if VisualLiftUnit[p]!=null then
            set VisualLiftAge[p]=VisualLiftAge[p]+.05
            if not FoundationAlive(VisualLiftUnit[p]) or VisualLiftUnit[p]!=Hero[p] or VisualLiftAge[p]>=VisualLiftLife[p] then
                call VisualLiftEnd(p)
            else
                set f=VisualLiftAge[p]/VisualLiftLife[p]
                call SetUnitFlyHeight(VisualLiftUnit[p],VisualLiftBase[p]+4.*VisualLiftHeight[p]*f*(1.-f),0.)
            endif
        endif
        if VisualVolleyLeft[p]>0 then
            set VisualVolleyDelay[p]=VisualVolleyDelay[p]-.05
            if not FoundationAlive(Hero[p]) then
                set VisualVolleyLeft[p]=0
            elseif VisualVolleyDelay[p]<=0. then
                call VisualPulse(p,26,VisualVolleyX[p],VisualVolleyY[p])
                set VisualVolleyLeft[p]=VisualVolleyLeft[p]-1
                set VisualVolleyDelay[p]=.25
            endif
        endif
        if VisualPoseLife[p]>0. then
            set VisualPoseLife[p]=VisualPoseLife[p]-.05
            if VisualPoseLife[p]<=0. and FoundationAlive(Hero[p]) and VisualChannelUntil[p]==0. then
                if GetUnitCurrentOrder(Hero[p])==0 then
                    call SetUnitAnimation(Hero[p],"stand")
                endif
            endif
        endif
        set p=p+1
    endloop
    set n=0
    loop
        exitwhen n>=48
        if VisualHand[n]!=null then
            set p=(n-ModuloInteger(n,4))/4
            set VisualHandLife[n]=VisualHandLife[n]-.05
            if VisualHandLife[n]<=0. or not FoundationAlive(Hero[p]) then
                call DestroyEffect(VisualHand[n])
                set VisualHand[n]=null
            endif
        endif
        set n=n+1
    endloop
endfunction
