// Shared fixed-size state: no per-cast timers, locations, or leaked effect handles.
function SkillsClearSharingan takes integer p returns nothing
    call UnitRemoveAbility(Hero[p],'Rsev')
    call UnitRemoveAbility(Hero[p],'Rscr')
    call UnitRemoveAbility(Hero[p],'Rsag')
    set SharinganUntil[p]=0.
    if SharinganArt[p]!=null then
        call DestroyEffect(SharinganArt[p])
        set SharinganArt[p]=null
    endif
endfunction
function SkillsBurst takes integer p, string model returns nothing
    if BurstArt[p]!=null then
        call DestroyEffect(BurstArt[p])
    endif
    set BurstArt[p]=AddSpecialEffectTarget(model,Hero[p],"hand right")
    set BurstUntil[p]=TimeNow+1.
endfunction
function SkillsHoldFlash takes effect art returns nothing
    if SkillFlash[SkillFlashCursor]!=null then
        call DestroyEffect(SkillFlash[SkillFlashCursor])
    endif
    set SkillFlash[SkillFlashCursor]=art
    set SkillFlashUntil[SkillFlashCursor]=TimeNow+1.5
    set SkillFlashCursor=ModuloInteger(SkillFlashCursor+1,256)
endfunction
function SkillsFlashAt takes string model, real x, real y returns nothing
    call SkillsHoldFlash(AddSpecialEffect(model,x,y))
endfunction
function SkillsFlashTarget takes string model, unit target returns nothing
    call SkillsHoldFlash(AddSpecialEffectTarget(model,target,"origin"))
endfunction
// ROSTER_RUNTIME
function SkillsLearnBot takes integer p returns nothing
    local integer role=HeroRole[p]
    local integer pass=0
    local integer k=0
    local integer raw=0
    local integer rank=0
    if role<0 then
        return
    endif
    loop
        exitwhen pass>=5 or GetHeroSkillPoints(Hero[p])<=0
        set k=4
        loop
            exitwhen k<0 or GetHeroSkillPoints(Hero[p])<=0
            set raw=PlayableSkill[role*5+k]
            set rank=GetUnitAbilityLevel(Hero[p],raw)
            if rank<SkillRanks[role*5+k] and GetHeroLevel(Hero[p])>=SkillRequired[role*5+k]+rank*SkillSkip[role*5+k] then
                call SelectHeroSkill(Hero[p],raw)
            endif
            set k=k-1
        endloop
        set pass=pass+1
    endloop
