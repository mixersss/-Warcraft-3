-- Own stock selection only; payment and item creation use original SafeBuy.
function OwnerGemSlots(character)
    local ids={};local pointers={}
    for slot=0,47 do
        local ok,item=pcall(GetChaItem,character,2,slot)
        if not ok then break end
        if ok then
            if item==nil or item==0 then ids[slot]=0
            else
                local valid,identity=pcall(GetItemID,item)
                if valid then ids[slot]=identity;pointers[slot]=item end
            end
        end
    end
    return ids,pointers
end

function OwnerInitializeFreshFairy(character,item,generation)
    -- NPC_SALE normally adds10to all five stats. Only a newly paid stock
    -- fairy starts at zero here; previously owned fairies are never reset.
    AddItemEffect(character,item,0)
    for _,attribute in ipairs({ITEMATTR_VAL_STR,ITEMATTR_VAL_AGI,ITEMATTR_VAL_DEX,ITEMATTR_VAL_CON,ITEMATTR_VAL_STA}) do
        SetItemAttr(item,attribute,0)
    end
    SetItemAttr(item,ITEMATTR_MAXENERGY,240)
    SetItemAttr(item,ITEMATTR_ENERGY,0)
    SetItemAttr(item,ITEMATTR_MAXURE,5000)
    SetItemAttr(item,ITEMATTR_URE,5000)
    local parameters=GetItemForgeParam(item,1)
    SetItemForgeParam(item,1,SetNum_Part1(parameters,generation))
    ResetItemFinalAttr(item)
    AddItemEffect(character,item,1)
end

function OwnerOpenTrade(character,npc,shopid,page)
    if shopid=="owner-bags" or shopid=="owner-profession" or shopid=="owner-stall" or shopid=="owner-combat" or shopid=="owner-gem-stats" then
        return OwnerProgressAction(character,npc,shopid,page)
    end
    local shop=OwnerNativeShops[shopid]
    local selected=shop and shop.pages[page]
    if selected==nil then return LUA_FALSE end
    selected.tp=TRADE_NOMAL
    local stamp=os.time()
    for player,row in pairs(OwnerNativeSelection) do
        if row.expires < stamp then OwnerNativeSelection[player]=nil end
    end
    OwnerNativeSelection[character]={npc=GetCharID(npc),shop=shopid,page=page,expires=stamp+3600}
    TradePage(character,npc,selected,TRADE_BUY,0)
    return LUA_TRUE
end

function OwnerNativeBuy(character,npc,trade,itemtype,index1,index2,count)
    local key=trade.owner_native_shop
    local shop=OwnerNativeShops[key]
    local selected=OwnerNativeSelection[character]
    if shop==nil or selected==nil or selected.npc~=GetCharID(npc)
        or selected.shop~=key or selected.expires<os.time() then
        SystemNotice(character,"Please reopen Trade at this merchant.")
        return LUA_FALSE
    end
    if type(itemtype)~="number" or itemtype<0 or itemtype>2 or itemtype~=math.floor(itemtype)
        or type(index1)~="number" or index1<0 or index1~=math.floor(index1)
        or type(index2)~="number" or index2<0 or index2>255 or index2~=math.floor(index2)
        or type(count)~="number" or count<1 or count>99 or count~=math.floor(count) then return LUA_FALSE end
    local stock=shop.pages[selected.page]
    local panel=stock and stock[itemtype+1]
    local identity=panel and panel.item[index1+1]
    if identity==nil then return LUA_FALSE end
    local before=nil
    local fairy=OwnerFreshFairies[identity]
    if OwnerBasicGems[identity] then
        if count~=1 or type(Set_StoneLv)~="function" or type(SynChaKitbag)~="function" then return LUA_FALSE end
        before=OwnerGemSlots(character)
    elseif fairy~=nil then
        if count~=1 or type(SetItemAttr)~="function" or type(GetItemForgeParam)~="function"
            or type(SetItemForgeParam)~="function" or type(SetNum_Part1)~="function"
            or type(ResetItemFinalAttr)~="function" or type(SynChaKitbag)~="function"
            or type(AddItemEffect)~="function" then return LUA_FALSE end
        local attributes={ITEMATTR_VAL_STR,ITEMATTR_VAL_AGI,ITEMATTR_VAL_DEX,ITEMATTR_VAL_CON,ITEMATTR_VAL_STA,
                          ITEMATTR_MAXENERGY,ITEMATTR_ENERGY,ITEMATTR_MAXURE,ITEMATTR_URE}
        for index=1,9 do if type(attributes[index])~="number" then return LUA_FALSE end end
        before=OwnerGemSlots(character)
    end
    local result=SafeBuy(character,identity,index2,count)
    if before~=nil then
        local after,pointers=OwnerGemSlots(character)
        local candidate=nil;local found=0
        for slot=0,47 do
            if before[slot]==0 and after[slot]==identity then candidate=pointers[slot];found=found+1 end
        end
        -- Only the newly purchased unstackable gem is configured. Existing
        -- high-level gems and the table's global energy limits remain intact.
        if found==1 then
            local ok
            if fairy~=nil then ok=pcall(OwnerInitializeFreshFairy,character,candidate,fairy)
            else ok=pcall(Set_StoneLv,candidate,1) end
            if ok then SynChaKitbag(character,13)
            else SystemNotice(character,"Item bought; initial setup failed. Please contact the administrator.") end
        end
    end
    return result
end
