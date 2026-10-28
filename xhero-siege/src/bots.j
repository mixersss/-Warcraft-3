// Classic 1.26 scripted allies. Never control human heroes or enemy scenario slots.
function XHAlive takes unit u returns boolean
    return u!=null and GetUnitTypeId(u)!=0 and not IsUnitType(u,UNIT_TYPE_DEAD) and GetWidgetLife(u)>.405
endfunction
function XHParticipant takes player p returns boolean
    return GetPlayerId(p)<8 and GetPlayerSlotState(p)==PLAYER_SLOT_STATE_PLAYING and (GetPlayerController(p)==MAP_CONTROL_USER or GetPlayerController(p)==MAP_CONTROL_COMPUTER)
endfunction
function XHNear takes unit u, real x, real y, real radius returns boolean
    local real dx=GetUnitX(u)-x
    local real dy=GetUnitY(u)-y
    return dx*dx+dy*dy<=radius*radius
endfunction
function XHBaseArea takes unit u returns boolean
    local integer k=1
    loop
        exitwhen k>8
        if RectContainsUnit(udg_rects02[k],u) then
            return false
        endif
        set k=k+1
    endloop
    return GetUnitX(u)>-3300. and GetUnitX(u)<3300. and GetUnitY(u)>-12500. and GetUnitY(u)<-5100. and not RectContainsUnit(udg_rect31,u)
endfunction
function XHHasSpace takes unit u returns boolean
    local integer k=0
    loop
        exitwhen k>=6
        if UnitItemInSlot(u,k)==null then
            return true
        endif
        set k=k+1
    endloop
    return false
endfunction
function XHOwns takes unit u, integer id returns boolean
    local integer k=0
    loop
        exitwhen k>=6
        if GetItemTypeId(UnitItemInSlot(u,k))==id then
            return true
        endif
        set k=k+1
    endloop
    return false
endfunction
// PROFILE_FUNCTIONS
function XHSpawn takes integer p returns nothing
    local integer n=GetRandomInt(0,7)
    local integer tries=0
    local integer raw=0
    local unit template=null
    local unit candidate=null
    local unit hero=null
    local integer j=0
    if udg_units01[p+1]!=null then
        return
    endif
    call GroupEnumUnitsInRect(XHScratch,udg_rect14,null)
    loop
        exitwhen tries>=8 or template!=null
        set raw=XHPool[n]
        loop
            set candidate=FirstOfGroup(XHScratch)
            exitwhen candidate==null
            call GroupRemoveUnit(XHScratch,candidate)
            if GetUnitTypeId(candidate)==raw and GetOwningPlayer(candidate)==Player(8) then
                set template=candidate
            endif
        endloop
        set n=ModuloInteger(n+1,8)
        set tries=tries+1
        if template==null then
            call GroupEnumUnitsInRect(XHScratch,udg_rect14,null)
        endif
    endloop
    call GroupClear(XHScratch)
    if template==null then
        set candidate=null
        return
    endif
    set raw=GetUnitTypeId(template)
    set hero=CreateUnit(Player(p),raw,GetRectCenterX(udg_rect33),GetRectCenterY(udg_rect33),225.)
    set udg_units01[p+1]=hero
    set udg_integers16[p+1]=1
    call UnitAddItemById(hero,'stwp')
    call UnitAddItemById(hero,'ankh')
    call UnitAddItemById(hero,'pghe')
    loop
        exitwhen j>=udg_integer08
        call UnitAddItemById(hero,'tpow')
        set j=j+1
    endloop
    if udg_boolean04 then
        call SetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD,100000)
    else
        call SetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD,1000)
    endif
    if not udg_boolean01 then
        call RemoveUnit(template)
    endif
    set XHCreated[p]=true
    call DisplayTimedTextToForce(bj_FORCE_ALL_PLAYERS,8.,"Бот "+I2S(p+1)+" выбрал: "+GetUnitName(hero))
    set hero=null
    set template=null
    set candidate=null
