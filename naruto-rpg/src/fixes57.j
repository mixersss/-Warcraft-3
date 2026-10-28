// Run a whole scene on its own Classic JASS budget; publish readiness only after successful setup.
function Scene57Build takes nothing returns nothing
    call CampaignSpawnStage()
    if CampaignStage==12 and CampaignActorType[0]==0 and FoundationAlive(CampaignActor[0]) then
        set Village57Ready=true
    endif
endfunction
function Companion57Player takes nothing returns nothing
    local integer p=Pet57Player
    local integer t=StoryTeam(p)
    local integer k=0
    local integer slot=0
    local integer rank=0
    local unit pet=null
    local unit target=null
    local real dx=0.
    local real dy=0.
    if Hero[p]==null or (HeroRole[p]!=7 and HeroRole[p]!=10) then
        return
    endif
    call RosterSyncPets(p)
    if GetPlayerController(Player(p))!=MAP_CONTROL_COMPUTER or not FoundationAlive(Hero[p]) or IsUnitPaused(Hero[p]) or IsUnitHidden(Hero[p]) or CampaignTransition or CampaignPermanentDead[p] or TimeNow<Pet57OrderAt[p] then
        return
    endif
    set Pet57OrderAt[p]=TimeNow+1.
    if StoryStage[t]>=9 then
        set target=CampaignNearest(p)
    elseif StoryStage[t]==7 then
        set target=ExamNearest(p)
    else
        set target=StoryNearest(t,Hero[p])
    endif
    loop
        exitwhen k>=3
        set slot=p*3+k
        set pet=Companion[slot]
        if FoundationAlive(pet) and not IsUnitPaused(pet) and PetTrapVictim[slot]==null then
            set dx=GetUnitX(pet)-GetUnitX(Hero[p])
            set dy=GetUnitY(pet)-GetUnitY(Hero[p])
            if StoryRetreat[t] or dx*dx+dy*dy>900.*900. or not FoundationAlive(target) then
                if Pet57Target[slot]!=Hero[p] or dx*dx+dy*dy>250.*250. then
                    call IssueTargetOrder(pet,"follow",Hero[p])
                    set Pet57Target[slot]=Hero[p]
                endif
            elseif IsUnitEnemy(target,Player(p)) and SkillsCanSeePet(target,Player(p)) then
                if Pet57Target[slot]!=target or GetUnitCurrentOrder(pet)==0 then
                    call IssueTargetOrder(pet,"attack",target)
                    set Pet57Target[slot]=target
                endif
            endif
        endif
        set k=k+1
    endloop
    // Missing permanent companions are summoned even while no enemy is nearby.
    // Respect learned ranks, real mana, native cooldowns, channeling and existing companions.
    if TimeNow>=BotNextCast[p] and TimeNow>=VisualChannelUntil[p] and JumpUnit[p]==null and JumpQueued[p]==null then
        if HeroRole[p]==7 and not FoundationAlive(Companion[p*3]) and GetUnitAbilityLevel(Hero[p],'R701')>0 and GetUnitState(Hero[p],UNIT_STATE_MANA)>=90. then
            if IssueImmediateOrder(Hero[p],"acidbomb") then
                set BotNextCast[p]=TimeNow+2.
            endif
        elseif HeroRole[p]==10 then
            if not FoundationAlive(Companion[p*3]) and GetUnitAbilityLevel(Hero[p],'RA01')>0 and GetUnitState(Hero[p],UNIT_STATE_MANA)>=90. then
                if IssueImmediateOrder(Hero[p],"acidbomb") then
                    set BotNextCast[p]=TimeNow+2.
                endif
            elseif not FoundationAlive(Companion[p*3+1]) and GetUnitAbilityLevel(Hero[p],'RA03')>0 and GetUnitState(Hero[p],UNIT_STATE_MANA)>=120. then
                if IssueImmediateOrder(Hero[p],"cripple") then
                    set BotNextCast[p]=TimeNow+2.
                endif
            elseif not FoundationAlive(Companion[p*3+2]) and GetUnitAbilityLevel(Hero[p],'RA04')>0 and GetUnitState(Hero[p],UNIT_STATE_MANA)>=400. then
                if IssuePointOrder(Hero[p],"inferno",GetUnitX(Hero[p])+96.,GetUnitY(Hero[p])) then
                    set BotNextCast[p]=TimeNow+2.
                endif
            endif
        endif
    endif
    set pet=null
    set target=null
endfunction
function Companion57Tick takes nothing returns nothing
    local integer p=0
    loop
        exitwhen p>=12
        set Pet57Player=p
        call ExecuteFunc("Companion57Player")
        set p=p+1
    endloop
endfunction
