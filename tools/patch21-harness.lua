-- Native card installation: exactly three enemy corners and center, no branch-card overlap.
for p=0,11 do
 reset();CommitArmyBranch(p,p%4)
 for k=0,3 do
  assert(GetUnitAbilityLevel(Base[p],FourCC('Fbr'..k))==0)
  assert(GetUnitAbilityLevel(Base[p],FourCC('Fao'..k))==(k==TeamOf(p)and 0 or 1))
  assert(GetUnitAbilityLevel(Base[p],FourCC('Fac'..k))==(k==TeamOf(p)and 1 or 0))
 end
end
-- All 12 source/destination pairs require the center, also on redirection.
for own=0,3 do for destination=0,3 do if own~=destination then
 reset();local p=own*3;ArmyDestination[p]=4
 SpawnWave(p);local troop=Army[p][1]
 assert(SetArmyDestination(p,destination)and ArmyDestination[p]==destination)
 assert(troop.order[2]==0 and troop.order[3]==0 and troop.data>10,'Fresh troops always enter center first')
 troop.x,troop.y=0,0;CommandArmy(p,false)
 local target=destination*3
 assert(troop.data<=10 and troop.order[2]==HomeX[target]and troop.order[3]==HomeY[target],'After actual center arrival, attack selected enemy fortress')
 local other=(destination+1)%4;if other==own then other=(other+1)%4 end
 troop.x,troop.y=HomeX[target],HomeY[target]
 assert(SetArmyDestination(p,other)and troop.order[2]==0 and troop.order[3]==0 and troop.data>10,'Changing corners recalls through center')
 assert(ArmyDestination[(p+1)%12]==4,'Only commanding player changes destination')
end end end
-- Native button and dialogue both reach the same command path; own corner is center.
reset();CommitArmyBranch(0,1);SpawnWave(0)
Dying=Base[0];SpellId=FourCC('Fao2');OnArmyOrderSpell();assert(ArmyDestination[0]==2)
SpellId=FourCC('Fac0');OnArmyOrderSpell();assert(ArmyDestination[0]==4)
Dying=Hero[0];SpellId=FourCC('Fao1');OnArmyOrderSpell();assert(ArmyDestination[0]==4)
Dying=Base[0];SpellId=FourCC('Fao0');OnArmyOrderSpell();assert(ArmyDestination[0]==4,'Own team cannot be attacked')
ShowArmyOrders(0);assert(#Shop[0].buttons==5)
for k=0,3 do if MenuAction[k]==601 then Clicked=ShopButton[k]end end
EventPlayer=0;OnArmyOrderDialog();assert(ArmyDestination[0]==1)
-- Does not charge gold, clear native research, reroll race or enable inactive slots.
reset();Players[0].gold=10000;assert(Buy(0,0));local pending=Base[0].pending;local gold=Players[0].gold
assert(SetArmyDestination(0,2));assert(Base[0].pending==pending and Players[0].gold==gold and not ArmyBranchChosen[0])
assert(not SetArmyDestination(0,0)and not SetArmyDestination(0,5)and not SetArmyDestination(-1,2))
SlotActive[0]=false;assert(not SetArmyDestination(0,1));SlotActive[0]=true
-- Center hold recalls long chases; emergency defense returns through center afterward.
reset();SpawnWave(0);local troop=Army[0][1];troop.x,troop.y=0,0;CommandArmy(0,false)
assert(troop.order[2]==0 and troop.order[3]==0)
troop.x=1200;troop.pending=1;CommandArmy(0,false);assert(troop.order[2]==0 and troop.order[3]==0,'Recall even a currently ordered long chase')
troop.pending=nil;Defending[0]=true;RallyX[0],RallyY[0]=HomeX[0]+100,HomeY[0]
assert(SetArmyDestination(0,2));assert(troop.order[2]==RallyX[0]and troop.order[3]==RallyY[0])
troop.x,troop.y=HomeX[0],HomeY[0];Defending[0]=false;CommandArmy(0,false);assert(troop.data>10 and troop.order[2]==0 and troop.order[3]==0,'Returning defenders cannot skip center')
-- Finish remaining barracks in the chosen team; fall back only when none survive.
reset();ArmyDestination[0]=1;Base[3].hp=0;assert(ArmyDestinationBase(0)==4)
Base[4].hp=0;Base[5].hp=0;CommandArmy(0,false);assert(ArmyDestination[0]==4)
-- Bots rally small armies, push real occupied teams with sufficient troops, retreat and replan.
reset();Bot[0]=true;RetreatUntil[0]=0;Seconds=WARMUP_SECONDS+100;for n=1,3 do SpawnWave(0)end
PlanBotArmyDestination(0);assert(ArmyDestination[0]~=4 and ArmyDestination[0]~=0 and ArmyDestinationBase(0)>=0)
local old=ArmyDestination[0];ArmyPlanAt[0]=Seconds+20;GroupClear(Army[0]);PlanBotArmyDestination(0);assert(ArmyDestination[0]==old,'Do not spam retarget orders')
Seconds=Seconds+20;PlanBotArmyDestination(0);assert(ArmyDestination[0]==4,'Small armies regroup centrally')
TeamPushUntil[0]=Seconds+60;Seconds=Seconds+20;PlanBotArmyDestination(0);assert(ArmyDestination[0]~=4,'Use team push signal')
RetreatUntil[0]=Seconds+60;Seconds=Seconds+20;PlanBotArmyDestination(0);assert(ArmyDestination[0]==4)
print('PASS:all12 directed routes through actual center,per-player native/dialog buttons,uncharged orders during research,center hold,defense return,destroyed/empty targets and20s bot push/regroup plans (mock natives).')

-- Trigger-created summons may have no OnSummon userdata; still visit center and stay outside cap.
reset();ArmyDestination[0]=2
local pet=CreateUnit(0,FourCC('hwat'),HomeX[0],HomeY[0],0);pet.summoned=true
CommandArmy(0,false);assert(pet.data==11 and pet.order[2]==0 and pet.order[3]==0 and #Army[0]==0)
pet.x,pet.y=0,0;CommandArmy(0,false);assert(pet.data==1 and pet.order[2]==HomeX[6]and pet.order[3]==HomeY[6])
print('PASS:unmarked trigger-created summons use center waypoint without occupying the trained-army cap.')
