-- Owner-authorized public progression shortcuts. No SQL/account/stat resets.
Owner56Bodies = {[1]={[1]=true,[2]=true},[2]={[1]=true,[3]=true},
                 [4]={[1]=true,[3]=true,[4]=true},[5]={[3]=true,[4]=true},
                 [8]={[2]=true},[9]={[1]=true},[12]={[1]=true,[3]=true},
                 [13]={[3]=true,[4]=true},[14]={[3]=true,[4]=true},[16]={[1]=true,[3]=true,[4]=true}}
Owner56First = {[8]=1,[9]=1,[12]=2,[13]=5,[14]=5,[16]=4}
Owner56Corals = {[817]=5,[867]=7,[635]=6}
Owner56BasicSpell = {[4]=214,[16]=214,[5]=99,[13]=99,[14]=99}

function Owner56CombatBasics(role)
    local skill=Owner56BasicSpell[GetChaAttr(role,ATTR_JOB)]
    if skill and GetChaAttr(role,ATTR_LV)>=9 and GetSkillLv(role,skill)==0 then
        -- One initial class spell is part of the shortcut profession package.
        -- Preserve all earned points and every previously learned skill/rank.
        -- Newer engines accept the sixth prerequisite flag; classic builds
        -- can reject it. Never retry if the first call actually learned it.
        local ok,result=pcall(AddChaSkill,role,skill,1,1,0,1)
        if GetSkillLv(role,skill)==0 then
            ok,result=pcall(AddChaSkill,role,skill,1,1,0)
        end
        if GetSkillLv(role,skill)==0 then
            SystemNotice(role,"Owner combat restore failed: skill="..skill.."; native result="..tostring(result))
            return LUA_FALSE
        end
    end
    return LUA_TRUE
end

function OwnerProgressAction(role,npc,kind,value)
    if IsPlayer(role)~=1 then return LUA_FALSE end
    if kind=="owner-profession" then
        local body=GetChaTypeID(role)
        local current=GetChaAttr(role,ATTR_JOB)
        local level=GetChaAttr(role,ATTR_LV)
        if not Owner56Bodies[value] or not Owner56Bodies[value][body] then
            SystemNotice(role,"This profession is not available for your race.")
            return LUA_FALSE
        end
        local first=Owner56First[value]
        if (first and (level<40 or current~=first)) or (not first and (level<9 or current~=0)) then
            SystemNotice(role,"First profession: level 9 novice. Second: level 40 and matching first profession.")
            return LUA_FALSE
        end
        SetProfession(role,value)
        if GetChaAttr(role,ATTR_JOB)~=value then return LUA_FALSE end
        Owner56CombatBasics(role)
        SystemNotice(role,"Profession granted. Existing attributes and skills were preserved.")
        return LUA_TRUE
    elseif kind=="owner-combat" then
        return Owner56CombatBasics(role)
    elseif kind=="owner-gem-stats" then
        local stats=Owner56GemStats
        if stats then
            SystemNotice(role,"Gem loot: kills="..stats.kills..", successful 3% rolls="..stats.rolls..", ground requests="..stats.ground..", failures="..stats.failures)
            if stats.blueprints then SystemNotice(role,"Owner57 ground blueprint requests="..stats.blueprints..". Protection should expire after1second.") end
        end
        return LUA_TRUE
    elseif kind=="owner-stall" then
        if GetSkillLv(role,241)<3 then AddChaSkill(role,241,3,1,0) end
        if GetSkillLv(role,241)<3 then
            SystemNotice(role,"Stall skill was not confirmed. Contact the server owner.")
            return LUA_FALSE
        end
        return LUA_TRUE
    elseif kind=="owner-bags" then
        local capacity=GetKbCap(role)
        for index=1,6 do
            local identity=3087+index
            if capacity<24+4*index and CheckBagItem(role,identity)==0 then
                local free=false
                for slot=0,capacity-1 do
                    local item=GetChaItem(role,2,slot)
                    if item==nil or item==0 then free=true;break end
                end
                if not free then break end
                local result=GiveItem(role,npc,identity,1,4)
                if result~=LUA_TRUE then break end
            end
        end
        return LUA_TRUE
    end
    return LUA_FALSE
end

function Owner56RefillCorals(role)
    if IsPlayer(role)~=1 then return end
    local changed=false
    for identity,link in pairs(Owner56Corals) do
        local item=GetChaItem(role,1,link)
        if item and item~=0 and GetItemID(item)==identity then
            local maximum=GetItemAttr(item,ITEMATTR_MAXENERGY)
            if maximum>0 and GetItemAttr(item,ITEMATTR_ENERGY)<maximum then
                SetItemAttr(item,ITEMATTR_ENERGY,maximum)
                changed=true
            end
        end
    end
    if changed then RefreshCha(role) end
end

-- Native skill Begin runs on an actual cast. Recharge only the three basic
-- corals; preserve higher tiers, SP charges, cooldowns and all spell effects.
Owner56OriginalBegins=Owner56OriginalBegins or {}
for _,name in ipairs({"Skill_Jf_Begin","Skill_Lj_Begin","Skill_Bkcj_Begin"}) do
    if Owner56OriginalBegins[name]==nil then Owner56OriginalBegins[name]=_G[name] end
    local original=Owner56OriginalBegins[name]
    if type(original)=="function" then
        _G[name]=function(role,level)
            Owner56RefillCorals(role)
            return original(role,level)
        end
    end
end
if Owner56OriginalTimer==nil then Owner56OriginalTimer=cha_timer end
if type(Owner56OriginalTimer)=="function" then
    function cha_timer(role,freq,time)
        Owner56RefillCorals(role)
        return Owner56OriginalTimer(role,freq,time)
    end
end
