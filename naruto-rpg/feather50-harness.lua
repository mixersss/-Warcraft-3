-- Exercise the actual feather action and emitter with overlapping Kabuto casts.
local saved={};local function mock(n,v)saved[n]={value=_G[n]};_G[n]=v end
local casterA=CreateUnit(15,raw('c00B'),10,20,0);local casterB=CreateUnit(15,raw('c00B'),30,40,0)
local victimA=CreateUnit(0,raw('R000'),100,100,0);local victimB=CreateUnit(3,raw('R001'),300,100,0)
local current=casterA;local enum=nil;local nested=false;local sceneChange=false;local disabled=0
local places={};local made,gone=0,0;local actors={};local roots={}
local nativeGroup=CreateGroup;local nativeDestroy=DestroyGroup
mock('CreateGroup',function()made=made+1;return nativeGroup()end)
mock('DestroyGroup',function(g)gone=gone+1;nativeDestroy(g)end)
mock('Location',function(x,y)local l={x=x,y=y};places[l]=true;return l end)
mock('GetUnitLoc',function(u)return Location(u.x,u.y)end)
mock('GetLocationX',function(l)return l.x end);mock('GetLocationY',function(l)return l.y end)
mock('RemoveLocation',function(l)assert(places[l],'No duplicate/free foreign feather location');places[l]=nil end)
mock('GetTriggerUnit',function()return current end)
mock('GetSpellTargetLoc',function()return Location(100,100)end)
mock('GetEnumUnit',function()return enum end)
mock('ForGroupBJ',function(g,fn)local prev=enum;local copy={table.unpack(g)};for _,u in ipairs(copy)do enum=u;fn()end;enum=prev end)
mock('OrigNPC_PIV',function(r,l,filter)local g=CreateGroup();assert(r==800);if filter==OrigNPC_V2X then g[1]=current==casterA and victimA or victimB else assert(filter==OrigNPC_VTX)end;return g end)
mock('PlaySoundOnUnitBJ',function()end)
mock('CreateNUnitsAtLocFacingLocBJ',function(n,id,owner,l,t)assert(id==raw('h02H'));bj_lastCreatedUnit=CreateUnit(owner,id,l.x,l.y,0)end)
mock('CreateNUnitsAtLoc',function(n,id,owner,l,f)assert(id==raw('h02A')or id==raw('h02B'));bj_lastCreatedUnit=CreateUnit(owner,id,l.x,l.y,f);actors[#actors+1]=bj_lastCreatedUnit end)
mock('IssueTargetOrderById',function(u,id,target)roots[#roots+1]={u=u,target=target}end)
mock('UnitApplyTimedLifeBJ',function(seconds,buff,u)u.lifeTime=seconds end)
mock('SetUnitTimeScalePercent',function(u,p)u.scalePercent=p end)
mock('SetUnitVertexColorBJ',function()end)
mock('EnableTrigger',function()end);mock('DisableTrigger',function()disabled=disabled+1 end)
mock('TriggerSleepAction',function(t)
 OrigNPC_DC=casterB;OrigNPC_JR={};OrigNPC_JR1={};OrigNPC_JR2={}
 if t==.5 then
  OrigNPC_EEX()
  if not nested and not sceneChange then
   nested=true;current=casterB;OrigNPC_V7X();current=casterA
   assert(Sleep50Casts==1 and not casterB.paused and victimB.scalePercent==100,'Nested cast restores only its own state')
  elseif sceneChange then
   Water50Epoch=Water50Epoch+1;Sleep50Casts=1
   for i=0,63 do Sleep50Targets[i]=nil;Sleep50Visuals[i]=nil;Sleep50Casters[i]=nil end
  end
 elseif t==5.5 then OrigNPC_EEX() else error('Unexpected feather delay')end
end)
Sleep50Casts=0;for i=0,63 do Sleep50Targets[i]=nil end
OrigNPC_V7X()
assert(not casterA.paused and not casterB.paused and victimA.scalePercent==100 and victimB.scalePercent==100)
assert(Sleep50Casts==0 and disabled==1 and made==gone and next(places)==nil)
assert(#roots==2 and roots[1].target==victimA and roots[2].target==victimB)
assert(#actors>=8);for _,u in ipairs(actors)do assert(u.removed and u.lifeTime==.65,'Every private feather actor removed')end
sceneChange=true;disabled=0;OrigNPC_V7X();assert(Sleep50Casts==1 and disabled==0 and made==gone and next(places)==nil,'Old completion cannot disable new scene emitter')
Sleep50Casts=0
for n,e in pairs(saved)do _G[n]=e.value end
print('PASS: overlapping Kabuto feather casts restore actual casters/victims, private visuals and groups cleaned, no double location free, original finite timing, scene-safe emitter (native mocks)')
