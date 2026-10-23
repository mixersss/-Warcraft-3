// Cast-local3.5 techniques. No sleeping callbacks or shared actor/location globals.
function Source35Valid takes integer p, unit u returns boolean
    return FoundationAlive(u) and not IsUnitType(u,UNIT_TYPE_STRUCTURE) and IsUnitEnemy(u,Player(p))
endfunction
function Source35LotusEnd takes integer p, boolean finish returns nothing
    local unit u=Lotus35Caster[p]
    local unit t=Lotus35Target[p]
    if finish and FoundationAlive(u) and Source35Valid(p,t) then
        call UnitDamageTarget(u,t,300.,false,false,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL,WEAPON_TYPE_WHOKNOWS)
        call FoundationSound(SkillAudio[15])
        call DestroyEffect(AddSpecialEffect("Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl",GetUnitX(t),GetUnitY(t)))
    endif
    if u!=null then
        call ShowUnit(u,true)
        call PauseUnit(u,false)
        call SetUnitPathing(u,true)
        call SetUnitFlyHeight(u,0.,0.)
        call SetUnitTimeScale(u,1.)
        call SetUnitAnimation(u,"stand")
    endif
    if t!=null then
        call ShowUnit(t,true)
        call PauseUnit(t,false)
        call SetUnitPathing(t,true)
        call SetUnitFlyHeight(t,0.,0.)
        call SetUnitTimeScale(t,1.)
    endif
    set Lotus35Caster[p]=null
    set Lotus35Target[p]=null
    set Lotus35Hits[p]=0
    set VisualChannelUntil[p]=0.
    if Lotus35Art[p]!=null then
        call DestroyEffect(Lotus35Art[p])
        set Lotus35Art[p]=null
    endif
    set u=null
    set t=null
endfunction
function Source35WireAdd takes integer p, unit target returns nothing
    local integer n=Source35WireCursor
    if Source35Wire[n]!=null then
        call DestroyLightning(Source35Wire[n])
    endif
    set Source35Wire[n]=AddLightningEx("LEAS",true,GetUnitX(Hero[p]),GetUnitY(Hero[p]),60.,GetUnitX(target),GetUnitY(target),60.)
    call SetLightningColor(Source35Wire[n],1.,.5,0.,1.)
    set Source35WireUntil[n]=TimeNow+.75
    set Source35WireOwner[n]=p
    set Source35WireCursor=ModuloInteger(n+1,64)
endfunction
function Source35ChokeEnd takes integer p, boolean stop returns nothing
    local unit caster=Choke35Caster[p]
    if Choke35Helper[p]!=null then
        call RemoveUnit(Choke35Helper[p])
    endif
    set Choke35Helper[p]=null
    set Choke35Caster[p]=null
    set Choke35Target[p]=null
    set Choke35Until[p]=0.
    if caster!=null then
        call RosterClearShadow(p)
        set VisualChannelUntil[p]=0.
        call SetUnitTimeScale(caster,1.)
        if stop and FoundationAlive(caster) then
            call IssueImmediateOrder(caster,"stop")
        endif
    endif
    set caster=null
endfunction
function Source35Clear takes integer p returns nothing
    local integer wire=0
    local unit holder=Source35Hero[p]
    local unit mine=null
    call Source35LotusEnd(p,false)
    call Source35ChokeEnd(p,true)
    if holder!=null then
        if Gate35Agility[p]!=0 or Drunk35Agility[p]!=0 then
            call SetHeroAgi(holder,GetHeroAgi(holder,false)-Gate35Agility[p]-Drunk35Agility[p],true)
        endif
        if Gate35Until[p]>0. then
            call SetUnitMoveSpeed(holder,Gate35Speed[p])
            call SetUnitVertexColor(holder,255,255,255,255)
            call SetUnitTimeScale(holder,1.)
        endif
    endif
    set Gate35Agility[p]=0
    set Gate35Until[p]=0.
    set Drunk35Agility[p]=0
    set Drunk35Left[p]=0
    set Clone35At[p]=0.
    if Barrage35Shots[p]!=null then
        call GroupClear(Barrage35Shots[p])
        call GroupClear(Barrage35Mines[p])
    endif
    set Barrage35At[p]=0.
    if Source35MineUnits[p]!=null then
        loop
            set mine=FirstOfGroup(Source35MineUnits[p])
            exitwhen mine==null
            call GroupRemoveUnit(Source35MineUnits[p],mine)
            call RemoveUnit(mine)
        endloop
    endif
    loop
        exitwhen wire>=64
        if Source35Wire[wire]!=null and Source35WireOwner[wire]==p then
            call DestroyLightning(Source35Wire[wire])
            set Source35Wire[wire]=null
        endif
        set wire=wire+1
    endloop
    set Source35Hero[p]=null
    set holder=null
    set mine=null
