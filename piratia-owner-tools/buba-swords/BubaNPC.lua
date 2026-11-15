-- Runtime-only bridge for classic GameServer without GetPlayerByName.
-- NPC MsgProc receives the authoritative character pointer. No SDK file edits.
local function setup()
    if type(MsgProc)~="function" or type(GetChaDefaultName)~="function"
        or type(GetResPath)~="function" then error("classic NPC API unavailable") end
    BubaLoadOnly=true
    local ok,problem=pcall(function()
        dofile(GetResPath("script/BubaSwords.lua"))
    end)
    BubaLoadOnly=nil
    if not ok then error(problem) end
    if not BubaOriginalMsgProc then BubaOriginalMsgProc=MsgProc end
    BubaNPCAttempted=false
    function MsgProc(character,npc,rpk,page,trade,missionlist,exchangeData)
        if character and npc and not BubaNPCAttempted and GetChaDefaultName(character)=="buba" then
            BubaNPCAttempted=true
            local worked,reason=pcall(function()
                BubaGiveSwords(character)
            end)
            if not worked then
                local text=tostring(reason)
                SystemNotice(character,"BubaNPC ERROR: "..string.sub(text,1,180))
                print("BubaNPC ERROR: "..text)
            end
        end
        return BubaOriginalMsgProc(character,npc,rpk,page,trade,missionlist,exchangeData)
    end
    Notice("BubaNPC READY: close old dialogue, then buba talks to any NPC. No GetPlayerByName needed.")
end

local ok,reason=pcall(setup)
if not ok then
    local text=tostring(reason)
    if type(Notice)=="function" then Notice("BubaNPC SETUP ERROR: "..string.sub(text,1,160)) end
    print("BubaNPC SETUP ERROR: "..text)
end
