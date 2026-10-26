// Independent adaptations for the remaining roster; all state is bounded.
function RosterFlag takes integer mask, integer flag returns boolean
    return ModuloInteger((mask-ModuloInteger(mask,flag))/flag,2)==1
endfunction
function RosterClearBuff takes integer p returns nothing
    local integer n=0
    if KibaFourLegs[p] then
        call AddUnitAnimationProperties(Hero[p],"alternate",false)
        set KibaFourLegs[p]=false
    endif
    loop
        exitwhen n>=6
        call UnitRemoveAbility(Hero[p],RosterBonus[n])
        set n=n+1
    endloop
    set RosterBuffUntil[p]=0.
    set RosterBuffDrain[p]=0.
    if RosterBuffArt[p]!=null then
        call DestroyEffect(RosterBuffArt[p])
        set RosterBuffArt[p]=null
    endif
endfunction
function RosterClearZone takes integer p returns nothing
    set ZoneUntil[p]=0.
    if ZoneArt[p]!=null then
        call DestroyEffect(ZoneArt[p])
        set ZoneArt[p]=null
    endif
endfunction
function RosterClearSand takes integer p returns nothing
    local integer n=0
    loop
        exitwhen n>=3
        if SandWave[p*3+n]!=null then
            if VisualUnit[SandWaveSlot[p*3+n]]==SandWave[p*3+n] then
                call VisualClearSlot(SandWaveSlot[p*3+n])
            endif
            set SandWave[p*3+n]=null
        endif
        set n=n+1
    endloop
    set SandWaveUntil[p]=0.
endfunction
function RosterSand takes integer p, real tx, real ty returns nothing
    local integer n=0
    local integer slot=0
    local real x=GetUnitX(Hero[p])
    local real y=GetUnitY(Hero[p])
    local real dx=tx-x
    local real dy=ty-y
    local real length=SquareRoot(dx*dx+dy*dy)
    local real offset=0.
    local real advance=0.
    call RosterClearSand(p)
    if length<1. then
        set length=1.
        set dx=1.
    endif
    set advance=RMinBJ(120.,length)
    set SandWaveUntil[p]=TimeNow+1.5
    loop
        exitwhen n>=3
        set offset=(n-1)*160.
        set slot=VisualCursor
        call VisualCreate(p,'rswv',x+dx/length*advance-dy/length*offset,y+dy/length*advance+dx/length*offset,tx-dy/length*offset,ty+dx/length*offset,0.,0.,1.5,1)
        set SandWaveSlot[p*3+n]=slot
        set SandWave[p*3+n]=VisualUnit[slot]
        set n=n+1
    endloop
endfunction
// Independent sight state: Kaiten/combat buffs do not cancel Byakugan.
function RosterClearVisionMarks takes integer p returns nothing
    local integer n=0
    loop
        exitwhen n>=VisionMarkCount[p]
        call FogModifierStop(VisionMarkFog[p*128+n])
        call DestroyFogModifier(VisionMarkFog[p*128+n])
        set VisionMarkFog[p*128+n]=null
        set n=n+1
    endloop
    set VisionMarkCount[p]=0
endfunction
function RosterClearVision takes integer p returns nothing
    call UnitRemoveAbility(Hero[p],'Rbv3')
    call UnitRemoveAbility(Hero[p],'BOac')
    call UnitRemoveAbility(Hero[p],'Rbyg')
    set VisionUntil[p]=0.
    call RosterClearVisionMarks(p)
    if VisionFog[p]!=null then
        call FogModifierStop(VisionFog[p])
        call DestroyFogModifier(VisionFog[p])
        set VisionFog[p]=null
    endif
    if VisionArt[p]!=null then
        call DestroyEffect(VisionArt[p])
        set VisionArt[p]=null
    endif
endfunction
function RosterVisionHero takes nothing returns boolean
    return IsUnitType(GetFilterUnit(),UNIT_TYPE_HERO)
