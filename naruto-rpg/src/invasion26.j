// Source spell cleanup must never delete the registered real Sasuke during invasion.
function InvasionSasukeSlot takes unit u returns integer
    local integer p=0
    if u==null or CampaignStage!=12 or CampaignTransition then
        return -1
    endif
    set p=GetPlayerId(GetOwningPlayer(u))
    if p<12 and u==Hero[p] and HeroRole[p]==1 and not IsUnitIllusion(u) then
        return p
    endif
    return -1
endfunction
function InvasionSourceRemove takes unit u, string source returns nothing
    local integer p=InvasionSasukeSlot(u)
    if p>=0 then
        set SasukeLastSource[p]=source
        set SasukeBlockedRemove[p]=SasukeBlockedRemove[p]+1
        // Preserve a legitimate death/corpse so the ordinary revival still works.
        return
    endif
    call RemoveUnit(u)
endfunction
function InvasionSourceHide takes unit u, string source returns nothing
    local integer p=InvasionSasukeSlot(u)
    if p>=0 then
        set SasukeLastSource[p]=source
    endif
    call ShowUnitHide(u)
endfunction
function InvasionSourcePause takes unit u, boolean pause, string source returns nothing
    local integer p=InvasionSasukeSlot(u)
    if p>=0 and pause then
        set SasukeLastSource[p]=source
    endif
    call PauseUnit(u,pause)
endfunction
// Source drain/heal callbacks can outlive their target. Never put positive HP
// on an engine-dead unit: only ReviveHero may restore a real dead hero.
function InvasionSourceLife takes unit u, real life, string source returns nothing
    local integer p=InvasionSasukeSlot(u)
    if u==null or GetUnitTypeId(u)==0 or IsUnitType(u,UNIT_TYPE_DEAD) then
        if p>=0 then
            set SasukeCorpseHealsBlocked[p]=SasukeCorpseHealsBlocked[p]+1
            set SasukeLastSource[p]=source
        endif
        return
    endif
    call SetWidgetLife(u,life)
endfunction
function InvasionSourceLifePercent takes unit u, real percent, string source returns nothing
    local integer p=InvasionSasukeSlot(u)
    if u==null or GetUnitTypeId(u)==0 or IsUnitType(u,UNIT_TYPE_DEAD) then
        if p>=0 then
            set SasukeCorpseHealsBlocked[p]=SasukeCorpseHealsBlocked[p]+1
            set SasukeLastSource[p]=source
        endif
        return
    endif
    call SetUnitLifePercentBJ(u,percent)
endfunction

function InvasionAfterRevive takes integer p returns nothing
    local unit u=Hero[p]
    if CampaignStage==12 and not CampaignTransition and HeroRole[p]==1 and FoundationAlive(u) then
        call CommonLogClear(p)
        call UnitRemoveAbility(u,'Apiv')
        call ShowUnit(u,false)
        call UnitRemoveAbility(u,'Aloc')
        call ShowUnit(u,true)
        call UnitRemoveAbility(u,'Avul')
        call SetUnitInvulnerable(u,false)
        call PauseUnit(u,false)
        call SetUnitPathing(u,true)
        call SetUnitFlyHeight(u,0.,0.)
        call SetUnitTimeScale(u,1.)
        call SetUnitVertexColor(u,255,255,255,255)
        call AddUnitAnimationProperties(u,"alternate",false)
        call SetUnitAnimation(u,"stand")
        set SasukeLastType[p]=GetUnitTypeId(u)
        set SasukeMorphRepairAt[p]=0.
    endif
    set u=null
