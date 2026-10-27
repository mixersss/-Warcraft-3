-- Invoke the shipped Kisame water-ring action while its old shared caster binding changes.
local saved={};local function mock(name,value)saved[name]={value=_G[name]};_G[name]=value end
CampaignStage=31;CampaignTransition=false;CampaignFinished=false
local caster=CreateUnit(15,raw('c004'),100,200,0);local other=CreateUnit(15,raw('c004'),400,200,0)
local shark=CreateUnit(15,raw('h01E'),200,300,0);local foreign=CreateUnit(15,raw('e002'),0,0,0)
OrigNPC_MA={foreign};local pauses={};local enum=nil;local spawnCount=0;local groupMade,groupGone=0,0;local places={};local sceneChange=false;local cancelEarly=false;local changed=false;local disabled=0
local nativeGroup=CreateGroup;local nativeDestroy=DestroyGroup;local nativePause=PauseUnit
mock('CreateGroup',function()groupMade=groupMade+1;return nativeGroup()end)
mock('DestroyGroup',function(g)groupGone=groupGone+1;nativeDestroy(g)end)
mock('Location',function(x,y)local l={x=x,y=y};places[l]=true;return l end)
mock('GetLocationX',function(l)return l.x end);mock('GetLocationY',function(l)return l.y end)
mock('GetUnitLoc',function(u)return Location(u.x,u.y)end)
mock('GetSpellTargetLoc',function()return Location(200,300)end)
mock('RemoveLocation',function(l)assert(places[l],'No double/free foreign locations');places[l]=nil end)
mock('GetTriggerUnit',function()return caster end)
mock('GetEnumUnit',function()return enum end)
mock('ForGroupBJ',function(g,fn)for _,u in ipairs(g)do enum=u;fn()end;enum=nil end)
mock('OrigNPC_PBV',function(id)assert(id==raw('h01E'));local g=CreateGroup();g[1]=shark;return g end)
mock('CreateNUnitsAtLocFacingLocBJ',function(n,id,owner,l,target)assert(n==1 and id==raw('e002'));bj_lastCreatedUnit=CreateUnit(owner,id,l.x,l.y,0);spawnCount=spawnCount+1 end)
mock('UnitApplyTimedLifeBJ',function(seconds,buff,u)u.lifeTime=seconds end)
mock('IssuePointOrderByIdLoc',function(u,id,l)assert(u==shark)end)
mock('SetUnitVertexColorBJ',function(u,r,g,b,t)u.alpha=255*(100-t)/100 end)
mock('EnableTrigger',function()end);mock('DisableTrigger',function()disabled=disabled+1 end)
mock('PauseUnit',function(u,v)pauses[#pauses+1]={u=u,value=v};nativePause(u,v)end)
mock('TriggerSleepAction',function(t)
 OrigNPC_KEV=other
 if not changed and ((sceneChange and t==.2)or(cancelEarly and t==.01))then
  Water50Epoch=Water50Epoch+1;Water50Casts=sceneChange and 1 or 0;changed=true
 end
end)
Water50Casts=0;OrigNPC_KEV=caster
OrigNPC_G9X();assert(spawnCount==9 and Water50Casts==0 and groupMade==2 and groupGone==2 and next(places)==nil)
assert(#pauses==2 and pauses[1].u==caster and pauses[1].value and pauses[2].u==caster and not pauses[2].value and not caster.paused and not other.paused,'Pause/unpause actual caster despite overwritten shared binding')
assert(not foreign.removed and OrigNPC_MA[1]==foreign,'Never remove another cast water actors')
assert(disabled==1)
sceneChange=true;changed=false;disabled=0;OrigNPC_G9X();assert(Water50Casts==1 and disabled==0 and next(places)==nil,'Old scene completion cannot stop a newer scene water effect')
sceneChange=false;cancelEarly=true;changed=false;local before=spawnCount;OrigNPC_G9X();assert(spawnCount==before and next(places)==nil and groupMade==groupGone,'Cancelled early action releases group/location without spawning water')
Water50Casts=0
for name,entry in pairs(saved)do _G[name]=entry.value end
print('PASS: Kisame actual caster captured before sleeps,9 original water actors, local groups/all temporary locations freed, no foreign cast removal, epoch-aware shared effect lifetime and early cancellation (native mocks)')
