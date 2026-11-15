-- Explicit owner-requested level target. Native AddExp awards the level-up points.
local function level35()
    if type(GetPlayerByName) ~= "function" or type(GetChaAttr) ~= "function"
        or type(AddExp) ~= "function" or type(GetChaDefaultName) ~= "function"
        or type(GetExp) ~= "table" or type(GetExp[35]) ~= "number" then
        error("BubaLevel35: required native API/experience table unavailable; nothing changed")
    end
    if not ATTR_LV or not ATTR_CEXP or not ATTR_JOB then
        error("BubaLevel35: character constants unavailable; nothing changed")
    end
    local role = GetPlayerByName("buba")
    if not role or GetChaDefaultName(role) ~= "buba" then
        error("BubaLevel35: buba must be online in this GameServer")
    end
    local level = GetChaAttr(role, ATTR_LV)
    if level >= 35 then
        SystemNotice(role, "BubaLevel35: already level35 or higher; nothing changed")
        return
    end
    if GetChaAttr(role, ATTR_JOB) ~= 1 then
        error("BubaLevel35: set swordsman profession first with GM command attr 4,1")
    end
    local current = GetChaAttr(role, ATTR_CEXP)
    if type(current) ~= "number" then error("BubaLevel35: experience unavailable") end
    local amount = GetExp[35] - current
    if amount <= 0 or amount >= 2147483647 then
        error("BubaLevel35: inconsistent experience; nothing changed")
    end
    AddExp(role, nil, amount, amount)
    if GetChaAttr(role, ATTR_LV) ~= 35 then
        error("BubaLevel35: native result is not level35; inspect the character before continuing")
    end
    SystemNotice(role, "BubaLevel35: native experience awarded; level35 confirmed")
end

level35()