endfunction
function Source35Dummy takes integer p, integer raw, integer rank, real x, real y returns unit
    local unit u=CreateUnit(Player(p),'rdst',x,y,0.)
    call UnitAddAbility(u,raw)
    call SetUnitAbilityLevel(u,raw,rank)
    call UnitApplyTimedLife(u,'BTLF',3.)
    set Source35Return=u
    set u=null
    return Source35Return
endfunction
function Source35ShadowGroup takes integer p, unit main returns nothing
    local unit t=null
    local unit helper=null
    call GroupEnumUnitsInRange(SkillScratch,GetUnitX(Hero[p]),GetUnitY(Hero[p]),550.,null)
    loop
        set t=FirstOfGroup(SkillScratch)
        exitwhen t==null
        call GroupRemoveUnit(SkillScratch,t)
        if t!=main and Source35Valid(p,t) and not IsUnitType(t,UNIT_TYPE_MAGIC_IMMUNE) then
            set helper=Source35Dummy(p,'R35s',1,GetUnitX(Hero[p]),GetUnitY(Hero[p]))
            call UnitApplyTimedLife(helper,'BTLF',10.)
            call IssueTargetOrder(helper,"magicleash",t)
        endif
    endloop
    set t=null
    set helper=null
endfunction
function Source35Apply takes integer p, integer index, integer rank, unit target returns nothing
    local integer j=0
    local integer amount=0
    local real radius=300.
    local real loss=1.2
    local unit u=Hero[p]
    local unit helper=null
    if index==1 then
        set Clone35Rank[p]=rank
        set Clone35At[p]=TimeNow+.1
        set Clone35Retry[p]=TimeNow+1.1
    elseif index==15 and Source35Valid(p,target) and not IsUnitPaused(target) then
        call Source35LotusEnd(p,false)
        set Lotus35Caster[p]=u
        set Lotus35Target[p]=target
        set Lotus35Hits[p]=4
        set Lotus35Damage[p]=150.
        if rank==2 then
            set Lotus35Hits[p]=8
            set Lotus35Damage[p]=100.
        elseif rank==3 then
            set Lotus35Hits[p]=16
            set Lotus35Damage[p]=75.
        endif
        set Lotus35Next[p]=TimeNow+.25
        set Lotus35Art[p]=AddSpecialEffectTarget("Abilities\\Spells\\Undead\\DarkSummoning\\DarkSummonMissile.mdl",u,"chest")
        call UnitAddAbility(u,'Amrf')
        call UnitRemoveAbility(u,'Amrf')
        call UnitAddAbility(target,'Amrf')
        call UnitRemoveAbility(target,'Amrf')
        call PauseUnit(u,true)
        call PauseUnit(target,true)
        call SetUnitPathing(u,false)
        call SetUnitPathing(target,false)
        call SetUnitFlyHeight(u,500.,2000.)
        call SetUnitFlyHeight(target,500.,2000.)
        set BotNextCast[p]=TimeNow+10.
    elseif index==16 and Source35Valid(p,target) then
        if not IsTerrainPathable(GetUnitX(target),GetUnitY(target),PATHING_TYPE_WALKABILITY) then
            call SetUnitPosition(u,GetUnitX(target)-80.,GetUnitY(target))
        endif
        call SetUnitAnimationByIndex(u,3)
    elseif index==17 then
        set Source35Hero[p]=u
        if Drunk35Agility[p]!=0 then
            call SetHeroAgi(u,GetHeroAgi(u,false)-Drunk35Agility[p],true)
        endif
        set Drunk35Agility[p]=0
        set Drunk35Rank[p]=rank
        set Drunk35Left[p]=8
        set Drunk35Next[p]=TimeNow
        call SetUnitAnimationByIndex(u,9)
    elseif index==18 then
        set Source35Hero[p]=u
        if Gate35Agility[p]!=0 then
            call SetHeroAgi(u,GetHeroAgi(u,false)-Gate35Agility[p],true)
        else
            set Gate35Speed[p]=GetUnitMoveSpeed(u)
        endif
        set amount=50
        if rank==2 then
            set amount=100
            set loss=1.35
        elseif rank==3 then
            set amount=200
            set loss=1.5
        endif
        set Gate35Agility[p]=amount
        set Gate35Until[p]=TimeNow+17.
        call SetHeroAgi(u,GetHeroAgi(u,false)+amount,true)
        call SetUnitState(u,UNIT_STATE_LIFE,RMaxBJ(1.,GetWidgetLife(u)/loss))
        call SetUnitMoveSpeed(u,5000.)
        call SetUnitVertexColor(u,255,64,64,255)
        call SetUnitAnimationByIndex(u,9)
        call DestroyEffect(AddSpecialEffect("Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl",GetUnitX(u),GetUnitY(u)))
    elseif index==30 and Source35Valid(p,target) then
        call RosterShadow(p,rank,target)
        if rank==4 then
            call Source35ShadowGroup(p,target)
        endif
    elseif index==32 then
        if rank==1 then
            set radius=150.
        endif
        call GroupClear(Barrage35Shots[p])
        call GroupClear(Barrage35Mines[p])
        call GroupEnumUnitsInRange(Barrage35Shots[p],GetSpellTargetX(),GetSpellTargetY(),radius,null)
        set Barrage35Rank[p]=rank
        set Barrage35At[p]=TimeNow+.75
    elseif index==33 and Source35Valid(p,target) then
        call Source35ChokeEnd(p,false)
        set Choke35Caster[p]=u
        set Choke35Target[p]=target
        set Choke35Until[p]=TimeNow+3.+rank
        if not IsUnitType(target,UNIT_TYPE_HERO) then
            set Choke35Until[p]=TimeNow+3.+2.*rank
        endif
        set helper=Source35Dummy(p,'R35c',rank,GetUnitX(u),GetUnitY(u))
        call UnitApplyTimedLife(helper,'BTLF',10.)
        call IssueTargetOrder(helper,"magicleash",target)
        set Choke35Helper[p]=helper
        set VisualChannelIndex[p]=33
        set VisualChannelUntil[p]=Choke35Until[p]
        set BotNextCast[p]=Choke35Until[p]+.25
        call RosterShadow(p,rank,target)
        set ShadowDuration[p]=3.+rank
        if not IsUnitType(target,UNIT_TYPE_HERO) then
            set ShadowDuration[p]=3.+2.*rank
        endif
        set ShadowUntil[p]=TimeNow+ShadowDuration[p]
        call DestroyEffect(AddSpecialEffectTarget("Abilities\\Spells\\Undead\\DeathCoil\\DeathCoilSpecialArt.mdl",target,"chest"))
    endif
    set helper=null
    set u=null