endfunction
function SkillsEffect takes nothing returns nothing
    local unit caster=GetTriggerUnit()
    local unit target=GetSpellTargetUnit()
    local unit other=null
    local integer p=GetPlayerId(GetOwningPlayer(caster))
    local integer raw=GetSpellAbilityId()
    local integer rank=GetUnitAbilityLevel(caster,raw)
    local integer j=0
    local integer index=-1
    local real x=0.
    local real y=0.
    if p>=12 or caster!=Hero[p] or IsUnitIllusion(caster) then
        set caster=null
        set target=null
        return
    endif
    loop
        exitwhen j>=60
        if PlayableSkill[j]==raw then
            set index=j
            if SkillAudio[j]>=0 then
                call FoundationSound(SkillAudio[j])
            endif
        endif
        set j=j+1
    endloop
    if raw=='Rlog' then
        call CommonLogEffect(p)
    endif
    if index>=0 then
        if not SkillPassive[index] then
            set SkillPoseAbility[p]=index
            set VisualPoseLife[p]=RMaxBJ(1.,SkillHold[index])+.35
            set SkillPoseQueued[p]=true
            set SkillPoseIndex[p]=SkillAnimation[index]
            set SkillPoseType[p]=GetUnitTypeId(caster)
        endif
        call RosterApply(p,index,rank,target)
        call VisualApply(p,index,rank,target)
        if SkillHold[index]>0. then
            set VisualChannelIndex[p]=index
            set VisualChannelUntil[p]=TimeNow+SkillHold[index]
            if GetUnitTypeId(caster)==HeroType[p] then
                call SetUnitTimeScale(caster,SkillPoseScale[index])
            else
                call SetUnitTimeScale(caster,SkillFormPoseScale[index])
            endif
            set BotNextCast[p]=RMaxBJ(BotNextCast[p],TimeNow+SkillHold[index]+.25)
        endif
    endif
    if raw=='Rn04' and FoundationAlive(target) then
        set x=GetUnitX(target)
        set y=GetUnitY(target)
        call DestroyEffect(AddSpecialEffect("Abilities\\Spells\\Human\\Thunderclap\\ThunderClapCaster.mdl",x,y))
        call GroupEnumUnitsInRange(SkillScratch,x,y,220.,null)
        loop
            set other=FirstOfGroup(SkillScratch)
            exitwhen other==null
            call GroupRemoveUnit(SkillScratch,other)
            if other!=target and FoundationAlive(other) and IsUnitEnemy(other,GetOwningPlayer(caster)) and not IsUnitType(other,UNIT_TYPE_STRUCTURE) and not IsUnitType(other,UNIT_TYPE_MAGIC_IMMUNE) then
                call UnitDamageTarget(caster,other,25.+100.*rank,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS)
            endif
        endloop
    elseif raw=='Rs02' then
        call SkillsClearSharingan(p)
        call UnitAddAbility(caster,'Rsev')
        call UnitAddAbility(caster,'Rscr')
        call UnitAddAbility(caster,'Rsag')
        call SetUnitAbilityLevel(caster,'Rsev',rank)
        call SetUnitAbilityLevel(caster,'Rscr',rank)
        call SetUnitAbilityLevel(caster,'Rsag',rank)
        set SharinganArt[p]=AddSpecialEffectTarget("Eye_Sharingan.mdl",caster,"overhead")
        set SharinganUntil[p]=TimeNow+18.
    elseif raw=='Rs03' and FoundationAlive(target) then
        set ComboTarget[p]=target
        set ComboLeft[p]=3
        set ComboBurn[p]=0.
        set ComboDamage[p]=40.+60.*rank
    endif
    set other=null
    set target=null
    set caster=null
endfunction
function SkillsEndcast takes nothing returns nothing
    local unit caster=GetTriggerUnit()
    local integer p=GetPlayerId(GetOwningPlayer(caster))
    local integer index=0
    if p<12 and caster==Hero[p] then
        set index=VisualChannelIndex[p]
        if VisualChannelUntil[p]>0. and index>=0 then
            if GetSpellAbilityId()==PlayableSkill[index] then
                if index==26 or index==28 then
                    call VisualLiftEnd(p)
                endif
                if index==21 or index==41 or index==43 then
                    call RosterClearZone(p)
                    call RosterClearBuff(p)
                endif
                call SetUnitTimeScale(caster,1.)
                call SetUnitAnimation(caster,"stand")
                set VisualChannelUntil[p]=0.
                set VisualChannelIndex[p]=-1
                set SkillPoseQueued[p]=false
            endif
        endif
    endif
    set caster=null
endfunction
function SkillsSummoned takes nothing returns nothing
    local unit summoner=GetSummoningUnit()
    local unit summoned=GetSummonedUnit()
    local integer p=GetPlayerId(GetOwningPlayer(summoner))
    if p<12 and summoner==Hero[p] and GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER and FoundationAlive(Dummy[(p-ModuloInteger(p,3))/3]) then
        call IssueTargetOrder(summoned,"attack",Dummy[(p-ModuloInteger(p,3))/3])
    endif
    set summoned=null
    set summoner=null