endfunction
function RosterVisionPulse takes integer p returns nothing
    local unit target=null
    local real x=GetUnitX(Hero[p])
    local real y=GetUnitY(Hero[p])
    local integer slot=0
    call RosterClearVisionMarks(p)
    if VisionFog[p]!=null then
        call FogModifierStop(VisionFog[p])
        call DestroyFogModifier(VisionFog[p])
    endif
    set VisionFog[p]=CreateFogModifierRadius(Player(p),FOG_OF_WAR_VISIBLE,x,y,VisionRadius[p],true,false)
    call FogModifierStart(VisionFog[p])
    call GroupEnumUnitsInRange(SkillScratch,x,y,VisionRadius[p],null)
    loop
        set target=FirstOfGroup(SkillScratch)
        exitwhen target==null
        call GroupRemoveUnit(SkillScratch,target)
        if FoundationAlive(target) and IsUnitEnemy(target,Player(p)) and not IsUnitType(target,UNIT_TYPE_STRUCTURE) and not IsUnitType(target,UNIT_TYPE_HERO) then
            // Only UI calls are local. Handle creation and state remain synchronized.
            if IsPlayerAlly(GetLocalPlayer(),Player(p)) then
                call PingMinimapEx(GetUnitX(target),GetUnitY(target),1.5,100,180,255,false)
            endif
        endif
    endloop
    // Every real living enemy hero, at any distance, including through fog/invisibility.
    // Fog handles are synchronized; only minimap UI is filtered per allied client.
    if VisionHeroFilter==null then
        set VisionHeroFilter=Condition(function RosterVisionHero)
    endif
    call GroupEnumUnitsInRect(SkillScratch,bj_mapInitialPlayableArea,VisionHeroFilter)
    loop
        set target=FirstOfGroup(SkillScratch)
        exitwhen target==null
        call GroupRemoveUnit(SkillScratch,target)
        if IsUnitType(target,UNIT_TYPE_HERO) and FoundationAlive(target) and not IsUnitIllusion(target) and not IsUnitHidden(target) and IsUnitEnemy(target,Player(p)) then
            if VisionMarkCount[p]<128 then
                set slot=p*128+VisionMarkCount[p]
                set VisionMarkFog[slot]=CreateFogModifierRadius(Player(p),FOG_OF_WAR_VISIBLE,GetUnitX(target),GetUnitY(target),192.,true,false)
                call FogModifierStart(VisionMarkFog[slot])
                set VisionMarkCount[p]=VisionMarkCount[p]+1
            endif
            if IsPlayerAlly(GetLocalPlayer(),Player(p)) then
                call PingMinimapEx(GetUnitX(target),GetUnitY(target),2.25,100,180,255,false)
            endif
        endif
    endloop
    set VisionNext[p]=TimeNow+2.
    set target=null
endfunction
function RosterVision takes integer p, integer rank returns nothing
    call RosterClearVision(p)
    call UnitAddAbility(Hero[p],'Rbv3')
    call UnitMakeAbilityPermanent(Hero[p],true,'Rbv3')
    call UnitAddAbility(Hero[p],'Rbyg')
    call SetUnitAbilityLevel(Hero[p],'Rbyg',rank)
    call UnitMakeAbilityPermanent(Hero[p],true,'Rbyg')
    set VisionUntil[p]=TimeNow+15.
    set VisionRadius[p]=200.+200.*rank
    set VisionArt[p]=AddSpecialEffectTarget("Eye_Byakugan.mdl",Hero[p],"origin")
    call RosterVisionPulse(p)
endfunction
function RosterClearShadow takes integer p returns nothing
    local integer n=0
    if VisualChannelIndex[p]==30 then
        set VisualChannelUntil[p]=0.
        set VisualChannelIndex[p]=-1
        set SkillPoseQueued[p]=false
        if Hero[p]!=null then
            call SetUnitTimeScale(Hero[p],1.)
        endif
    endif
    if Shadow43Helpers[p]!=null then
        call ForGroup(Shadow43Helpers[p],function Shadow43RemoveHelper)
        call GroupClear(Shadow43Helpers[p])
    endif
    loop
        exitwhen n>=16
        if ShadowSegment[p*16+n]!=null then
            call RemoveUnit(ShadowSegment[p*16+n])
            set ShadowSegment[p*16+n]=null
        endif
        set n=n+1
    endloop
    if ShadowRoot[p]!=null then
        call RemoveUnit(ShadowRoot[p])
        set ShadowRoot[p]=null
    endif
    set ShadowBuffSeen[p]=false
    set ShadowGraceUntil[p]=0.
    set ShadowUntil[p]=0.
    set ShadowTarget[p]=null
endfunction
function RosterShadowPulse takes integer p returns nothing
    local integer n=0
    local real x=GetUnitX(Hero[p])
    local real y=GetUnitY(Hero[p])
    local real dx=GetUnitX(ShadowTarget[p])-x
    local real dy=GetUnitY(ShadowTarget[p])-y
    local real distance=SquareRoot(dx*dx+dy*dy)
    local real facing=Atan2(dy,dx)*bj_RADTODEG
    local real offset=0.
    if ShadowRoot[p]!=null then
        call SetUnitX(ShadowRoot[p],GetUnitX(ShadowTarget[p]))
        call SetUnitY(ShadowRoot[p],GetUnitY(ShadowTarget[p]))
    endif
    loop
        exitwhen n>=16
        set offset=(n+.5)*50.
        if offset<distance and distance<=900. then
            if ShadowSegment[p*16+n]==null then
                set ShadowSegment[p*16+n]=CreateUnit(Player(p),'rshd',x,y,facing)
                call SetUnitPathing(ShadowSegment[p*16+n],false)
                call SetUnitFlyHeight(ShadowSegment[p*16+n],6.,0.)
                call SetUnitVertexColor(ShadowSegment[p*16+n],12,8,18,245)
                call SetUnitAnimation(ShadowSegment[p*16+n],"stand")
            endif
            call SetUnitX(ShadowSegment[p*16+n],x+dx*offset/distance)
            call SetUnitY(ShadowSegment[p*16+n],y+dy*offset/distance)
            call SetUnitFacing(ShadowSegment[p*16+n],facing)
        elseif ShadowSegment[p*16+n]!=null then
            call RemoveUnit(ShadowSegment[p*16+n])
            set ShadowSegment[p*16+n]=null
        endif
        set n=n+1
    endloop
