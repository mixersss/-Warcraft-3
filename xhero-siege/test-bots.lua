XHInit();assert(Timers==1 and Triggers==3)
for p=0,7 do Controllers[p]=MAP_CONTROL_COMPUTER;Slots[p]=PLAYER_SLOT_STATE_PLAYING end
Controllers[0]=MAP_CONTROL_USER;Slots[7]=0
assert(XHParticipant(0)and XHParticipant(1)and not XHParticipant(7)and not XHParticipant(9))
for i=0,7 do CreateUnit(8,XHPool[i],udg_rect14.x,udg_rect14.y,0)end
XHReady=false;for i=1,8 do XHStep()end;assert(udg_units01[2]==nil)
XHReady=true;for i=1,8 do XHStep()end
assert(udg_units01[1]==nil and udg_units01[8]==nil,'Never create heroes in human or empty slots')
local seen={};for p=1,6 do local u=udg_units01[p+1];assert(u and not seen[u.id]);seen[u.id]=true;assert(Gold[p]==1000 and XHOwns(u,raw('ankh'))and XHOwns(u,raw('pghe'))and XHOwns(u,raw('stwp')));local same=u;XHSpawn(p);assert(udg_units01[p+1]==same and Gold[p]==1000)end
local u=udg_units01[2];u.points=10;XHLearn(u);assert(u.points==7,'Bounded native skill learning')
u.abilities={};u.points=0;u.x=0;u.y=-8704;u.hp=u.max;XHTime=100;XHBuyAt[1]=999;local enemy=CreateUnit(10,raw('ugho'),100,-8704,0);local hidden=CreateUnit(10,raw('ugho'),1,-8704,0);hidden.invisible=true
assert(XHEnemy(u)==enemy);XHThink(1,1,u);assert(u.last.target==enemy)
u.hp=100;XHThink(1,1,u);assert(u.used==raw('pghe')and u.hp==u.max,'Actually use starting heal item')
u.hp=100;XHThink(1,1,u);assert(u.last.o=='move'and u.last.x==udg_rect33.x,'Critical retreat')
u.paused=true;u.last=nil;XHThink(1,1,u);assert(u.last==nil);u.paused=false
u.hp=u.max;enemy.dead=true;hidden.dead=true
udg_unit02=CreateUnit(8,raw('hcas'),0,-8704,0);udg_unit02.structure=true
XHBuyAt[1]=0;Gold[1]=20000;u.x=0;u.y=-8704
assert(XHShop(1,1,u)and Gold[1]==0 and XHOwns(u,raw('ofro'))and XHPurchases[1]==1)
XHTime=120;Gold[1]=50000;StockAvailable=false;XHShop(1,1,u);assert(Gold[1]==50000 and XHPurchases[1]==1,'Rejected stock order never charges fake gold')
StockAvailable=true;XHTime=140;XHShop(1,1,u);assert(Gold[1]==0 and XHOwns(u,raw('modt'))and XHPurchases[1]==2)
Gold[1]=50000;XHTime=160;local strength=u.str;XHShop(1,1,u);assert(Gold[1]==0 and u.str==strength+100 and XHPurchases[1]==3,'Exact original paid tome rule')
Gold[1]=50000;XHTime=180;udg_trigger62.enabled=true;assert(not XHShop(1,1,u)and Gold[1]==50000,'No book spending during special duel');udg_trigger62.enabled=false
XHBuyAt[1]=999;u.x=4000;u.y=5000;XHThink(1,1,u);assert(u.last.o=='holdposition','Never leave own cleared challenge room for another boss')
u.x=0;u.y=-8704;XHThink(1,1,u);assert(u.last.o=='attack'and math.abs(u.last.x)<=800 and math.abs(u.last.y+8704)<=800,'Spread idle defense across actual lane approaches')
TriggerUnit=u;SpellId=raw('AHbz');XHSpell();u.last=nil;XHThink(1,1,u);assert(u.last==nil and XHBusy[1]==XHTime+8,'Do not interrupt channel')
assert(Timers==1 and Triggers==3,'No per-think or per-unit handles')
print('PASS: active/computer/empty slot gates, one-time template selection, source starting items and budget, native learning, enemy visibility, fighting/healing/retreat, source-price paid purchases with stock failure and tomes, challenge-room hold, lane defense, channel protection and bounded timers')
-- Every supported pool hero has an active native order in its actual source kit.
for i=0,7 do
 local id=XHPool[i];local active=0
 for k=0,4 do local skill=XHSkill(id,k);if skill~=0 and XHMode(skill)>0 then active=active+1;assert(XHOrder(skill)~='')end end
 assert(active>=2,'Every manual pool hero needs useful active techniques')
end
-- Native healer picks an actually injured ally instead of issuing damage at an ally.
local paladin=CreateUnit(2,raw('Hpal'),0,-8704,0);paladin.abilities[raw('A00M')]=1
u.hp=u.max*.3;u.x=0;u.y=-8704;XHCastAt[2]=0;XHTime=500
assert(XHCast(2,paladin,nil)and paladin.last.o=='healingwave'and paladin.last.target==u)
print('PASS:8 actual source hero kits have active order profiles and healer targets injured ally')

local medicShop=CreateUnit(15,raw('ngme'),0,-8704,0);medicShop.structure=true
u.x=0;u.y=-8704;u.hp=100;Gold[1]=1000;XHHealAt[1]=0;XHTime=700
assert(XHHeal(1,1,u)and Gold[1]==400 and XHOwns(u,raw('pghe')),'Emergency potion bought through native shop for real gold')
local pet=CreateUnit(1,raw('hwat'),0,-8704,0);Summoning=u;Summoned=pet;XHSummon();assert(pet.last.o=='follow'and pet.last.target==u)
print('PASS: emergency native potion purchase and actual summoned-unit follow callback')
