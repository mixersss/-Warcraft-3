// Critical recovery runs in a separate thread before the large story/NPC loops.
function InvasionRecoverHero takes integer p returns nothing
    local unit u=Hero[p]
    if not FoundationAlive(u) then
        set u=null
        return
    endif
    call ShowUnit(u,true)
    call PauseUnit(u,false)
    call SetUnitPathing(u,true)
    call SetUnitFlyHeight(u,0.,0.)
    call SetUnitTimeScale(u,1.)
    call SetUnitVertexColor(u,255,255,255,255)
    call SetUnitAnimation(u,"stand")
    if (GetUnitX(u)<CampaignMinX[12] or GetUnitX(u)>CampaignMaxX[12] or GetUnitY(u)<CampaignMinY[12] or GetUnitY(u)>CampaignMaxY[12]) and SasukeSafeReady[p] then
        call SetUnitPosition(u,SasukeSafeX[p],SasukeSafeY[p])
    endif
    set SasukeHiddenSince[p]=0.
    set SasukePauseSince[p]=0.
    set SasukeAlphaSince[p]=0.
    set u=null
endfunction
function InvasionSourceColor takes unit u, real r, real g, real b, real transparency returns nothing
    local integer p=GetPlayerId(GetOwningPlayer(u))
    call SetUnitVertexColorBJ(u,r,g,b,transparency)
    if p<12 and u==Hero[p] and HeroRole[p]==1 and CampaignStage==12 then
        if transparency>=99.9 then
            set SasukeAlphaSince[p]=TimeNow
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
        if CampaignStage==12 and not CampaignTransition and HeroRole[p]==1 and FoundationAlive(u) then
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
            if not locked and TimeNow>=busy and ((SasukeHiddenSince[p]>0. and TimeNow>=SasukeHiddenSince[p]+10.) or (SasukeAlphaSince[p]>0. and TimeNow>=SasukeAlphaSince[p]+10.) or (SasukePauseSince[p]>0. and TimeNow>=SasukePauseSince[p]+15.)) then
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
            set SasukeSafeReady[p]=false
        endif
        set p=p+1
    endloop
    set u=null
endfunction
