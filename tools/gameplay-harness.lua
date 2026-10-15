-- Only the native API is substituted. All map functions come from shipped JASS.
-- Lua's string __add represents JASS string concatenation in the translator.
debug.setmetatable('', {__add=function(a,b) return tostring(a)..tostring(b) end})
UNIT_TYPE_DEAD, UNIT_TYPE_STRUCTURE = 'dead', 'structure'
UNIT_TYPE_SUMMONED = 'summoned'
UNIT_TYPE_UNDEAD, UNIT_TYPE_HERO = 'undead', 'hero'
UNIT_STATE_MAX_LIFE, UNIT_STATE_LIFE, UNIT_STATE_MANA, UNIT_STATE_MAX_MANA = 'max', 'hp', 'mana', 'maxmana'
PLAYER_STATE_RESOURCE_GOLD = 'gold'
Players, World = {}, {}
function Player(p) return p end
function I2R(n) return n end
function R2I(n) return math.modf(n) end
function I2S(n) return tostring(n) end
function ModuloInteger(a,b) return a%b end
function GetPlayerId(p) return p end
function GetPlayerName(p) return 'Player '..p end
function GetOwningPlayer(u) return u.owner end
function GetUnitTypeId(u) return u.id end
function GetWidgetLife(u) return u.hp end
function GetUnitState(u,k) return u[k] end
function SetUnitState(u,k,v) u[k]=math.min(v,u[k=='hp' and 'max' or 'maxmana']) end
function IsUnitType(u,t) return (t=='dead' and u.hp<=0) or u[t]==true end
function IsUnitAlly(u,p) return TeamOf(u.owner)==TeamOf(p) end
function GetPlayerState(p,k) return Players[p][k] end
function SetPlayerState(p,k,v) Players[p][k]=v end
function SetPlayerTechResearched(p,k,v) Players[p].tech[k]=v end
function GetPlayerTechCount(p,k) return Players[p].tech[k] or 0 end
function SelectUnitForPlayerSingle(u,p) Players[p].selection=u end
function GetHeroStr(u) return u.str end
function GetHeroAgi(u) return u.agi end
function GetHeroInt(u) return u.int end
function SetHeroStr(u,v) u.str=v end
function SetHeroAgi(u,v) u.agi=v end
function SetHeroInt(u,v) u.int=v end
function GetHeroLevel(u) return u.level end
function GetUnitX(u) return u.x end
function GetUnitY(u) return u.y end
function SetUnitUserData(u,v) u.data=v end
function GetUnitUserData(u) return u.data or 0 end
function CreateUnit(p,id,x,y,facing)
    local u={owner=p,id=id,x=x,y=y,hp=100,max=100,mana=100,maxmana=100,str=20,agi=20,int=20,level=1,data=0,abilities={},points=1}
    table.insert(World,u)
    return u
end
function IssuePointOrder(u,order,x,y) u.order={order,x,y}; return true end
function IssueImmediateOrder(u,order) u.order={order};return AllowedOrders and AllowedOrders[order] or false end
function IssueTargetOrder(u,order,target) u.order={order,target};return AllowedOrders and AllowedOrders[order] or false end
function GetUnitAbilityLevel(u,id) return u.abilities[id] or 0 end
function UnitAddAbility(u,id) u.abilities[id]=1;return true end
function UnitMakeAbilityPermanent(u,v,id) return true end
function SetUnitAbilityLevel(u,id,rank) u.abilities[id]=rank;return rank end
function GetSummonedUnit() return Summoned end
function GetSummoningUnit() return Summoner end
function PauseUnit(u,v) u.paused=v end
function SetHeroLevel(u,level) u.points=u.points+level-u.level;u.level=level end
function SelectHeroSkill(u,skill)
    if u.points<=0 then return end
    local kind=-1
    for k=0,HERO_COUNT-1 do if HeroType[k]==u.id then kind=k end end
    assert(kind>=0,'Learned skills must belong to a roster hero')
    local slot=-1
    for k=0,3 do if ResolvedSkill(u,HeroSkill[kind*4+k])==skill then slot=k end end
    assert(slot>=0,'Bot attempted a skill not owned by its hero')
    local old=u.abilities[skill] or 0
    local config=assert(SkillCaps[skill],'Missing emitted ability configuration')
    if old<config.cap and u.level>=config.req+old*config.skip then
        u.abilities[skill]=old+1;u.points=u.points-1
        -- Native Engineering Upgrade transfers existing skill ranks to variants.
        if skill==HeroSkill[22*4+2] and old<3 then
            -- Resolve destinations from their four-character IDs below.
            for _,pair in ipairs({{'ANsy','ANs'},{'ANcs','ANc'},{'ANrg','ANg'}}) do
                local function raw(t) local v=0;for i=1,#t do v=v*256+string.byte(t,i) end;return v end
                local from=old==0 and raw(pair[1]) or raw(pair[2]..old)
                local to=raw(pair[2]..(old+1))
                u.abilities[to]=u.abilities[from] or 0;u.abilities[from]=nil
            end
        end
    end
