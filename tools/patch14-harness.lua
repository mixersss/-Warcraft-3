-- Execute real JASS against emitted native research prices, not duplicated mock prices.
reset();Players[0].gold=1000000;Hero[0].hp=0
local gold=Players[0].gold
assert(Buy(0,6) and Base[0].pending==FourCC('Rfwn') and Players[0].gold==gold-2000,'Wave research works while hero is dead and debits native gold exactly once')
FinishResearch(0);assert(WaveRanks[0]==1 and Players[0].gold==gold-2000 and UpgradeCost(0,6)==3000)
SpawnWave(0);assert(#Army[0]==4)
for rank=2,WAVE_UPGRADE_MAX do
 local expected=2000+(rank-1)*1000;local before=Players[0].gold
 assert(UpgradeCost(0,6)==expected and purchase(0,6));assert(WaveRanks[0]==rank and Players[0].gold==before-expected)
end
assert(not Buy(0,6) and UpgradeCost(0,6)==-1)
Army[0]={};SpawnWave(0);assert(#Army[0]==23)
-- Four orientations keep the expanded formation facing inward, with unique sites.
for p=0,11 do
 Army[p]={};WaveRanks[p]=WAVE_UPGRADE_MAX;SpawnWave(p);assert(#Army[p]==23)
 local positions={}
 for _,u in ipairs(Army[p])do local k=u.x..':'..u.y;assert(not positions[k]);positions[k]=true end
end
-- The existing army limit remains in force, including partially filled final waves.
Army[0]={};for n=1,ARMY_CAP-1 do Army[0][n]=CreateUnit(0,ArmyType[0],0,0,0)end
SpawnWave(0);assert(#Army[0]==60);SpawnWave(0);assert(#Army[0]==60)
-- Bots purchase wave ranks through the same native queue and protect partial budgets.
reset();Bot[0]=true;Players[0].gold=1000000
for kind=0,2 do for rank=1,2 do assert(purchase(0,kind))end end
assert(purchase(0,3));assert(purchase(0,3));BotBuy(0);assert(Base[0].pending==FourCC('Rfwn'));FinishResearch(0);assert(WaveRanks[0]==1)
reset();Players[0].gold=1999;assert(not Buy(0,6) and not Base[0].pending)
-- An enemy approaching a base wakes its bastion BEFORE its first damage event.
reset();Seconds=WARMUP_SECONDS+10;AllowedOrders={attack=true}
Hero[3].x=HomeX[0]+800;Hero[3].y=HomeY[0];UpdateBastion(0)
assert(not Bastion[0].paused and Bastion[0].order[2]==Hero[3] and BastionUntil[0]==Seconds+6)
local first=Bastion[0].order;Seconds=Seconds+1;UpdateBastion(0)
assert(Bastion[0].order==first and BastionUntil[0]==Seconds+6,'Keep firing: repeated proximity checks must not reset tower attacks')
Hero[3].x=0;Hero[3].y=0;Seconds=Seconds+7;UpdateBastion(0);assert(Bastion[0].paused)
Hero[1].x=HomeX[0];Hero[1].y=HomeY[0];UpdateBastion(0);assert(Bastion[0].paused,'Allies do not wake defense')
Bastion[0].hp=0;Hero[3].x=HomeX[0];Hero[3].y=HomeY[0];UpdateBastion(0);assert(Bastion[0].hp==0,'No revival from proximity')
-- New supply shop delivers paid items through ordinary native shop interactions.
reset();UtilityShop[0]=CreateUnit(15,FourCC('futl'),UtilityX[0],UtilityY[0],0)
Hero[0].x=UtilityX[0];Hero[0].y=UtilityY[0];Players[0].gold=20000
assert(IssueNeutralTargetOrder(0,UtilityShop[0],'neutralinteract',Hero[0]))
for _,name in ipairs({'fdgr','fsdm','fsar','fshl','fpH0','fpM0'})do
 local id=FourCC(name);local before=Players[0].gold
 assert(IssueNeutralImmediateOrderById(0,UtilityShop[0],id) and Players[0].gold==before-EngineItems[id].cost)
end
print('PASS: native paid wave research 3→4→23, full rank/cost progression, dead-hero purchase, bot queue, four inward formations, army cap, proximity bastion wake without resetting attacks, idle/dead/allied defense and paid utility purchases (mock natives).')
