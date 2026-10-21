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
    call DestroyEffect(AddSpecialEffect("Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl",GetUnitX(Hero[p]),GetUnitY(Hero[p])))
endfunction
function CommonLogTick takes nothing returns nothing
    local integer p=0
    loop
        exitwhen p>=12
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
    if not FoundationAlive(Hero[p]) or not FoundationAlive(enemy) or TimeNow<LogReadyAt[p] or TimeNow<VisualChannelUntil[p] or ComboLeft[p]>0 or GetUnitAbilityLevel(Hero[p],'Rlog')==0 then
        return false
    endif
    if arena and (LogArenaUsed[p] or GetWidgetLife(Hero[p])>=GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.2) then
        return false
    endif
    set dx=GetUnitX(Hero[p])-GetUnitX(enemy)
    set dy=GetUnitY(Hero[p])-GetUnitY(enemy)
    if dx*dx+dy*dy<=650.*650. and GetWidgetLife(Hero[p])<GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.45 and GetUnitState(Hero[p],UNIT_STATE_MANA)>=150. then
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