endfunction
function Source35PruneMine takes nothing returns nothing
    local unit u=GetEnumUnit()
    if not FoundationAlive(u) then
        call GroupRemoveUnit(Source35MineUnits[Source35Player],u)
        call RemoveUnit(u)
    endif
    set u=null
endfunction
function Source35TickPlayer takes nothing returns nothing
    local integer p=Source35Player
    local integer j=0
    local integer amount=0
    local integer roll=0
    local unit u=Hero[p]
    local unit t=null
    local unit helper=null
    if not FoundationAlive(u) or (Source35Hero[p]!=null and Source35Hero[p]!=u) or (Lotus35Caster[p]!=null and Lotus35Caster[p]!=u) then
        call Source35Clear(p)
        set u=null
        return
    endif
    if Choke35Caster[p]!=null and (Choke35Caster[p]!=u or not Source35Valid(p,Choke35Target[p]) or TimeNow>=Choke35Until[p]) then
        call Source35ChokeEnd(p,true)
    endif
    if TimeNow>=Source35MineCheck[p] then
        set Source35MineCheck[p]=TimeNow+5.
        call ForGroup(Source35MineUnits[p],function Source35PruneMine)
    endif
    if Gate35Until[p]>0. and TimeNow>=Gate35Until[p] then
        call SetHeroAgi(u,GetHeroAgi(u,false)-Gate35Agility[p],true)
        call SetUnitMoveSpeed(u,Gate35Speed[p])
        call SetUnitVertexColor(u,255,255,255,255)
        call SetUnitTimeScale(u,1.)
        set Gate35Agility[p]=0
        set Gate35Until[p]=0.
    endif
    if Drunk35Left[p]>0 and TimeNow>=Drunk35Next[p] then
        set amount=10
        if Drunk35Rank[p]==2 then
            set amount=20
        elseif Drunk35Rank[p]==3 then
            set amount=40
        endif
        if Drunk35Rank[p]==1 and Drunk35Left[p]==4 then
            set roll=GetRandomInt(0,5)
        else
            set roll=GetRandomInt(-amount/2,amount)
        endif
        call SetHeroAgi(u,GetHeroAgi(u,false)+roll,true)
        set Drunk35Agility[p]=Drunk35Agility[p]+roll
        set Drunk35Left[p]=Drunk35Left[p]-1
        set Drunk35Next[p]=TimeNow+1.
    elseif Drunk35Left[p]==0 and Drunk35Agility[p]!=0 and TimeNow>=Drunk35Next[p] then
        call SetHeroAgi(u,GetHeroAgi(u,false)-Drunk35Agility[p],true)
        set Drunk35Agility[p]=0
    endif
    if Lotus35Caster[p]!=null then
        set t=Lotus35Target[p]
        if not Source35Valid(p,t) then
            call Source35LotusEnd(p,false)
        elseif TimeNow>=Lotus35Next[p] then
            if Lotus35Hits[p]>0 then
                call SetUnitAnimationByIndex(u,3)
                call DestroyEffect(AddSpecialEffectTarget("Abilities\\Spells\\Human\\FlakCannons\\FlakTarget.mdl",t,"chest"))
                call UnitDamageTarget(u,t,Lotus35Damage[p],false,false,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL,WEAPON_TYPE_WHOKNOWS)
                set Lotus35Hits[p]=Lotus35Hits[p]-1
                set Lotus35Next[p]=TimeNow+.5
            else
                call SetUnitAnimationByIndex(u,12)
                call Source35LotusEnd(p,true)
            endif
        endif
    endif
    if Clone35At[p]>0. and TimeNow>=Clone35At[p] then
        call GroupEnumUnitsInRange(SkillScratch,GetUnitX(u),GetUnitY(u),700.,null)
        set j=0
        set amount=Clone35Rank[p]-1
        if amount==3 then
            set amount=4
        endif
        loop
            set t=FirstOfGroup(SkillScratch)
            exitwhen t==null or j>=8
            call GroupRemoveUnit(SkillScratch,t)
            if GetOwningPlayer(t)==Player(p) and IsUnitIllusion(t) and FoundationAlive(t) and (GetUnitTypeId(t)=='R000' or GetUnitTypeId(t)=='Rnfm') then
                set roll=0
                loop
                    exitwhen roll>=amount
                    set helper=Source35Dummy(p,'R35i',Clone35Rank[p],GetUnitX(u),GetUnitY(u))
                    call IssueTargetOrderById(helper,0xD0132,t)
                    set roll=roll+1
                endloop
                set j=j+1
            endif
        endloop
        call GroupClear(SkillScratch)
        if j>0 or TimeNow>=Clone35Retry[p] then
            set Clone35At[p]=0.
        endif
    endif
    set j=0
    loop
        set t=FirstOfGroup(Barrage35Shots[p])
        exitwhen t==null or j>=12
        call GroupRemoveUnit(Barrage35Shots[p],t)
        if Source35Valid(p,t) and not IsUnitType(t,UNIT_TYPE_MAGIC_IMMUNE) then
            set helper=Source35Dummy(p,'R35k',1,GetUnitX(u),GetUnitY(u))
            call IssueTargetOrder(helper,"thunderbolt",t)
            call Source35WireAdd(p,t)
            call GroupAddUnit(Barrage35Mines[p],t)
            set Barrage35At[p]=TimeNow+.75
        endif
        set j=j+1
    endloop
    if FirstOfGroup(Barrage35Shots[p])==null and Barrage35At[p]>0. and TimeNow>=Barrage35At[p] then
        set j=0
        loop
            set t=FirstOfGroup(Barrage35Mines[p])
            exitwhen t==null or j>=12
            call GroupRemoveUnit(Barrage35Mines[p],t)
            if Source35Valid(p,t) then
                set helper=CreateUnit(Player(p),'nglm',GetUnitX(t),GetUnitY(t),0.)
                call GroupAddUnit(Source35MineUnits[p],helper)
                if Barrage35Rank[p]==3 then
                    set helper=CreateUnit(Player(p),'nglm',GetUnitX(t)+16.,GetUnitY(t),0.)
                    call GroupAddUnit(Source35MineUnits[p],helper)
                endif
            endif
            set j=j+1
        endloop
        if FirstOfGroup(Barrage35Mines[p])==null then
            set Barrage35At[p]=0.
        endif
    endif
    set helper=null
    set u=null
    set t=null
endfunction
function Source35Tick takes nothing returns nothing
    local integer p=0
    local integer wire=0
    loop
        exitwhen wire>=64
        if Source35Wire[wire]!=null and TimeNow>=Source35WireUntil[wire] then
            call DestroyLightning(Source35Wire[wire])
            set Source35Wire[wire]=null
        endif
        set wire=wire+1
    endloop
    loop
        exitwhen p>=12
        if Choke35Caster[p]!=null or Lotus35Caster[p]!=null or Gate35Until[p]>0. or Drunk35Left[p]>0 or Drunk35Agility[p]!=0 or Clone35At[p]>0. or Barrage35At[p]>0. or FirstOfGroup(Source35MineUnits[p])!=null then
            set Source35Player=p
            call ExecuteFunc("Source35TickPlayer")
        endif
        set p=p+1
    endloop
endfunction
function Source35Init takes nothing returns nothing
    local integer p=0
    loop
        exitwhen p>=12
        set Source35MineUnits[p]=CreateGroup()
        set Barrage35Shots[p]=CreateGroup()
        set Barrage35Mines[p]=CreateGroup()
        set p=p+1
    endloop
endfunction