endfunction
function InvasionQueueCorpse takes integer p returns nothing
    if CampaignStage==12 and not CampaignTransition and not CampaignFinished and not CampaignPermanentDead[p] and HeroRole[p]==1 and Hero[p]!=null and IsUnitType(Hero[p],UNIT_TYPE_DEAD) then
        if StoryRevive[p]<=0. then
            set StoryRevive[p]=TimeNow+20.
        endif
        if TimeNow>=StoryRevive[p] then
            if ReviveHero(Hero[p],SpawnX[p],SpawnY[p],true) and FoundationAlive(Hero[p]) then
                set StoryRevive[p]=0.
                call SetUnitState(Hero[p],UNIT_STATE_MANA,GetUnitState(Hero[p],UNIT_STATE_MAX_MANA))
                call InvasionAfterRevive(p)
            else
                set StoryRevive[p]=TimeNow+1.
                set SasukeReviveFailures[p]=SasukeReviveFailures[p]+1
            endif
        endif
        set SasukeHiddenSince[p]=0.
        set SasukePauseSince[p]=0.
        set SasukeAlphaSince[p]=0.
        set SasukeMorphRepairAt[p]=0.
    endif
endfunction
function InvasionSasukeStatus takes integer viewer returns nothing
    local integer p=0
    local unit u=null
    loop
        exitwhen p>=12
        if HeroRole[p]==1 and Hero[p]!=null then
            set u=Hero[p]
            if IsUnitType(u,UNIT_TYPE_DEAD) then
                call DisplayTimedTextToPlayer(Player(viewer),0.,0.,25.,"Движок: Саске мёртв, даже если показано положительное HP. До возрождения: "+I2S(R2I(RMaxBJ(0.,StoryRevive[p]-TimeNow)))+" сек.")
            endif
            call DisplayTimedTextToPlayer(Player(viewer),0.,0.,25.,"Аварийных пересозданий: "+I2S(SasukeRebuildCount[p])+". -rebuildsasuke: полное восстановление.")
            call DisplayTimedTextToPlayer(Player(viewer),0.,0.,25.,"Заблокировано лечений трупа: "+I2S(SasukeCorpseHealsBlocked[p])+". Неудачных попыток возрождения: "+I2S(SasukeReviveFailures[p]))
            call DisplayTimedTextToPlayer(Player(viewer),0.,0.,25.,"Саске: этап "+I2S(CampaignStage)+", тип "+I2S(GetUnitTypeId(u))+", HP "+I2S(R2I(GetWidgetLife(u)))+", X/Y "+I2S(R2I(GetUnitX(u)))+"/"+I2S(R2I(GetUnitY(u)))+", предотвращено удалений "+I2S(SasukeBlockedRemove[p])+", неуязвимость "+I2S(GetUnitAbilityLevel(u,'Avul'))+". Последняя техника: "+SasukeLastSource[p])
            if IsUnitHidden(u) then
                call DisplayTimedTextToPlayer(Player(viewer),0.,0.,25.,"Состояние: скрыт триггером.")
            endif
            if IsUnitPaused(u) then
                call DisplayTimedTextToPlayer(Player(viewer),0.,0.,25.,"Состояние: управление заблокировано.")
            endif
            if IsUnitInvisible(u,Player(viewer)) then
                call DisplayTimedTextToPlayer(Player(viewer),0.,0.,25.,"Состояние: невидимость.")
            endif
        endif
        set p=p+1
    endloop
    set u=null
endfunction
// Critical recovery runs in a separate thread before the large story/NPC loops.
function InvasionRecoverHero takes integer p returns nothing
    local unit u=Hero[p]
    if not FoundationAlive(u) then
        set u=null
        return
    endif
    call ShowUnit(u,true)
    call SetUnitInvulnerable(u,false)
    call UnitRemoveAbility(u,'Avul')
    call PauseUnit(u,false)
    call SetUnitPathing(u,true)
    call SetUnitFlyHeight(u,0.,0.)
    call SetUnitTimeScale(u,1.)
    call SetUnitVertexColor(u,255,255,255,255)
    call SetUnitAnimation(u,"stand")
    if (GetUnitX(u)<CampaignMinX[12] or GetUnitX(u)>CampaignMaxX[12] or GetUnitY(u)<CampaignMinY[12] or GetUnitY(u)>CampaignMaxY[12]) and SasukeSafeReady[p] then
        call SetUnitPosition(u,SasukeSafeX[p],SasukeSafeY[p])
    endif
    set SasukeOutsideSince[p]=0.
    set SasukeHiddenSince[p]=0.
    set SasukePauseSince[p]=0.
    set SasukeAlphaSince[p]=0.
    set u=null
