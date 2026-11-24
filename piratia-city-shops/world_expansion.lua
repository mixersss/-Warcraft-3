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
    Owner57GroundDrop(dead,ground_stones[math.random(1,8)],1)
end

-- Ordinary drops use indices into the compact positive ID/rate list.
-- Mission drops are evaluated separately by the engine.
local masks={}
local replaced={[1000]=true}
for _,id in ipairs(ground_stones) do replaced[id]=true end
local iterate=string.gmatch or string.gfind
local function fields(line, delimiter)
    local values={}
    for field in iterate(line..delimiter,"(.-)"..delimiter) do table.insert(values,field) end
    return values
end

-- Audited valuable original drops and two dungeon passes.
local retained={[684]=true,[938]=true,[2374]=true,[2843]=true,[2844]=true,[3141]=true,[4915]=true}
local function keep_drop(id, kind)
    if replaced[id] then return false end -- supplied by Owner56GroundGem
    if ForgeGroundStacks[id] then return false end -- retire old ground aliases
    if retained[id] or (id>=2461 and id<=2487) or (id>=5618 and id<=5647)
            or (id>=6410 and id<=6439) then return true end
    if not kind then return true end -- a custom item absent from the text table
    return (kind>=1 and kind<=11) or (kind>=18 and kind<=27) or kind==29
           or kind==44 or kind==49 or kind==50
end

if type(GetResPath)=="function" then
    local items=io.open(GetResPath("ItemInfo.txt"),"rb")
    local characters=io.open(GetResPath("CharacterInfo.txt"),"rb")
    if items and characters then
        local kinds={}
        for line in items:lines() do
            local columns=fields(line,"\t")
            local id=tonumber(columns[1])
            if id then kinds[id]=tonumber(columns[11]) end
        end
        for line in characters:lines() do
            local columns=fields(line,"\t")
            local model=tonumber(columns[1])
            if model and tonumber(columns[5])==5 and columns[47] and columns[48] then
                local ids,rates=fields(columns[47],","),fields(columns[48],",")
                local mask,expected={},{}
                for index,field in ipairs(ids) do
                    local id,rate=tonumber(field),tonumber(rates[index])
                    if id and id>0 and rate and rate>0 then
                        table.insert(expected,rate)
                        if not keep_drop(id,kinds[id]) then mask[table.getn(expected)]=true end
                    end
                end
                if next(mask) then masks[model]={mask=mask,rates=expected} end
            end
        end
    elseif type(LG)=="function" then
        LG("owner90_loot","Ordinary loot filter needs ItemInfo.txt and CharacterInfo.txt.")
    end
    if items then items:close() end
    if characters then characters:close() end
end

if type(Owner56OriginalDropCheck)=="function" then
    local logged={}
    function Check_Baoliao(attacker,defender,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10)
        local previous=Owner56FallFilter
        Owner56FallFilter=nil
        local args={a1,a2,a3,a4,a5,a6,a7,a8,a9,a10}
        if IsPlayer(defender)==0 then
            local model=GetChaTypeID(defender)
            local entry=masks[model]
            if entry then
                local match=table.getn(entry.rates)==table.getn(args)
                for index,rate in ipairs(entry.rates) do
                    if args[index]~=rate then match=false; break end
                end
                if match then
                    Owner56FallFilter=entry.mask
                elseif not logged[model] then
                    logged[model]=true
                    if type(LG)=="function" then LG("owner90_loot","Drop table mismatch for monster "..model) end
                end
            end
        end
        local status,message=pcall(Owner56OriginalDropCheck,attacker,defender,unpack(args))
        Owner56FallFilter=previous
        if not status then error(message) end
    end
end
-- WORLD_EXPANSION_END
