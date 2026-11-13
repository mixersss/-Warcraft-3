
local checks=0
local function check(ok) assert(ok); checks=checks+1 end
LUA_TRUE=1; LUA_FALSE=0
TE_LEVELUP=1; MIS_HELP_DESP=1
print=function(...) end
local triggers={}
function InitTrigger() Trigger={}; for i=1,16 do Trigger[i]={conditions={},actions={}} end end
function TriggerCondition(i,f,...) table.insert(Trigger[i].conditions,{f=f,args={...}}) end
function TriggerAction(i,f,...) table.insert(Trigger[i].actions,{f=f,args={...}}) end
function GetMultiTrigger() return Trigger end
function RegTrigger(id,i) triggers[id]=Trigger[i] end
function HelpInfo() end
function AddTrigger() end
function SaveMissionData(r) r.saved=(r.saved or 0)+1 end
function IsSpawnPos(r,name) if r.birth==name then return 1 else return 0 end end
function ObligeAcceptMission(r,id)
 if r.refused then return 0 end
 r.mission=id; r.boxes=(r.boxes or 0)+1; return 1
end
function MultiTrigger(r,n,p,t,count)
 for i=1,count do
  local match=true
  for _,c in ipairs(t[i].conditions) do if c.f(r,table.unpack(c.args))~=1 then match=false end end
  if match then for _,a in ipairs(t[i].actions) do a.f(r,table.unpack(a.args)) end; return end
 end
end
function IsPlayer(r) return r.player or 1 end
function PfEqual(r,p) return (r.job or 0)==p and 1 or 0 end
function NoRecord(r,id) if r.error then return nil end; return r.record==id and 0 or 1 end
function NoMission(r,id) return r.mission==id and 0 or 1 end
function GetChaFreeBagGridNum(r) return r.free or 10 end
function NoItem(r,id) return r.owned==id and 0 or 1 end
function BankNoItem(r,id) return r.bank==id and 0 or 1 end
function EquipNoItem(r,id) return r.equip==id and 0 or 1 end
