// Independent adaptations for the remaining roster; all state is bounded.
function RosterFlag takes integer mask, integer flag returns boolean
    return ModuloInteger((mask-ModuloInteger(mask,flag))/flag,2)==1
endfunction
function RosterClearBuff takes integer p returns nothing
    local integer n=0
    loop
        exitwhen n>=6
        call UnitRemoveAbility(Hero[p],RosterBonus[n])
        set n=n+1
    endloop
    call UnitRemoveAbility(Hero[p],'Atru')
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
function RosterReset takes integer p returns nothing
    local integer k=0
    call RosterClearBuff(p)
    call RosterClearZone(p)
    loop
        exitwhen k>=3
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
    call SetUnitAbilityLevel(dummy,'Rstn',rank)
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
            call RosterHit(Hero[p],target,damage,burn)
            if stun>0. then
                call RosterStun(p,target,stun)
            endif
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
    if HeroRole[p]==4 or HeroRole[p]==8 then
        if ModuloInteger(index,5)==0 then
            call UnitAddAbility(Hero[p],'Atru')
            call UnitMakeAbilityPermanent(Hero[p],true,'Atru')
        endif
    endif
    set RosterBuffUntil[p]=TimeNow+RosterDuration[index]
    if HeroRole[p]==3 and ModuloInteger(index,5)==3 then
        set RosterBuffDrain[p]=.02
    endif
    if RosterVisual[index]!="" and RosterMechanic[index]==4 then
        set RosterBuffArt[p]=AddSpecialEffectTarget(RosterVisual[index],Hero[p],"origin")
    endif
endfunction
function RosterSummon takes integer p, integer index, integer rank returns nothing
    local integer slot=p*3+RosterPetSlot[index]
    local integer raw=RosterPetType[index*4+rank-1]
    if Companion[slot]!=null then
        call RemoveUnit(Companion[slot])
    endif
    set Companion[slot]=CreateUnit(Player(p),raw,GetUnitX(Hero[p])+100.,GetUnitY(Hero[p]),GetUnitFacing(Hero[p]))
    call UnitApplyTimedLife(Companion[slot],'BTLF',RosterDuration[index])
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
    if kind==0 then
        return
    endif
    if SkillAnimation[index]>=0 then
        if GetUnitTypeId(Hero[p])==HeroType[p] then
            call SetUnitAnimationByIndex(Hero[p],SkillAnimation[index])
        else
            call SetUnitAnimation(Hero[p],"spell")
        endif
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
            call DestroyEffect(AddSpecialEffectTarget(RosterVisual[index],target,"origin"))
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
            call DestroyEffect(AddSpecialEffect(RosterVisual[index],x,y))
        endif
    elseif kind==3 then
        if FoundationAlive(target) and not IsUnitEnemy(target,Player(p)) and not IsUnitType(target,UNIT_TYPE_STRUCTURE) then
            call SetWidgetLife(target,RMinBJ(GetUnitState(target,UNIT_STATE_MAX_LIFE),GetWidgetLife(target)+power))
            call DestroyEffect(AddSpecialEffectTarget(RosterVisual[index],target,"origin"))
        endif
    elseif kind==4 then
        call RosterBuff(p,index,rank)
    elseif kind==5 or kind==8 then
        call RosterClearZone(p)
        if kind==5 then
            call RosterBuff(p,index,rank)
        else
            set x=GetSpellTargetX()
            set y=GetSpellTargetY()
        endif
        set ZoneFollow[p]=kind==5
        set ZoneX[p]=x
        set ZoneY[p]=y
        set ZoneRadius[p]=RosterRadius[index]
        set ZonePower[p]=power
        set ZoneBurn[p]=burn
        set ZoneUntil[p]=TimeNow+RosterDuration[index]
        set ZoneNext[p]=TimeNow+.5
        call RosterArea(p,x,y,RosterRadius[index],power,burn,0.)
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
        call RosterLine(p,index,rank)
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
                call DestroyEffect(AddSpecialEffect("Note.mdl",x,y))
            endif
            set n=n+1
        endloop
        if count==0 then
            call RosterArea(p,x,y,RosterRadius[index],power,0.,0.)
            call DestroyEffect(AddSpecialEffect("Note.mdl",x,y))
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
                call RosterArea(p,ZoneX[p],ZoneY[p],ZoneRadius[p],ZonePower[p],ZoneBurn[p],0.)
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
                if FoundationAlive(pet) and GetUnitTypeId(pet)=='rz01' then
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
