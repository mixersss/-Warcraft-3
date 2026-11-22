-- Owner's persistent private-server progression: retain the configured EXP_RAID
-- and native kill/quest calculation, remove only the online-time reduction.
-- Never grant experience directly or change saved characters/accounts.
if Owner60RawExpState==nil then Owner60RawExpState=GetExpState end
if type(Owner60RawExpState)=="function" then
    function GetExpState(role)
        local scale=Owner60RawExpState(role)
        if IsPlayer(role)==1 and type(scale)=="number" and scale>=0 and scale<100 then
            return 100
        end
        return scale
    end
end
