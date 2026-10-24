-- Actual recovery commands, source wrappers and native form-state observation, with mocked natives.
for p=0,11 do RosterReset(p)end
TimeNow=8000000;CampaignStage=12;CampaignTransition=false;CampaignFinished=false;CampaignAlliances(2);World={}
local p=7;HeroRole[p]=1;HeroRole[1]=7
local s=CreateUnit(p,raw('R001'),CampaignX[12],CampaignY[12],0);Hero[p]=s;HeroType[p]=s.type
s.hp=5000;s.mana=700;s.level=45;s.xp=9999;s.items={[0]={type=123,owned=true}};local kept=s.items[0]
function SetUnitScale(u,x,y,z)u.scale=x end
function SetUnitInvulnerable(u,on)u.invul=on;if on then u.abilities[raw('Avul')]=1 else u.abilities[raw('Avul')]=nil end end
NPCCooldowns=InitHashtable();SasukeLastType[p]=0;SasukeMorphRepairAt[p]=0;SasukeSafeReady[p]=false
InvasionHeroVisibility();assert(SasukeSafeReady[p])
-- Cursed-form enter and return must release stale alternate/invulnerability after the native delay.
for _,id in ipairs({raw('Rsfm'),raw('R001')})do
 s.type=id;s.alternate=true;s.hidden=true;s.abilities[raw('Avul')]=1;s.abilities[raw('BOwk')]=1;LogUntil[p]=TimeNow+3
 InvasionHeroVisibility();TimeNow=TimeNow+1;InvasionHeroVisibility();assert(s.hidden,'Wait for native morph transition')
 TimeNow=TimeNow+.5;InvasionHeroVisibility();assert(not s.hidden and not s.alternate and not s.abilities[raw('Avul')]and not s.abilities[raw('BOwk')])
 assert(Hero[p]==s and s.items[0]==kept and s.xp==9999 and s.hp==5000,'Never replace or heal the real hero')
end
-- Actual chat dispatch recovers invisible/untargetable/paused real Sasuke in a swapped slot.
s.hidden=true;s.paused=true;s.alpha=0;s.abilities[raw('Avul')]=1;s.abilities[raw('Aloc')]=1;s.abilities[raw('Apiv')]=1
local triggerPlayer,chat=GetTriggerPlayer,GetEventPlayerChatString
function GetTriggerPlayer()return 0 end;function GetEventPlayerChatString()return '-fixsasuke'end
FoundationChat();assert(not s.hidden and not s.paused and s.alpha==255 and not s.abilities[raw('Avul')]and not s.abilities[raw('Aloc')]and not s.abilities[raw('Apiv')])
assert(Hero[p]==s and s.items[0]==kept and s.level==45 and s.xp==9999 and s.hp==5000 and s.mana==700)
GetTriggerPlayer=triggerPlayer;GetEventPlayerChatString=chat
-- Source cleanup can remove a dummy, never the registered real hero during active invasion.
InvasionSourceRemove(s,'race-cleanup');assert(not s.removed and SasukeBlockedRemove[p]>0 and SasukeLastSource[p]=='race-cleanup')
local dummy=CreateUnit(p,raw('rdst'),0,0,0);InvasionSourceRemove(dummy,'cleanup');assert(dummy.removed)
-- Resetting repeated alpha writes cannot postpone recovery forever.
function SetUnitVertexColorBJ(u,r,g,b,t)SetUnitVertexColor(u,r,g,b,math.floor((100-t)*2.55+.5))end
SasukeAlphaSince[p]=0;InvasionSourceColor(s,100,100,100,100)
for n=1,10 do TimeNow=TimeNow+1;InvasionSourceColor(s,100,100,100,100);InvasionHeroVisibility()end
assert(s.alpha==255)
-- Accidental teleport outside village returns to last known safe point, without resurrection.
InvasionHeroVisibility();local x,y=s.x,s.y;s.x=0;s.y=16000;InvasionHeroVisibility();TimeNow=TimeNow+3;InvasionHeroVisibility();assert(s.x==x and s.y==y)
CampaignStage=17;s.hidden=true;s.paused=true;InvasionFixSasuke(0);assert(s.hidden and s.paused,'Never break intentional story hiding')
CampaignStage=12;s.hp=0;InvasionFixSasuke(0);assert(s.hp==0,'No resurrection cheat')
print('PASS: Sasuke native morph flag cleanup/identity and stats preservation, real -fixsasuke chat, protected source deletion, repeated-alpha deadline, outside teleport recovery and plot/death guards (mock natives).')
