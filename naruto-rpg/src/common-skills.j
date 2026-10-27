function Control50Tick takes nothing returns nothing
    local integer p=0
    loop
        exitwhen p>=12
        if (CampaignStage!=12 and CampaignStage!=31) or CampaignTransition or Control50Unit[p]!=Hero[p] or not FoundationAlive(Hero[p]) then
            set Control50Until[p]=0.
        elseif Control50Until[p]>0. and TimeNow>=Control50Until[p] then
            set Control50Until[p]=0.
            if IsUnitPaused(Hero[p]) then
                call PauseUnit(Hero[p],false)
                call SetUnitTimeScale(Hero[p],1.)
                call SetUnitPathing(Hero[p],true)
                call ShowUnit(Hero[p],true)
                call SetUnitAnimation(Hero[p],"stand")
            endif
        endif
        set p=p+1
    endloop
endfunction
function Experience49Init takes nothing returns nothing
    local integer p=0
    if Experience49Applied then
        return
    endif
    set Experience49Applied=true
    loop
        exitwhen p>=12
        call SetPlayerHandicapXP(Player(p),GetPlayerHandicapXP(Player(p))*1.7)
        set p=p+1
    endloop
endfunction
function Gates49Init takes nothing returns nothing
    local integer n=0
    local destructable wall=null
    if Gates49Built then
        return
    endif
    set Gates49Built=true
    loop
        exitwhen n>=7
        set wall=CreateDestructable('LTba',15712.+I2R(n)*64.,-12800.,0.,1.,0)
        call SetDestructableInvulnerable(wall,true)
        set n=n+1
    endloop
    set wall=null
endfunction
function CommonLogOwnerView takes integer p returns nothing
    if (CampaignStage==9 or CampaignStage==11) and Hero[p]!=null and not IsUnitHidden(Hero[p]) and GetLocalPlayer()==Player(p) then
        // Local color only: native Wind Walk and enemy detection remain unchanged.
        call SetUnitVertexColor(Hero[p],255,255,255,255)
    endif
endfunction
function CommonLogActorClear takes integer p returns nothing
    if LogActor[p]!=null then
        call RemoveUnit(LogActor[p])
        set LogActor[p]=null
    endif
endfunction
function CommonLogClear takes integer p returns nothing
    call CommonLogActorClear(p)
    if Hero[p]!=null then
        call UnitRemoveAbility(Hero[p],'BOwk')
    endif
    set LogUntil[p]=0.
endfunction
function CommonLogEffect takes integer p returns nothing
    // Native Wind Walk may already be active at SPELL_EFFECT: keep the fresh buff.
    call CommonLogActorClear(p)
    set LogActor[p]=CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'rlgd',GetUnitX(Hero[p]),GetUnitY(Hero[p]),GetUnitFacing(Hero[p]))
    call SetUnitFlyHeight(LogActor[p],150.,0.)
    call SetUnitFlyHeight(LogActor[p],0.,1000.)
    set LogActorUntil[p]=TimeNow+1.5
    set LogUntil[p]=TimeNow+3.
    set LogReadyAt[p]=TimeNow+22.
    set LogBotNextAt[p]=TimeNow+45.
    call CommonLogOwnerView(p)
    call DestroyEffect(AddSpecialEffect("Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl",GetUnitX(Hero[p]),GetUnitY(Hero[p])))
endfunction
function CommonLogTick takes nothing returns nothing
    local integer p=0
    loop
        exitwhen p>=12
        if Hero[p]!=LogObservedHero[p] then
            set LogObservedHero[p]=Hero[p]
            set LogPreviousHP[p]=0.
            set LogLastDamageAt[p]=0.
        endif
        if FoundationAlive(Hero[p]) then
            if LogPreviousHP[p]>GetWidgetLife(Hero[p])+1. and not IsUnitPaused(Hero[p]) then
                set LogLastDamageAt[p]=TimeNow
            endif
            set LogPreviousHP[p]=GetWidgetLife(Hero[p])
            if TimeNow<LogUntil[p] then
                call CommonLogOwnerView(p)
            endif
        else
            set LogPreviousHP[p]=0.
            set LogLastDamageAt[p]=0.
        endif
        if LogActor[p]!=null and (TimeNow>=LogActorUntil[p] or not FoundationAlive(Hero[p])) then
            call RemoveUnit(LogActor[p])
            set LogActor[p]=null
        endif
        if not FoundationAlive(Hero[p]) or (LogUntil[p]>0. and TimeNow>=LogUntil[p]) or (LogUntil[p]<=0. and Hero[p]!=null and GetUnitAbilityLevel(Hero[p],'BOwk')>0) then
            call CommonLogClear(p)
        endif
        set p=p+1
    endloop
endfunction
function CommonLogBot takes integer p, unit enemy returns boolean
    local real dx=0.
    local real dy=0.
    local real length=0.
    local real x=0.
    local real y=0.
    local boolean arena=CampaignStage==9 or CampaignStage==11
    if TimeNow<LogUntil[p] then
        if arena then
            // Resume the duel: an attack naturally ends Wind Walk instead of fleeing.
            if FoundationAlive(enemy) then
                if GetUnitCurrentOrder(Hero[p])!=OrderId("attack") then
                    call IssueTargetOrder(Hero[p],"attack",enemy)
                endif
                return true
            endif
            return false
        endif
        // Do not break native Wind Walk immediately with an attack or another spell.
        if FoundationAlive(enemy) then
            set dx=GetUnitX(Hero[p])-GetUnitX(enemy)
            set dy=GetUnitY(Hero[p])-GetUnitY(enemy)
            set length=SquareRoot(dx*dx+dy*dy)
            if length>1. then
                set x=GetUnitX(Hero[p])+dx/length*400.
                set y=GetUnitY(Hero[p])+dy/length*400.
                if TreeJumpInside(p,x,y) and not IsTerrainPathable(x,y,PATHING_TYPE_WALKABILITY) then
                    call IssuePointOrder(Hero[p],"move",x,y)
                endif
            endif
        endif
        return true
    endif
    if not FoundationAlive(Hero[p]) or not FoundationAlive(enemy) or TimeNow<LogReadyAt[p] or TimeNow<LogBotNextAt[p] or TimeNow<VisualChannelUntil[p] or ComboLeft[p]>0 or GetUnitAbilityLevel(Hero[p],'Rlog')==0 then
        return false
    endif
    if arena and (LogArenaUsed[p] or GetWidgetLife(Hero[p])>=GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.2) then
        return false
    endif
    if LogLastDamageAt[p]<=0. or TimeNow-LogLastDamageAt[p]>2.5 or GetWidgetLife(Hero[p])>=GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.25 then
        return false
    endif
    // Finish a weaker enemy rather than abandoning a winnable fight.
    if GetWidgetLife(Hero[p])>=GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.12 and GetWidgetLife(enemy)/GetUnitState(enemy,UNIT_STATE_MAX_LIFE)<=GetWidgetLife(Hero[p])/GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)+.15 then
        return false
    endif
    set dx=GetUnitX(Hero[p])-GetUnitX(enemy)
    set dy=GetUnitY(Hero[p])-GetUnitY(enemy)
    if dx*dx+dy*dy<=450.*450. and GetWidgetLife(Hero[p])<GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.25 and GetUnitState(Hero[p],UNIT_STATE_MANA)>=150. then
        if IssueImmediateOrder(Hero[p],"windwalk") then
            if arena then
                set LogArenaUsed[p]=true
            endif
            set BotNextCast[p]=TimeNow+.75
            return true
        endif
    endif
    return false
endfunction

// INVASION26_RECOVERY
