-- All four roles actually travel, buy their native item, debit real gold and the gear ledger.
local choices={[0]=3,[1]=0,[2]=2,[3]=1}
for role=0,3 do
 reset();local kind=0
 while HeroBotRole[kind]~=role do kind=kind+1;assert(kind<HERO_COUNT)end
 CreateHero(0,kind);Bot[0]=true;Seconds=500;GearProgress[0]=3;GearSavings[0]=50000;Players[0].gold=100000
 local h=Hero[0];h.x,h.y=0,0;local gold=Players[0].gold;local savings=GearSavings[0];local index=choices[role]
 assert(BotArenaShop(0)and h.order[2]==-720 and h.order[3]==320)
 assert(Players[0].gold==gold and GearSavings[0]==savings,'Travel is not a purchase')
 h.x,h.y=-720,320;assert(BotArenaShop(0));assert(HeroItem(h,ArenaItemId[index])and ArenaRelicBought[0])
 assert(Players[0].gold==gold-ArenaItemCost[index]and GearSavings[0]==savings-ArenaItemCost[index])
 assert(not BotArenaShop(0),'Do not repeatedly buy or spam visits')
 Seconds=680;h.x,h.y=720,320;gold=Players[0].gold;savings=GearSavings[0]
 local supply=role==0 and 4 or(role==3 and 6 or 7)
 assert(BotArenaShop(0)and HeroItem(h,ArenaItemId[supply]))
 assert(Players[0].gold==gold-ArenaItemCost[supply]and GearSavings[0]==savings-ArenaItemCost[supply])
 h.max=1000;h.hp=200;BotNearbyTroops[0]=6;BotEnemyPower[0]=5
 assert(BotUseSupplies(0)and h.used==ArenaItemId[supply]and not HeroItem(h,ArenaItemId[supply]))
end
-- Explicit defense-scroll targeting conditions and no waste outside a battle.
reset();local h=Hero[0];h.inventory[0]={id=FourCC('frdf')};BotNearbyTroops[0]=8
assert(not BotUseSupplies(0)and h.inventory[0]);BotEnemyPower[0]=5
assert(BotUseSupplies(0)and h.used==FourCC('frdf'))
-- Failed stock, insufficient savings, full inventory, and combat cannot create/free items.
reset();h=Hero[0];h.x,h.y=-720,320;GearProgress[0]=3;GearSavings[0]=100000;Players[0].gold=100000;Seconds=500
BlockStock=true;assert(BotArenaShop(0));assert(Players[0].gold==100000 and GearSavings[0]==100000 and not ArenaRelicBought[0]);BlockStock=false
Seconds=600;GearSavings[0]=1;assert(not BotArenaShop(0));GearSavings[0]=100000
for slot=0,5 do h.inventory[slot]={id=SuperId[slot]}end
assert(not BotArenaShop(0));for slot=0,5 do assert(h.inventory[slot].id==SuperId[slot])end
h.inventory={};BotEnemyPower[0]=1;assert(not BotArenaShop(0))
-- A relic replacing an early item must not stall later ordinary gear progression.
reset();h=Hero[0];GearProgress[0]=6;GearSavings[0]=100000;Players[0].gold=100000
local index=DesiredGear(0);local shop=GearShop[index];h.x,h.y=ShopX[shop],ShopY[shop]
for slot=0,5 do h.inventory[slot]={id=GearId[GearFamily(0,slot)*3]}end
for slot=0,5 do if h.inventory[slot].id==GearId[index-1]then h.inventory[slot]={id=FourCC('frcf')}end end
assert(BotShop(0)and GearProgress[0]==7 and HeroItem(h,GearId[index]),'Missing earlier-tier item still permits a paid upgrade')
assert(HeroItem(h,FourCC('frcf')),'Do not replace the more expensive relic with lesser gear')
-- Carry income shares retain fractional single-gold credits and constrain real research.
reset();Bot[0]=true;BotTactic[0]=3
for i=1,1000 do AddGold(0,1)end
assert(GearSavings[0]==550 and ArmySavings[0]==450 and Players[0].gold==STARTING_GOLD+1000)
local cost=UpgradeCost(0,0);local gold=Players[0].gold
assert(BotResearch(0,0)and ArmySavings[0]==450-cost and GearSavings[0]==550 and Players[0].gold==gold-cost)
FinishResearch(0);assert(ArmySavings[0]==450-cost,'Completion never debits the army budget twice')
ArmySavings[0]=0;Players[0].gold=100000;gold=Players[0].gold
assert(not BotResearch(0,1)and Players[0].gold==gold,'Other45% cannot be exceeded merely because cash is available')
GearProgress[0]=18;SuperProgress[0]=6;AddGold(0,100);assert(GearSavings[0]==605 and ArmySavings[0]==45,'Late-game supplies retain the same55/45 shares')
print('PASS:0.23 all4 native role purchases/use,travel,stock/funds/full inventory,gear continuation,1000 single-gold credits and paid55/45 carry research (mock natives).')