endfunction
function RosterShadow takes integer p, integer rank, unit target returns nothing
    call RosterClearShadow(p)
    if not FoundationAlive(target) then
        return
    endif
    set ShadowTarget[p]=target
    if IsUnitType(target,UNIT_TYPE_HERO) then
        set ShadowDuration[p]=3.+rank
    else
        set ShadowDuration[p]=5.+rank
    endif
    set ShadowUntil[p]=TimeNow+ShadowDuration[p]
    set ShadowGraceUntil[p]=TimeNow+1.
    set ShadowBuffSeen[p]=(GetUnitAbilityLevel(target,'Rsmb')>0 or GetUnitAbilityLevel(target,'Bmlt')>0)
    set ShadowRoot[p]=CreateUnit(Player(p),'rshk',GetUnitX(target),GetUnitY(target),GetUnitFacing(Hero[p]))
    call SetUnitPathing(ShadowRoot[p],false)
    call SetUnitFlyHeight(ShadowRoot[p],8.,0.)
    call SetUnitAnimation(ShadowRoot[p],"birth")
    call SetUnitTimeScale(ShadowRoot[p],2.334/ShadowDuration[p])
    call RosterShadowPulse(p)
endfunction
// SOURCE35_RUNTIME
function RosterGrantInnate takes integer p returns nothing
    // Both3.5 kits have a fourth active skill instead of automatic reincarnation.
endfunction
function RosterResetEffects takes integer p returns nothing
    local integer k=0
    call Source40Clear(p)
    call Source35Clear(p)
    call KibaRollEnd(p)
    call KunaiClear(p)
    call CommonLogClear(p)
    call VisualClearHero(p)
    call RosterClearSand(p)
    call RosterClearVision(p)
    call RosterClearShadow(p)
    call RosterClearBuff(p)
    call RosterClearZone(p)
    loop
        exitwhen k>=3
        if PetFog[p*3+k]!=null then
            call RemoveUnit(PetFog[p*3+k])
            set PetFog[p*3+k]=null
        endif
        // A trap from the previous bout must never hit the next opponent.
        set PetTrapVictim[p*3+k]=null
        set PetTrapCaster[p*3+k]=null
        set k=k+1
    endloop
endfunction
function RosterReset takes integer p returns nothing
    local integer k=0
    call RosterResetEffects(p)
    loop
        exitwhen k>=3
        if PetFog[p*3+k]!=null then
            call RemoveUnit(PetFog[p*3+k])
            set PetFog[p*3+k]=null
        endif
        set PetTrapVictim[p*3+k]=null
        set PetTrapCaster[p*3+k]=null
        set PetCastAt[p*3+k]=0.
        if Companion[p*3+k]!=null then
            call RemoveUnit(Companion[p*3+k])
            set Companion[p*3+k]=null
        endif
        set k=k+1
    endloop
endfunction
function RosterEnemy takes unit target, player owner returns boolean
    return FoundationAlive(target) and IsUnitEnemy(target,owner) and not IsUnitType(target,UNIT_TYPE_STRUCTURE) and not IsUnitType(target,UNIT_TYPE_MAGIC_IMMUNE)
endfunction
function RosterHit takes unit caster, unit target, real damage, real burn returns nothing
    if RosterEnemy(target,GetOwningPlayer(caster)) then
        if UnitDamageTarget(caster,target,damage,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS) and burn>0. then
            call SetUnitState(target,UNIT_STATE_MANA,RMaxBJ(0.,GetUnitState(target,UNIT_STATE_MANA)-burn))
        endif
    endif
