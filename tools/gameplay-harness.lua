-- Only the native API is substituted. All map functions come from shipped JASS.
-- Lua's string __add represents JASS string concatenation in the translator.
debug.setmetatable('', {__add=function(a,b) return tostring(a)..tostring(b) end})
UNIT_TYPE_DEAD, UNIT_TYPE_STRUCTURE = 'dead', 'structure'
UNIT_TYPE_SUMMONED = 'summoned'
UNIT_TYPE_UNDEAD, UNIT_TYPE_HERO = 'undead', 'hero'
UNIT_STATE_MAX_LIFE, UNIT_STATE_LIFE, UNIT_STATE_MANA, UNIT_STATE_MAX_MANA = 'max', 'hp', 'mana', 'maxmana'
PLAYER_STATE_RESOURCE_GOLD = 'gold'
Players, World = {}, {}
function FourCC(t) local v=0;for i=1,#t do v=v*256+string.byte(t,i) end;return v end
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
    local u={owner=p,id=id,x=x,y=y,hp=100,max=100,mana=100,maxmana=100,str=20,agi=20,int=20,level=1,data=0,abilities={},points=1,inventory={}}
    table.insert(World,u)
    return u
end
function IssuePointOrder(u,order,x,y) u.order={order,x,y}; return true end
function IssueImmediateOrder(u,order) u.order={order};return AllowedOrders and AllowedOrders[order] or false end
function IssueTargetOrder(u,order,target) u.order={order,target};return AllowedOrders and AllowedOrders[order] or false end
function UnitItemInSlot(u,slot) return u.inventory[slot] end
function UnitInventorySize(u) return 6 end
function GetItemTypeId(it) return it and it.id or 0 end
function IMinBJ(a,b) return math.min(a,b) end
function IMaxBJ(a,b) return math.max(a,b) end
function IssueNeutralTargetOrder(p,shop,order,h)
    assert(order=='neutralinteract')
    if h.owner~=p or (h.x-shop.x)^2+(h.y-shop.y)^2>600^2 then return false end
    shop.buyers=shop.buyers or {};shop.buyers[p]=h;return true
end
function IssueNeutralImmediateOrderById(p,shop,id)
    local h=shop.buyers and shop.buyers[p]
    if not h or not EngineShops[shop.id][id] or BlockStock then return false end
    local config=assert(EngineItems[id])
    if Players[p].gold<config.cost then return false end
    for slot=0,5 do
        if not h.inventory[slot] then
            Players[p].gold=Players[p].gold-config.cost
            h.inventory[slot]={id=id};return true
        end
    end
    return false
end
function UnitDropItemTarget(h,it,shop)
    if BlockSale or (h.x-shop.x)^2+(h.y-shop.y)^2>600^2 then return false end
    for slot=0,5 do if h.inventory[slot]==it then
        h.inventory[slot]=nil
        Players[h.owner].gold=Players[h.owner].gold+math.floor(EngineItems[it.id].cost/2)
        return true
    end end
    return false