endfunction
function SkillsTick takes nothing returns nothing
    local integer p=0
    local unit u=null
    local unit target=null
    local real dx=0.
    local real dy=0.
    loop
        exitwhen p>=256
        if SkillFlash[p]!=null and TimeNow>=SkillFlashUntil[p] then
            call DestroyEffect(SkillFlash[p])
            set SkillFlash[p]=null
        endif
        set p=p+1
    endloop
    set p=0
    loop
        exitwhen p>=12
        set u=Hero[p]
        if SkillPoseQueued[p] then
            set SkillPoseQueued[p]=false
            if FoundationAlive(u) and GetUnitTypeId(u)==SkillPoseType[p] then
                // A real Channel already plays and holds this pose. Restarting it here
                // would cut the end of the sphere/throw sequence by another quarter second.
                if SkillHold[SkillPoseAbility[p]]<=0. then
                    call VisualPose(p,SkillPoseAbility[p])
                endif
            endif
        endif
        if VisualChannelUntil[p]>0. and (not FoundationAlive(u) or TimeNow>VisualChannelUntil[p]+.5) then
            call SetUnitTimeScale(u,1.)
            set VisualChannelUntil[p]=0.
            set VisualChannelIndex[p]=-1
        endif
        if SharinganUntil[p]>0. and (TimeNow>=SharinganUntil[p] or not FoundationAlive(u)) then
            call SkillsClearSharingan(p)
        endif
        if BurstArt[p]!=null and (TimeNow>=BurstUntil[p] or not FoundationAlive(u)) then
            call DestroyEffect(BurstArt[p])
            set BurstArt[p]=null
        endif
        if ComboLeft[p]>0 then
            set target=ComboTarget[p]
            if FoundationAlive(u) and FoundationAlive(target) and IsUnitEnemy(target,Player(p)) then
                set dx=GetUnitX(u)-GetUnitX(target)
                set dy=GetUnitY(u)-GetUnitY(target)
                if dx*dx+dy*dy<=650.*650. and not IsUnitType(target,UNIT_TYPE_MAGIC_IMMUNE) then
                    call SetUnitAnimation(u,"attack")
                    call DestroyEffect(AddSpecialEffectTarget("Abilities\\Spells\\Human\\Thunderclap\\ThunderClapCaster.mdl",target,"origin"))
                    call RosterHit(u,target,ComboDamage[p],ComboBurn[p])
                    set ComboLeft[p]=ComboLeft[p]-1
                else
                    set ComboLeft[p]=0
                endif
            else
                set ComboLeft[p]=0
            endif
            if ComboLeft[p]==0 then
                set ComboTarget[p]=null
            endif
        endif
        set p=p+1
    endloop
    call CommonLogTick()
    call RosterTick()
    set u=null
    set target=null
endfunction
function SkillsBot takes integer p returns boolean
    local integer role=HeroRole[p]
    local integer k=4
    local integer raw=0
    local integer rank=0
    local unit u=Hero[p]
    local unit target=Dummy[(p-ModuloInteger(p,3))/3]
    local boolean issued=false
    local real dx=0.
    local real dy=0.
    if not SkillDataReady or role<0 or not FoundationAlive(u) or not FoundationAlive(target) or TimeNow<BotNextCast[p] or ComboLeft[p]>0 or TimeNow<VisualChannelUntil[p] then
        set u=null
        set target=null
        return false
    endif
    call SkillsLearnBot(p)
    set dx=GetUnitX(u)-GetUnitX(target)
    set dy=GetUnitY(u)-GetUnitY(target)
    if dx*dx+dy*dy>700.*700. then
        set u=null
        set target=null
        return false
    endif
    loop
        exitwhen k<0 or issued
        set raw=PlayableSkill[role*5+k]
        set rank=GetUnitAbilityLevel(u,raw)
        if rank>0 and not SkillPassive[role*5+k] and TimeNow>=BotReadyAt[p*5+k] and GetUnitState(u,UNIT_STATE_MANA)>=SkillMana[(role*5+k)*4+rank-1] then
            if SkillHeal[role*5+k] then
                call RosterFindAlly(p)
                set target=RosterAlly
                set RosterAlly=null
            else
                set target=Dummy[(p-ModuloInteger(p,3))/3]
            endif
            if SkillHeal[role*5+k] and target==null then
                // Healing only spends mana when an ally actually needs it.
            elseif SkillToggle[role*5+k] and GetUnitAbilityLevel(u,'BNms')>0 then
                // Leave an active native mana shield enabled.
            elseif SkillMorph[role*5+k] and GetUnitTypeId(u)!=HeroType[p] then
                // Do not re-enter a native transformation while already transformed.
            elseif (RosterMechanic[role*5+k]==5 or (RosterMechanic[role*5+k]==2 and SkillTarget[role*5+k]==0)) and dx*dx+dy*dy>RosterRadius[role*5+k]*RosterRadius[role*5+k] then
                // Self-centered damage is useful only inside its actual hit radius.
            elseif SkillTarget[role*5+k]==0 then
                set issued=IssueImmediateOrder(u,SkillOrder[role*5+k])
            elseif SkillTarget[role*5+k]==1 then
                set issued=IssueTargetOrder(u,SkillOrder[role*5+k],target)
            else
                set issued=IssuePointOrder(u,SkillOrder[role*5+k],GetUnitX(target),GetUnitY(target))
            endif
            if issued then
                set BotReadyAt[p*5+k]=TimeNow+SkillCooldown[role*5+k]+2.
                set BotNextCast[p]=TimeNow+RMaxBJ(2.5,SkillHold[role*5+k]+.25)
            endif
        endif
        set k=k-1
    endloop
    set u=null
    set target=null
    return issued