endfunction
function RosterStun takes integer p, unit target, real duration returns nothing
    local unit dummy=null
    local integer rank=R2I(duration*2.+.5)
    if duration<=0. or not RosterEnemy(target,Player(p)) then
        return
    endif
    if rank<1 then
        set rank=1
    elseif rank>4 then
        set rank=4
    endif
    if StunDummy[StunCursor]!=null then
        call RemoveUnit(StunDummy[StunCursor])
    endif
    set dummy=CreateUnit(Player(p),'rdst',GetUnitX(target),GetUnitY(target),0.)
    set StunDummy[StunCursor]=dummy
    set StunExpires[StunCursor]=TimeNow+1.5
    set StunCursor=ModuloInteger(StunCursor+1,128)
    if duration<.5 then
        call UnitRemoveAbility(dummy,'Rstn')
        call UnitAddAbility(dummy,'Rmic')
    else
        call SetUnitAbilityLevel(dummy,'Rstn',rank)
    endif
    call IssueTargetOrder(dummy,"thunderbolt",target)
    set dummy=null
endfunction
function RosterArea takes integer p, real x, real y, real radius, real damage, real burn, real stun returns nothing
    local unit target=null
    call GroupEnumUnitsInRange(SkillScratch,x,y,radius,null)
    loop
        set target=FirstOfGroup(SkillScratch)
        exitwhen target==null
        call GroupRemoveUnit(SkillScratch,target)
        if RosterEnemy(target,Player(p)) then
            if damage>0. or burn>0. then
                call RosterHit(Hero[p],target,damage,burn)
            endif
            if stun>0. then
                call RosterStun(p,target,stun)
            endif
        endif
    endloop
    set target=null
endfunction
// Native placement respects collision; short sampled steps never cross a blocked wall/cliff.
function Hyuuga43Stun takes integer p, unit target returns nothing
    local unit dummy=null
    if not RosterEnemy(target,Player(p)) then
        return
    endif
    if StunDummy[StunCursor]!=null then
        call RemoveUnit(StunDummy[StunCursor])
    endif
    set dummy=CreateUnit(Player(p),'rdst',GetUnitX(target),GetUnitY(target),0.)
    set StunDummy[StunCursor]=dummy
    set StunExpires[StunCursor]=TimeNow+1.5
    set StunCursor=ModuloInteger(StunCursor+1,128)
    call UnitRemoveAbility(dummy,'Rstn')
    call UnitAddAbility(dummy,'Rkt3')
    call IssueTargetOrder(dummy,"thunderbolt",target)
    set dummy=null
endfunction
function RosterRepel takes integer p, integer rank returns nothing
    local unit target=null
    local real x=GetUnitX(Hero[p])
    local real y=GetUnitY(Hero[p])
    local real dx=0.
    local real dy=0.
    local real length=0.
    local real tx=0.
    local real ty=0.
    local real nx=0.
    local real ny=0.
    local integer n=0
    local real radius=270.
    if rank==4 then
        set radius=400.
    endif
    call GroupEnumUnitsInRange(SkillScratch,x,y,radius,null)
    loop
        set target=FirstOfGroup(SkillScratch)
        exitwhen target==null
        call GroupRemoveUnit(SkillScratch,target)
        if RosterEnemy(target,Player(p)) then
            call Hyuuga43Stun(p,target)
            set tx=GetUnitX(target)
            set ty=GetUnitY(target)
            set dx=tx-x
            set dy=ty-y
            set length=SquareRoot(dx*dx+dy*dy)
            if length<1. then
                set dx=Cos(GetUnitFacing(Hero[p])*bj_DEGTORAD)
                set dy=Sin(GetUnitFacing(Hero[p])*bj_DEGTORAD)
                set length=1.
            endif
            set n=0
            loop
                exitwhen n>=4+2*rank
                set nx=tx+dx/length*20.
                set ny=ty+dy/length*20.
                exitwhen IsTerrainPathable(nx,ny,PATHING_TYPE_WALKABILITY) or GetTerrainCliffLevel(nx,ny)!=GetTerrainCliffLevel(tx,ty)
                set tx=nx
                set ty=ny
                set n=n+1
            endloop
            call SetUnitPosition(target,tx,ty)
        endif
    endloop
    set target=null
endfunction
function RosterBuff takes integer p, integer index, integer rank returns nothing
    local integer n=0
    local integer flag=1
    call RosterClearBuff(p)
    loop
        exitwhen n>=6
        if RosterFlag(RosterProfile[index],flag) then
            call UnitAddAbility(Hero[p],RosterBonus[n])
            call SetUnitAbilityLevel(Hero[p],RosterBonus[n],rank)
            call UnitMakeAbilityPermanent(Hero[p],true,RosterBonus[n])
        endif
        set n=n+1
        set flag=flag*2
    endloop
    if index==37 then
        call AddUnitAnimationProperties(Hero[p],"alternate",true)
        set KibaFourLegs[p]=true
    endif
    set RosterBuffUntil[p]=TimeNow+RosterDuration[index]
    if HeroRole[p]==3 and ModuloInteger(index,5)==3 then
        set RosterBuffDrain[p]=.02
    endif
    if RosterVisual[index]!="" and RosterMechanic[index]==4 and index!=20 and index!=40 then
        set RosterBuffArt[p]=AddSpecialEffectTarget(RosterVisual[index],Hero[p],"origin")
    endif