endfunction
function XHLearn takes unit u returns nothing
    local integer j=0
    local integer k=0
    local integer old=0
    local integer id=0
    loop
        exitwhen j>=3 or GetHeroSkillPoints(u)<=0
        set k=0
        set old=GetHeroSkillPoints(u)
        loop
            exitwhen k>=5 or GetHeroSkillPoints(u)<old
            set id=XHSkill(GetUnitTypeId(u),ModuloInteger(GetHeroLevel(u)+j+k,5))
            if id!=0 then
                call SelectHeroSkill(u,id)
            endif
            set k=k+1
        endloop
        exitwhen GetHeroSkillPoints(u)==old
        set j=j+1
    endloop
endfunction
function XHEnemy takes unit u returns unit
    local unit v=null
    local unit best=null
    local real dist=1000000000.
    local real d=0.
    local real dx=0.
    local real dy=0.
    call GroupEnumUnitsInRange(XHScratch,GetUnitX(u),GetUnitY(u),1800.,null)
    loop
        set v=FirstOfGroup(XHScratch)
        exitwhen v==null
        call GroupRemoveUnit(XHScratch,v)
        if XHAlive(v) and IsUnitEnemy(v,GetOwningPlayer(u)) and IsUnitVisible(v,GetOwningPlayer(u)) and GetUnitAbilityLevel(v,'Avul')==0 and GetUnitAbilityLevel(v,'Aloc')==0 then
            set dx=GetUnitX(v)-GetUnitX(u)
            set dy=GetUnitY(v)-GetUnitY(u)
            set d=dx*dx+dy*dy
            if d<dist then
                set dist=d
                set best=v
            endif
        endif
    endloop
    set v=null
    return best
endfunction
function XHCast takes integer index, unit u, unit enemy returns boolean
    local integer k=0
    local integer id=0
    local integer mode=0
    local string order=""
    local boolean ok=false
    local unit heal=null
    local unit v=null
    local real ratio=.65
    if XHTime<XHCastAt[index] then
        return false
    endif
    loop
        exitwhen k>=5
        set id=XHSkill(GetUnitTypeId(u),ModuloInteger(k+R2I(XHTime),5))
        if id!=0 and GetUnitAbilityLevel(u,id)>0 then
            set order=XHOrder(id)
            set mode=XHMode(id)
            if mode==4 then
                set heal=null
                call GroupEnumUnitsInRange(XHScratch,GetUnitX(u),GetUnitY(u),650.,null)
                loop
                    set v=FirstOfGroup(XHScratch)
                    exitwhen v==null
                    call GroupRemoveUnit(XHScratch,v)
                    if XHAlive(v) and IsUnitAlly(v,GetOwningPlayer(u)) and not IsUnitType(v,UNIT_TYPE_STRUCTURE) and GetWidgetLife(v)/GetUnitState(v,UNIT_STATE_MAX_LIFE)<ratio then
                        set heal=v
                        set ratio=GetWidgetLife(v)/GetUnitState(v,UNIT_STATE_MAX_LIFE)
                    endif
                endloop
                if heal!=null then
                    set ok=IssueTargetOrder(u,order,heal)
                endif
            elseif enemy!=null and XHNear(u,GetUnitX(enemy),GetUnitY(enemy),800.) then
                if mode==1 then
                    if XHNear(u,GetUnitX(enemy),GetUnitY(enemy),400.) then
                        set ok=IssueImmediateOrder(u,order)
                    endif
                elseif mode==2 then
                    set ok=IssueTargetOrder(u,order,enemy)
                elseif mode==3 then
                    set ok=IssuePointOrder(u,order,GetUnitX(enemy),GetUnitY(enemy))
                elseif mode==5 then
                    if GetWidgetLife(u)<GetUnitState(u,UNIT_STATE_MAX_LIFE)*.4 then
                        set ok=IssueImmediateOrder(u,order)
                    endif
                elseif mode==6 then
                    set ok=IssueImmediateOrder(u,order)
                endif
            endif
            if ok then
                // Mana/cooldown decisions remain native; failed orders don't consume resources.
                set XHCastAt[index]=XHTime+3.
                set heal=null
                set v=null
                return true
            endif
        endif
        set k=k+1
    endloop
    set heal=null
    set v=null
    return false