endfunction
function InvasionFixSasuke takes integer viewer returns nothing
    local integer p=0
    local integer k=0
    local boolean locked=false
    local unit u=null
    if CampaignStage!=12 or CampaignTransition or CampaignFinished then
        call DisplayTimedTextToPlayer(Player(viewer),0.,0.,10.,"Восстановление Саске доступно во время активного нападения на Коноху.")
        return
    endif
    loop
        exitwhen p>=12
        if HeroRole[p]==1 and Hero[p]!=null then
            set u=Hero[p]
            if FoundationAlive(u) then
                set k=0
                loop
                    exitwhen k>=12
                    if Lotus35Target[k]==u and Lotus35Caster[k]!=null then
                        set locked=true
                    endif
                    set k=k+1
                endloop
                if locked then
                    call DisplayTimedTextToPlayer(Player(viewer),0.,0.,10.,"Саске участвует в действующей технике. Повторите команду после её завершения.")
                    set u=null
                    return
                endif
                call CommonLogClear(p)
                call UnitRemoveAbility(u,'Apiv')
                call ShowUnit(u,false)
                call UnitRemoveAbility(u,'Aloc')
                call ShowUnit(u,true)
                call SetUnitInvulnerable(u,false)
                call UnitRemoveAbility(u,'Avul')
                call SetUnitScale(u,.8,.8,.8)
                call AddUnitAnimationProperties(u,"alternate",false)
                call InvasionRecoverHero(p)
                call IssueImmediateOrder(u,"stop")
                call DisplayTimedTextToPlayer(Player(viewer),0.,0.,12.,"Саске восстановлен: видимость, управление и уязвимость возвращены. Уровень и предметы сохранены.")
            elseif IsUnitType(u,UNIT_TYPE_DEAD) then
                call InvasionQueueCorpse(p)
                if FoundationAlive(u) then
                    call DisplayTimedTextToPlayer(Player(viewer),0.,0.,12.,"Саске штатно возрождён; видимость и управление восстановлены.")
                else
                    call DisplayTimedTextToPlayer(Player(viewer),0.,0.,12.,"Саске находится в состоянии смерти движка. Назначено штатное возрождение: "+I2S(R2I(RMaxBJ(0.,StoryRevive[p]-TimeNow)))+" сек. Сброс прозрачности не воскрешает героя.")
                endif
            else
                call DisplayTimedTextToPlayer(Player(viewer),0.,0.,12.,"Саске погиб или его юнит удалён. Команда не воскрешает погибших; используйте -sasuke для проверки состояния.")
            endif
        endif
        set p=p+1
    endloop
    set u=null
endfunction
function InvasionSourceColor takes unit u, real r, real g, real b, real transparency returns nothing
    local integer p=GetPlayerId(GetOwningPlayer(u))
    call SetUnitVertexColorBJ(u,r,g,b,transparency)
    if p<12 and u==Hero[p] and HeroRole[p]==1 and CampaignStage==12 then
        if transparency>=99.9 then
            if SasukeAlphaSince[p]==0. then
                set SasukeAlphaSince[p]=TimeNow
            endif
        else
            set SasukeAlphaSince[p]=0.
        endif
    endif