endfunction
function RosterSummon takes integer p, integer index, integer rank returns nothing
    local integer slot=p*3+RosterPetSlot[index]
    local integer raw=RosterPetType[index*4+rank-1]
    if RosterDuration[index]<=0. and FoundationAlive(Companion[slot]) and (GetUnitTypeId(Companion[slot])==raw or (raw=='ra03' and GetUnitTypeId(Companion[slot])=='rdgf')) then
        return
    endif
    if Companion[slot]!=null then
        call RemoveUnit(Companion[slot])
    endif
    set Companion[slot]=CreateUnit(Player(p),raw,GetUnitX(Hero[p])+100.,GetUnitY(Hero[p]),GetUnitFacing(Hero[p]))
    if RosterDuration[index]>0. then
        call UnitApplyTimedLife(Companion[slot],'BTLF',RosterDuration[index])
    endif
    if FoundationAlive(Dummy[(p-ModuloInteger(p,3))/3]) then
        call IssueTargetOrder(Companion[slot],"attack",Dummy[(p-ModuloInteger(p,3))/3])
    endif
endfunction
function RosterLine takes integer p, integer index, integer rank returns nothing
    local unit target=null
    local real x=GetUnitX(Hero[p])
    local real y=GetUnitY(Hero[p])
    local real tx=GetSpellTargetX()-x
    local real ty=GetSpellTargetY()-y
    local real length=SquareRoot(tx*tx+ty*ty)
    local real dx=0.
    local real dy=0.
    local real along=0.
    local real across=0.
    if length<1. then
        set tx=Cos(GetUnitFacing(Hero[p])*bj_DEGTORAD)
        set ty=Sin(GetUnitFacing(Hero[p])*bj_DEGTORAD)
    else
        set tx=tx/length
        set ty=ty/length
    endif
    call GroupEnumUnitsInRange(SkillScratch,x+tx*450.,y+ty*450.,700.,null)
    loop
        set target=FirstOfGroup(SkillScratch)
        exitwhen target==null
        call GroupRemoveUnit(SkillScratch,target)
        if RosterEnemy(target,Player(p)) then
            set dx=GetUnitX(target)-x
            set dy=GetUnitY(target)-y
            set along=dx*tx+dy*ty
            set across=dx*ty-dy*tx
            if along>=0. and along<=900. and across*across<=RosterRadius[index]*RosterRadius[index] then
                call RosterHit(Hero[p],target,RosterPower[index*4+rank-1],RosterBurn[index*4+rank-1])
            endif
        endif
    endloop
    set target=null
