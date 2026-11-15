-- Owner-authorized, one-time grant for buba. Loaded explicitly by a GM only.
-- Creates new items; never selects, edits or equips existing player equipment.
function BubaGiveSwords(role)
    local required = {"GetChaDefaultName", "GetChaFreeBagGridNum",
        "GetChaItem", "GetItemID", "MakeItem", "FusionItem", "SetItemAttr",
        "GetItemAttr", "SetItemForgeParam", "GetItemForgeParam", "GetResPath",
        "RemoveChaItem", "SetChaKitbagChange", "SynChaKitbag", "SystemNotice"}
    for _, name in ipairs(required) do
        if type(_G[name]) ~= "function" then
            error("BubaSwords: unavailable server function: " .. name .. "; nothing created")
        end
    end
    if type(check_item_final_data)~="function" and
        (type(ResetItemFinalAttr)~="function" or type(AddItemFinalAttr)~="function") then
        error("BubaSwords: final item attribute API unavailable; nothing created")
    end
    if not io or not io.open then error("BubaSwords: file ledger unavailable; nothing created") end
    if not ITEMATTR_VAL_FUSIONID or not ITEMATTR_VAL_LEVEL or not ITEMATTR_URE or not ITEMATTR_MAXURE then
        error("BubaSwords: item constants unavailable; nothing created")
    end
    if not role or string.lower(GetChaDefaultName(role)) ~= "buba" then
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
        local ok,item = pcall(GetChaItem, role, 2, slot)
        if not ok then break end -- Some classic bags expose only24 cells.
        if item ~= nil and item ~= 0 then
            local valid,identity = pcall(GetItemID,item)
            if not valid or type(identity)~="number" then fail("bag inspection unavailable") end
            if identity ~= 0 then occupied[slot] = true end
        end
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
        if not item or item == 0 or GetItemID(item) ~= identity then fail("created item not confirmed") end
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
        if type(check_item_final_data)=="function" then check_item_final_data(outfit)
        else
            -- Same fixed gem contributions as source check_item_final_data.
            if ResetItemFinalAttr(outfit)==0 or AddItemFinalAttr(outfit,26,45)==0
                or AddItemFinalAttr(outfit,34,486)==0 or AddItemFinalAttr(outfit,35,486)==0 then
                fail("native final gem attributes failed")
            end
        end
        local verified_forge=GetItemForgeParam(outfit,1)
        if type(verified_forge)~="number" then fail("forge parameter unavailable") end
        if verified_forge<0 then verified_forge=verified_forge+4294967296 end
        if GetItemID(outfit) ~= 5002 or GetItemAttr(outfit, ITEMATTR_VAL_FUSIONID) ~= 1397
            or GetItemAttr(outfit, ITEMATTR_VAL_LEVEL) ~= 15
            or verified_forge ~= 3129139019 then fail("final item verification failed") end
        outfits[index] = outfit_slot
        bases[index] = base_slot
    end
    -- Consume only the two temporary bases created above, as normal fusion does.
    for index = 1, 2 do
        local slot = bases[index]
        local item = GetChaItem(role, 2, slot)
        if not item or item == 0 or GetItemID(item) ~= 1397 then fail("temporary base identity changed") end
        local removed = RemoveChaItem(role, 1397, 1, 2, slot, 2, 1, 0)
        if removed ~= 1 and removed ~= true then fail("temporary base removal failed") end
    end
    SetChaKitbagChange(role, 1)
    SynChaKitbag(role, 13)
    save("done buba slots " .. outfits[1] .. "," .. outfits[2])
    SystemNotice(role, "BubaSwords: received 2 Crimson Thunder/Assassin swords, gems9/9/9 (+27), apparel15")
end

if not BubaLoadOnly then
    if type(GetPlayerByName)=="function" then BubaGiveSwords(GetPlayerByName("buba"))
    else error("BubaSwords: this classic server needs BubaNPC.lua; then talk to an NPC") end
end
