-- Additional native ground loot. One independent 3/100 roll per real mob death.
-- No use of MF_RAID, character luck, normal drop lists or player inventories.
Owner56GemIDs={860,861,862,863,864,865,866,1012}
Owner56GemStats=Owner56GemStats or {kills=0,rolls=0,ground=0,failures=0}
Owner56GemSlots={}
Owner56MonsterModels=nil
function Owner56ReadGemSlots()
    if type(GetResPath)~="function" then return end
    local stream=io.open(GetResPath("CharacterInfo.txt"),"rb")
    if not stream then error("Owner56: CharacterInfo.txt is required for exact 3 percent gem loot") end
    local iterate=string.gmatch or string.gfind
    Owner56MonsterModels={}
    local allowed={}
    for _,id in ipairs(Owner56GemIDs) do allowed[id]=true end
    for line in stream:lines() do
        local fields={}
        for field in iterate(line.."\t","(.-)\t") do table.insert(fields,field) end
        local model=tonumber(fields[1])
        if model and fields[47] then
            if tonumber(fields[5])==5 then Owner56MonsterModels[model]=true end
            local slots={};local index=0
            for field in iterate(fields[47]..",","(.-),") do
                index=index+1
                if allowed[tonumber(field)] then slots[index]=true end
            end
            if next(slots) then Owner56GemSlots[model]=slots end
        end
    end
    stream:close()
end
Owner56ReadGemSlots()

-- The original monster list must not add another multiplier-scaled chance for
-- these eight gems. Filter only their original NORMAL drop indices; keep every
-- other ordinary item and the separate mission-loot pass byte-for-byte in effect.
if Owner56OriginalSetFall==nil then Owner56OriginalSetFall=SetItemFall end
if type(Owner56OriginalSetFall)=="function" then
    function SetItemFall(count,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10)
        local values={a1,a2,a3,a4,a5,a6,a7,a8,a9,a10}
        if not Owner56FallFilter then return Owner56OriginalSetFall(count,unpack(values)) end
        local kept={};local kept_count=0
        for index=1,count do
            if not Owner56FallFilter[values[index]] then kept_count=kept_count+1;kept[kept_count]=values[index] end
        end
        return Owner56OriginalSetFall(kept_count,unpack(kept))
    end
end
if Owner56OriginalDropCheck==nil then Owner56OriginalDropCheck=Check_Baoliao end
if type(Owner56OriginalDropCheck)=="function" then
    function Check_Baoliao(attacker,dead,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10)
        local filter=nil
        if Owner56PendingLoot==dead then
            Owner56PendingLoot=nil
            filter=Owner56GemSlots[GetChaTypeID(dead)]
        end
        Owner56FallFilter=filter
        local args={a1,a2,a3,a4,a5,a6,a7,a8,a9,a10}
        local values={pcall(Owner56OriginalDropCheck,attacker,dead,unpack(args))}
        Owner56FallFilter=nil
        if not values[1] then error(values[2]) end
    end
end

function Owner56GroundGem(dead,attacker)
    if IsPlayer(dead)~=0 or IsPlayer(attacker)~=1 or GetChaAttr(dead,ATTR_HP)>0 then return end
    if Owner56MonsterModels and not Owner56MonsterModels[GetChaTypeID(dead)] then return end
    Owner56GemStats.kills=Owner56GemStats.kills+1
    if math.random(1,100)>3 then return end
    Owner56GemStats.rolls=Owner56GemStats.rolls+1
    local identity=Owner56GemIDs[math.random(1,8)]
    local capacity=GetKbCap(dead)
    if type(capacity)~="number" or capacity<0 or capacity>48 or CheckBagItem(dead,identity)~=0 then
        Owner56GemStats.failures=Owner56GemStats.failures+1
        LG("owner56_gems","Unsupported monster inventory; ground drop was not created.")
        return
    end
    local free=0
    for slot=0,capacity-1 do
        local item=GetChaItem(dead,2,slot)
        if item==nil or item==0 then free=free+1 end
    end
    -- Classic GiveItem -> CCharacter::GiveItem -> KbPushItem: overflow is
    -- ItemSpawn at the receiver's position. Receiver is the DEAD MONSTER.
    -- Fill only its free slots with temporary unstackable copies, overflow
    -- exactly one real ground item, then remove all temporary bag copies.
    -- Existing corpse inventory and every player's inventory remain untouched.
    Owner56CreatingGroundGem=identity
    local ok,result=pcall(GiveItem,dead,0,identity,free+1,MONSTER_BAOLIAO)
    Owner56CreatingGroundGem=nil
    local inserted=CheckBagItem(dead,identity)
    if inserted>0 then TakeItem(dead,0,identity,inserted) end
    if ok and result==LUA_TRUE and inserted==free and CheckBagItem(dead,identity)==0 then
        Owner56GemStats.ground=Owner56GemStats.ground+1
    else
        Owner56GemStats.failures=Owner56GemStats.failures+1
        LG("owner56_gems","Native ground-loot operation was not confirmed; inspect GameServer.")
    end
end

if Owner56OriginalCreateItem==nil then Owner56OriginalCreateItem=Creat_Item end
if type(Owner56OriginalCreateItem)=="function" then
    function Creat_Item(item,kind,level,event)
        local values={Owner56OriginalCreateItem(item,kind,level,event)}
        if Owner56CreatingGroundGem==GetItemID(item) and kind==49 then
            local result={0}
            for index=1,values[1] do
                local id=values[index*2]
                if id~=ITEMATTR_MAXENERGY then
                    result[1]=result[1]+1
                    result[result[1]*2]=id
                    result[result[1]*2+1]=values[index*2+1]
                end
            end
            for index=result[1]*2+2,15 do result[index]=0 end
            Set_StoneLv(item,1)
            return unpack(result)
        end
        return unpack(values)
    end
end
if Owner56OriginalGetExp==nil then Owner56OriginalGetExp=GetExp_New end
if type(Owner56OriginalGetExp)=="function" then
    function GetExp_New(dead,attacker)
        Owner56OriginalGetExp(dead,attacker)
        Owner56PendingLoot=dead
        local ok,message=pcall(Owner56GroundGem,dead,attacker)
        if not ok then
            Owner56GemStats.failures=Owner56GemStats.failures+1
            LG("owner56_gems",tostring(message))
        end
    end
end
