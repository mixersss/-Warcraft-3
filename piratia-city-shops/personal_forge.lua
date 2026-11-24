-- OWNER_PERSONAL_FORGE_BEGIN
local pending = {}
local unavailable

local function notice(role, npc, message, confirmation)
    if confirmation then
        SendMissionPage(role, npc, 2, message, {"Подтвердить", "Назад"}, 2, nil, 0)
        return LUA_TRUE
    end
    SendMissionPage(role, npc, 3, message, {"Назад"}, 1, nil, 0)
    return LUA_FALSE
end

local function identify(item)
    if item == nil or item == 0 then return 0 end
    return GetItemID(item) or 0
end

local function packed(item)
    return TansferNum(GetItemForgeParam(item, 1))
end

local function snapshot(item)
    local attrs = {}
    for index = 1, 47 do attrs[index] = GetItemAttr(item, index) end
    return {id = identify(item), forge = packed(item), attrs = attrs}
end

local function unchanged(item, before)
    if identify(item) ~= before.id or packed(item) ~= before.forge then return false end
    for index = 1, 47 do
        if GetItemAttr(item, index) ~= before.attrs[index] then return false end
    end
    return true
end

local function put_forge(item, value)
    SetItemForgeParam(item, 1, value >= 2147483648 and value - 4294967296 or value)
    return packed(item) == value
end

local function put_attr(item, key, value)
    SetItemAttr(item, key, value)
    return GetItemAttr(item, key) == value
end

local function restore(item, before)
    for index = 1, 47 do
        if GetItemAttr(item, index) ~= before.attrs[index] then
            SetItemAttr(item, index, before.attrs[index])
        end
    end
    put_forge(item, before.forge)
    check_item_final_data(item)
    return unchanged(item, before)
end

local function sync(role)
    SetChaKitbagChange(role, 1)
    SynChaKitbag(role, 13)
end

local function equipment(kind)
    return (kind >= 1 and kind <= 11) or (kind >= 20 and kind <= 24) or kind == 27
end

local function can_pay_raw(role, identity, count)
    local seen = 0
    for slot = 1, 47 do
        local item = GetChaItem(role, 2, slot)
        if identify(item) == identity then
            if Get_StoneLv(item) ~= 1 then return false end
            seen = seen + 1
        end
    end
    return seen >= count and CheckBagItem(role, identity) == seen
end

local function migration_plan(role)
    for slot=2,3 do
        local item=GetChaItem(role,2,slot)
        local old=identify(item)
        local new=ForgeLegacyItems and ForgeLegacyItems[old]
        if new then
            local count=CheckBagItem(role,old)
            if count<=0 or GetChaFreeBagGridNum(role)<math.ceil(count/99) then
                return nil, "Освободи в рюкзаке место для переноса."
            end
            return {item=item, old=old, new=new, count=count, slot=slot},
                "Перенос всех "..count.." шт. одного вида из старой таблицы. Количество и вид сохранятся."
        end
    end
    return nil, "Положи старые стопки в ячейку 3 или 4."
end

local function migrate(role,npc,quote)
    local plan,message=migration_plan(role)
    if not plan or plan.old~=quote.old or plan.count~=quote.count
            or plan.slot~=quote.slot or not unchanged(plan.item,quote.item) then
        return notice(role,npc,message or "Стопки изменились. Проверь перенос заново.")
    end
    local initial=CheckBagItem(role,plan.new)
    -- Space was verified above so GiveItem cannot spill onto the ground.
    pcall(GiveItem,role,0,plan.new,plan.count,101)
    local gained=CheckBagItem(role,plan.new)-initial
    local removed=0
    if gained==plan.count then
        pcall(DelBagItem,role,plan.old,plan.count)
        removed=plan.count-CheckBagItem(role,plan.old)
    end
    if gained>removed then pcall(DelBagItem,role,plan.new,gained-removed) end
    sync(role)
    if removed~=plan.count or CheckBagItem(role,plan.new)~=initial+removed then
        if type(LG)=="function" then
            pcall(LG,"OwnerPersonalForge","Legacy transfer stopped; item="..plan.old.." moved="..removed)
        end
        return notice(role,npc,"Перенос остановлен. Перенесено "..removed.." шт. Проверь рюкзак.")
    end
    SendMissionPage(role,npc,3,"Перенесено "..removed.." шт. в новые стопки.",{"Назад"},1,nil,0)
    return LUA_TRUE
