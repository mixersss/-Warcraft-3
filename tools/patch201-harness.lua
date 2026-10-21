-- Actual Keeper AI uses an immediate native summon, with no point/tree target.
for _,rank in ipairs({1,10,100,200})do
 reset();CreateHero(0,13);Bot[0]=true
 UnitAddAbility(Hero[0],FourCC('Fent'));SetUnitAbilityLevel(Hero[0],FourCC('Fent'),rank)
 local enemy=CreateUnit(3,0,100,0,0)
 AllowedOrders={waterelemental=true}
 assert(HeroSkill[13*4+2]==FourCC('Fent'))
 assert(TryBotSpell(0,enemy)and Hero[0].order[1]=='waterelemental'and #Hero[0].order==1,'Keeper summons without any tree or point target')
 assert(CastUntil[0]==Seconds+1)
 AllowedOrders=nil
end
print('PASS:Keeper native summon uses immediate bot orders at ranks1/10/100/200 with no destructable or point target (mock natives).')