end
function GetRandomInt(low,high)
    local value=RngQueue and table.remove(RngQueue,1) or low
    assert(value>=low and value<=high,'Random choice uses full valid bounds')
    return value
end
function IssueImmediateOrderById(u,id)
    local config=EngineResearch[id]
    if not config or u.pending or u.hp<=0 then return false end
    local p=u.owner;local old=GetPlayerTechCount(p,id)
    local cost=config.base+config.step*old
    if old>=config.cap or Players[p].gold<cost then return false end
    Players[p].gold=Players[p].gold-cost
    u.pending=id
    return true
end
function FinishResearch(p)
    local id=Base[p].pending
    if not id then return end
    Base[p].pending=nil
    Players[p].tech[id]=GetPlayerTechCount(p,id)+1
    local old=Dying;Dying=Base[p];OnResearch();Dying=old
end
function purchase(p,kind)
    local result=Buy(p,kind)
    if result and kind<4 then FinishResearch(p) end
    return result
end
function GetUnitCurrentOrder(u) return 0 end
function CountUnitsInGroup(g) return #g end
function GroupAddUnit(g,u)
    for _,v in ipairs(g) do if v==u then return end end
    table.insert(g,u)
end
function FirstOfGroup(g) return g[1] end
function GroupRemoveUnit(g,u)
    for i,v in ipairs(g) do if v==u then table.remove(g,i); return end end
end
function IsUnitInGroup(u,g) for _,v in ipairs(g) do if v==u then return true end end; return false end
function GroupAddGroup(a,b) for _,u in ipairs(a) do table.insert(b,u) end end
function GroupClear(g) for i=#g,1,-1 do g[i]=nil end end
function GroupEnumUnitsOfPlayer(g,p)
    for i=#g,1,-1 do g[i]=nil end
    for _,u in ipairs(World) do if u.owner==p and not u.removed then table.insert(g,u) end end
end
function GroupEnumUnitsInRange(g,x,y,r)
    for i=#g,1,-1 do g[i]=nil end
    for _,u in ipairs(World) do
        if not u.removed and (u.x-x)^2+(u.y-y)^2<=r*r then table.insert(g,u) end
    end