end
function GetUnitAbilityLevel(u,id) return u.abilities[id] or 0 end
function UnitAddAbility(u,id) u.abilities[id]=1;return true end
function UnitMakeAbilityPermanent(u,v,id) return true end
function SetUnitAbilityLevel(u,id,rank) u.abilities[id]=rank;return rank end
function GetSummonedUnit() return Summoned end
function GetSummoningUnit() return Summoner end
function PauseUnit(u,v) u.paused=v end
function SetHeroLevel(u,level) u.points=u.points+level-u.level;u.level=level end
function UnitModifySkillPoints(u,delta) u.points=u.points+delta;return true end
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
function GetUnitCurrentOrder(u) return u.pending or 0 end
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
function GetTrainedUnit() return Trained end
function GetEventDamageSource() return DamageSource end
function GetEventDamage() return DamageAmount or 0 end
function IsUnitEnemy(u,p) return TeamOf(u.owner)~=TeamOf(p) end
function SetUnitInvulnerable(u,v) u.invulnerable=v end
function PanCameraToTimedForPlayer() end
function GetKillingUnit() return Killer end
function AddHeroXP(u,xp) u.xp=(u.xp or 0)+xp end
function ReviveHero(u,x,y) u.hp=u.max;u.x=x;u.y=y;u.revived=true; return true end
function GetLocalPlayer() return 0 end
function CreateTextTag() local tag={};table.insert(GoldTags,tag);return tag end
function SetTextTagText(t,v,size) t.text=v;t.size=size end
function SetTextTagPosUnit(t,u,h) t.unit=u end
function SetTextTagColor(t,r,g,b,a) t.color={r,g,b,a} end
function SetTextTagVelocity(t,x,y) t.vy=y end
function SetTextTagPermanent(t,v) t.permanent=v end
function SetTextTagLifespan(t,v) t.lifespan=v end
function SetTextTagFadepoint(t,v) t.fadepoint=v end
function SetTextTagVisibility(t,v) t.visible=v end
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
    HostPlayer,AllRandomMode,ModeDialogOpen=0,false,false
    GoldTags={}
    BlockStock,BlockSale=false,false
    InitBalance()
    for t=0,3 do TeamLost[t]=false; Defending[t]=false; RallyX[t]=0;RallyY[t]=0 end
    for shop=0,19 do
        local raw=function(t) local v=0;for i=1,#t do v=v*256+string.byte(t,i) end;return v end
        FortressShop[shop]=CreateUnit(15,raw("fs"..(shop%5).."p"),ShopX[shop],ShopY[shop],0);FortressShop[shop].structure=true
    end
    for p=0,11 do
        Players[p]={gold=STARTING_GOLD,tech={}}
        GearProgress[p],GearSavings[p]=0,0
        HeroPicker[p],PickerPage[p],BastionUntil[p]=nil,0,0
        SlotActive[p]=true
        Bot[p],Lost[p],AutoArmy[p]=false,false,true
        ArmyRace[p],HeroKind[p],CastUntil[p]=0,0,0
        Tier[p],Attack[p],Armor[p],Vitality[p],Power[p],SpawnClock[p],Respawn[p],Kills[p]=0,0,0,0,0,0,0,0
        Army[p]={}
        Shop[p]={buttons={}}
        Base[p]=CreateUnit(p,0,HomeX[p],HomeY[p],0);Base[p].structure=true;Base[p].hp=BASE_HP;Base[p].max=BASE_HP
        Hero[p]=CreateUnit(p,0,HomeX[p],HomeY[p]-240,0);SkillLevel[p]=1
        Bastion[p]=CreateUnit(p,0,BastionX[p],BastionY[p],0);Bastion[p].structure=true;Bastion[p].hp=60000;Bastion[p].max=60000;Bastion[p].paused=true
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
    assert(Army[p][1].id==ArmyType[0] and Army[p][3].id==ArmyType[0])
