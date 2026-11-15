-- Owner-authorized, one-time grant for buba. Loaded explicitly by a GM only.
-- Creates new items; never selects, edits or equips existing player equipment.
local function give()
    local required = {"GetPlayerByName", "GetChaDefaultName", "GetChaFreeBagGridNum",
        "GetChaItem", "GetItemID", "MakeItem", "FusionItem", "SetItemAttr",
        "GetItemAttr", "SetItemForgeParam", "GetItemForgeParam", "GetResPath",
        "RemoveChaItem", "SetChaKitbagChange", "SynChaKitbag", "SystemNotice",
        "check_item_final_data", "GetItem_JinglianLv", "TansferNum"}
    for _, name in ipairs(required) do
        if type(_G[name]) ~= "function" then
            error("BubaSwords: unavailable server function: " .. name .. "; nothing created")
        end
    end
    if not io or not io.open then error("BubaSwords: file ledger unavailable; nothing created") end
    if not ITEMATTR_VAL_FUSIONID or not ITEMATTR_VAL_LEVEL or not ITEMATTR_URE or not ITEMATTR_MAXURE then
        error("BubaSwords: item constants unavailable; nothing created")
    end
    local role = GetPlayerByName("buba")
    if not role or GetChaDefaultName(role) ~= "buba" then
        error("BubaSwords: buba must be online in this GameServer; nothing created")
    end
    local function fail(message)
        SystemNotice(role, "BubaSwords: " .. message)
        error("BubaSwords: " .. message)
    end
    local ledger = GetResPath("owner-buba-swords-01.state")
    local previous = io.open(ledger, "r")
    if previous then
        local state = previous:read("*a"); previous:close()
        fail("already attempted: " .. state .. "; inspect the bag/server log; do not repeat blindly")
    end
    if GetChaFreeBagGridNum(role) < 4 then fail("need four free ordinary bag slots; nothing created") end
    local occupied = {}
    for slot = 0, 47 do
        local item = GetChaItem(role, 2, slot)
        if item and GetItemID(item) ~= 0 then occupied[slot] = true end
    end
    local function save(state)
        local file = io.open(ledger, "w")
        if not file then fail("cannot write local ledger; stop and inspect") end
        if not file:write(state .. "\n") then file:close();fail("ledger write failed; stop and inspect") end
        if not file:close() then fail("ledger close failed; stop and inspect") end
    end
    -- Any interrupted attempt stays pending and cannot mint another pair on retry.
    save("pending buba")
    local function create(identity)
        local ok, slot = MakeItem(role, identity, 1, 4)
        if ok ~= 1 and ok ~= true then fail("item creation failed; pending ledger retained") end
        if type(slot) ~= "number" or slot < 0 or slot > 47 or occupied[slot] then
            fail("unexpected creation slot; no existing item will be edited")
        end
        local item = GetChaItem(role, 2, slot)
        if not item or GetItemID(item) ~= identity then fail("created item not confirmed") end
        occupied[slot] = true
        return item, slot
    end
    local outfits = {}
    local bases = {}
    for index = 1, 2 do
        local base, base_slot = create(1397) -- Assassin Sword, one hand, level35.
        local outfit, outfit_slot = create(5002) -- Sword of Crimson Thunder apparel.
        SetItemAttr(outfit, ITEMATTR_VAL_FUSIONID, 1397)
        local fused = FusionItem(outfit, base)
        if fused ~= 1 and fused ~= true then fail("native fusion failed") end
        SetItemAttr(outfit, ITEMATTR_VAL_LEVEL, 15) -- Native apparel strengthening cap.
        SetItemAttr(outfit, ITEMATTR_MAXURE, 20000) -- Same durability as source fusion.
        SetItemAttr(outfit, ITEMATTR_URE, 20000)
        -- 3 sockets; type12/rank9, type13/rank9, type1/rank9 = +27 total.
        SetItemForgeParam(outfit, 1, 3129139019)
        check_item_final_data(outfit)
        if GetItemID(outfit) ~= 5002 or GetItemAttr(outfit, ITEMATTR_VAL_FUSIONID) ~= 1397
            or GetItemAttr(outfit, ITEMATTR_VAL_LEVEL) ~= 15
            or TansferNum(GetItemForgeParam(outfit, 1)) ~= 3129139019
            or GetItem_JinglianLv(outfit) ~= 27 then fail("final item verification failed") end
        outfits[index] = outfit_slot
        bases[index] = base_slot
    end
    -- Consume only the two temporary bases created above, as normal fusion does.
    for index = 1, 2 do
        local slot = bases[index]
        local item = GetChaItem(role, 2, slot)
        if not item or GetItemID(item) ~= 1397 then fail("temporary base identity changed") end
        local removed = RemoveChaItem(role, 1397, 1, 2, slot, 2, 1, 0)
        if removed ~= 1 and removed ~= true then fail("temporary base removal failed") end
    end
    SetChaKitbagChange(role, 1)
    SynChaKitbag(role, 13)
    save("done buba slots " .. outfits[1] .. "," .. outfits[2])
    SystemNotice(role, "BubaSwords: received 2 Crimson Thunder/Assassin swords, gems9/9/9 (+27), apparel15")
end

give()