end
function RemoveUnit(u) u.removed=true; u.hp=0 end
function GetTriggerUnit() return Dying end
function GetKillingUnit() return Killer end
function AddHeroXP(u,xp) u.xp=(u.xp or 0)+xp end
function ReviveHero(u,x,y) u.hp=u.max;u.x=x;u.y=y;u.revived=true; return true end
function DisplayTimedTextToPlayer() end
function DisplayTimedTextToForce() end
function DialogDisplay(p,d,v) if d then d.visible=v end end
function DialogClear(d) d.buttons={} end
function DialogSetMessage(d,s) d.title=s end
function DialogAddButton(d,s,key)
    local button={label=s}
    table.insert(d.buttons,button)
    assert(#d.buttons<=12,'Classic dialogs may not overflow their button capacity')
    return button
end
function GetTriggerPlayer() return EventPlayer or 0 end
function GetClickedButton() return Clicked end
function GetSpellAbilityId() return SpellId end
function CustomVictoryBJ(p) Players[p].victory=true end
function CustomDefeatBJ(p) Players[p].defeat=true end
-- The main clock test skips board rendering and tactical combat.
local realBotHero=BotHero
function UpdateBoard() end
function BotHero() end
function reset()
    Players,World,Work,Scan = {},{},{},{}
    Seconds,Finished = 0,false
    InitBalance()
    for t=0,3 do TeamLost[t]=false; Defending[t]=false; RallyX[t]=0;RallyY[t]=0 end
    for p=0,11 do
        Players[p]={gold=STARTING_GOLD,tech={}}
        Bot[p],Lost[p],AutoArmy[p]=false,false,true
        ArmyRace[p],HeroKind[p],CastUntil[p]=0,0,0
        Tier[p],Attack[p],Armor[p],Vitality[p],Power[p],SpawnClock[p],Respawn[p],Kills[p]=0,0,0,0,0,0,0,0
        Army[p]={}
        Shop[p]={buttons={}}
        Base[p]=CreateUnit(p,0,HomeX[p],HomeY[p],0);Base[p].structure=true;Base[p].hp=BASE_HP;Base[p].max=BASE_HP
        Hero[p]=CreateUnit(p,0,HomeX[p],HomeY[p]-240,0)
    end
end

reset()
for p=0,11 do assert(TeamOf(p)==math.floor(p/3)) end
assert(purchase(0,0)==true and Attack[0]==1 and Players[0].gold==STARTING_GOLD-ATTACK_COST)
Players[0].gold=0
assert(purchase(0,0)==false and Attack[0]==1 and Players[0].gold==0)
Players[0].gold=100000000
while Attack[0]<UPGRADE_MAX do assert(purchase(0,0)) end
local gold=Players[0].gold
assert(not purchase(0,0) and Players[0].gold==gold)
while Armor[0]<UPGRADE_MAX do assert(purchase(0,1)) end
while Vitality[0]<UPGRADE_MAX do assert(purchase(0,2)) end
assert(not purchase(0,1) and not purchase(0,2))
while Tier[0]<4 do assert(purchase(0,3)) end
assert(not purchase(0,3) and Tier[0]==4)
local strength=Hero[0].str
assert(purchase(0,4) and Hero[0].str==strength+3 and Power[0]==1)
Hero[0].hp=30
assert(purchase(0,5) and Hero[0].hp==Hero[0].max)
assert(not purchase(0,5))
Hero[0].hp=30;Hero[0].x=0;Hero[0].y=0
assert(not purchase(0,5),'No remote fountain purchase')
Base[0].hp=0;gold=Players[0].gold
assert(not purchase(0,0) and Players[0].gold==gold,'No purchases after barracks loss')

reset()
for p=0,11 do
    for wave=1,100 do SpawnWave(p) end
    assert(#Army[p]==ARMY_CAP,'Wave cap applies to every player')
    assert(Army[p][1].data==11,'New troops route through center')
    assert(Army[p][1].id==MeleeType[0] and Army[p][3].id==RangedType[0])
end
-- Killing a unit frees one cap slot, produces one reward, and permits a partial wave.
Dying,Killer=Army[3][1],Hero[0]
Dying.hp=0
local gold=Players[0].gold
OnDeath()
assert(#Army[3]==ARMY_CAP-1 and Players[0].gold==gold+8 and Kills[0]==1)
SpawnWave(3)
assert(#Army[3]==ARMY_CAP)
Dying,Killer=Army[1][1],Hero[0];Dying.hp=0;gold=Players[0].gold
OnDeath()
assert(Players[0].gold==gold,'Allied kills give no gold')

reset()
-- Only passive income is supplied: no bonus money for bots.
Bot[0]=true
local income=0
for second=1,18000 do
    AddGold(0,INCOME_PER_SECOND);income=income+INCOME_PER_SECOND
    if second%5==0 then BotBuy(0);FinishResearch(0) end
    assert(Players[0].gold>=0 and Players[0].gold<=STARTING_GOLD+income)
end
assert(Tier[0]==4 and Attack[0]>0 and Armor[0]>0 and Vitality[0]>0)
-- A large test-only budget verifies all 600 troop research ranks are reachable.
Players[0].gold=100000000
for n=1,1000 do BotBuy(0);FinishResearch(0) end
assert(Attack[0]==200 and Armor[0]==200 and Vitality[0]==200 and Power[0]==10)

reset()
-- A lost personal base does not eliminate the two allied players.
Base[0].hp=0;CheckTeam(0)
assert(not TeamLost[0] and not Lost[0] and Alive(Hero[0]))
Base[1].hp=0;Base[2].hp=0;CheckTeam(0)
assert(TeamLost[0] and Lost[0] and Lost[1] and Lost[2])
assert(Hero[0].removed and not Finished)
for p=3,8 do Base[p].hp=0 end
CheckTeam(1);CheckTeam(2)
assert(Finished and Players[9].victory and Players[11].victory and Players[0].defeat)

reset()
-- Warmup is exact; subsequent waves keep the configured interval.
for n=1,WARMUP_SECONDS-1 do Tick() end
assert(#Army[0]==0)
Tick();assert(#Army[0]==SPAWN_UNITS)
for n=1,SPAWN_SECONDS-1 do Tick() end
assert(#Army[0]==SPAWN_UNITS)
Tick();assert(#Army[0]==SPAWN_UNITS*2)
-- An owned living barracks revives heroes; destroyed ones never do.
Hero[0].hp=0;Respawn[0]=2
Tick();assert(Hero[0].hp==0)
Tick();assert(Hero[0].revived and Hero[0].hp==Hero[0].max)
Base[1].hp=0;Hero[1].hp=0;Respawn[1]=1
Tick();Tick();assert(not Hero[1].revived)

-- All races retain upgrades, prices and the two-melee/one-ranged wave layout.
for race=0,3 do
    reset()
    assert(SelectArmyRace(0,race))
    Players[0].gold=100000000
    assert(purchase(0,0) and purchase(0,1))
    for tier=0,4 do
        GroupClear(Army[0]);SpawnWave(0)
        assert(#Army[0]==SPAWN_UNITS)
        assert(Army[0][1].id==MeleeType[race*5+tier])
        assert(Army[0][3].id==RangedType[race*5+tier])
        assert(IsArmyUnit(Army[0][1]) and IsArmyUnit(Army[0][3]))
        if tier<4 then assert(purchase(0,3)) end
    end
    Seconds=WARMUP_SECONDS
    assert(not SelectArmyRace(0,(race+1)%4) and ArmyRace[0]==race)
end

reset()
-- Selection dialogs finish by focusing the barracks, without an upgrade dialog.
local function click(action)
    for k=0,11 do
        if MenuAction[k]==action and ShopButton[k] then Clicked=ShopButton[k];OnShop();return end
    end
    error('Missing menu action '..action)
end
ShowRaces(0);assert(#Shop[0].buttons==7)
click(102);assert(ArmyRace[0]==2)
click(204);assert(#Shop[0].buttons==11,'Eight neutral heroes plus navigation fit')
click(323);assert(HeroKind[0]==23 and Hero[0].id==HeroType[23])
assert(Players[0].selection==Base[0])
local gold=Players[0].gold
-- A human research-button click reaches the same finish event as a bot order.
assert(IssueImmediateOrderById(Base[0],ArmyResearch[0]))
assert(Attack[0]==0,'Research is not instant')
assert(Players[0].gold==gold-ATTACK_COST)
FinishResearch(0);assert(Attack[0]==1)
local oldHero=Hero[0]
Seconds=WARMUP_SECONDS
assert(not SelectRosterHero(0,0) and Hero[0]==oldHero)

-- Every roster hero is selectable. Every bot can draw both RNG endpoints and
-- all intervening choices, rather than using its player index as a hero class.
for kind=0,HERO_COUNT-1 do
    reset()
    assert(SelectRosterHero(0,kind))
    assert(Hero[0].id==HeroType[kind] and Hero[0].paused)
    Bot[1]=true;RngQueue={kind%4,kind}
    AssignBotChoices(1)
    assert(ArmyRace[1]==kind%4 and HeroKind[1]==kind and Hero[1].id==HeroType[kind])
    SetHeroLevel(Hero[1],100)
    for i=1,25 do LearnHero(1) end
    assert(Hero[1].points==33,'Hero level 100 spends 3x20 + 7 skill points')
    for slot=0,3 do
        assert(GetUnitAbilityLevel(Hero[1],ResolvedSkill(Hero[1],HeroSkill[kind*4+slot]))==(slot==3 and 7 or 20))
    end
    Seconds=WARMUP_SECONDS+10
    Hero[1].paused=false
    Hero[3].x=HomeX[1]+150;Hero[3].y=HomeY[1]
    AllowedOrders={}
    for slot=0,3 do AllowedOrders[SpellOrder[kind*4+slot]]=true end
    if AutoOrder[kind]~='' then AllowedOrders[AutoOrder[kind]]=true end
    realBotHero(1)
    assert(Hero[1].order,'Each of the 24 bot hero classes issues combat orders')
    if CastUntil[1]>Seconds then
        local order=Hero[1].order
        realBotHero(1)
        assert(Hero[1].order==order,'Do not interrupt a spell with skill/autocast orders')
    end
    AllowedOrders=nil
end

reset()
-- Generic casting uses this hero's learned skill, and waits for a channel.
Bot[0]=true;CreateHero(0,1)
local enemy=Hero[3];enemy.x=HomeX[0]+100;enemy.y=HomeY[0]
AllowedOrders={thunderbolt=true}
assert(TryBotSpell(0,enemy) and Hero[0].order[1]=='thunderbolt')
assert(CastUntil[0]>Seconds)
AllowedOrders=nil

reset()
-- Charm must remove a troop from its old owner's cap at reconciliation.
SpawnWave(0)
local charmed=Army[0][1];charmed.owner=3
CommandArmy(0,true);CommandArmy(3,true)
assert(#Army[0]==2 and IsUnitInGroup(charmed,Army[3]))

reset()
CreateHero(0,2);SetHeroLevel(Hero[0],100)
for n=1,25 do LearnHero(0) end
Summoner=Hero[0];Summoned=CreateUnit(0,0,0,0,0)
OnSummon()
assert(GetUnitAbilityLevel(Summoned,(string.byte("F")*16777216+string.byte("s")*65536+string.byte("H")*256+string.byte("P")))==18) -- FsHP, rank 18 for skill rank 20
