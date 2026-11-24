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
-- SUPPLY_STOCK
}}
function ForgeSupply()
    Talk(1,"Cooking and Manufacturing")
    Trade=OwnerNativeShops["forge-supply"].pages[1]
-- SUPPLY_OPTIONS
    Text(1,"Close",CloseTalk)
end

-- Native purchase initializes equipment produced by the manufacturing recipe.
local craft_tools={[1067]=true,[1068]=true,[1069]=true,[1070]=true,[2236]=true}
local prior_native_buy=OwnerNativeBuy
local prior_create=Creat_Item
local tool_purchase
if type(prior_native_buy)=="function" and type(prior_create)=="function" then
    function OwnerNativeBuy(character,npc,trade,itemtype,index1,index2,count)
        local selected=OwnerNativeSelection[character]
        local page=selected and OwnerNativeShops["forge-supply"].pages[selected.page]
        local identity
        if trade.owner_native_shop=="forge-supply" and itemtype==2 and type(index1)=="number" and page then
            identity=page[3].item[index1+1]
        end
        if not craft_tools[identity] then return prior_native_buy(character,npc,trade,itemtype,index1,index2,count) end
        local previous=tool_purchase
        tool_purchase=identity
        local ok,result=pcall(prior_native_buy,character,npc,trade,itemtype,index1,index2,count)
        tool_purchase=previous
        if not ok then error(result) end
        return result
    end
    function Creat_Item(item,kind,level,event)
        local attrs={prior_create(item,kind,level,event)}
        if tool_purchase and event==NPC_SALE and GetItemID(item)==tool_purchase then
            SetItemAttr(item,ITEMATTR_VAL_STR,tool_purchase==2236 and 20 or 1)
            if tool_purchase~=2236 then
                SetItemAttr(item,ITEMATTR_MAXENERGY,10000)
                SetItemAttr(item,ITEMATTR_ENERGY,1)
            end
        end
        return unpack(attrs)
    end
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

local masks={}
local function level_trophy(level)
    if level and level>=10 and level<=309 then return 5618+math.floor(level/10)-1 end
end

-- The older ground mechanism is a fallback for full monster tables.
function Owner56GroundGem(dead, attacker)
    if IsPlayer(dead)~=0 or IsPlayer(attacker)~=1 or GetChaAttr(dead,ATTR_HP)>0 then return end
    if Owner56MonsterModels and not Owner56MonsterModels[GetChaTypeID(dead)] then return end
    Owner56GemStats.kills=Owner56GemStats.kills+1
    Owner57GroundDrop(dead,1000,99)
    local model=GetChaTypeID(dead)
    local trophy=level_trophy(GetChaAttr(dead,ATTR_LV))
    if trophy and not (masks[model] and masks[model].trophy) then
        Owner57GroundDrop(dead,trophy,99)
    end
    if math.random(1,100)>3 then return end
    Owner56GemStats.rolls=Owner56GemStats.rolls+1
    Owner57GroundDrop(dead,ground_stones[math.random(1,8)],1)
end

-- Ordinary drops use indices into the compact positive ID/rate list.
-- Mission drops are evaluated separately by the engine.
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
                local entry={mask={},rates={}}
                local trophy=level_trophy(tonumber(columns[61]))
                for index,field in ipairs(ids) do
                    local id,rate=tonumber(field),tonumber(rates[index])
                    if id and id>0 and rate and rate>0 then
                        table.insert(entry.rates,rate)
                        local slot=table.getn(entry.rates)
                        if id==trophy then entry.trophy=slot
                        elseif not keep_drop(id,kinds[id]) then entry.mask[slot]=true end
                    end
                end
                if next(entry.mask) or entry.trophy then masks[model]=entry end
            end
        end
    elseif type(LG)=="function" then
        LG("owner90_loot","Ordinary loot filter needs ItemInfo.txt and CharacterInfo.txt.")
    end
    if items then items:close() end
    if characters then characters:close() end
end

local active
local prior_fall=SetItemFall
if type(prior_fall)=="function" then
    function SetItemFall(count,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10)
        local slots={a1,a2,a3,a4,a5,a6,a7,a8,a9,a10}
        if not active then return prior_fall(count,unpack(slots)) end
        local kept={}
        for i=1,count do
            if slots[i]~=active.slot then table.insert(kept,slots[i]) end
        end
        if active.award then table.insert(kept,active.slot) end
        active.emitted=true
        return prior_fall(table.getn(kept),unpack(kept))
    end
end

if type(Owner56OriginalDropCheck)=="function" then
    local logged={}
    function Check_Baoliao(attacker,defender,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10)
        local previous,previous_active=Owner56FallFilter,active
        Owner56FallFilter,active=nil,nil
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
                    if entry.trophy and type(prior_fall)=="function" then
                        active={slot=entry.trophy,award=IsPlayer(attacker)==1}
                    end
                elseif not logged[model] then
                    logged[model]=true
                    if type(LG)=="function" then LG("owner90_loot","Drop table mismatch for monster "..model) end
                end
            end
        end
        local status,message=pcall(Owner56OriginalDropCheck,attacker,defender,unpack(args))
        if status and active and active.award and not active.emitted then
            status,message=pcall(SetItemFall,0)
        end
        Owner56FallFilter,active=previous,previous_active
        if not status then error(message) end
    end
end
-- WORLD_EXPANSION_END