endfunction
function SkillsChoose takes integer p, integer role returns nothing
    local unit old=Hero[p]
    local item carried=null
    local integer k=0
    local integer xp=0
    if StoryStarted[(p-ModuloInteger(p,3))/3] then
        call DisplayTimedTextToPlayer(Player(p),0.,0.,8.,"Выбор героя закрыт: отряд уже вышел на миссию.")
        set old=null
        return
    endif
    if GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER or not FoundationAlive(old) then
        return
    endif
    call TreeJumpEnd(p)
    set xp=GetHeroXP(old)
    call SkillsClearSharingan(p)
    call RosterReset(p)
    if BurstArt[p]!=null then
        call DestroyEffect(BurstArt[p])
        set BurstArt[p]=null
    endif
    set ComboLeft[p]=0
    set ComboTarget[p]=null
    set ComboBurn[p]=0.
    set ResumeAt[p]=0.
    set AnimCursor[p]=0
    set VoiceCursor[p]=0
    set HeroTemplate[p]=role
    set HeroRole[p]=role
    set HeroType[p]=RosterHeroType[role]
    set Hero[p]=CreateUnit(Player(p),HeroType[p],SpawnX[p],SpawnY[p],90.)
    call VisualPrepareHero(p)
    call SetHeroXP(Hero[p],xp,false)
    call RosterGrantInnate(p)
    if GetHeroLevel(Hero[p])<1 then
        call SetHeroLevel(Hero[p],1,false)
    endif
    loop
        exitwhen k>=6
        set carried=UnitItemInSlot(old,k)
        if carried!=null then
            call UnitRemoveItem(old,carried)
            call UnitAddItem(Hero[p],carried)
        endif
        set k=k+1
    endloop
    call RemoveUnit(old)
    call SelectUnitForPlayerSingle(Hero[p],Player(p))
    call PanCameraToTimedForPlayer(Player(p),SpawnX[p],SpawnY[p],0.)
    call DisplayTimedTextToPlayer(Player(p),0,0,12.,"Герой выбран. Изучи техники кнопкой +. Когда будете готовы, напиши -go.")
    set old=null
    set carried=null
endfunction
// GENERATED_SKILL_FUNCTIONS
function SkillsInit takes nothing returns nothing
    local integer p=0
    local trigger spells=CreateTrigger()
    local trigger summons=CreateTrigger()
    local trigger ended=CreateTrigger()
    local timer visualclock=CreateTimer()
    local timer clock=CreateTimer()
    set SkillScratch=CreateGroup()
// GENERATED_SKILLS
    set RosterBonus[0]='Rbev'
    set RosterBonus[1]='Rbcr'
    set RosterBonus[2]='Rbat'
    set RosterBonus[3]='Rbas'
    set RosterBonus[4]='Rbar'
    set RosterBonus[5]='Rbms'
    loop
        exitwhen p>=12
        call TriggerRegisterPlayerUnitEvent(spells,Player(p),EVENT_PLAYER_UNIT_SPELL_EFFECT,null)
        call TriggerRegisterPlayerUnitEvent(ended,Player(p),EVENT_PLAYER_UNIT_SPELL_ENDCAST,null)
        call TriggerRegisterPlayerUnitEvent(summons,Player(p),EVENT_PLAYER_UNIT_SUMMON,null)
        set HeroRole[p]=p
        set p=p+1
    endloop
    call TriggerAddAction(spells,function SkillsEffect)
    call TriggerAddAction(ended,function SkillsEndcast)
    call TimerStart(visualclock,.05,true,function VisualTick)
    call TriggerAddAction(summons,function SkillsSummoned)
    call TimerStart(clock,.25,true,function SkillsTick)
    set ended=null
    set visualclock=null
    set spells=null
    set summons=null
    set clock=null
endfunction