end
-- Killing a unit frees one cap slot, produces one reward, and permits a partial wave.
Dying,Killer=Army[3][1],Hero[0]
Hero[0].x=Dying.x;Hero[0].y=Dying.y
Dying.hp=0
local gold=Players[0].gold
OnDeath()
assert(#Army[3]==ARMY_CAP-1 and Players[0].gold==gold+8 and Kills[0]==1)
assert(Hero[0].xp==8,'Manual reward XP is reduced from 16 to 8 for an 8-gold kill')
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

-- All races retain upgrades, prices and the single-type wave layout.
for race=0,3 do
    reset()
    assert(SelectArmyRace(0,race))
    Players[0].gold=100000000
    assert(purchase(0,0) and purchase(0,1))
    for tier=0,4 do
        GroupClear(Army[0]);SpawnWave(0)
        assert(#Army[0]==SPAWN_UNITS)
        assert(Army[0][1].id==ArmyType[race*5+tier])
        assert(Army[0][3].id==ArmyType[race*5+tier])
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
assert(Players[0].selection==HeroPicker[0],'Race choice opens native portrait gallery')
ShowHeroGroups(0)
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
    SetHeroLevel(Hero[1],500)
    for i=1,310 do LearnHero(1) end
    assert(Hero[1].points==49,'500 levels grant 999 points; 3x300 + 50 are spent')
    for slot=0,3 do
        assert(GetUnitAbilityLevel(Hero[1],ResolvedSkill(Hero[1],HeroSkill[kind*4+slot]))==(slot==3 and 50 or 300))
    end
    Seconds=WARMUP_SECONDS+10
    Hero[1].paused=false
    Hero[3].x=HomeX[1]+150;Hero[3].y=HomeY[1]
    AllowedOrders={}
    for slot=0,3 do AllowedOrders[SpellOrder[kind*4+slot]]=true end
    if AutoOrder[kind]~='' then AllowedOrders[AutoOrder[kind]]=true end
    realBotHero(1)
    assert(Hero[1].order,'Each of the 28 bot hero classes issues combat orders')
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
-- A level event grants exactly one additional point per gained level to humans.
CreateHero(0,2)
SetHeroLevel(Hero[0],500);Dying=Hero[0];OnHeroLevel()
assert(Hero[0].points==999)
OnHeroLevel();assert(Hero[0].points==999,'Repeated events cannot duplicate points')
Dying=Hero[3];OnHeroLevel();assert(Hero[0].points==999)

-- Slow sanctuary regeneration applies only to allies inside their own circle.
reset()
local friend=Hero[0];friend.x=FortressX[0];friend.y=FortressY[0];friend.hp=50;friend.mana=40
local ally=Hero[1];ally.x=friend.x+100;ally.y=friend.y;ally.hp=50;ally.mana=40
local invader=Hero[3];invader.x=friend.x;invader.y=friend.y;invader.hp=50;invader.mana=40
local outside=Hero[2];outside.x=0;outside.y=0;outside.hp=50;outside.mana=40
Base[0].hp=1000
RegenerateFortresses()
assert(math.abs(friend.hp-50.15)<1e-6 and math.abs(friend.mana-40.1)<1e-6)
assert(math.abs(ally.hp-50.15)<1e-6)
assert(invader.hp==50 and invader.mana==40,'Enemies receive no regeneration')
assert(outside.hp==50 and Base[0].hp==1000,'Arena units and buildings receive no sanctuary regeneration')
friend.hp=100;friend.mana=100;RegenerateFortresses();assert(friend.hp==100 and friend.mana==100)

-- All hero classes build and upgrade six slots across all five fortress shops.
for kind=0,HERO_COUNT-1 do
    reset();Bot[0]=true;CreateHero(0,kind);Players[0].gold=100000000
    local first=DesiredGear(0);local target=GearShop[first]
    local gold=Players[0].gold
    assert(BotShop(0) and GearProgress[0]==0 and Players[0].gold==gold,'Travel before buying')
    for step=0,17 do
        local index=DesiredGear(0);local shop=GearShop[index]
        Hero[0].x=ShopX[shop];Hero[0].y=ShopY[shop]
        local before=Players[0].gold
        local refund=step>=6 and math.floor(EngineItems[GearId[index-1]].cost/2) or 0
        assert(BotShop(0) and GearProgress[0]==step+1,"Gear progress: hero "..kind.." step "..step)
        assert(Players[0].gold==before-GearCost[index]+refund,'Native full price and resale apply exactly once')
        assert(HeroItem(Hero[0],GearId[index]))
    end
    local count=0;for slot=0,5 do if UnitItemInSlot(Hero[0],slot) then count=count+1 end end
    assert(count==6 and not BotShop(0),'Six final items, no infinite duplicate buying')
end
reset();Bot[0]=true;Players[0].gold=100000
local index=DesiredGear(0);local shop=GearShop[index]
Hero[0].x=ShopX[shop];Hero[0].y=ShopY[shop]
BlockStock=true;BotShop(0);assert(GearProgress[0]==0 and Players[0].gold==100000,'No stock means no free item or charge')
BlockStock=false
for slot=0,5 do Hero[0].inventory[slot]={id=0} end
assert(not BotShop(0) and GearProgress[0]==0 and Players[0].gold==100000,'Full unrelated inventory is preserved')
reset();Bot[0]=true;AddGold(0,1000)
assert(math.floor(GearSavings[0])==333 and Players[0].gold==STARTING_GOLD+1000,'Equipment savings reserve real income; they do not create gold')

reset()
SpawnWave(3);Dying=Army[3][1];Killer=Hero[0];Dying.hp=0
local gold=Players[0].gold;OnDeath()
assert(Players[0].gold==gold+8 and #GoldTags==1)
assert(GoldTags[1].text=='+8' and GoldTags[1].visible and not GoldTags[1].permanent and GoldTags[1].lifespan==1.8)
SpawnWave(1);Dying=Army[1][1];Dying.hp=0;OnDeath();assert(#GoldTags==1,'Allied kills give neither gold nor floating reward')
Bot[0]=true;SpawnWave(3);Dying=Army[3][1];Dying.hp=0;OnDeath();assert(#GoldTags==1,'No cosmetic tag allocation for bot rewards')
Bot[0]=false;ShowGoldReward(1,Hero[3],10);assert(not GoldTags[2].visible,'Reward is private to its owning player')

reset()
-- Destroying a vulnerable bastion pays once, without destroying its barracks.
Dying=Bastion[3];Killer=Hero[0];Dying.hp=0
local gold=Players[0].gold;OnDeath()
assert(Players[0].gold==gold+250 and Alive(Base[3]) and not TeamLost[1])
for second=1,120 do Tick() end
assert(not Alive(Bastion[3]),'Bastions never respawn')


-- Gallery callbacks and page controls, including every custom hero.
for kind=0,HERO_COUNT-1 do
 reset();ShowHeroPicker(0,math.floor(kind/8))
 assert(PickerPage[0]==math.floor(kind/8) and Players[0].selection==HeroPicker[0])
 local picker=HeroPicker[0];Dying=picker
 Trained=CreateUnit(0,PickToken[kind],0,0,0);OnHeroPick()
 assert(Trained.removed and HeroKind[0]==kind and Hero[0].id==HeroType[kind])
 assert(Players[0].selection==Base[0],'Chosen hero returns focus to research barracks')
end
reset();ShowHeroPicker(0,0);local previous=HeroPicker[0]
Dying=previous;SpellId=FourCC('Fprv');OnPickerSpell()
assert(PickerPage[0]==3 and previous.removed,'Previous wraps to last page')
Dying=HeroPicker[0];SpellId=FourCC('Fnxt');OnPickerSpell();assert(PickerPage[0]==0)
Dying=HeroPicker[0];SpellId=FourCC('Frnd');RngQueue={27};OnPickerSpell();assert(HeroKind[0]==27)
Seconds=WARMUP_SECONDS-1;Tick();assert(HeroPicker[0]==nil,'Remove gallery before combat')

-- All Random is host-only, synchronized, available only in first 15 seconds.
reset();ShowHeroPicker(0,0);local oldPicker=HeroPicker[0]
SetAllRandom(1);assert(not AllRandomMode)
RngQueue={};for p=0,11 do table.insert(RngQueue,p%4);table.insert(RngQueue,(p%2==0) and 0 or HERO_COUNT-1) end
SetAllRandom(0);assert(AllRandomMode and oldPicker.removed)
for p=0,11 do assert(ArmyRace[p]==p%4 and HeroKind[p]==((p%2==0) and 0 or HERO_COUNT-1)) end
local chosen=Hero[0];assert(not SelectRosterHero(0,1) and Hero[0]==chosen);assert(not SelectArmyRace(0,1))
reset();Seconds=16;SetAllRandom(0);assert(not AllRandomMode)
reset();Power[5]=1;SetAllRandom(0);assert(not AllRandomMode,'Preserve paid hero stats')
reset();ShowModes(0);assert(ModeDialogOpen and #Shop[0].buttons==2)
Seconds=15;Tick();assert(not ModeDialogOpen and #Shop[0].buttons==7,'Unanswered mode defaults to normal')

-- Bastions defend attacked bases (and themselves), without firing on passersby.
reset();Seconds=70;Dying=Base[0];DamageSource=Hero[3];DamageAmount=1
OnBaseDefense();assert(not Bastion[0].paused and BastionUntil[0]==76 and Bastion[0].order[2]==Hero[3])
for n=1,6 do Tick() end
assert(Bastion[0].paused,'Tower goes idle six seconds after last hostile damage')
Dying=Bastion[0];OnBaseDefense();assert(not Bastion[0].paused,'Tower can defend itself')
Bastion[0].paused=true;DamageSource=Hero[1];OnBaseDefense();assert(Bastion[0].paused,'Friendly damage cannot wake tower')
DamageSource=Hero[3];DamageAmount=0;OnBaseDefense();assert(Bastion[0].paused)
Bastion[0].hp=0;DamageAmount=10;OnBaseDefense();assert(Bastion[0].hp==0,'No resurrection')

-- Bots prioritize affordable research despite an expensive desired item.
reset();Bot[0]=true;GearSavings[0]=200;Players[0].gold=500
BotBuy(0);assert(Base[0].pending==ArmyResearch[0] and Players[0].gold==400)
local budget=Players[0].gold;BotBuy(0);assert(Players[0].gold==budget,'No duplicate orders during research')
FinishResearch(0);BotBuy(0);FinishResearch(0);BotBuy(0);FinishResearch(0)
assert(Attack[0]==1 and Armor[0]==1 and Vitality[0]==1,'Bots develop all troop stats early')
reset();Bot[0]=true;Seconds=60;Tick();assert(Base[0].pending~=nil,'Research starts on next second, without five-second idle delay')


-- Execute the actual per-slot startup with human, computer, open and closed slots.
MAP_CONTROL_USER,MAP_CONTROL_COMPUTER='user','computer'
PLAYER_SLOT_STATE_PLAYING,PLAYER_SLOT_STATE_EMPTY,PLAYER_SLOT_STATE_LEFT='playing','empty','left'
PLAYER_STATE_RESOURCE_LUMBER,PLAYER_STATE_RESOURCE_FOOD_CAP='lumber','food'
PLAYER_STATE_GIVES_BOUNTY,PLAYER_STATE_FOOD_CAP_CEILING='bounty','ceiling'
function GetPlayerController(p) return Players[p].controller or MAP_CONTROL_USER end
function GetPlayerSlotState(p) return Players[p].slot or PLAYER_SLOT_STATE_PLAYING end
function SetPlayerController(p,c) Players[p].controller=c end
function SetPlayerName(p,n) Players[p].name=n end
function CreateGroup() return {} end
function DialogCreate() return {buttons={}} end
function SetPlayerAllianceStateAllyBJ() end
function SetPlayerAlliance() end
function CreateFogModifierRadius() return {} end
function FogModifierStart() end
function TriggerRegisterDialogEvent() end
function TriggerRegisterUnitEvent() end
function TriggerRegisterPlayerUnitEvent() end
function TriggerRegisterPlayerChatEvent() end
function TriggerRegisterPlayerEvent() end
function SetPlayerTechMaxAllowed() end
reset();HostPlayer=-1;World={}
for p=0,11 do
 Base[p],Hero[p],Bastion[p],Tower[p]=nil,nil,nil,nil
 Players[p].slot=PLAYER_SLOT_STATE_EMPTY
end
Players[2].slot=PLAYER_SLOT_STATE_PLAYING
Players[3].slot=PLAYER_SLOT_STATE_PLAYING;Players[3].controller=MAP_CONTROL_COMPUTER
Players[5].slot=PLAYER_SLOT_STATE_LEFT
Players[7].slot=PLAYER_SLOT_STATE_PLAYING
for p=0,11 do InitSlot(p) end
assert(HostPlayer==2,'First occupied human slot controls mode, not always red')
for p=0,11 do
 if p==2 or p==3 or p==7 then
  assert(SlotActive[p] and not Lost[p] and Alive(Base[p]) and Alive(Hero[p]) and Alive(Tower[p]) and Alive(Bastion[p]))
 else
  assert(not SlotActive[p] and Lost[p] and Base[p]==nil and Hero[p]==nil and Tower[p]==nil and Bastion[p]==nil)
 end
end
assert(Bot[3] and not Bot[2] and not Bot[0],'Only explicitly selected computer becomes a bot')
SetAllRandom(2);assert(AllRandomMode)
for _,u in ipairs(World) do assert(u.owner==2 or u.owner==3 or u.owner==7,'Random mode never creates units for empty slots') end
Seconds=WARMUP_SECONDS-1;Tick()
for p=0,11 do if not SlotActive[p] then assert(Base[p]==nil and Hero[p]==nil and #Army[p]==0) end end

reset();Dying=Base[0];DamageSource=Hero[3];DamageAmount=1;Seconds=70
OnBaseDefense();local order=Bastion[0].order
Seconds=71;DamageSource=Hero[4];OnBaseDefense()
assert(Bastion[0].order==order and BastionUntil[0]==77,'Rapid hits extend defense without resetting tower attacks')
reset();Seconds=0;Tick();assert(ModeDialogOpen and #Shop[0].buttons==2,'Host sees mode choice at match start')

-- Full startup also excludes wholly empty teams from victory accounting.
PLAYER_NEUTRAL_PASSIVE=15
function CreateTrigger() return {events={},actions={}} end
function TriggerAddAction(t,f) table.insert(t.actions,f) end
function CreateTimer() return {} end
function TimerStart(t,period,repeats,callback) t.callback=callback;Clock=t end
function CreateDestructable() return {} end
function CreateMultiboard() return {} end
function MultiboardGetItem() return {} end
function CreateQuest() return {} end
for _,name in ipairs({'SetDestructableInvulnerable','SetTimeOfDay','SetTimeOfDayScale','SetMapFlag','FogMaskEnable','FogEnable','MultiboardSetRowCount','MultiboardSetColumnCount','MultiboardSetItemsStyle','MultiboardSetItemsWidth','MultiboardSetItemWidth','MultiboardReleaseItem','MultiboardSetItemValue','MultiboardDisplay','QuestSetTitle','QuestSetDescription','QuestSetRequired','QuestSetDiscovered'}) do _G[name]=function() end end
reset();HostPlayer=-1;World={}
for p=0,11 do
 Base[p],Hero[p],Bastion[p],Tower[p]=nil,nil,nil,nil
 Players[p].slot=PLAYER_SLOT_STATE_EMPTY
end
Players[2].slot=PLAYER_SLOT_STATE_PLAYING
Players[3].slot=PLAYER_SLOT_STATE_PLAYING;Players[3].controller=MAP_CONTROL_COMPUTER
Players[7].slot=PLAYER_SLOT_STATE_PLAYING
InitGame()
assert(HostPlayer==2 and TeamLost[3] and not TeamLost[0] and not TeamLost[1] and not TeamLost[2])
assert(Clock.callback==Tick and #BaseDefenseTrigger.actions==1 and #PickerTrainTrigger.actions==1)
for _,u in ipairs(World) do assert(u.owner==15 or u.owner==2 or u.owner==3 or u.owner==7,'No private buildings in free slots after actual InitGame') end
Dying=Base[7];Killer=Hero[2];Dying.hp=0;OnDeath();assert(TeamLost[2] and not Finished)
Dying=Base[3];Dying.hp=0;OnDeath();assert(TeamLost[1] and Finished and Players[2].victory)
for p=0,11 do if not SlotActive[p] then assert(not Players[p].victory and not Players[p].defeat,'No outcome UI for unoccupied slots') end end