endfunction
function XHShop takes integer p, integer index, unit u returns boolean
    local unit shop=udg_unit02
    local integer wanted=0
    local integer price=0
    local integer before=0
    local integer j=0
    local item it=null
    if not XHAlive(shop) or XHTime<XHBuyAt[index] or IsTriggerEnabled(udg_trigger62) then
        return false
    endif
    // Only stock that exists in this exact map. Preserve quest items and the six-slot limit.
    if not XHOwns(u,'ofro') then
        set wanted='ofro'
        set price=20000
    elseif not XHOwns(u,'modt') then
        set wanted='modt'
        set price=50000
    endif
    if wanted!=0 and XHHasSpace(u) and GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)>=price then
        if not XHNear(u,GetUnitX(shop),GetUnitY(shop),350.) then
            call IssuePointOrder(u,"move",GetUnitX(shop),GetUnitY(shop))
        else
            set before=GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)
            call IssueNeutralTargetOrder(Player(p),shop,"neutralinteract",u)
            call IssueNeutralImmediateOrderById(Player(p),shop,wanted)
            set XHBuyAt[index]=XHTime+10.
            if GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)<before then
                set XHPurchases[p]=XHPurchases[p]+1
            endif
        endif
        return true
    endif
    // Existing map's -bt rule: 50000 for +100 to each stat, only between special duels.
    if GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)>=50000 and not XHNear(u,GetUnitX(shop),GetUnitY(shop),450.) then
        call IssuePointOrder(u,"move",GetUnitX(shop),GetUnitY(shop))
        return true
    endif
    if GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)>=50000 and XHNear(u,GetUnitX(shop),GetUnitY(shop),450.) then
        call SetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)-50000)
        call SetHeroStr(u,GetHeroStr(u,false)+100,true)
        call SetHeroAgi(u,GetHeroAgi(u,false)+100,true)
        call SetHeroInt(u,GetHeroInt(u,false)+100,true)
        set XHBuyAt[index]=XHTime+10.
        set XHPurchases[p]=XHPurchases[p]+1
        return true
    endif
    return false
endfunction
function XHHeal takes integer p, integer index, unit u returns boolean
    local unit v=null
    local unit shop=null
    local real best=1000000000.
    local real dx=0.
    local real dy=0.
    local real d=0.
    local integer before=0
    if not XHBaseArea(u) or GetWidgetLife(u)>=GetUnitState(u,UNIT_STATE_MAX_LIFE)*.35 or GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)<1000 or not XHHasSpace(u) or XHTime<XHHealAt[index] then
        return false
    endif
    call GroupEnumUnitsInRange(XHScratch,GetUnitX(u),GetUnitY(u),5000.,null)
    loop
        set v=FirstOfGroup(XHScratch)
        exitwhen v==null
        call GroupRemoveUnit(XHScratch,v)
        if XHAlive(v) and GetUnitTypeId(v)=='ngme' and not IsUnitEnemy(v,Player(p)) and XHBaseArea(v) then
            set dx=GetUnitX(v)-GetUnitX(u)
            set dy=GetUnitY(v)-GetUnitY(u)
            set d=dx*dx+dy*dy
            if d<best then
                set best=d
                set shop=v
            endif
        endif
    endloop
    if shop==null then
        set v=null
        return false
    endif
    if best>300.*300. then
        call IssuePointOrder(u,"move",GetUnitX(shop),GetUnitY(shop))
    else
        set before=GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)
        call IssueNeutralTargetOrder(Player(p),shop,"neutralinteract",u)
        call IssueNeutralImmediateOrderById(Player(p),shop,'pghe')
        set XHHealAt[index]=XHTime+5.
        if GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)<before then
            set XHPurchases[p]=XHPurchases[p]+1
        endif
    endif
    set v=null
    set shop=null
    return true
