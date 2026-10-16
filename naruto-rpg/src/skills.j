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
    set BurstArt[p]=AddSpecialEffectTarget(model,Hero[p],"hand,right")
    set BurstUntil[p]=TimeNow+1.
endfunction
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
    local real x=0.
    local real y=0.
    if p>=12 or caster!=Hero[p] or IsUnitIllusion(caster) then
        set caster=null
        set target=null
        return
    endif
    loop
        exitwhen j>=10
        if PlayableSkill[j]==raw and SkillAudio[j]>=0 then
            call FoundationSound(SkillAudio[j])
        endif
        set j=j+1
    endloop
    if raw=='Rn04' and FoundationAlive(target) then
        set x=GetUnitX(target)
        set y=GetUnitY(target)
        call SkillsBurst(p,"Abilities\\Spells\\Human\\ManaFlare\\ManaFlareBoltImpact.mdl")
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
    elseif raw=='Rs04' then
        call SkillsBurst(p,"Abilities\\Weapons\\FarseerMissile\\FarseerMissile.mdl")
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
        set ComboDamage[p]=40.+60.*rank
    elseif raw=='Rn03' then
        call DestroyEffect(AddSpecialEffect("Kuchiyose.mdl",GetUnitX(caster),GetUnitY(caster)))
    endif
    set other=null
    set target=null
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
        exitwhen p>=12
        set u=Hero[p]
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
                    call UnitDamageTarget(u,target,ComboDamage[p],false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS)
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
    if role<0 or not FoundationAlive(u) or not FoundationAlive(target) or TimeNow<BotNextCast[p] or ComboLeft[p]>0 then
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
        if rank>0 and not (role==0 and k==0) and TimeNow>=BotReadyAt[p*5+k] and GetUnitState(u,UNIT_STATE_MANA)>=SkillMana[(role*5+k)*4+rank-1] then
            if k==4 and GetUnitTypeId(u)!=HeroType[p] then
                // Do not re-enter a native transformation while already transformed.
            elseif SkillTarget[role*5+k]==0 then
                set issued=IssueImmediateOrder(u,SkillOrder[role*5+k])
            elseif SkillTarget[role*5+k]==1 then
                set issued=IssueTargetOrder(u,SkillOrder[role*5+k],target)
            else
                set issued=IssuePointOrder(u,SkillOrder[role*5+k],GetUnitX(target),GetUnitY(target))
            endif
            if issued then
                set BotReadyAt[p*5+k]=TimeNow+SkillCooldown[role*5+k]+2.
                set BotNextCast[p]=TimeNow+2.5
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
    if GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER or not FoundationAlive(old) then
        return
    endif
    set xp=GetHeroXP(old)
    call SkillsClearSharingan(p)
    if BurstArt[p]!=null then
        call DestroyEffect(BurstArt[p])
        set BurstArt[p]=null
    endif
    set ComboLeft[p]=0
    set ComboTarget[p]=null
    set ResumeAt[p]=0.
    set AnimCursor[p]=0
    set VoiceCursor[p]=0
    set HeroTemplate[p]=role
    set HeroRole[p]=role
    if role==0 then
        set HeroType[p]='R000'
    else
        set HeroType[p]='R001'
    endif
    set Hero[p]=CreateUnit(Player(p),HeroType[p],SpawnX[p],SpawnY[p],90.)
    call SetHeroXP(Hero[p],xp,false)
    if GetHeroLevel(Hero[p])<10 then
        call SetHeroLevel(Hero[p],10,false)
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
    call DisplayTimedTextToPlayer(Player(p),0,0,12.,"Тренировочная смена героя: изучи техники кнопкой +. -practice даёт 30-й уровень только в этой тестовой сборке.")
    set old=null
    set carried=null
endfunction
function SkillsInit takes nothing returns nothing
    local integer p=0
    local trigger spells=CreateTrigger()
    local trigger summons=CreateTrigger()
    local timer clock=CreateTimer()
    set SkillScratch=CreateGroup()
// GENERATED_SKILLS
    loop
        exitwhen p>=12
        call TriggerRegisterPlayerUnitEvent(spells,Player(p),EVENT_PLAYER_UNIT_SPELL_EFFECT,null)
        call TriggerRegisterPlayerUnitEvent(summons,Player(p),EVENT_PLAYER_UNIT_SUMMON,null)
        if p==0 or p==1 then
            set HeroRole[p]=p
        else
            set HeroRole[p]=-1
        endif
        set p=p+1
    endloop
    call TriggerAddAction(spells,function SkillsEffect)
    call TriggerAddAction(summons,function SkillsSummoned)
    call TimerStart(clock,.25,true,function SkillsTick)
    set spells=null
    set summons=null
    set clock=null
endfunction