end

local function request(role, mode, material_slot)
    material_slot = material_slot or 1
    local target = GetChaItem(role, 2, 0)
    local material = GetChaItem(role, 2, material_slot)
    local first, second = identify(target), identify(material)
    if first == 0 or (mode ~= 3 and second == 0) then
        return nil, "Положи нужные предметы в первые ячейки рюкзака."
    end
    local fusion = GetItemAttr(target, ITEMATTR_VAL_FUSIONID)
    local kind = GetItemType(target)
    if mode == 1 then
        if first < 5000 or first >= 6000 or fusion ~= 0 or packed(target) ~= 0 then
            return nil, "В ячейку 1 положи чистую аппарель без слияния и ковки."
        end
        local base_kind = GetItemType(material)
        if second >= 5000 or not equipment(base_kind)
                or (kind ~= base_kind and not (kind == 27 and base_kind == 22))
                or CheckFusionItem(target, material) == LUA_FALSE then
            return nil, "В ячейке 2 нужна совместимая экипировка без аппарели."
        end
        return {target=target, material=material, id=second, forge=packed(material)},
            "Аппарель "..GetItemName(first)..", основа "..GetItemName(second)..". Основа будет потрачена. Итог: 110%."
    end
    if mode == 3 then
        local rank = GetItemAttr(target, ITEMATTR_VAL_LEVEL)
        if fusion == 0 or rank >= 15 then
            return nil, "Нужна слитая аппарель с эффективностью ниже 110%."
        end
        return {target=target}, "Усилить "..GetItemName(first).." до 110%."
    end
    if not equipment(kind) or (first >= 5000 and first < 6000 and fusion == 0) then
        return nil, "В ячейку 1 положи экипировку или слитую аппарель."
    end
    local base = ForgeGroundStacks and ForgeGroundStacks[second]
    local stone
    if base then
        for id=1,StoneTpye_ID_Num do
            if StoneTpye_ID[id]==base then stone=id; break end
        end
    elseif GetItemType(material) == 49 then
        stone = GetStone_TypeID(material)
    end
    if not stone or stone < 1 then
        return nil, "В выбранной ячейке нужен самоцвет, который поддерживает сервер."
    end
    local num = packed(target)
    local types = {GetNum_Part2(num), GetNum_Part4(num), GetNum_Part6(num)}
    local ranks = {GetNum_Part3(num), GetNum_Part5(num), GetNum_Part7(num)}
    local rank, used = 1, 0
    local slot, first_free
    for i = 1, 3 do
        if types[i] ~= 0 then
            used = used + 1
            if types[i] == stone then rank, slot = ranks[i] + 1, i end
        elseif not first_free then
            first_free = i
        end
    end
    if rank > 9 then return nil, "Этот самоцвет уже 9-го ранга." end
    if not slot and not first_free then return nil, "Все гнёзда заняты другими самоцветами." end
    local required = math.max(1, rank - 1)
    local cost = math.floor(2^(required-1))
    local raw
    if base then
        local capacity = GetKbCap(role)
        if type(capacity) ~= "number" or capacity < 4 then
            return nil, "Не удалось проверить ячейки рюкзака."
        end
        for i=0,capacity-1 do
            if i~=2 and i~=3 and identify(GetChaItem(role,2,i))==second then
                return nil, "Оставь стопки этого вида только в ячейках 3 и 4."
            end
        end
        if CheckBagItem(role, second) < cost then
            return nil, "Для этого шага нужно "..cost.." гемов в ячейках 3 и 4."
        end
        raw = true
    else
        raw = Get_StoneLv(material) == 1 and required > 1 and can_pay_raw(role, second, cost)
    end
    if not raw and Get_StoneLv(material) ~= required then
        return nil, "До ранга "..rank.." нужен один гем ранга "..required.." или "..cost.." одинаковых гемов первого ранга."
    end
    local sockets = GetNum_Part1(num)
    if not slot and used >= sockets then num = SetNum_Part1(num, used + 1) end
    local result
    if base then
        local socket = slot or first_free
        local put_stone = ({SetNum_Part2, SetNum_Part4, SetNum_Part6})[socket]
        local put_rank = ({SetNum_Part3, SetNum_Part5, SetNum_Part7})[socket]
        result = put_rank(put_stone(num, stone), rank)
    else
        result = SetJinglian_Lv(material, rank, num)
    end
    if result == num then return nil, "Сервер не смог рассчитать ковку." end
    local payment = raw and (cost.." гемов первого ранга") or ("1 гем ранга "..required)
    local bonus = fusion ~= 0 and " Эффективность: 110%." or " Обычная вещь: только ковка."
    local change = slot and ("ранг "..(rank-1).." -> "..rank) or "вставка ранга 1"
    return {target=target, material=material, id=second, forge=result, raw=raw,
            count=raw and cost or 1, strengthen=fusion ~= 0, material_slot=material_slot},
        GetItemName(first)..": "..GetItemName(second)..". Гнездо "..(slot or first_free)..": "..change..". Цена: "..payment.."."..bonus
