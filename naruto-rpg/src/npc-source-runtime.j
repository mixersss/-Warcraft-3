function NPCSourceType takes unit u returns integer
    local integer raw=GetUnitTypeId(u)
    if raw=='re01' then
        return 'nban'
    endif
    if raw=='re03' then
        return 'h014'
    endif
    if raw=='re04' then
        return 'h013'
    endif
    if raw=='re06' then
        return 'n003'
    endif
    if raw=='re07' then
        return 'nass'
    endif
    if raw=='C014' then
        return RosterHeroType[4]
    elseif raw=='C015' then
        return RosterHeroType[3]
    elseif raw=='C016' then
        return RosterHeroType[5]
    elseif raw=='C017' then
        return RosterHeroType[7]
    elseif raw=='C018' then
        return RosterHeroType[8]
    elseif raw=='C019' then
        return RosterHeroType[9]
    elseif raw=='C01A' then
        return RosterHeroType[10]
    elseif raw=='C01B' then
        return RosterHeroType[11]
    endif
    return raw
endfunction
// Imported source spell actions with namespace/type adapters; see npc-source-audit.json.
function OrigNPC_M0V takes real OrigNPC_M0V_local_M1V returns nothing
local real OrigNPC_M0V_local_M2V
local real OrigNPC_M0V_local_st=TimerGetElapsed(OrigNPC_MQV)
if OrigNPC_M0V_local_st<=0 then
set OrigNPC_MQV=CreateTimer()
call TimerStart(OrigNPC_MQV,0xF4240,false,null)
endif
if(OrigNPC_M0V_local_M1V>0)then
loop
set OrigNPC_M0V_local_M2V=OrigNPC_M0V_local_M1V-TimerGetElapsed(OrigNPC_MQV)+OrigNPC_M0V_local_st
exitwhen OrigNPC_M0V_local_M2V<=0
if(OrigNPC_M0V_local_M2V>bj_POLLED_WAIT_SKIP_THRESHOLD)then
call TriggerSleepAction(.1*OrigNPC_M0V_local_M2V)
else
call TriggerSleepAction(bj_POLLED_WAIT_INTERVAL)
endif
endloop
endif
endfunction
function OrigNPC_M3V takes location OrigNPC_M3V_local_M4V,real OrigNPC_M3V_local_M5V,real OrigNPC_M3V_local_M6V returns location
return Location(GetLocationX(OrigNPC_M3V_local_M4V)+OrigNPC_M3V_local_M5V*Cos(OrigNPC_M3V_local_M6V*bj_DEGTORAD),GetLocationY(OrigNPC_M3V_local_M4V)+OrigNPC_M3V_local_M5V*Sin(OrigNPC_M3V_local_M6V*bj_DEGTORAD))
endfunction
function OrigNPC_M8V takes real OrigNPC_M8V_local_M9V,location OrigNPC_M8V_local_PVV,code OrigNPC_M8V_local_PEV returns nothing
local rect OrigNPC_M8V_local_r
if(OrigNPC_M8V_local_M9V>=0)then
set OrigNPC_MTV=GetLocationX(OrigNPC_M8V_local_PVV)
set OrigNPC_MUV=GetLocationY(OrigNPC_M8V_local_PVV)
set bj_enumDestructableRadius=OrigNPC_M8V_local_M9V*OrigNPC_M8V_local_M9V
set OrigNPC_M8V_local_r=Rect(OrigNPC_MTV-OrigNPC_M8V_local_M9V,OrigNPC_MUV-OrigNPC_M8V_local_M9V,OrigNPC_MTV+OrigNPC_M8V_local_M9V,OrigNPC_MUV+OrigNPC_M8V_local_M9V)
call EnumDestructablesInRect(OrigNPC_M8V_local_r,filterEnumDestructablesInCircleBJ,OrigNPC_M8V_local_PEV)
call RemoveRect(OrigNPC_M8V_local_r)
set OrigNPC_M8V_local_r=null
endif
endfunction
function OrigNPC_PRV takes rect OrigNPC_PRV_local_r returns group
set OrigNPC_MWV=CreateGroup()
call GroupEnumUnitsInRect(OrigNPC_MWV,OrigNPC_PRV_local_r,OrigNPC_MZV)
return OrigNPC_MWV
endfunction
function OrigNPC_PIV takes real OrigNPC_PIV_local_M9V,location OrigNPC_PIV_local_PAV,boolexpr OrigNPC_PIV_local_POV returns group
set OrigNPC_MWV=CreateGroup()
call GroupEnumUnitsInRangeOfLoc(OrigNPC_MWV,OrigNPC_PIV_local_PAV,OrigNPC_PIV_local_M9V,OrigNPC_PIV_local_POV)
return OrigNPC_MWV
endfunction
function OrigNPC_PNV takes real OrigNPC_PNV_local_M9V,location OrigNPC_PNV_local_PAV returns group
set OrigNPC_MWV=CreateGroup()
call GroupEnumUnitsInRangeOfLoc(OrigNPC_MWV,OrigNPC_PNV_local_PAV,OrigNPC_PNV_local_M9V,OrigNPC_MZV)
return OrigNPC_MWV
endfunction
function OrigNPC_PBV takes integer OrigNPC_PBV_local_PCV returns group
    local group result=CreateGroup()
    local group extra=null
    local unit u=null
    local integer kind=20
    local integer raw=0
    call GroupEnumUnitsOfType(result,UnitId2String(OrigNPC_PBV_local_PCV),OrigNPC_MZV)
    if OrigNPC_PBV_local_PCV=='nban' then
        set extra=CreateGroup()
        call GroupEnumUnitsOfType(extra,UnitId2String('re01'),OrigNPC_MZV)
        loop
            set u=FirstOfGroup(extra)
            exitwhen u==null
            call GroupRemoveUnit(extra,u)
            call GroupAddUnit(result,u)
        endloop
        call DestroyGroup(extra)
        set extra=null
    endif
    if OrigNPC_PBV_local_PCV=='h014' then
        set extra=CreateGroup()
        call GroupEnumUnitsOfType(extra,UnitId2String('re03'),OrigNPC_MZV)
        loop
            set u=FirstOfGroup(extra)
            exitwhen u==null
            call GroupRemoveUnit(extra,u)
            call GroupAddUnit(result,u)
        endloop
        call DestroyGroup(extra)
        set extra=null
    endif
    if OrigNPC_PBV_local_PCV=='h013' then
        set extra=CreateGroup()
        call GroupEnumUnitsOfType(extra,UnitId2String('re04'),OrigNPC_MZV)
        loop
            set u=FirstOfGroup(extra)
            exitwhen u==null
            call GroupRemoveUnit(extra,u)
            call GroupAddUnit(result,u)
        endloop
        call DestroyGroup(extra)
        set extra=null
    endif
    if OrigNPC_PBV_local_PCV=='n003' then
        set extra=CreateGroup()
        call GroupEnumUnitsOfType(extra,UnitId2String('re06'),OrigNPC_MZV)
        loop
            set u=FirstOfGroup(extra)
            exitwhen u==null
            call GroupRemoveUnit(extra,u)
            call GroupAddUnit(result,u)
        endloop
        call DestroyGroup(extra)
        set extra=null
    endif
    if OrigNPC_PBV_local_PCV=='nass' then
        set extra=CreateGroup()
        call GroupEnumUnitsOfType(extra,UnitId2String('re07'),OrigNPC_MZV)
        loop
            set u=FirstOfGroup(extra)
            exitwhen u==null
            call GroupRemoveUnit(extra,u)
            call GroupAddUnit(result,u)
        endloop
        call DestroyGroup(extra)
        set extra=null
    endif
    loop
        exitwhen kind>=28
        set raw=CampaignUnit[kind]
        if NPCSourceTypeDummy[kind]==OrigNPC_PBV_local_PCV then
            set extra=CreateGroup()
            call GroupEnumUnitsOfType(extra,UnitId2String(raw),OrigNPC_MZV)
            loop
                set u=FirstOfGroup(extra)
                exitwhen u==null
                call GroupRemoveUnit(extra,u)
                call GroupAddUnit(result,u)
            endloop
            call DestroyGroup(extra)
            set extra=null
        endif
        set kind=kind+1
    endloop
    set u=null
    set OrigNPC_MWV=result
    set result=null
    return OrigNPC_MWV
endfunction
function OrigNPC_PDV takes player OrigNPC_PDV_local_PFV,boolexpr OrigNPC_PDV_local_POV returns group
set OrigNPC_MWV=CreateGroup()
call GroupEnumUnitsOfPlayer(OrigNPC_MWV,OrigNPC_PDV_local_PFV,OrigNPC_PDV_local_POV)
call DestroyBoolExpr(OrigNPC_PDV_local_POV)
return OrigNPC_MWV
endfunction
function OrigNPC_PHV takes player OrigNPC_PHV_local_PFV,integer OrigNPC_PHV_local_PCV returns group
set OrigNPC_MWV=CreateGroup()
set bj_groupEnumTypeId=OrigNPC_PHV_local_PCV
call GroupEnumUnitsOfPlayer(OrigNPC_MWV,OrigNPC_PHV_local_PFV,filterGetUnitsOfPlayerAndTypeId)
return OrigNPC_MWV
endfunction
function OrigNPC_PJV takes mapcontrol OrigNPC_PJV_local_PKV returns force
local integer OrigNPC_PJV_local_PLV
local player OrigNPC_PJV_local_PMV
set OrigNPC_MYV=CreateForce()
set OrigNPC_PJV_local_PLV=0
loop
set OrigNPC_PJV_local_PMV=Player(OrigNPC_PJV_local_PLV)
if GetPlayerController(OrigNPC_PJV_local_PMV)==OrigNPC_PJV_local_PKV then
call ForceAddPlayer(OrigNPC_MYV,OrigNPC_PJV_local_PMV)
endif
set OrigNPC_PJV_local_PLV=OrigNPC_PJV_local_PLV+1
exitwhen OrigNPC_PJV_local_PLV==16
endloop
return OrigNPC_MYV
endfunction
function OrigNPC_E7E takes nothing returns boolean
return(GetSpellAbilityId()=='A025')and(NPCSourceType(GetTriggerUnit())=='c00D')
endfunction
function OrigNPC_E8E takes nothing returns boolean
return(OrigNPC_E7E())
endfunction
function OrigNPC_E9E takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),4)
call TriggerSleepAction(.75)
call SetUnitAnimationByIndex(GetTriggerUnit(),5)
endfunction
function OrigNPC_XEE takes nothing returns boolean
return(GetSpellAbilityId()=='A00R')or(GetSpellAbilityId()=='A027')or(GetSpellAbilityId()=='A01S')
endfunction
function OrigNPC_XXE takes nothing returns boolean
return(OrigNPC_XEE())
endfunction
function OrigNPC_XOE takes nothing returns nothing
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_AE,100.,GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h033',GetOwningPlayer(GetTriggerUnit()),OrigNPC_BE,GetRandomReal(0,360))
call SetUnitAnimation(bj_lastCreatedUnit,"Birth")
call SetUnitTimeScalePercent(bj_lastCreatedUnit,300.)
call UnitApplyTimedLifeBJ(1.,'BTLF',bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_AE)
call RemoveLocation(OrigNPC_BE)
endfunction
function OrigNPC_XJE takes nothing returns boolean
return(GetSpellAbilityId()=='A02Z')
endfunction
function OrigNPC_XKE takes nothing returns boolean
return(GetOwningPlayer(GetTriggerUnit())==Player(0xC))
endfunction
function OrigNPC_XLE takes nothing returns nothing
call UnitApplyTimedLifeBJ(2.,'BTLF',GetEnumUnit())
endfunction
function OrigNPC_XME takes nothing returns nothing
call UnitApplyTimedLifeBJ(2.,'BTLF',GetEnumUnit())
endfunction
function OrigNPC_XPE takes nothing returns boolean
return(GetOwningPlayer(GetTriggerUnit())==Player(0xC))
endfunction
function OrigNPC_XQE takes nothing returns nothing
set OrigNPC_TF=GetTriggerUnit()
set OrigNPC_WF=GetSpellTargetLoc()
call SetUnitFacingToFaceLocTimed(GetTriggerUnit(),OrigNPC_WF,.01)
call TriggerSleepAction(.01)
call SetUnitAnimation(GetTriggerUnit(),"spell")
call TriggerSleepAction(.75)
call PauseUnit(GetTriggerUnit(),true)
if(OrigNPC_XKE())then
call SetUnitInvulnerable(GetTriggerUnit(),true)
endif
call SetUnitTimeScalePercent(OrigNPC_TF,400.)
call CreateNUnitsAtLocFacingLocBJ(1,'h031',GetOwningPlayer(GetTriggerUnit()),OrigNPC_WF,OrigNPC_WF)
call SelectUnitRemoveForPlayer(GetTriggerUnit(),GetOwningPlayer(GetTriggerUnit()))
call RemoveLocation(OrigNPC_WF)
set OrigNPC_LF=bj_lastCreatedUnit
call UnitApplyTimedLifeBJ(7.5,'BTLF',OrigNPC_LF)
set OrigNPC_KR=GetUnitLoc(bj_lastCreatedUnit)
call SelectUnitForPlayerSingle(OrigNPC_LF,GetTriggerPlayer())
call SetCameraTargetControllerNoZForPlayer(GetOwningPlayer(OrigNPC_TF),OrigNPC_LF,0,-625.,false)
set OrigNPC_CG[0]=OrigNPC_M3V(OrigNPC_KR,250.,0)
set OrigNPC_CG[1]=OrigNPC_M3V(OrigNPC_KR,225.,45.)
set OrigNPC_CG[2]=OrigNPC_M3V(OrigNPC_KR,250.,90.)
set OrigNPC_CG[3]=OrigNPC_M3V(OrigNPC_KR,225.,135.)
set OrigNPC_CG[4]=OrigNPC_M3V(OrigNPC_KR,250.,180.)
set OrigNPC_CG[5]=OrigNPC_M3V(OrigNPC_KR,225.,225.)
set OrigNPC_CG[6]=OrigNPC_M3V(OrigNPC_KR,250.,270.)
set OrigNPC_CG[7]=OrigNPC_M3V(OrigNPC_KR,225.,315.)
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[0],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[1],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[2],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[3],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[4],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[5],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[6],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[7],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,GetRandomReal(0,360))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,GetRandomReal(0,360))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,GetRandomReal(0,360))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,GetRandomReal(0,360))
set OrigNPC_ME=OrigNPC_PBV('h02K')
call ForGroupBJ(OrigNPC_ME,function OrigNPC_XLE)
call DestroyGroup(OrigNPC_ME)
call RemoveLocation(OrigNPC_KR)
call ForGroupBJ(OrigNPC_PBV('h02K'),function OrigNPC_XME)
call EnableTrigger(OrigNPC_R4)
call EnableTrigger(OrigNPC_I4)
call EnableTrigger(OrigNPC_N4)
call EnableTrigger(OrigNPC_A4)
call EnableTrigger(OrigNPC_O4)
call TriggerSleepAction(8.)
call PauseUnit(GetTriggerUnit(),false)
if(OrigNPC_XPE())then
call SetUnitInvulnerable(GetTriggerUnit(),false)
endif
call SelectUnitForPlayerSingle(OrigNPC_TF,GetOwningPlayer(GetTriggerUnit()))
call SetUnitTimeScalePercent(OrigNPC_TF,100.)
set OrigNPC_AE=OffsetLocation(GetUnitLoc(OrigNPC_TF),.0,-625.)
call PanCameraToTimedLocForPlayer(GetOwningPlayer(OrigNPC_TF),OrigNPC_AE,0)
call RemoveLocation(OrigNPC_AE)
call DisableTrigger(OrigNPC_R4)
call DisableTrigger(OrigNPC_I4)
call DisableTrigger(OrigNPC_B4)
call DisableTrigger(OrigNPC_O4)
call DisableTrigger(OrigNPC_A4)
call DisableTrigger(OrigNPC_N4)
call SetUnitAnimation(OrigNPC_TF,"stand")
call RemoveLocation(OrigNPC_WF)
endfunction
function OrigNPC_XTE takes nothing returns boolean
return(GetSpellAbilityId()=='A02Z')and(GetTriggerUnit()==OrigNPC_J4V)
endfunction
function OrigNPC_XUE takes nothing returns boolean
return(OrigNPC_XTE())
endfunction
function OrigNPC_XWE takes nothing returns nothing
call DisplayTextToPlayer(GetOwningPlayer(GetTriggerUnit()),0,0,"|cff32cd32You may control this object by right-clicking a point.|r")
call DestroyTrigger(GetTriggeringTrigger())
endfunction
function OrigNPC_XZE takes nothing returns nothing
call SetUnitAnimation(OrigNPC_TF,"attack alternate")
endfunction
function OrigNPC_X0E takes nothing returns nothing
set OrigNPC_MF=(GetUnitFacing(OrigNPC_LF)+90.)
set OrigNPC_PF=GetUnitLoc(OrigNPC_LF)
call SetUnitPositionLocFacingBJ(OrigNPC_LF,OrigNPC_PF,OrigNPC_MF)
call RemoveLocation(OrigNPC_PF)
endfunction
function OrigNPC_X2E takes nothing returns boolean
return(IsUnitType(GetFilterUnit(),UNIT_TYPE_STRUCTURE)==false)!=null
endfunction
function OrigNPC_X3E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_X4E takes nothing returns boolean
return(IsUnitAliveBJ(GetFilterUnit()))
endfunction
function OrigNPC_X5E takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_LF)))
endfunction
function OrigNPC_X6E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_X4E(),OrigNPC_X5E())
endfunction
function OrigNPC_X7E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_X3E(),OrigNPC_X6E())
endfunction
function OrigNPC_X8E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_X2E(),OrigNPC_X7E())
endfunction
function OrigNPC_X9E takes nothing returns boolean
return(IsUnitType(GetFilterUnit(),UNIT_TYPE_STRUCTURE)==false)!=null
endfunction
function OrigNPC_OVE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_OEE takes nothing returns boolean
return(IsUnitAliveBJ(GetFilterUnit()))
endfunction
function OrigNPC_OXE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_LF)))
endfunction
function OrigNPC_OOE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_OEE(),OrigNPC_OXE())
endfunction
function OrigNPC_ORE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_OVE(),OrigNPC_OOE())
endfunction
function OrigNPC_OIE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_X9E(),OrigNPC_ORE())
endfunction
function OrigNPC_OAE takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_LF,GetEnumUnit(),24.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_ONE takes nothing returns nothing
set OrigNPC_UF=GetUnitLoc(GetEnumUnit())
call AddSpecialEffectLocBJ(OrigNPC_UF,"Abilities\\Weapons\\AncientProtectorMissile\\AncientProtectorMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call SetUnitPositionLoc(GetEnumUnit(),OrigNPC_M3V(OrigNPC_UF,30.,AngleBetweenPoints(OrigNPC_DR,OrigNPC_UF)))
call RemoveLocation(OrigNPC_UF)
endfunction
function OrigNPC_OBE takes nothing returns nothing
call KillDestructable(GetEnumDestructable())
call SetDestAnimationSpeedPercent(GetEnumDestructable(),300.)
endfunction
function OrigNPC_OCE takes nothing returns nothing
set OrigNPC_DR=GetUnitLoc(OrigNPC_LF)
set OrigNPC_SF=OrigNPC_M3V(OrigNPC_DR,30.,GetUnitFacing(OrigNPC_TF))
call SetUnitPositionLoc(OrigNPC_LF,OrigNPC_SF)
set OrigNPC_QF=OrigNPC_PIV(500.,OrigNPC_DR,Condition(function OrigNPC_X8E))
set OrigNPC_HG=OrigNPC_PIV(550.,OrigNPC_DR,Condition(function OrigNPC_OIE))
call ForGroupBJ(OrigNPC_HG,function OrigNPC_OAE)
call ForGroupBJ(OrigNPC_QF,function OrigNPC_ONE)
call OrigNPC_M8V(500.,OrigNPC_DR,function OrigNPC_OBE)
call DestroyGroup(OrigNPC_QF)
call DestroyGroup(OrigNPC_HG)
call RemoveLocation(OrigNPC_SF)
call RemoveLocation(OrigNPC_DR)
endfunction
function OrigNPC_OFE takes nothing returns boolean
return(GetTriggerUnit()==OrigNPC_LF)
endfunction
function OrigNPC_OGE takes nothing returns nothing
call DisableTrigger(OrigNPC_I4)
call RemoveLocation(OrigNPC_WF)
set OrigNPC_WF=GetOrderPointLoc()
call EnableTrigger(OrigNPC_B4)
endfunction
function OrigNPC_OJE takes nothing returns boolean
return(GetTriggerUnit()==OrigNPC_LF)and(GetOrderTargetUnit()!=OrigNPC_LF)
endfunction
function OrigNPC_OKE takes nothing returns nothing
call DisableTrigger(OrigNPC_I4)
call RemoveLocation(OrigNPC_WF)
set OrigNPC_WF=GetUnitLoc(GetOrderTargetUnit())
call EnableTrigger(OrigNPC_B4)
endfunction
function OrigNPC_OME takes nothing returns boolean
return(IsUnitType(GetFilterUnit(),UNIT_TYPE_STRUCTURE)==false)!=null
endfunction
function OrigNPC_OPE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_LF)))
endfunction
function OrigNPC_OQE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_OME(),OrigNPC_OPE())
endfunction
function OrigNPC_OSE takes nothing returns boolean
return(IsUnitType(GetFilterUnit(),UNIT_TYPE_STRUCTURE)==false)!=null
endfunction
function OrigNPC_OTE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_LF)))
endfunction
function OrigNPC_OUE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_OWE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_OTE(),OrigNPC_OUE())
endfunction
function OrigNPC_OYE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_OSE(),OrigNPC_OWE())
endfunction
function OrigNPC_OZE takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_LF,GetEnumUnit(),21.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_O_E takes nothing returns nothing
set OrigNPC_UF=GetUnitLoc(GetEnumUnit())
call AddSpecialEffectLocBJ(OrigNPC_UF,"Abilities\\Weapons\\AncientProtectorMissile\\AncientProtectorMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call SetUnitPositionLoc(GetEnumUnit(),OrigNPC_M3V(OrigNPC_UF,30.,AngleBetweenPoints(OrigNPC_DR,OrigNPC_UF)))
call RemoveLocation(OrigNPC_UF)
endfunction
function OrigNPC_O0E takes nothing returns nothing
call KillDestructable(GetEnumDestructable())
call SetDestAnimationSpeedPercent(GetEnumDestructable(),300.)
endfunction
function OrigNPC_O1E takes nothing returns nothing
set OrigNPC_DR=GetUnitLoc(OrigNPC_LF)
set OrigNPC_YF=AngleBetweenPoints(OrigNPC_DR,OrigNPC_M3V(OrigNPC_WF,4000.,OrigNPC_YF))
set OrigNPC_SF=OrigNPC_M3V(OrigNPC_DR,30.,OrigNPC_YF)
call SetUnitPositionLoc(OrigNPC_LF,OrigNPC_SF)
set OrigNPC_QF=OrigNPC_PIV(500.,OrigNPC_DR,Condition(function OrigNPC_OQE))
set OrigNPC_HG=OrigNPC_PIV(550.,OrigNPC_DR,Condition(function OrigNPC_OYE))
call ForGroupBJ(OrigNPC_HG,function OrigNPC_OZE)
call ForGroupBJ(OrigNPC_QF,function OrigNPC_O_E)
call OrigNPC_M8V(500.,OrigNPC_DR,function OrigNPC_O0E)
call DestroyGroup(OrigNPC_QF)
call DestroyGroup(OrigNPC_HG)
call RemoveLocation(OrigNPC_DR)
endfunction
function OrigNPC_RKE takes nothing returns boolean
return(IsUnitIllusion(GetSpellTargetUnit()))and(IsUnitEnemy(GetTriggerUnit(),GetOwningPlayer(GetSpellTargetUnit())))and(GetSpellAbilityId()!='A033')and(GetSpellAbilityId()!='A02A')
endfunction
function OrigNPC_RLE takes nothing returns nothing
call KillUnit(GetSpellTargetUnit())
call RemoveUnit(GetSpellTargetUnit())
endfunction
function OrigNPC_GBE takes nothing returns boolean
return(GetSpellAbilityId()=='A034')and(GetTriggerUnit()==OrigNPC_J1V)
endfunction
function OrigNPC_GCE takes nothing returns boolean
return(OrigNPC_GBE())
endfunction
function OrigNPC_GDE takes nothing returns nothing
call DisplayTextToPlayer(GetOwningPlayer(GetTriggerUnit()),0,0,"TRIGSTR_4349")
call DestroyTrigger(GetTriggeringTrigger())
endfunction
function OrigNPC_GGE takes nothing returns boolean
return(GetSpellAbilityId()=='A034')and(GetTriggerUnit()==OrigNPC_K0V)
endfunction
function OrigNPC_GHE takes nothing returns boolean
return(OrigNPC_GGE())
endfunction
function OrigNPC_GJE takes nothing returns nothing
call DisplayTextToPlayer(GetOwningPlayer(GetTriggerUnit()),0,0,"TRIGSTR_5336")
call DestroyTrigger(GetTriggeringTrigger())
endfunction
function OrigNPC_GLE takes nothing returns boolean
return(GetSpellAbilityId()=='A01D')and(GetTriggerUnit()==OrigNPC_JZV)
endfunction
function OrigNPC_GME takes nothing returns boolean
return(OrigNPC_GLE())
endfunction
function OrigNPC_GPE takes nothing returns boolean
return(NPCSourceType(OrigNPC_GV)=='H00S')
endfunction
function OrigNPC_GQE takes nothing returns boolean
return(NPCSourceType(OrigNPC_GV)=='H00S')
endfunction
function OrigNPC_GSE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01D',OrigNPC_GV)==1)
endfunction
function OrigNPC_GTE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01D',OrigNPC_GV)==2)
endfunction
function OrigNPC_GUE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01D',OrigNPC_GV)==3)
endfunction
function OrigNPC_GWE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01D',OrigNPC_GV)==1)
endfunction
function OrigNPC_GYE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01D',OrigNPC_GV)==2)
endfunction
function OrigNPC_GZE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01D',OrigNPC_GV)==3)
endfunction
function OrigNPC_G_E takes nothing returns boolean
return(IsUnitType(OrigNPC_HV,UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_G0E takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_GV)))
endfunction
function OrigNPC_G1E takes nothing returns boolean
return(GetFilterUnit()!=OrigNPC_HV)
endfunction
function OrigNPC_G2E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_G3E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_G1E(),OrigNPC_G2E())
endfunction
function OrigNPC_G4E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_G0E(),OrigNPC_G3E())
endfunction
function OrigNPC_G5E takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_GV)))
endfunction
function OrigNPC_G6E takes nothing returns boolean
return(GetFilterUnit()!=OrigNPC_HV)
endfunction
function OrigNPC_G7E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_G8E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_G6E(),OrigNPC_G7E())
endfunction
function OrigNPC_G9E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_G5E(),OrigNPC_G8E())
endfunction
function OrigNPC_HVE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_GV)))
endfunction
function OrigNPC_HEE takes nothing returns boolean
return(GetFilterUnit()!=OrigNPC_HV)
endfunction
function OrigNPC_HXE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_HOE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_HEE(),OrigNPC_HXE())
endfunction
function OrigNPC_HRE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_HVE(),OrigNPC_HOE())
endfunction
function OrigNPC_HIE takes nothing returns boolean
return(IsUnitType(GetEnumUnit(),UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_HAE takes nothing returns boolean
return(IsUnitIllusion(GetEnumUnit()))
endfunction
function OrigNPC_HNE takes nothing returns nothing
call RemoveLocation(OrigNPC_AE)
set OrigNPC_LG[0]=GetUnitLoc(GetEnumUnit())
if(OrigNPC_HAE())then
call KillUnit(GetEnumUnit())
else
if(OrigNPC_HIE())then
call UnitDamageTargetBJ(OrigNPC_GV,GetEnumUnit(),1000.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call UnitDamageTargetBJ(OrigNPC_GV,GetEnumUnit(),2000.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
endif
call AddSpecialEffectLocBJ(OrigNPC_LG[0],"Abilities\\Weapons\\ChimaeraLightningMissile\\ChimaeraLightningMissile.mdl")
set OrigNPC_CO[5]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_LG[0],"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
set OrigNPC_CO[6]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_LG[0],"Abilities\\Weapons\\ChimaeraLightningMissile\\ChimaeraLightningMissile.mdl")
set OrigNPC_CO[7]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_LG[0],"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
set OrigNPC_CO[8]=bj_lastCreatedEffect
call RemoveLocation(OrigNPC_LG[0])
call TriggerSleepAction(2)
call DestroyEffect(OrigNPC_CO[1])
call DestroyEffect(OrigNPC_CO[2])
call DestroyEffect(OrigNPC_CO[3])
call DestroyEffect(OrigNPC_CO[4])
call DestroyEffect(OrigNPC_CO[5])
call DestroyEffect(OrigNPC_CO[6])
call DestroyEffect(OrigNPC_CO[7])
call DestroyEffect(OrigNPC_CO[8])
endfunction
function OrigNPC_HBE takes nothing returns boolean
return(IsUnitType(GetEnumUnit(),UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_HCE takes nothing returns boolean
return(IsUnitIllusion(GetEnumUnit()))
endfunction
function OrigNPC_HDE takes nothing returns nothing
call RemoveLocation(OrigNPC_AE)
set OrigNPC_LG[0]=GetUnitLoc(GetEnumUnit())
if(OrigNPC_HCE())then
call KillUnit(GetEnumUnit())
else
if(OrigNPC_HBE())then
call UnitDamageTargetBJ(OrigNPC_GV,GetEnumUnit(),800.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call UnitDamageTargetBJ(OrigNPC_GV,GetEnumUnit(),1500.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
endif
call AddSpecialEffectLocBJ(OrigNPC_LG[0],"Abilities\\Weapons\\ChimaeraLightningMissile\\ChimaeraLightningMissile.mdl")
set OrigNPC_CO[5]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_LG[0],"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
set OrigNPC_CO[6]=bj_lastCreatedEffect
call RemoveLocation(OrigNPC_LG[0])
call TriggerSleepAction(2)
call DestroyEffect(OrigNPC_CO[1])
call DestroyEffect(OrigNPC_CO[2])
call DestroyEffect(OrigNPC_CO[3])
call DestroyEffect(OrigNPC_CO[4])
call DestroyEffect(OrigNPC_CO[5])
call DestroyEffect(OrigNPC_CO[6])
endfunction
function OrigNPC_HFE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01D',OrigNPC_GV)==2)
endfunction
function OrigNPC_HGE takes nothing returns boolean
return(IsUnitType(GetEnumUnit(),UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_HHE takes nothing returns boolean
return(IsUnitIllusion(GetEnumUnit()))
endfunction
function OrigNPC_HJE takes nothing returns nothing
call RemoveLocation(OrigNPC_AE)
set OrigNPC_LG[0]=GetUnitLoc(GetEnumUnit())
if(OrigNPC_HHE())then
call KillUnit(GetEnumUnit())
else
if(OrigNPC_HGE())then
call UnitDamageTargetBJ(OrigNPC_GV,GetEnumUnit(),600.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call UnitDamageTargetBJ(OrigNPC_GV,GetEnumUnit(),1000.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
endif
call AddSpecialEffectLocBJ(OrigNPC_LG[0],"Abilities\\Weapons\\ChimaeraLightningMissile\\ChimaeraLightningMissile.mdl")
set OrigNPC_CO[5]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_LG[0],"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
set OrigNPC_CO[6]=bj_lastCreatedEffect
call RemoveLocation(OrigNPC_LG[0])
call TriggerSleepAction(2)
call DestroyEffect(OrigNPC_CO[1])
call DestroyEffect(OrigNPC_CO[2])
call DestroyEffect(OrigNPC_CO[3])
call DestroyEffect(OrigNPC_CO[4])
call DestroyEffect(OrigNPC_CO[5])
call DestroyEffect(OrigNPC_CO[6])
endfunction
function OrigNPC_HKE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01D',OrigNPC_GV)==1)
endfunction
function OrigNPC_HLE takes nothing returns nothing
set OrigNPC_GV=GetTriggerUnit()
set OrigNPC_HV=GetSpellTargetUnit()
set OrigNPC_LG[0]=GetUnitLoc(OrigNPC_GV)
set OrigNPC_LG[1]=GetUnitLoc(OrigNPC_HV)
set OrigNPC_MG=DistanceBetweenPoints(OrigNPC_LG[0],OrigNPC_LG[1])
call PlaySoundOnUnitBJ(OrigNPC_Q0,'d',OrigNPC_GV)
set OrigNPC_WG[1]=bj_lastPlayedSound
call AddSpecialEffectTargetUnitBJ("left hand",OrigNPC_GV,"Abilities\\Spells\\Orc\\Purge\\PurgeBuffTarget.mdl")
set OrigNPC_CO[9]=bj_lastCreatedEffect
call TriggerSleepAction(.02)
call PauseUnit(OrigNPC_GV,true)
call PauseUnit(OrigNPC_HV,true)
call AddSpecialEffectTargetUnitBJ("left hand",OrigNPC_GV,"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
set OrigNPC_CO[1]=bj_lastCreatedEffect
call SetUnitFacingToFaceUnitTimed(OrigNPC_GV,OrigNPC_HV,0)
call AddSpecialEffectTargetUnitBJ("left hand",OrigNPC_GV,"Abilities\\Spells\\Orc\\Purge\\PurgeBuffTarget.mdl")
set OrigNPC_CO[0]=bj_lastCreatedEffect
call TriggerWaitForSound(OrigNPC_WG[0],.05)
call PlaySoundOnUnitBJ(OrigNPC_P0,'d',OrigNPC_GV)
call SetUnitPathing(OrigNPC_GV,false)
if(OrigNPC_GPE())then
call SetUnitAnimationByIndex(OrigNPC_GV,5)
else
call SetUnitAnimation(OrigNPC_GV,"spell Death")
endif
call EnableTrigger(OrigNPC_F5)
call TriggerSleepAction((OrigNPC_MG/ 600.))
call DisableTrigger(OrigNPC_F5)
call RemoveLocation(OrigNPC_LG[0])
call RemoveLocation(OrigNPC_LG[1])
call DestroyEffect(OrigNPC_CO[0])
call DestroyEffect(OrigNPC_CO[1])
call DestroyEffect(OrigNPC_CO[9])
call StopSoundBJ(OrigNPC_WG[1],true)
call PlaySoundOnUnitBJ(OrigNPC_G0,'d',OrigNPC_HV)
if(OrigNPC_GQE())then
call SetUnitAnimation(OrigNPC_GV,"Attack")
else
call SetUnitAnimation(OrigNPC_GV,"spell Dissipate")
endif
set OrigNPC_AE=GetUnitLoc(OrigNPC_HV)
call AddSpecialEffectLocBJ(OrigNPC_AE,"Abilities\\Spells\\Human\\Thunderclap\\ThunderClapCaster.mdl")
set OrigNPC_CO[1]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_AE,"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
set OrigNPC_CO[2]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_AE,"Abilities\\Spells\\Human\\ManaFlare\\ManaFlareBoltImpact.mdl")
set OrigNPC_CO[3]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_AE,"Abilities\\Spells\\Other\\Stampede\\StampedeMissileDeath.mdl")
set OrigNPC_CO[4]=bj_lastCreatedEffect
call CreateNUnitsAtLoc(1,'h019',GetOwningPlayer(OrigNPC_GV),OrigNPC_AE,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h019',GetOwningPlayer(OrigNPC_GV),OrigNPC_AE,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02I',GetOwningPlayer(OrigNPC_GV),OrigNPC_AE,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02I',GetOwningPlayer(OrigNPC_GV),OrigNPC_AE,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02I',GetOwningPlayer(OrigNPC_GV),OrigNPC_AE,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
if(OrigNPC_G_E())then
if(OrigNPC_GWE())then
call UnitDamageTargetBJ(OrigNPC_GV,OrigNPC_HV,1000.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_GYE())then
call UnitDamageTargetBJ(OrigNPC_GV,OrigNPC_HV,1500.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_GZE())then
call UnitDamageTargetBJ(OrigNPC_GV,OrigNPC_HV,2000.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
else
if(OrigNPC_GSE())then
call UnitDamageTargetBJ(OrigNPC_GV,OrigNPC_HV,1500.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_GTE())then
call UnitDamageTargetBJ(OrigNPC_GV,OrigNPC_HV,2000.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_GUE())then
call UnitDamageTargetBJ(OrigNPC_GV,OrigNPC_HV,2500.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
endif
if(OrigNPC_HKE())then
set OrigNPC_CE=OrigNPC_PIV(400.,OrigNPC_AE,Condition(function OrigNPC_G4E))
call ForGroupBJ(OrigNPC_CE,function OrigNPC_HJE)
else
if(OrigNPC_HFE())then
set OrigNPC_CE=OrigNPC_PIV(500.,OrigNPC_AE,Condition(function OrigNPC_HRE))
call ForGroupBJ(OrigNPC_CE,function OrigNPC_HDE)
else
set OrigNPC_CE=OrigNPC_PIV(600.,OrigNPC_AE,Condition(function OrigNPC_G9E))
call ForGroupBJ(OrigNPC_CE,function OrigNPC_HNE)
endif
endif
call SetUnitAnimation(OrigNPC_GV,"Stand Ready")
call SetUnitPathing(OrigNPC_GV,true)
call PauseUnit(OrigNPC_HV,false)
call PauseUnit(OrigNPC_GV,false)
endfunction
function OrigNPC_HPE takes nothing returns nothing
set OrigNPC_LG[2]=GetUnitLoc(OrigNPC_GV)
set OrigNPC_LG[3]=GetUnitLoc(OrigNPC_HV)
set OrigNPC_LG[4]=OrigNPC_M3V(OrigNPC_LG[2],20.,AngleBetweenPoints(OrigNPC_LG[2],OrigNPC_LG[3]))
call SetUnitPositionLoc(OrigNPC_GV,OrigNPC_LG[4])
call RemoveLocation(OrigNPC_LG[2])
call RemoveLocation(OrigNPC_LG[3])
call RemoveLocation(OrigNPC_LG[4])
endfunction
function OrigNPC_HSE takes nothing returns boolean
return(GetSpellAbilityId()=='A01D')and(GetTriggerUnit()==OrigNPC_JZV)
endfunction
function OrigNPC_HTE takes nothing returns boolean
return(OrigNPC_HSE())
endfunction
function OrigNPC_HUE takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='H00S')
endfunction
function OrigNPC_HWE takes nothing returns nothing
call TriggerSleepAction(.01)
if(OrigNPC_HUE())then
call SetUnitAnimation(GetTriggerUnit(),"spell channel")
else
call SetUnitAnimation(GetTriggerUnit(),"Spell Attack")
endif
call PlaySoundOnUnitBJ(OrigNPC_HY,'d',GetTriggerUnit())
set OrigNPC_WG[0]=bj_lastPlayedSound
endfunction
function OrigNPC_HZE takes nothing returns boolean
return(GetSpellAbilityId()=='A01D')and(GetTriggerUnit()!=OrigNPC_JZV)
endfunction
function OrigNPC_H_E takes nothing returns boolean
return(OrigNPC_HZE())
endfunction
function OrigNPC_H0E takes nothing returns boolean
return(IsUnitType(OrigNPC_QG,UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_H1E takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_PG)))
endfunction
function OrigNPC_H2E takes nothing returns boolean
return(GetFilterUnit()!=OrigNPC_QG)
endfunction
function OrigNPC_H3E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_H4E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_H2E(),OrigNPC_H3E())
endfunction
function OrigNPC_H5E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_H1E(),OrigNPC_H4E())
endfunction
function OrigNPC_H6E takes nothing returns boolean
return(IsUnitType(GetEnumUnit(),UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_H7E takes nothing returns boolean
return(IsUnitIllusion(GetEnumUnit()))
endfunction
function OrigNPC_H8E takes nothing returns nothing
call RemoveLocation(OrigNPC_AE)
set OrigNPC_SG[0]=GetUnitLoc(GetEnumUnit())
call UnitDamageTargetBJ(OrigNPC_PG,GetEnumUnit(),900.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
if(OrigNPC_H7E())then
call KillUnit(GetEnumUnit())
else
if(OrigNPC_H6E())then
call UnitDamageTargetBJ(OrigNPC_PG,GetEnumUnit(),1000.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call UnitDamageTargetBJ(OrigNPC_PG,GetEnumUnit(),2000.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
endif
call AddSpecialEffectLocBJ(OrigNPC_SG[0],"Abilities\\Weapons\\ChimaeraLightningMissile\\ChimaeraLightningMissile.mdl")
set OrigNPC_UG[5]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_SG[0],"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
set OrigNPC_UG[6]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_SG[0],"Abilities\\Weapons\\ChimaeraLightningMissile\\ChimaeraLightningMissile.mdl")
set OrigNPC_UG[7]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_SG[0],"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
set OrigNPC_UG[8]=bj_lastCreatedEffect
call TriggerSleepAction(2)
call DestroyEffect(OrigNPC_UG[1])
call DestroyEffect(OrigNPC_UG[2])
call DestroyEffect(OrigNPC_UG[3])
call DestroyEffect(OrigNPC_UG[4])
call DestroyEffect(OrigNPC_UG[5])
call DestroyEffect(OrigNPC_UG[6])
call DestroyEffect(OrigNPC_UG[7])
call DestroyEffect(OrigNPC_UG[8])
call RemoveLocation(OrigNPC_SG[0])
endfunction
function OrigNPC_H9E takes nothing returns nothing
set OrigNPC_PG=GetTriggerUnit()
set OrigNPC_QG=GetSpellTargetUnit()
set OrigNPC_SG[0]=GetUnitLoc(OrigNPC_PG)
set OrigNPC_SG[1]=GetUnitLoc(OrigNPC_QG)
set OrigNPC_TG=DistanceBetweenPoints(OrigNPC_SG[0],OrigNPC_SG[1])
call PlaySoundOnUnitBJ(OrigNPC_Q0,'d',OrigNPC_PG)
set OrigNPC_WG[3]=bj_lastPlayedSound
call TriggerSleepAction(.02)
call PauseUnit(OrigNPC_PG,true)
call PauseUnit(OrigNPC_QG,true)
call SetUnitFacingToFaceUnitTimed(OrigNPC_PG,OrigNPC_QG,0)
call TriggerWaitForSound(OrigNPC_WG[2],.05)
call PlaySoundOnUnitBJ(OrigNPC_M0,'d',OrigNPC_PG)
call SetUnitPathing(OrigNPC_PG,false)
call SetUnitAnimation(OrigNPC_PG,"Spell three")
call EnableTrigger(OrigNPC_J5)
call TriggerSleepAction((OrigNPC_TG/ 600.))
call DisableTrigger(OrigNPC_J5)
call RemoveLocation(OrigNPC_SG[0])
call RemoveLocation(OrigNPC_SG[1])
call StopSoundBJ(OrigNPC_WG[3],true)
call PlaySoundOnUnitBJ(OrigNPC_G0,'d',OrigNPC_QG)
call SetUnitAnimation(OrigNPC_PG,"Spell Slam")
set OrigNPC_AE=GetUnitLoc(OrigNPC_QG)
call AddSpecialEffectLocBJ(OrigNPC_AE,"Abilities\\Spells\\Human\\Thunderclap\\ThunderClapCaster.mdl")
set OrigNPC_UG[1]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_AE,"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
set OrigNPC_UG[2]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_AE,"Abilities\\Spells\\Human\\ManaFlare\\ManaFlareBoltImpact.mdl")
set OrigNPC_UG[3]=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_AE,"Abilities\\Spells\\Other\\Stampede\\StampedeMissileDeath.mdl")
set OrigNPC_UG[4]=bj_lastCreatedEffect
call CreateNUnitsAtLoc(1,'h019',GetOwningPlayer(OrigNPC_PG),OrigNPC_AE,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h019',GetOwningPlayer(OrigNPC_PG),OrigNPC_AE,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02I',GetOwningPlayer(OrigNPC_PG),OrigNPC_AE,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02I',GetOwningPlayer(OrigNPC_PG),OrigNPC_AE,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02I',GetOwningPlayer(OrigNPC_PG),OrigNPC_AE,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
if(OrigNPC_H0E())then
call UnitDamageTargetBJ(OrigNPC_PG,OrigNPC_QG,2000.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call UnitDamageTargetBJ(OrigNPC_PG,OrigNPC_QG,3000.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
set OrigNPC_CE=OrigNPC_PIV(500.,OrigNPC_AE,Condition(function OrigNPC_H5E))
call ForGroupBJ(OrigNPC_CE,function OrigNPC_H8E)
call SetUnitAnimation(OrigNPC_PG,"Stand Ready")
call SetUnitPathing(OrigNPC_PG,true)
call PauseUnit(OrigNPC_PG,false)
call PauseUnit(OrigNPC_QG,false)
endfunction
function OrigNPC_JEE takes nothing returns nothing
set OrigNPC_SG[2]=GetUnitLoc(OrigNPC_PG)
set OrigNPC_SG[3]=GetUnitLoc(OrigNPC_QG)
set OrigNPC_SG[4]=OrigNPC_M3V(OrigNPC_SG[2],20.,AngleBetweenPoints(OrigNPC_SG[2],OrigNPC_SG[3]))
call SetUnitPositionLoc(OrigNPC_PG,OrigNPC_SG[4])
call RemoveLocation(OrigNPC_SG[2])
call RemoveLocation(OrigNPC_SG[3])
call RemoveLocation(OrigNPC_SG[4])
endfunction
function OrigNPC_JOE takes nothing returns boolean
return(GetSpellAbilityId()=='A01D')and(GetTriggerUnit()!=OrigNPC_JZV)
endfunction
function OrigNPC_JRE takes nothing returns boolean
return(OrigNPC_JOE())
endfunction
function OrigNPC_JIE takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitAnimation(GetTriggerUnit(),"Spell two")
call PlaySoundOnUnitBJ(OrigNPC_S0,'d',GetTriggerUnit())
set OrigNPC_WG[2]=bj_lastPlayedSound
endfunction
function OrigNPC_JNE takes nothing returns boolean
return(GetSpellAbilityId()=='A01M')
endfunction
function OrigNPC_JBE takes nothing returns nothing
set OrigNPC_AE=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),500.,.0)
set OrigNPC_BE=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),500.,90.)
set OrigNPC_DR=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),500.,180.)
set OrigNPC_KR=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),500.,270.)
call CreateNUnitsAtLoc(1,'e002',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(15.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'e002',GetOwningPlayer(GetTriggerUnit()),OrigNPC_BE,bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(15.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'e002',GetOwningPlayer(GetTriggerUnit()),OrigNPC_DR,bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(15.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'e002',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(15.,'BTLF',bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_AE)
call RemoveLocation(OrigNPC_BE)
call RemoveLocation(OrigNPC_DR)
call RemoveLocation(OrigNPC_KR)
endfunction
function OrigNPC_JDE takes nothing returns boolean
return(GetSpellAbilityId()=='A02A')
endfunction
function OrigNPC_JFE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_YR)))
endfunction
function OrigNPC_JGE takes nothing returns boolean
return(IsUnitDeadBJ(GetFilterUnit())==false)
endfunction
function OrigNPC_JHE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_JJE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_JGE(),OrigNPC_JHE())
endfunction
function OrigNPC_JKE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_JFE(),OrigNPC_JJE())
endfunction
function OrigNPC_JLE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_YR)))
endfunction
function OrigNPC_JME takes nothing returns boolean
return(IsUnitDeadBJ(GetFilterUnit())==false)
endfunction
function OrigNPC_JPE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_JQE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_JME(),OrigNPC_JPE())
endfunction
function OrigNPC_JSE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_JLE(),OrigNPC_JQE())
endfunction
function OrigNPC_JTE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_YR)))
endfunction
function OrigNPC_JUE takes nothing returns boolean
return(IsUnitDeadBJ(GetFilterUnit())==false)
endfunction
function OrigNPC_JWE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_JYE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_JUE(),OrigNPC_JWE())
endfunction
function OrigNPC_JZE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_JTE(),OrigNPC_JYE())
endfunction
function OrigNPC_J_E takes nothing returns nothing
set OrigNPC_ZR[2]=GetUnitLoc(GetEnumUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h01R',GetOwningPlayer(OrigNPC_YR),OrigNPC_ZR[1],OrigNPC_ZR[2])
call UnitAddAbility(bj_lastCreatedUnit,'A02G')
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD007F,GetEnumUnit())
call RemoveLocation(OrigNPC_ZR[2])
endfunction
function OrigNPC_J0E takes nothing returns nothing
set OrigNPC_ZR[2]=GetUnitLoc(GetEnumUnit())
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_ZR[2],50.,.0)
call CreateNUnitsAtLocFacingLocBJ(1,'v00D',GetOwningPlayer(OrigNPC_YR),OrigNPC_ZR[2],OrigNPC_ZR[2])
call GroupAddUnit(OrigNPC_JF,bj_lastCreatedUnit)
call UnitRemoveAbility(bj_lastCreatedUnit,'S008')
call UnitAddAbility(bj_lastCreatedUnit,'A02Y')
call UnitAddAbility(bj_lastCreatedUnit,'S02C')
call CreateNUnitsAtLocFacingLocBJ(1,'v00D',GetOwningPlayer(OrigNPC_YR),OrigNPC_BE,OrigNPC_ZR[2])
call GroupAddUnit(OrigNPC_JF,bj_lastCreatedUnit)
call UnitRemoveAbility(bj_lastCreatedUnit,'S008')
call UnitAddAbility(bj_lastCreatedUnit,'A02Y')
call UnitAddAbility(bj_lastCreatedUnit,'S02C')
call RemoveLocation(OrigNPC_ZR[2])
call RemoveLocation(OrigNPC_BE)
endfunction
function OrigNPC_J1E takes nothing returns boolean
return(CountUnitsInGroup(OrigNPC_VI[2])!=0)
endfunction
function OrigNPC_J2E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A02A',OrigNPC_YR)==3)
endfunction
function OrigNPC_J3E takes nothing returns nothing
set OrigNPC_ZR[2]=GetUnitLoc(GetEnumUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h01R',GetOwningPlayer(OrigNPC_YR),OrigNPC_ZR[1],OrigNPC_ZR[2])
call UnitAddAbility(bj_lastCreatedUnit,'A02G')
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD007F,GetEnumUnit())
call RemoveLocation(OrigNPC_ZR[2])
endfunction
function OrigNPC_J4E takes nothing returns nothing
set OrigNPC_ZR[2]=GetUnitLoc(GetEnumUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'v00D',GetOwningPlayer(OrigNPC_YR),OrigNPC_ZR[2],OrigNPC_ZR[1])
call GroupAddUnit(OrigNPC_JF,bj_lastCreatedUnit)
call UnitRemoveAbility(bj_lastCreatedUnit,'S008')
call UnitAddAbility(bj_lastCreatedUnit,'A02Y')
call UnitAddAbility(bj_lastCreatedUnit,'S02C')
call RemoveLocation(OrigNPC_ZR[2])
endfunction
function OrigNPC_J5E takes nothing returns boolean
return(CountUnitsInGroup(OrigNPC_VI[1])!=0)
endfunction
function OrigNPC_J6E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A02A',OrigNPC_YR)==2)
endfunction
function OrigNPC_J7E takes nothing returns nothing
set OrigNPC_ZR[2]=GetUnitLoc(GetEnumUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h01R',GetOwningPlayer(OrigNPC_YR),OrigNPC_ZR[1],OrigNPC_ZR[2])
call UnitAddAbility(bj_lastCreatedUnit,'A02G')
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD007F,GetEnumUnit())
call RemoveLocation(OrigNPC_ZR[2])
endfunction
function OrigNPC_J8E takes nothing returns nothing
set OrigNPC_ZR[2]=GetUnitLoc(GetEnumUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'v00D',GetOwningPlayer(OrigNPC_YR),OrigNPC_ZR[2],OrigNPC_ZR[2])
call GroupAddUnit(OrigNPC_JF,bj_lastCreatedUnit)
call UnitRemoveAbility(bj_lastCreatedUnit,'S008')
call UnitAddAbility(bj_lastCreatedUnit,'A02Y')
call UnitAddAbility(bj_lastCreatedUnit,'S02C')
call RemoveLocation(OrigNPC_ZR[2])
endfunction
function OrigNPC_J9E takes nothing returns boolean
return(CountUnitsInGroup(OrigNPC_VI[0])!=0)
endfunction
function OrigNPC_KVE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A02A',OrigNPC_YR)==1)
endfunction
function OrigNPC_KEE takes nothing returns nothing
call UnitRemoveAbility(GetEnumUnit(),'S02C')
call UnitRemoveAbility(GetEnumUnit(),'A02Y')
call UnitAddAbility(GetEnumUnit(),'S008')
endfunction
function OrigNPC_KXE takes nothing returns nothing
set OrigNPC_YR=GetTriggerUnit()
set OrigNPC_ZR[0]=GetSpellTargetLoc()
set OrigNPC_ZR[1]=GetUnitLoc(OrigNPC_YR)
call PauseUnit(OrigNPC_YR,true)
call SetUnitAnimationByIndex(OrigNPC_YR,1)
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(OrigNPC_YR,3)
call PlaySoundOnUnitBJ(OrigNPC_I2,'d',OrigNPC_YR)
set OrigNPC_VI[0]=OrigNPC_PIV(150.,OrigNPC_ZR[0],Condition(function OrigNPC_JKE))
set OrigNPC_VI[1]=OrigNPC_PIV(300.,OrigNPC_ZR[0],Condition(function OrigNPC_JSE))
set OrigNPC_VI[2]=OrigNPC_PIV(300.,OrigNPC_ZR[0],Condition(function OrigNPC_JZE))
if(OrigNPC_KVE())then
call ForGroupBJ(OrigNPC_VI[0],function OrigNPC_J7E)
if(OrigNPC_J9E())then
call TriggerSleepAction(.75)
set OrigNPC_ZR[3]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[0]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[3])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[0]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[3])
set OrigNPC_ZR[3]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[0]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[3])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[1]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[3])
set OrigNPC_ZR[3]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[0]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[3])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[2]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[3])
set OrigNPC_ZR[3]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[0]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[3])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[3]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[3])
set OrigNPC_ZR[3]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[0]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[3])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[4]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[3])
call ForGroupBJ(OrigNPC_VI[0],function OrigNPC_J8E)
call TriggerSleepAction(.75)
call DestroyLightning(OrigNPC_EI[0])
call DestroyLightning(OrigNPC_EI[1])
call DestroyLightning(OrigNPC_EI[2])
call DestroyLightning(OrigNPC_EI[3])
call DestroyLightning(OrigNPC_EI[4])
endif
else
if(OrigNPC_J6E())then
call ForGroupBJ(OrigNPC_VI[1],function OrigNPC_J3E)
if(OrigNPC_J5E())then
call TriggerSleepAction(.75)
set OrigNPC_ZR[4]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[1]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[4])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[0]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[4])
set OrigNPC_ZR[4]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[1]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[4])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[1]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[4])
set OrigNPC_ZR[4]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[1]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[4])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[2]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[4])
set OrigNPC_ZR[4]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[1]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[4])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[3]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[4])
set OrigNPC_ZR[4]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[1]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[4])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[4]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[4])
call ForGroupBJ(OrigNPC_VI[1],function OrigNPC_J4E)
call TriggerSleepAction(.75)
call DestroyLightning(OrigNPC_EI[0])
call DestroyLightning(OrigNPC_EI[1])
call DestroyLightning(OrigNPC_EI[2])
call DestroyLightning(OrigNPC_EI[3])
call DestroyLightning(OrigNPC_EI[4])
endif
else
if(OrigNPC_J2E())then
call ForGroupBJ(OrigNPC_VI[2],function OrigNPC_J_E)
if(OrigNPC_J1E())then
call TriggerSleepAction(.75)
set OrigNPC_ZR[5]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[2]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[5])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[0]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[5])
set OrigNPC_ZR[5]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[2]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[5])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[1]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[5])
set OrigNPC_ZR[5]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[2]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[5])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[2]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[5])
set OrigNPC_ZR[5]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[2]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[5])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[3]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[5])
set OrigNPC_ZR[5]=GetUnitLoc(GroupPickRandomUnit(OrigNPC_VI[2]))
call AddLightningLoc("LEAS",OrigNPC_ZR[1],OrigNPC_ZR[5])
call SetLightningColor(bj_lastCreatedLightning,1.,.5,.0,1)
call MoveLightningEx(bj_lastCreatedLightning,true,.0,.0,200.,.0,.0,200.)
set OrigNPC_EI[4]=bj_lastCreatedLightning
call RemoveLocation(OrigNPC_ZR[5])
call ForGroupBJ(OrigNPC_VI[2],function OrigNPC_J0E)
call TriggerSleepAction(.75)
call DestroyLightning(OrigNPC_EI[0])
call DestroyLightning(OrigNPC_EI[1])
call DestroyLightning(OrigNPC_EI[2])
call DestroyLightning(OrigNPC_EI[3])
call DestroyLightning(OrigNPC_EI[4])
endif
endif
endif
endif
call PauseUnit(OrigNPC_YR,false)
call RemoveLocation(OrigNPC_ZR[0])
call RemoveLocation(OrigNPC_ZR[1])
call DestroyGroup(OrigNPC_VI[0])
call DestroyGroup(OrigNPC_VI[1])
call DestroyGroup(OrigNPC_VI[2])
call EnableTrigger(OrigNPC_P5)
call TriggerSleepAction(3.)
call DisableTrigger(OrigNPC_P5)
call TriggerSleepAction(.1)
call ForGroupBJ(OrigNPC_JF,function OrigNPC_KEE)
endfunction
function OrigNPC_KRE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_YR)))
endfunction
function OrigNPC_KIE takes nothing returns boolean
return(IsUnitAliveBJ(GetFilterUnit()))
endfunction
function OrigNPC_KAE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_KNE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_KIE(),OrigNPC_KAE())
endfunction
function OrigNPC_KBE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_KRE(),OrigNPC_KNE())
endfunction
function OrigNPC_KCE takes nothing returns boolean
return(IsUnitAliveBJ(GetEnumUnit()))
endfunction
function OrigNPC_KDE takes nothing returns nothing
if(OrigNPC_KCE())then
set OrigNPC_KR=GetUnitLoc(GetEnumUnit())
set OrigNPC_HE=OrigNPC_PIV(150.,OrigNPC_KR,Condition(function OrigNPC_KBE))
set OrigNPC_DR=GetUnitLoc(GroupPickRandomUnit(OrigNPC_HE))
call SetUnitPositionLocFacingBJ(GetEnumUnit(),OrigNPC_DR,AngleBetweenPoints(OrigNPC_DR,OrigNPC_KR))
call DestroyGroup(OrigNPC_HE)
call RemoveLocation(OrigNPC_DR)
call RemoveLocation(OrigNPC_KR)
endif
endfunction
function OrigNPC_KFE takes nothing returns nothing
call ForGroupBJ(OrigNPC_JF,function OrigNPC_KDE)
endfunction
function OrigNPC_KHE takes nothing returns boolean
return(GetSpellAbilityId()=='A02A')
endfunction
function OrigNPC_KJE takes nothing returns nothing
call SetUnitAnimationByIndex(GetTriggerUnit(),1)
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),1)
endfunction
function OrigNPC_KWE takes nothing returns boolean
return(GetSpellAbilityId()=='A01E')
endfunction
function OrigNPC_KYE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_KZE takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,GetFilterUnit())!=.0)
endfunction
function OrigNPC_K_E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_KYE(),OrigNPC_KZE())
endfunction
function OrigNPC_K0E takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_K1E takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,GetFilterUnit())!=.0)
endfunction
function OrigNPC_K2E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_K0E(),OrigNPC_K1E())
endfunction
function OrigNPC_K3E takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_K4E takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,GetFilterUnit())!=.0)
endfunction
function OrigNPC_K5E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_K3E(),OrigNPC_K4E())
endfunction
function OrigNPC_K6E takes nothing returns nothing
set OrigNPC_ER=GetEnumUnit()
set OrigNPC_ZO=GetUnitLoc(OrigNPC_ER)
call CreateNUnitsAtLocFacingLocBJ(1,'h02M',GetOwningPlayer(GetTriggerUnit()),OrigNPC_ZO,OrigNPC_ZO)
call UnitApplyTimedLifeBJ(4.,'BTLF',bj_lastCreatedUnit)
call UnitAddAbility(bj_lastCreatedUnit,'A02C')
call SetUnitPositionLoc(bj_lastCreatedUnit,OrigNPC_XR)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD0207,OrigNPC_ER)
call CreateNUnitsAtLocFacingLocBJ(1,'h02M',GetOwningPlayer(GetTriggerUnit()),OrigNPC_ZO,OrigNPC_ZO)
call UnitApplyTimedLifeBJ(4.,'BTLF',bj_lastCreatedUnit)
call UnitAddAbility(bj_lastCreatedUnit,'A02C')
call SetUnitPositionLoc(bj_lastCreatedUnit,OrigNPC_XR)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD0207,OrigNPC_ER)
call CreateNUnitsAtLocFacingLocBJ(1,'h02M',GetOwningPlayer(GetTriggerUnit()),OrigNPC_ZO,OrigNPC_ZO)
call UnitApplyTimedLifeBJ(4.,'BTLF',bj_lastCreatedUnit)
call UnitAddAbility(bj_lastCreatedUnit,'A02C')
call SetUnitPositionLoc(bj_lastCreatedUnit,OrigNPC_XR)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD0207,OrigNPC_ER)
call RemoveLocation(OrigNPC_ZO)
endfunction
function OrigNPC_K7E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01E',GetTriggerUnit())==3)
endfunction
function OrigNPC_K8E takes nothing returns nothing
set OrigNPC_ER=GetEnumUnit()
set OrigNPC_ZO=GetUnitLoc(OrigNPC_ER)
call CreateNUnitsAtLocFacingLocBJ(1,'h02M',GetOwningPlayer(GetTriggerUnit()),OrigNPC_ZO,OrigNPC_ZO)
call UnitApplyTimedLifeBJ(4.,'BTLF',bj_lastCreatedUnit)
call UnitAddAbility(bj_lastCreatedUnit,'A02C')
call SetUnitPositionLoc(bj_lastCreatedUnit,OrigNPC_XR)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD0207,OrigNPC_ER)
call CreateNUnitsAtLocFacingLocBJ(1,'h02M',GetOwningPlayer(GetTriggerUnit()),OrigNPC_ZO,OrigNPC_ZO)
call UnitApplyTimedLifeBJ(4.,'BTLF',bj_lastCreatedUnit)
call UnitAddAbility(bj_lastCreatedUnit,'A02C')
call SetUnitPositionLoc(bj_lastCreatedUnit,OrigNPC_XR)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD0207,OrigNPC_ER)
call RemoveLocation(OrigNPC_ZO)
endfunction
function OrigNPC_K9E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01E',GetTriggerUnit())==2)
endfunction
function OrigNPC_LVE takes nothing returns nothing
set OrigNPC_ER=GetEnumUnit()
set OrigNPC_ZO=GetUnitLoc(OrigNPC_ER)
call CreateNUnitsAtLocFacingLocBJ(1,'h02M',GetOwningPlayer(GetTriggerUnit()),OrigNPC_ZO,OrigNPC_ZO)
call UnitApplyTimedLifeBJ(4.,'BTLF',bj_lastCreatedUnit)
call UnitAddAbility(bj_lastCreatedUnit,'A02C')
call SetUnitPositionLoc(bj_lastCreatedUnit,OrigNPC_XR)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD0207,OrigNPC_ER)
call RemoveLocation(OrigNPC_ZO)
endfunction
function OrigNPC_LEE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01E',GetTriggerUnit())==1)
endfunction
function OrigNPC_LXE takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_LOE takes nothing returns nothing
set OrigNPC_AI=GetTriggerUnit()
set OrigNPC_XR=GetUnitLoc(GetTriggerUnit())
set OrigNPC_YO=GetSpellTargetLoc()
set OrigNPC_WO[0]=OrigNPC_PIV(200.,OrigNPC_YO,Condition(function OrigNPC_K_E))
set OrigNPC_WO[1]=OrigNPC_PIV(275.,OrigNPC_YO,Condition(function OrigNPC_K2E))
set OrigNPC_WO[2]=OrigNPC_PIV(350.,OrigNPC_YO,Condition(function OrigNPC_K5E))
if(OrigNPC_LEE())then
call ForGroupBJ(OrigNPC_WO[0],function OrigNPC_LVE)
else
if(OrigNPC_K9E())then
call ForGroupBJ(OrigNPC_WO[1],function OrigNPC_K8E)
else
if(OrigNPC_K7E())then
call ForGroupBJ(OrigNPC_WO[2],function OrigNPC_K6E)
endif
endif
endif
call RemoveLocation(OrigNPC_XR)
call RemoveLocation(OrigNPC_YO)
call DestroyGroup(OrigNPC_WO[0])
call DestroyGroup(OrigNPC_WO[1])
call DestroyGroup(OrigNPC_WO[2])
set OrigNPC_VR=OrigNPC_PBV('h02M')
call TriggerSleepAction(5.)
call ForGroupBJ(OrigNPC_VR,function OrigNPC_LXE)
call DestroyGroup(OrigNPC_VR)
endfunction
function OrigNPC_LFE takes nothing returns boolean
return(GetSpellAbilityId()=='A008')
endfunction
function OrigNPC_LGE takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_LHE takes nothing returns boolean
return(GetUnitLevel(OrigNPC_JD)>=50)and(GetOwningPlayer(OrigNPC_JD)!=Player(0xC))
endfunction
function OrigNPC_LJE takes nothing returns boolean
return(OrigNPC_LHE())
endfunction
function OrigNPC_LKE takes nothing returns nothing
set OrigNPC_JD=GetTriggerUnit()
set OrigNPC_HD=GetSpellTargetUnit()
set OrigNPC_DD=GetUnitLoc(GetTriggerUnit())
set OrigNPC_FD=GetUnitLoc(GetSpellTargetUnit())
set OrigNPC_GD=AngleBetweenPoints(OrigNPC_DD,OrigNPC_FD)
call CreateNUnitsAtLoc(1,'h01X',GetOwningPlayer(GetTriggerUnit()),OrigNPC_DD,bj_UNIT_FACING)
set OrigNPC_CD[2]=bj_lastCreatedUnit
call CreateNUnitsAtLocFacingLocBJ(1,'h02H',GetOwningPlayer(GetTriggerUnit()),OrigNPC_FD,OrigNPC_FD)
call UnitAddAbility(bj_lastCreatedUnit,'A02M')
call UnitApplyTimedLifeBJ(1.,'BTLF',bj_lastCreatedUnit)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD00CB,GetSpellTargetUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h029',GetOwningPlayer(GetTriggerUnit()),OrigNPC_M3V(OrigNPC_DD,75.,OrigNPC_GD),OrigNPC_FD)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,400.)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD000F,GetSpellTargetUnit())
call SetUnitColor(bj_lastCreatedUnit,ConvertPlayerColor(0xC))
call GroupAddUnit(OrigNPC_KD,bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_FD)
call SetUnitTimeScalePercent(OrigNPC_HD,400.)
call PauseUnit(GetTriggerUnit(),true)
call ShowUnitHide(GetTriggerUnit())
call EnableTrigger(OrigNPC_Y5)
call EnableTrigger(OrigNPC_Z5)
call TriggerSleepAction(4.)
call DisableTrigger(OrigNPC_Y5)
call DisableTrigger(OrigNPC_Z5)
call ForGroupBJ(OrigNPC_KD,function OrigNPC_LGE)
call SetUnitTimeScalePercent(OrigNPC_HD,100.)
if(OrigNPC_LJE())then
call PauseUnit(OrigNPC_HD,true)
call ShowUnitShow(GetTriggerUnit())
call AddSpecialEffectTargetUnitBJ("hand left",OrigNPC_JD,"Abilities\\Weapons\\ZigguratFrostMissile\\ZigguratFrostMissile.mdl")
set OrigNPC_LD=bj_lastCreatedEffect
call SetUnitAnimationByIndex(OrigNPC_JD,5)
call PlaySoundOnUnitBJ(OrigNPC_JZ,'d',OrigNPC_JD)
call TriggerSleepAction(.1)
set OrigNPC_FD=GetUnitLoc(OrigNPC_HD)
set OrigNPC_GD=AngleBetweenPoints(OrigNPC_DD,OrigNPC_FD)
call SetUnitPositionLocFacingLocBJ(OrigNPC_JD,OrigNPC_M3V(OrigNPC_FD,-50.,OrigNPC_GD),OrigNPC_FD)
call TriggerSleepAction(.25)
call SetUnitAnimation(OrigNPC_HD,"death")
call CreateNUnitsAtLoc(1,'h00O',GetOwningPlayer(OrigNPC_JD),OrigNPC_FD,OrigNPC_GD)
call UnitAddAbility(bj_lastCreatedUnit,'Amrf')
call UnitRemoveAbility(bj_lastCreatedUnit,'Amrf')
call SetUnitTimeScalePercent(bj_lastCreatedUnit,200.)
call SetUnitVertexColorBJ(bj_lastCreatedUnit,100.,100.,'d',75.)
call SetUnitFlyHeight(bj_lastCreatedUnit,200.,.0)
set OrigNPC_MD[0]=bj_lastCreatedUnit
call CreateNUnitsAtLoc(1,'h00O',GetOwningPlayer(OrigNPC_JD),OrigNPC_FD,OrigNPC_GD)
call UnitAddAbility(bj_lastCreatedUnit,'Amrf')
call UnitRemoveAbility(bj_lastCreatedUnit,'Amrf')
call SetUnitTimeScalePercent(bj_lastCreatedUnit,50.)
call SetUnitVertexColorBJ(bj_lastCreatedUnit,60.,80.,'d',25.)
call SetUnitFlyHeight(bj_lastCreatedUnit,200.,.0)
set OrigNPC_MD[1]=bj_lastCreatedUnit
call CreateNUnitsAtLoc(1,'h02S',GetOwningPlayer(OrigNPC_JD),OrigNPC_FD,OrigNPC_GD)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,200.)
call UnitApplyTimedLifeBJ(1.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02S',GetOwningPlayer(OrigNPC_JD),OrigNPC_FD,OrigNPC_GD)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,50.)
call UnitApplyTimedLifeBJ(1.25,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02S',GetOwningPlayer(OrigNPC_JD),OrigNPC_FD,OrigNPC_GD)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,100.)
call UnitApplyTimedLifeBJ(1.5,'BTLF',bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_FD)
call RemoveUnit(OrigNPC_CD[2])
call EnableTrigger(OrigNPC_V6)
call TriggerSleepAction(1.)
call RemoveUnit(OrigNPC_MD[1])
call TriggerSleepAction(.5)
call RemoveUnit(OrigNPC_MD[0])
call DisableTrigger(OrigNPC_V6)
call DestroyEffect(OrigNPC_LD)
call PauseUnit(GetTriggerUnit(),false)
call PauseUnit(OrigNPC_HD,false)
else
call SetUnitAnimation(OrigNPC_HD,"death")
call RemoveUnit(OrigNPC_CD[2])
call ShowUnitShow(GetTriggerUnit())
call PauseUnit(GetTriggerUnit(),false)
endif
call RemoveLocation(OrigNPC_DD)
endfunction
function OrigNPC_LME takes nothing returns nothing
set OrigNPC_FD=GetUnitLoc(OrigNPC_HD)
call SetUnitPositionLoc(OrigNPC_HD,OrigNPC_M3V(OrigNPC_FD,2.,OrigNPC_GD))
call AddSpecialEffectLocBJ(OrigNPC_FD,"Abilities\\Weapons\\AncientProtectorMissile\\AncientProtectorMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call RemoveLocation(OrigNPC_FD)
endfunction
function OrigNPC_LQE takes nothing returns nothing
call SetDestAnimationSpeedPercent(GetEnumDestructable(),300.)
call KillDestructable(GetEnumDestructable())
endfunction
function OrigNPC_LSE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A008',GetTriggerUnit())==2)
endfunction
function OrigNPC_LTE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A008',OrigNPC_JD)==1)
endfunction
function OrigNPC_LUE takes nothing returns nothing
set OrigNPC_FD=GetUnitLoc(OrigNPC_HD)
call CreateNUnitsAtLocFacingLocBJ(1,'h029',GetOwningPlayer(OrigNPC_JD),OrigNPC_M3V(OrigNPC_FD,-50.,OrigNPC_GD),OrigNPC_FD)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,600.)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD000F,OrigNPC_HD)
call SetUnitColor(bj_lastCreatedUnit,ConvertPlayerColor(0xC))
call GroupAddUnit(OrigNPC_KD,bj_lastCreatedUnit)
call SetUnitVertexColorBJ(bj_lastCreatedUnit,'d','d','d',75.)
call OrigNPC_M8V(200.,OrigNPC_FD,function OrigNPC_LQE)
if(OrigNPC_LTE())then
call UnitDamageTargetBJ(OrigNPC_JD,OrigNPC_HD,22.5,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitManaBJ(OrigNPC_HD,(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_HD)-22.5))
call SetUnitAnimation(OrigNPC_HD,"death")
else
if(OrigNPC_LSE())then
call UnitDamageTargetBJ(OrigNPC_JD,OrigNPC_HD,30.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitManaBJ(OrigNPC_HD,(GetUnitStateSwap(UNIT_STATE_MANA,GetEnumUnit())-30.))
call SetUnitAnimation(OrigNPC_HD,"death")
else
call UnitDamageTargetBJ(OrigNPC_JD,OrigNPC_HD,37.5,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitManaBJ(OrigNPC_HD,(GetUnitStateSwap(UNIT_STATE_MANA,GetEnumUnit())-37.5))
call SetUnitAnimation(OrigNPC_HD,"death")
endif
endif
call RemoveLocation(OrigNPC_FD)
endfunction
function OrigNPC_LYE takes nothing returns nothing
call SetDestAnimationSpeedPercent(GetEnumDestructable(),300.)
call KillDestructable(GetEnumDestructable())
endfunction
function OrigNPC_LZE takes nothing returns nothing
set OrigNPC_FD=GetUnitLoc(OrigNPC_HD)
call SetUnitPositionLoc(OrigNPC_HD,OrigNPC_M3V(OrigNPC_FD,30.,OrigNPC_GD))
call AddSpecialEffectLocBJ(OrigNPC_FD,"Abilities\\Weapons\\AncientProtectorMissile\\AncientProtectorMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call UnitDamageTargetBJ(OrigNPC_JD,OrigNPC_HD,53.34,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call OrigNPC_M8V(300.,OrigNPC_FD,function OrigNPC_LYE)
call RemoveLocation(OrigNPC_FD)
endfunction
function OrigNPC_L0E takes nothing returns boolean
return(GetSpellAbilityId()=='A02L')
endfunction
function OrigNPC_L1E takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_L2E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_L3E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_L1E(),OrigNPC_L2E())
endfunction
function OrigNPC_L4E takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_L5E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_L6E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_L4E(),OrigNPC_L5E())
endfunction
function OrigNPC_L7E takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_L8E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_L9E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_L7E(),OrigNPC_L8E())
endfunction
function OrigNPC_MVE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A02L',GetTriggerUnit())==2)
endfunction
function OrigNPC_MEE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A02L',GetTriggerUnit())==1)
endfunction
function OrigNPC_MXE takes nothing returns nothing
set OrigNPC_AE=GetUnitLoc(GetEnumUnit())
call SetUnitTimeScalePercent(GetEnumUnit(),300.)
call CreateNUnitsAtLocFacingLocBJ(1,'h029',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AD,OrigNPC_AE)
call RemoveLocation(OrigNPC_AE)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,300.)
call SetUnitVertexColorBJ(bj_lastCreatedUnit,'d','d','d',50.)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD000F,GetEnumUnit())
call SetUnitColor(bj_lastCreatedUnit,ConvertPlayerColor(0xC))
call GroupAddUnit(OrigNPC_BD,bj_lastCreatedUnit)
set OrigNPC_AE=GetUnitLoc(GetEnumUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h02H',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,OrigNPC_AE)
call RemoveLocation(OrigNPC_AE)
call UnitAddAbility(bj_lastCreatedUnit,'A02M')
call UnitApplyTimedLifeBJ(1.,'BTLF',bj_lastCreatedUnit)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD00CB,GetEnumUnit())
endfunction
function OrigNPC_MOE takes nothing returns nothing
call SetUnitTimeScalePercent(GetEnumUnit(),100.)
endfunction
function OrigNPC_MRE takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_MIE takes nothing returns nothing
set OrigNPC_ND=GetTriggerUnit()
set OrigNPC_XD=GetUnitLoc(GetTriggerUnit())
set OrigNPC_OD=GetUnitLoc(GetSpellTargetUnit())
set OrigNPC_ID=AngleBetweenPoints(OrigNPC_XD,OrigNPC_OD)
if(OrigNPC_MEE())then
set OrigNPC_RD=OrigNPC_PIV(100.,OrigNPC_XD,Condition(function OrigNPC_L3E))
else
if(OrigNPC_MVE())then
set OrigNPC_RD=OrigNPC_PIV(200.,OrigNPC_XD,Condition(function OrigNPC_L6E))
else
set OrigNPC_RD=OrigNPC_PIV(300.,OrigNPC_XD,Condition(function OrigNPC_L9E))
endif
endif
call GroupAddUnit(OrigNPC_RD,GetSpellTargetUnit())
call CreateNUnitsAtLoc(1,'h01X',GetOwningPlayer(GetTriggerUnit()),OrigNPC_XD,OrigNPC_ID)
set OrigNPC_CD[0]=bj_lastCreatedUnit
call PauseUnit(GetTriggerUnit(),true)
call ShowUnitHide(GetTriggerUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h029',GetOwningPlayer(GetTriggerUnit()),OrigNPC_M3V(OrigNPC_OD,-100.,OrigNPC_ID),OrigNPC_OD)
set OrigNPC_AD=GetUnitLoc(bj_lastCreatedUnit)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,300.)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD000F,GetSpellTargetUnit())
call SetUnitColor(bj_lastCreatedUnit,ConvertPlayerColor(0xC))
call GroupAddUnit(OrigNPC_BD,bj_lastCreatedUnit)
call ForGroupBJ(OrigNPC_RD,function OrigNPC_MXE)
call EnableTrigger(OrigNPC_X6)
call TriggerSleepAction(4.)
call DisableTrigger(OrigNPC_X6)
call ForGroupBJ(OrigNPC_RD,function OrigNPC_MOE)
call ForGroupBJ(OrigNPC_BD,function OrigNPC_MRE)
call ShowUnitShow(GetTriggerUnit())
call PauseUnit(GetTriggerUnit(),false)
call IssueImmediateOrderById(GetTriggerUnit(),0xD0004)
call RemoveUnit(OrigNPC_CD[0])
call DestroyGroup(OrigNPC_RD)
call RemoveLocation(OrigNPC_AD)
call RemoveLocation(OrigNPC_XD)
call RemoveLocation(OrigNPC_OD)
endfunction
function OrigNPC_MNE takes nothing returns nothing
call SetUnitAnimation(GetEnumUnit(),"death")
call UnitDamageTargetBJ(OrigNPC_ND,GetEnumUnit(),10.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitManaBJ(GetEnumUnit(),(GetUnitStateSwap(UNIT_STATE_MANA,GetEnumUnit())-10.))
endfunction
function OrigNPC_MBE takes nothing returns nothing
call SetUnitAnimation(GetEnumUnit(),"death")
call UnitDamageTargetBJ(OrigNPC_ND,GetEnumUnit(),20.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitManaBJ(GetEnumUnit(),(GetUnitStateSwap(UNIT_STATE_MANA,GetEnumUnit())-20.))
endfunction
function OrigNPC_MCE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A02L',OrigNPC_ND)==3)
endfunction
function OrigNPC_MDE takes nothing returns nothing
call SetUnitAnimation(GetEnumUnit(),"death")
call UnitDamageTargetBJ(OrigNPC_ND,GetEnumUnit(),15.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitManaBJ(GetEnumUnit(),(GetUnitStateSwap(UNIT_STATE_MANA,GetEnumUnit())-15.))
endfunction
function OrigNPC_MFE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A02L',OrigNPC_ND)==2)
endfunction
function OrigNPC_MGE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A02L',OrigNPC_ND)==1)
endfunction
function OrigNPC_MHE takes nothing returns nothing
if(OrigNPC_MGE())then
call ForGroupBJ(OrigNPC_RD,function OrigNPC_MNE)
else
if(OrigNPC_MFE())then
call ForGroupBJ(OrigNPC_RD,function OrigNPC_MDE)
else
if(OrigNPC_MCE())then
call ForGroupBJ(OrigNPC_RD,function OrigNPC_MBE)
endif
endif
endif
endfunction
function OrigNPC_MKE takes nothing returns boolean
return(GetSpellAbilityId()=='A02J')
endfunction
function OrigNPC_MLE takes nothing returns nothing
local unit OrigNPC_MLE_caster=GetTriggerUnit()
local unit OrigNPC_MLE_target=GetSpellTargetUnit()
set OrigNPC_QC=OrigNPC_MLE_caster
set OrigNPC_PC=OrigNPC_MLE_target
call PlaySoundOnUnitBJ(OrigNPC_DZ,'d',OrigNPC_MLE_caster)
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
call CreateNUnitsAtLoc(1,'h01X',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
call RemoveLocation(OrigNPC_AE)
set OrigNPC_CD[1]=bj_lastCreatedUnit
call AddSpecialEffectTargetUnitBJ("hand right",GetTriggerUnit(),"Abilities\\Weapons\\ZigguratFrostMissile\\ZigguratFrostMissile.mdl")
set OrigNPC_MC[0]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("hand left",GetTriggerUnit(),"Abilities\\Weapons\\ZigguratFrostMissile\\ZigguratFrostMissile.mdl")
set OrigNPC_MC[1]=bj_lastCreatedEffect
call SetUnitAnimation(GetTriggerUnit(),"stand ready")
set OrigNPC_MLE_caster=GetTriggerUnit()
set OrigNPC_MLE_target=GetSpellTargetUnit()
call TriggerSleepAction(1.)
call RemoveUnit(OrigNPC_CD[1])
set OrigNPC_SC=GetUnitLoc(OrigNPC_MLE_caster)
set OrigNPC_TC=GetUnitLoc(OrigNPC_MLE_target)
set OrigNPC_UC=AngleBetweenPoints(OrigNPC_SC,OrigNPC_TC)
call SetUnitPositionLocFacingLocBJ(OrigNPC_MLE_caster,OrigNPC_M3V(OrigNPC_TC,-75.,OrigNPC_UC),OrigNPC_TC)
call CreateNUnitsAtLocFacingLocBJ(1,'h02Q',GetOwningPlayer(OrigNPC_MLE_caster),OrigNPC_SC,OrigNPC_TC)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,600.)
call PauseUnit(OrigNPC_MLE_caster,true)
call ShowUnitHide(OrigNPC_MLE_caster)
call SetUnitColor(bj_lastCreatedUnit,ConvertPlayerColor(0xC))
set OrigNPC_WC=bj_lastCreatedUnit
call AddSpecialEffectTargetUnitBJ("hand right",OrigNPC_WC,"Abilities\\Weapons\\ZigguratFrostMissile\\ZigguratFrostMissile.mdl")
set OrigNPC_MC[2]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("hand left",OrigNPC_WC,"Abilities\\Weapons\\ZigguratFrostMissile\\ZigguratFrostMissile.mdl")
set OrigNPC_MC[3]=bj_lastCreatedEffect
call IssueTargetOrderById(OrigNPC_WC,0xD000F,OrigNPC_MLE_target)
call PauseUnit(OrigNPC_MLE_target,true)
call TriggerSleepAction(.35)
call UnitDamageTargetBJ(OrigNPC_MLE_caster,OrigNPC_MLE_target,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitAnimation(OrigNPC_MLE_target,"death")
call TriggerSleepAction(.35)
call UnitDamageTargetBJ(OrigNPC_MLE_caster,OrigNPC_MLE_target,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitAnimation(OrigNPC_MLE_target,"death")
call TriggerSleepAction(.35)
call UnitDamageTargetBJ(OrigNPC_MLE_caster,OrigNPC_MLE_target,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitAnimation(OrigNPC_MLE_target,"death")
call TriggerSleepAction(.35)
call UnitDamageTargetBJ(OrigNPC_MLE_caster,OrigNPC_MLE_target,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitAnimation(OrigNPC_MLE_target,"death")
call TriggerSleepAction(.35)
call UnitDamageTargetBJ(OrigNPC_MLE_caster,OrigNPC_MLE_target,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitAnimation(OrigNPC_MLE_target,"death")
call TriggerSleepAction(.35)
call UnitDamageTargetBJ(OrigNPC_MLE_caster,OrigNPC_MLE_target,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call SetUnitAnimation(OrigNPC_MLE_target,"death")
call DestroyEffect(OrigNPC_MC[2])
call DestroyEffect(OrigNPC_MC[3])
call SetUnitPathing(OrigNPC_WC,false)
set OrigNPC_AE=GetUnitLoc(OrigNPC_WC)
call SetUnitPositionLocFacingLocBJ(OrigNPC_MLE_caster,OrigNPC_AE,OrigNPC_TC)
call RemoveLocation(OrigNPC_AE)
call RemoveUnit(OrigNPC_WC)
call ShowUnitShow(OrigNPC_MLE_caster)
call SetUnitAnimationByIndex(OrigNPC_MLE_caster,6)
call PlaySoundOnUnitBJ(OrigNPC_CZ,'d',OrigNPC_MLE_caster)
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_MLE_caster,"Abilities\\Weapons\\FrostWyrmMissile\\FrostWyrmMissile.mdl")
set OrigNPC_MC[4]=bj_lastCreatedEffect
call TriggerSleepAction(.5)
call DestroyEffect(OrigNPC_MC[0])
call DestroyEffect(OrigNPC_MC[1])
call RemoveLocation(OrigNPC_TC)
call RemoveLocation(OrigNPC_SC)
set OrigNPC_SC=GetUnitLoc(OrigNPC_MLE_caster)
set OrigNPC_TC=GetUnitLoc(OrigNPC_MLE_target)
call CreateNUnitsAtLocFacingLocBJ(1,'h02H',GetOwningPlayer(OrigNPC_MLE_caster),OrigNPC_SC,OrigNPC_QB)
call UnitApplyTimedLifeBJ(3.,'BTLF',bj_lastCreatedUnit)
call UnitAddAbility(bj_lastCreatedUnit,'A02K')
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD009D,OrigNPC_TC)
call DestroyEffect(OrigNPC_MC[4])
call RemoveLocation(OrigNPC_TC)
call PauseUnit(OrigNPC_MLE_caster,true)
call SetUnitAnimationByIndex(OrigNPC_MLE_caster,6)
call SetUnitAnimation(OrigNPC_MLE_target,"death")
call DisableTrigger(OrigNPC_XJV)
call CreateNUnitsAtLoc(1,'h02R',GetOwningPlayer(OrigNPC_MLE_caster),OrigNPC_SC,OrigNPC_UC)
set OrigNPC_YC=bj_lastCreatedUnit
set OrigNPC_ZC=OrigNPC_M3V(GetUnitLoc(OrigNPC_YC),-100.,OrigNPC_UC)
call CreateNUnitsAtLoc(1,'h02R',GetOwningPlayer(OrigNPC_MLE_caster),OrigNPC_ZC,OrigNPC_UC)
set OrigNPC_VD=bj_lastCreatedUnit
call UnitApplyTimedLifeBJ(1.,'BTLF',OrigNPC_YC)
call UnitApplyTimedLifeBJ(.75,'BTLF',OrigNPC_VD)
call EnableTrigger(OrigNPC_R6)
call TriggerSleepAction(1.)
call DisableTrigger(OrigNPC_R6)
call PauseUnit(OrigNPC_MLE_target,false)
call PauseUnit(OrigNPC_MLE_caster,false)
call RemoveLocation(OrigNPC_SC)
call RemoveLocation(OrigNPC_TC)
call TriggerSleepAction(2)
call EnableTrigger(OrigNPC_XJV)
set OrigNPC_MLE_caster=null
set OrigNPC_MLE_target=null
endfunction
function OrigNPC_MPE takes nothing returns nothing
call SetDestAnimationSpeedPercent(GetEnumDestructable(),300.)
call KillDestructable(GetEnumDestructable())
endfunction
function OrigNPC_MQE takes nothing returns nothing
set OrigNPC_TC=GetUnitLoc(OrigNPC_PC)
call OrigNPC_M8V(300.,OrigNPC_TC,function OrigNPC_MPE)
call UnitDamageTargetBJ(OrigNPC_QC,OrigNPC_PC,56.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call AddSpecialEffectLocBJ(OrigNPC_TC,"Abilities\\Weapons\\TreantMissile\\TreantMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call SetUnitPositionLoc(OrigNPC_PC,OrigNPC_M3V(OrigNPC_TC,30.,OrigNPC_UC))
call SetUnitPositionLoc(OrigNPC_YC,OrigNPC_M3V(OrigNPC_TC,32.,OrigNPC_UC))
call SetUnitPositionLoc(OrigNPC_VD,OrigNPC_M3V(OrigNPC_TC,32.,OrigNPC_UC))
call RemoveLocation(OrigNPC_TC)
endfunction
function OrigNPC_MTE takes nothing returns boolean
return(GetSpellAbilityId()=='A010')
endfunction
function OrigNPC_MUE takes nothing returns nothing
call SetUnitTimeScalePercent(GetTriggerUnit(),200.)
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),3)
call TriggerSleepAction(.25)
call SetUnitTimeScalePercent(GetTriggerUnit(),100.)
endfunction
function OrigNPC_MYE takes nothing returns boolean
return(GetSpellAbilityId()=='A02F')
endfunction
function OrigNPC_MZE takes nothing returns boolean
return(OrigNPC_FC>='d')
endfunction
function OrigNPC_M_E takes nothing returns boolean
return(OrigNPC_FC<=0)
endfunction
function OrigNPC_M0E takes nothing returns boolean
return(DistanceBetweenPoints(GetRectCenter(OrigNPC_SL),OrigNPC_HB[0])>1200.)
endfunction
function OrigNPC_M1E takes nothing returns nothing
call TriggerSleepAction(.05)
set OrigNPC_FB=GetTriggerUnit()
set OrigNPC_GB=GetSpellTargetUnit()
set OrigNPC_HB[0]=GetUnitLoc(OrigNPC_FB)
set OrigNPC_HB[1]=GetUnitLoc(OrigNPC_GB)
set OrigNPC_FC=0
call DisableTrigger(OrigNPC_XJV)
call PauseUnit(OrigNPC_FB,true)
call SetUnitInvulnerable(OrigNPC_FB,true)
call PlaySoundOnUnitBJ(OrigNPC_IZ,'d',OrigNPC_FB)
call SetUnitPathing(OrigNPC_FB,false)
call CreateNUnitsAtLoc(1,'h01Y',GetOwningPlayer(OrigNPC_FB),OrigNPC_HB[0],bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call SetUnitVertexColorBJ(bj_lastCreatedUnit,'d','d','d',75.)
call CreateDestructableLoc('NTtw',OrigNPC_M3V(OrigNPC_HB[1],-90.,GetUnitFacing(OrigNPC_GB)),GetRandomReal(0,360),1.5,0)
set OrigNPC_JB=bj_lastCreatedDestructable
set OrigNPC_HB[2]=GetDestructableLoc(OrigNPC_JB)
call SetDestAnimationSpeedPercent(OrigNPC_JB,300.)
call EnableTrigger(OrigNPC_N6)
loop
exitwhen(OrigNPC_MZE())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
call DisableTrigger(OrigNPC_N6)
call SetUnitPositionLocFacingLocBJ(OrigNPC_FB,OrigNPC_HB[2],OrigNPC_HB[1])
call SetUnitAnimation(OrigNPC_FB,"stand ready")
call EnableTrigger(OrigNPC_B6)
loop
exitwhen(OrigNPC_M_E())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
call DisableTrigger(OrigNPC_B6)
call SetUnitAnimation(OrigNPC_FB,"attack")
call TriggerSleepAction(.25)
call SetDestAnimationSpeedPercent(OrigNPC_JB,100.)
call UnitDamageTargetBJ(OrigNPC_FB,OrigNPC_GB,1500.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call AddSpecialEffectLocBJ(OrigNPC_HB[1],"Objects\\Spawnmodels\\Human\\HumanBlood\\BloodElfSpellThiefBlood.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call SetUnitInvulnerable(OrigNPC_FB,false)
call PauseUnit(OrigNPC_FB,false)
call RemoveLocation(OrigNPC_HB[1])
call RemoveLocation(OrigNPC_HB[2])
call TriggerSleepAction(1.)
call SetUnitPathing(OrigNPC_FB,true)
call KillDestructable(OrigNPC_JB)
call EnableTrigger(OrigNPC_XJV)
call TriggerSleepAction(3.)
if(OrigNPC_M0E())then
call IssuePointOrderByIdLoc(OrigNPC_FB,0xD000F,OrigNPC_HB[0])
else
call IssuePointOrderByIdLoc(OrigNPC_FB,0xD0012,GetRectCenter(OrigNPC_SL))
endif
call RemoveLocation(OrigNPC_HB[0])
call RemoveDestructable(OrigNPC_JB)
endfunction
function OrigNPC_M3E takes nothing returns nothing
set OrigNPC_FC=(OrigNPC_FC+5)
call SetUnitVertexColorBJ(OrigNPC_FB,'d','d','d',I2R(OrigNPC_FC))
endfunction
function OrigNPC_M5E takes nothing returns nothing
set OrigNPC_FC=(OrigNPC_FC-5)
call SetUnitVertexColorBJ(OrigNPC_FB,'d','d','d',I2R(OrigNPC_FC))
endfunction
function OrigNPC_T0E takes nothing returns boolean
return(GetSpellAbilityId()=='A006')and(NPCSourceType(GetTriggerUnit())=='R004')
endfunction
function OrigNPC_T1E takes nothing returns boolean
return(OrigNPC_T0E())
endfunction
function OrigNPC_T2E takes nothing returns boolean
return(IsUnitInGroup(GetTriggerUnit(),OrigNPC_JN[0]))
endfunction
function OrigNPC_T3E takes nothing returns nothing
set OrigNPC_BV=GetSpellAbilityUnit()
set OrigNPC_NV=GetUnitLoc(OrigNPC_BV)
call EnableTrigger(OrigNPC_N7)
call AddSpecialEffectLocBJ(OrigNPC_NV,"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
set OrigNPC_AV=bj_lastCreatedEffect
call DestroyEffect(OrigNPC_AV)
call SetUnitInvulnerable(GetTriggerUnit(),true)
call TriggerSleepAction(1.)
set OrigNPC_JN[0]=OrigNPC_PRV(OrigNPC_MK)
set OrigNPC_JN[1]=OrigNPC_PRV(OrigNPC_JK)
set OrigNPC_JN[2]=OrigNPC_PRV(OrigNPC_LK)
set OrigNPC_JN[3]=OrigNPC_PRV(OrigNPC_HK)
call GroupAddGroup(OrigNPC_JN[1],OrigNPC_JN[0])
call GroupAddGroup(OrigNPC_JN[2],OrigNPC_JN[0])
call GroupAddGroup(OrigNPC_JN[3],OrigNPC_JN[0])
if(OrigNPC_T2E())then
else
call SetUnitInvulnerable(GetTriggerUnit(),false)
endif
call DisableTrigger(OrigNPC_N7)
call RemoveLocation(OrigNPC_NV)
call DestroyGroup(OrigNPC_JN[0])
call DestroyGroup(OrigNPC_JN[1])
call DestroyGroup(OrigNPC_JN[2])
call DestroyGroup(OrigNPC_JN[3])
endfunction
function OrigNPC_T5E takes nothing returns boolean
return(IsUnitType(GetFilterUnit(),UNIT_TYPE_STRUCTURE)==false)!=null
endfunction
function OrigNPC_T6E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_T7E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_T5E(),OrigNPC_T6E())
endfunction
function OrigNPC_T8E takes nothing returns boolean
return(IsUnitAlly(GetFilterUnit(),GetOwningPlayer(OrigNPC_BV))==false)
endfunction
function OrigNPC_T9E takes nothing returns boolean
return GetBooleanAnd(OrigNPC_T7E(),OrigNPC_T8E())
endfunction
function OrigNPC_UVE takes nothing returns nothing
set OrigNPC_PO=GetUnitLoc(GetEnumUnit())
call AddSpecialEffectLocBJ(OrigNPC_PO,"Abilities\\Weapons\\AncientProtectorMissile\\AncientProtectorMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call SetUnitPositionLoc(GetEnumUnit(),OrigNPC_M3V(OrigNPC_PO,32.,AngleBetweenPoints(OrigNPC_NV,OrigNPC_PO)))
call RemoveLocation(OrigNPC_PO)
endfunction
function OrigNPC_UEE takes nothing returns nothing
set OrigNPC_MO=OrigNPC_PIV(550.,OrigNPC_NV,Condition(function OrigNPC_T9E))
call ForGroupBJ(OrigNPC_MO,function OrigNPC_UVE)
call DestroyGroup(OrigNPC_MO)
endfunction
function OrigNPC_UOE takes nothing returns boolean
return(GetSpellAbilityId()=='A006')and(NPCSourceType(GetTriggerUnit())=='R008')
endfunction
function OrigNPC_URE takes nothing returns boolean
return(OrigNPC_UOE())
endfunction
function OrigNPC_UIE takes nothing returns boolean
return(IsUnitInGroup(GetTriggerUnit(),OrigNPC_JN[0]))
endfunction
function OrigNPC_UAE takes nothing returns nothing
set OrigNPC_XJ=GetSpellAbilityUnit()
set OrigNPC_RJ=GetUnitLoc(OrigNPC_XJ)
call EnableTrigger(OrigNPC_C7)
call AddSpecialEffectLocBJ(OrigNPC_RJ,"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
set OrigNPC_OJ=bj_lastCreatedEffect
call DestroyEffect(OrigNPC_OJ)
call SetUnitInvulnerable(GetTriggerUnit(),true)
call TriggerSleepAction(1.)
set OrigNPC_JN[0]=OrigNPC_PRV(OrigNPC_MK)
set OrigNPC_JN[1]=OrigNPC_PRV(OrigNPC_JK)
set OrigNPC_JN[2]=OrigNPC_PRV(OrigNPC_LK)
set OrigNPC_JN[3]=OrigNPC_PRV(OrigNPC_HK)
call GroupAddGroup(OrigNPC_JN[1],OrigNPC_JN[0])
call GroupAddGroup(OrigNPC_JN[2],OrigNPC_JN[0])
call GroupAddGroup(OrigNPC_JN[3],OrigNPC_JN[0])
if(OrigNPC_UIE())then
else
call SetUnitInvulnerable(GetTriggerUnit(),false)
endif
call DisableTrigger(OrigNPC_C7)
call RemoveLocation(OrigNPC_RJ)
call DestroyGroup(OrigNPC_JN[0])
call DestroyGroup(OrigNPC_JN[1])
call DestroyGroup(OrigNPC_JN[2])
call DestroyGroup(OrigNPC_JN[3])
endfunction
function OrigNPC_UBE takes nothing returns boolean
return(IsUnitType(GetFilterUnit(),UNIT_TYPE_STRUCTURE)==false)!=null
endfunction
function OrigNPC_UCE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_UDE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_UBE(),OrigNPC_UCE())
endfunction
function OrigNPC_UFE takes nothing returns boolean
return(IsUnitAlly(GetFilterUnit(),GetOwningPlayer(OrigNPC_XJ))==false)
endfunction
function OrigNPC_UGE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_UDE(),OrigNPC_UFE())
endfunction
function OrigNPC_UHE takes nothing returns nothing
set OrigNPC_IJ=GetUnitLoc(GetEnumUnit())
call AddSpecialEffectLocBJ(OrigNPC_IJ,"Abilities\\Weapons\\AncientProtectorMissile\\AncientProtectorMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call SetUnitPositionLoc(GetEnumUnit(),OrigNPC_M3V(OrigNPC_IJ,32.,AngleBetweenPoints(OrigNPC_RJ,OrigNPC_IJ)))
call RemoveLocation(OrigNPC_IJ)
endfunction
function OrigNPC_UJE takes nothing returns nothing
set OrigNPC_AJ=OrigNPC_PIV(550.,OrigNPC_RJ,Condition(function OrigNPC_UGE))
call ForGroupBJ(OrigNPC_AJ,function OrigNPC_UHE)
call DestroyGroup(OrigNPC_AJ)
endfunction
function OrigNPC_ULE takes nothing returns boolean
return(GetSpellAbilityId()=='A00S')
endfunction
function OrigNPC_UME takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_UPE takes nothing returns boolean
return(IsUnitType(GetFilterUnit(),UNIT_TYPE_STRUCTURE)==false)!=null
endfunction
function OrigNPC_UQE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_USE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_UPE(),OrigNPC_UQE())
endfunction
function OrigNPC_UTE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_UME(),OrigNPC_USE())
endfunction
function OrigNPC_UUE takes nothing returns nothing
call SetUnitFlyHeight(GetEnumUnit(),125.,1000.)
endfunction
function OrigNPC_UWE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00S',GetTriggerUnit())!=1)
endfunction
function OrigNPC_UYE takes nothing returns nothing
call UnitAddAbility(GetEnumUnit(),'Amrf')
call UnitRemoveAbility(GetEnumUnit(),'Amrf')
if(OrigNPC_UWE())then
call ForGroupBJ(OrigNPC_FN,function OrigNPC_UUE)
endif
endfunction
function OrigNPC_UZE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00S',GetTriggerUnit())==1)
endfunction
function OrigNPC_U_E takes nothing returns nothing
call SetUnitFlyHeight(GetEnumUnit(),.0,1500.)
endfunction
function OrigNPC_U0E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00S',GetTriggerUnit())==2)
endfunction
function OrigNPC_U1E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00S',GetTriggerUnit())==2)
endfunction
function OrigNPC_U2E takes nothing returns nothing
call SetUnitFlyHeight(GetEnumUnit(),.0,1500.)
endfunction
function OrigNPC_U3E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00S',GetTriggerUnit())==3)
endfunction
function OrigNPC_U4E takes nothing returns nothing
call SetUnitFlyHeight(GetEnumUnit(),.0,1500.)
endfunction
function OrigNPC_U5E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00S',GetTriggerUnit())==4)
endfunction
function OrigNPC_U6E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00S',GetTriggerUnit())==3)
endfunction
function OrigNPC_U7E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00S',GetTriggerUnit())==4)
endfunction
function OrigNPC_U8E takes nothing returns nothing
local unit OrigNPC_U8E_local_BI
set OrigNPC_GN=GetUnitLoc(GetTriggerUnit())
set OrigNPC_DN=GetSpellTargetLoc()
call CreateNUnitsAtLocFacingLocBJ(1,'h00O',GetOwningPlayer(GetTriggerUnit()),OrigNPC_GN,OrigNPC_DN)
set OrigNPC_U8E_local_BI=bj_lastCreatedUnit
set OrigNPC_FN=OrigNPC_PIV(300.,OrigNPC_DN,Condition(function OrigNPC_UTE))
call ForGroupBJ(OrigNPC_FN,function OrigNPC_UYE)
call EnableTrigger(OrigNPC_F7)
call SetUnitPathing(OrigNPC_U8E_local_BI,false)
call TriggerSleepAction(.1)
call SetUnitVertexColorBJ(OrigNPC_U8E_local_BI,'d','d','d',10.)
if(OrigNPC_UZE())then
call DisableTrigger(OrigNPC_F7)
endif
if(OrigNPC_U0E())then
call ForGroupBJ(OrigNPC_FN,function OrigNPC_U_E)
endif
call TriggerSleepAction(.1)
call SetUnitVertexColorBJ(OrigNPC_U8E_local_BI,'d','d','d',20.)
if(OrigNPC_U1E())then
call DisableTrigger(OrigNPC_F7)
endif
if(OrigNPC_U3E())then
call ForGroupBJ(OrigNPC_FN,function OrigNPC_U2E)
endif
if(OrigNPC_U5E())then
call ForGroupBJ(OrigNPC_FN,function OrigNPC_U4E)
endif
call TriggerSleepAction(.1)
call SetUnitVertexColorBJ(OrigNPC_U8E_local_BI,'d','d','d',30.)
if(OrigNPC_U6E())then
call DisableTrigger(OrigNPC_F7)
endif
call TriggerSleepAction(.1)
call SetUnitVertexColorBJ(OrigNPC_U8E_local_BI,'d','d','d',40.)
if(OrigNPC_U7E())then
call DisableTrigger(OrigNPC_F7)
endif
call TriggerSleepAction(.1)
call SetUnitVertexColorBJ(OrigNPC_U8E_local_BI,'d','d','d',50.)
call TriggerSleepAction(.1)
call SetUnitVertexColorBJ(OrigNPC_U8E_local_BI,'d','d','d',60.)
call TriggerSleepAction(.1)
call SetUnitVertexColorBJ(OrigNPC_U8E_local_BI,'d','d','d',70.)
call TriggerSleepAction(.1)
call SetUnitVertexColorBJ(OrigNPC_U8E_local_BI,'d','d','d',80.)
call TriggerSleepAction(.1)
call SetUnitVertexColorBJ(OrigNPC_U8E_local_BI,'d','d','d',90.)
call TriggerSleepAction(.1)
call SetUnitVertexColorBJ(OrigNPC_U8E_local_BI,'d','d','d',100.)
call TriggerSleepAction(.1)
call RemoveUnit(OrigNPC_U8E_local_BI)
call RemoveLocation(OrigNPC_GN)
call RemoveLocation(OrigNPC_DN)
call DestroyGroup(OrigNPC_FN)
set OrigNPC_U8E_local_BI=null
endfunction
function OrigNPC_WVE takes nothing returns boolean
return(GetUnitFlyHeight(GetEnumUnit())==.0)
endfunction
function OrigNPC_WEE takes nothing returns nothing
set OrigNPC_HN=GetUnitLoc(GetEnumUnit())
if(OrigNPC_WVE())then
call AddSpecialEffectLocBJ(OrigNPC_HN,"Abilities\\Weapons\\AncientProtectorMissile\\AncientProtectorMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
endif
set OrigNPC_AE=OrigNPC_M3V(OrigNPC_HN,12.,AngleBetweenPoints(OrigNPC_GN,OrigNPC_DN))
call SetUnitPositionLoc(GetEnumUnit(),OrigNPC_M3V(OrigNPC_HN,12.,AngleBetweenPoints(OrigNPC_GN,OrigNPC_DN)))
call RemoveLocation(OrigNPC_HN)
endfunction
function OrigNPC_WXE takes nothing returns nothing
call ForGroupBJ(OrigNPC_FN,function OrigNPC_WEE)
endfunction
function OrigNPC_WRE takes nothing returns boolean
return(GetSpellAbilityId()=='A01B')and(GetUnitAbilityLevelSwapped('A01B',GetTriggerUnit())!=1)and(GetUnitAbilityLevelSwapped('A01B',GetTriggerUnit())!=2)
endfunction
function OrigNPC_WIE takes nothing returns boolean
return(OrigNPC_WRE())
endfunction
function OrigNPC_WAE takes nothing returns boolean
return(OrigNPC_WIE())
endfunction
function OrigNPC_WNE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_KF)))
endfunction
function OrigNPC_WBE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_WCE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_WNE(),OrigNPC_WBE())
endfunction
function OrigNPC_WDE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01B',OrigNPC_KF)==3)
endfunction
function OrigNPC_WFE takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_KF,GetEnumUnit(),100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_WGE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01B',OrigNPC_KF)==4)
endfunction
function OrigNPC_WHE takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_KF,GetEnumUnit(),200.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_WJE takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='R001')
endfunction
function OrigNPC_WKE takes nothing returns boolean
return(IsUnitIllusion(GetEnumUnit()))
endfunction
function OrigNPC_WLE takes nothing returns nothing
set OrigNPC_DR=GetUnitLoc(GetEnumUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h01Z',GetOwningPlayer(OrigNPC_KF),OrigNPC_DR,OrigNPC_KR)
call UnitApplyTimedLifeBJ(.6,'BTLF',bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_DR)
if(OrigNPC_WKE())then
call KillUnit(GetEnumUnit())
endif
endfunction
function OrigNPC_WME takes nothing returns nothing
set OrigNPC_MV=OrigNPC_M3V(GetSpellTargetLoc(),100.,AngleBetweenPoints(GetUnitLoc(GetTriggerUnit()),GetSpellTargetLoc()))
set OrigNPC_KF=GetSpellAbilityUnit()
call TriggerSleepAction(.3)
call AddSpecialEffectLocBJ(OrigNPC_MV,"Objects\\Spawnmodels\\Other\\NeutralBuildingExplosion\\NeutralBuildingExplosion.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call CreateNUnitsAtLocFacingLocBJ(1,'h022',GetOwningPlayer(OrigNPC_KF),OrigNPC_MV,OrigNPC_MV)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
set OrigNPC_KR=GetUnitLoc(bj_lastCreatedUnit)
set OrigNPC_GE=OrigNPC_PIV(300.,OrigNPC_KR,Condition(function OrigNPC_WCE))
if(OrigNPC_WJE())then
if(OrigNPC_WDE())then
call ForGroupBJ(OrigNPC_GE,function OrigNPC_WFE)
endif
if(OrigNPC_WGE())then
call ForGroupBJ(OrigNPC_GE,function OrigNPC_WHE)
endif
endif
call ForGroupBJ(OrigNPC_GE,function OrigNPC_WLE)
call DestroyGroup(OrigNPC_GE)
call SetUnitAnimation(bj_lastCreatedUnit,"birth")
call SetUnitTimeScalePercent(bj_lastCreatedUnit,87.5)
call SetUnitPathing(bj_lastCreatedUnit,false)
call CreateNUnitsAtLocFacingLocBJ(1,'h021',GetOwningPlayer(OrigNPC_KF),OrigNPC_MV,OrigNPC_KR)
call UnitApplyTimedLifeBJ(4.,'BTLF',bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_KR)
call RemoveLocation(OrigNPC_MV)
endfunction
function OrigNPC_WQE takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='H00S')or(NPCSourceType(GetTriggerUnit())=='c021')or(NPCSourceType(GetTriggerUnit())=='c000')or(NPCSourceType(GetTriggerUnit())=='c003')
endfunction
function OrigNPC_WSE takes nothing returns boolean
return(GetSpellAbilityId()=='A01B')and(OrigNPC_WQE())
endfunction
function OrigNPC_WTE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_JG)))
endfunction
function OrigNPC_WUE takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_WWE takes nothing returns boolean
return GetBooleanAnd(OrigNPC_WTE(),OrigNPC_WUE())
endfunction
function OrigNPC_WYE takes nothing returns boolean
return(IsUnitIllusion(GetEnumUnit()))
endfunction
function OrigNPC_WZE takes nothing returns nothing
set OrigNPC_DR=GetUnitLoc(GetEnumUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h01Z',GetOwningPlayer(OrigNPC_JG),OrigNPC_DR,OrigNPC_ZF)
call SetUnitPathing(bj_lastCreatedUnit,false)
call UnitApplyTimedLifeBJ(.4,'BTLF',bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_DR)
call UnitDamageTargetBJ(OrigNPC_JG,GetEnumUnit(),325.,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_NORMAL)
if(OrigNPC_WYE())then
call KillUnit(GetEnumUnit())
endif
endfunction
function OrigNPC_W_E takes nothing returns nothing
set OrigNPC_JG=GetTriggerUnit()
set OrigNPC_PV=AngleBetweenPoints(GetUnitLoc(OrigNPC_JG),GetSpellTargetLoc())
set OrigNPC_KG=OrigNPC_M3V(GetUnitLoc(OrigNPC_JG),100.,OrigNPC_PV)
call CreateNUnitsAtLoc(1,'h022',GetOwningPlayer(OrigNPC_JG),OrigNPC_QV,GetRandomReal(0,360))
call SetUnitPathing(bj_lastCreatedUnit,false)
call UnitApplyTimedLifeBJ(.25,'BTLF',bj_lastCreatedUnit)
set bj_forLoopAIndex=1
set bj_forLoopAIndexEnd=20
loop
exitwhen bj_forLoopAIndex>bj_forLoopAIndexEnd
set OrigNPC_QV=OrigNPC_M3V(OrigNPC_KG,50.,OrigNPC_PV)
set OrigNPC_SV=OrigNPC_M3V(OrigNPC_QV,(100.*SinBJ((48.*I2R(bj_forLoopAIndex)))),(OrigNPC_PV+90.))
call CreateNUnitsAtLoc(1,'h022',GetOwningPlayer(OrigNPC_JG),OrigNPC_SV,GetRandomReal(0,360))
call RemoveLocation(OrigNPC_KG)
set OrigNPC_KG=GetUnitLoc(bj_lastCreatedUnit)
call SetUnitAnimation(bj_lastCreatedUnit,"birth")
call SetUnitPathing(bj_lastCreatedUnit,false)
call UnitApplyTimedLifeBJ(.25,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h021',GetOwningPlayer(OrigNPC_JG),OrigNPC_SV,GetRandomReal(0,360))
call SetUnitPathing(bj_lastCreatedUnit,false)
call UnitApplyTimedLifeBJ(.25,'BTLF',bj_lastCreatedUnit)
set OrigNPC_HE=OrigNPC_PIV(275.,OrigNPC_KG,Condition(function OrigNPC_WWE))
call ForGroupBJ(OrigNPC_HE,function OrigNPC_WZE)
call DestroyGroup(OrigNPC_HE)
call RemoveLocation(OrigNPC_QV)
call RemoveLocation(OrigNPC_SV)
call TriggerSleepAction(.01)
set bj_forLoopAIndex=bj_forLoopAIndex+1
endloop
call RemoveLocation(OrigNPC_KG)
endfunction
function OrigNPC_W1E takes nothing returns boolean
return(GetSpellAbilityId()=='A01B')and(NPCSourceType(GetTriggerUnit())=='c021')
endfunction
function OrigNPC_W2E takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),8)
endfunction
function OrigNPC_W4E takes nothing returns boolean
return(GetSpellAbilityId()=='A01B')and(NPCSourceType(GetTriggerUnit())=='c000')
endfunction
function OrigNPC_W5E takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),9)
endfunction
function OrigNPC_W7E takes nothing returns boolean
return(GetSpellAbilityId()=='A01B')and(NPCSourceType(GetTriggerUnit())=='c003')
endfunction
function OrigNPC_W8E takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),8)
endfunction
function OrigNPC_YVE takes nothing returns boolean
return(GetSpellAbilityId()=='A012')
endfunction
function OrigNPC_YEE takes nothing returns nothing
set OrigNPC_VG=GetUnitLoc(GetTriggerUnit())
call CreateNUnitsAtLoc(1,'h00P',GetOwningPlayer(GetTriggerUnit()),OrigNPC_VG,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(1.5,'BTLF',bj_lastCreatedUnit)
call UnitAddAbility(bj_lastCreatedUnit,'Amrf')
call UnitRemoveAbility(bj_lastCreatedUnit,'Amrf')
call SetUnitFlyHeight(bj_lastCreatedUnit,.0,1000.)
set OrigNPC_IX=GetUnitLoc(bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_VG)
call AddSpecialEffectLocBJ(OrigNPC_IX,"Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call RemoveLocation(OrigNPC_IX)
endfunction
function OrigNPC_YOE takes nothing returns boolean
return(GetPlayerController(GetOwningPlayer(GetTriggerUnit()))==MAP_CONTROL_CREEP)
endfunction
function OrigNPC_YRE takes nothing returns boolean
return(GetPlayerController(GetOwningPlayer(GetTriggerUnit()))==MAP_CONTROL_NEUTRAL)
endfunction
function OrigNPC_YIE takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c00B')or(NPCSourceType(GetTriggerUnit())=='R001')or(NPCSourceType(GetTriggerUnit())=='H00S')or(NPCSourceType(GetTriggerUnit())=='c00D')
endfunction
function OrigNPC_YAE takes nothing returns boolean
return(GetSpellAbilityId()=='A012')and(GetBooleanOr(OrigNPC_YOE(),OrigNPC_YRE()))and(OrigNPC_YIE())
endfunction
function OrigNPC_YNE takes nothing returns nothing
set OrigNPC_AE=GetSpellTargetLoc()
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_AE,GetRandomReal(800.,2000.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(GetTriggerUnit(),0xD0012,OrigNPC_BE)
call RemoveLocation(OrigNPC_BE)
call RemoveLocation(OrigNPC_AE)
call TriggerSleepAction(3.)
call IssueImmediateOrderById(GetTriggerUnit(),0xD0004)
endfunction
function OrigNPC_YCE takes nothing returns boolean
return(GetSpellAbilityId()=='S025')and(NPCSourceType(GetTriggerUnit())=='c006')
endfunction
function OrigNPC_YDE takes nothing returns boolean
return(OrigNPC_YCE())
endfunction
function OrigNPC_YFE takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_SR)))
endfunction
function OrigNPC_YGE takes nothing returns nothing
set OrigNPC_DR=GetUnitLoc(GetEnumUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h01R',GetOwningPlayer(OrigNPC_SR),OrigNPC_DR,OrigNPC_DR)
call UnitApplyTimedLifeBJ(1.,'BTLF',bj_lastCreatedUnit)
call UnitAddAbility(bj_lastCreatedUnit,'S025')
call IssueTargetOrderById(bj_lastCreatedUnit,0xD00F3,GetEnumUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h00C',GetOwningPlayer(OrigNPC_SR),OffsetLocation(OrigNPC_DR,0,0),OrigNPC_DR)
call SetUnitAnimation(bj_lastCreatedUnit,"birth")
call UnitApplyTimedLifeBJ(6.5,'BTLF',bj_lastCreatedUnit)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,200.)
call RemoveLocation(OrigNPC_DR)
endfunction
function OrigNPC_YHE takes nothing returns nothing
set OrigNPC_MR=GetSpellTargetUnit()
set OrigNPC_SR=GetTriggerUnit()
call TriggerSleepAction(.5)
set OrigNPC_PR=GetUnitLoc(OrigNPC_MR)
set OrigNPC_QR=GetRandomLocInRect(GetCurrentCameraBoundsMapRectBJ())
set OrigNPC_HE=OrigNPC_PIV(200.,OrigNPC_PR,Condition(function OrigNPC_YFE))
call ForGroupBJ(OrigNPC_HE,function OrigNPC_YGE)
call DestroyGroup(OrigNPC_HE)
call TriggerSleepAction(.25)
call CreateNUnitsAtLocFacingLocBJ(1,'h00C',GetOwningPlayer(OrigNPC_SR),OrigNPC_PR,OrigNPC_QR)
call SetUnitAnimation(bj_lastCreatedUnit,"birth")
call UnitApplyTimedLifeBJ(6.5,'BTLF',bj_lastCreatedUnit)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,50.)
call CreateNUnitsAtLocFacingLocBJ(1,'h00C',GetOwningPlayer(OrigNPC_SR),OffsetLocation(OrigNPC_PR,40.,40.),OrigNPC_QR)
call SetUnitAnimation(bj_lastCreatedUnit,"birth")
call UnitApplyTimedLifeBJ(5.5,'BTLF',bj_lastCreatedUnit)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,150.)
call CreateNUnitsAtLocFacingLocBJ(1,'h00C',GetOwningPlayer(OrigNPC_SR),OffsetLocation(OrigNPC_PR,-40.,-40.),OrigNPC_QR)
call SetUnitAnimation(bj_lastCreatedUnit,"birth")
call UnitApplyTimedLifeBJ(6.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'h00C',GetOwningPlayer(OrigNPC_SR),OffsetLocation(OrigNPC_PR,-40.,.0),OrigNPC_QR)
call SetUnitAnimation(bj_lastCreatedUnit,"birth")
call UnitApplyTimedLifeBJ(5.75,'BTLF',bj_lastCreatedUnit)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,200.)
call CreateNUnitsAtLocFacingLocBJ(1,'h00C',GetOwningPlayer(OrigNPC_SR),OffsetLocation(OrigNPC_PR,.0,-40.),OrigNPC_QR)
call SetUnitAnimation(bj_lastCreatedUnit,"birth")
call UnitApplyTimedLifeBJ(5.,'BTLF',bj_lastCreatedUnit)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,300.)
call RemoveLocation(OrigNPC_PR)
call RemoveLocation(OrigNPC_QR)
endfunction
function OrigNPC_YKE takes nothing returns boolean
return(GetSpellAbilityId()=='A006')and(NPCSourceType(GetTriggerUnit())=='c009')
endfunction
function OrigNPC_YLE takes nothing returns boolean
return(OrigNPC_YKE())
endfunction
function OrigNPC_YME takes nothing returns boolean
return(IsUnitIllusion(GetFilterUnit()))
endfunction
function OrigNPC_YPE takes nothing returns nothing
call KillUnit(GetEnumUnit())
endfunction
function OrigNPC_YQE takes nothing returns nothing
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
set OrigNPC_VN=OrigNPC_PIV(500.,OrigNPC_AE,Condition(function OrigNPC_YME))
call ForGroupBJ(OrigNPC_VN,function OrigNPC_YPE)
call RemoveLocation(OrigNPC_AE)
call DestroyGroup(OrigNPC_VN)
endfunction
function OrigNPC_YTE takes nothing returns boolean
return(GetSpellAbilityId()=='A00E')
endfunction
function OrigNPC_YUE takes nothing returns nothing
call UnitAddAbility(GetTriggerUnit(),'Amrf')
call UnitRemoveAbility(GetTriggerUnit(),'Amrf')
call SetUnitFlyHeight(GetTriggerUnit(),100.,200.)
call SetUnitPathing(GetTriggerUnit(),false)
call TriggerSleepAction(1.2)
call SetUnitFlyHeight(GetTriggerUnit(),.0,600.)
call SetUnitPathing(GetTriggerUnit(),true)
endfunction
function OrigNPC_YYE takes nothing returns boolean
return(GetSpellAbilityId()=='A00E')
endfunction
function OrigNPC_YZE takes nothing returns boolean
return(IsUnitInGroup(OrigNPC_XI,OrigNPC_JN[0]))
endfunction
function OrigNPC_Y_E takes nothing returns nothing
set OrigNPC_XI=GetSpellAbilityUnit()
set OrigNPC_OI=GetUnitLoc(GetSpellAbilityUnit())
set OrigNPC_KN=GetSpellTargetUnit()
set OrigNPC_RI=GetUnitLoc(OrigNPC_KN)
call TriggerSleepAction(.01)
call SetUnitTimeScalePercent(GetTriggerUnit(),200.)
call TriggerSleepAction(.3)
call SetUnitTimeScalePercent(GetTriggerUnit(),100.)
call SetUnitAnimationByIndex(GetSpellAbilityUnit(),3)
set OrigNPC_JN[0]=OrigNPC_PRV(OrigNPC_MK)
set OrigNPC_JN[1]=OrigNPC_PRV(OrigNPC_JK)
set OrigNPC_JN[2]=OrigNPC_PRV(OrigNPC_LK)
call GroupAddGroup(OrigNPC_JN[1],OrigNPC_JN[0])
call GroupAddGroup(OrigNPC_JN[2],OrigNPC_JN[0])
if(OrigNPC_YZE())then
else
call SetUnitPositionLoc(GetTriggerUnit(),OrigNPC_RI)
call RemoveLocation(OrigNPC_RI)
call EnableTrigger(OrigNPC_W7)
call TriggerSleepAction(.7)
call DisableTrigger(OrigNPC_W7)
endif
call RemoveLocation(OrigNPC_OI)
endfunction
function OrigNPC_Y1E takes nothing returns nothing
set OrigNPC_RI=GetUnitLoc(OrigNPC_KN)
call AddSpecialEffectLocBJ(OrigNPC_RI,"Abilities\\Weapons\\TreantMissile\\TreantMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call SetUnitPositionLoc(OrigNPC_KN,OrigNPC_M3V(OrigNPC_RI,12.,AngleBetweenPoints(OrigNPC_OI,OrigNPC_RI)))
call RemoveLocation(OrigNPC_RI)
endfunction
function OrigNPC_ZLE takes nothing returns boolean
return(GetSpellAbilityId()=='A00R')and(NPCSourceType(GetTriggerUnit())=='c021')
endfunction
function OrigNPC_ZME takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),0xA)
endfunction
function OrigNPC_ZQE takes nothing returns boolean
return(GetSpellAbilityId()=='A027')
endfunction
function OrigNPC_ZSE takes nothing returns nothing
call UnitApplyTimedLifeBJ(2.,'BTLF',GetEnumUnit())
endfunction
function OrigNPC_ZTE takes nothing returns nothing
set OrigNPC_FG[0]=GetUnitLoc(GetTriggerUnit())
set OrigNPC_FG[1]=GetSpellTargetLoc()
set OrigNPC_TH=AngleBetweenPoints(OrigNPC_FG[0],OrigNPC_FG[1])
set OrigNPC_KR=OrigNPC_M3V(OrigNPC_FG[0],200.,OrigNPC_TH)
set OrigNPC_CG[0]=OrigNPC_M3V(OrigNPC_KR,125.,0)
set OrigNPC_CG[1]=OrigNPC_M3V(OrigNPC_KR,125.,45.)
set OrigNPC_CG[2]=OrigNPC_M3V(OrigNPC_KR,125.,90.)
set OrigNPC_CG[3]=OrigNPC_M3V(OrigNPC_KR,125.,135.)
set OrigNPC_CG[4]=OrigNPC_M3V(OrigNPC_KR,125.,180.)
set OrigNPC_CG[5]=OrigNPC_M3V(OrigNPC_KR,125.,225.)
set OrigNPC_CG[6]=OrigNPC_M3V(OrigNPC_KR,125.,270.)
set OrigNPC_CG[7]=OrigNPC_M3V(OrigNPC_KR,125.,315.)
call AddSpecialEffectLocBJ(OrigNPC_CG[0],"Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_CG[1],"Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_CG[2],"Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_CG[3],"Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_CG[4],"Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_CG[5],"Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_CG[6],"Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_CG[7],"Objects\\Spawnmodels\\Other\\ToonBoom\\ToonBoom.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[0],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[1],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[2],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[3],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[4],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[5],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[6],GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h02K',GetOwningPlayer(GetTriggerUnit()),OrigNPC_CG[7],GetUnitFacing(GetTriggerUnit()))
set OrigNPC_ME=OrigNPC_PBV('h02K')
call ForGroupBJ(OrigNPC_ME,function OrigNPC_ZSE)
call DestroyGroup(OrigNPC_ME)
call RemoveLocation(OrigNPC_KR)
call RemoveLocation(OrigNPC_CG[0])
call RemoveLocation(OrigNPC_CG[1])
call RemoveLocation(OrigNPC_CG[2])
call RemoveLocation(OrigNPC_CG[3])
call RemoveLocation(OrigNPC_CG[4])
call RemoveLocation(OrigNPC_CG[5])
call RemoveLocation(OrigNPC_CG[6])
call RemoveLocation(OrigNPC_CG[7])
call AddSpecialEffectLocBJ(OrigNPC_FG[0],"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
set OrigNPC_GG=bj_lastCreatedEffect
set OrigNPC_FG[2]=OrigNPC_M3V(OrigNPC_FG[1],300.,OrigNPC_TH)
call TriggerSleepAction(.25)
call SetUnitManaPercentBJ(OrigNPC_UH,'d')
call UnitResetCooldown(OrigNPC_UH)
call SetUnitPositionLocFacingBJ(OrigNPC_UH,OrigNPC_FG[2],OrigNPC_TH)
set OrigNPC_FG[3]=GetUnitLoc(OrigNPC_UH)
set OrigNPC_FG[4]=OrigNPC_M3V(OrigNPC_FG[3],200.,OrigNPC_TH)
call CreateNUnitsAtLoc(1,'h02H',GetOwningPlayer(GetTriggerUnit()),OrigNPC_FG[3],bj_UNIT_FACING)
call SetUnitFlyHeight(bj_lastCreatedUnit,400.,.0)
call UnitApplyTimedLifeBJ(2.75,'BTLF',bj_lastCreatedUnit)
call DestroyEffect(OrigNPC_GG)
call TriggerSleepAction(.25)
call IssuePointOrderByIdLoc(OrigNPC_UH,0xD0271,OrigNPC_FG[4])
call RemoveLocation(OrigNPC_FG[0])
call RemoveLocation(OrigNPC_FG[1])
call RemoveLocation(OrigNPC_FG[2])
call RemoveLocation(OrigNPC_FG[3])
call RemoveLocation(OrigNPC_FG[4])
call TriggerSleepAction(2.25)
set OrigNPC_AE=GetRectCenter(OrigNPC_EK)
call SetUnitPositionLocFacingBJ(OrigNPC_UH,OrigNPC_AE,OrigNPC_TH)
call RemoveLocation(OrigNPC_AE)
endfunction
function OrigNPC_ZWE takes nothing returns boolean
return(GetSpellAbilityId()=='A00R')and(NPCSourceType(GetTriggerUnit())=='R000')
endfunction
function OrigNPC_ZYE takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitTimeScalePercent(GetTriggerUnit(),200.)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
call TriggerSleepAction(.5)
call SetUnitTimeScalePercent(GetTriggerUnit(),100.)
endfunction
function OrigNPC_Z_E takes nothing returns boolean
return(GetSpellAbilityId()=='A004')
endfunction
function OrigNPC_Z0E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A004',GetTriggerUnit())==4)
endfunction
function OrigNPC_Z1E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A004',GetTriggerUnit())==3)
endfunction
function OrigNPC_Z2E takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A004',GetTriggerUnit())==2)
endfunction
function OrigNPC_Z3E takes nothing returns nothing
set OrigNPC_AE=GetSpellTargetLoc()
call CreateNUnitsAtLoc(1,'h02H',GetOwningPlayer(GetSpellTargetUnit()),OrigNPC_AE,bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(.6,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h01W',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,(GetUnitFacing(GetTriggerUnit())+180.))
if(OrigNPC_Z2E())then
call UnitAddAbility(bj_lastCreatedUnit,'S00C')
call SetUnitAbilityLevelSwapped('S00C',bj_lastCreatedUnit,1)
else
if(OrigNPC_Z1E())then
call UnitAddAbility(bj_lastCreatedUnit,'S00C')
call SetUnitAbilityLevelSwapped('S00C',bj_lastCreatedUnit,2)
else
if(OrigNPC_Z0E())then
call UnitAddAbility(bj_lastCreatedUnit,'S00C')
call SetUnitAbilityLevelSwapped('S00C',bj_lastCreatedUnit,3)
endif
endif
endif
set OrigNPC_YA=bj_lastCreatedUnit
call SetUnitTimeScalePercent(bj_lastCreatedUnit,150.)
call IssueTargetOrderById(bj_lastCreatedUnit,0xD000F,GetSpellTargetUnit())
call RemoveLocation(OrigNPC_AE)
call TriggerSleepAction(.6)
call RemoveUnit(OrigNPC_YA)
endfunction
function OrigNPC_VOX takes nothing returns boolean
return(GetSpellAbilityId()=='A01S')and(NPCSourceType(GetTriggerUnit())=='c00D')
endfunction
function OrigNPC_VRX takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
endfunction
function OrigNPC_VAX takes nothing returns boolean
return(GetSpellAbilityId()=='A01K')
endfunction
function OrigNPC_VNX takes nothing returns nothing
set OrigNPC_JH=GetTriggerUnit()
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
call RemoveUnit(OrigNPC_FH)
call CreateNUnitsAtLoc(1,'h035',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,90.)
call RemoveLocation(OrigNPC_AE)
set OrigNPC_FH=bj_lastCreatedUnit
call SetUnitScalePercent(OrigNPC_FH,.0,.0,.0)
call EnableTrigger(OrigNPC_D8)
call EnableTrigger(OrigNPC_C8)
call TriggerSleepAction(12.)
call DisableTrigger(OrigNPC_C8)
endfunction
function OrigNPC_VCX takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c003')
endfunction
function OrigNPC_VDX takes nothing returns boolean
return(GetEnumUnit()==GetOrderTargetUnit())
endfunction
function OrigNPC_VFX takes nothing returns nothing
if(OrigNPC_VDX())then
call SetUnitPositionLoc(GetTriggerUnit(),GetUnitLoc(GetOrderTargetUnit()))
endif
endfunction
function OrigNPC_VGX takes nothing returns nothing
call ForGroupBJ(OrigNPC_PNV(1400.,GetUnitLoc(GetTriggerUnit())),function OrigNPC_VFX)
endfunction
function OrigNPC_VJX takes nothing returns boolean
return(OrigNPC_GH>=100.)
endfunction
function OrigNPC_VKX takes nothing returns nothing
set OrigNPC_HH=GetUnitLoc(OrigNPC_JH)
call SetUnitPositionLoc(OrigNPC_FH,OrigNPC_HH)
call RemoveLocation(OrigNPC_HH)
set OrigNPC_GH=(OrigNPC_GH+2.)
call SetUnitScalePercent(OrigNPC_FH,OrigNPC_GH,OrigNPC_GH,OrigNPC_GH)
if(OrigNPC_VJX())then
call EnableTrigger(OrigNPC_F8)
call DisableTrigger(GetTriggeringTrigger())
endif
endfunction
function OrigNPC_VMX takes nothing returns boolean
return(OrigNPC_GH<=.0)
endfunction
function OrigNPC_VPX takes nothing returns nothing
set OrigNPC_HH=GetUnitLoc(OrigNPC_JH)
call SetUnitPositionLoc(OrigNPC_FH,OrigNPC_HH)
call RemoveLocation(OrigNPC_HH)
set OrigNPC_GH=(OrigNPC_GH-2.)
call SetUnitScalePercent(OrigNPC_FH,OrigNPC_GH,OrigNPC_GH,OrigNPC_GH)
if(OrigNPC_VMX())then
call RemoveUnit(OrigNPC_FH)
call DisableTrigger(GetTriggeringTrigger())
endif
endfunction
function OrigNPC_VSX takes nothing returns boolean
return(GetSpellAbilityId()=='A028')
endfunction
function OrigNPC_VTX takes nothing returns boolean
return(IsUnitIllusion(GetFilterUnit()))
endfunction
function OrigNPC_VUX takes nothing returns nothing
call KillUnit(GetEnumUnit())
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_VWX takes nothing returns boolean
return(IsUnitIllusion(GetFilterUnit())==false)
endfunction
function OrigNPC_VYX takes nothing returns boolean
return(IsUnitType(GetFilterUnit(),UNIT_TYPE_STRUCTURE)==false)!=null
endfunction
function OrigNPC_VZX takes nothing returns boolean
return(IsUnitAlly(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit()))==false)
endfunction
function OrigNPC_V_X takes nothing returns boolean
return(IsUnitDeadBJ(GetFilterUnit())==false)
endfunction
function OrigNPC_V0X takes nothing returns boolean
return GetBooleanAnd(OrigNPC_VZX(),OrigNPC_V_X())
endfunction
function OrigNPC_V1X takes nothing returns boolean
return GetBooleanAnd(OrigNPC_VYX(),OrigNPC_V0X())
endfunction
function OrigNPC_V2X takes nothing returns boolean
return GetBooleanAnd(OrigNPC_VWX(),OrigNPC_V1X())
endfunction
function OrigNPC_V3X takes nothing returns nothing
set OrigNPC_KR=GetUnitLoc(GetEnumUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h02H',GetOwningPlayer(OrigNPC_DC),OrigNPC_KR,OrigNPC_KR)
call RemoveLocation(OrigNPC_KR)
call UnitApplyTimedLifeBJ(6.,'BTLF',bj_lastCreatedUnit)
call UnitAddAbility(bj_lastCreatedUnit,'A024')
call IssueTargetOrderById(bj_lastCreatedUnit,0xD00CB,GetEnumUnit())
endfunction
function OrigNPC_V4X takes nothing returns nothing
call SetUnitTimeScalePercent(GetEnumUnit(),50.)
call SetUnitAnimation(GetEnumUnit(),"Death")
endfunction
function OrigNPC_V5X takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_V6X takes nothing returns nothing
call SetUnitTimeScalePercent(GetEnumUnit(),100.)
endfunction
function OrigNPC_V7X takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_QT,'d',GetTriggerUnit())
call PlaySoundOnUnitBJ(OrigNPC_QT,'d',GetTriggerUnit())
set OrigNPC_DC=GetTriggerUnit()
set OrigNPC_XE=GetSpellTargetLoc()
set OrigNPC_JR[0]=OrigNPC_PIV(800.,OrigNPC_XE,Condition(function OrigNPC_VTX))
call PauseUnit(OrigNPC_DC,true)
call ForGroupBJ(OrigNPC_JR[0],function OrigNPC_VUX)
call DestroyGroup(OrigNPC_JR[0])
set OrigNPC_JR[1]=OrigNPC_PIV(800.,OrigNPC_XE,Condition(function OrigNPC_V2X))
call ForGroupBJ(OrigNPC_JR[1],function OrigNPC_V3X)
call EnableTrigger(OrigNPC_H8)
call TriggerSleepAction(.5)
call PauseUnit(OrigNPC_DC,false)
call ForGroupBJ(OrigNPC_JR[1],function OrigNPC_V4X)
call TriggerSleepAction(5.5)
call DisableTrigger(OrigNPC_H8)
call ForGroupBJ(OrigNPC_JR[2],function OrigNPC_V5X)
call ForGroupBJ(OrigNPC_JR[1],function OrigNPC_V6X)
call DestroyGroup(OrigNPC_JR[1])
call RemoveLocation(OrigNPC_XE)
endfunction
function OrigNPC_V9X takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_EVX takes nothing returns nothing
call ForGroupBJ(OrigNPC_JR[2],function OrigNPC_V9X)
set OrigNPC_BE=GetUnitLoc(GetEnumUnit())
set OrigNPC_KR=OrigNPC_M3V(OrigNPC_BE,GetRandomReal(.0,300.),GetRandomReal(0,360))
call CreateNUnitsAtLoc(1,'h02A',GetOwningPlayer(OrigNPC_DC),OrigNPC_KR,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(.65,'BTLF',bj_lastCreatedUnit)
call GroupAddUnit(OrigNPC_JR[2],bj_lastCreatedUnit)
call SetUnitVertexColorBJ(bj_lastCreatedUnit,'d','d','d',30.)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,200.)
call RemoveLocation(OrigNPC_KR)
set OrigNPC_DR=OrigNPC_M3V(OrigNPC_BE,GetRandomReal(.0,300.),GetRandomReal(0,360))
call CreateNUnitsAtLoc(1,'h02B',GetOwningPlayer(OrigNPC_DC),OrigNPC_DR,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(.65,'BTLF',bj_lastCreatedUnit)
call GroupAddUnit(OrigNPC_JR[2],bj_lastCreatedUnit)
call SetUnitVertexColorBJ(bj_lastCreatedUnit,'d','d','d',50.)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,30.)
call RemoveLocation(OrigNPC_BE)
call RemoveLocation(OrigNPC_DR)
call RemoveLocation(OrigNPC_KR)
endfunction
function OrigNPC_EEX takes nothing returns nothing
call ForGroupBJ(OrigNPC_JR[1],function OrigNPC_EVX)
endfunction
function OrigNPC_EOX takes nothing returns boolean
return(GetSpellAbilityId()=='A01G')
endfunction
function OrigNPC_ERX takes nothing returns nothing
call KillDestructable(GetEnumDestructable())
endfunction
function OrigNPC_EIX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_EAX takes nothing returns boolean
return(IsUnitAliveBJ(GetFilterUnit()))
endfunction
function OrigNPC_ENX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_EBX takes nothing returns boolean
return GetBooleanAnd(OrigNPC_EAX(),OrigNPC_ENX())
endfunction
function OrigNPC_ECX takes nothing returns boolean
return GetBooleanAnd(OrigNPC_EIX(),OrigNPC_EBX())
endfunction
function OrigNPC_EDX takes nothing returns boolean
return(IsUnitType(GetEnumUnit(),UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_EFX takes nothing returns nothing
if(OrigNPC_EDX())then
call UnitDamageTargetBJ(GetTriggerUnit(),GetEnumUnit(),300.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call UnitDamageTargetBJ(GetTriggerUnit(),GetEnumUnit(),600.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
endfunction
function OrigNPC_EGX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_EHX takes nothing returns boolean
return(IsUnitAliveBJ(GetFilterUnit()))
endfunction
function OrigNPC_EJX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_EKX takes nothing returns boolean
return GetBooleanAnd(OrigNPC_EHX(),OrigNPC_EJX())
endfunction
function OrigNPC_ELX takes nothing returns boolean
return GetBooleanAnd(OrigNPC_EGX(),OrigNPC_EKX())
endfunction
function OrigNPC_EMX takes nothing returns boolean
return(IsUnitType(GetEnumUnit(),UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_EPX takes nothing returns nothing
if(OrigNPC_EMX())then
call UnitDamageTargetBJ(GetTriggerUnit(),GetEnumUnit(),300.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call UnitDamageTargetBJ(GetTriggerUnit(),GetEnumUnit(),600.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
endfunction
function OrigNPC_EQX takes nothing returns nothing
call PauseUnit(GetTriggerUnit(),true)
call SetUnitInvulnerable(GetTriggerUnit(),true)
call SetUnitTimeScalePercent(GetTriggerUnit(),200.)
call TriggerSleepAction(.01)
set OrigNPC_WE=GetUnitLoc(GetTriggerUnit())
call AddSpecialEffectLocBJ(OrigNPC_WE,"Abilities\\Spells\\Orc\\EarthQuake\\EarthQuakeTarget.mdl")
set OrigNPC_EV=bj_lastCreatedEffect
call SetUnitAnimationByIndex(GetTriggerUnit(),3)
call CameraSetEQNoiseForPlayer(Player(0),50.)
call CameraSetEQNoiseForPlayer(Player(1),50.)
call CameraSetEQNoiseForPlayer(Player(2),50.)
call CameraSetEQNoiseForPlayer(Player(3),50.)
call CameraSetEQNoiseForPlayer(Player(4),50.)
call CameraSetEQNoiseForPlayer(Player(5),50.)
call CameraSetEQNoiseForPlayer(Player(6),50.)
call CameraSetEQNoiseForPlayer(Player(7),50.)
call CameraSetEQNoiseForPlayer(Player(8),50.)
call CameraSetEQNoiseForPlayer(Player(9),50.)
call CameraSetEQNoiseForPlayer(Player(0xA),50.)
call CameraSetEQNoiseForPlayer(Player(0xB),50.)
call AddSpecialEffectLocBJ(OrigNPC_WE,"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
set OrigNPC_SE=bj_lastCreatedEffect
call OrigNPC_M8V(600.,OrigNPC_WE,function OrigNPC_ERX)
call RemoveLocation(OrigNPC_WE)
call TriggerSleepAction(.25)
call DestroyEffect(OrigNPC_SE)
set OrigNPC_WE=GetUnitLoc(GetTriggerUnit())
call SetUnitAnimationByIndex(GetTriggerUnit(),4)
call AddSpecialEffectLocBJ(OrigNPC_WE,"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
set OrigNPC_TE=bj_lastCreatedEffect
call CreateNUnitsAtLoc(1,'h01C',GetOwningPlayer(GetTriggerUnit()),OrigNPC_WE,GetRandomReal(0,300.))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
set OrigNPC_DI=OrigNPC_PIV(600.,OrigNPC_WE,Condition(function OrigNPC_ECX))
call ForGroupBJ(OrigNPC_DI,function OrigNPC_EFX)
call DestroyGroup(OrigNPC_DI)
call RemoveLocation(OrigNPC_WE)
call TriggerSleepAction(.25)
call DestroyEffect(OrigNPC_TE)
set OrigNPC_WE=GetUnitLoc(GetTriggerUnit())
call SetUnitAnimationByIndex(GetTriggerUnit(),3)
call AddSpecialEffectLocBJ(OrigNPC_WE,"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
set OrigNPC_UE=bj_lastCreatedEffect
call CreateNUnitsAtLoc(1,'h01C',GetOwningPlayer(GetTriggerUnit()),OrigNPC_WE,GetRandomReal(0,300.))
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
set OrigNPC_DI=OrigNPC_PIV(600.,OrigNPC_WE,Condition(function OrigNPC_ELX))
call ForGroupBJ(OrigNPC_DI,function OrigNPC_EPX)
call DestroyGroup(OrigNPC_DI)
call RemoveLocation(OrigNPC_WE)
call TriggerSleepAction(.25)
call DestroyEffect(OrigNPC_UE)
call DestroyEffect(OrigNPC_EV)
call CameraClearNoiseForPlayer(Player(0))
call CameraClearNoiseForPlayer(Player(1))
call CameraClearNoiseForPlayer(Player(2))
call CameraClearNoiseForPlayer(Player(3))
call CameraClearNoiseForPlayer(Player(4))
call CameraClearNoiseForPlayer(Player(5))
call CameraClearNoiseForPlayer(Player(6))
call CameraClearNoiseForPlayer(Player(7))
call CameraClearNoiseForPlayer(Player(8))
call CameraClearNoiseForPlayer(Player(9))
call CameraClearNoiseForPlayer(Player(0xA))
call CameraClearNoiseForPlayer(Player(0xB))
call SetUnitTimeScalePercent(GetTriggerUnit(),100.)
call ResetUnitAnimation(GetTriggerUnit())
call PauseUnit(GetTriggerUnit(),false)
call SetUnitInvulnerable(GetTriggerUnit(),false)
endfunction
function OrigNPC_ETX takes nothing returns boolean
return(GetSpellAbilityId()=='A029')
endfunction
function OrigNPC_EUX takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),9)
endfunction
function OrigNPC_EYX takes nothing returns boolean
return(GetSpellAbilityId()=='A029')and(NPCSourceType(GetTriggerUnit())!='c002')and(NPCSourceType(GetTriggerUnit())!='c026')
endfunction
function OrigNPC_EZX takes nothing returns boolean
return(OrigNPC_EYX())
endfunction
function OrigNPC_E_X takes nothing returns boolean
return(UnitHasBuffBJ(GetTriggerUnit(),'B002'))
endfunction
function OrigNPC_E0X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A029',GetTriggerUnit())==1)
endfunction
function OrigNPC_E1X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A029',GetTriggerUnit())==2)
endfunction
function OrigNPC_E2X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A029',GetTriggerUnit())==3)
endfunction
function OrigNPC_E3X takes nothing returns boolean
return(GetUnitLevel(GetTriggerUnit())>=45)
endfunction
function OrigNPC_E4X takes nothing returns boolean
return(GetUnitLevel(GetTriggerUnit())>=40)and(GetUnitLevel(GetTriggerUnit())<=44)
endfunction
function OrigNPC_E5X takes nothing returns boolean
return(OrigNPC_E4X())
endfunction
function OrigNPC_E6X takes nothing returns boolean
return(GetUnitLevel(GetTriggerUnit())<=39)and(GetUnitLevel(GetTriggerUnit())>=35)
endfunction
function OrigNPC_E7X takes nothing returns boolean
return(OrigNPC_E6X())
endfunction
function OrigNPC_E8X takes nothing returns boolean
return(UnitHasBuffBJ(GetTriggerUnit(),'B002')==false)
endfunction
function OrigNPC_E9X takes nothing returns nothing
loop
exitwhen(OrigNPC_E_X())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
call AddSpecialEffectLocBJ(OrigNPC_AE,"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
call RemoveLocation(OrigNPC_AE)
call DestroyEffect(bj_lastCreatedEffect)
call SetUnitVertexColorBJ(GetTriggerUnit(),'d',25.,25.,0)
call SetUnitTimeScalePercent(GetTriggerUnit(),500.)
call SetUnitTurnSpeed(GetTriggerUnit(),1.)
call SetUnitMoveSpeed(GetTriggerUnit(),5000.)
if(OrigNPC_E0X())then
set OrigNPC_EH=(GetHeroStatBJ(1,GetTriggerUnit(),false)/ 2)
call ModifyHeroStat(1,GetTriggerUnit(),0,OrigNPC_EH)
call SetUnitLifePercentBJ(GetTriggerUnit(),(GetUnitLifePercent(GetTriggerUnit())/ 1.))
endif
if(OrigNPC_E1X())then
set OrigNPC_EH=(GetHeroStatBJ(1,GetTriggerUnit(),false)/ 1)
call ModifyHeroStat(1,GetTriggerUnit(),0,OrigNPC_EH)
call SetUnitLifePercentBJ(GetTriggerUnit(),(GetUnitLifePercent(GetTriggerUnit())/ 1.25))
endif
if(OrigNPC_E2X())then
set OrigNPC_EH=(GetHeroStatBJ(1,GetTriggerUnit(),false)+(GetHeroStatBJ(1,GetTriggerUnit(),false)/ 2))
call ModifyHeroStat(1,GetTriggerUnit(),0,OrigNPC_EH)
call SetUnitLifePercentBJ(GetTriggerUnit(),(GetUnitLifePercent(GetTriggerUnit())/ 1.5))
endif
call PlaySoundOnUnitBJ(OrigNPC_QZ,'d',GetTriggerUnit())
if(OrigNPC_E7X())then
call UnitAddAbility(GetTriggerUnit(),'A01T')
call SetUnitAbilityLevelSwapped('A01T',GetTriggerUnit(),1)
call SelectHeroSkill(GetTriggerUnit(),'A01T')
else
if(OrigNPC_E5X())then
call UnitAddAbility(GetTriggerUnit(),'A01T')
call SetUnitAbilityLevelSwapped('A01T',GetTriggerUnit(),2)
call SelectHeroSkill(GetTriggerUnit(),'A01T')
else
if(OrigNPC_E3X())then
call UnitAddAbility(GetTriggerUnit(),'A01T')
call SetUnitAbilityLevelSwapped('A01T',GetTriggerUnit(),3)
call SelectHeroSkill(GetTriggerUnit(),'A01T')
endif
endif
endif
loop
exitwhen(OrigNPC_E8X())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
call ModifyHeroStat(1,GetTriggerUnit(),1,OrigNPC_EH)
call SetUnitVertexColorBJ(GetTriggerUnit(),'d',100.,100.,0)
call SetUnitMoveSpeed(GetTriggerUnit(),GetUnitDefaultMoveSpeed(GetTriggerUnit()))
call SetUnitTurnSpeed(GetTriggerUnit(),GetUnitDefaultTurnSpeed(GetTriggerUnit()))
call SetUnitTimeScalePercent(GetTriggerUnit(),'d')
call UnitRemoveAbility(GetTriggerUnit(),'A01T')
endfunction
function OrigNPC_XEX takes nothing returns boolean
return(GetSpellAbilityId()=='A029')
endfunction
function OrigNPC_XXX takes nothing returns nothing
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
call CreateNUnitsAtLocFacingLocBJ(1,'h02H',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,OrigNPC_AE)
call UnitAddAbility(bj_lastCreatedUnit,'A01X')
call IssueTargetOrderById(bj_lastCreatedUnit,0xD00DD,GetTriggerUnit())
call UnitApplyTimedLifeBJ(1.25,'BTLF',bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_AE)
endfunction
function OrigNPC_XRX takes nothing returns boolean
return(GetSpellAbilityId()=='A029')and(GetUnitAbilityLevelSwapped('A029',GetTriggerUnit())==3)
endfunction
function OrigNPC_XIX takes nothing returns boolean
return(OrigNPC_XRX())
endfunction
function OrigNPC_XAX takes nothing returns boolean
return(UnitHasBuffBJ(OrigNPC_J3V,'B002'))
endfunction
function OrigNPC_XNX takes nothing returns boolean
return(UnitHasBuffBJ(OrigNPC_J3V,'B002')==false)
endfunction
function OrigNPC_XBX takes nothing returns boolean
return(GetSpellAbilityUnit()==OrigNPC_J3V)
endfunction
function OrigNPC_XCX takes nothing returns nothing
if(OrigNPC_XBX())then
set OrigNPC_OO[0]=GetSpellAbilityUnit()
set OrigNPC_RO[0]=GetUnitLoc(OrigNPC_OO[0])
call AddSpecialEffectLocBJ(OrigNPC_RO[0],"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_RO[0],"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
call DestroyEffect(bj_lastCreatedEffect)
loop
exitwhen(OrigNPC_XAX())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
call EnableTrigger(OrigNPC_Q8)
call EnableTrigger(OrigNPC_S8)
call AddSpecialEffectTargetUnitBJ("foot",OrigNPC_OO[0],"Abilities\\Spells\\Undead\\DarkSummoning\\DarkSummonMissile.mdl")
set OrigNPC_PE[0]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("hand",OrigNPC_OO[0],"Abilities\\Spells\\Undead\\DarkSummoning\\DarkSummonMissile.mdl")
set OrigNPC_PE[1]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_OO[0],"Abilities\\Spells\\Undead\\DarkSummoning\\DarkSummonMissile.mdl")
set OrigNPC_PE[2]=bj_lastCreatedEffect
loop
exitwhen(OrigNPC_XNX())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
call DestroyEffect(OrigNPC_PE[0])
call DestroyEffect(OrigNPC_PE[1])
call DestroyEffect(OrigNPC_PE[2])
call DisableTrigger(OrigNPC_Q8)
call DisableTrigger(OrigNPC_S8)
call RemoveLocation(OrigNPC_RO[0])
else
set OrigNPC_OO[1]=GetSpellAbilityUnit()
set OrigNPC_RO[1]=GetUnitLoc(OrigNPC_OO[1])
call EnableTrigger(OrigNPC_Q8)
call AddSpecialEffectLocBJ(OrigNPC_RO[1],"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_RO[1],"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectTargetUnitBJ("foot",OrigNPC_OO[1],"Abilities\\Spells\\Undead\\DarkSummoning\\DarkSummonMissile.mdl")
set OrigNPC_PE[3]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("hand",OrigNPC_OO[1],"Abilities\\Spells\\Undead\\DarkSummoning\\DarkSummonMissile.mdl")
set OrigNPC_PE[4]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_OO[1],"Abilities\\Spells\\Undead\\DarkSummoning\\DarkSummonMissile.mdl")
set OrigNPC_PE[5]=bj_lastCreatedEffect
call TriggerSleepAction(17.)
call DestroyEffect(OrigNPC_PE[3])
call DestroyEffect(OrigNPC_PE[4])
call DestroyEffect(OrigNPC_PE[5])
call DisableTrigger(OrigNPC_Q8)
call RemoveLocation(OrigNPC_RO[1])
endif
endfunction
function OrigNPC_XFX takes nothing returns boolean
return(GetIssuedOrderId()==0xD000F)or(GetIssuedOrderId()==0xD0003)or(GetIssuedOrderId()==0xD0012)
endfunction
function OrigNPC_XGX takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='R003')and(OrigNPC_XFX())
endfunction
function OrigNPC_XHX takes nothing returns boolean
return(OrigNPC_XGX())
endfunction
function OrigNPC_XJX takes nothing returns boolean
return(GetEnumUnit()==GetOrderTargetUnit())
endfunction
function OrigNPC_XKX takes nothing returns nothing
if(OrigNPC_XJX())then
call SetUnitPositionLoc(GetTriggerUnit(),OrigNPC_ZF)
call SetUnitFacingToFaceLocTimed(GetTriggerUnit(),OrigNPC_BE,.1)
call SetUnitAnimationByIndex(GetTriggerUnit(),9)
endif
endfunction
function OrigNPC_XLX takes nothing returns nothing
set OrigNPC_BE=GetUnitLoc(GetOrderTargetUnit())
set OrigNPC_DR=GetUnitLoc(GetTriggerUnit())
set OrigNPC_DJ=AngleBetweenPoints(OrigNPC_BE,OrigNPC_DR)
set OrigNPC_ZF=OrigNPC_M3V(OrigNPC_BE,75.,OrigNPC_DJ)
set OrigNPC_CE=OrigNPC_PNV(1400.,OrigNPC_DR)
call ForGroupBJ(OrigNPC_CE,function OrigNPC_XKX)
call RemoveLocation(OrigNPC_BE)
call RemoveLocation(OrigNPC_DR)
call DestroyGroup(OrigNPC_CE)
endfunction
function OrigNPC_XPX takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='R003')
endfunction
function OrigNPC_XQX takes nothing returns boolean
return(IsLocationVisibleToPlayer(OrigNPC_KR,GetOwningPlayer(GetTriggerUnit())))and(DistanceBetweenPoints(OrigNPC_DR,OrigNPC_KR)<=1400.)
endfunction
function OrigNPC_XSX takes nothing returns nothing
set OrigNPC_DR=GetUnitLoc(GetTriggerUnit())
set OrigNPC_KR=GetOrderPointLoc()
set OrigNPC_DJ=AngleBetweenPoints(OrigNPC_DR,OrigNPC_KR)
set OrigNPC_ZF=OrigNPC_M3V(OrigNPC_KR,100.,AngleBetweenPoints(OrigNPC_KR,OrigNPC_DR))
if(OrigNPC_XQX())then
call SetUnitTurnSpeed(GetTriggerUnit(),1.)
call SetUnitPositionLoc(GetTriggerUnit(),OrigNPC_ZF)
call SetUnitAnimationByIndex(GetTriggerUnit(),9)
call SetUnitFacingToFaceLocTimed(GetTriggerUnit(),OrigNPC_KR,.1)
call SetUnitAnimationByIndex(GetTriggerUnit(),9)
endif
call RemoveLocation(OrigNPC_DR)
call RemoveLocation(OrigNPC_KR)
call RemoveLocation(OrigNPC_ZF)
endfunction
function OrigNPC_XUX takes nothing returns boolean
return(NPCSourceType(GetSpellAbilityUnit())=='c002')
endfunction
function OrigNPC_XWX takes nothing returns boolean
return(NPCSourceType(GetSpellAbilityUnit())=='c026')
endfunction
function OrigNPC_XYX takes nothing returns boolean
return(GetSpellAbilityId()=='A029')and(GetBooleanOr(OrigNPC_XUX(),OrigNPC_XWX()))
endfunction
function OrigNPC_XZX takes nothing returns boolean
return(OrigNPC_XYX())
endfunction
function OrigNPC_X_X takes nothing returns nothing
call AddSpecialEffectLocBJ(GetUnitLoc(GetTriggerUnit()),"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
call SetUnitVertexColorBJ(GetTriggerUnit(),'d',25.,25.,0)
call SetUnitTimeScalePercent(GetTriggerUnit(),500.)
call PlaySoundOnUnitBJ(OrigNPC_UZ,'d',GetTriggerUnit())
call SetUnitMoveSpeed(GetTriggerUnit(),1000.)
call EnableTrigger(OrigNPC_U8)
call EnableTrigger(OrigNPC_W8)
call TriggerSleepAction(1.)
call SetUnitTurnSpeed(GetTriggerUnit(),1.)
call TriggerSleepAction(16.)
call DisableTrigger(OrigNPC_U8)
call DisableTrigger(OrigNPC_W8)
call SetUnitVertexColorBJ(GetTriggerUnit(),'d',100.,100.,0)
call SetUnitMoveSpeed(GetTriggerUnit(),GetUnitDefaultMoveSpeed(GetTriggerUnit()))
call SetUnitTurnSpeed(GetTriggerUnit(),GetUnitDefaultTurnSpeed(GetTriggerUnit()))
call SetUnitTimeScalePercent(GetTriggerUnit(),'d')
endfunction
function OrigNPC_X1X takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c002')
endfunction
function OrigNPC_X2X takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c026')
endfunction
function OrigNPC_X3X takes nothing returns boolean
return(GetBooleanOr(OrigNPC_X1X(),OrigNPC_X2X()))
endfunction
function OrigNPC_X4X takes nothing returns boolean
return(GetEnumUnit()==GetOrderTargetUnit())
endfunction
function OrigNPC_X5X takes nothing returns nothing
if(OrigNPC_X4X())then
call SetUnitPositionLoc(GetTriggerUnit(),OrigNPC_ZF)
call SetUnitFacingToFaceLocTimed(GetTriggerUnit(),OrigNPC_BE,.1)
call SetUnitAnimationByIndex(GetTriggerUnit(),9)
endif
endfunction
function OrigNPC_X6X takes nothing returns nothing
set OrigNPC_BE=GetUnitLoc(GetOrderTargetUnit())
set OrigNPC_DR=GetUnitLoc(GetTriggerUnit())
set OrigNPC_DJ=AngleBetweenPoints(OrigNPC_BE,OrigNPC_DR)
set OrigNPC_ZF=OrigNPC_M3V(OrigNPC_BE,75.,OrigNPC_DJ)
set OrigNPC_CE=OrigNPC_PNV(1400.,OrigNPC_DR)
call ForGroupBJ(OrigNPC_CE,function OrigNPC_X5X)
call RemoveLocation(OrigNPC_BE)
call RemoveLocation(OrigNPC_DR)
call DestroyGroup(OrigNPC_CE)
endfunction
function OrigNPC_X8X takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c002')
endfunction
function OrigNPC_X9X takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c026')
endfunction
function OrigNPC_OVX takes nothing returns boolean
return(GetBooleanOr(OrigNPC_X8X(),OrigNPC_X9X()))
endfunction
function OrigNPC_OEX takes nothing returns boolean
return(IsLocationVisibleToPlayer(OrigNPC_KR,GetOwningPlayer(GetTriggerUnit())))and(DistanceBetweenPoints(OrigNPC_DR,OrigNPC_KR)<=1400.)
endfunction
function OrigNPC_OXX takes nothing returns nothing
set OrigNPC_DR=GetUnitLoc(GetTriggerUnit())
set OrigNPC_KR=GetOrderPointLoc()
set OrigNPC_DJ=AngleBetweenPoints(OrigNPC_DR,OrigNPC_KR)
set OrigNPC_ZF=OrigNPC_M3V(OrigNPC_KR,100.,AngleBetweenPoints(OrigNPC_KR,OrigNPC_DR))
if(OrigNPC_OEX())then
call SetUnitTurnSpeed(GetTriggerUnit(),1.)
call SetUnitPositionLoc(GetTriggerUnit(),OrigNPC_ZF)
call SetUnitAnimationByIndex(GetTriggerUnit(),9)
call SetUnitFacingToFaceLocTimed(GetTriggerUnit(),OrigNPC_KR,.1)
call SetUnitAnimationByIndex(GetTriggerUnit(),9)
endif
call RemoveLocation(OrigNPC_DR)
call RemoveLocation(OrigNPC_KR)
call RemoveLocation(OrigNPC_ZF)
endfunction
function OrigNPC_ORX takes nothing returns boolean
return(GetSpellAbilityId()=='A02R')
endfunction
function OrigNPC_OIX takes nothing returns boolean
return(CountUnitsInGroup(OrigNPC_PBV('h00V'))==0)
endfunction
function OrigNPC_OAX takes nothing returns boolean
return(CountUnitsInGroup(OrigNPC_PBV('h00V'))>=1)
endfunction
function OrigNPC_ONX takes nothing returns boolean
return(CountUnitsInGroup(OrigNPC_PBV('h00W'))==0)
endfunction
function OrigNPC_OBX takes nothing returns boolean
return(CountUnitsInGroup(OrigNPC_PBV('h00W'))>=1)
endfunction
function OrigNPC_OCX takes nothing returns nothing
set OrigNPC_SD[0]=GetEnumUnit()
endfunction
function OrigNPC_ODX takes nothing returns nothing
set OrigNPC_SD[1]=GetEnumUnit()
endfunction
function OrigNPC_OFX takes nothing returns nothing
set OrigNPC_SD[2]=GetEnumUnit()
endfunction
function OrigNPC_OGX takes nothing returns nothing
call UnitAddAbility(GetEnumUnit(),'Amrf')
call UnitRemoveAbility(GetEnumUnit(),'Amrf')
call SetUnitFlyHeight(GetEnumUnit(),350.,1600.)
endfunction
function OrigNPC_OHX takes nothing returns nothing
call SetUnitFlyHeight(GetEnumUnit(),.0,1000.)
endfunction
function OrigNPC_OJX takes nothing returns nothing
if(OrigNPC_OIX())then
call IssueImmediateOrderById(GetTriggerUnit(),0xD0272)
call IssueImmediateOrderById(GetTriggerUnit(),0xD009E)
endif
loop
exitwhen(OrigNPC_OAX())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
if(OrigNPC_ONX())then
set OrigNPC_AE=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),300.,GetRandomReal(0,360))
call IssuePointOrderByIdLoc(OrigNPC_J2V,0xD0100,OrigNPC_AE)
call RemoveLocation(OrigNPC_AE)
endif
loop
exitwhen(OrigNPC_OBX())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
call ForGroupBJ(OrigNPC_PBV('h00V'),function OrigNPC_OCX)
call ForGroupBJ(OrigNPC_PBV('o002'),function OrigNPC_ODX)
call ForGroupBJ(OrigNPC_PBV('h00W'),function OrigNPC_OFX)
set OrigNPC_AE=GetUnitLoc(OrigNPC_SD[0])
set OrigNPC_DR=GetUnitLoc(OrigNPC_SD[1])
set OrigNPC_KR=GetUnitLoc(OrigNPC_SD[2])
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_KR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_KR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_KR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_KR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_KR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_KR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_DR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_DR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_DR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_DR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_DR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_DR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_DR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_DR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_DR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_DR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_DR,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_DR,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_BE)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_AE,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call RemoveLocation(OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_AE,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call RemoveLocation(OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_AE,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call RemoveLocation(OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_AE,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call RemoveLocation(OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_AE,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call RemoveLocation(OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'n005',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_AE,GetRandomReal(200.,600.),GetRandomReal(0,360))
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0012,OrigNPC_BE)
call RemoveLocation(OrigNPC_BE)
call GroupAddUnit(OrigNPC_TD[0],bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_AE)
call RemoveLocation(OrigNPC_DR)
call RemoveLocation(OrigNPC_KR)
call ForGroupBJ(OrigNPC_TD[0],function OrigNPC_OGX)
call TriggerSleepAction(.35)
call ForGroupBJ(OrigNPC_TD[0],function OrigNPC_OHX)
endfunction
function OrigNPC_OQX takes nothing returns boolean
return(GetSpellAbilityId()=='A01P')
endfunction
function OrigNPC_OSX takes nothing returns boolean
return(OrigNPC_OQX())
endfunction
function OrigNPC_OTX takes nothing returns boolean
return(IsUnitType(OrigNPC_YV,UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_OUX takes nothing returns nothing
call SetUnitPathing(GetEnumUnit(),true)
endfunction
function OrigNPC_OWX takes nothing returns nothing
call DestroyEffect(OrigNPC_DO[0])
call DestroyEffect(OrigNPC_DO[1])
call DestroyEffect(OrigNPC_DO[2])
call DestroyEffect(OrigNPC_DO[3])
call DestroyEffect(OrigNPC_DO[4])
call DestroyEffect(OrigNPC_DO[5])
set OrigNPC_YV=GetSpellTargetUnit()
set OrigNPC_ZV=GetSpellAbilityUnit()
set OrigNPC_ZG=GetUnitFacing(OrigNPC_ZV)
if(OrigNPC_OTX())then
call SetCameraTargetControllerNoZForPlayer(GetOwningPlayer(OrigNPC_YV),OrigNPC_YV,0,-200.,false)
endif
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_YV,"Abilities\\Spells\\NightElf\\Blink\\BlinkCaster.mdl")
set OrigNPC_DO[0]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_YV,"Abilities\\Spells\\NightElf\\Blink\\BlinkTarget.mdl")
set OrigNPC_DO[1]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_YV,"Abilities\\Spells\\Other\\Charm\\CharmTarget.mdl")
set OrigNPC_DO[2]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_YV,"Abilities\\Spells\\Items\\ClarityPotion\\ClarityTarget.mdl")
set OrigNPC_DO[3]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_YV,"Abilities\\Spells\\Items\\ClarityPotion\\ClarityTarget.mdl")
set OrigNPC_DO[4]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_YV,"Abilities\\Spells\\Items\\ClarityPotion\\ClarityTarget.mdl")
set OrigNPC_DO[5]=bj_lastCreatedEffect
call TriggerSleepAction(.01)
call EnableTrigger(OrigNPC_VEV)
call UnitShareVisionBJ(true,OrigNPC_YV,GetOwningPlayer(OrigNPC_ZV))
call TriggerSleepAction(3.)
call DisableTrigger(OrigNPC_VEV)
call TriggerSleepAction(.01)
call UnitShareVisionBJ(false,OrigNPC_YV,GetOwningPlayer(OrigNPC_ZV))
call ForGroupBJ(OrigNPC_DG,function OrigNPC_OUX)
set OrigNPC_ZF=GetUnitLoc(OrigNPC_YV)
call CreateNUnitsAtLoc(1,'h02J',GetOwningPlayer(OrigNPC_ZV),OrigNPC_ZF,bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call ResetToGameCameraForPlayer(GetOwningPlayer(OrigNPC_YV),0)
call SetCameraFieldForPlayer(GetOwningPlayer(OrigNPC_YV),CAMERA_FIELD_ZOFFSET,1000.,0)
call DestroyEffect(OrigNPC_DO[0])
call DestroyEffect(OrigNPC_DO[1])
call DestroyEffect(OrigNPC_DO[2])
call DestroyEffect(OrigNPC_DO[3])
call DestroyEffect(OrigNPC_DO[4])
call DestroyEffect(OrigNPC_DO[5])
call RemoveLocation(OrigNPC_ZF)
endfunction
function OrigNPC_OZX takes nothing returns boolean
return(IsPlayerEnemy(GetOwningPlayer(GetFilterUnit()),GetOwningPlayer(OrigNPC_ZV)))
endfunction
function OrigNPC_O_X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_O0X takes nothing returns boolean
return(GetFilterUnit()!=OrigNPC_YV)
endfunction
function OrigNPC_O1X takes nothing returns boolean
return GetBooleanAnd(OrigNPC_O_X(),OrigNPC_O0X())
endfunction
function OrigNPC_O2X takes nothing returns boolean
return GetBooleanAnd(OrigNPC_OZX(),OrigNPC_O1X())
endfunction
function OrigNPC_O3X takes nothing returns boolean
return(IsUnitIllusion(GetFilterUnit()))
endfunction
function OrigNPC_O4X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01P',OrigNPC_ZV)==1)
endfunction
function OrigNPC_O5X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01P',OrigNPC_ZV)==2)
endfunction
function OrigNPC_O6X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01P',OrigNPC_ZV)==3)
endfunction
function OrigNPC_O7X takes nothing returns nothing
set OrigNPC_ZF=GetUnitLoc(GetEnumUnit())
call AddSpecialEffectLocBJ(OrigNPC_ZF,"Abilities\\Weapons\\SteamMissile\\SteamMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call SetUnitPositionLoc(GetEnumUnit(),OrigNPC_M3V(OrigNPC_ZF,20.,OrigNPC_ZG))
if(OrigNPC_O4X())then
call UnitDamageTargetBJ(OrigNPC_ZV,GetEnumUnit(),6.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_O5X())then
call UnitDamageTargetBJ(OrigNPC_ZV,GetEnumUnit(),9.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_O6X())then
call UnitDamageTargetBJ(OrigNPC_ZV,GetEnumUnit(),12.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
call RemoveLocation(OrigNPC_ZF)
endfunction
function OrigNPC_O8X takes nothing returns nothing
call SetUnitPathing(GetEnumUnit(),false)
call GroupAddUnit(OrigNPC_DG,GetEnumUnit())
endfunction
function OrigNPC_O9X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01P',OrigNPC_ZV)==1)
endfunction
function OrigNPC_RVX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01P',OrigNPC_ZV)==2)
endfunction
function OrigNPC_REX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01P',OrigNPC_ZV)==3)
endfunction
function OrigNPC_RXX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01P',OrigNPC_ZV)==1)
endfunction
function OrigNPC_ROX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01P',OrigNPC_ZV)==2)
endfunction
function OrigNPC_RRX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01P',OrigNPC_ZV)==3)
endfunction
function OrigNPC_RIX takes nothing returns boolean
return(IsUnitType(OrigNPC_YV,UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_RAX takes nothing returns nothing
set OrigNPC_VG=GetUnitLoc(OrigNPC_YV)
set OrigNPC_ME=OrigNPC_PIV(350.,OrigNPC_VG,Condition(function OrigNPC_O2X))
set OrigNPC_LE=OrigNPC_PIV(200.,OrigNPC_VG,Condition(function OrigNPC_O3X))
call ForGroupBJ(OrigNPC_ME,function OrigNPC_O7X)
call ForGroupBJ(OrigNPC_LE,function OrigNPC_O8X)
call SetUnitPositionLoc(OrigNPC_YV,OrigNPC_M3V(OrigNPC_VG,22.,OrigNPC_ZG))
call AddSpecialEffectLocBJ(OrigNPC_VG,"Abilities\\Weapons\\AncientProtectorMissile\\AncientProtectorMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_VG,"Abilities\\Weapons\\SteamMissile\\SteamMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
if(OrigNPC_RIX())then
if(OrigNPC_RXX())then
call UnitDamageTargetBJ(OrigNPC_ZV,OrigNPC_YV,4.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_ROX())then
call UnitDamageTargetBJ(OrigNPC_ZV,OrigNPC_YV,6.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_RRX())then
call UnitDamageTargetBJ(OrigNPC_ZV,OrigNPC_YV,8.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
else
if(OrigNPC_O9X())then
call UnitDamageTargetBJ(OrigNPC_ZV,OrigNPC_YV,6.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_RVX())then
call UnitDamageTargetBJ(OrigNPC_ZV,OrigNPC_YV,9.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_REX())then
call UnitDamageTargetBJ(OrigNPC_ZV,OrigNPC_YV,12.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
endif
call DestroyGroup(OrigNPC_ME)
call DestroyGroup(OrigNPC_LE)
call RemoveLocation(OrigNPC_VG)
endfunction
function OrigNPC_RBX takes nothing returns boolean
return(GetSpellAbilityId()=='A01P')
endfunction
function OrigNPC_RCX takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='H00N')
endfunction
function OrigNPC_RDX takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='R000')
endfunction
function OrigNPC_RFX takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c021')
endfunction
function OrigNPC_RGX takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='R000')
endfunction
function OrigNPC_RHX takes nothing returns nothing
call DestroyEffect(OrigNPC_DO[6])
call DestroyEffect(OrigNPC_DO[7])
call DestroyEffect(OrigNPC_DO[8])
call TriggerSleepAction(.01)
call AddSpecialEffectTargetUnitBJ("hand",GetTriggerUnit(),"Abilities\\Spells\\Items\\ClarityPotion\\ClarityTarget.mdl")
set OrigNPC_DO[6]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("hand",GetTriggerUnit(),"Abilities\\Spells\\Items\\ClarityPotion\\ClarityTarget.mdl")
set OrigNPC_DO[7]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("hand",GetTriggerUnit(),"Abilities\\Spells\\Items\\ClarityPotion\\ClarityTarget.mdl")
set OrigNPC_DO[8]=bj_lastCreatedEffect
call PlaySoundOnUnitBJ(OrigNPC_FZ,'d',GetTriggerUnit())
call PlaySoundOnUnitBJ(OrigNPC_FZ,'d',GetTriggerUnit())
call PlaySoundOnUnitBJ(OrigNPC_FZ,'d',GetTriggerUnit())
if(OrigNPC_RFX())then
call SetUnitAnimationByIndex(GetTriggerUnit(),0xA)
else
if(OrigNPC_RDX())then
call SetUnitTimeScalePercent(GetTriggerUnit(),200.)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
else
if(OrigNPC_RCX())then
call SetUnitAnimationByIndex(GetTriggerUnit(),0xF)
endif
endif
endif
call TriggerSleepAction(.5)
if(OrigNPC_RGX())then
call SetUnitTimeScalePercent(GetTriggerUnit(),100.)
endif
call DestroyEffect(OrigNPC_DO[6])
call DestroyEffect(OrigNPC_DO[7])
call DestroyEffect(OrigNPC_DO[8])
endfunction
function OrigNPC_RTX takes nothing returns boolean
return(GetSpellAbilityId()=='A014')
endfunction
function OrigNPC_RUX takes nothing returns nothing
set OrigNPC_AE=GetUnitLoc(GetSpellTargetUnit())
call AddSpecialEffectLocBJ(OrigNPC_AE,"Objects\\Spawnmodels\\Human\\HumanBlood\\BloodElfSpellThiefBlood.mdl")
set OrigNPC_QE=bj_lastCreatedEffect
call DestroyEffect(OrigNPC_QE)
call RemoveLocation(OrigNPC_AE)
call TriggerSleepAction(1.)
set OrigNPC_AE=GetUnitLoc(GetSpellTargetUnit())
call AddSpecialEffectLocBJ(OrigNPC_AE,"Objects\\Spawnmodels\\Human\\HumanBlood\\BloodElfSpellThiefBlood.mdl")
set OrigNPC_QE=bj_lastCreatedEffect
call DestroyEffect(OrigNPC_QE)
call RemoveLocation(OrigNPC_AE)
call TriggerSleepAction(1.)
set OrigNPC_AE=GetUnitLoc(GetSpellTargetUnit())
call AddSpecialEffectLocBJ(OrigNPC_AE,"Objects\\Spawnmodels\\Human\\HumanBlood\\BloodElfSpellThiefBlood.mdl")
set OrigNPC_QE=bj_lastCreatedEffect
call DestroyEffect(OrigNPC_QE)
call RemoveLocation(OrigNPC_AE)
endfunction
function OrigNPC_RYX takes nothing returns boolean
return(GetSpellAbilityId()=='A01I')and(GetUnitLevel(GetTriggerUnit())>=50)
endfunction
function OrigNPC_RZX takes nothing returns boolean
return(OrigNPC_RYX())
endfunction
function OrigNPC_R_X takes nothing returns nothing
call UnitApplyTimedLifeBJ(4.,'BTLF',GetEnumUnit())
call SetUnitTimeScalePercent(GetEnumUnit(),50.)
call UnitAddAbility(GetEnumUnit(),'Amrf')
call UnitRemoveAbility(GetEnumUnit(),'Amrf')
call SetUnitFlyHeight(GetEnumUnit(),-300.,.0)
call SetUnitFlyHeight(GetEnumUnit(),300.,500.)
endfunction
function OrigNPC_R0X takes nothing returns nothing
call SetUnitTimeScalePercent(GetEnumUnit(),200.)
call SetUnitVertexColorBJ(GetEnumUnit(),'d','d','d',75.)
call SetUnitFlyHeight(GetEnumUnit(),-300.,3000.)
endfunction
function OrigNPC_R1X takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_R2X takes nothing returns nothing
call UnitDamageTargetBJ(GetTriggerUnit(),GetEnumUnit(),2000.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_R3X takes nothing returns nothing
call SetDestAnimationSpeedPercent(GetEnumDestructable(),300.)
call KillDestructable(GetEnumDestructable())
endfunction
function OrigNPC_R4X takes nothing returns nothing
call TriggerSleepAction(1.)
set OrigNPC_PD[1]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),200.,0)
set OrigNPC_PD[2]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),200.,90.)
set OrigNPC_PD[3]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),200.,180.)
set OrigNPC_PD[4]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),200.,270.)
set OrigNPC_PD[5]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),400.,0)
set OrigNPC_PD[6]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),400.,45.)
set OrigNPC_PD[7]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),400.,90.)
set OrigNPC_PD[8]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),400.,135.)
set OrigNPC_PD[9]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),400.,180.)
set OrigNPC_PD[0xA]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),400.,225.)
set OrigNPC_PD[0xB]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),400.,270.)
set OrigNPC_PD[0xC]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),400.,315.)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[1],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[2],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[3],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[4],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[5],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[6],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[7],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[8],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[9],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[0xA],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[0xB],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02T',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[0xC],bj_UNIT_FACING)
call GroupAddUnit(OrigNPC_QD,bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_PD[1])
call RemoveLocation(OrigNPC_PD[2])
call RemoveLocation(OrigNPC_PD[3])
call RemoveLocation(OrigNPC_PD[4])
call RemoveLocation(OrigNPC_PD[5])
call RemoveLocation(OrigNPC_PD[6])
call RemoveLocation(OrigNPC_PD[7])
call RemoveLocation(OrigNPC_PD[8])
call RemoveLocation(OrigNPC_PD[9])
call RemoveLocation(OrigNPC_PD[0xA])
call RemoveLocation(OrigNPC_PD[0xB])
call RemoveLocation(OrigNPC_PD[0xC])
call ForGroupBJ(OrigNPC_QD,function OrigNPC_R_X)
call TriggerSleepAction(2.)
call PlaySoundOnUnitBJ(OrigNPC_KZ,'d',GetTriggerUnit())
call TriggerSleepAction(.25)
call IssueImmediateOrderById(GetTriggerUnit(),0xD0004)
call PauseUnit(GetTriggerUnit(),true)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
call TriggerSleepAction(.25)
set OrigNPC_PD[1]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),200.,0)
set OrigNPC_PD[2]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),200.,90.)
set OrigNPC_PD[3]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),200.,180.)
set OrigNPC_PD[4]=OrigNPC_M3V(GetUnitLoc(GetTriggerUnit()),200.,270.)
call CreateNUnitsAtLoc(1,'h00X',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[1],bj_UNIT_FACING)
call SetUnitVertexColorBJ(bj_lastCreatedUnit,'d','d','d',50.)
call UnitApplyTimedLifeBJ(1.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h00X',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[2],bj_UNIT_FACING)
call SetUnitVertexColorBJ(bj_lastCreatedUnit,'d','d','d',50.)
call UnitApplyTimedLifeBJ(1.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h00X',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[3],bj_UNIT_FACING)
call SetUnitVertexColorBJ(bj_lastCreatedUnit,'d','d','d',50.)
call UnitApplyTimedLifeBJ(1.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h00X',GetOwningPlayer(GetTriggerUnit()),OrigNPC_PD[4],bj_UNIT_FACING)
call SetUnitVertexColorBJ(bj_lastCreatedUnit,'d','d','d',50.)
call UnitApplyTimedLifeBJ(1.,'BTLF',bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_PD[1])
call RemoveLocation(OrigNPC_PD[2])
call RemoveLocation(OrigNPC_PD[3])
call RemoveLocation(OrigNPC_PD[4])
call CameraSetEQNoiseForPlayer(Player(0),50.)
call CameraSetEQNoiseForPlayer(Player(1),50.)
call CameraSetEQNoiseForPlayer(Player(2),50.)
call CameraSetEQNoiseForPlayer(Player(3),50.)
call CameraSetEQNoiseForPlayer(Player(4),50.)
call CameraSetEQNoiseForPlayer(Player(5),50.)
call CameraSetEQNoiseForPlayer(Player(6),50.)
call CameraSetEQNoiseForPlayer(Player(7),50.)
call CameraSetEQNoiseForPlayer(Player(8),50.)
call CameraSetEQNoiseForPlayer(Player(9),50.)
call CameraSetEQNoiseForPlayer(Player(0xA),50.)
call CameraSetEQNoiseForPlayer(Player(0xB),50.)
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
call CreateNUnitsAtLoc(1,'h02H',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
call UnitAddAbility(bj_lastCreatedUnit,'S00B')
call IssuePointOrderByIdLoc(bj_lastCreatedUnit,0xD0099,OrigNPC_AE)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02U',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02U',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_AE)
call ForGroupBJ(OrigNPC_QD,function OrigNPC_R0X)
call TriggerSleepAction(.1)
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
set OrigNPC_CE=OrigNPC_PIV(500.,OrigNPC_AE,Condition(function OrigNPC_R1X))
call CreateNUnitsAtLoc(1,'h02U',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h02U',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call ForGroupBJ(OrigNPC_CE,function OrigNPC_R2X)
call OrigNPC_M8V(500.,OrigNPC_AE,function OrigNPC_R3X)
call DestroyGroup(OrigNPC_CE)
call RemoveLocation(OrigNPC_AE)
call TriggerSleepAction(.9)
call PauseUnit(GetTriggerUnit(),false)
call CameraClearNoiseForPlayer(Player(0))
call CameraClearNoiseForPlayer(Player(1))
call CameraClearNoiseForPlayer(Player(2))
call CameraClearNoiseForPlayer(Player(3))
call CameraClearNoiseForPlayer(Player(4))
call CameraClearNoiseForPlayer(Player(5))
call CameraClearNoiseForPlayer(Player(6))
call CameraClearNoiseForPlayer(Player(7))
call CameraClearNoiseForPlayer(Player(8))
call CameraClearNoiseForPlayer(Player(9))
call CameraClearNoiseForPlayer(Player(0xA))
call CameraClearNoiseForPlayer(Player(0xB))
endfunction
function OrigNPC_IJX takes nothing returns boolean
return(GetSpellAbilityId()=='A013')
endfunction
function OrigNPC_IKX takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_ILX takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_IMX takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_IPX takes nothing returns nothing
set OrigNPC_HE=OrigNPC_PHV(GetOwningPlayer(GetTriggerUnit()),'h023')
set OrigNPC_JE=OrigNPC_PHV(GetOwningPlayer(GetTriggerUnit()),'h024')
set OrigNPC_KE=OrigNPC_PHV(GetOwningPlayer(GetTriggerUnit()),'h00W')
call ForGroupBJ(OrigNPC_HE,function OrigNPC_IKX)
call ForGroupBJ(OrigNPC_JE,function OrigNPC_ILX)
call ForGroupBJ(OrigNPC_KE,function OrigNPC_IMX)
call DestroyGroup(OrigNPC_HE)
call DestroyGroup(OrigNPC_JE)
call DestroyGroup(OrigNPC_KE)
endfunction
function OrigNPC_AVX takes nothing returns boolean
return(GetSpellAbilityId()=='A01Q')
endfunction
function OrigNPC_AEX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01Q',GetTriggerUnit())==2)
endfunction
function OrigNPC_AXX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01Q',GetTriggerUnit())==1)
endfunction
function OrigNPC_AOX takes nothing returns nothing
if(OrigNPC_AXX())then
call ModifyHeroStat(1,GetTriggerUnit(),0,20)
call TriggerSleepAction(25.)
call ModifyHeroStat(1,GetTriggerUnit(),1,20)
else
if(OrigNPC_AEX())then
call ModifyHeroStat(1,GetTriggerUnit(),0,40)
call TriggerSleepAction(50.)
call ModifyHeroStat(1,GetTriggerUnit(),1,40)
else
call ModifyHeroStat(1,GetTriggerUnit(),0,80)
call TriggerSleepAction(50.)
call ModifyHeroStat(1,GetTriggerUnit(),1,80)
endif
endif
endfunction
function OrigNPC_AIX takes nothing returns boolean
return(GetSpellAbilityId()=='A033')
endfunction
function OrigNPC_AAX takes nothing returns boolean
return(IsUnitInRange(OrigNPC_EB,OrigNPC_XB,50.))
endfunction
function OrigNPC_ANX takes nothing returns boolean
return(IsUnitHidden(OrigNPC_XB))
endfunction
function OrigNPC_ABX takes nothing returns boolean
return(IsUnitInRange(OrigNPC_EB,OrigNPC_XB,500)==false)
endfunction
function OrigNPC_ACX takes nothing returns boolean
return GetBooleanOr(OrigNPC_ANX(),OrigNPC_ABX())
endfunction
function OrigNPC_ADX takes nothing returns boolean
return GetBooleanOr(OrigNPC_AAX(),OrigNPC_ACX())
endfunction
function OrigNPC_AFX takes nothing returns boolean
return(GetUnitFlyHeight(OrigNPC_XB)>800.)
endfunction
function OrigNPC_AGX takes nothing returns boolean
return(NPCSourceType(OrigNPC_EB)=='H00S')
endfunction
function OrigNPC_AHX takes nothing returns boolean
return(NPCSourceType(OrigNPC_EB)=='H00S')
endfunction
function OrigNPC_AJX takes nothing returns boolean
return(GetUnitFlyHeight(OrigNPC_XB)<=50.)
endfunction
function OrigNPC_AKX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A033',GetTriggerUnit())==1)
endfunction
function OrigNPC_ALX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A033',GetTriggerUnit())==2)
endfunction
function OrigNPC_AMX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A033',GetTriggerUnit())==3)
endfunction
function OrigNPC_APX takes nothing returns boolean
return(IsUnitHidden(OrigNPC_XB))or(IsUnitInRange(OrigNPC_EB,OrigNPC_XB,500)==false)
endfunction
function OrigNPC_AQX takes nothing returns boolean
return(OrigNPC_APX())
endfunction
function OrigNPC_ASX takes nothing returns nothing
set OrigNPC_EB=GetTriggerUnit()
set OrigNPC_XB=GetSpellTargetUnit()
set OrigNPC_RB=GetUnitLoc(OrigNPC_XB)
call PauseUnit(OrigNPC_EB,true)
call TriggerSleepAction(.01)
call SetUnitAnimation(OrigNPC_EB,"walk")
call SetUnitTimeScalePercent(OrigNPC_EB,250.)
call UnitAddAbility(OrigNPC_EB,'Amrf')
call UnitRemoveAbility(OrigNPC_EB,'Amrf')
call UnitAddAbility(OrigNPC_XB,'Amrf')
call UnitRemoveAbility(OrigNPC_XB,'Amrf')
call SetUnitPathing(OrigNPC_EB,false)
call SetUnitPathing(OrigNPC_XB,false)
call EnableTrigger(OrigNPC_VPV)
loop
exitwhen(OrigNPC_ADX())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
call DisableTrigger(OrigNPC_VPV)
if(OrigNPC_AQX())then
call SetUnitTimeScalePercent(OrigNPC_EB,100.)
call SetUnitPathing(OrigNPC_EB,true)
call SetUnitPathing(OrigNPC_XB,true)
call PauseUnit(OrigNPC_EB,false)
call SelectHeroSkill(OrigNPC_EB,'A033')
return
else
call PauseUnit(OrigNPC_XB,true)
set OrigNPC_OB=GetUnitLoc(OrigNPC_EB)
call CreateNUnitsAtLocFacingLocBJ(1,'h028',Player(1),OrigNPC_OB,OffsetLocation(OrigNPC_RB,90.,0))
call SetUnitTimeScalePercent(bj_lastCreatedUnit,200.)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'h028',Player(1),OrigNPC_OB,OffsetLocation(OrigNPC_RB,90.,0))
call SetUnitTimeScalePercent(bj_lastCreatedUnit,200.)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call SetUnitAnimationByIndex(OrigNPC_EB,8)
call SetUnitTimeScalePercent(OrigNPC_EB,400.)
call SetUnitFlyHeight(OrigNPC_XB,1000.,1000.)
call SetUnitAnimation(OrigNPC_XB,"death")
call SetUnitAnimation(OrigNPC_XB,"dissipate")
loop
exitwhen(OrigNPC_AFX())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
call SetUnitTimeScalePercent(OrigNPC_EB,200.)
call RemoveLocation(OrigNPC_OB)
set OrigNPC_OB=GetUnitLoc(OrigNPC_EB)
call AddSpecialEffectLocBJ(OrigNPC_OB,"Abilities\\Spells\\Human\\FlakCannons\\FlakTarget.mdl")
call DestroyEffect(bj_lastCreatedEffect)
set OrigNPC_RB=GetUnitLoc(OrigNPC_XB)
call SetUnitPositionLoc(OrigNPC_EB,OffsetLocation(OrigNPC_RB,25.,.0))
call SetUnitFlyHeight(OrigNPC_EB,800.,.0)
if(OrigNPC_AGX())then
call SetUnitAnimationByIndex(OrigNPC_EB,9)
else
call SetUnitAnimationByIndex(OrigNPC_EB,0xC)
endif
call SetUnitFacingToFaceUnitTimed(OrigNPC_EB,OrigNPC_XB,.25)
call PlaySoundOnUnitBJ(OrigNPC_KY,'d',OrigNPC_EB)
call TriggerSleepAction(.5)
call SetUnitPositionLoc(OrigNPC_EB,OrigNPC_RB)
call SetUnitTimeScalePercent(OrigNPC_EB,100.)
call SetUnitAnimation(OrigNPC_XB,"death")
call CreateNUnitsAtLocFacingLocBJ(1,'h00I',Player(1),OrigNPC_OB,OffsetLocation(OrigNPC_RB,90.,0))
call SetUnitTimeScalePercent(bj_lastCreatedUnit,200.)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'h028',Player(1),OrigNPC_OB,OffsetLocation(OrigNPC_RB,90.,0))
call SetUnitTimeScalePercent(bj_lastCreatedUnit,200.)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call SetUnitFlyHeight(OrigNPC_XB,.0,2000.)
call SetUnitFlyHeight(OrigNPC_EB,.0,2000.)
if(OrigNPC_AHX())then
call SetUnitAnimationByIndex(OrigNPC_EB,9)
else
call SetUnitAnimationByIndex(OrigNPC_EB,0xC)
endif
call SetUnitFacingToFaceUnitTimed(OrigNPC_XB,OrigNPC_EB,.5)
loop
exitwhen(OrigNPC_AJX())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
call RemoveLocation(OrigNPC_RB)
set OrigNPC_RB=GetUnitLoc(OrigNPC_XB)
call AddSpecialEffectLocBJ(OrigNPC_RB,"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
call DestroyEffect(bj_lastCreatedEffect)
if(OrigNPC_AKX())then
call UnitDamageTargetBJ(GetTriggerUnit(),OrigNPC_XB,400.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_ALX())then
call UnitDamageTargetBJ(GetTriggerUnit(),OrigNPC_XB,600.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_AMX())then
call UnitDamageTargetBJ(GetTriggerUnit(),OrigNPC_XB,800.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
call SetUnitPathing(OrigNPC_EB,true)
call SetUnitPathing(OrigNPC_XB,true)
call PauseUnit(OrigNPC_EB,false)
call PauseUnit(OrigNPC_XB,false)
call RemoveLocation(OrigNPC_RB)
call RemoveLocation(OrigNPC_OB)
endif
endfunction
function OrigNPC_AUX takes nothing returns nothing
set OrigNPC_OB=GetUnitLoc(OrigNPC_EB)
set OrigNPC_RB=GetUnitLoc(OrigNPC_XB)
call SetUnitPositionLoc(OrigNPC_EB,OrigNPC_M3V(OrigNPC_OB,30.,AngleBetweenPoints(OrigNPC_OB,OrigNPC_RB)))
call RemoveLocation(OrigNPC_OB)
call RemoveLocation(OrigNPC_RB)
endfunction
function OrigNPC_AYX takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c00B')or(NPCSourceType(GetTriggerUnit())=='h02V')
endfunction
function OrigNPC_AZX takes nothing returns boolean
return(GetSpellAbilityId()=='A02D')and(OrigNPC_AYX())
endfunction
function OrigNPC_A_X takes nothing returns boolean
return(OrigNPC_AZX())
endfunction
function OrigNPC_A0X takes nothing returns nothing
set OrigNPC_OR[1]=GetSpellAbilityUnit()
set OrigNPC_LN[1]=GetUnitLoc(GetSpellAbilityUnit())
set OrigNPC_RR[1]=GetSpellTargetUnit()
call AddSpecialEffectTargetUnitBJ("hand",OrigNPC_OR[1],"Abilities\\Spells\\Other\\Parasite\\ParasiteMissile.mdl")
set OrigNPC_AF[7]=bj_lastCreatedEffect
call EnableTrigger(OrigNPC_VSV)
endfunction
function OrigNPC_A2X takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[1])>24.)and(IsUnitAlly(OrigNPC_OR[1],GetOwningPlayer(OrigNPC_RR[1]))==false)and(DistanceBetweenPoints(OrigNPC_LN[1],OrigNPC_MN[1])<500.)
endfunction
function OrigNPC_A3X takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[1])>24.)and(GetUnitLifePercent(OrigNPC_RR[1])!=100.)and(IsUnitAlly(OrigNPC_OR[1],GetOwningPlayer(OrigNPC_RR[1])))and(DistanceBetweenPoints(OrigNPC_LN[1],OrigNPC_MN[1])<500.)
endfunction
function OrigNPC_A4X takes nothing returns boolean
return(OrigNPC_A3X())
endfunction
function OrigNPC_A5X takes nothing returns nothing
set OrigNPC_MN[1]=GetUnitLoc(OrigNPC_RR[1])
if(OrigNPC_A4X())then
call SetUnitTimeScalePercent(OrigNPC_OR[1],300.)
call SetUnitManaBJ(OrigNPC_OR[1],(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[1])-25.))
call SetWidgetLife(OrigNPC_RR[1],(GetUnitStateSwap(UNIT_STATE_LIFE,OrigNPC_RR[1])+75.))
else
if(OrigNPC_A2X())then
call SetUnitTimeScalePercent(OrigNPC_OR[1],300.)
call SetUnitManaBJ(OrigNPC_OR[1],(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[1])-25.))
call UnitDamageTargetBJ(OrigNPC_OR[1],OrigNPC_RR[1],75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call DestroyEffect(OrigNPC_AF[7])
call SetUnitTimeScalePercent(OrigNPC_OR[1],100.)
call IssueImmediateOrderById(OrigNPC_OR[1],0xD0004)
call DisableTrigger(GetTriggeringTrigger())
endif
endif
call RemoveLocation(OrigNPC_MN[1])
endfunction
function OrigNPC_A7X takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c00B')or(NPCSourceType(GetTriggerUnit())=='h02V')
endfunction
function OrigNPC_A8X takes nothing returns boolean
return(GetSpellAbilityId()=='A02D')and(OrigNPC_A7X())
endfunction
function OrigNPC_A9X takes nothing returns boolean
return(OrigNPC_A8X())
endfunction
function OrigNPC_NVX takes nothing returns nothing
call DestroyEffect(OrigNPC_AF[7])
call SetUnitTimeScalePercent(OrigNPC_OR[1],'d')
call DisableTrigger(OrigNPC_VSV)
call RemoveLocation(OrigNPC_LN[1])
endfunction
function OrigNPC_NXX takes nothing returns boolean
return(GetSpellAbilityId()=='A02D')and(NPCSourceType(GetTriggerUnit())=='R002')
endfunction
function OrigNPC_NOX takes nothing returns boolean
return(OrigNPC_NXX())
endfunction
function OrigNPC_NRX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A02D',OrigNPC_OR[0])==2)
endfunction
function OrigNPC_NIX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A02D',OrigNPC_OR[0])==1)
endfunction
function OrigNPC_NAX takes nothing returns nothing
set OrigNPC_OR[0]=GetSpellAbilityUnit()
set OrigNPC_LN[0]=GetUnitLoc(GetSpellAbilityUnit())
set OrigNPC_RR[0]=GetSpellTargetUnit()
call AddSpecialEffectTargetUnitBJ("hand",OrigNPC_OR[0],"Abilities\\Spells\\Other\\Parasite\\ParasiteMissile.mdl")
set OrigNPC_AF[6]=bj_lastCreatedEffect
if(OrigNPC_NIX())then
call EnableTrigger(OrigNPC_VWV)
else
if(OrigNPC_NRX())then
call EnableTrigger(OrigNPC_VYV)
else
call EnableTrigger(OrigNPC_VZV)
endif
endif
endfunction
function OrigNPC_NBX takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])>24.)and(IsUnitAlly(OrigNPC_OR[0],GetOwningPlayer(OrigNPC_RR[0]))==false)and(DistanceBetweenPoints(OrigNPC_LN[0],OrigNPC_MN[0])<500.)
endfunction
function OrigNPC_NCX takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])>24.)and(GetUnitLifePercent(OrigNPC_RR[0])!=100.)and(IsUnitAlly(OrigNPC_OR[0],GetOwningPlayer(OrigNPC_RR[0])))and(DistanceBetweenPoints(OrigNPC_LN[0],OrigNPC_MN[0])<500.)
endfunction
function OrigNPC_NDX takes nothing returns boolean
return(OrigNPC_NCX())
endfunction
function OrigNPC_NFX takes nothing returns nothing
set OrigNPC_MN[0]=GetUnitLoc(OrigNPC_RR[0])
if(OrigNPC_NDX())then
call SetUnitManaBJ(OrigNPC_OR[0],(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])-25.))
call SetWidgetLife(OrigNPC_RR[0],(GetUnitStateSwap(UNIT_STATE_LIFE,OrigNPC_RR[0])+25.))
else
if(OrigNPC_NBX())then
call SetUnitManaBJ(OrigNPC_OR[0],(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])-25.))
call UnitDamageTargetBJ(OrigNPC_OR[0],OrigNPC_RR[0],25.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call DestroyEffect(OrigNPC_AF[6])
call SetUnitTimeScalePercent(OrigNPC_OR[0],100.)
call IssueImmediateOrderById(OrigNPC_OR[0],0xD0004)
call DisableTrigger(GetTriggeringTrigger())
endif
endif
call RemoveLocation(OrigNPC_MN[0])
endfunction
function OrigNPC_NHX takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])>49.)and(IsUnitAlly(OrigNPC_OR[0],GetOwningPlayer(OrigNPC_RR[0]))==false)and(DistanceBetweenPoints(OrigNPC_LN[0],OrigNPC_MN[0])<500.)
endfunction
function OrigNPC_NJX takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])>49.)and(GetUnitLifePercent(OrigNPC_RR[0])!=100.)and(IsUnitAlly(OrigNPC_OR[0],GetOwningPlayer(OrigNPC_RR[0])))and(DistanceBetweenPoints(OrigNPC_LN[0],OrigNPC_MN[0])<500.)
endfunction
function OrigNPC_NKX takes nothing returns boolean
return(OrigNPC_NJX())
endfunction
function OrigNPC_NLX takes nothing returns nothing
set OrigNPC_MN[0]=GetUnitLoc(OrigNPC_RR[0])
if(OrigNPC_NKX())then
call SetUnitTimeScalePercent(OrigNPC_OR[0],200.)
call SetUnitManaBJ(OrigNPC_OR[0],(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])-50.))
call SetWidgetLife(OrigNPC_RR[0],(GetUnitStateSwap(UNIT_STATE_LIFE,OrigNPC_RR[0])+50.))
else
if(OrigNPC_NHX())then
call SetUnitTimeScalePercent(OrigNPC_OR[0],200.)
call SetUnitManaBJ(OrigNPC_OR[0],(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])-50.))
call UnitDamageTargetBJ(OrigNPC_OR[0],OrigNPC_RR[0],50.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call DestroyEffect(OrigNPC_AF[6])
call SetUnitTimeScalePercent(OrigNPC_OR[0],100.)
call IssueImmediateOrderById(OrigNPC_OR[0],0xD0004)
call DisableTrigger(GetTriggeringTrigger())
endif
endif
call RemoveLocation(OrigNPC_MN[0])
endfunction
function OrigNPC_NPX takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])>74.)and(IsUnitAlly(OrigNPC_OR[0],GetOwningPlayer(OrigNPC_RR[0]))==false)and(DistanceBetweenPoints(OrigNPC_LN[0],OrigNPC_MN[0])<500.)
endfunction
function OrigNPC_NQX takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])>74.)and(GetUnitLifePercent(OrigNPC_RR[0])!=100.)and(IsUnitAlly(OrigNPC_OR[0],GetOwningPlayer(OrigNPC_RR[0])))and(DistanceBetweenPoints(OrigNPC_LN[0],OrigNPC_MN[0])<500.)
endfunction
function OrigNPC_NSX takes nothing returns boolean
return(OrigNPC_NQX())
endfunction
function OrigNPC_NTX takes nothing returns nothing
set OrigNPC_MN[0]=GetUnitLoc(OrigNPC_RR[0])
if(OrigNPC_NSX())then
call SetUnitTimeScalePercent(OrigNPC_OR[0],300.)
call SetUnitManaBJ(OrigNPC_OR[0],(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])-75.))
call SetWidgetLife(OrigNPC_RR[0],(GetUnitStateSwap(UNIT_STATE_LIFE,OrigNPC_RR[0])+75.))
else
if(OrigNPC_NPX())then
call SetUnitTimeScalePercent(OrigNPC_OR[0],300.)
call SetUnitManaBJ(OrigNPC_OR[0],(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_OR[0])-75.))
call UnitDamageTargetBJ(OrigNPC_OR[0],OrigNPC_RR[0],75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call DestroyEffect(OrigNPC_AF[6])
call SetUnitTimeScalePercent(OrigNPC_OR[0],100.)
call IssueImmediateOrderById(OrigNPC_OR[0],0xD0004)
call DisableTrigger(GetTriggeringTrigger())
endif
endif
call RemoveLocation(OrigNPC_MN[0])
endfunction
function OrigNPC_NWX takes nothing returns boolean
return(GetSpellAbilityId()=='A02D')and(NPCSourceType(GetTriggerUnit())=='R002')
endfunction
function OrigNPC_NYX takes nothing returns boolean
return(OrigNPC_NWX())
endfunction
function OrigNPC_NZX takes nothing returns nothing
call DestroyEffect(OrigNPC_AF[6])
call SetUnitTimeScalePercent(OrigNPC_OR[0],'d')
call DisableTrigger(OrigNPC_VWV)
call DisableTrigger(OrigNPC_VYV)
call DisableTrigger(OrigNPC_VZV)
call RemoveLocation(OrigNPC_LN[0])
endfunction
function OrigNPC_N0X takes nothing returns boolean
return(GetSpellAbilityId()=='A02D')and(GetTriggerUnit()==OrigNPC_J6V)
endfunction
function OrigNPC_N1X takes nothing returns boolean
return(OrigNPC_N0X())
endfunction
function OrigNPC_N2X takes nothing returns nothing
call DisplayTextToPlayer(GetOwningPlayer(GetTriggerUnit()),0,0,"|cff32cd32Сёсэн-дзюцу лечит союзников и ранит врагов. Во время применения нужно стоять неподвижно, а цель должна оставаться рядом.|r")
call DestroyTrigger(GetTriggeringTrigger())
endfunction
function OrigNPC_N4X takes nothing returns boolean
return(GetSpellAbilityId()=='A01F')
endfunction
function OrigNPC_N5X takes nothing returns boolean
return(IsUnitEnemy(GetEnumUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_N6X takes nothing returns nothing
if(OrigNPC_N5X())then
call AddSpecialEffectLocBJ(GetUnitLoc(GetEnumUnit()),"Objects\\Spawnmodels\\Naga\\NagaDeath\\NagaDeath.mdl")
set OrigNPC_AO=bj_lastCreatedEffect
endif
endfunction
function OrigNPC_N7X takes nothing returns boolean
return(IsUnitEnemy(GetEnumUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_N8X takes nothing returns nothing
if(OrigNPC_N7X())then
call AddSpecialEffectLocBJ(GetUnitLoc(GetEnumUnit()),"Objects\\Spawnmodels\\Naga\\NagaDeath\\NagaDeath.mdl")
set OrigNPC_AO=bj_lastCreatedEffect
endif
endfunction
function OrigNPC_N9X takes nothing returns nothing
call TriggerSleepAction(.01)
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
call CreateNUnitsAtLoc(1,'h01X',GetTriggerPlayer(),OrigNPC_AE,bj_UNIT_FACING)
call RemoveLocation(OrigNPC_AE)
set OrigNPC_CD[3]=bj_lastCreatedUnit
call SetUnitAnimationByIndex(GetTriggerUnit(),3)
call SetUnitTimeScalePercent(GetTriggerUnit(),200.)
call SetUnitTurnSpeed(GetTriggerUnit(),1.)
call TriggerSleepAction(.2)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
call TriggerSleepAction(.2)
call SetUnitAnimationByIndex(GetTriggerUnit(),3)
call TriggerSleepAction(.15)
call ForGroupBJ(OrigNPC_PNV(300.,GetUnitLoc(GetTriggerUnit())),function OrigNPC_N6X)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
call TriggerSleepAction(.2)
call SetUnitAnimationByIndex(GetTriggerUnit(),3)
call TriggerSleepAction(.15)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
call TriggerSleepAction(.2)
call DestroyEffect(OrigNPC_AO)
call ForGroupBJ(OrigNPC_PNV(300.,GetUnitLoc(GetTriggerUnit())),function OrigNPC_N8X)
call SetUnitAnimationByIndex(GetTriggerUnit(),3)
call TriggerSleepAction(.15)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
call TriggerSleepAction(.2)
call SetUnitAnimationByIndex(GetTriggerUnit(),3)
call TriggerSleepAction(.15)
call DestroyEffect(OrigNPC_AO)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
call TriggerSleepAction(.2)
call SetUnitAnimationByIndex(GetTriggerUnit(),3)
call TriggerSleepAction(.15)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
call TriggerSleepAction(.2)
call SetUnitAnimationByIndex(GetTriggerUnit(),3)
call RemoveUnit(OrigNPC_CD[3])
call TriggerSleepAction(5.)
call SetUnitTimeScalePercent(GetTriggerUnit(),100.)
call SetUnitTurnSpeed(GetTriggerUnit(),.6)
endfunction
function OrigNPC_BHX takes nothing returns boolean
return(GetSpellAbilityId()=='A016')and(NPCSourceType(GetTriggerUnit())=='R007')
endfunction
function OrigNPC_BJX takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),9)
endfunction
function OrigNPC_BLX takes nothing returns boolean
return(GetSpellAbilityId()=='A016')
endfunction
function OrigNPC_BMX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_BPX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),50.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_BQX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_BSX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),50.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_BTX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_BUX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),50.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_BWX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_BYX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),50.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_BZX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_B_X takes nothing returns boolean
return(IsUnitIllusion(GetEnumUnit()))
endfunction
function OrigNPC_B0X takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),50.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
if(OrigNPC_B_X())then
call KillUnit(GetEnumUnit())
endif
endfunction
function OrigNPC_B1X takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_B2X takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_B3X takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_B4X takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_B5X takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_B6X takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_B7X takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_B8X takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_B9X takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_CVX takes nothing returns boolean
return(IsUnitIllusion(GetEnumUnit()))
endfunction
function OrigNPC_CEX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
if(OrigNPC_CVX())then
call KillUnit(GetEnumUnit())
endif
endfunction
function OrigNPC_CXX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_COX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),25.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_CRX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_CIX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),25.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_CAX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_CNX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),25.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_CBX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_CCX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),25.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_CDX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_CFX takes nothing returns boolean
return(IsUnitIllusion(GetEnumUnit()))
endfunction
function OrigNPC_CGX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),25.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
if(OrigNPC_CFX())then
call KillUnit(GetEnumUnit())
endif
endfunction
function OrigNPC_CHX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_CJX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_CKX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_CLX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_CMX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_CPX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_CQX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_CSX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_CTX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_OC)))
endfunction
function OrigNPC_CUX takes nothing returns boolean
return(IsUnitIllusion(GetEnumUnit()))
endfunction
function OrigNPC_CWX takes nothing returns nothing
call UnitDamageTargetBJ(OrigNPC_OC,GetEnumUnit(),100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
if(OrigNPC_CUX())then
call KillUnit(GetEnumUnit())
endif
endfunction
function OrigNPC_CYX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A016',GetTriggerUnit())==4)
endfunction
function OrigNPC_CZX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A016',GetTriggerUnit())==3)
endfunction
function OrigNPC_C_X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A016',GetTriggerUnit())==2)
endfunction
function OrigNPC_C0X takes nothing returns nothing
set OrigNPC_OC=GetTriggerUnit()
set OrigNPC_EC=GetSpellTargetLoc()
set OrigNPC_RC=GetUnitLoc(GetTriggerUnit())
call TriggerSleepAction(.9)
if(OrigNPC_C_X())then
call CreateNUnitsAtLocFacingLocBJ(1,'h025',GetOwningPlayer(GetTriggerUnit()),OrigNPC_EC,OrigNPC_RC)
set OrigNPC_IC=bj_lastCreatedUnit
call UnitAddAbility(OrigNPC_IC,'A02I')
call SetUnitAbilityLevelSwapped('A02I',bj_lastCreatedUnit,2)
call UnitApplyTimedLifeBJ(5.,'BTLF',bj_lastCreatedUnit)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(350.,OrigNPC_EC,Condition(function OrigNPC_BMX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_BPX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(350.,OrigNPC_EC,Condition(function OrigNPC_BQX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_BSX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(350.,OrigNPC_EC,Condition(function OrigNPC_BTX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_BUX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(350.,OrigNPC_EC,Condition(function OrigNPC_BWX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_BYX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(350.,OrigNPC_EC,Condition(function OrigNPC_BZX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_B0X)
call DestroyGroup(OrigNPC_XC)
else
if(OrigNPC_CZX())then
call CreateNUnitsAtLocFacingLocBJ(1,'h025',GetTriggerPlayer(),OrigNPC_EC,OrigNPC_RC)
set OrigNPC_IC=bj_lastCreatedUnit
call UnitAddAbility(OrigNPC_IC,'A02I')
call SetUnitAbilityLevelSwapped('A02I',bj_lastCreatedUnit,2)
call UnitApplyTimedLifeBJ(5.,'BTLF',bj_lastCreatedUnit)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(400.,OrigNPC_EC,Condition(function OrigNPC_B1X))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_B2X)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(400.,OrigNPC_EC,Condition(function OrigNPC_B3X))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_B4X)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(400.,OrigNPC_EC,Condition(function OrigNPC_B5X))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_B6X)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(400.,OrigNPC_EC,Condition(function OrigNPC_B7X))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_B8X)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(400.,OrigNPC_EC,Condition(function OrigNPC_B9X))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_CEX)
call DestroyGroup(OrigNPC_XC)
else
if(OrigNPC_CYX())then
call CreateNUnitsAtLocFacingLocBJ(1,'h025',GetTriggerPlayer(),OrigNPC_EC,OrigNPC_RC)
set OrigNPC_IC=bj_lastCreatedUnit
call UnitAddAbility(OrigNPC_IC,'A02I')
call SetUnitAbilityLevelSwapped('A02I',bj_lastCreatedUnit,4)
call UnitApplyTimedLifeBJ(5.,'BTLF',bj_lastCreatedUnit)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(550.,OrigNPC_EC,Condition(function OrigNPC_CHX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_CJX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(550.,OrigNPC_EC,Condition(function OrigNPC_CKX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_CLX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(550.,OrigNPC_EC,Condition(function OrigNPC_CMX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_CPX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(550.,OrigNPC_EC,Condition(function OrigNPC_CQX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_CSX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(550.,OrigNPC_EC,Condition(function OrigNPC_CTX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_CWX)
call DestroyGroup(OrigNPC_XC)
else
call CreateNUnitsAtLocFacingLocBJ(1,'h025',GetTriggerPlayer(),OrigNPC_EC,OrigNPC_RC)
set OrigNPC_IC=bj_lastCreatedUnit
call UnitAddAbility(OrigNPC_IC,'A02I')
call SetUnitAbilityLevelSwapped('A02I',bj_lastCreatedUnit,1)
call UnitApplyTimedLifeBJ(5.,'BTLF',bj_lastCreatedUnit)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(200.,OrigNPC_EC,Condition(function OrigNPC_CXX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_COX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(200.,OrigNPC_EC,Condition(function OrigNPC_CRX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_CIX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(200.,OrigNPC_EC,Condition(function OrigNPC_CAX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_CNX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(200.,OrigNPC_EC,Condition(function OrigNPC_CBX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_CCX)
call DestroyGroup(OrigNPC_XC)
call TriggerSleepAction(.8)
call IssueImmediateOrderById(OrigNPC_IC,0xD0080)
set OrigNPC_XC=OrigNPC_PIV(200.,OrigNPC_EC,Condition(function OrigNPC_CDX))
call ForGroupBJ(OrigNPC_XC,function OrigNPC_CGX)
call DestroyGroup(OrigNPC_XC)
endif
endif
endif
call RemoveLocation(OrigNPC_EC)
call RemoveLocation(OrigNPC_RC)
endfunction
function OrigNPC_C2X takes nothing returns boolean
return(GetSpellAbilityId()=='A016')or(GetSpellAbilityId()=='A00H')
endfunction
function OrigNPC_C3X takes nothing returns boolean
return(OrigNPC_C2X())
endfunction
function OrigNPC_C4X takes nothing returns nothing
set OrigNPC_NC=GetSpellTargetLoc()
call TriggerSleepAction(.9)
call AddSpecialEffectLocBJ(OrigNPC_NC,"Units\\NightElf\\Wisp\\WispExplode.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call CreateNUnitsAtLoc(1,'h01U',GetOwningPlayer(GetTriggerUnit()),OrigNPC_NC,bj_UNIT_FACING)
set OrigNPC_AE=GetUnitLoc(bj_lastCreatedUnit)
call UnitApplyTimedLifeBJ(3.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h01U',GetOwningPlayer(GetTriggerUnit()),OffsetLocation(OrigNPC_AE,100.,0),bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(4.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLoc(1,'h01U',GetOwningPlayer(GetTriggerUnit()),OffsetLocation(OrigNPC_AE,-200.,0),bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(4.,'BTLF',bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_AE)
call RemoveLocation(OrigNPC_NC)
endfunction
function OrigNPC_DRX takes nothing returns boolean
return(GetSpellAbilityId()=='A00Z')and(NPCSourceType(GetTriggerUnit())!='c000')
endfunction
function OrigNPC_DIX takes nothing returns nothing
set OrigNPC_GO[0]=GetSpellAbilityUnit()
call UnitAddAbility(OrigNPC_GO[0],'Amrf')
call UnitRemoveAbility(OrigNPC_GO[0],'Amrf')
call CreateNUnitsAtLoc(1,'h02H',GetOwningPlayer(OrigNPC_GO[0]),GetUnitLoc(OrigNPC_GO[0]),GetUnitFacing(OrigNPC_GO[0]))
set OrigNPC_GO[1]=bj_lastCreatedUnit
call UnitAddAbility(OrigNPC_GO[1],'A00A')
call UnitApplyTimedLifeBJ(3.,'BTLF',OrigNPC_GO[1])
call CreateNUnitsAtLoc(1,'h02H',GetOwningPlayer(OrigNPC_GO[0]),GetUnitLoc(OrigNPC_GO[0]),GetUnitFacing(OrigNPC_GO[0]))
set OrigNPC_GO[2]=bj_lastCreatedUnit
call UnitAddAbility(OrigNPC_GO[2],'A00A')
call UnitApplyTimedLifeBJ(3.,'BTLF',OrigNPC_GO[2])
call CreateNUnitsAtLoc(1,'h02H',GetOwningPlayer(OrigNPC_GO[0]),GetUnitLoc(OrigNPC_GO[0]),GetUnitFacing(OrigNPC_GO[0]))
set OrigNPC_GO[3]=bj_lastCreatedUnit
call UnitAddAbility(OrigNPC_GO[3],'A00A')
call UnitApplyTimedLifeBJ(3.,'BTLF',OrigNPC_GO[3])
set OrigNPC_HO=GetUnitLoc(OrigNPC_GO[0])
call EnableTrigger(OrigNPC_V9V)
call EnableTrigger(OrigNPC_EEV)
call SetUnitFlyHeight(OrigNPC_GO[0],1000.,500.)
call SetUnitFlyHeight(OrigNPC_GO[1],1000.,500.)
call SetUnitFlyHeight(OrigNPC_GO[2],1000.,500.)
call SetUnitFlyHeight(OrigNPC_GO[3],1000.,500.)
call TriggerSleepAction(2.5)
call SetUnitFlyHeight(OrigNPC_GO[0],400.,1000.)
call SetUnitFlyHeight(OrigNPC_GO[1],400.,1000.)
call SetUnitFlyHeight(OrigNPC_GO[2],400.,1000.)
call SetUnitFlyHeight(OrigNPC_GO[3],400.,1000.)
call DisableTrigger(OrigNPC_V9V)
call SetUnitAnimation(OrigNPC_GO[0],"attack")
call SetUnitTimeScalePercent(OrigNPC_GO[0],130.)
call SetUnitFlyHeight(OrigNPC_GO[0],.0,1800.)
call SetUnitTimeScalePercent(OrigNPC_GO[1],130.)
call SetUnitFlyHeight(OrigNPC_GO[1],.0,1800.)
call SetUnitTimeScalePercent(OrigNPC_GO[2],130.)
call SetUnitFlyHeight(OrigNPC_GO[2],.0,1800.)
call SetUnitFlyHeight(OrigNPC_GO[3],.0,1800.)
call DisableTrigger(OrigNPC_EEV)
call RemoveLocation(OrigNPC_HO)
call TriggerSleepAction(.25)
call SetUnitTimeScalePercent(OrigNPC_GO[0],100.)
endfunction
function OrigNPC_DNX takes nothing returns nothing
call SetUnitAnimation(OrigNPC_GO[0],"spell")
endfunction
function OrigNPC_DCX takes nothing returns boolean
return(GetSpellAbilityId()=='A00Z')and(NPCSourceType(GetTriggerUnit())!='c000')
endfunction
function OrigNPC_DDX takes nothing returns nothing
call DisableTrigger(OrigNPC_EEV)
call RemoveUnit(OrigNPC_GO[1])
call RemoveUnit(OrigNPC_GO[2])
call SetUnitTimeScalePercent(OrigNPC_GO[0],100.)
call DisableTrigger(OrigNPC_V9V)
call SetUnitFlyHeight(OrigNPC_GO[0],.0,2000.)
endfunction
function OrigNPC_DGX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_GO[0])))
endfunction
function OrigNPC_DHX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_GO[0])))
endfunction
function OrigNPC_DJX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_GO[0])))
endfunction
function OrigNPC_DKX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(OrigNPC_GO[0])))
endfunction
function OrigNPC_DLX takes nothing returns nothing
set OrigNPC_ZF=GetUnitLoc(OrigNPC_GO[0])
call CreateNUnitsAtLoc(1,'h02H',GetOwningPlayer(OrigNPC_GO[0]),OrigNPC_ZF,GetUnitFacing(OrigNPC_GO[0]))
call RemoveLocation(OrigNPC_ZF)
set OrigNPC_GO[4]=bj_lastCreatedUnit
call SetUnitFlyHeight(OrigNPC_GO[4],600.,20000.)
call UnitAddAbility(OrigNPC_GO[4],'A00A')
call UnitApplyTimedLifeBJ(.5,'BTLF',OrigNPC_GO[4])
call IssueTargetOrderById(OrigNPC_GO[1],0xD007F,GroupPickRandomUnit(OrigNPC_PIV(600.,OrigNPC_HO,Condition(function OrigNPC_DGX))))
call IssueTargetOrderById(OrigNPC_GO[2],0xD007F,GroupPickRandomUnit(OrigNPC_PIV(600.,OrigNPC_HO,Condition(function OrigNPC_DHX))))
call IssueTargetOrderById(OrigNPC_GO[3],0xD007F,GroupPickRandomUnit(OrigNPC_PIV(600.,OrigNPC_HO,Condition(function OrigNPC_DJX))))
call IssueTargetOrderById(OrigNPC_GO[4],0xD007F,GroupPickRandomUnit(OrigNPC_PIV(600.,OrigNPC_HO,Condition(function OrigNPC_DKX))))
endfunction
function OrigNPC_DPX takes nothing returns boolean
return(GetSpellAbilityId()=='A00Z')and(NPCSourceType(GetTriggerUnit())!='c000')
endfunction
function OrigNPC_DQX takes nothing returns nothing
call SetUnitFlyHeight(GetEnumUnit(),500.,1000.)
call UnitApplyTimedLifeBJ(2.,'BTLF',GetEnumUnit())
endfunction
function OrigNPC_DSX takes nothing returns nothing
call TriggerSleepAction(.01)
call CreateNUnitsAtLoc(0xC,'h02K',GetOwningPlayer(OrigNPC_GO[0]),OrigNPC_M3V(OrigNPC_HO,GetRandomReal(0,100.),GetRandomReal(0,360)),GetRandomReal(.0,359.))
set OrigNPC_CE=OrigNPC_PHV(GetOwningPlayer(OrigNPC_GO[0]),'h02K')
call ForGroupBJ(OrigNPC_CE,function OrigNPC_DQX)
call DestroyGroup(OrigNPC_CE)
endfunction
function OrigNPC_DUX takes nothing returns boolean
return(GetSpellAbilityId()=='A01C')
endfunction
function OrigNPC_DWX takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),3)
endfunction
function OrigNPC_D2X takes nothing returns boolean
return(GetSpellAbilityId()=='A01C')and(GetUnitAbilityLevelSwapped('A01C',GetTriggerUnit())==3)
endfunction
function OrigNPC_D3X takes nothing returns boolean
return(OrigNPC_D2X())
endfunction
function OrigNPC_D4X takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_D5X takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_D6X takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_D7X takes nothing returns nothing
set OrigNPC_HE=OrigNPC_PHV(GetOwningPlayer(GetTriggerUnit()),'h00L')
set OrigNPC_JE=OrigNPC_PHV(GetOwningPlayer(GetTriggerUnit()),'h00M')
set OrigNPC_KE=OrigNPC_PHV(GetOwningPlayer(GetTriggerUnit()),'h01I')
call ForGroupBJ(OrigNPC_HE,function OrigNPC_D4X)
call ForGroupBJ(OrigNPC_JE,function OrigNPC_D5X)
call ForGroupBJ(OrigNPC_KE,function OrigNPC_D6X)
call DestroyGroup(OrigNPC_HE)
call DestroyGroup(OrigNPC_JE)
call DestroyGroup(OrigNPC_KE)
set OrigNPC_DR=GetUnitLoc(GetTriggerUnit())
set OrigNPC_KR=OrigNPC_M3V(OrigNPC_DR,200.,GetUnitFacing(GetTriggerUnit()))
call CreateNUnitsAtLoc(1,'h00M',GetOwningPlayer(GetTriggerUnit()),OrigNPC_KR,GetUnitFacing(GetTriggerUnit()))
set OrigNPC_ZF=GetUnitLoc(bj_lastCreatedUnit)
call AddSpecialEffectLocBJ(OrigNPC_ZF,"Abilities\\Spells\\Human\\FlakCannons\\FlakTarget.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call IssueImmediateOrderById(bj_lastCreatedUnit,0xD02B0)
call SelectUnitAddForPlayer(bj_lastCreatedUnit,GetOwningPlayer(GetTriggerUnit()))
call RemoveLocation(OrigNPC_DR)
call RemoveLocation(OrigNPC_KR)
call RemoveLocation(OrigNPC_ZF)
endfunction
function OrigNPC_FDX takes nothing returns boolean
return(GetSpellAbilityId()=='A00U')
endfunction
function OrigNPC_FFX takes nothing returns nothing
set OrigNPC_AR=GetTriggerUnit()
call TriggerExecute(OrigNPC_EFV)
call TriggerSleepAction(1.)
call TriggerExecute(OrigNPC_EGV)
call TriggerSleepAction(1.)
call TriggerExecute(OrigNPC_EHV)
call TriggerSleepAction(1.)
call TriggerExecute(OrigNPC_EJV)
call TriggerSleepAction(1.)
call TriggerExecute(OrigNPC_EKV)
call TriggerSleepAction(1.)
call TriggerExecute(OrigNPC_ELV)
call TriggerSleepAction(1.)
call TriggerExecute(OrigNPC_EMV)
call TriggerSleepAction(1.)
call TriggerExecute(OrigNPC_EPV)
call TriggerSleepAction(1.)
call ModifyHeroStat(1,OrigNPC_AR,1,OrigNPC_XN)
call ModifyHeroStat(1,OrigNPC_AR,1,OrigNPC_ON)
call ModifyHeroStat(1,OrigNPC_AR,1,OrigNPC_RN)
call ModifyHeroStat(1,OrigNPC_AR,1,OrigNPC_IN)
call ModifyHeroStat(1,OrigNPC_AR,1,OrigNPC_AN)
call ModifyHeroStat(1,OrigNPC_AR,1,OrigNPC_NN)
call ModifyHeroStat(1,OrigNPC_AR,1,OrigNPC_BN)
call ModifyHeroStat(1,OrigNPC_AR,1,OrigNPC_CN)
endfunction
function OrigNPC_FHX takes nothing returns boolean
return(GetSpellAbilityId()=='A00U')
endfunction
function OrigNPC_FJX takes nothing returns nothing
call TriggerSleepAction(.01)
call SetUnitAnimationByIndex(GetTriggerUnit(),9)
call TriggerSleepAction(.25)
call SetUnitTimeScalePercent(GetTriggerUnit(),150.)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
call TriggerSleepAction(.25)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
call TriggerSleepAction(.25)
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
call TriggerSleepAction(.35)
call SetUnitTimeScalePercent(GetTriggerUnit(),100.)
endfunction
function OrigNPC_FLX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==2)
endfunction
function OrigNPC_FMX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==1)
endfunction
function OrigNPC_FPX takes nothing returns nothing
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
if(OrigNPC_FMX())then
set OrigNPC_XN=GetRandomInt(-5,0xA)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_XN)
else
if(OrigNPC_FLX())then
set OrigNPC_XN=GetRandomInt(-0xA,20)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_XN)
else
set OrigNPC_XN=GetRandomInt(-20,40)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_XN)
endif
endif
endfunction
function OrigNPC_FSX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==2)
endfunction
function OrigNPC_FTX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==1)
endfunction
function OrigNPC_FUX takes nothing returns nothing
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
if(OrigNPC_FTX())then
set OrigNPC_ON=GetRandomInt(-5,0xA)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_ON)
else
if(OrigNPC_FSX())then
set OrigNPC_ON=GetRandomInt(-0xA,20)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_ON)
else
set OrigNPC_ON=GetRandomInt(-20,40)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_ON)
endif
endif
endfunction
function OrigNPC_FYX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==2)
endfunction
function OrigNPC_FZX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==1)
endfunction
function OrigNPC_F_X takes nothing returns nothing
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
if(OrigNPC_FZX())then
set OrigNPC_RN=GetRandomInt(-5,0xA)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_RN)
else
if(OrigNPC_FYX())then
set OrigNPC_RN=GetRandomInt(-0xA,20)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_RN)
else
set OrigNPC_RN=GetRandomInt(-20,40)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_RN)
endif
endif
endfunction
function OrigNPC_F1X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==2)
endfunction
function OrigNPC_F2X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==1)
endfunction
function OrigNPC_F3X takes nothing returns nothing
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
if(OrigNPC_F2X())then
set OrigNPC_IN=GetRandomInt(-5,0xA)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_IN)
else
if(OrigNPC_F1X())then
set OrigNPC_IN=GetRandomInt(-0xA,20)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_IN)
else
set OrigNPC_IN=GetRandomInt(-20,40)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_IN)
endif
endif
endfunction
function OrigNPC_F5X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==2)
endfunction
function OrigNPC_F6X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==1)
endfunction
function OrigNPC_F7X takes nothing returns nothing
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
if(OrigNPC_F6X())then
set OrigNPC_AN=GetRandomInt(0,5)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_AN)
else
if(OrigNPC_F5X())then
set OrigNPC_AN=GetRandomInt(-0xA,20)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_AN)
else
set OrigNPC_AN=GetRandomInt(-20,40)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_AN)
endif
endif
endfunction
function OrigNPC_F9X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==2)
endfunction
function OrigNPC_GVX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==1)
endfunction
function OrigNPC_GEX takes nothing returns nothing
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
if(OrigNPC_GVX())then
set OrigNPC_NN=GetRandomInt(-5,0xA)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_NN)
else
if(OrigNPC_F9X())then
set OrigNPC_NN=GetRandomInt(-0xA,20)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_NN)
else
set OrigNPC_NN=GetRandomInt(-20,40)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_NN)
endif
endif
endfunction
function OrigNPC_GOX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==2)
endfunction
function OrigNPC_GRX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==1)
endfunction
function OrigNPC_GIX takes nothing returns nothing
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
if(OrigNPC_GRX())then
set OrigNPC_BN=GetRandomInt(-5,0xA)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_BN)
else
if(OrigNPC_GOX())then
set OrigNPC_BN=GetRandomInt(-0xA,20)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_BN)
else
set OrigNPC_BN=GetRandomInt(-20,40)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_BN)
endif
endif
endfunction
function OrigNPC_GNX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==2)
endfunction
function OrigNPC_GBX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00U',OrigNPC_AR)==1)
endfunction
function OrigNPC_GCX takes nothing returns nothing
call SetUnitAnimationByIndex(GetTriggerUnit(),6)
if(OrigNPC_GBX())then
set OrigNPC_CN=GetRandomInt(-5,0xA)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_CN)
else
if(OrigNPC_GNX())then
set OrigNPC_CN=GetRandomInt(-0xA,20)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_CN)
else
set OrigNPC_CN=GetRandomInt(-20,40)
call ModifyHeroStat(1,OrigNPC_AR,0,OrigNPC_CN)
endif
endif
endfunction
function OrigNPC_GFX takes nothing returns boolean
return(GetSpellAbilityId()=='A021')
endfunction
function OrigNPC_GGX takes nothing returns nothing
set OrigNPC_PA=GetEnumUnit()
endfunction
function OrigNPC_GHX takes nothing returns nothing
call SetUnitFlyHeight(GetTriggerUnit(),500.,250.)
endfunction
function OrigNPC_GJX takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',90.)
endfunction
function OrigNPC_GKX takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',80.)
endfunction
function OrigNPC_GLX takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',70.)
endfunction
function OrigNPC_GMX takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',60.)
endfunction
function OrigNPC_GPX takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',50.)
endfunction
function OrigNPC_GQX takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',40.)
endfunction
function OrigNPC_GSX takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',30.)
endfunction
function OrigNPC_GTX takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',20.)
endfunction
function OrigNPC_GUX takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',10.)
endfunction
function OrigNPC_GWX takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',.0)
endfunction
function OrigNPC_GYX takes nothing returns nothing
call UnitApplyTimedLifeBJ(9.,'BTLF',GetEnumUnit())
endfunction
function OrigNPC_GZX takes nothing returns nothing
call SetUnitFlyHeight(GetTriggerUnit(),.0,500.)
endfunction
function OrigNPC_G_X takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',10.)
endfunction
function OrigNPC_G0X takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',20.)
endfunction
function OrigNPC_G1X takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',30.)
endfunction
function OrigNPC_G2X takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',40.)
endfunction
function OrigNPC_G3X takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',50.)
endfunction
function OrigNPC_G4X takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',60.)
endfunction
function OrigNPC_G5X takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',70.)
endfunction
function OrigNPC_G6X takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',80.)
endfunction
function OrigNPC_G7X takes nothing returns nothing
call SetUnitVertexColorBJ(GetEnumUnit(),.0,30.,'d',90.)
endfunction
function OrigNPC_G8X takes nothing returns nothing
call RemoveUnit(GetEnumUnit())
endfunction
function OrigNPC_G9X takes nothing returns nothing
call TriggerSleepAction(.01)
set OrigNPC_KA=GetSpellAbilityUnit()
set OrigNPC_LA[0]=GetUnitLoc(OrigNPC_KA)
call UnitAddAbility(OrigNPC_KA,'Amrf')
call UnitRemoveAbility(OrigNPC_KA,'Amrf')
call UnitAddAbility(OrigNPC_KEV,'S000')
call PauseUnit(OrigNPC_KEV,true)
call CreateNUnitsAtLocFacingLocBJ(1,'e002',GetOwningPlayer(OrigNPC_KA),OrigNPC_LA[0],OrigNPC_LA[0])
set OrigNPC_LA[1]=GetUnitLoc(bj_lastCreatedUnit)
call GroupAddUnit(OrigNPC_MA,bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'e002',GetOwningPlayer(OrigNPC_KA),OrigNPC_M3V(OrigNPC_LA[1],700.,0),GetSpellTargetLoc())
call UnitApplyTimedLifeBJ(12.,'BTLF',bj_lastCreatedUnit)
call GroupAddUnit(OrigNPC_MA,bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'e002',GetOwningPlayer(OrigNPC_KA),OrigNPC_M3V(OrigNPC_LA[1],700.,45.),GetSpellTargetLoc())
call UnitApplyTimedLifeBJ(12.,'BTLF',bj_lastCreatedUnit)
call GroupAddUnit(OrigNPC_MA,bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'e002',GetOwningPlayer(OrigNPC_KA),OrigNPC_M3V(OrigNPC_LA[1],700.,90.),GetSpellTargetLoc())
call UnitApplyTimedLifeBJ(12.,'BTLF',bj_lastCreatedUnit)
call GroupAddUnit(OrigNPC_MA,bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'e002',GetOwningPlayer(OrigNPC_KA),OrigNPC_M3V(OrigNPC_LA[1],700.,135.),GetSpellTargetLoc())
call UnitApplyTimedLifeBJ(12.,'BTLF',bj_lastCreatedUnit)
call GroupAddUnit(OrigNPC_MA,bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'e002',GetOwningPlayer(OrigNPC_KA),OrigNPC_M3V(OrigNPC_LA[1],700.,180.),GetSpellTargetLoc())
call UnitApplyTimedLifeBJ(12.,'BTLF',bj_lastCreatedUnit)
call GroupAddUnit(OrigNPC_MA,bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'e002',GetOwningPlayer(OrigNPC_KA),OrigNPC_M3V(OrigNPC_LA[1],700.,225.),GetSpellTargetLoc())
call UnitApplyTimedLifeBJ(12.,'BTLF',bj_lastCreatedUnit)
call GroupAddUnit(OrigNPC_MA,bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'e002',GetOwningPlayer(OrigNPC_KA),OrigNPC_M3V(OrigNPC_LA[1],700.,270.),GetSpellTargetLoc())
call UnitApplyTimedLifeBJ(12.,'BTLF',bj_lastCreatedUnit)
call GroupAddUnit(OrigNPC_MA,bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'e002',GetOwningPlayer(OrigNPC_KA),OrigNPC_M3V(OrigNPC_LA[1],700.,315.),GetSpellTargetLoc())
call UnitApplyTimedLifeBJ(12.,'BTLF',bj_lastCreatedUnit)
call GroupAddUnit(OrigNPC_MA,bj_lastCreatedUnit)
call ForGroupBJ(OrigNPC_PBV('h01E'),function OrigNPC_GGX)
call IssuePointOrderByIdLoc(OrigNPC_PA,0xD0012,OrigNPC_M3V(OrigNPC_LA[0],GetRandomReal(-800.,800.),GetRandomReal(0,360)))
call SetUnitFlyHeight(OrigNPC_PA,GetRandomReal(-100.,400.),GetRandomReal(200.,400.))
call RemoveLocation(OrigNPC_LA[0])
call EnableTrigger(OrigNPC_ETV)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GHX)
call SetUnitFlyHeight(OrigNPC_KA,500.,250.)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GJX)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GKX)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GLX)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GMX)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GPX)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GQX)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GSX)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GTX)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GUX)
call TriggerSleepAction(.2)
call UnitRemoveAbility(OrigNPC_KEV,'S000')
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GWX)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GYX)
call TriggerSleepAction(6.3)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_GZX)
call SetUnitFlyHeight(OrigNPC_KA,.0,500.)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_G_X)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_G0X)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_G1X)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_G2X)
call TriggerSleepAction(.2)
call PauseUnit(OrigNPC_KEV,false)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_G3X)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_G4X)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_G5X)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_G6X)
call TriggerSleepAction(.2)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_G7X)
call TriggerSleepAction(.2)
call DisableTrigger(OrigNPC_ETV)
call ForGroupBJ(OrigNPC_MA,function OrigNPC_G8X)
call RemoveLocation(OrigNPC_LA[1])
endfunction
function OrigNPC_HEX takes nothing returns boolean
return(GetSpellAbilityId()=='A021')
endfunction
function OrigNPC_HXX takes nothing returns nothing
set OrigNPC_ZF=GetUnitLoc(GetTriggerUnit())
set OrigNPC_VG=GetSpellTargetLoc()
call CreateNUnitsAtLocFacingLocBJ(1,'e000',GetOwningPlayer(GetTriggerUnit()),OrigNPC_ZF,OrigNPC_VG)
set OrigNPC_TV=bj_lastCreatedUnit
set OrigNPC_WV=GetUnitFacing(OrigNPC_TV)
call IssuePointOrderByIdLoc(OrigNPC_TV,0xD0012,OrigNPC_M3V(OrigNPC_ZF,3000.,OrigNPC_WV))
call RemoveLocation(OrigNPC_ZF)
call RemoveLocation(OrigNPC_VG)
call OrigNPC_M0V(.5)
call IssueImmediateOrderById(OrigNPC_TV,0xD009E)
set OrigNPC_ZF=GetUnitLoc(GetTriggerUnit())
call IssuePointOrderByIdLoc(OrigNPC_TV,0xD0012,OrigNPC_M3V(OrigNPC_ZF,3000.,OrigNPC_WV))
call RemoveLocation(OrigNPC_ZF)
call OrigNPC_M0V(2.)
call IssueImmediateOrderById(OrigNPC_TV,0xD009E)
set OrigNPC_ZF=GetUnitLoc(GetTriggerUnit())
call IssuePointOrderByIdLoc(OrigNPC_TV,0xD0012,OrigNPC_M3V(OrigNPC_ZF,3000.,OrigNPC_WV))
call RemoveLocation(OrigNPC_ZF)
call OrigNPC_M0V(2.)
call IssueImmediateOrderById(OrigNPC_TV,0xD009E)
set OrigNPC_ZF=GetUnitLoc(GetTriggerUnit())
call IssuePointOrderByIdLoc(OrigNPC_TV,0xD0012,OrigNPC_M3V(OrigNPC_ZF,3000.,OrigNPC_WV))
call RemoveLocation(OrigNPC_ZF)
call OrigNPC_M0V(1.)
call AddSpecialEffectTargetUnitBJ("Chest",bj_lastCreatedUnit,"Objects\\Spawnmodels\\Naga\\NagaDeath\\NagaDeath.mdl")
set OrigNPC_YE=bj_lastCreatedEffect
call RemoveUnit(OrigNPC_TV)
call TriggerSleepAction(2)
call DestroyEffect(OrigNPC_YE)
endfunction
function OrigNPC_HRX takes nothing returns boolean
return(IsUnitAliveBJ(OrigNPC_PA))
endfunction
function OrigNPC_HIX takes nothing returns nothing
set OrigNPC_LA[0]=GetUnitLoc(OrigNPC_KA)
call IssuePointOrderByIdLoc(OrigNPC_PA,0xD0012,OrigNPC_M3V(OrigNPC_LA[0],GetRandomReal(500.,800.),GetRandomReal(0,360)))
call SetUnitFlyHeight(OrigNPC_PA,GetRandomReal(-100.,400.),GetRandomReal(300.,700.))
call RemoveLocation(OrigNPC_LA[0])
endfunction
function OrigNPC_H8X takes nothing returns boolean
return(GetSpellAbilityId()=='A00X')
endfunction
function OrigNPC_H9X takes nothing returns boolean
return(IsUnitInRange(OrigNPC_NB,OrigNPC_BB,75.))
endfunction
function OrigNPC_JVX takes nothing returns boolean
return(IsUnitHidden(OrigNPC_BB))
endfunction
function OrigNPC_JEX takes nothing returns boolean
return(IsUnitInRange(OrigNPC_NB,OrigNPC_BB,500)==false)
endfunction
function OrigNPC_JXX takes nothing returns boolean
return GetBooleanOr(OrigNPC_JVX(),OrigNPC_JEX())
endfunction
function OrigNPC_JOX takes nothing returns boolean
return GetBooleanOr(OrigNPC_H9X(),OrigNPC_JXX())
endfunction
function OrigNPC_JRX takes nothing returns boolean
return(IsUnitHidden(GetSpellTargetUnit()))or(IsUnitInRange(OrigNPC_NB,OrigNPC_BB,500)==false)
endfunction
function OrigNPC_JIX takes nothing returns boolean
return(OrigNPC_JRX())
endfunction
function OrigNPC_JAX takes nothing returns nothing
call TriggerSleepAction(.01)
set OrigNPC_NB=GetTriggerUnit()
set OrigNPC_BB=GetSpellTargetUnit()
call SetUnitPathing(GetTriggerUnit(),false)
call SetUnitFacingToFaceUnitTimed(OrigNPC_BB,OrigNPC_NB,.25)
call SetUnitTimeScalePercent(OrigNPC_NB,150.)
call SetUnitAnimation(OrigNPC_NB,"attack")
call EnableTrigger(OrigNPC_E4V)
loop
exitwhen(OrigNPC_JOX())
call TriggerSleepAction(RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL,.1))
endloop
call DisableTrigger(OrigNPC_E4V)
call SetUnitPathing(GetTriggerUnit(),true)
if(OrigNPC_JIX())then
call SetUnitTimeScalePercent(OrigNPC_NB,100.)
return
else
call SetUnitTimeScalePercent(OrigNPC_NB,100.)
set OrigNPC_IB=GetUnitLoc(OrigNPC_NB)
set OrigNPC_AB=GetUnitLoc(OrigNPC_BB)
call CreateNUnitsAtLocFacingLocBJ(1,'h00I',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AB,OrigNPC_IB)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'h028',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AB,OrigNPC_IB)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call RemoveLocation(OrigNPC_AB)
call RemoveLocation(OrigNPC_IB)
call SetUnitAnimation(OrigNPC_BB,"death")
call UnitDamageTargetBJ(OrigNPC_NB,OrigNPC_BB,600.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call EnableTrigger(OrigNPC_E5V)
call TriggerSleepAction(.8)
call DisableTrigger(OrigNPC_E5V)
endif
endfunction
function OrigNPC_JBX takes nothing returns nothing
set OrigNPC_IB=GetUnitLoc(OrigNPC_NB)
set OrigNPC_AB=GetUnitLoc(OrigNPC_BB)
call SetUnitPositionLoc(OrigNPC_NB,OrigNPC_M3V(OrigNPC_IB,10.,AngleBetweenPoints(OrigNPC_IB,OrigNPC_AB)))
call RemoveLocation(OrigNPC_IB)
call RemoveLocation(OrigNPC_AB)
endfunction
function OrigNPC_JDX takes nothing returns nothing
set OrigNPC_IB=GetUnitLoc(OrigNPC_NB)
set OrigNPC_AB=GetUnitLoc(OrigNPC_BB)
call SetUnitPositionLoc(OrigNPC_BB,OrigNPC_M3V(OrigNPC_AB,35.,AngleBetweenPoints(OrigNPC_IB,OrigNPC_AB)))
call AddSpecialEffectLocBJ(OrigNPC_AB,"Abilities\\Weapons\\AncientProtectorMissile\\AncientProtectorMissile.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call RemoveLocation(OrigNPC_IB)
call RemoveLocation(OrigNPC_AB)
endfunction
function OrigNPC_JGX takes nothing returns boolean
return(GetSpellAbilityId()=='A01J')
endfunction
function OrigNPC_JHX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01J',GetTriggerUnit())==2)
endfunction
function OrigNPC_JJX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01J',GetTriggerUnit())==1)
endfunction
function OrigNPC_JKX takes nothing returns nothing
set OrigNPC_NO=GetSpellAbilityUnit()
set OrigNPC_BO=GetSpellTargetUnit()
set OrigNPC_VO=GetOwningPlayer(GetSpellAbilityUnit())
set OrigNPC_EO=GetUnitLoc(GetSpellTargetUnit())
set OrigNPC_XO=GetUnitLoc(GetSpellAbilityUnit())
call CreateNUnitsAtLoc(1,'h02H',GetOwningPlayer(GetSpellTargetUnit()),OrigNPC_EO,bj_UNIT_FACING)
call UnitApplyTimedLifeBJ(7.,'BTLF',bj_lastCreatedUnit)
call PauseUnit(GetSpellTargetUnit(),false)
call CreateNUnitsAtLoc(1,'h02C',OrigNPC_VO,OrigNPC_EO,45.)
call UnitApplyTimedLifeBJ(5.5,'BTLF',bj_lastCreatedUnit)
set OrigNPC_YX=bj_lastCreatedUnit
call AddSpecialEffectTargetUnitBJ("overhead",bj_lastCreatedUnit,"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectTargetUnitBJ("overhead",bj_lastCreatedUnit,"Abilities\\Spells\\Other\\Tornado\\TornadoElementalSmall.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_EO,"Abilities\\Spells\\NightElf\\Cyclone\\CycloneTarget.mdl")
set OrigNPC_RE=bj_lastCreatedEffect
call AddSpecialEffectLocBJ(OrigNPC_EO,"Abilities\\Spells\\NightElf\\Cyclone\\CycloneTarget.mdl")
set OrigNPC_IE=bj_lastCreatedEffect
if(OrigNPC_JJX())then
call UnitDamageTargetBJ(OrigNPC_NO,OrigNPC_BO,400.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
if(OrigNPC_JHX())then
call UnitDamageTargetBJ(OrigNPC_NO,OrigNPC_BO,600.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call UnitDamageTargetBJ(OrigNPC_NO,OrigNPC_BO,800.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
endif
call TriggerSleepAction(2.25)
call CreateNUnitsAtLoc(1,'h02C',OrigNPC_VO,OrigNPC_EO,GetRandomReal(0,360))
call UnitApplyTimedLifeBJ(3.5,'BTLF',bj_lastCreatedUnit)
call AddSpecialEffectTargetUnitBJ("overhead",bj_lastCreatedUnit,"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call TriggerSleepAction(.25)
call DestroyEffect(OrigNPC_RE)
call TriggerSleepAction(.5)
call DestroyEffect(OrigNPC_IE)
call RemoveLocation(OrigNPC_EO)
call RemoveLocation(OrigNPC_XO)
endfunction
function OrigNPC_JMX takes nothing returns boolean
return(GetSpellAbilityId()=='A01J')and(GetUnitAbilityLevelSwapped('A01J',GetSpellAbilityUnit())==3)
endfunction
function OrigNPC_JPX takes nothing returns boolean
return(OrigNPC_JMX())
endfunction
function OrigNPC_JQX takes nothing returns boolean
return true
endfunction
function OrigNPC_JSX takes nothing returns nothing
if(OrigNPC_JQX())then
call SetUnitFlyHeight(GetEnumUnit(),.0,2000.)
call SetUnitPathing(GetEnumUnit(),true)
endif
endfunction
function OrigNPC_JTX takes nothing returns nothing
call TriggerSleepAction(.05)
call EnableTrigger(OrigNPC_E8V)
call TriggerSleepAction(.04)
call TriggerExecute(OrigNPC_E9V)
call TriggerSleepAction(2.4)
call TriggerExecute(OrigNPC_E9V)
call TriggerSleepAction(2.4)
call TriggerExecute(OrigNPC_E9V)
call TriggerSleepAction(1.2)
call DisableTrigger(OrigNPC_E8V)
call ForGroupBJ(OrigNPC_CR,function OrigNPC_JSX)
call GroupClear(OrigNPC_CR)
endfunction
function OrigNPC_JWX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),OrigNPC_VO))
endfunction
function OrigNPC_JYX takes nothing returns boolean
return(GetFilterUnit()!=OrigNPC_BO)
endfunction
function OrigNPC_JZX takes nothing returns boolean
return GetBooleanAnd(OrigNPC_JWX(),OrigNPC_JYX())
endfunction
function OrigNPC_J_X takes nothing returns boolean
return(IsUnitInGroup(OrigNPC_ZX,OrigNPC_CR)==false)
endfunction
function OrigNPC_J0X takes nothing returns nothing
set OrigNPC_ZX=GetEnumUnit()
if(OrigNPC_J_X())then
call SetUnitPathing(OrigNPC_ZX,false)
call UnitAddAbility(OrigNPC_ZX,'Amrf')
call UnitRemoveAbility(OrigNPC_ZX,'Amrf')
call GroupAddUnit(OrigNPC_CR,OrigNPC_ZX)
endif
set OrigNPC_ZF=GetUnitLoc(OrigNPC_ZX)
set OrigNPC_KR=OrigNPC_M3V(OrigNPC_VG,DistanceBetweenPoints(OrigNPC_VG,OrigNPC_ZF),(AngleBetweenPoints(OrigNPC_VG,OrigNPC_ZF)+8.))
call SetUnitPositionLocFacingBJ(OrigNPC_ZX,OrigNPC_KR,(GetUnitFacing(OrigNPC_ZX)+15.))
call RemoveLocation(OrigNPC_KR)
call RemoveLocation(OrigNPC_ZF)
endfunction
function OrigNPC_J1X takes nothing returns nothing
set OrigNPC_VG=GetUnitLoc(OrigNPC_YX)
set OrigNPC_ME=OrigNPC_PIV(250.,OrigNPC_VG,Condition(function OrigNPC_JZX))
call ForGroupBJ(OrigNPC_ME,function OrigNPC_J0X)
call DestroyGroup(OrigNPC_JE)
call RemoveLocation(OrigNPC_VG)
endfunction
function OrigNPC_J3X takes nothing returns nothing
set OrigNPC_BR=GetEnumUnit()
call SetUnitFlyHeight(OrigNPC_BR,GetRandomReal(0,800.),GetRandomReal(200.,1000.))
call AddSpecialEffectTargetUnitBJ("overhead",OrigNPC_BR,"Abilities\\Weapons\\Bolt\\BoltImpact.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectTargetUnitBJ("overhead",OrigNPC_BR,"Abilities\\Spells\\NightElf\\Cyclone\\CycloneTarget.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectTargetUnitBJ("overhead",OrigNPC_BR,"Abilities\\Spells\\Other\\Tornado\\TornadoElementalSmall.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call UnitDamageTargetBJ(OrigNPC_NO,OrigNPC_BR,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endfunction
function OrigNPC_J4X takes nothing returns nothing
set OrigNPC_AE=GetUnitLoc(OrigNPC_BO)
call AddSpecialEffectLocBJ(OrigNPC_AE,"Abilities\\Spells\\NightElf\\Cyclone\\CycloneTarget.mdl")
call RemoveLocation(OrigNPC_AE)
call DestroyEffect(bj_lastCreatedEffect)
call ForGroupBJ(OrigNPC_CR,function OrigNPC_J3X)
endfunction
function OrigNPC_J6X takes nothing returns boolean
return(GetSpellAbilityId()=='A00W')and(NPCSourceType(GetTriggerUnit())!='c000')
endfunction
function OrigNPC_J7X takes nothing returns boolean
return(OrigNPC_J6X())
endfunction
function OrigNPC_J8X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00W',OrigNPC_TR)==2)and(IsUnitAliveBJ(OrigNPC_TR))
endfunction
function OrigNPC_J9X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A00W',OrigNPC_TR)==3)and(IsUnitAliveBJ(OrigNPC_TR))
endfunction
function OrigNPC_KVX takes nothing returns boolean
return(OrigNPC_J9X())
endfunction
function OrigNPC_KEX takes nothing returns boolean
return(OrigNPC_J8X())
endfunction
function OrigNPC_KXX takes nothing returns nothing
set OrigNPC_TR=GetTriggerUnit()
set OrigNPC_UR=GetUnitLoc(OrigNPC_TR)
call CreateNUnitsAtLocFacingLocBJ(1,'h02N',GetOwningPlayer(OrigNPC_TR),OrigNPC_UR,OrigNPC_UR)
set OrigNPC_WR=bj_lastCreatedUnit
call UnitAddAbility(OrigNPC_WR,'A002')
call SetUnitMoveSpeed(OrigNPC_TR,.0)
call UnitAddAbility(OrigNPC_TR,'Amrf')
call UnitRemoveAbility(OrigNPC_TR,'Amrf')
call SetUnitFlyHeight(OrigNPC_TR,700.,1500.)
call TriggerSleepAction(.25)
call RemoveLocation(OrigNPC_UR)
set OrigNPC_UR=GetUnitLoc(OrigNPC_TR)
call SetUnitPositionLoc(OrigNPC_WR,OrigNPC_UR)
call IssueImmediateOrderById(OrigNPC_WR,0xD022E)
if(OrigNPC_KEX())then
call SetUnitFlyHeight(OrigNPC_TR,.0,2000.)
call TriggerSleepAction(.15)
call SetUnitFlyHeight(OrigNPC_TR,700.,1500.)
call SetUnitAnimation(OrigNPC_TR,"spell")
call TriggerSleepAction(.25)
call RemoveLocation(OrigNPC_UR)
set OrigNPC_UR=GetUnitLoc(OrigNPC_TR)
call SetUnitPositionLoc(OrigNPC_WR,OrigNPC_UR)
call IssueImmediateOrderById(OrigNPC_WR,0xD022E)
else
if(OrigNPC_KVX())then
call SetUnitFlyHeight(OrigNPC_TR,.0,2000.)
call TriggerSleepAction(.15)
call SetUnitFlyHeight(OrigNPC_TR,700.,1500.)
call SetUnitAnimation(OrigNPC_TR,"spell")
call TriggerSleepAction(.25)
call RemoveLocation(OrigNPC_UR)
set OrigNPC_UR=GetUnitLoc(OrigNPC_TR)
call SetUnitPositionLoc(OrigNPC_WR,OrigNPC_UR)
call IssueImmediateOrderById(OrigNPC_WR,0xD022E)
call SetUnitFlyHeight(OrigNPC_TR,.0,2000.)
call TriggerSleepAction(.15)
call SetUnitFlyHeight(OrigNPC_TR,700.,1500.)
call SetUnitAnimation(OrigNPC_TR,"spell")
call TriggerSleepAction(.25)
call RemoveLocation(OrigNPC_UR)
set OrigNPC_UR=GetUnitLoc(OrigNPC_TR)
call SetUnitPositionLoc(OrigNPC_WR,OrigNPC_UR)
call IssueImmediateOrderById(OrigNPC_WR,0xD022E)
else
call SetUnitFlyHeight(OrigNPC_TR,.0,2000.)
call SetUnitMoveSpeed(OrigNPC_TR,GetUnitDefaultMoveSpeed(GetTriggerUnit()))
endif
endif
call SetUnitFlyHeight(OrigNPC_TR,.0,2000.)
call SetUnitMoveSpeed(OrigNPC_TR,GetUnitDefaultMoveSpeed(GetTriggerUnit()))
call RemoveLocation(OrigNPC_UR)
call TriggerSleepAction(1.)
call RemoveUnit(OrigNPC_WR)
endfunction
function OrigNPC_KRX takes nothing returns boolean
return(GetSpellAbilityId()=='A00C')
endfunction
function OrigNPC_KIX takes nothing returns nothing
local unit OrigNPC_KIX_local_IV
set OrigNPC_KIX_local_IV=GetSpellTargetUnit()
call PauseUnit(OrigNPC_KIX_local_IV,true)
call SetUnitAnimation(OrigNPC_KIX_local_IV,"Death")
call TriggerSleepAction(14.)
call PauseUnit(OrigNPC_KIX_local_IV,false)
set OrigNPC_KIX_local_IV=null
endfunction
function OrigNPC_KNX takes nothing returns boolean
return(GetSpellAbilityId()=='A01H')
endfunction
function OrigNPC_KBX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==1)
endfunction
function OrigNPC_KCX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==2)
endfunction
function OrigNPC_KDX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==3)
endfunction
function OrigNPC_KFX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==1)
endfunction
function OrigNPC_KGX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==2)
endfunction
function OrigNPC_KHX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==3)
endfunction
function OrigNPC_KJX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==1)
endfunction
function OrigNPC_KKX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==2)
endfunction
function OrigNPC_KLX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==3)
endfunction
function OrigNPC_KMX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==1)
endfunction
function OrigNPC_KPX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==2)
endfunction
function OrigNPC_KQX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==3)
endfunction
function OrigNPC_KSX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==1)
endfunction
function OrigNPC_KTX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==2)
endfunction
function OrigNPC_KUX takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01H',OrigNPC_CV)==3)
endfunction
function OrigNPC_KWX takes nothing returns nothing
set OrigNPC_CV=GetSpellAbilityUnit()
set OrigNPC_FV=GetSpellTargetUnit()
set OrigNPC_DV=DistanceBetweenPoints(GetUnitLoc(OrigNPC_CV),GetUnitLoc(OrigNPC_FV))
call PauseUnit(OrigNPC_CV,true)
call SetUnitPathing(OrigNPC_CV,false)
call SetUnitFacingToFaceUnitTimed(OrigNPC_CV,OrigNPC_FV,0)
call EnableTrigger(OrigNPC_XOV)
call SetUnitAnimation(OrigNPC_CV,"attack walk stand spin")
call TriggerSleepAction((OrigNPC_DV/ 950.))
call DisableTrigger(OrigNPC_XOV)
call AddSpecialEffectLocBJ(GetUnitLoc(OrigNPC_FV),"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
set OrigNPC_ZE=bj_lastCreatedEffect
call SetUnitPositionLocFacingLocBJ(OrigNPC_CV,OrigNPC_M3V(GetUnitLoc(OrigNPC_FV),200.,AngleBetweenPoints(GetUnitLoc(OrigNPC_CV),GetUnitLoc(OrigNPC_FV))),GetUnitLoc(OrigNPC_FV))
call TriggerSleepAction(.01)
if(OrigNPC_KBX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,180.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_KCX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,240.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_KDX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,300.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
call AddSpecialEffectLocBJ(GetUnitLoc(OrigNPC_FV),"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
set OrigNPC_VX=bj_lastCreatedEffect
call SetUnitPositionLocFacingLocBJ(OrigNPC_CV,OrigNPC_M3V(GetUnitLoc(OrigNPC_FV),200.,AngleBetweenPoints(GetUnitLoc(OrigNPC_CV),GetUnitLoc(OrigNPC_FV))),GetUnitLoc(OrigNPC_FV))
call TriggerSleepAction(.35)
if(OrigNPC_KFX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,180.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_KGX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,240.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_KHX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,300.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
call AddSpecialEffectLocBJ(GetUnitLoc(OrigNPC_FV),"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
set OrigNPC_EX=bj_lastCreatedEffect
call SetUnitPositionLocFacingLocBJ(OrigNPC_CV,OrigNPC_M3V(GetUnitLoc(OrigNPC_FV),200.,AngleBetweenPoints(GetUnitLoc(OrigNPC_CV),GetUnitLoc(OrigNPC_FV))),GetUnitLoc(OrigNPC_FV))
call TriggerSleepAction(.35)
if(OrigNPC_KJX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,180.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_KKX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,240.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_KLX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,300.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
call AddSpecialEffectLocBJ(GetUnitLoc(OrigNPC_FV),"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
set OrigNPC_XX=bj_lastCreatedEffect
call SetUnitPositionLocFacingLocBJ(OrigNPC_CV,OrigNPC_M3V(GetUnitLoc(OrigNPC_FV),200.,AngleBetweenPoints(GetUnitLoc(OrigNPC_CV),GetUnitLoc(OrigNPC_FV))),GetUnitLoc(OrigNPC_FV))
call TriggerSleepAction(.35)
if(OrigNPC_KMX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,180.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_KPX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,240.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_KQX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,300.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
call AddSpecialEffectLocBJ(GetUnitLoc(OrigNPC_FV),"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
set OrigNPC_OX=bj_lastCreatedEffect
call SetUnitPositionLocFacingLocBJ(OrigNPC_CV,OrigNPC_M3V(GetUnitLoc(OrigNPC_FV),200.,AngleBetweenPoints(GetUnitLoc(OrigNPC_CV),GetUnitLoc(OrigNPC_FV))),GetUnitLoc(OrigNPC_FV))
call TriggerSleepAction(.35)
if(OrigNPC_KSX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,180.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_KTX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,240.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
if(OrigNPC_KUX())then
call UnitDamageTargetBJ(OrigNPC_CV,OrigNPC_FV,300.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
call AddSpecialEffectLocBJ(GetUnitLoc(OrigNPC_FV),"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
set OrigNPC_RX=bj_lastCreatedEffect
call SetUnitPositionLocFacingLocBJ(OrigNPC_CV,OrigNPC_M3V(GetUnitLoc(OrigNPC_FV),200.,AngleBetweenPoints(GetUnitLoc(OrigNPC_CV),GetUnitLoc(OrigNPC_FV))),GetUnitLoc(OrigNPC_FV))
call SetUnitPathing(OrigNPC_CV,true)
call PauseUnit(OrigNPC_CV,false)
call SetUnitAnimation(OrigNPC_CV,"Stand")
call DestroyEffect(OrigNPC_ZE)
call DestroyEffect(OrigNPC_VX)
call DestroyEffect(OrigNPC_EX)
call DestroyEffect(OrigNPC_XX)
call DestroyEffect(OrigNPC_OX)
call DestroyEffect(OrigNPC_RX)
endfunction
function OrigNPC_KZX takes nothing returns nothing
set OrigNPC_ZF=GetUnitLoc(OrigNPC_CV)
set OrigNPC_VG=GetUnitLoc(OrigNPC_FV)
call SetUnitPositionLoc(OrigNPC_CV,OrigNPC_M3V(OrigNPC_ZF,14.,AngleBetweenPoints(OrigNPC_ZF,OrigNPC_VG)))
call RemoveLocation(OrigNPC_ZF)
call RemoveLocation(OrigNPC_VG)
endfunction
function OrigNPC_K0X takes nothing returns boolean
return(GetSpellAbilityId()=='A01T')
endfunction
function OrigNPC_K1X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01T',OrigNPC_UN)==2)
endfunction
function OrigNPC_K2X takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('A01T',OrigNPC_UN)==1)
endfunction
function OrigNPC_K3X takes nothing returns nothing
local unit OrigNPC_K3X_visualCaster=GetTriggerUnit()
local unit OrigNPC_K3X_visualTarget=GetSpellTargetUnit()
local location OrigNPC_K3X_origin=null
local effect OrigNPC_K3X_flash=null
set OrigNPC_VB=GetUnitLoc(GetTriggerUnit())
set OrigNPC_K3X_origin=OrigNPC_VB
set OrigNPC_UN=GetTriggerUnit()
set OrigNPC_WN=GetSpellTargetUnit()
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_UN,"Abilities\\Spells\\Undead\\DarkSummoning\\DarkSummonMissile.mdl")
set OrigNPC_ZN=bj_lastCreatedEffect
set OrigNPC_K3X_flash=OrigNPC_ZN
call UnitAddAbility(OrigNPC_UN,'Amrf')
call UnitRemoveAbility(OrigNPC_UN,'Amrf')
call UnitAddAbility(OrigNPC_WN,'Amrf')
call UnitRemoveAbility(OrigNPC_WN,'Amrf')
call SetUnitTimeScalePercent(OrigNPC_K3X_visualTarget,250.)
call SetUnitAnimation(OrigNPC_WN,"death")
call SetUnitPathing(OrigNPC_K3X_visualCaster,false)
call SetUnitPathing(OrigNPC_K3X_visualTarget,false)
call PauseUnit(OrigNPC_K3X_visualCaster,true)
call PauseUnit(OrigNPC_K3X_visualTarget,true)
call ShowUnitHide(OrigNPC_K3X_visualCaster)
call SetUnitFlyHeight(OrigNPC_K3X_visualTarget,500.,2000.)
call SetUnitFlyHeight(OrigNPC_K3X_visualCaster,500.,2000.)
call TriggerSleepAction(.25)
call ShowUnitShow(OrigNPC_K3X_visualCaster)
call SetUnitTimeScalePercent(OrigNPC_K3X_visualCaster,300.)
if(OrigNPC_K2X())then
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,150.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,150.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,150.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,150.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
if(OrigNPC_K1X())then
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,100.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
else
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call TriggerSleepAction(.5)
call TriggerExecute(OrigNPC_XAV)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,75.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
endif
endif
call TriggerSleepAction(.5)
call SetUnitPositionLoc(OrigNPC_K3X_visualCaster,OrigNPC_K3X_origin)
call SetUnitPositionLoc(OrigNPC_K3X_visualTarget,OrigNPC_K3X_origin)
call SetUnitTimeScalePercent(OrigNPC_K3X_visualCaster,100.)
call PlaySoundBJ(OrigNPC_CY)
call SetUnitAnimationByIndex(OrigNPC_K3X_visualCaster,0xC)
call TriggerSleepAction(.01)
call ShowUnitHide(OrigNPC_K3X_visualCaster)
call ShowUnitHide(OrigNPC_K3X_visualTarget)
call SetUnitFlyHeight(OrigNPC_K3X_visualCaster,.0,.0)
call SetUnitFlyHeight(OrigNPC_K3X_visualTarget,.0,.0)
call TriggerSleepAction(.5)
call ShowUnitShow(OrigNPC_K3X_visualCaster)
call TriggerSleepAction(.5)
call ShowUnitShow(OrigNPC_K3X_visualTarget)
call SetUnitTimeScalePercent(OrigNPC_K3X_visualTarget,100.)
call UnitDamageTargetBJ(OrigNPC_UN,OrigNPC_WN,300.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_UNIVERSAL)
call AddSpecialEffectLocBJ(OrigNPC_VB,"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call SetUnitPathing(OrigNPC_K3X_visualCaster,true)
call SetUnitPathing(OrigNPC_K3X_visualTarget,true)
call PauseUnit(OrigNPC_K3X_visualCaster,false)
call PauseUnit(OrigNPC_K3X_visualTarget,false)
call DestroyEffect(OrigNPC_K3X_flash)
call RemoveLocation(OrigNPC_K3X_origin)
set OrigNPC_K3X_origin=null
set OrigNPC_K3X_flash=null
set OrigNPC_K3X_visualCaster=null
set OrigNPC_K3X_visualTarget=null
endfunction
function OrigNPC_K5X takes nothing returns boolean
return(GetSpellAbilityId()=='A01T')
endfunction
function OrigNPC_K6X takes nothing returns nothing
call TriggerSleepAction(.01)
set OrigNPC_VG=GetUnitLoc(GetSpellTargetUnit())
call SetUnitAnimationByIndex(GetTriggerUnit(),0xC)
call AddSpecialEffectLocBJ(OrigNPC_AE,"Abilities\\Spells\\Human\\FlakCannons\\FlakTarget.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call AddSpecialEffectLocBJ(OrigNPC_VB,"Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call RemoveLocation(OrigNPC_VG)
endfunction
function OrigNPC_K8X takes nothing returns nothing
set OrigNPC_IO=GetUnitLoc(OrigNPC_UN)
set OrigNPC_TN=GetUnitLoc(OrigNPC_WN)
set OrigNPC_YN=(GetUnitFacing(OrigNPC_UN)-90.)
call SetUnitPositionLocFacingBJ(OrigNPC_UN,OrigNPC_TN,OrigNPC_YN)
call SetUnitAnimationByIndex(OrigNPC_UN,8)
call CreateNUnitsAtLocFacingLocBJ(1,'h028',GetOwningPlayer(OrigNPC_UN),GetUnitLoc(OrigNPC_WN),OrigNPC_TN)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,200.)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call CreateNUnitsAtLocFacingLocBJ(1,'h00I',GetOwningPlayer(OrigNPC_UN),GetUnitLoc(OrigNPC_WN),OrigNPC_TN)
call SetUnitTimeScalePercent(bj_lastCreatedUnit,200.)
call UnitApplyTimedLifeBJ(2.,'BTLF',bj_lastCreatedUnit)
call SetUnitAnimation(OrigNPC_WN,"death")
call EnableTrigger(OrigNPC_XNV)
call TriggerSleepAction(.5)
call DisableTrigger(OrigNPC_XNV)
call RemoveLocation(OrigNPC_IO)
call RemoveLocation(OrigNPC_TN)
endfunction
function OrigNPC_LVX takes nothing returns nothing
set OrigNPC_TN=GetUnitLoc(OrigNPC_WN)
call SetUnitPositionLoc(OrigNPC_WN,OrigNPC_M3V(OrigNPC_TN,50.,GetUnitFacing(OrigNPC_UN)))
call RemoveLocation(OrigNPC_TN)
endfunction
function OrigNPC_MJX takes nothing returns boolean
return(IsDestructableAliveBJ(GetEnumDestructable()))and(GetDestructableTypeId(GetEnumDestructable())!='DTg5')and(GetDestructableTypeId(GetEnumDestructable())!='DTg7')and(GetDestructableTypeId(GetEnumDestructable())!='LTcr')and(GetDestructableTypeId(GetEnumDestructable())!='LTba')
endfunction
function OrigNPC_MKX takes nothing returns nothing
if(OrigNPC_MJX())then
call SetDestAnimationSpeedPercent(GetEnumDestructable(),5.)
call SetDestructableAnimation(GetEnumDestructable(),"stand hit")
else
call SetDestAnimationSpeedPercent(GetEnumDestructable(),100.)
endif
endfunction
function OrigNPC_MLX takes nothing returns nothing
call EnumDestructablesInRectAll(bj_mapInitialPlayableArea,function OrigNPC_MKX)
endfunction
function OrigNPC_MPX takes nothing returns boolean
return(GetSpellAbilityId()=='A00F')
endfunction
function OrigNPC_MQX takes nothing returns boolean
return(OrigNPC_MPX())
endfunction
function OrigNPC_MSX takes nothing returns nothing
call SetDestAnimationSpeedPercent(GetEnumDestructable(),55.)
call SetDestructableAnimation(GetEnumDestructable(),"stand hit")
endfunction
function OrigNPC_MTX takes nothing returns boolean
return(IsUnitType(GetTriggerUnit(),UNIT_TYPE_SNARED)==false)!=null
endfunction
function OrigNPC_MUX takes nothing returns nothing
if(OrigNPC_MTX())then
set OrigNPC_BE=GetUnitLoc(GetTriggerUnit())
call AddSpecialEffectLocBJ(OrigNPC_BE,"Abilities\\Spells\\Human\\FlakCannons\\FlakTarget.mdl")
call DestroyEffect(bj_lastCreatedEffect)
call RemoveLocation(OrigNPC_BE)
set OrigNPC_AE=GetSpellTargetLoc()
call OrigNPC_M8V(50.,OrigNPC_AE,function OrigNPC_MSX)
call SetUnitPathing(GetTriggerUnit(),false)
call SetUnitPositionLoc(GetTriggerUnit(),OrigNPC_AE)
call UnitAddAbility(GetTriggerUnit(),'Amrf')
call UnitRemoveAbility(GetTriggerUnit(),'Amrf')
call SetUnitFlyHeight(GetTriggerUnit(),400.,.0)
call RemoveLocation(OrigNPC_AE)
call TriggerSleepAction(.01)
call SetUnitPathing(GetTriggerUnit(),true)
set OrigNPC_DR=GetUnitLoc(GetTriggerUnit())
call SetUnitPositionLoc(GetTriggerUnit(),OrigNPC_DR)
call PlaySoundOnUnitBJ(OrigNPC_VU,'d',GetTriggerUnit())
call RemoveLocation(OrigNPC_DR)
call SetUnitAnimation(GetTriggerUnit(),"walk")
call SetUnitFlyHeight(GetTriggerUnit(),.0,1800.)
else
call IssueImmediateOrderById(GetTriggerUnit(),0xD0004)
endif
endfunction
function OrigNPC_PUX takes nothing returns boolean
return(GetSpellAbilityId()=='A015')or(GetSpellAbilityId()=='A019')or(GetSpellAbilityId()=='A026')or(GetSpellAbilityId()=='A00Y')or(NPCSourceType(GetDyingUnit())=='h00R')or(NPCSourceType(GetDyingUnit())=='h027')
endfunction
function OrigNPC_PWX takes nothing returns boolean
return(OrigNPC_PUX())
endfunction
function OrigNPC_PYX takes nothing returns boolean
return(NPCSourceType(GetFilterUnit())=='H00N')
endfunction
function OrigNPC_PZX takes nothing returns boolean
return(IsUnitIllusion(GetFilterUnit())==false)
endfunction
function OrigNPC_P_X takes nothing returns boolean
return GetBooleanAnd(OrigNPC_PYX(),OrigNPC_PZX())
endfunction
function OrigNPC_P0X takes nothing returns boolean
return(CountUnitsInGroup(OrigNPC_PDV(Player(0),Condition(function OrigNPC_P_X)))>0)
endfunction
function OrigNPC_P1X takes nothing returns boolean
return(CountUnitsInGroup(OrigNPC_PBV('H00S'))==1)
endfunction
function OrigNPC_P2X takes nothing returns boolean
return(CountUnitsInGroup(OrigNPC_PHV(Player(7),'h027'))==1)
endfunction
function OrigNPC_P3X takes nothing returns boolean
return(CountUnitsInGroup(OrigNPC_PHV(Player(9),'h00R'))==1)
endfunction
function OrigNPC_P4X takes nothing returns nothing
if(OrigNPC_P0X())then
call MultiboardSetItemIconBJ(OrigNPC_BG,1,2,"Icon_Naruto_OneTailedTransformation.blp")
else
call MultiboardSetItemIconBJ(OrigNPC_BG,1,2,"Icon_Naruto_Portrait2.blp")
endif
if(OrigNPC_P1X())then
call MultiboardSetItemIconBJ(OrigNPC_BG,1,3,"Icon_Sasuke_2ndForm.blp")
else
call MultiboardSetItemIconBJ(OrigNPC_BG,1,3,"Icon_Sasuke_Portrait2.blp")
endif
if(OrigNPC_P2X())then
call MultiboardSetItemIconBJ(OrigNPC_BG,1,9,"Icon_Kiba_Shikyaku.blp")
else
call MultiboardSetItemIconBJ(OrigNPC_BG,1,9,"Icon_Kiba_Portrait.blp")
endif
if(OrigNPC_P3X())then
call MultiboardSetItemIconBJ(OrigNPC_BG,1,0xB,"Icon_Shukaku_Portrait2.blp")
else
call MultiboardSetItemIconBJ(OrigNPC_BG,1,0xB,"Icon_Gaara_Portrait.blp")
endif
endfunction
function OrigNPC_YPX takes nothing returns boolean
return(GetSpellAbilityId()=='A012')and(CountPlayersInForceBJ(OrigNPC_PJV(MAP_CONTROL_COMPUTER))>0)
endfunction
function OrigNPC_YQX takes nothing returns boolean
return(OrigNPC_YPX())
endfunction
function OrigNPC_YSX takes nothing returns boolean
return(GetPlayerController(GetOwningPlayer(GetFilterUnit()))==MAP_CONTROL_COMPUTER)
endfunction
function OrigNPC_YTX takes nothing returns boolean
return(IsUnitType(GetFilterUnit(),UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_YUX takes nothing returns boolean
return(UnitHasBuffBJ(GetFilterUnit(),'S011')==false)
endfunction
function OrigNPC_YWX takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_YYX takes nothing returns boolean
return GetBooleanAnd(OrigNPC_YUX(),OrigNPC_YWX())
endfunction
function OrigNPC_YZX takes nothing returns boolean
return GetBooleanAnd(OrigNPC_YTX(),OrigNPC_YYX())
endfunction
function OrigNPC_Y_X takes nothing returns boolean
return GetBooleanAnd(OrigNPC_YSX(),OrigNPC_YZX())
endfunction
function OrigNPC_Y0X takes nothing returns nothing
set OrigNPC_DR=GetSpellTargetLoc()
set OrigNPC_BE=OrigNPC_M3V(OrigNPC_DR,GetRandomReal(800.,2000.),GetUnitFacing(GetTriggerUnit()))
call IssuePointOrderByIdLoc(GetEnumUnit(),0xD0016,OrigNPC_BE)
call RemoveLocation(OrigNPC_BE)
call RemoveLocation(OrigNPC_DR)
endfunction
function OrigNPC_Y1X takes nothing returns nothing
call TriggerSleepAction(.3)
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
set OrigNPC_CE=OrigNPC_PIV(600.,OrigNPC_AE,Condition(function OrigNPC_Y_X))
call ForGroupBJ(OrigNPC_CE,function OrigNPC_Y0X)
call DestroyGroup(OrigNPC_CE)
call RemoveLocation(OrigNPC_AE)
endfunction
function OrigNPC_VUO takes nothing returns boolean
return(GetSpellAbilityId()=='A012')and(GetPlayerController(GetOwningPlayer(GetTriggerUnit()))==MAP_CONTROL_COMPUTER)
endfunction
function OrigNPC_VWO takes nothing returns boolean
return(OrigNPC_VUO())
endfunction
function OrigNPC_VYO takes nothing returns boolean
return(IsUnitAliveBJ(GetFilterUnit()))
endfunction
function OrigNPC_VZO takes nothing returns boolean
return(IsUnitType(GetFilterUnit(),UNIT_TYPE_HERO))!=null
endfunction
function OrigNPC_V_O takes nothing returns boolean
return(GetUnitAbilityLevelSwapped('S000',GetFilterUnit())!=1)
endfunction
function OrigNPC_V0O takes nothing returns boolean
return(IsUnitEnemy(GetFilterUnit(),GetOwningPlayer(GetTriggerUnit())))
endfunction
function OrigNPC_V1O takes nothing returns boolean
return GetBooleanAnd(OrigNPC_V_O(),OrigNPC_V0O())
endfunction
function OrigNPC_V2O takes nothing returns boolean
return GetBooleanAnd(OrigNPC_VZO(),OrigNPC_V1O())
endfunction
function OrigNPC_V3O takes nothing returns boolean
return GetBooleanAnd(OrigNPC_VYO(),OrigNPC_V2O())
endfunction
function OrigNPC_V4O takes nothing returns nothing
call IssueTargetOrderById(GetTriggerUnit(),0xD000F,GetEnumUnit())
endfunction
function OrigNPC_V5O takes nothing returns nothing
call TriggerSleepAction(.1)
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
set OrigNPC_CE=OrigNPC_PIV(1000.,OrigNPC_AE,Condition(function OrigNPC_V3O))
call ForGroupBJ(OrigNPC_CE,function OrigNPC_V4O)
call DestroyGroup(OrigNPC_CE)
call RemoveLocation(OrigNPC_AE)
endfunction
// Six original 0.25s medic clocks; no temporary locations or random wandering.
function NPCMedicClock takes integer j returns trigger
    if j==0 then
        return OrigNPC_R4V
    elseif j==1 then
        return OrigNPC_R5V
    elseif j==2 then
        return OrigNPC_R6V
    elseif j==3 then
        return OrigNPC_R7V
    elseif j==4 then
        return OrigNPC_R8V
    endif
    return OrigNPC_R9V
endfunction
function NPCMedicStop takes integer j returns nothing
    call DisableTrigger(NPCMedicClock(j))
    set OrigNPC_RR[j+2]=null
    if OrigNPC_AF[j]!=null then
        call DestroyEffect(OrigNPC_AF[j])
        set OrigNPC_AF[j]=null
    endif
    if OrigNPC_IF[j]!=null then
        call SetUnitTimeScale(OrigNPC_IF[j],1.)
        if NPCCooldowns!=null then
            call SaveReal(NPCCooldowns,GetHandleId(OrigNPC_IF[j]),0,0.)
        endif
    endif
endfunction
function NPCMedicPulse takes integer j returns nothing
    local unit medic=OrigNPC_IF[j]
    local unit target=OrigNPC_RR[j+2]
    local real dx=GetUnitX(medic)-GetUnitX(target)
    local real dy=GetUnitY(medic)-GetUnitY(target)
    if FoundationAlive(medic) and FoundationAlive(target) and not IsUnitPaused(medic) and IsUnitAlly(target,GetOwningPlayer(medic)) and dx*dx+dy*dy<500.*500. and GetWidgetLife(target)<GetUnitState(target,UNIT_STATE_MAX_LIFE) and GetUnitState(medic,UNIT_STATE_MANA)>=25. and GetUnitCurrentOrder(medic)==OrderId("drain") then
        call SetUnitTimeScale(medic,2.)
        call SetUnitAnimation(medic,"attack")
        call SetUnitState(medic,UNIT_STATE_MANA,GetUnitState(medic,UNIT_STATE_MANA)-25.)
        call SetWidgetLife(target,RMinBJ(GetUnitState(target,UNIT_STATE_MAX_LIFE),GetWidgetLife(target)+75.))
    else
        call NPCMedicStop(j)
        if FoundationAlive(medic) and GetUnitCurrentOrder(medic)==OrderId("drain") then
            call IssueImmediateOrder(medic,"stop")
        endif
    endif
    set medic=null
    set target=null
endfunction
function OrigNPC_GVO takes nothing returns boolean
return(NPCSourceType(GetSpellAbilityUnit())=='c020')and(GetSpellAbilityId()=='A02X')
endfunction
function OrigNPC_GEO takes nothing returns boolean
return(OrigNPC_GVO())
endfunction
function OrigNPC_GXO takes nothing returns boolean
return(GetSpellAbilityUnit()==OrigNPC_IF[5])
endfunction
function OrigNPC_GOO takes nothing returns boolean
return(GetSpellAbilityUnit()==OrigNPC_IF[4])
endfunction
function OrigNPC_GRO takes nothing returns boolean
return(GetSpellAbilityUnit()==OrigNPC_IF[3])
endfunction
function OrigNPC_GIO takes nothing returns boolean
return(GetSpellAbilityUnit()==OrigNPC_IF[2])
endfunction
function OrigNPC_GAO takes nothing returns boolean
return(GetSpellAbilityUnit()==OrigNPC_IF[1])
endfunction
function OrigNPC_GNO takes nothing returns boolean
return(GetSpellAbilityUnit()==OrigNPC_IF[0])
endfunction
function OrigNPC_GBO takes nothing returns nothing
    local integer j=0
    loop
        exitwhen j>=6
        if GetSpellAbilityUnit()==OrigNPC_IF[j] then
            call NPCMedicStop(j)
            set OrigNPC_RR[j+2]=GetSpellTargetUnit()
            set OrigNPC_AF[j]=AddSpecialEffectTarget("Abilities\\Spells\\Other\\Parasite\\ParasiteMissile.mdl",OrigNPC_IF[j],"hand left")
            call EnableTrigger(NPCMedicClock(j))
        endif
        set j=j+1
    endloop
endfunction
function OrigNPC_GDO takes nothing returns boolean
return(NPCSourceType(GetSpellAbilityUnit())=='c020')and(GetSpellAbilityId()=='A02X')
endfunction
function OrigNPC_GFO takes nothing returns boolean
return(OrigNPC_GDO())
endfunction
function OrigNPC_GGO takes nothing returns boolean
return(GetTriggerUnit()==OrigNPC_IF[5])
endfunction
function OrigNPC_GHO takes nothing returns boolean
return(GetTriggerUnit()==OrigNPC_IF[4])
endfunction
function OrigNPC_GJO takes nothing returns boolean
return(GetTriggerUnit()==OrigNPC_IF[3])
endfunction
function OrigNPC_GKO takes nothing returns boolean
return(GetTriggerUnit()==OrigNPC_IF[2])
endfunction
function OrigNPC_GLO takes nothing returns boolean
return(GetTriggerUnit()==OrigNPC_IF[1])
endfunction
function OrigNPC_GMO takes nothing returns boolean
return(GetTriggerUnit()==OrigNPC_IF[0])
endfunction
function OrigNPC_GPO takes nothing returns nothing
    local integer j=0
    loop
        exitwhen j>=6
        if GetTriggerUnit()==OrigNPC_IF[j] then
            call NPCMedicStop(j)
        endif
        set j=j+1
    endloop
endfunction
function OrigNPC_GSO takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_IF[0])>24.)and(GetUnitLifePercent(OrigNPC_RR[2])!=100.)and(DistanceBetweenPoints(OrigNPC_LN[2],OrigNPC_MN[2])<500.)and(IsUnitAliveBJ(OrigNPC_RR[2]))
endfunction
function OrigNPC_GTO takes nothing returns boolean
return(OrigNPC_GSO())
endfunction
function OrigNPC_GUO takes nothing returns nothing
    call NPCMedicPulse(0)
endfunction
function OrigNPC_GYO takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_IF[1])>24.)and(GetUnitLifePercent(OrigNPC_RR[3])!=100.)and(DistanceBetweenPoints(OrigNPC_LN[3],OrigNPC_MN[3])<500.)and(IsUnitAliveBJ(OrigNPC_RR[3]))
endfunction
function OrigNPC_GZO takes nothing returns boolean
return(OrigNPC_GYO())
endfunction
function OrigNPC_G_O takes nothing returns nothing
    call NPCMedicPulse(1)
endfunction
function OrigNPC_G1O takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_IF[2])>24.)and(GetUnitLifePercent(OrigNPC_RR[4])!=100.)and(DistanceBetweenPoints(OrigNPC_LN[4],OrigNPC_MN[4])<500.)and(IsUnitAliveBJ(OrigNPC_RR[4]))
endfunction
function OrigNPC_G2O takes nothing returns boolean
return(OrigNPC_G1O())
endfunction
function OrigNPC_G3O takes nothing returns nothing
    call NPCMedicPulse(2)
endfunction
function OrigNPC_G5O takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_IF[3])>24.)and(GetUnitLifePercent(OrigNPC_RR[5])!=100.)and(DistanceBetweenPoints(OrigNPC_LN[5],OrigNPC_MN[5])<500.)and(IsUnitAliveBJ(OrigNPC_RR[5]))
endfunction
function OrigNPC_G6O takes nothing returns boolean
return(OrigNPC_G5O())
endfunction
function OrigNPC_G7O takes nothing returns nothing
    call NPCMedicPulse(3)
endfunction
function OrigNPC_G9O takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_IF[4])>24.)and(GetUnitLifePercent(OrigNPC_RR[6])!=100.)and(DistanceBetweenPoints(OrigNPC_LN[6],OrigNPC_MN[6])<500.)and(IsUnitAliveBJ(OrigNPC_RR[6]))
endfunction
function OrigNPC_HVO takes nothing returns boolean
return(OrigNPC_G9O())
endfunction
function OrigNPC_HEO takes nothing returns nothing
    call NPCMedicPulse(4)
endfunction
function OrigNPC_HOO takes nothing returns boolean
return(GetUnitStateSwap(UNIT_STATE_MANA,OrigNPC_IF[5])>24.)and(GetUnitLifePercent(OrigNPC_RR[7])!=100.)and(DistanceBetweenPoints(OrigNPC_LN[7],OrigNPC_MN[7])<500.)and(IsUnitAliveBJ(OrigNPC_RR[7]))
endfunction
function OrigNPC_HRO takes nothing returns boolean
return(OrigNPC_HOO())
endfunction
function OrigNPC_HIO takes nothing returns nothing
    call NPCMedicPulse(5)
endfunction
function OrigNPC_DRR takes nothing returns boolean
return(GetSpellAbilityId()=='A01G')and(GetSpellAbilityUnit()==OrigNPC_J6V)
endfunction
function OrigNPC_DIR takes nothing returns boolean
return(OrigNPC_DRR())
endfunction
function OrigNPC_DAR takes nothing returns nothing
call ShowUnitShow(GetEnumUnit())
endfunction
function OrigNPC_DNR takes nothing returns nothing
call PauseUnit(GetEnumUnit(),false)
endfunction
function OrigNPC_DBR takes nothing returns nothing
call TriggerSleepAction(.5)
call KillUnit(OrigNPC_MIV)
call TriggerSleepAction(.25)
call KillUnit(OrigNPC_LOV)
call TriggerSleepAction(.25)
call KillUnit(OrigNPC_MAV)
call ForGroupBJ(OrigNPC_PRV(OrigNPC_KM),function OrigNPC_DAR)
call ForGroupBJ(OrigNPC_PRV(OrigNPC_KM),function OrigNPC_DNR)
endfunction
function OrigNPC_ZMR takes nothing returns nothing
call UnitAddAbility(OrigNPC_LDV,'ANth')
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_LDV,"Abilities\\Spells\\Undead\\ThornyShield\\ThornyShieldTargetChestRight.mdl")
set OrigNPC_SN[0]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_LDV,"Abilities\\Spells\\Undead\\ThornyShield\\ThornyShieldTargetChestMountLeft.mdl")
set OrigNPC_SN[1]=bj_lastCreatedEffect
call AddSpecialEffectTargetUnitBJ("chest",OrigNPC_LDV,"Abilities\\Spells\\Undead\\ThornyShield\\ThornyShieldTargetChestMountRight.mdl")
set OrigNPC_SN[2]=bj_lastCreatedEffect
call UnitAddAbility(OrigNPC_LDV,'A006')
call SetUnitAbilityLevelSwapped('A006',OrigNPC_LDV,4)
call IssueImmediateOrderById(OrigNPC_LDV,0xD009F)
endfunction
function OrigNPC_VGI takes nothing returns nothing
set OrigNPC_AE=GetUnitLoc(GetTriggerUnit())
call CreateNUnitsAtLoc(1,'c027',GetOwningPlayer(GetTriggerUnit()),OrigNPC_AE,bj_UNIT_FACING)
call RemoveLocation(OrigNPC_AE)
set OrigNPC_KI[1]=bj_lastCreatedUnit
call UnitAddAbility(bj_lastCreatedUnit,'A00X')
call UnitAddAbility(bj_lastCreatedUnit,'S027')
// Ukon uses the shared NPC AI after CampaignAdopt, avoiding a second order timer.
call DisableTrigger(GetTriggeringTrigger())
endfunction
function OrigNPC_OVI takes nothing returns boolean
return(GetSpellAbilityId()=='A00Y')
endfunction
function OrigNPC_OEI takes nothing returns boolean
return(OrigNPC_NE==1)
endfunction
function OrigNPC_OXI takes nothing returns nothing
set OrigNPC_NE=GetRandomInt(1,2)
if(OrigNPC_OEI())then
call PlaySoundOnUnitBJ(OrigNPC_MW,'d',GetTriggerUnit())
else
call PlaySoundOnUnitBJ(OrigNPC_YY,'d',GetTriggerUnit())
endif
endfunction
function OrigNPC_OUI takes nothing returns boolean
return(GetSpellAbilityId()=='A006')and(NPCSourceType(GetTriggerUnit())=='R008')
endfunction
function OrigNPC_OWI takes nothing returns boolean
return(OrigNPC_OUI())
endfunction
function OrigNPC_OYI takes nothing returns boolean
return(OrigNPC_NE==5)
endfunction
function OrigNPC_OZI takes nothing returns nothing
set OrigNPC_NE=GetRandomInt(5,6)
if(OrigNPC_OYI())then
call PlaySoundOnUnitBJ(OrigNPC_AW,'d',GetTriggerUnit())
else
call PlaySoundOnUnitBJ(OrigNPC_O1,'d',GetTriggerUnit())
endif
endfunction
function OrigNPC_RHI takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c003')and(GetSpellAbilityId()!='S028')
endfunction
function OrigNPC_RJI takes nothing returns boolean
return(OrigNPC_RHI())
endfunction
function OrigNPC_RKI takes nothing returns nothing
call PlaySoundBJ(OrigNPC_H0)
endfunction
function OrigNPC_RMI takes nothing returns boolean
return(GetSpellAbilityId()=='A01B')and(NPCSourceType(GetTriggerUnit())=='c003')
endfunction
function OrigNPC_RPI takes nothing returns boolean
return(OrigNPC_RMI())
endfunction
function OrigNPC_RQI takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_OY,'d',GetTriggerUnit())
endfunction
function OrigNPC_RTI takes nothing returns boolean
return(GetSpellAbilityId()=='A01K')and(NPCSourceType(GetTriggerUnit())=='c003')
endfunction
function OrigNPC_RUI takes nothing returns boolean
return(OrigNPC_RTI())
endfunction
function OrigNPC_RWI takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_RY,'d',GetTriggerUnit())
endfunction
function OrigNPC_RZI takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c003')and(GetSpellAbilityId()=='S028')
endfunction
function OrigNPC_R_I takes nothing returns boolean
return(OrigNPC_RZI())
endfunction
function OrigNPC_R0I takes nothing returns boolean
return(OrigNPC_NE==5)
endfunction
function OrigNPC_R1I takes nothing returns nothing
set OrigNPC_NE=GetRandomInt(5,6)
if(OrigNPC_R0I())then
call PlaySoundOnUnitBJ(OrigNPC_AU,'d',GetTriggerUnit())
else
call PlaySoundOnUnitBJ(OrigNPC_R1,'d',GetTriggerUnit())
endif
endfunction
function OrigNPC_R4I takes nothing returns boolean
return(GetSpellAbilityId()=='A00C')and(NPCSourceType(GetTriggerUnit())=='c003')
endfunction
function OrigNPC_R5I takes nothing returns boolean
return(OrigNPC_R4I())
endfunction
function OrigNPC_R6I takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_XY,'d',GetTriggerUnit())
endfunction
function OrigNPC_IEI takes nothing returns boolean
return(GetSpellAbilityId()=='A00R')and(NPCSourceType(GetTriggerUnit())=='c021')
endfunction
function OrigNPC_IXI takes nothing returns boolean
return(OrigNPC_IEI())
endfunction
function OrigNPC_IOI takes nothing returns boolean
return(IsUnitType(OrigNPC_QA,UNIT_TYPE_STUNNED))!=null
endfunction
function OrigNPC_IRI takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_IY,'d',GetTriggerUnit())
call TriggerSleepAction(1.)
if(OrigNPC_IOI())then
call StopSoundBJ(OrigNPC_I0,false)
endif
endfunction
function OrigNPC_IAI takes nothing returns boolean
return(GetSpellAbilityId()=='A01P')and(NPCSourceType(GetTriggerUnit())=='c021')
endfunction
function OrigNPC_INI takes nothing returns boolean
return(OrigNPC_IAI())
endfunction
function OrigNPC_IBI takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_NU,'d',GetTriggerUnit())
endfunction
function OrigNPC_IDI takes nothing returns boolean
return(GetSpellAbilityId()=='A01B')and(NPCSourceType(GetTriggerUnit())=='c021')
endfunction
function OrigNPC_IFI takes nothing returns boolean
return(OrigNPC_IDI())
endfunction
function OrigNPC_IGI takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_I0,'d',GetTriggerUnit())
endfunction
function OrigNPC_IMI takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c00B')and(GetSpellAbilityId()!='A012')and(GetSpellAbilityId()!='A00F')and(GetSpellAbilityId()!='A00B')and(GetSpellAbilityId()!='A00M')
endfunction
function OrigNPC_IPI takes nothing returns boolean
return(OrigNPC_NE==1)
endfunction
function OrigNPC_IQI takes nothing returns nothing
set OrigNPC_NE=GetRandomInt(1,2)
if(OrigNPC_IPI())then
call PlaySoundOnUnitBJ(OrigNPC_CU,'d',GetTriggerUnit())
else
call PlaySoundOnUnitBJ(OrigNPC_RW,'d',GetTriggerUnit())
endif
endfunction
function OrigNPC_IZI takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c001')or(NPCSourceType(GetTriggerUnit())=='c025')
endfunction
function OrigNPC_I_I takes nothing returns boolean
return(GetSpellAbilityId()=='A01M')and(OrigNPC_IZI())
endfunction
function OrigNPC_I0I takes nothing returns boolean
return(OrigNPC_I_I())
endfunction
function OrigNPC_I1I takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_WT,'d',GetTriggerUnit())
endfunction
function OrigNPC_AFI takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c004')and(GetSpellAbilityId()!='S028')
endfunction
function OrigNPC_AGI takes nothing returns boolean
return(OrigNPC_AFI())
endfunction
function OrigNPC_AHI takes nothing returns nothing
call PlaySoundBJ(OrigNPC_H0)
endfunction
function OrigNPC_AKI takes nothing returns boolean
return(GetSpellAbilityId()=='A021')and(GetTriggerUnit()==OrigNPC_KEV)
endfunction
function OrigNPC_ALI takes nothing returns boolean
return(OrigNPC_AKI())
endfunction
function OrigNPC_AMI takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_BY,'d',GetTriggerUnit())
endfunction
function OrigNPC_AQI takes nothing returns boolean
return(GetSpellAbilityId()=='A01N')and(GetTriggerUnit()==OrigNPC_KEV)
endfunction
function OrigNPC_ASI takes nothing returns boolean
return(OrigNPC_AQI())
endfunction
function OrigNPC_ATI takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_X0,'d',GetTriggerUnit())
endfunction
function OrigNPC_AWI takes nothing returns boolean
return(GetSpellAbilityId()=='A01O')and(GetTriggerUnit()==OrigNPC_KEV)
endfunction
function OrigNPC_AYI takes nothing returns boolean
return(OrigNPC_AWI())
endfunction
function OrigNPC_AZI takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_O0,'d',GetTriggerUnit())
endfunction
function OrigNPC_NRI takes nothing returns boolean
return(GetSpellAbilityId()=='A01Q')
endfunction
function OrigNPC_NII takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_NY,'d',GetTriggerUnit())
endfunction
function OrigNPC_CBI takes nothing returns boolean
return(GetSpellAbilityId()=='A006')and(NPCSourceType(GetTriggerUnit())=='R004')
endfunction
function OrigNPC_CCI takes nothing returns boolean
return(OrigNPC_CBI())
endfunction
function OrigNPC_CDI takes nothing returns boolean
return(OrigNPC_NE==5)
endfunction
function OrigNPC_CFI takes nothing returns nothing
set OrigNPC_NE=GetRandomInt(5,6)
if(OrigNPC_CDI())then
call PlaySoundOnUnitBJ(OrigNPC_ZZ,'d',GetTriggerUnit())
else
call PlaySoundOnUnitBJ(OrigNPC_FY,'d',GetTriggerUnit())
endif
endfunction
function OrigNPC_C0I takes nothing returns boolean
return(GetSpellAbilityId()=='A01S')and(NPCSourceType(GetTriggerUnit())=='c00D')
endfunction
function OrigNPC_C1I takes nothing returns boolean
return(OrigNPC_C0I())
endfunction
function OrigNPC_C2I takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_GY,'d',GetTriggerUnit())
endfunction
function OrigNPC_C4I takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='c00D')and(GetSpellAbilityId()!='A012')and(GetSpellAbilityId()!='A00F')and(GetSpellAbilityId()!='A01S')and(GetSpellAbilityId()!='A01S')
endfunction
function OrigNPC_C5I takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_KU,'d',GetTriggerUnit())
endfunction
function OrigNPC_D4I takes nothing returns boolean
return(NPCSourceType(GetSpellAbilityUnit())=='H00S')
endfunction
function OrigNPC_D5I takes nothing returns boolean
return(NPCSourceType(GetSpellAbilityUnit())=='R001')
endfunction
function OrigNPC_D6I takes nothing returns boolean
return(GetSpellAbilityId()=='A01B')and(GetBooleanOr(OrigNPC_D4I(),OrigNPC_D5I()))
endfunction
function OrigNPC_D7I takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_D0,'d',GetTriggerUnit())
endfunction
function OrigNPC_D9I takes nothing returns boolean
return(NPCSourceType(GetSpellAbilityUnit())=='H00S')
endfunction
function OrigNPC_FVI takes nothing returns boolean
return(NPCSourceType(GetSpellAbilityUnit())=='R001')
endfunction
function OrigNPC_FEI takes nothing returns boolean
return(GetSpellAbilityId()=='A01B')and(GetBooleanOr(OrigNPC_D9I(),OrigNPC_FVI()))
endfunction
function OrigNPC_FXI takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_F0,'d',GetTriggerUnit())
endfunction
function OrigNPC_FUI takes nothing returns boolean
return(GetSpellAbilityId()=='A00C')and(GetTriggerUnit()!=OrigNPC_KIV)
endfunction
function OrigNPC_FWI takes nothing returns boolean
return(OrigNPC_FUI())
endfunction
function OrigNPC_FYI takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_BT,'d',GetTriggerUnit())
endfunction
function OrigNPC_GRI takes nothing returns boolean
return(NPCSourceType(GetTriggerUnit())=='h02V')and(GetSpellAbilityId()!='A012')and(GetSpellAbilityId()!='A00F')
endfunction
function OrigNPC_GII takes nothing returns nothing
call PlaySoundOnUnitBJ(OrigNPC_LZ,'d',GetTriggerUnit())
endfunction
function NPCSourceHooks0 takes nothing returns nothing
    set OrigNPC_A4=CreateTrigger()
    call DisableTrigger(OrigNPC_A4)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_A4,EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER)
    call TriggerAddCondition(OrigNPC_A4,Condition(function OrigNPC_OFE))
    call TriggerAddAction(OrigNPC_A4,function OrigNPC_OGE)
    set OrigNPC_A6=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_A6,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_A6,Condition(function OrigNPC_MYE))
    call TriggerAddAction(OrigNPC_A6,function OrigNPC_M1E)
    set OrigNPC_A7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_A7,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_A7,Condition(function OrigNPC_T1E))
    call TriggerAddAction(OrigNPC_A7,function OrigNPC_T3E)
    set OrigNPC_B4=CreateTrigger()
    call DisableTrigger(OrigNPC_B4)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_B4,.03)
    call TriggerAddAction(OrigNPC_B4,function OrigNPC_O1E)
    set OrigNPC_B5=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_B5,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_B5,Condition(function OrigNPC_GCE))
    call TriggerAddAction(OrigNPC_B5,function OrigNPC_GDE)
    set OrigNPC_B6=CreateTrigger()
    call DisableTrigger(OrigNPC_B6)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_B6,.05)
    call TriggerAddAction(OrigNPC_B6,function OrigNPC_M5E)
    set OrigNPC_B7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_B7,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_B7,Condition(function OrigNPC_URE))
    call TriggerAddAction(OrigNPC_B7,function OrigNPC_UAE)
    set OrigNPC_B8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_B8,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_B8,Condition(function OrigNPC_VAX))
    call TriggerAddAction(OrigNPC_B8,function OrigNPC_VNX)
    set OrigNPC_BZV=CreateTrigger()
    call DisableTrigger(OrigNPC_BZV)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_BZV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_BZV,Condition(function OrigNPC_DIR))
    call TriggerAddAction(OrigNPC_BZV,function OrigNPC_DBR)
    set OrigNPC_C5=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_C5,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_C5,Condition(function OrigNPC_GHE))
    call TriggerAddAction(OrigNPC_C5,function OrigNPC_GJE)
    set OrigNPC_C7=CreateTrigger()
    call DisableTrigger(OrigNPC_C7)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_C7,.04)
    call TriggerAddAction(OrigNPC_C7,function OrigNPC_UJE)
    set OrigNPC_C8=CreateTrigger()
    call DisableTrigger(OrigNPC_C8)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_C8,EVENT_PLAYER_UNIT_ISSUED_TARGET_ORDER)
    call TriggerAddCondition(OrigNPC_C8,Condition(function OrigNPC_VCX))
    call TriggerAddAction(OrigNPC_C8,function OrigNPC_VGX)
    set OrigNPC_D5=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_D5,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_D5,Condition(function OrigNPC_GME))
    call TriggerAddAction(OrigNPC_D5,function OrigNPC_HLE)
    set OrigNPC_D7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_D7,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_D7,Condition(function OrigNPC_ULE))
    call TriggerAddAction(OrigNPC_D7,function OrigNPC_U8E)
    set OrigNPC_D8=CreateTrigger()
    call DisableTrigger(OrigNPC_D8)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_D8,.02)
    call TriggerAddAction(OrigNPC_D8,function OrigNPC_VKX)
    set OrigNPC_E3V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_E3V,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_E3V,Condition(function OrigNPC_H8X))
    call TriggerAddAction(OrigNPC_E3V,function OrigNPC_JAX)
endfunction
function NPCSourceHooks1 takes nothing returns nothing
    set OrigNPC_E4=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_E4,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_E4,Condition(function OrigNPC_XJE))
    call TriggerAddAction(OrigNPC_E4,function OrigNPC_XQE)
    set OrigNPC_E4V=CreateTrigger()
    call DisableTrigger(OrigNPC_E4V)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_E4V,.02)
    call TriggerAddAction(OrigNPC_E4V,function OrigNPC_JBX)
    set OrigNPC_E5V=CreateTrigger()
    call DisableTrigger(OrigNPC_E5V)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_E5V,.04)
    call TriggerAddAction(OrigNPC_E5V,function OrigNPC_JDX)
    set OrigNPC_E6=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_E6,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_E6,Condition(function OrigNPC_L0E))
    call TriggerAddAction(OrigNPC_E6,function OrigNPC_MIE)
    set OrigNPC_E6V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_E6V,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_E6V,Condition(function OrigNPC_JGX))
    call TriggerAddAction(OrigNPC_E6V,function OrigNPC_JKX)
    set OrigNPC_E7V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_E7V,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_E7V,Condition(function OrigNPC_JPX))
    call TriggerAddAction(OrigNPC_E7V,function OrigNPC_JTX)
    set OrigNPC_E8V=CreateTrigger()
    call DisableTrigger(OrigNPC_E8V)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_E8V,.03)
    call TriggerAddAction(OrigNPC_E8V,function OrigNPC_J1X)
    set OrigNPC_E9V=CreateTrigger()
    call DisableTrigger(OrigNPC_E9V)
    call TriggerAddAction(OrigNPC_E9V,function OrigNPC_J4X)
    set OrigNPC_ECV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_ECV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_ECV,Condition(function OrigNPC_FDX))
    call TriggerAddAction(OrigNPC_ECV,function OrigNPC_FFX)
    set OrigNPC_EDV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_EDV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_EDV,Condition(function OrigNPC_FHX))
    call TriggerAddAction(OrigNPC_EDV,function OrigNPC_FJX)
    set OrigNPC_EEV=CreateTrigger()
    call DisableTrigger(OrigNPC_EEV)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_EEV,.1)
    call TriggerAddAction(OrigNPC_EEV,function OrigNPC_DLX)
    set OrigNPC_EFV=CreateTrigger()
    call DisableTrigger(OrigNPC_EFV)
    call TriggerAddAction(OrigNPC_EFV,function OrigNPC_FPX)
    set OrigNPC_EGV=CreateTrigger()
    call DisableTrigger(OrigNPC_EGV)
    call TriggerAddAction(OrigNPC_EGV,function OrigNPC_FUX)
    set OrigNPC_EHV=CreateTrigger()
    call DisableTrigger(OrigNPC_EHV)
    call TriggerAddAction(OrigNPC_EHV,function OrigNPC_F_X)
    set OrigNPC_EIV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_EIV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_EIV,Condition(function OrigNPC_D3X))
    call TriggerAddAction(OrigNPC_EIV,function OrigNPC_D7X)
    set OrigNPC_EJV=CreateTrigger()
    call DisableTrigger(OrigNPC_EJV)
    call TriggerAddAction(OrigNPC_EJV,function OrigNPC_F3X)
endfunction
function NPCSourceHooks2 takes nothing returns nothing
    set OrigNPC_EKV=CreateTrigger()
    call DisableTrigger(OrigNPC_EKV)
    call TriggerAddAction(OrigNPC_EKV,function OrigNPC_F7X)
    set OrigNPC_ELV=CreateTrigger()
    call DisableTrigger(OrigNPC_ELV)
    call TriggerAddAction(OrigNPC_ELV,function OrigNPC_GEX)
    set OrigNPC_EMV=CreateTrigger()
    call DisableTrigger(OrigNPC_EMV)
    call TriggerAddAction(OrigNPC_EMV,function OrigNPC_GIX)
    set OrigNPC_EOV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_EOV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_EOV,Condition(function OrigNPC_DUX))
    call TriggerAddAction(OrigNPC_EOV,function OrigNPC_DWX)
    set OrigNPC_EPV=CreateTrigger()
    call DisableTrigger(OrigNPC_EPV)
    call TriggerAddAction(OrigNPC_EPV,function OrigNPC_GCX)
    set OrigNPC_EQV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_EQV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_EQV,Condition(function OrigNPC_GFX))
    call TriggerAddAction(OrigNPC_EQV,function OrigNPC_G9X)
    set OrigNPC_ESV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_ESV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_ESV,Condition(function OrigNPC_HEX))
    call TriggerAddAction(OrigNPC_ESV,function OrigNPC_HXX)
    set OrigNPC_ETV=CreateTrigger()
    call DisableTrigger(OrigNPC_ETV)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_ETV,3.)
    call TriggerAddCondition(OrigNPC_ETV,Condition(function OrigNPC_HRX))
    call TriggerAddAction(OrigNPC_ETV,function OrigNPC_HIX)
    set OrigNPC_EVV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_EVV,EVENT_PLAYER_UNIT_SPELL_ENDCAST)
    call TriggerAddCondition(OrigNPC_EVV,Condition(function OrigNPC_DCX))
    call TriggerAddAction(OrigNPC_EVV,function OrigNPC_DDX)
    set OrigNPC_EXV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_EXV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_EXV,Condition(function OrigNPC_DPX))
    call TriggerAddAction(OrigNPC_EXV,function OrigNPC_DSX)
    set OrigNPC_F3V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_F3V,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_F3V,Condition(function OrigNPC_OVI))
    call TriggerAddAction(OrigNPC_F3V,function OrigNPC_OXI)
    set OrigNPC_F5=CreateTrigger()
    call DisableTrigger(OrigNPC_F5)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_F5,.04)
    call TriggerAddAction(OrigNPC_F5,function OrigNPC_HPE)
    set OrigNPC_F7=CreateTrigger()
    call DisableTrigger(OrigNPC_F7)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_F7,.03)
    call TriggerAddAction(OrigNPC_F7,function OrigNPC_WXE)
    set OrigNPC_F8=CreateTrigger()
    call DisableTrigger(OrigNPC_F8)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_F8,.02)
    call TriggerAddAction(OrigNPC_F8,function OrigNPC_VPX)
    set OrigNPC_F8V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_F8V,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_F8V,Condition(function OrigNPC_OWI))
    call TriggerAddAction(OrigNPC_F8V,function OrigNPC_OZI)
    set OrigNPC_G0V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_G0V,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_G0V,Condition(function OrigNPC_AYI))
    call TriggerAddAction(OrigNPC_G0V,function OrigNPC_AZI)
endfunction
function NPCSourceHooks3 takes nothing returns nothing
    set OrigNPC_G5=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_G5,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_G5,Condition(function OrigNPC_HTE))
    call TriggerAddAction(OrigNPC_G5,function OrigNPC_HWE)
    set OrigNPC_G5V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_G5V,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_G5V,Condition(function OrigNPC_NRI))
    call TriggerAddAction(OrigNPC_G5V,function OrigNPC_NII)
    set OrigNPC_G7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_G7,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_G7,Condition(function OrigNPC_WAE))
    call TriggerAddAction(OrigNPC_G7,function OrigNPC_WME)
    set OrigNPC_G8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_G8,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_G8,Condition(function OrigNPC_VSX))
    call TriggerAddAction(OrigNPC_G8,function OrigNPC_V7X)
    set OrigNPC_GAV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GAV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_GAV,Condition(function OrigNPC_RJI))
    call TriggerAddAction(OrigNPC_GAV,function OrigNPC_RKI)
    set OrigNPC_GBV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GBV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_GBV,Condition(function OrigNPC_RUI))
    call TriggerAddAction(OrigNPC_GBV,function OrigNPC_RWI)
    set OrigNPC_GCV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GCV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_GCV,Condition(function OrigNPC_R_I))
    call TriggerAddAction(OrigNPC_GCV,function OrigNPC_R1I)
    set OrigNPC_GDV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GDV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_GDV,Condition(function OrigNPC_R5I))
    call TriggerAddAction(OrigNPC_GDV,function OrigNPC_R6I)
    set OrigNPC_GGV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GGV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_GGV,Condition(function OrigNPC_IXI))
    call TriggerAddAction(OrigNPC_GGV,function OrigNPC_IRI)
    set OrigNPC_GHV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GHV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_GHV,Condition(function OrigNPC_INI))
    call TriggerAddAction(OrigNPC_GHV,function OrigNPC_IBI)
    set OrigNPC_GJV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GJV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_GJV,Condition(function OrigNPC_IFI))
    call TriggerAddAction(OrigNPC_GJV,function OrigNPC_IGI)
    set OrigNPC_GLV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GLV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_GLV,Condition(function OrigNPC_IMI))
    call TriggerAddAction(OrigNPC_GLV,function OrigNPC_IQI)
    set OrigNPC_GNV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GNV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_GNV,Condition(function OrigNPC_RPI))
    call TriggerAddAction(OrigNPC_GNV,function OrigNPC_RQI)
    set OrigNPC_GPV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GPV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_GPV,Condition(function OrigNPC_I0I))
    call TriggerAddAction(OrigNPC_GPV,function OrigNPC_I1I)
    set OrigNPC_GYV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GYV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_GYV,Condition(function OrigNPC_AGI))
    call TriggerAddAction(OrigNPC_GYV,function OrigNPC_AHI)
    set OrigNPC_GZV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_GZV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_GZV,Condition(function OrigNPC_ALI))
    call TriggerAddAction(OrigNPC_GZV,function OrigNPC_AMI)
endfunction
function NPCSourceHooks4 takes nothing returns nothing
    set OrigNPC_G_V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_G_V,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_G_V,Condition(function OrigNPC_ASI))
    call TriggerAddAction(OrigNPC_G_V,function OrigNPC_ATI)
    set OrigNPC_H5=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_H5,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_H5,Condition(function OrigNPC_H_E))
    call TriggerAddAction(OrigNPC_H5,function OrigNPC_H9E)
    set OrigNPC_H6V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_H6V,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_H6V,Condition(function OrigNPC_D6I))
    call TriggerAddAction(OrigNPC_H6V,function OrigNPC_D7I)
    set OrigNPC_H7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_H7,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_H7,Condition(function OrigNPC_WSE))
    call TriggerAddAction(OrigNPC_H7,function OrigNPC_W_E)
    set OrigNPC_H7V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_H7V,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_H7V,Condition(function OrigNPC_FEI))
    call TriggerAddAction(OrigNPC_H7V,function OrigNPC_FXI)
    set OrigNPC_H8=CreateTrigger()
    call DisableTrigger(OrigNPC_H8)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_H8,.75)
    call TriggerAddAction(OrigNPC_H8,function OrigNPC_EEX)
    set OrigNPC_HLV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_HLV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_HLV,Condition(function OrigNPC_CCI))
    call TriggerAddAction(OrigNPC_HLV,function OrigNPC_CFI)
    set OrigNPC_HTV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_HTV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_HTV,Condition(function OrigNPC_C1I))
    call TriggerAddAction(OrigNPC_HTV,function OrigNPC_C2I)
    set OrigNPC_HUV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_HUV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_HUV,Condition(function OrigNPC_C4I))
    call TriggerAddAction(OrigNPC_HUV,function OrigNPC_C5I)
    set OrigNPC_I4=CreateTrigger()
    call DisableTrigger(OrigNPC_I4)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_I4,.03)
    call TriggerAddAction(OrigNPC_I4,function OrigNPC_OCE)
    set OrigNPC_I6=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_I6,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_I6,Condition(function OrigNPC_MTE))
    call TriggerAddAction(OrigNPC_I6,function OrigNPC_MUE)
    set OrigNPC_I8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_I8,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_I8,Condition(function OrigNPC_Z_E))
    call TriggerAddAction(OrigNPC_I8,function OrigNPC_Z3E)
    set OrigNPC_J4=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_J4,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_J4,Condition(function OrigNPC_RKE))
    call TriggerAddAction(OrigNPC_J4,function OrigNPC_RLE)
    set OrigNPC_J5=CreateTrigger()
    call DisableTrigger(OrigNPC_J5)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_J5,.04)
    call TriggerAddAction(OrigNPC_J5,function OrigNPC_JEE)
    set OrigNPC_J7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_J7,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_J7,Condition(function OrigNPC_W1E))
    call TriggerAddAction(OrigNPC_J7,function OrigNPC_W2E)
    set OrigNPC_J8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_J8,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_J8,Condition(function OrigNPC_EOX))
    call TriggerAddAction(OrigNPC_J8,function OrigNPC_EQX)
endfunction
function NPCSourceHooks5 takes nothing returns nothing
    set OrigNPC_JNV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_JNV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_JNV,Condition(function OrigNPC_GRI))
    call TriggerAddAction(OrigNPC_JNV,function OrigNPC_GII)
    set OrigNPC_JXV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_JXV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_JXV,Condition(function OrigNPC_FWI))
    call TriggerAddAction(OrigNPC_JXV,function OrigNPC_FYI)
    set OrigNPC_K5=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_K5,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_K5,Condition(function OrigNPC_JRE))
    call TriggerAddAction(OrigNPC_K5,function OrigNPC_JIE)
    set OrigNPC_K7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_K7,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_K7,Condition(function OrigNPC_W4E))
    call TriggerAddAction(OrigNPC_K7,function OrigNPC_W5E)
    set OrigNPC_K8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_K8,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_K8,Condition(function OrigNPC_ETX))
    call TriggerAddAction(OrigNPC_K8,function OrigNPC_EUX)
    set OrigNPC_L5=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_L5,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_L5,Condition(function OrigNPC_JNE))
    call TriggerAddAction(OrigNPC_L5,function OrigNPC_JBE)
    set OrigNPC_L7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_L7,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_L7,Condition(function OrigNPC_W7E))
    call TriggerAddAction(OrigNPC_L7,function OrigNPC_W8E)
    set OrigNPC_L8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_L8,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_L8,Condition(function OrigNPC_EZX))
    call TriggerAddAction(OrigNPC_L8,function OrigNPC_E9X)
    set OrigNPC_M5=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_M5,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_M5,Condition(function OrigNPC_JDE))
    call TriggerAddAction(OrigNPC_M5,function OrigNPC_KXE)
    set OrigNPC_M7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_M7,EVENT_PLAYER_UNIT_SPELL_FINISH)
    call TriggerAddCondition(OrigNPC_M7,Condition(function OrigNPC_YVE))
    call TriggerAddAction(OrigNPC_M7,function OrigNPC_YEE)
    set OrigNPC_M8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_M8,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_M8,Condition(function OrigNPC_XEX))
    call TriggerAddAction(OrigNPC_M8,function OrigNPC_XXX)
    set OrigNPC_N4=CreateTrigger()
    call DisableTrigger(OrigNPC_N4)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_N4,EVENT_PLAYER_UNIT_ISSUED_TARGET_ORDER)
    call TriggerAddCondition(OrigNPC_N4,Condition(function OrigNPC_OJE))
    call TriggerAddAction(OrigNPC_N4,function OrigNPC_OKE)
    set OrigNPC_N6=CreateTrigger()
    call DisableTrigger(OrigNPC_N6)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_N6,.05)
    call TriggerAddAction(OrigNPC_N6,function OrigNPC_M3E)
    set OrigNPC_N7=CreateTrigger()
    call DisableTrigger(OrigNPC_N7)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_N7,.04)
    call TriggerAddAction(OrigNPC_N7,function OrigNPC_UEE)
    set OrigNPC_N8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_N8,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_N8,Condition(function OrigNPC_VOX))
    call TriggerAddAction(OrigNPC_N8,function OrigNPC_VRX)
    set OrigNPC_O4=CreateTrigger()
    call DisableTrigger(OrigNPC_O4)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_O4,.25)
    call TriggerAddAction(OrigNPC_O4,function OrigNPC_XZE)
endfunction
function NPCSourceHooks6 takes nothing returns nothing
    set OrigNPC_O6=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_O6,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_O6,Condition(function OrigNPC_MKE))
    call TriggerAddAction(OrigNPC_O6,function OrigNPC_MLE)
    set OrigNPC_O8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_O8,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_O8,Condition(function OrigNPC_ZQE))
    call TriggerAddAction(OrigNPC_O8,function OrigNPC_ZTE)
    set OrigNPC_O_V=CreateTrigger()
    call DisableTrigger(OrigNPC_O_V)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_O_V,EVENT_PLAYER_UNIT_SPELL_FINISH)
    call TriggerAddCondition(OrigNPC_O_V,Condition(function OrigNPC_YQX))
    call TriggerAddAction(OrigNPC_O_V,function OrigNPC_Y1X)
    set OrigNPC_P5=CreateTrigger()
    call DisableTrigger(OrigNPC_P5)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_P5,.03)
    call TriggerAddAction(OrigNPC_P5,function OrigNPC_KFE)
    set OrigNPC_P7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_P7,EVENT_PLAYER_UNIT_SPELL_FINISH)
    call TriggerAddCondition(OrigNPC_P7,Condition(function OrigNPC_YAE))
    call TriggerAddAction(OrigNPC_P7,function OrigNPC_YNE)
    set OrigNPC_P8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_P8,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_P8,Condition(function OrigNPC_XIX))
    call TriggerAddAction(OrigNPC_P8,function OrigNPC_XCX)
    set OrigNPC_Q5=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_Q5,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_Q5,Condition(function OrigNPC_KHE))
    call TriggerAddAction(OrigNPC_Q5,function OrigNPC_KJE)
    set OrigNPC_Q7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_Q7,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_Q7,Condition(function OrigNPC_YDE))
    call TriggerAddAction(OrigNPC_Q7,function OrigNPC_YHE)
    set OrigNPC_Q8=CreateTrigger()
    call DisableTrigger(OrigNPC_Q8)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_Q8,EVENT_PLAYER_UNIT_ISSUED_TARGET_ORDER)
    call TriggerAddCondition(OrigNPC_Q8,Condition(function OrigNPC_XHX))
    call TriggerAddAction(OrigNPC_Q8,function OrigNPC_XLX)
    set OrigNPC_R2V=CreateTrigger()
    call DisableTrigger(OrigNPC_R2V)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_R2V,EVENT_PLAYER_UNIT_SPELL_CHANNEL)
    call TriggerAddCondition(OrigNPC_R2V,Condition(function OrigNPC_GEO))
    call TriggerAddAction(OrigNPC_R2V,function OrigNPC_GBO)
    set OrigNPC_R3V=CreateTrigger()
    call DisableTrigger(OrigNPC_R3V)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_R3V,EVENT_PLAYER_UNIT_SPELL_ENDCAST)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_R3V,EVENT_PLAYER_UNIT_SPELL_FINISH)
    call TriggerAddCondition(OrigNPC_R3V,Condition(function OrigNPC_GFO))
    call TriggerAddAction(OrigNPC_R3V,function OrigNPC_GPO)
    set OrigNPC_R4=CreateTrigger()
    call DisableTrigger(OrigNPC_R4)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_R4,.04)
    call TriggerAddAction(OrigNPC_R4,function OrigNPC_X0E)
    set OrigNPC_R4V=CreateTrigger()
    call DisableTrigger(OrigNPC_R4V)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_R4V,.25)
    call TriggerAddAction(OrigNPC_R4V,function OrigNPC_GUO)
    set OrigNPC_R5V=CreateTrigger()
    call DisableTrigger(OrigNPC_R5V)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_R5V,.25)
    call TriggerAddAction(OrigNPC_R5V,function OrigNPC_G_O)
    set OrigNPC_R6=CreateTrigger()
    call DisableTrigger(OrigNPC_R6)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_R6,.04)
    call TriggerAddAction(OrigNPC_R6,function OrigNPC_MQE)
    set OrigNPC_R6V=CreateTrigger()
    call DisableTrigger(OrigNPC_R6V)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_R6V,.25)
    call TriggerAddAction(OrigNPC_R6V,function OrigNPC_G3O)
endfunction
function NPCSourceHooks7 takes nothing returns nothing
    set OrigNPC_R7V=CreateTrigger()
    call DisableTrigger(OrigNPC_R7V)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_R7V,.25)
    call TriggerAddAction(OrigNPC_R7V,function OrigNPC_G7O)
    set OrigNPC_R8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_R8,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_R8,Condition(function OrigNPC_ZWE))
    call TriggerAddAction(OrigNPC_R8,function OrigNPC_ZYE)
    set OrigNPC_R8V=CreateTrigger()
    call DisableTrigger(OrigNPC_R8V)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_R8V,.25)
    call TriggerAddAction(OrigNPC_R8V,function OrigNPC_HEO)
    set OrigNPC_R9V=CreateTrigger()
    call DisableTrigger(OrigNPC_R9V)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_R9V,.25)
    call TriggerAddAction(OrigNPC_R9V,function OrigNPC_HIO)
    set OrigNPC_REV=CreateTrigger()
    call DisableTrigger(OrigNPC_REV)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_REV,EVENT_PLAYER_UNIT_SPELL_FINISH)
    call TriggerAddCondition(OrigNPC_REV,Condition(function OrigNPC_VWO))
    call TriggerAddAction(OrigNPC_REV,function OrigNPC_V5O)
    set OrigNPC_S7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_S7,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_S7,Condition(function OrigNPC_YLE))
    call TriggerAddAction(OrigNPC_S7,function OrigNPC_YQE)
    set OrigNPC_S8=CreateTrigger()
    call DisableTrigger(OrigNPC_S8)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_S8,EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER)
    call TriggerAddCondition(OrigNPC_S8,Condition(function OrigNPC_XPX))
    call TriggerAddAction(OrigNPC_S8,function OrigNPC_XSX)
    set OrigNPC_T5=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_T5,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_T5,Condition(function OrigNPC_KWE))
    call TriggerAddAction(OrigNPC_T5,function OrigNPC_LOE)
    set OrigNPC_T7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_T7,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_T7,Condition(function OrigNPC_YTE))
    call TriggerAddAction(OrigNPC_T7,function OrigNPC_YUE)
    set OrigNPC_T8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_T8,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_T8,Condition(function OrigNPC_XZX))
    call TriggerAddAction(OrigNPC_T8,function OrigNPC_X_X)
    set OrigNPC_U3=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_U3,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_U3,Condition(function OrigNPC_E8E))
    call TriggerAddAction(OrigNPC_U3,function OrigNPC_E9E)
    set OrigNPC_U7=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_U7,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_U7,Condition(function OrigNPC_YYE))
    call TriggerAddAction(OrigNPC_U7,function OrigNPC_Y_E)
    set OrigNPC_U8=CreateTrigger()
    call DisableTrigger(OrigNPC_U8)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_U8,EVENT_PLAYER_UNIT_ISSUED_TARGET_ORDER)
    call TriggerAddCondition(OrigNPC_U8,Condition(function OrigNPC_X3X))
    call TriggerAddAction(OrigNPC_U8,function OrigNPC_X6X)
    set OrigNPC_V0V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_V0V,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_V0V,Condition(function OrigNPC_N1X))
    call TriggerAddAction(OrigNPC_V0V,function OrigNPC_N2X)
    set OrigNPC_V1V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_V1V,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_V1V,Condition(function OrigNPC_N4X))
    call TriggerAddAction(OrigNPC_V1V,function OrigNPC_N9X)
    set OrigNPC_V4V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_V4V,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_V4V,Condition(function OrigNPC_BHX))
    call TriggerAddAction(OrigNPC_V4V,function OrigNPC_BJX)
endfunction
function NPCSourceHooks8 takes nothing returns nothing
    set OrigNPC_V5V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_V5V,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_V5V,Condition(function OrigNPC_BLX))
    call TriggerAddAction(OrigNPC_V5V,function OrigNPC_C0X)
    set OrigNPC_V6=CreateTrigger()
    call DisableTrigger(OrigNPC_V6)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_V6,.04)
    call TriggerAddAction(OrigNPC_V6,function OrigNPC_LZE)
    set OrigNPC_V6V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_V6V,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_V6V,Condition(function OrigNPC_C3X))
    call TriggerAddAction(OrigNPC_V6V,function OrigNPC_C4X)
    set OrigNPC_V8V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_V8V,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_V8V,Condition(function OrigNPC_DRX))
    call TriggerAddAction(OrigNPC_V8V,function OrigNPC_DIX)
    set OrigNPC_V9V=CreateTrigger()
    call DisableTrigger(OrigNPC_V9V)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_V9V,.7)
    call TriggerAddAction(OrigNPC_V9V,function OrigNPC_DNX)
    set OrigNPC_VAV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_VAV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_VAV,Condition(function OrigNPC_RZX))
    call TriggerAddAction(OrigNPC_VAV,function OrigNPC_R4X)
    set OrigNPC_VEV=CreateTrigger()
    call DisableTrigger(OrigNPC_VEV)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_VEV,.02)
    call TriggerAddAction(OrigNPC_VEV,function OrigNPC_RAX)
    set OrigNPC_VFV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_VFV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_VFV,Condition(function OrigNPC_IJX))
    call TriggerAddAction(OrigNPC_VFV,function OrigNPC_IPX)
    set OrigNPC_VIV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_VIV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_VIV,Condition(function OrigNPC_RTX))
    call TriggerAddAction(OrigNPC_VIV,function OrigNPC_RUX)
    set OrigNPC_VLV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_VLV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_VLV,Condition(function OrigNPC_AVX))
    call TriggerAddAction(OrigNPC_VLV,function OrigNPC_AOX)
    set OrigNPC_VMV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_VMV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_VMV,Condition(function OrigNPC_AIX))
    call TriggerAddAction(OrigNPC_VMV,function OrigNPC_ASX)
    set OrigNPC_VPV=CreateTrigger()
    call DisableTrigger(OrigNPC_VPV)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_VPV,.03)
    call TriggerAddAction(OrigNPC_VPV,function OrigNPC_AUX)
    set OrigNPC_VQV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_VQV,EVENT_PLAYER_UNIT_SPELL_CHANNEL)
    call TriggerAddCondition(OrigNPC_VQV,Condition(function OrigNPC_A_X))
    call TriggerAddAction(OrigNPC_VQV,function OrigNPC_A0X)
    set OrigNPC_VSV=CreateTrigger()
    call DisableTrigger(OrigNPC_VSV)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_VSV,.25)
    call TriggerAddAction(OrigNPC_VSV,function OrigNPC_A5X)
    set OrigNPC_VTV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_VTV,EVENT_PLAYER_UNIT_SPELL_ENDCAST)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_VTV,EVENT_PLAYER_UNIT_SPELL_FINISH)
    call TriggerAddCondition(OrigNPC_VTV,Condition(function OrigNPC_A9X))
    call TriggerAddAction(OrigNPC_VTV,function OrigNPC_NVX)
    set OrigNPC_VUV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_VUV,EVENT_PLAYER_UNIT_SPELL_CHANNEL)
    call TriggerAddCondition(OrigNPC_VUV,Condition(function OrigNPC_NOX))
    call TriggerAddAction(OrigNPC_VUV,function OrigNPC_NAX)
endfunction
function NPCSourceHooks9 takes nothing returns nothing
    set OrigNPC_VVV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_VVV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_VVV,Condition(function OrigNPC_OSX))
    call TriggerAddAction(OrigNPC_VVV,function OrigNPC_OWX)
    set OrigNPC_VWV=CreateTrigger()
    call DisableTrigger(OrigNPC_VWV)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_VWV,.25)
    call TriggerAddAction(OrigNPC_VWV,function OrigNPC_NFX)
    set OrigNPC_VXV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_VXV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_VXV,Condition(function OrigNPC_RBX))
    call TriggerAddAction(OrigNPC_VXV,function OrigNPC_RHX)
    set OrigNPC_VYV=CreateTrigger()
    call DisableTrigger(OrigNPC_VYV)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_VYV,.25)
    call TriggerAddAction(OrigNPC_VYV,function OrigNPC_NLX)
    set OrigNPC_VZV=CreateTrigger()
    call DisableTrigger(OrigNPC_VZV)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_VZV,.25)
    call TriggerAddAction(OrigNPC_VZV,function OrigNPC_NTX)
    set OrigNPC_V_V=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_V_V,EVENT_PLAYER_UNIT_SPELL_ENDCAST)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_V_V,EVENT_PLAYER_UNIT_SPELL_FINISH)
    call TriggerAddCondition(OrigNPC_V_V,Condition(function OrigNPC_NYX))
    call TriggerAddAction(OrigNPC_V_V,function OrigNPC_NZX)
    set OrigNPC_W3=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_W3,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_W3,Condition(function OrigNPC_XXE))
    call TriggerAddAction(OrigNPC_W3,function OrigNPC_XOE)
    set OrigNPC_W5=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_W5,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_W5,Condition(function OrigNPC_LFE))
    call TriggerAddAction(OrigNPC_W5,function OrigNPC_LKE)
    set OrigNPC_W7=CreateTrigger()
    call DisableTrigger(OrigNPC_W7)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_W7,.04)
    call TriggerAddAction(OrigNPC_W7,function OrigNPC_Y1E)
    set OrigNPC_W8=CreateTrigger()
    call DisableTrigger(OrigNPC_W8)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_W8,EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER)
    call TriggerAddCondition(OrigNPC_W8,Condition(function OrigNPC_OVX))
    call TriggerAddAction(OrigNPC_W8,function OrigNPC_OXX)
    set OrigNPC_X4=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_X4,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_X4,Condition(function OrigNPC_XUE))
    call TriggerAddAction(OrigNPC_X4,function OrigNPC_XWE)
    set OrigNPC_X6=CreateTrigger()
    call DisableTrigger(OrigNPC_X6)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_X6,.1)
    call TriggerAddAction(OrigNPC_X6,function OrigNPC_MHE)
    set OrigNPC_X8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_X8,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_X8,Condition(function OrigNPC_ZLE))
    call TriggerAddAction(OrigNPC_X8,function OrigNPC_ZME)
    set OrigNPC_XAV=CreateTrigger()
    call DisableTrigger(OrigNPC_XAV)
    call TriggerAddAction(OrigNPC_XAV,function OrigNPC_K8X)
    set OrigNPC_XEV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_XEV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_XEV,Condition(function OrigNPC_KRX))
    call TriggerAddAction(OrigNPC_XEV,function OrigNPC_KIX)
    set OrigNPC_XIV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_XIV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_XIV,Condition(function OrigNPC_K5X))
    call TriggerAddAction(OrigNPC_XIV,function OrigNPC_K6X)
endfunction
function NPCSourceHooks10 takes nothing returns nothing
    set OrigNPC_XJV=CreateTrigger()
    call TriggerRegisterTimerEventPeriodic(OrigNPC_XJV,3.)
    call TriggerAddAction(OrigNPC_XJV,function OrigNPC_MLX)
    set OrigNPC_XKV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_XKV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_XKV,Condition(function OrigNPC_MQX))
    call TriggerAddAction(OrigNPC_XKV,function OrigNPC_MUX)
    set OrigNPC_XNV=CreateTrigger()
    call DisableTrigger(OrigNPC_XNV)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_XNV,.04)
    call TriggerAddAction(OrigNPC_XNV,function OrigNPC_LVX)
    set OrigNPC_XOV=CreateTrigger()
    call DisableTrigger(OrigNPC_XOV)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_XOV,.02)
    call TriggerAddAction(OrigNPC_XOV,function OrigNPC_KZX)
    set OrigNPC_XRV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_XRV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_XRV,Condition(function OrigNPC_K0X))
    call TriggerAddAction(OrigNPC_XRV,function OrigNPC_K3X)
    set OrigNPC_XTV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_XTV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_XTV,EVENT_PLAYER_UNIT_SPELL_ENDCAST)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_XTV,EVENT_PLAYER_UNIT_SPELL_FINISH)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_XTV,EVENT_PLAYER_UNIT_DEATH)
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_XTV,EVENT_PLAYER_HERO_REVIVE_FINISH)
    call TriggerAddCondition(OrigNPC_XTV,Condition(function OrigNPC_PWX))
    call TriggerAddAction(OrigNPC_XTV,function OrigNPC_P4X)
    set OrigNPC_XVV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_XVV,EVENT_PLAYER_UNIT_SPELL_CAST)
    call TriggerAddCondition(OrigNPC_XVV,Condition(function OrigNPC_J7X))
    call TriggerAddAction(OrigNPC_XVV,function OrigNPC_KXX)
    set OrigNPC_XXV=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_XXV,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_XXV,Condition(function OrigNPC_KNX))
    call TriggerAddAction(OrigNPC_XXV,function OrigNPC_KWX)
    set OrigNPC_Y5=CreateTrigger()
    call DisableTrigger(OrigNPC_Y5)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_Y5,.04)
    call TriggerAddAction(OrigNPC_Y5,function OrigNPC_LME)
    set OrigNPC_Y8=CreateTrigger()
    call TriggerRegisterAnyUnitEventBJ(OrigNPC_Y8,EVENT_PLAYER_UNIT_SPELL_EFFECT)
    call TriggerAddCondition(OrigNPC_Y8,Condition(function OrigNPC_ORX))
    call TriggerAddAction(OrigNPC_Y8,function OrigNPC_OJX)
    set OrigNPC_Z5=CreateTrigger()
    call DisableTrigger(OrigNPC_Z5)
    call TriggerRegisterTimerEventPeriodic(OrigNPC_Z5,.1)
    call TriggerAddAction(OrigNPC_Z5,function OrigNPC_LUE)
endfunction
function NPCSourceHeroes takes nothing returns nothing
    local integer p=0
    loop
        exitwhen p>=12
        if Hero[p]!=null then
            if HeroRole[p]==1 then
                set OrigNPC_JZV=Hero[p]
            elseif HeroRole[p]==2 then
                set OrigNPC_J6V=Hero[p]
            elseif HeroRole[p]==3 then
                set OrigNPC_J3V=Hero[p]
            elseif HeroRole[p]==4 then
                set OrigNPC_J1V=Hero[p]
            elseif HeroRole[p]==5 then
                set OrigNPC_J4V=Hero[p]
            elseif HeroRole[p]==8 then
                set OrigNPC_K0V=Hero[p]
            elseif HeroRole[p]==10 then
                set OrigNPC_J2V=Hero[p]
            endif
        endif
        set p=p+1
    endloop
endfunction
function NPCSourceInit takes nothing returns nothing
    local integer p=0
    if NPCSourceReady then
        return
    endif
    set NPCSourceReady=true
    set OrigNPC_CE=CreateGroup()
    set OrigNPC_GE=CreateGroup()
    set OrigNPC_HE=CreateGroup()
    set OrigNPC_JE=CreateGroup()
    set OrigNPC_KE=CreateGroup()
    set OrigNPC_LE=CreateGroup()
    set OrigNPC_ME=CreateGroup()
    set OrigNPC_MO=CreateGroup()
    set OrigNPC_VR=CreateGroup()
    set OrigNPC_CR=CreateGroup()
    set OrigNPC_DI=CreateGroup()
    set OrigNPC_MA=CreateGroup()
    set OrigNPC_VN=CreateGroup()
    set OrigNPC_FN=CreateGroup()
    set OrigNPC_XC=CreateGroup()
    set OrigNPC_RD=CreateGroup()
    set OrigNPC_BD=CreateGroup()
    set OrigNPC_KD=CreateGroup()
    set OrigNPC_QD=CreateGroup()
    set OrigNPC_JF=CreateGroup()
    set OrigNPC_QF=CreateGroup()
    set OrigNPC_DG=CreateGroup()
    set OrigNPC_HG=CreateGroup()
    set OrigNPC_AJ=CreateGroup()
    set OrigNPC_EK=Rect(-2848.,-1632.,832.,2080.)
    set OrigNPC_HK=Rect(13984.,-8096.,16384.,-7904.)
    set OrigNPC_JK=Rect(13408.,-13376.,13728.,-12768.)
    set OrigNPC_LK=Rect(13408.,-14240.,13856.,-13920.)
    set OrigNPC_MK=Rect(13984.,-10400.,16384.,-10208.)
    set OrigNPC_PK=Rect(12928.,-15488.,13088.,-15328.)
    set OrigNPC_RL=Rect(16160.,-13568.,16256.,-13440.)
    set OrigNPC_SL=Rect(13216.,-11616.,13376.,-11456.)
    set OrigNPC_KM=Rect(-14112.,1024.,-13152.,2016.)
    set OrigNPC_BT=CreateSound("war3mapImported\\SoundSharingan.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_BT,0x738)
    call SetSoundChannel(OrigNPC_BT,0)
    call SetSoundVolume(OrigNPC_BT,0x7F)
    call SetSoundPitch(OrigNPC_BT,1.)
    set OrigNPC_QT=CreateSound("Abilities\\Spells\\Undead\\Sleep\\SleepBirth1.wav",false,true,true,0xA,0xA,"SpellsEAX")
    call SetSoundDuration(OrigNPC_QT,0xC83)
    call SetSoundPitch(OrigNPC_QT,.7)
    set OrigNPC_WT=CreateSound("war3mapImported\\SoundKakashiSkill1.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_WT,0x5E8)
    call SetSoundChannel(OrigNPC_WT,0)
    call SetSoundVolume(OrigNPC_WT,0x7F)
    call SetSoundPitch(OrigNPC_WT,1.)
    set OrigNPC_VU=CreateSound("war3mapImported\\SoundTreeJump.mp3",false,false,false,0xA,0xA,"DefaultEAXON")
    call SetSoundDuration(OrigNPC_VU,720)
    call SetSoundChannel(OrigNPC_VU,0)
    call SetSoundVolume(OrigNPC_VU,0x7F)
    call SetSoundPitch(OrigNPC_VU,1.)
    set OrigNPC_AU=CreateSound("war3mapImported\\SoundItachiThrow.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_AU,288)
    call SetSoundChannel(OrigNPC_AU,0)
    call SetSoundVolume(OrigNPC_AU,0x7F)
    call SetSoundPitch(OrigNPC_AU,1.)
    set OrigNPC_NU=CreateSound("war3mapImported\\SoundJiraiyaRasenganNew.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_NU,0x4C8)
    call SetSoundChannel(OrigNPC_NU,0)
    call SetSoundVolume(OrigNPC_NU,0x7F)
    call SetSoundPitch(OrigNPC_NU,1.)
    set OrigNPC_CU=CreateSound("war3mapImported\\SoundKabutoThrow.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_CU,384)
    call SetSoundChannel(OrigNPC_CU,0)
    call SetSoundVolume(OrigNPC_CU,0x7F)
    call SetSoundPitch(OrigNPC_CU,1.)
    set OrigNPC_KU=CreateSound("war3mapImported\\SoundOrochimaruThrow2.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_KU,984)
    call SetSoundChannel(OrigNPC_KU,0)
    call SetSoundVolume(OrigNPC_KU,0x7F)
    call SetSoundPitch(OrigNPC_KU,1.)
    set OrigNPC_RW=CreateSound("war3mapImported\\SoundKabutoThrow2.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_RW,456)
    call SetSoundChannel(OrigNPC_RW,0)
    call SetSoundVolume(OrigNPC_RW,0x7F)
    call SetSoundPitch(OrigNPC_RW,1.)
    set OrigNPC_AW=CreateSound("war3mapImported\\SoundHinataSpin3.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_AW,648)
    call SetSoundChannel(OrigNPC_AW,0)
    call SetSoundVolume(OrigNPC_AW,0x7F)
    call SetSoundPitch(OrigNPC_AW,1.)
    set OrigNPC_MW=CreateSound("war3mapImported\\SoundGaaraTransform2.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_MW,0x5E8)
    call SetSoundChannel(OrigNPC_MW,0)
    call SetSoundVolume(OrigNPC_MW,0x7F)
    call SetSoundPitch(OrigNPC_MW,1.)
    set OrigNPC_XY=CreateSound("war3mapImported\\Sound_Itachi_Tsukiyomi.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_XY,720)
    call SetSoundChannel(OrigNPC_XY,0)
    call SetSoundVolume(OrigNPC_XY,0x7F)
    call SetSoundPitch(OrigNPC_XY,1.)
    set OrigNPC_OY=CreateSound("war3mapImported\\Sound_Itachi_KatonGokakyu.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_OY,0x720)
    call SetSoundChannel(OrigNPC_OY,0)
    call SetSoundVolume(OrigNPC_OY,0x7F)
    call SetSoundPitch(OrigNPC_OY,1.)
    set OrigNPC_RY=CreateSound("war3mapImported\\Sound_Itachi_MangekyoSharingan.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_RY,0x4F8)
    call SetSoundChannel(OrigNPC_RY,0)
    call SetSoundVolume(OrigNPC_RY,0x7F)
    call SetSoundPitch(OrigNPC_RY,1.)
    set OrigNPC_IY=CreateSound("war3mapImported\\Sound_Jiraiya_Kuchiyose.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_IY,960)
    call SetSoundChannel(OrigNPC_IY,0)
    call SetSoundVolume(OrigNPC_IY,0x7F)
    call SetSoundPitch(OrigNPC_IY,1.)
    set OrigNPC_NY=CreateSound("war3mapImported\\Sound_Kiba_Shikyaku.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_NY,0x468)
    call SetSoundChannel(OrigNPC_NY,0)
    call SetSoundVolume(OrigNPC_NY,0x7F)
    call SetSoundPitch(OrigNPC_NY,1.)
    set OrigNPC_BY=CreateSound("war3mapImported\\Sound_Kisame_Suikodan.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_BY,0x840)
    call SetSoundChannel(OrigNPC_BY,0)
    call SetSoundVolume(OrigNPC_BY,0x7F)
    call SetSoundPitch(OrigNPC_BY,1.)
    set OrigNPC_CY=CreateSound("war3mapImported\\Sound_Lee_UraRenge.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_CY,0x618)
    call SetSoundChannel(OrigNPC_CY,0)
    call SetSoundVolume(OrigNPC_CY,0x7F)
    call SetSoundPitch(OrigNPC_CY,1.)
    set OrigNPC_FY=CreateSound("war3mapImported\\Sound_Neji_Kaiten2.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_FY,816)
    call SetSoundChannel(OrigNPC_FY,0)
    call SetSoundVolume(OrigNPC_FY,0x7F)
    call SetSoundPitch(OrigNPC_FY,1.)
    set OrigNPC_GY=CreateSound("war3mapImported\\Sound_Orochimaru_Kuchiyose.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_GY,0x468)
    call SetSoundChannel(OrigNPC_GY,0)
    call SetSoundVolume(OrigNPC_GY,0x7F)
    call SetSoundPitch(OrigNPC_GY,1.)
    set OrigNPC_HY=CreateSound("war3mapImported\\Sound_Sasuke_Roar.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_HY,0x510)
    call SetSoundChannel(OrigNPC_HY,0)
    call SetSoundVolume(OrigNPC_HY,0x7F)
    call SetSoundPitch(OrigNPC_HY,1.)
    set OrigNPC_KY=CreateSound("war3mapImported\\Sound_Sasuke_ShishiRendan.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_KY,840)
    call SetSoundChannel(OrigNPC_KY,0)
    call SetSoundVolume(OrigNPC_KY,0x7F)
    call SetSoundPitch(OrigNPC_KY,1.)
    set OrigNPC_YY=CreateSound("war3mapImported\\SoundGaaraTransform.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_YY,0x588)
    call SetSoundChannel(OrigNPC_YY,0)
    call SetSoundVolume(OrigNPC_YY,0x7F)
    call SetSoundPitch(OrigNPC_YY,1.)
    set OrigNPC_IZ=CreateSound("war3mapImported\\Sound_Kurenai_JubakuSatsu_32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_IZ,0x5B8)
    call SetSoundChannel(OrigNPC_IZ,0)
    call SetSoundVolume(OrigNPC_IZ,0x7F)
    call SetSoundPitch(OrigNPC_IZ,1.)
    set OrigNPC_CZ=CreateSound("war3mapImported\\Sound_Hinata_HakuroTenbu_32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_CZ,0x630)
    call SetSoundChannel(OrigNPC_CZ,0)
    call SetSoundVolume(OrigNPC_CZ,0x7F)
    call SetSoundPitch(OrigNPC_CZ,1.)
    set OrigNPC_DZ=CreateSound("war3mapImported\\Sound_Hinata_Charge_32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_DZ,0x498)
    call SetSoundChannel(OrigNPC_DZ,0)
    call SetSoundVolume(OrigNPC_DZ,0x7F)
    call SetSoundPitch(OrigNPC_DZ,1.)
    set OrigNPC_FZ=CreateSound("Abilities\\Spells\\Human\\Banish\\BanishLoop1.wav",false,true,true,0xA,0xA,"SpellsEAX")
    call SetSoundDuration(OrigNPC_FZ,0x6B9)
    call SetSoundPitch(OrigNPC_FZ,1.3)
    set OrigNPC_JZ=CreateSound("war3mapImported\\Sound_Neji_HakkeHasangeki32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_JZ,862)
    call SetSoundChannel(OrigNPC_JZ,0)
    call SetSoundVolume(OrigNPC_JZ,0x7F)
    call SetSoundPitch(OrigNPC_JZ,1.)
    set OrigNPC_KZ=CreateSound("war3mapImported\\Sound_Gaara_SabakuTaiso_32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_KZ,0x720)
    call SetSoundChannel(OrigNPC_KZ,0)
    call SetSoundVolume(OrigNPC_KZ,0x7F)
    call SetSoundPitch(OrigNPC_KZ,1.)
    set OrigNPC_LZ=CreateSound("war3mapImported\\Sound_Shizune_Attack32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_LZ,552)
    call SetSoundChannel(OrigNPC_LZ,0)
    call SetSoundVolume(OrigNPC_LZ,0x7F)
    call SetSoundPitch(OrigNPC_LZ,1.)
    set OrigNPC_QZ=CreateSound("war3mapImported\\Sound_Lee_Hachimon32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_QZ,548)
    call SetSoundChannel(OrigNPC_QZ,0)
    call SetSoundVolume(OrigNPC_QZ,0x7F)
    call SetSoundPitch(OrigNPC_QZ,1.)
    set OrigNPC_UZ=CreateSound("war3mapImported\\Sound_Gai_Hachimon32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_UZ,456)
    call SetSoundChannel(OrigNPC_UZ,0)
    call SetSoundVolume(OrigNPC_UZ,0x7F)
    call SetSoundPitch(OrigNPC_UZ,1.)
    set OrigNPC_ZZ=CreateSound("war3mapImported\\Sound_Neji_Kaiten32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_ZZ,552)
    call SetSoundChannel(OrigNPC_ZZ,0)
    call SetSoundVolume(OrigNPC_ZZ,0x7F)
    call SetSoundPitch(OrigNPC_ZZ,1.)
    set OrigNPC_X0=CreateSound("war3mapImported\\Sound_Kisame_Suiro32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_X0,0x600)
    call SetSoundChannel(OrigNPC_X0,0)
    call SetSoundVolume(OrigNPC_X0,0x7F)
    call SetSoundPitch(OrigNPC_X0,1.)
    set OrigNPC_O0=CreateSound("war3mapImported\\Sound_Kisame_MizuBunshin32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_O0,0x648)
    call SetSoundChannel(OrigNPC_O0,0)
    call SetSoundVolume(OrigNPC_O0,0x7F)
    call SetSoundPitch(OrigNPC_O0,1.)
    set OrigNPC_I0=CreateSound("war3mapImported\\Sound_Jiraiya_KatonGamayuEndan_32br.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_I0,0x8B8)
    call SetSoundChannel(OrigNPC_I0,0)
    call SetSoundVolume(OrigNPC_I0,0x7F)
    call SetSoundPitch(OrigNPC_I0,1.)
    set OrigNPC_D0=CreateSound("war3mapImported\\Sound_Sasuke_KatonP1 32br48hz.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_D0,528)
    call SetSoundChannel(OrigNPC_D0,0)
    call SetSoundVolume(OrigNPC_D0,0x7F)
    call SetSoundPitch(OrigNPC_D0,1.)
    set OrigNPC_F0=CreateSound("war3mapImported\\Sound_Sasuke_KatonP2 32br48hz.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_F0,0x4B0)
    call SetSoundChannel(OrigNPC_F0,0)
    call SetSoundVolume(OrigNPC_F0,0x7F)
    call SetSoundPitch(OrigNPC_F0,1.)
    set OrigNPC_G0=CreateSound("war3mapImported\\Sound_Chidori32br38hz.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_G0,0xDE0)
    call SetSoundChannel(OrigNPC_G0,0)
    call SetSoundVolume(OrigNPC_G0,0x7F)
    call SetSoundPitch(OrigNPC_G0,1.)
    set OrigNPC_H0=CreateSound("war3mapImported\\Sound_JutsuAkatsuki32br38hz.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_H0,816)
    call SetSoundChannel(OrigNPC_H0,0)
    call SetSoundVolume(OrigNPC_H0,0x7F)
    call SetSoundPitch(OrigNPC_H0,1.)
    set OrigNPC_M0=CreateSound("war3mapImported\\Sound_Kakashi_Raikiri 32br48hz.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_M0,816)
    call SetSoundChannel(OrigNPC_M0,0)
    call SetSoundVolume(OrigNPC_M0,0x7F)
    call SetSoundPitch(OrigNPC_M0,1.)
    set OrigNPC_P0=CreateSound("war3mapImported\\Sound_Sasuke_Chidori 32br48hz.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_P0,720)
    call SetSoundChannel(OrigNPC_P0,0)
    call SetSoundVolume(OrigNPC_P0,0x7F)
    call SetSoundPitch(OrigNPC_P0,1.)
    set OrigNPC_Q0=CreateSound("war3mapImported\\Sound_ChidoriStart 32br48hz.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_Q0,0xCD8)
    call SetSoundChannel(OrigNPC_Q0,0)
    call SetSoundVolume(OrigNPC_Q0,0x7F)
    call SetSoundPitch(OrigNPC_Q0,1.)
    set OrigNPC_S0=CreateSound("war3mapImported\\Sound_Kakashi_Roar 32br48hz.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_S0,912)
    call SetSoundChannel(OrigNPC_S0,0)
    call SetSoundVolume(OrigNPC_S0,0x7F)
    call SetSoundPitch(OrigNPC_S0,1.)
    set OrigNPC_O1=CreateSound("war3mapImported\\Sound_Hinata_Kaiten 32br48hz.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_O1,600)
    call SetSoundChannel(OrigNPC_O1,0)
    call SetSoundVolume(OrigNPC_O1,0x7F)
    call SetSoundPitch(OrigNPC_O1,1.)
    set OrigNPC_R1=CreateSound("war3mapImported\\Sound_Itachi_Throw 32br48hz.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_R1,264)
    call SetSoundChannel(OrigNPC_R1,0)
    call SetSoundVolume(OrigNPC_R1,0x7F)
    call SetSoundPitch(OrigNPC_R1,1.)
    set OrigNPC_I2=CreateSound("war3mapImported\\Sound_Shikamaru_Throw3 32br48hz.mp3",false,false,false,0xA,0xA,"")
    call SetSoundDuration(OrigNPC_I2,624)
    call SetSoundChannel(OrigNPC_I2,0)
    call SetSoundVolume(OrigNPC_I2,0x7F)
    call SetSoundPitch(OrigNPC_I2,1.)
    set OrigNPC_MWV=CreateGroup()
    call NPCSourceHooks0()
    call NPCSourceHooks1()
    call NPCSourceHooks2()
    call NPCSourceHooks3()
    call NPCSourceHooks4()
    call NPCSourceHooks5()
    call NPCSourceHooks6()
    call NPCSourceHooks7()
    call NPCSourceHooks8()
    call NPCSourceHooks9()
    call NPCSourceHooks10()
    call NPCSourceHeroes()
    if CampaignStage==12 then
        call EnableTrigger(OrigNPC_R2V)
        call EnableTrigger(OrigNPC_R3V)
    endif
endfunction
function NPCSourceBind takes unit u, integer kind returns nothing
    call NPCSourceInit()
    if kind==3 then
        set OrigNPC_KIV=u
    endif
    if kind==4 then
        set OrigNPC_KEV=u
    endif
    if kind==9 then
        set OrigNPC_LDV=u
    endif
    if kind==33 then
        set OrigNPC_QA=u
    endif
    if kind==32 and GetUnitX(u)==CampaignMedicX[0] and GetUnitY(u)==CampaignMedicY[0] then
        set OrigNPC_IF[0]=u
    endif
    if kind==32 and GetUnitX(u)==CampaignMedicX[1] and GetUnitY(u)==CampaignMedicY[1] then
        set OrigNPC_IF[1]=u
    endif
    if kind==32 and GetUnitX(u)==CampaignMedicX[2] and GetUnitY(u)==CampaignMedicY[2] then
        set OrigNPC_IF[2]=u
    endif
    if kind==32 and GetUnitX(u)==CampaignMedicX[3] and GetUnitY(u)==CampaignMedicY[3] then
        set OrigNPC_IF[3]=u
    endif
    if kind==32 and GetUnitX(u)==CampaignMedicX[4] and GetUnitY(u)==CampaignMedicY[4] then
        set OrigNPC_IF[4]=u
    endif
    if kind==32 and GetUnitX(u)==CampaignMedicX[5] and GetUnitY(u)==CampaignMedicY[5] then
        set OrigNPC_IF[5]=u
    endif
endfunction

// First forest Haku: original UBR/UNR/UCR tree response with a released location.
function NPCFirstHakuTree takes nothing returns nothing
    call IssueTargetOrderById(GetEnumUnit(),0xD00B2,GetEnumDestructable())
endfunction
function NPCFirstHakuResponse takes nothing returns nothing
    local location point=null
    if GetWidgetLife(GetEnumUnit())<=1500. then
        call UnitAddAbility(GetEnumUnit(),'ANfa')
        set point=GetUnitLoc(GetEnumUnit())
        call OrigNPC_M8V(700.,point,function NPCFirstHakuTree)
        call RemoveLocation(point)
    endif
    set point=null
endfunction
function NPCFirstHaku takes unit u returns nothing
    if NPCFirstGroup==null then
        set NPCFirstGroup=CreateGroup()
    endif
    call GroupAddUnit(NPCFirstGroup,u)
    call ForGroup(NPCFirstGroup,function NPCFirstHakuResponse)
    call GroupRemoveUnit(NPCFirstGroup,u)
endfunction

function NPCBindAliases takes unit u, integer kind returns nothing
    if kind==3 then
        set OrigNPC_KIV=u
    endif
    if kind==4 then
        set OrigNPC_KEV=u
    endif
    if kind==9 then
        set OrigNPC_LDV=u
    endif
endfunction
