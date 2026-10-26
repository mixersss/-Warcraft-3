-- Native registration and storage mocks; original action semantics are tested separately.
local nativeIds=setmetatable({},{__mode='k'});local nextNativeId=100
function GetHandleId(h)if not nativeIds[h]then nextNativeId=nextNativeId+1;nativeIds[h]=nextNativeId end;return nativeIds[h]end
function InitHashtable()return {}end
function LoadReal(t,p,c)return t[p] and t[p][c] or 0 end
function SaveReal(t,p,c,v)t[p]=t[p]or{};t[p][c]=v;return true end
function FlushChildHashtable(t,p)t[p]=nil end
function DestroyTrigger(t)if t then t.destroyed=true end end
function TriggerRegisterAnyUnitEventBJ()end
function TriggerRegisterTimerEventPeriodic(t,d)t.period=d end
function TriggerRegisterPlayerUnitEventSimple()end
function TriggerRegisterUnitEvent()end
function TriggerRegisterEnterRectSimple()end
function TriggerRegisterLeaveRectSimple()end
function TriggerAddCondition()end
function SetSoundConeAngles()end
function SetSoundConeOrientation()end
function SetSoundDistanceCutoff()end
function SetSoundDistances()end
function CreateSound(path,...)return {path=path}end
function SetSoundDuration(s,d)s.duration=d end
function SetSoundChannel()end
function SetSoundVolume()end
function SetSoundPitch()end
function Rect(a,b,c,d)return {a,b,c,d}end
function SquareRoot(n)return math.sqrt(n)end

function Condition(f)return f end
function EnableTrigger(t)t.enabled=true end
function DisableTrigger(t)t.enabled=false end
function TriggerRegisterUnitLifeEvent(t,u,op,hp)t.unit=u;t.threshold=hp end

function ConvertPlayerColor(p)return p end
function SetUnitColor(u,c)u.color=c end
function GroupAddUnit(g,u)for _,v in ipairs(g)do if v==u then return end end;g[#g+1]=u end
local npcEnumUnit=nil
function GetEnumUnit()return npcEnumUnit end
function ForGroup(g,callback)local old=npcEnumUnit;local snapshot={table.unpack(g)};for _,u in ipairs(snapshot)do npcEnumUnit=u;callback()end;npcEnumUnit=old end
function ForGroupBJ(g,callback)ForGroup(g,callback)end

function LoadBoolean(t,p,c)return t[p] and t[p][c] or false end
function SaveBoolean(t,p,c,v)t[p]=t[p]or{};t[p][c]=v;return true end
function UnitAddItemByIdSwapped(id,u)local it=CreateItem(id,u.x,u.y);UnitAddItem(u,it);return it end
function GetTriggeringTrigger()return NativeCurrentTrigger end
function CreateNUnitsAtLoc(n,id,p,loc,f)
 for k=1,n do bj_lastCreatedUnit=CreateUnit(p,id,loc.x or loc[1],loc.y or loc[2],f)end
 return {bj_lastCreatedUnit}
end

function GetUnitLoc(u)return {x=u.x,y=u.y}end
function RemoveLocation(loc)loc.removed=true end

function IssueImmediateOrderById(u,id)u.last={o=id};return true end

function UnitId2String(n)return n end
function GroupEnumUnitsOfType(g,id,filter)
 for _,u in ipairs(World)do if u.type==id then GroupAddUnit(g,u)end end
end
function RAbsBJ(n)return math.abs(n)end
function DestroyGroup(g)g.destroyed=true end

function LoadInteger(t,p,c)return t[p] and t[p][c] or 0 end
function SaveInteger(t,p,c,v)t[p]=t[p]or{};t[p][c]=v;return true end

function ExecuteFunc(name)assert(type(_G[name])=='function','Missing ExecuteFunc target: '..name);_G[name]()end

-- Classic per-unit damage registrations for Naruto clone impact handling.
EVENT_UNIT_DAMAGED='damaged'
function GetEventDamage()return NativeEventDamage or 0 end
function SaveTriggerHandle(t,p,c,v)t[p]=t[p]or{};t[p][c]=v;return true end
function LoadTriggerHandle(t,p,c)return t[p]and t[p][c]or nil end
function IsUnitInGroup(u,g)for _,v in ipairs(g)do if u==v then return true end end;return false end
function TriggerRegisterUnitEvent(t,u,event)t.unitEvents=t.unitEvents or{};t.unitEvents[#t.unitEvents+1]={unit=u,event=event}end

function SaveInteger(t,p,c,v)t[p]=t[p]or{};t[p][c]=v;return true end
function LoadInteger(t,p,c)return t[p]and t[p][c]or 0 end
UNIT_TYPE_SUMMONED='summoned'
