debug.setmetatable('',{__add=function(a,b)return tostring(a)..tostring(b)end})
function raw(s)local n=0;for i=1,#s do n=n*256+string.byte(s,i)end;return n end
function FourCC(s)return raw(s)end
MAP_CONTROL_USER=1;MAP_CONTROL_COMPUTER=2;PLAYER_SLOT_STATE_PLAYING=1;PLAYER_STATE_RESOURCE_GOLD=0
UNIT_TYPE_DEAD=1;UNIT_TYPE_HERO=2;UNIT_TYPE_STRUCTURE=3;UNIT_STATE_MAX_LIFE=1
EVENT_PLAYER_UNIT_SPELL_EFFECT=1
World={};Controllers={};Slots={};Gold={};udg_units01={};udg_integers16={};udg_booleans04={};udg_integer08=0;udg_boolean01=false;udg_boolean04=false
udg_rect14={x=-4000,y=-6000};udg_rect33={x=-300,y=-9000};udg_rect11={x=0,y=-8704}
udg_rects02={};for k=1,8 do udg_rects02[k]={x=99999,y=99999}end;udg_rect31={x=4000,y= -6000}
udg_rects03={{x=-1152,y=-8704},{x=0,y=-7552},{x=1152,y=-8704},{x=0,y=-9856}}
bj_mapInitialPlayableArea={all=true};bj_FORCE_ALL_PLAYERS={};udg_trigger62={enabled=false}
function Player(p)return p end
function GetPlayerId(p)return p end
function GetPlayerController(p)return Controllers[p]or MAP_CONTROL_USER end
function GetPlayerSlotState(p)return Slots[p]or 0 end
function CreateGroup()return {}end
function GroupClear(g)for k in pairs(g)do g[k]=nil end end
function FirstOfGroup(g)return g[1]end
function GroupRemoveUnit(g,u)for i,v in ipairs(g)do if v==u then table.remove(g,i);return end end end
function GroupEnumUnitsInRect(g,r)GroupClear(g);for _,u in ipairs(World)do if not u.removed and(r.all or(u.x==r.x and u.y==r.y))then g[#g+1]=u end end end
function GroupEnumUnitsInRange(g,x,y,r)GroupClear(g);for _,u in ipairs(World)do if not u.removed and(u.x-x)^2+(u.y-y)^2<=r*r then g[#g+1]=u end end end
function CreateUnit(p,id,x,y,f)local u={owner=p,id=id,x=x,y=y,hp=1000,max=1000,level=1,points=1,abilities={},items={},str=20,agi=20,int=20};World[#World+1]=u;return u end
function RemoveUnit(u)u.removed=true end
function GetUnitTypeId(u)return u and not u.removed and u.id or 0 end
function GetOwningPlayer(u)return u.owner end
function GetUnitX(u)return u.x end
function GetUnitY(u)return u.y end
function GetUnitName(u)return 'mock hero'end
function GetRectCenterX(r)return r.x end
function GetRectCenterY(r)return r.y end
function IsUnitType(u,t)if t==UNIT_TYPE_DEAD then return u.dead or false elseif t==UNIT_TYPE_HERO then return not u.structure else return u.structure or false end end
function GetWidgetLife(u)return u.hp end
function GetUnitState(u,s)return u.max end
function IsUnitPaused(u)return u.paused or false end
function IsUnitEnemy(u,p)return (u.owner>=9 and u.owner<=11 and p<8)or(u.owner<8 and p>=9 and p<=11)end
function IsUnitAlly(u,p)return not IsUnitEnemy(u,p)end
function IsUnitVisible(u,p)return not u.invisible end
function RectContainsUnit(r,u)return r.all or(u.x==r.x and u.y==r.y)end
function UnitItemInSlot(u,k)return u.items[k]end
function GetItemTypeId(i)return i and i.id or 0 end
function UnitAddItemById(u,id)for k=0,5 do if not u.items[k]then local i={id=id};u.items[k]=i;return i end end end
function UnitUseItem(u,i)u.used=i.id;u.hp=u.max;for k,v in pairs(u.items)do if v==i then u.items[k]=nil end end;return true end
function GetPlayerState(p,k)return Gold[p]or 0 end
function SetPlayerState(p,k,v)Gold[p]=v end
function GetRandomInt(a,b)return a end
function ModuloInteger(a,b)return a%b end
function GetHeroLevel(u)return u.level end
function GetHeroSkillPoints(u)return u.points end
function SelectHeroSkill(u,id)if u.points>0 and(u.abilities[id]or 0)<4 then u.abilities[id]=(u.abilities[id]or 0)+1;u.points=u.points-1 end end
function GetUnitAbilityLevel(u,id)return u.abilities[id]or 0 end
function IssuePointOrder(u,o,x,y)u.last={o=o,x=x,y=y};return true end
function IssueTargetOrder(u,o,t)u.last={o=o,target=t};return true end
function IssueImmediateOrder(u,o)u.last={o=o};return true end
function IsTriggerEnabled(t)return t and t.enabled or false end
Timers=0;Triggers=0
function CreateTimer()Timers=Timers+1;return {}end
function TimerStart(t,period,repeats,fn)t.period=period;t.fn=fn end
function CreateTrigger()Triggers=Triggers+1;return {}end
function TriggerRegisterAnyUnitEventBJ()end
function TriggerRegisterPlayerChatEvent()end
function TriggerAddAction()end
function DisplayTimedTextToForce()end
function DisplayTimedTextToPlayer()end
function I2S(i)return tostring(i)end
function R2I(r)return math.floor(r)end
function GetHeroStr(u)return u.str end;function SetHeroStr(u,v)u.str=v end
function GetHeroAgi(u)return u.agi end;function SetHeroAgi(u,v)u.agi=v end
function GetHeroInt(u)return u.int end;function SetHeroInt(u,v)u.int=v end
NativePurchases=0;StockAvailable=true
function IssueNeutralTargetOrder(p,shop,o,u)assert(o=='neutralinteract');shop.buyer=u;return true end
function IssueNeutralImmediateOrderById(p,shop,id)local price=id==raw('ofro')and 20000 or id==raw('modt')and 50000 or id==raw('pghe')and 600 or 999999;if StockAvailable and Gold[p]>=price then Gold[p]=Gold[p]-price;UnitAddItemById(shop.buyer,id);NativePurchases=NativePurchases+1;return true end;return false end
function GetTriggerUnit()return TriggerUnit end
function GetSpellAbilityId()return SpellId end
function GetTriggerPlayer()return 0 end

function GetSummoningUnit()return Summoning end
function GetSummonedUnit()return Summoned end
