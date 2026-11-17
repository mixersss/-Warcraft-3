-- Real satiety cost, not a fixed100-stamina gate that rejects fed shop fairies.
-- Preserve generation, item, SP, cooldown and native state/experience formulas.
function Skill_JLFT_BEGIN(role,sklv)
    local fairy=GetChaItem(role,2,1)
    if fairy==nil or fairy==0 or GetItemType(fairy)~=59 then
        SkillUnable(role)
        SystemNotice(role,"Put your second-generation fairy in bag slot2.")
        return
    end
    if GetNum_Part1(GetItemForgeParam(fairy,1))~=1 then
        SkillUnable(role)
        SystemNotice(role,"Fairy Possession requires a second-generation fairy.")
        return
    end
    if type(sklv)~="number" or sklv<1 or sklv>3 then
        SkillUnable(role)
        SystemNotice(role,"Fairy Possession skill rank is invalid.")
        return
    end
    local level=0
    for _,attribute in ipairs({ITEMATTR_VAL_STR,ITEMATTR_VAL_CON,ITEMATTR_VAL_AGI,ITEMATTR_VAL_DEX,ITEMATTR_VAL_STA}) do
        level=level+GetItemAttr(fairy,attribute)
    end
    local cost=math.ceil(300*level/sklv)
    local satiety=GetItemAttr(fairy,ITEMATTR_URE)
    if satiety<math.max(50,cost) then
        SkillUnable(role)
        SystemNotice(role,"Feed your fairy: Possession needs "..math.ceil(math.max(50,cost)/50).." stamina.")
        return
    end
    SetItemAttr(fairy,ITEMATTR_URE,satiety-cost)
end
