// Explicit NPC-side attribution. Native hero-owned victim rewards remain unchanged.
// BOUNTY44_DATA
function Invasion44HeroOwner takes unit killer returns integer
    local integer p=0
    local integer n=0
    local integer raw=0
    if killer==null then
        return -1
    endif
    set p=GetPlayerId(GetOwningPlayer(killer))
    if p<0 or p>=12 or Hero[p]==null or GetPlayerSlotState(Player(p))!=PLAYER_SLOT_STATE_PLAYING then
        return -1
    endif
    if killer==Hero[p] or IsUnitIllusion(killer) or IsUnitType(killer,UNIT_TYPE_SUMMONED) then
        return p
    endif
    loop
        exitwhen n>=3
        if killer==Companion[p*3+n] then
            return p
        endif
        set n=n+1
    endloop
    set raw=GetUnitTypeId(killer)
    if raw=='rdst' or raw=='r40d' or raw=='r40w' or raw=='r40c' or raw=='r40b' then
        return p
    endif
    return -1
endfunction
function Invasion44Death takes nothing returns nothing
    local unit victim=GetTriggerUnit()
    local unit killer=GetKillingUnit()
    local integer owner=GetPlayerId(GetOwningPlayer(victim))
    local integer p=-1
    local integer raw=0
    local integer gold=0
    local integer dice=0
    local integer sides=0
    local integer n=0
    local texttag label=null
    if CampaignStage!=12 or CampaignTransition or CampaignFinished or not CampaignBountyActive or (owner!=13 and owner!=PLAYER_NEUTRAL_PASSIVE) or IsUnitIllusion(victim) then
        set victim=null
        set killer=null
        return
    endif
    set p=Invasion44HeroOwner(killer)
    if p>=0 and IsUnitEnemy(victim,Player(p)) then
        set raw=GetUnitTypeId(victim)
        set gold=LoadInteger(Invasion44Bounty,raw,0)
        set dice=LoadInteger(Invasion44Bounty,raw,1)
        set sides=LoadInteger(Invasion44Bounty,raw,2)
        // Match the original dice distribution, not a uniform min/max approximation.
        loop
            exitwhen n>=dice or sides<=0
            set gold=gold+GetRandomInt(1,sides)
            set n=n+1
        endloop
        if gold>0 then
            call SetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)+gold)
            set Invasion44Earned[p]=Invasion44Earned[p]+gold
            set Invasion44Kills[p]=Invasion44Kills[p]+1
            set label=CreateTextTag()
            if label!=null then
                call SetTextTagText(label,"+"+I2S(gold),.024)
                call SetTextTagPosUnit(label,victim,40.)
                call SetTextTagColor(label,255,215,0,255)
                call SetTextTagVelocity(label,0.,.03)
                call SetTextTagPermanent(label,false)
                call SetTextTagLifespan(label,2.)
                call SetTextTagFadepoint(label,1.)
                call SetTextTagVisibility(label,GetLocalPlayer()==Player(p))
            endif
        endif
    endif
    set label=null
    set victim=null
    set killer=null
endfunction
function Invasion44Inspect takes integer viewer returns nothing
    local integer p=0
    if CampaignStage!=12 then
        call DisplayTimedTextToPlayer(Player(viewer),0.,0.,10.,"Учёт наград доступен во время нападения на Коноху.")
        return
    endif
    call DisplayTimedTextToPlayer(Player(viewer),0.,0.,20.,"Золото за NPC: только добивания героями, их клонами, питомцами и техниками. Обычная армия не получает награды для героев.")
    loop
        exitwhen p>=12
        if Hero[p]!=null then
            call DisplayTimedTextToPlayer(Player(viewer),0.,0.,20.,I2S(p+1)+". "+GetUnitName(Hero[p])+": добиваний NPC "+I2S(Invasion44Kills[p])+", награда "+I2S(Invasion44Earned[p])+", сейчас золота "+I2S(GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)))
        endif
        set p=p+1
    endloop
endfunction
function Invasion44Init takes nothing returns nothing
    if Invasion44DeathHook!=null then
        return
    endif
    set Invasion44Bounty=InitHashtable()
    call Invasion44Load()
    set Invasion44DeathHook=CreateTrigger()
    call TriggerRegisterPlayerUnitEvent(Invasion44DeathHook,Player(13),EVENT_PLAYER_UNIT_DEATH,null)
    call TriggerRegisterPlayerUnitEvent(Invasion44DeathHook,Player(PLAYER_NEUTRAL_PASSIVE),EVENT_PLAYER_UNIT_DEATH,null)
    call TriggerAddAction(Invasion44DeathHook,function Invasion44Death)
endfunction