endfunction
function XHThink takes integer p, integer index, unit u returns nothing
    local unit enemy=null
    local unit v=null
    local unit goal=null
    local real best=1000000000.
    local real d=0.
    local real x=0.
    local real y=0.
    local integer k=0
    local item it=null
    if not XHAlive(u) or IsUnitPaused(u) or XHTime<XHBusy[index] then
        return
    endif
    call XHLearn(u)
    set enemy=XHEnemy(u)
    set k=0
    loop
        exitwhen k>=6
        set it=UnitItemInSlot(u,k)
        if GetItemTypeId(it)=='pghe' and GetWidgetLife(u)<GetUnitState(u,UNIT_STATE_MAX_LIFE)*.4 then
            call UnitUseItem(u,it)
            set enemy=null
            set it=null
            return
        endif
        set k=k+1
    endloop
    if XHHeal(p,index,u) then
        set enemy=null
        set it=null
        return
    endif
    if enemy!=null and not XHNear(u,GetUnitX(enemy),GetUnitY(enemy),900.) and GetWidgetLife(u)>GetUnitState(u,UNIT_STATE_MAX_LIFE)*.6 and XHBaseArea(u) and XHShop(p,index,u) then
        set enemy=null
        set it=null
        return
    endif
    if XHCast(index,u,enemy) then
        set enemy=null
        set it=null
        return
    endif
    if enemy!=null then
        if GetWidgetLife(u)<GetUnitState(u,UNIT_STATE_MAX_LIFE)*.2 and XHBaseArea(u) and not IsTriggerEnabled(udg_trigger62) then
            call IssuePointOrder(u,"move",GetRectCenterX(udg_rect33),GetRectCenterY(udg_rect33))
        else
            call IssueTargetOrder(u,"attack",enemy)
        endif
        set enemy=null
        set it=null
        return
    endif
    if XHBaseArea(u) and XHShop(p,index,u) then
        set it=null
        return
    endif
    // An active human in a remote encounter gives bots a rally destination, never ownership/control.
    set k=0
    loop
        exitwhen k>=8
        set v=udg_units01[k+1]
        if GetPlayerController(Player(k))==MAP_CONTROL_USER and XHAlive(v) and not IsUnitPaused(v) and not RectContainsUnit(udg_rect14,v) and not XHBaseArea(v) then
            set goal=v
        endif
        set k=k+1
    endloop
    if not XHBaseArea(u) then
        // Personal challenge rooms must not be left to chase another player's opponent.
        call IssueImmediateOrder(u,"holdposition")
    elseif goal!=null and not XHNear(u,GetUnitX(goal),GetUnitY(goal),350.) then
        call IssuePointOrder(u,"attack",GetUnitX(goal),GetUnitY(goal))
    else
        // Nearest visible, vulnerable scenario boss; closed/invulnerable challenges aren't activated.
        call GroupEnumUnitsInRect(XHScratch,bj_mapInitialPlayableArea,null)
        loop
            set v=FirstOfGroup(XHScratch)
            exitwhen v==null
            call GroupRemoveUnit(XHScratch,v)
            if XHAlive(v) and IsUnitEnemy(v,Player(p)) and IsUnitVisible(v,Player(p)) and IsUnitType(v,UNIT_TYPE_HERO) and GetUnitAbilityLevel(v,'Avul')==0 and GetUnitAbilityLevel(v,'Aloc')==0 and not IsUnitPaused(v) then
                set x=GetUnitX(v)-GetUnitX(u)
                set y=GetUnitY(v)-GetUnitY(u)
                set d=x*x+y*y
                if d<best then
                    set best=d
                    set goal=v
                endif
            endif
        endloop
        if goal!=null then
            call IssuePointOrder(u,"attack",GetUnitX(goal),GetUnitY(goal))
        elseif XHBaseArea(u) then
            set k=ModuloInteger(p,4)+1
            set x=GetRectCenterX(udg_rect11)+(GetRectCenterX(udg_rects03[k])-GetRectCenterX(udg_rect11))*.65
            set y=GetRectCenterY(udg_rect11)+(GetRectCenterY(udg_rects03[k])-GetRectCenterY(udg_rect11))*.65
            if not XHNear(u,x,y,160.) then
                call IssuePointOrder(u,"attack",x,y)
            endif
        endif
    endif
    set enemy=null
    set v=null
    set goal=null
    set it=null
