-- Read-only evidence around the existing XP/ground-loot chain. Never add XP,
-- change rates or replace the game's eligibility/team calculations.
Owner60XPCounters={}
Owner60XPActors=0
if Owner60OriginalGetExp==nil then Owner60OriginalGetExp=GetExp_New end
if type(Owner60OriginalGetExp)=="function" then
    function GetExp_New(dead,attacker)
        if IsPlayer(dead)~=0 or IsPlayer(attacker)~=1 then
            return Owner60OriginalGetExp(dead,attacker)
        end
        local before=GetChaAttr(attacker,ATTR_CEXP)
        local scale=-1
        if type(GetExpState)=="function" then scale=GetExpState(attacker) end
        local raw_scale=scale
        if type(Owner60RawExpState)=="function" then raw_scale=Owner60RawExpState(attacker) end
        local base=GetChaAttr(dead,ATTR_CEXP)
        local result={pcall(Owner60OriginalGetExp,dead,attacker)}
        local ok=table.remove(result,1)
        local after=GetChaAttr(attacker,ATTR_CEXP)
        pcall(function()
        local key=GetChaDefaultName(attacker)
        local count=Owner60XPCounters[key]
        if count==nil and Owner60XPActors<1024 then
            count=0;Owner60XPActors=Owner60XPActors+1
        end
        if count~=nil then
            count=count+1;Owner60XPCounters[key]=count
            if count<=3 or math.mod(count,20)==0 or not ok then
                SystemNotice(attacker,"OWNER60_XP rate="..tostring(EXP_RAID or -1)..
                    " scale="..tostring(raw_scale).." base="..tostring(base)..
                    " before="..tostring(before).." after="..tostring(after)..
                    " monster="..tostring(GetChaTypeID(dead)).." ok="..(ok and "1" or "0")..
                    " effective="..tostring(scale))
            end
        end
        end)
        if not ok then error(result[1]) end
        return unpack(result)
    end
end