endfunction
function RosterApply takes integer p, integer index, integer rank, unit target returns nothing
    local integer kind=RosterMechanic[index]
    local integer n=0
    local integer count=0
    local real x=GetUnitX(Hero[p])
    local real y=GetUnitY(Hero[p])
    local real power=RosterPower[index*4+rank-1]
    local real burn=RosterBurn[index*4+rank-1]
    if Source40Apply(p,index,rank) then
        return
    endif
    call Source35Apply(p,index,rank,target)
    if kind==0 then
        return
    endif
    if SkillAnimation[index]>=0 then
        call VisualPose(p,index)
    endif
    if kind==1 then
        if HeroRole[p]==10 then
            loop
                exitwhen n>=3
                if FoundationAlive(Companion[p*3+n]) then
                    set count=count+1
                endif
                set n=n+1
            endloop
            set power=power*(1.+.25*count)
        endif
        call RosterHit(Hero[p],target,power,burn)
        call RosterStun(p,target,RosterDuration[index])
        if FoundationAlive(target) and RosterVisual[index]!="" then
            call SkillsFlashTarget(RosterVisual[index],target)
        endif
    elseif kind==2 then
        if SkillTarget[index]==2 then
            set x=GetSpellTargetX()
            set y=GetSpellTargetY()
        elseif HeroRole[p]==9 and ZoneUntil[p]>TimeNow then
            set x=ZoneX[p]
            set y=ZoneY[p]
        endif
        call RosterArea(p,x,y,RosterRadius[index],power,burn,RosterDuration[index])
        if RosterVisual[index]!="" then
            call SkillsFlashAt(RosterVisual[index],x,y)
        endif
    elseif kind==3 then
        if FoundationAlive(target) and not IsUnitEnemy(target,Player(p)) and not IsUnitType(target,UNIT_TYPE_STRUCTURE) then
            call SetWidgetLife(target,RMinBJ(GetUnitState(target,UNIT_STATE_MAX_LIFE),GetWidgetLife(target)+power))
            call SkillsFlashTarget(RosterVisual[index],target)
        endif
    elseif kind==4 then
        if index==20 or index==40 then
            call RosterVision(p,rank)
        else
            call RosterBuff(p,index,rank)
            if index==36 then
                call RosterArea(p,x,y,300.,0.,0.,.2)
            endif
        endif
    elseif kind==5 or kind==8 then
        if index==47 then
            call RosterSand(p,GetSpellTargetX(),GetSpellTargetY())
        endif
        call RosterClearZone(p)
        if kind==5 then
            call RosterBuff(p,index,rank)
        else
            set x=GetSpellTargetX()
            set y=GetSpellTargetY()
        endif
        set VisualZoneIndex[p]=index
        set ZoneFollow[p]=kind==5
        set ZoneX[p]=x
        set ZoneY[p]=y
        set ZoneRadius[p]=RosterRadius[index]
        set ZonePower[p]=power
        set ZoneBurn[p]=burn
        set ZoneUntil[p]=TimeNow+RosterDuration[index]
        set ZoneNext[p]=TimeNow+.5
        if index==47 then
            call VisualPulse(p,index,x,y)
        endif
        if (index==21 or index==41) and rank==4 then
            call RosterArea(p,x,y,400.,power,burn,0.)
        else
            call RosterArea(p,x,y,RosterRadius[index],power,burn,0.)
        endif
        if index==21 or index==41 then
            call RosterRepel(p,rank)
        endif
        if RosterVisual[index]!="" then
            if kind==5 then
                set ZoneArt[p]=AddSpecialEffectTarget(RosterVisual[index],Hero[p],"origin")
            else
                set ZoneArt[p]=AddSpecialEffect(RosterVisual[index],x,y)
            endif
        endif
    elseif kind==6 and RosterEnemy(target,Player(p)) then
        set ComboTarget[p]=target
        set ComboDamage[p]=power
        set ComboBurn[p]=burn
        call RosterStun(p,target,RosterDuration[index])
        if index==23 then
            set ComboLeft[p]=8
        elseif index==44 then
            set ComboLeft[p]=6
        else
            set ComboLeft[p]=4
        endif
    elseif kind==7 then
        call RosterSummon(p,index,rank)
    elseif kind==9 then
        if index==38 then
            call KibaRollStart(p,rank,target)
        else
            call RosterLine(p,index,rank)
        endif
        if RosterVisual[index]!="" then
            call SkillsBurst(p,RosterVisual[index])
        endif
    elseif kind==10 then
        loop
            exitwhen n>=3
            if FoundationAlive(Companion[p*3+n]) then
                set count=count+1
                set x=GetUnitX(Companion[p*3+n])
                set y=GetUnitY(Companion[p*3+n])
                call RosterArea(p,x,y,RosterRadius[index],power,0.,0.)
            endif
            set n=n+1
        endloop
        if count==0 then
            call RosterArea(p,x,y,RosterRadius[index],power,0.,0.)
        endif
    endif
endfunction
function RosterFindAlly takes integer p returns nothing
    local integer q=0
    local real missing=0.
    local real best=50.
    local real dx=0.
    local real dy=0.
    set RosterAlly=null
    loop
        exitwhen q>=12
        if FoundationAlive(Hero[q]) and not IsUnitEnemy(Hero[q],Player(p)) then
            set dx=GetUnitX(Hero[q])-GetUnitX(Hero[p])
            set dy=GetUnitY(Hero[q])-GetUnitY(Hero[p])
            set missing=GetUnitState(Hero[q],UNIT_STATE_MAX_LIFE)-GetWidgetLife(Hero[q])
            if dx*dx+dy*dy<=700.*700. and missing>best then
                set best=missing
                set RosterAlly=Hero[q]
            endif
        endif
        set q=q+1
    endloop
endfunction
function SkillsCanSeePet takes unit target, player viewer returns boolean
    return IsUnitVisible(target,viewer) and (not IsUnitInvisible(target,viewer) or IsUnitDetected(target,viewer))
endfunction
// Pet availability follows the owner's actual arena/transition state, not team alliances.
function RosterSyncPets takes integer p returns nothing
    local integer k=0
    local unit pet=null
    local boolean waiting=not FoundationAlive(Hero[p]) or IsUnitPaused(Hero[p]) or IsUnitHidden(Hero[p])
    local real dx=0.
    local real dy=0.
    loop
        exitwhen k>=3
        set pet=Companion[p*3+k]
        if FoundationAlive(pet) then
            if IsUnitPaused(pet)!=waiting then
                call PauseUnit(pet,waiting)
                if waiting then
                    call UnitAddAbility(pet,'Avul')
                    call IssueImmediateOrder(pet,"stop")
                else
                    call UnitRemoveAbility(pet,'Avul')
                endif
            endif
            set dx=GetUnitX(pet)-GetUnitX(Hero[p])
            set dy=GetUnitY(pet)-GetUnitY(Hero[p])
            if waiting or dx*dx+dy*dy>1800.*1800. then
                call SetUnitPosition(pet,GetUnitX(Hero[p])+64.*(k+1),GetUnitY(Hero[p]))
            endif
        endif
        set k=k+1
    endloop
    set pet=null
