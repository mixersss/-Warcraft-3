// Explicit emergency rebuild; active invasion only. No periodic hero duplication.
function InvasionRebuildAllowed takes integer viewer, integer p returns boolean
    return viewer==p or CampaignTestHost(viewer)
endfunction
function InvasionRebuildWorker takes nothing returns nothing
    local integer p=SasukeRebuildSlot
    local integer k=0
    local integer level=0
    local integer xp=0
    local integer points=0
    local integer strength=0
    local integer agility=0
    local integer intelligence=0
    local integer logRank=0
    local integer skill=0
    local integer viewer=0
    local unit old=null
    local unit fresh=null
    local item carried=null
    local real life=1.
    local real mana=1.
    if p<0 or p>=12 then
        return
    endif
    set old=SasukeRebuildTarget[p]
    set viewer=SasukeRebuildViewer[p]
    if (CampaignStage!=12 and CampaignStage!=31) or CampaignTransition or CampaignFinished or CampaignPermanentDead[p] or HeroRole[p]!=1 or old==null or old!=Hero[p] or GetUnitTypeId(old)==0 then
        set SasukeRebuildTarget[p]=null
        set SasukeRebuildAt[p]=0.
        set old=null
        return
    endif
    if SasukeRebuildAt[p]>TimeNow then
        set old=null
        return
    endif
    // Create and validate first. Keep the original hero if creation fails.
    set fresh=CreateUnit(Player(p),'R001',SpawnX[p],SpawnY[p],90.)
    if fresh==null or GetUnitTypeId(fresh)==0 then
        call DisplayTimedTextToPlayer(Player(viewer),0.,0.,15.,"Не удалось создать нового Саске. Исходный герой и его вещи сохранены.")
        set SasukeRebuildTarget[p]=null
        set SasukeRebuildAt[p]=0.
        set old=null
        set fresh=null
        return
    endif
    call UnitAddAbility(fresh,'AInv')
    if UnitInventorySize(fresh)<6 then
        call RemoveUnit(fresh)
        call DisplayTimedTextToPlayer(Player(viewer),0.,0.,15.,"Пересоздание отменено: новый инвентарь недоступен. Исходный герой сохранён.")
        set SasukeRebuildTarget[p]=null
        set SasukeRebuildAt[p]=0.
        set old=null
        set fresh=null
        return
    endif
    set level=GetHeroLevel(old)
    set xp=GetHeroXP(old)
    set points=GetHeroSkillPoints(old)
    set logRank=GetUnitAbilityLevel(old,'Rlog')
    if FoundationAlive(old) then
        set life=RMinBJ(1.,RMaxBJ(0.,GetWidgetLife(old)/RMaxBJ(1.,GetUnitState(old,UNIT_STATE_MAX_LIFE))))
        set mana=RMinBJ(1.,RMaxBJ(0.,GetUnitState(old,UNIT_STATE_MANA)/RMaxBJ(1.,GetUnitState(old,UNIT_STATE_MAX_MANA))))
    endif
    loop
        exitwhen k>=5
        set SasukeRebuildRanks[p*5+k]=GetUnitAbilityLevel(old,PlayableSkill[5+k])
        set k=k+1
    endloop
    set k=0
    loop
        exitwhen k>=6
        set SasukeRebuildItems[p*6+k]=UnitItemInSlot(old,k)
        set k=k+1
    endloop
    // Finish cast-local references to the retired unit, never to the new body.
    set k=0
    loop
        exitwhen k>=12
        if Lotus35Target[k]==old and Lotus35Caster[k]!=null then
            call Source35LotusEnd(k,false)
        endif
        if Choke35Target[k]==old and Choke35Caster[k]!=null then
            call Source35ChokeEnd(k,true)
        endif
        set k=k+1
    endloop
    call SkillsClearSharingan(p)
    call RosterReset(p)
    set strength=GetHeroStr(old,false)
    set agility=GetHeroAgi(old,false)
    set intelligence=GetHeroInt(old,false)
    call SetHeroLevel(fresh,level,false)
    call SetHeroXP(fresh,xp,false)
    call SetHeroStr(fresh,strength,true)
    call SetHeroAgi(fresh,agility,true)
    call SetHeroInt(fresh,intelligence,true)
    set k=0
    loop
        exitwhen k>=5
        set skill=PlayableSkill[5+k]
        if SasukeRebuildRanks[p*5+k]>0 then
            call UnitAddAbility(fresh,skill)
            call SetUnitAbilityLevel(fresh,skill,SasukeRebuildRanks[p*5+k])
        endif
        set SasukeRebuildRanks[p*5+k]=0
        set k=k+1
    endloop
    if logRank>0 then
        call UnitAddAbility(fresh,'Rlog')
        call SetUnitAbilityLevel(fresh,'Rlog',logRank)
    else
        call UnitRemoveAbility(fresh,'Rlog')
    endif
    call UnitModifySkillPoints(fresh,points-GetHeroSkillPoints(fresh))
    set k=0
    loop
        exitwhen k>=6
        set carried=SasukeRebuildItems[p*6+k]
        if carried!=null then
            call UnitRemoveItem(old,carried)
            if UnitAddItem(fresh,carried) then
                call UnitDropItemSlot(fresh,carried,k)
            else
                // Do not delete an item even if a native pickup is unexpectedly rejected.
                call SetItemPosition(carried,SpawnX[p]+80.,SpawnY[p])
                call DisplayTimedTextToPlayer(Player(viewer),0.,0.,15.,"Один предмет не удалось надеть: он сохранён рядом с точкой появления Саске.")
            endif
        endif
        set SasukeRebuildItems[p*6+k]=null
        set k=k+1
    endloop
    set Hero[p]=fresh
    set HeroType[p]='R001'
    if CampaignSasuke==old or CampaignSasukePlayer==p then
        set CampaignSasuke=fresh
    endif
    if CampaignOroTarget==old then
        set CampaignOroTarget=null
    endif
    set k=0
    loop
        exitwhen k>=4
        if Dummy[k]==old then
            set Dummy[k]=fresh
        endif
        set k=k+1
    endloop
    if NPCSourceReady then
        call NPCSourceHeroes()
    endif
    if NPCCooldowns!=null then
        call FlushChildHashtable(NPCCooldowns,GetHandleId(old))
    endif
    if NPCHiddenAbilities!=null then
        call FlushChildHashtable(NPCHiddenAbilities,GetHandleId(old))
    endif
    // Native removal, not KillUnit: no extra death, bounty, duplicate corpse or inventory.
    call RemoveUnit(old)
    set StoryRevive[p]=0.
    set SasukeReviveFailures[p]=0
    set SasukeHiddenSince[p]=0.
    set SasukePauseSince[p]=0.
    set SasukeAlphaSince[p]=0.
    set SasukeOutsideSince[p]=0.
    set SasukeMorphRepairAt[p]=0.
    set SasukeLastType[p]='R001'
    set SasukeLastSource[p]="Аварийное пересоздание"
    set SasukeSafeX[p]=GetUnitX(fresh)
    set SasukeSafeY[p]=GetUnitY(fresh)
    set SasukeSafeReady[p]=true
    call SetUnitState(fresh,UNIT_STATE_LIFE,RMaxBJ(1.,GetUnitState(fresh,UNIT_STATE_MAX_LIFE)*life))
    call SetUnitState(fresh,UNIT_STATE_MANA,GetUnitState(fresh,UNIT_STATE_MAX_MANA)*mana)
    call InvasionAfterRevive(p)
    call IssueImmediateOrder(fresh,"stop")
    set SasukeRebuildTarget[p]=null
    set SasukeRebuildAt[p]=0.
    set SasukeRebuildNext[p]=TimeNow+30.
    set SasukeRebuildCount[p]=SasukeRebuildCount[p]+1
    if GetPlayerController(Player(p))!=MAP_CONTROL_COMPUTER then
        call SelectUnitForPlayerSingle(fresh,Player(p))
        call PanCameraToTimedForPlayer(Player(p),GetUnitX(fresh),GetUnitY(fresh),.3)
    endif
    call DisplayTimedTextToPlayer(Player(viewer),0.,0.,20.,"Саске пересоздан в обычном облике. Прогресс и вещи сохранены; временные эффекты сброшены.")
    set carried=null
    set old=null
    set fresh=null
