-- Real emitted JASS decisions; Classic rendering and native spell effects still need a playtest.
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
TimeNow=900000;CampaignStage=0;CampaignAlliances(0)
local timers=CreatedTimers
for _,id in ipairs({'R000','Rnfm'})do
 local clone=CreateUnit(0,raw(id),0,0,0);clone.illusion=true;clone.hp=10000;Caster=clone
 Clone43Track(clone);NativeEventDamage=1;SkillsFragileClone();NativeEventDamage=0;assert(clone.hp==0,'Naruto clone disappears from one attack regardless of copied HP')
end
local real=CreateUnit(0,raw('R000'),0,0,0);Caster=real;SkillsFragileClone();assert(real.hp==10000,'Never kill the real Naruto')
local other=CreateUnit(1,raw('R001'),0,0,0);other.illusion=true;Caster=other;SkillsFragileClone();assert(other.hp==10000,'Do not change other illusion families')
assert(CreatedTimers==timers,'The clone rule uses bounded damage registrations, no per-clone timers')
-- Both Hyuugas get exactly one source hit with requested additional +30% before the push at every rank.
for _,p in ipairs({4,8})do
 Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroType[p]=Hero[p].type;HeroRole[p]=p;Hero[p].level=60
 for rank,damage in ipairs({156,234,312,546})do
  RosterReset(p);local enemy=CreateUnit(12,raw('re06'),100,0,0);enemy.hp=10000;World={enemy}
  cast(p,PlayableSkill[p*5+1],rank,nil);assert(enemy.hp==10000-damage,'Immediate boosted Kaiten damage before pushing target away')
  for i=1,5 do TimeNow=TimeNow+.5;RosterTick()end
  assert(enemy.hp==10000-damage,'Animation pulses must not duplicate source damage')
 end
end
-- Native and scripted cooldown paths must both reset for a new arena opponent.
Hero[0]=real;BotNextCast[0]=TimeNow+100;LogReadyAt[0]=TimeNow+100;JumpReadyAt[0]=TimeNow+100;BotUseItemAt[0]=TimeNow+100
for k=0,4 do BotReadyAt[k]=TimeNow+100 end
local resets=real.cooldownResets or 0;CampaignResetFighter(0)
assert(real.cooldownResets==resets+1 and BotNextCast[0]==TimeNow and LogReadyAt[0]==TimeNow and JumpReadyAt[0]==TimeNow and BotUseItemAt[0]==TimeNow)
for k=0,4 do assert(BotReadyAt[k]==TimeNow)end
-- First city visit already has the original corner shop/fountain, not only invasion.
CampaignStage=10;CampaignTransition=false;CampaignAlliances(1);StoryShopsOpen();CampaignFountainsOpen();CampaignVillageLandmarksOpen()
assert(StoryShop[0].x==16192 and StoryShop[0].y==-16256 and VillageFountain[0].x==16128 and VillageFountain[0].y==-15744)
assert(StoryShopFor(0)and StoryFountainFor(0));StoryCommand(0,'-shop');assert(Selected==StoryShopFor(0));StoryCommand(0,'-fountain');assert(Selected==StoryFountainFor(0))
CampaignVillageLandmarksClose();StoryShopsClose()
print('PASS: one-attack Naruto clones without killing the real hero/other illusions; both Hyuugas and all four boosted instant Kaiten ranks; native plus bot cooldown reset; original corner supply available during Jiraiya search (mock natives).')

-- Role ownership must follow chosen characters, not the original player numbers.
CampaignStage=12;CampaignTransition=false;CampaignCount=0;CampaignThinkCursor=0;World={}
for p=0,11 do HeroRole[p]=p end
HeroRole[0]=9;HeroRole[9]=0;CampaignBindRoles();CampaignAlliances(2);CampaignMoveHeroes()
assert(Hero[0].x==-2336 and Hero[9].x~=-2336 and CampaignAttackerOwner[0]==0,'A Gaara selected by red must join Sand at FM')
for lane=0,7 do
 local first=CampaignCount;CampaignInvasionWave(lane);assert(CampaignCount==first+4)
 for j=first,first+3 do
  local u=CampaignActor[j];local owner=PLAYER_NEUTRAL_PASSIVE
  assert(u.owner==owner and IsUnitEnemy(u,9) and not IsUnitEnemy(u,0),'All streams belong to Sand, hostile to Leaf')
  assert(not u.paused and u.last.o=='attack' and CampaignActorRoute[j]==CampaignWaveDestination[lane])
 end
 -- Simulate arrival; the real JASS must progress through VM before the Hokage.
 local u=CampaignActor[first];local destination=CampaignActorRoute[first]
 u.x=CampaignRouteX[destination];u.y=CampaignRouteY[destination];CampaignMoveAt[first]=0;CampaignThinkCursor=first
 CampaignNPCTick();assert(CampaignActorRoute[first]==(destination==8 and 11 or 8))
 u.x=CampaignRouteX[8];u.y=CampaignRouteY[8];CampaignMoveAt[first]=0;CampaignThinkCursor=first
 CampaignNPCTick();assert(CampaignActorRoute[first]==11 and u.last.o=='attack','Every lane redirects through VM toward the Hokage')
end
print('PASS: all eight source invasion streams, three active attackers each, character-based ownership even after swapped selection, enemy relations and VM-to-Hokage redirects (mock natives).')