endfunction
function InvasionHeroVisibility takes nothing returns nothing
    local integer p=0
    local integer k=0
    local real busy=0.
    local boolean locked=false
    local unit u=null
    loop
        exitwhen p>=12
        set u=Hero[p]
        if CampaignStage==12 and not CampaignTransition and HeroRole[p]==1 and u!=null and IsUnitType(u,UNIT_TYPE_DEAD) then
            call InvasionQueueCorpse(p)
        endif
        if CampaignStage==12 and not CampaignTransition and HeroRole[p]==1 and FoundationAlive(u) then
            if SasukeLastType[p]!=0 and GetUnitTypeId(u)!=SasukeLastType[p] and (GetUnitTypeId(u)=='R001' or GetUnitTypeId(u)=='Rsfm') then
                set SasukeMorphRepairAt[p]=TimeNow+1.5
            endif
            set SasukeLastType[p]=GetUnitTypeId(u)
            set busy=0.
            if NPCCooldowns!=null then
                set busy=LoadReal(NPCCooldowns,GetHandleId(u),0)
            endif
            set locked=false
            set k=0
            loop
                exitwhen k>=12
                if Lotus35Target[k]==u and Lotus35Caster[k]!=null then
                    set locked=true
                endif
                set k=k+1
            endloop
            if SasukeMorphRepairAt[p]>0. and TimeNow>=SasukeMorphRepairAt[p] and not locked and TimeNow>=busy and not IsUnitPaused(u) then
                // Both imported Sasuke models have no Alternate sequences. Native AEme
                // can retain that tag/visibility flags when Wind Walk overlaps the return.
                call CommonLogClear(p)
                call AddUnitAnimationProperties(u,"alternate",false)
                call SetUnitInvulnerable(u,false)
                call UnitRemoveAbility(u,'Avul')
                call ShowUnit(u,true)
                call SetUnitVertexColor(u,255,255,255,255)
                call SetUnitTimeScale(u,1.)
                call SetUnitAnimation(u,"stand")
                set SasukeMorphRepairAt[p]=0.
            endif
            if IsUnitHidden(u) then
                if SasukeHiddenSince[p]==0. then
                    set SasukeHiddenSince[p]=TimeNow
                endif
            else
                set SasukeHiddenSince[p]=0.
            endif
            if IsUnitPaused(u) then
                if SasukePauseSince[p]==0. then
                    set SasukePauseSince[p]=TimeNow
                endif
            else
                set SasukePauseSince[p]=0.
            endif
            if SasukeSafeReady[p] and (GetUnitX(u)<CampaignMinX[12] or GetUnitX(u)>CampaignMaxX[12] or GetUnitY(u)<CampaignMinY[12] or GetUnitY(u)>CampaignMaxY[12]) then
                if SasukeOutsideSince[p]==0. then
                    set SasukeOutsideSince[p]=TimeNow
                endif
            else
                set SasukeOutsideSince[p]=0.
            endif
            if not locked and TimeNow>=busy and ((SasukeOutsideSince[p]>0. and TimeNow>=SasukeOutsideSince[p]+3.) or (SasukeHiddenSince[p]>0. and TimeNow>=SasukeHiddenSince[p]+10.) or (SasukeAlphaSince[p]>0. and TimeNow>=SasukeAlphaSince[p]+10.) or (SasukePauseSince[p]>0. and TimeNow>=SasukePauseSince[p]+15.)) then
                call InvasionRecoverHero(p)
            endif
            if not IsUnitHidden(u) and not IsUnitPaused(u) and GetUnitX(u)>=CampaignMinX[12] and GetUnitX(u)<=CampaignMaxX[12] and GetUnitY(u)>=CampaignMinY[12] and GetUnitY(u)<=CampaignMaxY[12] then
                set SasukeSafeX[p]=GetUnitX(u)
                set SasukeSafeY[p]=GetUnitY(u)
                set SasukeSafeReady[p]=true
            endif
        else
            set SasukeHiddenSince[p]=0.
            set SasukePauseSince[p]=0.
            set SasukeAlphaSince[p]=0.
            set SasukeOutsideSince[p]=0.
            set SasukeLastType[p]=0
            set SasukeMorphRepairAt[p]=0.
            set SasukeSafeReady[p]=false
        endif
        set p=p+1
    endloop
    set u=null
endfunction
