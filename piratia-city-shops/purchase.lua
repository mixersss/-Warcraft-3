-- Original owner-market implementation. No source server scripts are bundled.
OwnerMarketBusy = {}
function OwnerMarketBuy(character, npc, shopid, itemid)
    local shop = OwnerMarketCatalog[shopid]
    local offer = shop and shop[itemid]
    if offer == nil or OwnerMarketBusy[character] then return LUA_FALSE end
    if ChaIsBoat(character) ~= 0 then
        SystemNotice(character, "Please land before buying.")
        return LUA_FALSE
    end
    if GetChaFreeBagGridNum(character) < 1 then
        SystemNotice(character, "Please free one inventory slot.")
        return LUA_FALSE
    end
    local price = offer.price
    local before = GetChaAttr(character, ATTR_GD)
    if type(before) ~= "number" or before < price then
        SystemNotice(character, "Not enough gold. Price: " .. price)
        return LUA_FALSE
    end
    OwnerMarketBusy[character] = true
    local ok, result = pcall(function()
        local paid, ret = pcall(TakeMoney, character, npc, price)
        local after = GetChaAttr(character, ATTR_GD)
        local spent = before - after
        if not paid or ret ~= LUA_TRUE or spent ~= price then
            -- Refund only the amount actually deducted; never mint a quoted price.
            if spent > 0 and spent <= price then AddMoney(character, npc, spent) end
            SystemNotice(character, "Payment was not confirmed. Purchase cancelled.")
            return LUA_FALSE
        end
        local count = CheckBagItem(character, itemid)
        local given, native = pcall(GiveItem, character, npc, itemid, 1, 4)
        local current = CheckBagItem(character, itemid)
        if current == count + 1 then
            SystemNotice(character, "Purchased " .. offer.name .. " for " .. price .. " gold.")
            return LUA_TRUE
        end
        if current == count then
            AddMoney(character, npc, spent)
            if GetChaAttr(character, ATTR_GD) ~= before then
                LG("owner_market_error", "Refund failed for item %d", itemid)
                SystemNotice(character, "Delivery failed. Please contact the administrator about payment.")
            else
                SystemNotice(character, "Item was not delivered. Your payment was returned.")
            end
            return LUA_FALSE
        end
        LG("owner_market_error", "Unexpected inventory change for item %d", itemid)
        return LUA_FALSE
    end)
    OwnerMarketBusy[character] = nil
    if not ok then
        -- An unexpected engine failure must not trigger a blind duplicate item/refund.
        LG("owner_market_error", "Unexpected purchase error for item %d", itemid)
        SystemNotice(character, "Purchase error. Please contact the administrator.")
        return LUA_FALSE
    end
    return result
end