endfunction
// Adapted A00I: native three-second stun, then source 400/600/800 damage and sacrifice.
// Uses the existing 36 companion slots and heartbeat, never a timer per trap.
function RosterPetSpell takes unit caster, unit target, integer raw returns nothing
    local integer p=GetPlayerId(GetOwningPlayer(caster))
    local integer slot=p*3+1
    local integer rank=0
    local integer k=0
    if p<12 and caster==Companion[p*3] and raw=='Rpsm' then
        loop
            exitwhen k>=3
            set slot=p*3+k
            if PetFog[slot]!=null then
                call RemoveUnit(PetFog[slot])
            endif
            set PetFog[slot]=CreateUnit(Player(p),'h01U',GetSpellTargetX()+(k-1)*100.,GetSpellTargetY(),0.)
            set PetFogUntil[slot]=TimeNow+4.
            call UnitApplyTimedLife(PetFog[slot],'BTLF',4.)
            set k=k+1
        endloop
    endif
    set slot=p*3+1
    if p<12 and caster==Companion[slot] and raw=='Rktr' and RosterEnemy(target,Player(p)) then
        set rank=GetUnitAbilityLevel(Hero[p],'RA03')
        set PetTrapVictim[slot]=target
        set PetTrapCaster[slot]=caster
        set PetTrapUntil[slot]=TimeNow+3.
        set PetTrapDamage[slot]=200.+200.*rank
    endif
endfunction
function RosterPetThink takes integer p returns nothing
    local integer k=0
    local integer slot=0
    local unit pet=null
    local unit target=Dummy[(p-ModuloInteger(p,3))/3]
    local real dx=0.
    local real dy=0.
    loop
        exitwhen k>=3
        set slot=p*3+k
        set pet=Companion[slot]
        if PetFog[slot]!=null and (TimeNow>=PetFogUntil[slot] or not FoundationAlive(Hero[p]) or IsUnitPaused(Hero[p])) then
            call RemoveUnit(PetFog[slot])
            set PetFog[slot]=null
        endif
        if PetTrapVictim[slot]!=null and not FoundationAlive(PetTrapCaster[slot]) then
            set PetTrapVictim[slot]=null
            set PetTrapCaster[slot]=null
        endif
        if PetTrapVictim[slot]!=null and TimeNow>=PetTrapUntil[slot] then
            call RosterHit(PetTrapCaster[slot],PetTrapVictim[slot],PetTrapDamage[slot],0.)
            call DestroyEffect(AddSpecialEffectTarget("Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl",PetTrapVictim[slot],"origin"))
            call KillUnit(PetTrapCaster[slot])
            set PetTrapVictim[slot]=null
            set PetTrapCaster[slot]=null
        endif
        if FoundationAlive(pet) and not IsUnitPaused(pet) and FoundationAlive(target) and IsUnitEnemy(target,Player(p)) and SkillsCanSeePet(target,Player(p)) and TimeNow>=PetCastAt[slot] then
            set dx=GetUnitX(pet)-GetUnitX(target)
            set dy=GetUnitY(pet)-GetUnitY(target)
            if GetUnitAbilityLevel(pet,'Rdog')>0 and GetUnitTypeId(pet)=='ra03' and GetUnitState(pet,UNIT_STATE_MANA)>=100. then
                if IssueImmediateOrder(pet,"robogoblin") then
                    set PetCastAt[slot]=TimeNow+30.
                endif
            elseif GetUnitAbilityLevel(pet,'Rktr')>0 and PetTrapVictim[slot]==null and dx*dx+dy*dy<=100.*100. and GetUnitState(pet,UNIT_STATE_MANA)>=100. then
                if IssueTargetOrder(pet,"thunderbolt",target) then
                    set PetCastAt[slot]=TimeNow+25.
                endif
            elseif GetUnitAbilityLevel(pet,'Rpsm')>0 and dx*dx+dy*dy<=700.*700. and GetUnitState(pet,UNIT_STATE_MANA)>=200. then
                if IssuePointOrder(pet,"clusterrockets",GetUnitX(target),GetUnitY(target)) then
                    set PetCastAt[slot]=TimeNow+30.
                endif
            elseif GetUnitAbilityLevel(pet,'Aens')>0 and dx*dx+dy*dy<=600.*600. then
                if IssueTargetOrder(pet,"ensnare",target) then
                    set PetCastAt[slot]=TimeNow+15.
                endif
            endif
        endif
        set k=k+1
    endloop
    set pet=null
    set target=null
