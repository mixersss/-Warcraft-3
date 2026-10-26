-- Full recovery executes the actual chat and native-replacement code, with explicit native mocks.
for p=0,11 do RosterReset(p)end
CampaignStage=12;CampaignTransition=false;CampaignFinished=false;TimeNow=11000000;World={}
for p=0,11 do
 Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;HeroType[p]=Hero[p].type;HeroTemplate[p]=p;Controllers[p]='computer';CampaignPermanentDead[p]=false;StoryRevive[p]=0
end
Controllers[0]='human';Controllers[3]='human';CampaignBindRoles();CampaignAlliances(2)
SpawnX[1]=1000;SpawnY[1]=2000;NPCSourceReady=true
local saved={}
local function mock(name,f)saved[#saved+1]={name,_G[name]};_G[name]=f end
mock('GetHeroStr',function(u,bonus)return u.str or 20 end)
mock('GetHeroInt',function(u,bonus)return u.int or 20 end)
mock('SetHeroStr',function(u,n,permanent)assert(permanent);u.str=n end)
mock('SetHeroInt',function(u,n,permanent)assert(permanent);u.int=n end)
mock('UnitInventorySize',function(u)return 6 end)
mock('UnitModifySkillPoints',function(u,n)u.points=u.points+n;return true end)
mock('UnitDropItemSlot',function(u,item,slot)
 local prior=nil;for k=0,5 do if u.items[k]==item then prior=k end end
 if prior==nil then return false end
 u.items[prior],u.items[slot]=u.items[slot],item;return true
end)
local sender=0;local message='-rebuildsasuke'
mock('GetTriggerPlayer',function()return sender end)
mock('GetEventPlayerChatString',function()return message end)
local function fixture(u)
 u.type=raw('Rsfm');u.level=45;u.xp=4425;u.points=7;u.str=123;u.agi=234;u.int=345
 u.hp=2500;u.maxLife=10000;u.mana=200;u.maxMana=1000;u.dead=false;u.paused=true;u.hidden=true;u.alpha=0;u.pathing=false;u.items={}
 for k=0,4 do u.abilities[PlayableSkill[5+k]]=({4,3,2,3,1})[k+1]end
 u.abilities[raw('Rlog')]=1
 for k=0,5 do local it=CreateItem(100+k,0,0);it.charges=k+1;UnitAddItem(u,it)end
end
local old=Hero[1];fixture(old);CampaignSasuke=old;Dummy[0]=old;CampaignOroTarget=old
local kept={};for k=0,5 do kept[k]=old.items[k]end
sender=3;FoundationChat();assert(Hero[1]==old and not old.removed,'Unrelated non-host cannot rebuild another hero')
sender=0;FoundationChat();local fresh=Hero[1]
assert(fresh~=old and old.removed and fresh.owner==1 and fresh.type==raw('R001'),'Native replacement at same owner in ordinary base form')
assert(CampaignSasuke==fresh and OrigNPC_JZV==fresh and Dummy[0]==fresh and CampaignOroTarget==nil,'Story/source/target references rebound')
assert(fresh.x==SpawnX[1]and fresh.y==SpawnY[1]and not fresh.paused and not fresh.hidden and fresh.alpha==255 and fresh.pathing and not fresh.invul,'Clean visible controllable vulnerable body')
assert(fresh.level==45 and fresh.xp==4425 and fresh.points==7 and fresh.str==123 and fresh.agi==234 and fresh.int==345,'Level XP points and permanent book stats retained')
for k=0,4 do assert(GetUnitAbilityLevel(fresh,PlayableSkill[5+k])==({4,3,2,3,1})[k+1])end
assert(GetUnitAbilityLevel(fresh,raw('Rlog'))==1)
for k=0,5 do assert(fresh.items[k]==kept[k]and kept[k].charges==k+1 and not old.items[k],'Same item handles/charges/slots, no duplication')end
assert(math.abs(fresh.hp/fresh.maxLife-.25)<.001 and math.abs(fresh.mana/fresh.maxMana-.2)<.001,'Living rebuild preserves pool fractions instead of granting full healing')
assert(SasukeRebuildCount[1]==1 and StoryRevive[1]==0)
FoundationChat();assert(Hero[1]==fresh and SasukeRebuildCount[1]==1,'30-second spam guard')
-- Native creation failure is non-destructive to the existing body and gear.
TimeNow=TimeNow+31;local create=CreateUnit
CreateUnit=function(p,id,x,y,facing)if p==1 and id==raw('R001')then return nil end;return create(p,id,x,y,facing)end
FoundationChat();assert(Hero[1]==fresh and not fresh.removed and fresh.items[0]==kept[0]and not SasukeRebuildTarget[1],'Failed CreateUnit keeps original progress and clears request')
CreateUnit=create
-- A normal death waits its existing deadline once, then rebuilds even if native revive is broken.
old=Hero[1];old.dead=true;old.hp=700;StoryRevive[1]=TimeNow+20;SasukeReviveFailures[1]=0
FoundationChat();local due=SasukeRebuildAt[1];assert(SasukeRebuildTarget[1]==old and due==StoryRevive[1]and Hero[1]==old)
TimeNow=TimeNow+5;FoundationChat();assert(SasukeRebuildAt[1]==due,'Repeated requests do not postpone death recovery')
TimeNow=due-.5;InvasionRebuildTick();assert(Hero[1]==old)
-- The recovery prefix must still finish before an intentionally failing story loop.
local story=StoryTick;StoryTick=function()error('simulated story abort')end
local ok=pcall(FoundationTick);assert(not ok and Hero[1]~=old and old.removed and FoundationAlive(Hero[1]),'Critical isolated prefix can replace a dead+positiveHP ghost before a broken StoryTick')
StoryTick=story;fresh=Hero[1]
assert(fresh.items[0]==kept[0]and fresh.level==45 and fresh.xp==4425 and fresh.points==7 and SasukeRebuildCount[1]==2)
-- Diagnostics now reaches the actual status handler instead of the earlier hero-choice alias.
local status,choose=InvasionSasukeStatus,SkillsChoose;local shown,chosen=0,0
InvasionSasukeStatus=function(p)shown=shown+1 end;SkillsChoose=function(p,role)chosen=chosen+1 end
message='-sasuke';FoundationChat();assert(shown==1 and chosen==0,'Active-invasion -sasuke is diagnostics, not an unreachable branch')
CampaignStage=0;FoundationChat();assert(chosen==1,'The original pre-story hero-choice shortcut remains')
InvasionSasukeStatus,SkillsChoose=status,choose
message='-rebuildsasuke';CampaignStage=17;FoundationChat();assert(Hero[1]==fresh,'No resurrection during late clone elimination')
CampaignStage=12;CampaignTransition=true;FoundationChat();assert(Hero[1]==fresh,'No rebuild during scene placement')
CampaignTransition=false;CampaignFinished=true;FoundationChat();assert(Hero[1]==fresh)
CampaignFinished=false;TimeNow=TimeNow+31
-- Actual owner may use the hard alias; a failed normal revival does not loop another20seconds.
Controllers[1]='human';sender=1;message='-fixsasuke hard';fresh.dead=true;fresh.hp=400;StoryRevive[1]=TimeNow+1;SasukeReviveFailures[1]=2
FoundationChat();assert(Hero[1]~=fresh and fresh.removed and FoundationAlive(Hero[1])and SasukeRebuildCount[1]==3)
-- Requests are cancelled if the scene changes before the ordinary death wait ends.
TimeNow=TimeNow+31;fresh=Hero[1];fresh.dead=true;StoryRevive[1]=TimeNow+20;SasukeReviveFailures[1]=0;FoundationChat();assert(SasukeRebuildTarget[1])
CampaignTransition=true;InvasionRebuildTick();assert(not SasukeRebuildTarget[1]and Hero[1]==fresh,'No delayed unit creation in the next scene')
CampaignTransition=false
for i=#saved,1,-1 do _G[saved[i][1]]=saved[i][2]end
print('PASS: real hard-recovery chat/host-owner guards, same gear handles/charges/slots, XP/level/book stats/skills/unspent points/pool fractions, source references, creation rollback, one20s death deadline, critical prefix before aborted story, native-dead ghost replacement, diagnostics dispatch, cooldown and late-scene cancellation (mock natives).')
