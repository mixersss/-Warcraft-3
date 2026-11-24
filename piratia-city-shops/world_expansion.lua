-- WORLD_EXPANSION_BEGIN
local ground_stones = {860,861,862,863,864,865,866,1012}
ForgeGroundStacks = {}
ForgeLegacyItems = {}
for offset=0,29 do ForgeLegacyItems[6410+offset]=5618+offset end
for offset,id in ipairs(ground_stones) do
    ForgeGroundStacks[5608+offset]=id
    ForgeGroundStacks[6399+offset]=id
    ForgeLegacyItems[6399+offset]=5608+offset
end

local function supply_page(weapons, armour, goods, key)
    return {tp=TRADE_NOMAL, berth=-1, owner_native_shop=key,
            [1]={itemtype=0,count=table.getn(weapons),item=weapons,price={}},
            [2]={itemtype=1,count=table.getn(armour),item=armour,price={}},
            [3]={itemtype=2,count=table.getn(goods),item=goods,price={}},
            [4]={itemtype=3,count=0,item={},price={}}}
end

OwnerNativeShops["forge-supply"] = {pages={
    supply_page({},{},{1847,1848,1849,1854,1855,1856,1857,1858,1859,893,894,895,896,897,3094},"forge-supply"),
    supply_page({},{},{4602,4603,4604},"forge-supply")
}}
function ForgeSupply()
    Talk(1,"Forge Supply")
    Trade=OwnerNativeShops["forge-supply"].pages[1]
    Text(1,"Food, healing and boosts",OwnerOpenTrade,"forge-supply",1)
    Text(1,"Teleport tickets",OwnerOpenTrade,"forge-supply",2)
    Text(1,"Close",CloseTalk)
end

local equipment = OwnerNativeShops["equipment"].pages
local weapon_page = table.getn(equipment)+1
equipment[weapon_page] = supply_page(
    {2331,2332,2333,2334,2335,2336,2337,2338,2339,2340,2341,2342,2343,2344},
    {},{},"equipment")
local prior_equipment=OwnerEquipment
function OwnerEquipment()
    prior_equipment()
    Text(1,"Abaddon weapons Lv75",OwnerOpenTrade,"equipment",weapon_page)
end

-- Reuse the installed drop hook and the ordinary monster/owner guards.
function Owner56GroundGem(dead, attacker)
    if IsPlayer(dead)~=0 or IsPlayer(attacker)~=1 or GetChaAttr(dead,ATTR_HP)>0 then return end
    if Owner56MonsterModels and not Owner56MonsterModels[GetChaTypeID(dead)] then return end
    Owner56GemStats.kills=Owner56GemStats.kills+1
    Owner57GroundDrop(dead,1000,99)
    local level = GetChaAttr(dead,ATTR_LV)
    if level >= 10 and level <= 309 then
        Owner57GroundDrop(dead,5618+math.floor(level/10)-1,99)
    end
    if math.random(1,100)>3 then return end
    Owner56GemStats.rolls=Owner56GemStats.rolls+1
    Owner57GroundDrop(dead,5608+math.random(1,8),99)
end

-- Remove only cosmetic junk explicitly audited for this item set.
local junk = {[1218]=true,[1573]=true,[1574]=true,[1575]=true,[1579]=true}
local source = type(GetResPath)=="function" and io.open(GetResPath("CharacterInfo.txt"),"rb")
if source then
    local iterate=string.gmatch or string.gfind
    for line in source:lines() do
        local columns={}
        for field in iterate(line.."\t","(.-)\t") do table.insert(columns,field) end
        local model=tonumber(columns[1])
        if model and tonumber(columns[5])==5 and columns[47] then
            local index=0
            for field in iterate(columns[47]..",","(.-),") do
                index=index+1
                if junk[tonumber(field)] then
                    Owner56GemSlots[model]=Owner56GemSlots[model] or {}
                    Owner56GemSlots[model][index]=true
                end
            end
        end
    end
    source:close()
end

-- The engine can call ordinary loot before the EXP callback. Scope the
-- mask to the current monster directly, leaving mission and PvP loot separate.
if type(Owner56OriginalDropCheck)=="function" then
    function Check_Baoliao(attacker,defender,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10)
        local previous=Owner56FallFilter
        local model=GetChaTypeID(defender)
        Owner56FallFilter=nil
        if IsPlayer(defender)==0 and Owner56MonsterModels and Owner56MonsterModels[model] then
            Owner56FallFilter=Owner56GemSlots[model]
        end
        local args={a1,a2,a3,a4,a5,a6,a7,a8,a9,a10}
        local status,message=pcall(Owner56OriginalDropCheck,attacker,defender,unpack(args))
        Owner56FallFilter=previous
        if not status then error(message) end
    end
end
-- WORLD_EXPANSION_END