end

local function apply(role, mode, plan)
    local target = plan.target
    if mode == 2 then
        return put_forge(target, plan.forge)
            and (not plan.strengthen or put_attr(target, ITEMATTR_VAL_LEVEL, 15))
    end
    if mode == 1 then
        if not put_attr(target, ITEMATTR_VAL_FUSIONID, plan.id) then return false end
        local fused = FusionItem(target, plan.material)
        if fused ~= 1 and fused ~= true then return false end
        if not put_attr(target, ITEMATTR_MAXURE, 20000)
                or not put_attr(target, ITEMATTR_URE, 20000)
                or not put_forge(target, plan.forge) then return false end
    end
    return put_attr(target, ITEMATTR_VAL_LEVEL, 15)
end

-- OWNER_GEM_COMBINE_CODE

local function handle_action(role, npc, action)
    if IsPlayer(role) ~= 1 then return LUA_FALSE end
    local x, y = GetChaPos(role)
    if GetChaMapName(role) ~= "garner" or (x - 225750)^2 + (y - 277050)^2 > 500^2 then
        return notice(role, npc, "Подойди ближе к личной кузнице.")
    end
    if unavailable then return notice(role, npc, "Кузница остановлена после сбоя. Нужна проверка сервера.") end
    if action == 5 then
        return notice(role, npc, "Для ковки до рангов 1-9, в гемах первого ранга: 1, 1, 2, 4, 8, 16, 32, 64, 128. Принеси один гем соответствующего ранга.")
    end
    if action < 1 or (action > 9 and (action < 20 or action > 25)) then return LUA_FALSE end
    local actor = GetCharID(role)
    if type(actor) ~= "number" or actor == 0 then
        return notice(role, npc, "Сервер не распознал персонажа. Открой кузницу заново.")
    end
    local now = os.time()
    for id, quote in pairs(pending) do
        if quote.expires < now then pending[id] = nil end
    end
    for id, menu in pairs(combine_menus) do
        if menu.expires<now then combine_menus[id]=nil end
    end
    if action == 8 or action == 9 then
        pending[actor]=nil
        local menu=combine_menus[actor]
        return show_combinations(role,npc,actor,now,action==9 and menu and menu.next or 1)
    end
    if action >= 20 then
        pending[actor]=nil
        return combination_preview(role,npc,actor,action,now)
    end
    if action == 7 then
        pending[actor]=nil
        local plan,message=migration_plan(role)
        if not plan then return notice(role,npc,message) end
        pending[actor]={migration=true, old=plan.old, count=plan.count, slot=plan.slot,
                        item=snapshot(plan.item), expires=now+60}
        return notice(role,npc,message,true)
    end
    if action <= 3 or action == 6 then
        pending[actor] = nil
        local mode = action == 6 and 2 or action
        local material_slot = 1
        if mode == 2 and ForgeGroundStacks then material_slot = action == 6 and 3 or 2 end
        local plan, message = request(role, mode, material_slot)
        if not plan then return notice(role, npc, message) end
        pending[actor] = {mode=mode, material_slot=material_slot, first=snapshot(plan.target), second=plan.material and snapshot(plan.material),
                          count=plan.count, raw=plan.raw, expires=now+60}
        return notice(role, npc, message, true)
    end
    local quote = pending[actor]
    pending[actor] = nil
    if type(SetChaKitbagChange) ~= "function" or type(SynChaKitbag) ~= "function"
            or type(RemoveChaItem) ~= "function" then
        return notice(role, npc, "На сервере недоступны функции обновления рюкзака.")
    end
    if not quote then return notice(role, npc, "Сначала снова проверь операцию.") end
    if quote.migration then return migrate(role,npc,quote) end
    if quote.combination then return confirm_combination(role,npc,quote) end
    local plan = request(role, quote.mode, quote.material_slot)
    if not plan or quote.count ~= plan.count or quote.raw ~= plan.raw
            or not unchanged(plan.target, quote.first)
            or (quote.second and not unchanged(plan.material, quote.second)) then
        return notice(role, npc, "Предметы изменились. Проверь операцию заново.")
    end
    local ok, changed = pcall(apply, role, quote.mode, plan)
    if ok and changed then
        local refreshed = pcall(check_item_final_data, plan.target)
        local paid = false
        if refreshed then
            if plan.raw then
                paid = DelBagItem(role, plan.id, plan.count) == 1
            else
                paid = not plan.id or RemoveChaItem(role, plan.id, 1, 2, plan.material_slot or 1, 2, 1, 0) == 1
            end
        end
        if paid then
            sync(role)
            SendMissionPage(role, npc, 3, "Готово. Улучшенная вещь осталась в ячейке 1.", {"Назад"}, 1, nil, 0)
            return LUA_TRUE
        end
    end
    local rolled_back, verified = pcall(restore, plan.target, quote.first)
    if not rolled_back or not verified then
        unavailable = true
        LG("OwnerPersonalForge", "Item rollback could not be verified")
    end
    sync(role)
    return notice(role, npc, "Операция остановлена. Проверь предметы в рюкзаке.")
