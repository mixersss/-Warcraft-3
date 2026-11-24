local combine_menus = {}

local function bag_gems(role)
    local capacity = GetKbCap(role)
    local by_id, seen = {}, {}
    if type(capacity)~="number" or capacity<1 or capacity>256 then return by_id end
    for slot=0,capacity-1 do
        local item=GetChaItem(role,2,slot)
        local id=identify(item)
        local kind=id>0 and GetItemType(item)
        if kind==49 or kind==50 then
            local rank=Get_StoneLv(item)
            seen[id]=(seen[id] or 0)+1
            if rank and rank>=1 and rank<=8 and rank==math.floor(rank) then
                if not by_id[id] then by_id[id]={{},{},{},{},{},{},{},{},{}} end
                table.insert(by_id[id][rank],{slot=slot, rank=rank, count=1, key=slot..":"..rank})
            end
        end
    end
    -- A pair spends one whole bag slot. Refuse any items of the same ID
    -- if the engine reports stacked entries instead of single gemstones.
    for id in pairs(by_id) do
        if CheckBagItem(role,id)~=seen[id] then by_id[id]=nil end
    end
    return by_id
end

local function best_combination(ranks)
    local best
    for level=1,8 do
        local queue=ranks[level]
        table.sort(queue,function(a,b)
            if a.count~=b.count then return a.count<b.count end
            return a.slot<b.slot
        end)
        for index=1,table.getn(queue)-1,2 do
            local left,right=queue[index],queue[index+1]
            local node={left=left,right=right,slot=left.slot,rank=level+1,
                        count=left.count+right.count,key=left.key..","..right.key}
            if index==1 then best=node end
            table.insert(ranks[level+1],node)
        end
    end
    return best
end

local function combinations(role)
    local result={}
    for id,ranks in pairs(bag_gems(role)) do
        result[id]=best_combination(ranks)
    end
    return result
end

local function show_combinations(role,npc,actor,now,start)
    local plans, ids = combinations(role), {}
    for id in pairs(plans) do table.insert(ids,id) end
    table.sort(ids)
    if table.getn(ids)==0 then
        combine_menus[actor]=nil
        return notice(role,npc,"Нужны два обычных гема одного вида и одинакового ранга.")
    end
    if start>table.getn(ids) then start=1 end
    local options, visible = {"Назад","Следующие виды"}, {}
    for i=start,math.min(start+5,table.getn(ids)) do
        local id=ids[i]
        table.insert(visible,id)
        table.insert(options,GetItemName(id).." -> ур. "..plans[id].rank)
    end
    combine_menus[actor]={ids=visible,next=start+6,expires=now+60}
    SendMissionPage(role,npc,4,"Выбери гем. Кузница использует минимум камней для максимального ранга.",
                    options,table.getn(options),nil,0)
    return LUA_TRUE
end

local function combination_preview(role,npc,actor,action,now)
    local menu=combine_menus[actor]
    if not menu or menu.expires<now then return notice(role,npc,"Открой список гемов заново.") end
    local id=menu.ids[action-19]
    if not id then return LUA_FALSE end
    local plan=combinations(role)[id]
    if not plan then return notice(role,npc,"Гемы изменились. Открой список заново.") end
    pending[actor]={combination=id,key=plan.key,rank=plan.rank,expires=now+60}
    return notice(role,npc,GetItemName(id)..": нужно "..plan.count..
        " шт. из рюкзака. Результат — один гем "..plan.rank.." ранга. Остальные остаются.",true)
end

local function verify_stone(role,slot,id,rank)
    local item=GetChaItem(role,2,slot)
    if identify(item)==id and Get_StoneLv(item)==rank then return item end
end

local function execute_combination(role,id,node,progress)
    if not node.left then return verify_stone(role,node.slot,id,node.rank)~=nil end
    if not execute_combination(role,id,node.left,progress)
        or not execute_combination(role,id,node.right,progress) then return false end
    local previous=node.rank-1
    local receiver=verify_stone(role,node.slot,id,previous)
    if not receiver or not verify_stone(role,node.right.slot,id,previous) then return false end
    pcall(Set_StoneLv,receiver,node.rank)
    if not verify_stone(role,node.slot,id,node.rank) then return false end
    local before=CheckBagItem(role,id)
    pcall(RemoveChaItem,role,id,1,2,node.right.slot,2,1,0)
    local removed=before-CheckBagItem(role,id)
    if removed==0 then
        pcall(Set_StoneLv,receiver,previous)
        if not verify_stone(role,node.slot,id,previous) then
            unavailable=true
            LG("OwnerPersonalForge","Combination rollback failed, item "..id)
        end
        return false
    end
    if removed~=1 or identify(GetChaItem(role,2,node.right.slot))==id
            or not verify_stone(role,node.slot,id,node.rank) then
        unavailable=true
        LG("OwnerPersonalForge","Combination write not confirmed, item "..id.." debit "..removed)
        return false
    end
    progress.done=progress.done+1
    return true
end

local function confirm_combination(role,npc,quote)
    local id=quote.combination
    local plan=combinations(role)[id]
    if not plan or plan.rank~=quote.rank or plan.key~=quote.key then
        return notice(role,npc,"Гемы изменились. Открой список заново.")
    end
    local progress={done=0}
    local ok=execute_combination(role,id,plan,progress)
    sync(role)
    if not ok then
        return notice(role,npc,"Операция остановлена. Завершено пар: "..progress.done..". Проверь рюкзак.")
    end
    SendMissionPage(role,npc,3,"Готово. "..GetItemName(id).." теперь "..plan.rank.." ранга.",
                    {"Назад"},1,nil,0)
    return LUA_TRUE
end