endfunction
function XHStep takes nothing returns nothing
    local integer p=XHCursor
    local unit u=null
    set XHTime=XHTime+.25
    set XHCursor=ModuloInteger(XHCursor+1,8)
    if not XHReady or udg_rect33==null or GetPlayerSlotState(Player(p))!=PLAYER_SLOT_STATE_PLAYING or GetPlayerController(Player(p))!=MAP_CONTROL_COMPUTER then
        return
    endif
    set u=udg_units01[p+1]
    if u==null then
        call XHSpawn(p)
    else
        call XHThink(p,p,u)
        if udg_booleans04[p+1] and udg_units01[p+9]!=null then
            call XHThink(p,p+8,udg_units01[p+9])
        endif
    endif
    set u=null
endfunction
function XHSpell takes nothing returns nothing
    local unit u=GetTriggerUnit()
    local integer p=GetPlayerId(GetOwningPlayer(u))
    local integer i=p
    local string order=""
    if p<8 and GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER then
        if udg_units01[p+9]==u then
            set i=p+8
        endif
        set order=XHOrder(GetSpellAbilityId())
        if order=="blizzard" or order=="starfall" or order=="whirlwind" or order=="earthquake" or order=="deathanddecay" or order=="stampede" or order=="monsoon" then
            set XHBusy[i]=XHTime+8.
        else
            set XHBusy[i]=XHTime+1.25
        endif
    endif
    set u=null
endfunction
function XHSummon takes nothing returns nothing
    local unit caster=GetSummoningUnit()
    local unit pet=GetSummonedUnit()
    local unit enemy=null
    local integer p=GetPlayerId(GetOwningPlayer(caster))
    if p<8 and GetPlayerSlotState(Player(p))==PLAYER_SLOT_STATE_PLAYING and GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER then
        set enemy=XHEnemy(caster)
        if enemy!=null then
            call IssueTargetOrder(pet,"attack",enemy)
        else
            call IssueTargetOrder(pet,"follow",caster)
        endif
    endif
    set caster=null
    set pet=null
    set enemy=null
endfunction
function XHStatus takes nothing returns nothing
    local integer p=0
    local unit u=null
    loop
        exitwhen p>=8
        if GetPlayerSlotState(Player(p))==PLAYER_SLOT_STATE_PLAYING and GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER then
            set u=udg_units01[p+1]
            if u==null then
                call DisplayTimedTextToPlayer(GetTriggerPlayer(),0.,0.,20.,"Бот "+I2S(p+1)+": ждёт выбора режима/героя.")
            else
                call DisplayTimedTextToPlayer(GetTriggerPlayer(),0.,0.,20.,"Бот "+I2S(p+1)+": "+GetUnitName(u)+", уровень "+I2S(GetHeroLevel(u))+", золото "+I2S(GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD))+", закупок "+I2S(XHPurchases[p]))
            endif
        endif
        set p=p+1
    endloop
    set u=null
endfunction
function XHInit takes nothing returns nothing
    local trigger t=CreateTrigger()
    local integer p=0
    set XHScratch=CreateGroup()
    // PROFILE_DATA
    call TriggerRegisterAnyUnitEventBJ(t,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddAction(t,function XHSpell)
    set t=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(t,EVENT_PLAYER_UNIT_SUMMON)
    call TriggerAddAction(t,function XHSummon)
    set t=CreateTrigger()
    loop
        exitwhen p>=8
        call TriggerRegisterPlayerChatEvent(t,Player(p),"-bots",true)
        set p=p+1
    endloop
    call TriggerAddAction(t,function XHStatus)
    call TimerStart(CreateTimer(),.25,true,function XHStep)
    set t=null
endfunction