endfunction
function RosterTick takes nothing returns nothing
    local integer p=0
    local integer q=0
    local real dx=0.
    local real dy=0.
    local unit pet=null
    loop
        exitwhen p>=128
        if StunDummy[p]!=null and TimeNow>=StunExpires[p] then
            call RemoveUnit(StunDummy[p])
            set StunDummy[p]=null
        endif
        set p=p+1
    endloop
    set p=0
    loop
        exitwhen p>=12
        call RosterSyncPets(p)
        call RosterPetThink(p)
        if ShadowUntil[p]>0. then
            if not FoundationAlive(Hero[p]) or not FoundationAlive(ShadowTarget[p]) then
                call RosterClearShadow(p)
            else
                if not ShadowBuffSeen[p] and (GetUnitAbilityLevel(ShadowTarget[p],'Rsmb')>0 or GetUnitAbilityLevel(ShadowTarget[p],'Bmlt')>0) then
                    set ShadowBuffSeen[p]=true
                    set ShadowUntil[p]=TimeNow+ShadowDuration[p]
                endif
                if TimeNow>=ShadowUntil[p] or (ShadowBuffSeen[p] and GetUnitAbilityLevel(ShadowTarget[p],'Rsmb')==0 and GetUnitAbilityLevel(ShadowTarget[p],'Bmlt')==0) or (not ShadowBuffSeen[p] and TimeNow>=ShadowGraceUntil[p]) then
                    call RosterClearShadow(p)
                else
                    call RosterShadowPulse(p)
                endif
            endif
        endif
        if VisionUntil[p]>0. then
            if not FoundationAlive(Hero[p]) or TimeNow>=VisionUntil[p] then
                call RosterClearVision(p)
            elseif TimeNow>=VisionNext[p] then
                call RosterVisionPulse(p)
            endif
        endif
        if SandWaveUntil[p]>0. and (not FoundationAlive(Hero[p]) or TimeNow>=SandWaveUntil[p]) then
            call RosterClearSand(p)
        endif
        if not FoundationAlive(Hero[p]) then
            if RosterBuffUntil[p]>0. then
                call RosterClearBuff(p)
            endif
            call RosterClearZone(p)
        else
            if RosterBuffUntil[p]>0. and TimeNow>=RosterBuffUntil[p] then
                call RosterClearBuff(p)
            endif
            if ZoneUntil[p]>TimeNow and TimeNow>=ZoneNext[p] then
                if ZoneFollow[p] then
                    set ZoneX[p]=GetUnitX(Hero[p])
                    set ZoneY[p]=GetUnitY(Hero[p])
                endif
                if VisualZoneIndex[p]!=21 and VisualZoneIndex[p]!=41 then
                    call RosterArea(p,ZoneX[p],ZoneY[p],ZoneRadius[p],ZonePower[p],ZoneBurn[p],0.)
                endif
                call VisualPulse(p,VisualZoneIndex[p],ZoneX[p],ZoneY[p])
                set ZoneNext[p]=TimeNow+.5
            elseif ZoneUntil[p]>0. and TimeNow>=ZoneUntil[p] then
                call RosterClearZone(p)
            endif
            if TimeNow>=RosterNextSecond[p] then
                set RosterNextSecond[p]=TimeNow+1.
                if RosterBuffDrain[p]>0. then
                    call SetWidgetLife(Hero[p],RMaxBJ(1.,GetWidgetLife(Hero[p])-GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*RosterBuffDrain[p]))
                endif
                set pet=Companion[p*3]
                if FoundationAlive(pet) and not IsUnitPaused(pet) and GetUnitTypeId(pet)=='rz01' then
                    set q=0
                    loop
                        exitwhen q>=12
                        if FoundationAlive(Hero[q]) and not IsUnitEnemy(Hero[q],Player(p)) then
                            set dx=GetUnitX(Hero[q])-GetUnitX(pet)
                            set dy=GetUnitY(Hero[q])-GetUnitY(pet)
                            if dx*dx+dy*dy<=600.*600. then
                                call SetWidgetLife(Hero[q],RMinBJ(GetUnitState(Hero[q],UNIT_STATE_MAX_LIFE),GetWidgetLife(Hero[q])+35.))
                            endif
                        endif
                        set q=q+1
                    endloop
                endif
            endif
        endif
        set q=0
        loop
            exitwhen q>=3
            set pet=Companion[p*3+q]
            if pet!=null and not FoundationAlive(pet) then
                call RemoveUnit(pet)
                set Companion[p*3+q]=null
            endif
            set q=q+1
        endloop
        set p=p+1
    endloop
    set pet=null
endfunction