endfunction
function InvasionRebuildCommand takes integer viewer returns nothing
    local integer p=CampaignSasukePlayer
    if (CampaignStage!=12 and CampaignStage!=31) or CampaignTransition or CampaignFinished then
        call DisplayTimedTextToPlayer(Player(viewer),0.,0.,12.,"Аварийное пересоздание доступно только во время активной защиты Конохи.")
        return
    endif
    if p<0 or p>=12 or HeroRole[p]!=1 or Hero[p]==null or GetUnitTypeId(Hero[p])==0 or CampaignPermanentDead[p] then
        call DisplayTimedTextToPlayer(Player(viewer),0.,0.,12.,"Текущий сюжетный Саске не найден. Пересоздавать сюжетных двойников нельзя.")
        return
    endif
    if not InvasionRebuildAllowed(viewer,p) then
        call DisplayTimedTextToPlayer(Player(viewer),0.,0.,12.,"Команда доступна владельцу Саске или первому игроку-человеку.")
        return
    endif
    if SasukeRebuildTarget[p]!=null then
        call DisplayTimedTextToPlayer(Player(viewer),0.,0.,12.,"Пересоздание уже запрошено. До восстановления: "+I2S(R2I(RMaxBJ(0.,SasukeRebuildAt[p]-TimeNow)))+" сек.")
        return
    endif
    if TimeNow<SasukeRebuildNext[p] then
        call DisplayTimedTextToPlayer(Player(viewer),0.,0.,12.,"Повторное аварийное пересоздание будет доступно через "+I2S(R2I(SasukeRebuildNext[p]-TimeNow))+" сек.")
        return
    endif
    set SasukeRebuildTarget[p]=Hero[p]
    set SasukeRebuildViewer[p]=viewer
    set SasukeRebuildAt[p]=TimeNow
    if IsUnitType(Hero[p],UNIT_TYPE_DEAD) and SasukeReviveFailures[p]==0 then
        if StoryRevive[p]<=0. then
            set StoryRevive[p]=TimeNow+20.
        endif
        set SasukeRebuildAt[p]=RMaxBJ(TimeNow,StoryRevive[p])
    endif
    if SasukeRebuildAt[p]>TimeNow then
        call DisplayTimedTextToPlayer(Player(viewer),0.,0.,15.,"Пересоздание назначено на конец обычного ожидания возрождения. Повторять команду не нужно.")
    else
        set SasukeRebuildSlot=p
        call ExecuteFunc("InvasionRebuildWorker")
    endif
endfunction
function InvasionRebuildTick takes nothing returns nothing
    local integer p=0
    loop
        exitwhen p>=12
        if SasukeRebuildTarget[p]!=null then
            if (CampaignStage!=12 and CampaignStage!=31) or CampaignTransition or CampaignFinished or CampaignPermanentDead[p] or Hero[p]!=SasukeRebuildTarget[p] then
                set SasukeRebuildTarget[p]=null
                set SasukeRebuildAt[p]=0.
            elseif TimeNow>=SasukeRebuildAt[p] then
                set SasukeRebuildSlot=p
                call ExecuteFunc("InvasionRebuildWorker")
            endif
        endif
        set p=p+1
    endloop
endfunction