end

function OwnerPersonalForgeAction(role, npc, action)
    local ok, result = pcall(handle_action, role, npc, action)
    if ok then return result end
    local found, actor = pcall(GetCharID, role)
    if found and actor then pending[actor] = nil end
    if type(LG) == "function" then
        pcall(LG, "OwnerPersonalForge", "Action "..tostring(action).." failed: "..tostring(result))
    end
    return notice(role, npc, "Сервер не завершил операцию. Проверь рюкзак. Причина записана в журнал кузницы.")
end

function OwnForgePrivate()
    if ForgeGroundStacks then
        Talk(1, "Слияние: аппарель в 1, основа во 2. Ковка: вещь в 1, гемы в 3 и 4.")
    else
        Talk(1, "Для слияния: аппарель в ячейку 1, оружие или броню во 2. Для ковки: вещь в 1, гем во 2.")
    end
    Text(1, "Слияние с аппарелью 110%", OwnerPersonalForgeAction, 1)
    if ForgeGroundStacks then
        Text(1, "Ковка гемом из ячейки 3", OwnerPersonalForgeAction, 2)
        Text(1, "Ковка гемом из ячейки 4", OwnerPersonalForgeAction, 6)
        Text(1, "Перенести старые стопки", OwnerPersonalForgeAction, 7)
    else
        Text(1, "Проверить ковку", OwnerPersonalForgeAction, 2)
    end
    Text(1, "Усиление аппарели 110%", OwnerPersonalForgeAction, 3)
    Text(1, "Скомбинировать гемы", OwnerPersonalForgeAction, 8)
    Text(1, "Сколько гемов нужно", OwnerPersonalForgeAction, 5)
    Text(1, "Закрыть", CloseTalk)
    Talk(2, "Сначала проверь операцию.")
    Text(2, "Подтвердить", OwnerPersonalForgeAction, 4)
    Text(2, "Назад", JumpPage, 1)
    Talk(3, "Личная кузница")
    Text(3, "Назад", JumpPage, 1)
    Talk(4, "Скомбинировать гемы")
    Text(4, "Назад", JumpPage, 1)
    Text(4, "Следующие виды", OwnerPersonalForgeAction, 9)
    for i=20,25 do Text(4,"Самоцвет",OwnerPersonalForgeAction,i) end
end
-- OWNER_PERSONAL_FORGE_END
